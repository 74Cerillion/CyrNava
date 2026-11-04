"""Real isolated Git histories and fail-closed accepted-source preparation."""

import copy
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core
import workflow_policy


class SourceCheckoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="p5b-source-tests-")
        cls.root = Path(cls.temporary.name)
        cls.environment = {
            **os.environ,
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z",
            "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z",
        }
        cls.seed = cls.root / "seed"
        cls.git("init", "--quiet", "--initial-branch=tooling", cls.seed)
        for text in ("accepted application source", "later release tooling"):
            (cls.seed / "synthetic.txt").write_text(text)
            cls.git("-C", cls.seed, "add", "synthetic.txt")
            cls.git(
                "-C",
                cls.seed,
                "-c",
                "user.name=Synthetic Test",
                "-c",
                "user.email=synthetic@invalid.example",
                "commit",
                "--quiet",
                "--no-gpg-sign",
                "-m",
                text,
            )
            if text == "accepted application source":
                cls.accepted = cls.git("-C", cls.seed, "rev-parse", "HEAD").strip()
        cls.tooling = cls.git("-C", cls.seed, "rev-parse", "HEAD").strip()
        for name, extra in (("shallow", ["--depth=1"]), ("full", [])):
            dest = cls.root / name
            cls.git("clone", "--quiet", "--no-local", *extra, cls.seed.as_uri(), dest)
            assert not (dest / ".git/objects/info/alternates").exists()

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    @classmethod
    def git(cls, *args):
        return subprocess.check_output(
            ["git", *map(str, args)],
            env=cls.environment,
            text=True,
            stderr=subprocess.PIPE,
            timeout=30,
        )

    def setUp(self):
        self.work = Path(tempfile.mkdtemp(dir=self.root))

    def test_shallow_missing_ancestor_fails_at_detached_checkout(self):
        with (
            patch.object(core, "ROOT", self.root / "shallow"),
            self.assertRaisesRegex(
                core.Rejected, "accepted-source-checkout \\(exit-128\\)"
            ),
        ):
            core.checkout_accepted_source(self.work / "source", self.accepted)

    def test_full_history_resolves_exact_accepted_source_detached(self):
        with patch.object(core, "ROOT", self.root / "full"):
            source = core.checkout_accepted_source(self.work / "source", self.accepted)
        self.assertEqual(
            self.git("-C", source, "rev-parse", "HEAD").strip(), self.accepted
        )
        self.assertEqual(
            (source / "synthetic.txt").read_text(), "accepted application source"
        )
        self.assertEqual((source / ".git/HEAD").read_text().strip(), self.accepted)
        self.assertNotEqual(self.accepted, self.tooling)

    def test_unavailable_sha_never_falls_back_to_tooling(self):
        with (
            patch.object(core, "ROOT", self.root / "full"),
            self.assertRaisesRegex(core.Rejected, "accepted-source-checkout"),
        ):
            core.checkout_accepted_source(self.work / "source", "f" * 40)

    def test_nonimmutable_source_rejected_before_any_git_operation(self):
        for invalid in ("HEAD", "tooling", self.accepted[:7], "--help"):
            with (
                self.subTest(source=invalid),
                patch.object(core, "call") as git,
                self.assertRaisesRegex(core.Rejected, "Full immutable"),
            ):
                core.checkout_accepted_source(self.work / "source", invalid)
            git.assert_not_called()

    def test_unexpected_checkout_result_cannot_reach_key_audit_or_signing(self):
        real_call = core.call

        def wrong_revision(*args, **kwargs):
            if kwargs.get("operation") == "accepted-source-verify":
                return self.tooling.encode() + b"\n"
            return real_call(*args, **kwargs)

        with (
            patch.object(core, "ROOT", self.root / "full"),
            patch.object(core, "call", side_effect=wrong_revision) as calls,
            patch.object(core, "make_key") as key,
            self.assertRaisesRegex(core.Rejected, "Immutable source checkout mismatch"),
        ):
            core.generate_repository(
                self.work / "candidate",
                self.work / "public",
                self.work,
                {"source_commit": self.accepted},
                "https://invalid.example",
            )
        key.assert_not_called()
        self.assertTrue(all(c.args[0] == "git" for c in calls.call_args_list))
        self.assertFalse((self.work / "public").exists())

    def test_missing_history_cannot_reach_key_or_publication(self):
        with (
            patch.object(core, "ROOT", self.root / "shallow"),
            patch.object(core, "make_key") as key,
            self.assertRaisesRegex(core.Rejected, "accepted-source-checkout"),
        ):
            core.generate_repository(
                self.work / "candidate",
                self.work / "public",
                self.work,
                {"source_commit": self.accepted},
                "https://invalid.example",
            )
        key.assert_not_called()
        self.assertFalse((self.work / "public").exists())


class SourcePolicyTests(unittest.TestCase):
    def test_staging_requires_full_history_and_immutable_credential_free_checkout(self):
        workflow = workflow_policy.read_workflow(
            core.ROOT / ".github/workflows/release.yml"
        )
        self.assertTrue(workflow_policy.validate(workflow))
        for depth in (None, 1, 2, "0"):
            changed = copy.deepcopy(workflow)
            settings = changed["jobs"]["staging"]["steps"][0]["with"]
            settings.pop("fetch-depth")
            if depth is not None:
                settings["fetch-depth"] = depth
            with self.subTest(depth=depth), self.assertRaises(core.Rejected):
                workflow_policy.validate(changed)

    def test_fixed_git_operation_categories_never_expose_sensitive_details(self):
        sensitive = "https://user:TOKEN_SECRET@invalid.example/private/path"
        failures = (
            (
                subprocess.CalledProcessError(128, [sensitive], stderr=sensitive),
                "exit-128",
            ),
            (subprocess.TimeoutExpired([sensitive], 1, stderr=sensitive), "timeout"),
            (OSError(sensitive), "unavailable"),
        )
        for operation in (
            "accepted-source-clone",
            "accepted-source-checkout",
            "accepted-source-verify",
        ):
            for error, category in failures:
                with (
                    self.subTest(operation=operation, category=category),
                    patch.object(subprocess, "run", side_effect=error),
                    self.assertRaises(core.Rejected) as caught,
                ):
                    core.call(
                        "git", sensitive, operation=operation, env={"TOKEN": sensitive}
                    )
                self.assertEqual(
                    str(caught.exception),
                    f"Git operation failed: {operation} ({category})",
                )
                self.assertNotIn("TOKEN_SECRET", str(caught.exception))

    def test_unreviewed_operation_label_cannot_leak_arguments(self):
        with (
            patch.object(subprocess, "run") as run,
            self.assertRaises(core.Rejected) as caught,
        ):
            core.call("git", "secret", operation="secret")
        run.assert_not_called()
        self.assertEqual(str(caught.exception), "Unreviewed operation label")


if __name__ == "__main__":
    unittest.main()
