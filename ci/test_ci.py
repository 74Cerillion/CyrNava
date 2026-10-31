"""Isolated workflow, failure propagation and exported-payload contracts.

Mocked Flatpak commands are never reported as hosted/native verification.
"""

import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location("p5a_" + name, HERE / (name + ".py"))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


validator = load("validate")
verification = load("verify")
flatpak = load("flatpak")


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.value = validator.workflow(HERE.parent / ".github/workflows/ci.yml")
        self.pins = json.loads((HERE / "tools.json").read_text())["actions"]

    def test_actual_workflow(self):
        self.assertTrue(validator.validate(self.value, self.pins))
        self.assertIn("on", self.value)
        self.assertNotIn(True, self.value)

    def test_unreviewed_capabilities_are_rejected(self):
        changes = (
            lambda v: v.update(permissions={"contents": "write"}),
            lambda v: v["on"].update(pull_request_target={}),
            lambda v: v["on"]["push"].update(paths=["frontend/**"]),
            lambda v: v["jobs"]["backend"].update(**{"continue-on-error": True}),
            lambda v: v["jobs"]["backend"].update(permissions={"contents": "write"}),
            lambda v: v["jobs"]["flatpak"].update(needs=["backend"]),
            lambda v: v["jobs"]["required"].update(**{"if": "success()"}),
            lambda v: v["jobs"]["backend"]["steps"][0].update(
                uses="actions/checkout@v6"
            ),
            lambda v: v["jobs"]["backend"]["steps"][0]["with"].update(
                **{"persist-credentials": True}
            ),
            lambda v: v["jobs"]["backend"]["steps"][-1]["with"].update(
                **{"if-no-files-found": "warn"}
            ),
            lambda v: v["jobs"]["backend"]["steps"][-1].update(
                **{"continue-on-error": True}
            ),
            lambda v: v["jobs"]["backend"]["steps"][2].update(
                run="echo '${{ github.event.pull_request.title }}'"
            ),
        )
        for mutate in changes:
            with self.subTest(mutation=changes.index(mutate)):
                value = copy.deepcopy(self.value)
                mutate(value)
                with self.assertRaises(ValueError):
                    validator.validate(value, self.pins)

    def test_package_upload_cannot_run_after_failed_audit(self):
        value = copy.deepcopy(self.value)
        step = next(
            s
            for s in value["jobs"]["flatpak"]["steps"]
            if s.get("with", {}).get("path") == "ci-output/flatpak/artifacts/"
        )
        step["if"] = "always()"
        with self.assertRaises(ValueError):
            validator.validate(value, self.pins)

    def test_final_gate_fails_for_failed_skipped_and_cancelled_jobs(self):
        script = self.value["jobs"]["required"]["steps"][0]["run"]
        environment = {
            name: "success"
            for name in (
                "VALIDATE_RESULT",
                "BACKEND_RESULT",
                "FRONTEND_RESULT",
                "FLATPAK_RESULT",
            )
        }
        self.assertEqual(
            subprocess.run(["bash", "-e", "-c", script], env=environment).returncode, 0
        )
        for key in environment:
            for status in ("failure", "skipped", "cancelled", ""):
                with self.subTest(job=key, status=status):
                    changed = {**environment, key: status}
                    self.assertNotEqual(
                        subprocess.run(
                            ["bash", "-e", "-c", script], env=changed
                        ).returncode,
                        0,
                    )


class ExecutionTests(unittest.TestCase):
    def test_real_deliberate_failure_blocks_later_artifact_step(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = root / "result.json"
            marker = root / "should-not-exist"
            steps = [
                (
                    "deliberate-broken-test",
                    [sys.executable, "-c", "raise SystemExit(17)"],
                    root,
                ),
                (
                    "upload",
                    [sys.executable, "-c", f"open({str(marker)!r}, 'w').close()"],
                    root,
                ),
            ]
            self.assertEqual(verification.run_steps(steps, result), 1)
            record = json.loads(result.read_text())
            self.assertEqual(record["status"], "FAIL")
            self.assertEqual(record["exit_code"], 17)
            self.assertTrue(record["complete"])
            self.assertFalse(marker.exists())
            self.assertEqual(len(record["steps"]), 1)

    def test_missing_executable_produces_final_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = Path(tmp) / "result.json"
            self.assertEqual(
                verification.run_steps(
                    [("missing", ["/nonexistent-cyrnava-tool"], tmp)], result
                ),
                1,
            )
            self.assertEqual(
                json.loads(result.read_text())["error_type"], "FileNotFoundError"
            )

    def test_backend_commands_preserve_cwd_and_all_previous_suites(self):
        steps = verification.steps_for("backend", Path("/tmp/synthetic-report"))
        self.assertEqual(steps[-1][2], HERE.parent / "backend")
        self.assertIn("tests", steps[-1][1])
        self.assertIn("../packaging/flatpak/production/test_packaging.py", steps[-1][1])
        self.assertNotIn("--ignore", steps[-1][1])

    def test_no_silent_runtime_substitution(self):
        with (
            patch.dict(
                os.environ,
                {"GITHUB_ACTIONS": "true", "RUNNER_ENVIRONMENT": "github-hosted"},
            ),
            patch.object(flatpak, "run") as run,
        ):
            with patch.object(flatpak, "module") as module:
                module.return_value.verify_refs.side_effect = ValueError(
                    "commit missing"
                )
                with self.assertRaises(ValueError):
                    flatpak.prepare_runtimes()
            commands = [c.args for c in run.call_args_list]
            lock = json.loads((flatpak.PACKAGING / "toolchain.lock.json").read_text())
            for commit in lock["refs"].values():
                self.assertTrue(
                    any("--commit=" + commit in command for command in commands)
                )
            self.assertFalse(any("--no-gpg-verify" in command for command in commands))

    def test_runtime_provisioning_refuses_regular_owner_environment(self):
        with (
            patch.dict(os.environ, {}, clear=True),
            patch.object(flatpak, "run") as run,
        ):
            with self.assertRaises(ValueError):
                flatpak.prepare_runtimes()
            run.assert_not_called()


class PayloadTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.checkout = self.root / "checkout"
        self.files = self.checkout / "files"
        paths = [
            "bin/cyrnava",
            "bin/QtWebEngineProcess",
            "share/cyrnava/frontend/dist/index.html",
            "share/cyrnava/backend/app/main.py",
            "lib/python3.13/site-packages/PySide6/__init__.py",
            f"share/applications/{flatpak.APP_ID}.desktop",
            f"share/metainfo/{flatpak.APP_ID}.metainfo.xml",
            f"share/icons/hicolor/256x256/apps/{flatpak.APP_ID}.png",
        ]
        for name in paths:
            path = self.files / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("synthetic structural fixture only")
        identity = self.files / "share/cyrnava/desktop/native/build_identity.py"
        identity.parent.mkdir(parents=True)
        identity.write_text(f'APP_ID = "{flatpak.APP_ID}"\nCHANNEL = "production"\n')
        self.identity = identity
        (self.checkout / "metadata").write_text(
            f"[Application]\nname={flatpak.APP_ID}\ncommand=cyrnava\n"
            "runtime=org.kde.Platform/x86_64/6.11\nsdk=org.kde.Sdk/x86_64/6.11\n"
            "base=app/io.qt.PySide.BaseApp/x86_64/6.11\n"
            "[Context]\nsockets=wayland;\ndevices=dri;\nshared=!network;\nfilesystems=!home;!host;\n"
        )
        manifest = json.loads(
            (flatpak.PACKAGING / (flatpak.APP_ID + ".json")).read_text()
        )
        with (self.checkout / "metadata").open("a") as stream:
            stream.write(
                "[Environment]\n"
                + "\n".join(
                    value.removeprefix("--env=")
                    for value in manifest["finish-args"]
                    if value.startswith("--env=")
                )
                + "\n"
            )

    def test_runtime_and_sandbox_environment_mismatch(self):
        path = self.checkout / "metadata"
        original = path.read_text()
        for changed in (
            original.replace(
                "org.kde.Platform/x86_64/6.11", "org.kde.Platform/x86_64/6.10"
            ),
            original + "QTWEBENGINE_DISABLE_SANDBOX=1\n",
        ):
            path.write_text(changed)
            with self.assertRaises(ValueError):
                flatpak.validate_payload(self.checkout)

    def test_valid_structural_payload(self):
        self.assertEqual(flatpak.validate_payload(self.checkout)["status"], "PASS")

    def test_bad_identity(self):
        self.identity.write_text(
            'APP_ID="org.cyrnava.CyrNava.Devel"\nCHANNEL="development"\n'
        )
        with self.assertRaisesRegex(ValueError, "identity"):
            flatpak.validate_payload(self.checkout)

    def test_missing_webengine_helper(self):
        (self.files / "bin/QtWebEngineProcess").unlink()
        with self.assertRaises(ValueError):
            flatpak.validate_payload(self.checkout)

    def test_network_permission_regression(self):
        path = self.checkout / "metadata"
        path.write_text(path.read_text().replace("!network", "network"))
        with self.assertRaises(ValueError):
            flatpak.validate_payload(self.checkout)

    def test_prohibited_packaged_file(self):
        (self.files / "personal.sqlite3").write_bytes(b"synthetic negative fixture")
        with self.assertRaisesRegex(ValueError, "Prohibited"):
            flatpak.validate_payload(self.checkout)

    def test_corrupt_bundle_never_creates_upload_directory(self):
        directory = self.root / "build"
        directory.mkdir()
        (directory / (flatpak.APP_ID + ".flatpak")).write_bytes(b"damaged")
        (directory / "result.json").write_text(
            json.dumps({"status": "PASS", "sha256": "wrong", "bytes": 7})
        )
        with self.assertRaises(ValueError):
            flatpak.audit_bundle(directory, self.root / "audit")
        self.assertFalse((self.root / "audit/artifacts").exists())

    def test_exported_bundle_audit_checks_provenance_and_only_then_stages_upload(self):
        # Command substitution is synthetic; this does not claim Flatpak execution.
        directory = self.root / "build"
        directory.mkdir()
        destination = self.root / "audit"
        destination.mkdir()
        bundle = directory / (flatpak.APP_ID + ".flatpak")
        bundle.write_bytes(b"synthetic bundle structural contract")
        inputs = {"version": "0.1.0", "runtime_lock": {}, "git_commit": "a" * 40}
        (directory / "build-inputs.json").write_text(json.dumps(inputs))
        (self.files / "share/cyrnava/build-inputs.json").write_text(json.dumps(inputs))
        inventory = flatpak.validate_payload(self.checkout)
        (directory / "package-inventory.json").write_text(json.dumps(inventory))
        (directory / "result.json").write_text(
            json.dumps(
                {
                    "status": "PASS",
                    "sha256": flatpak.sha(bundle),
                    "bytes": bundle.stat().st_size,
                    "ostree_commit": "b" * 64,
                }
            )
        )

        def output(*args):
            return "a" * 40 if args[0] == "git" else "b" * 64

        def run(*args):
            if "checkout" in args:
                import shutil

                shutil.copytree(self.checkout, destination / "bundle-checkout")

        with (
            patch.object(flatpak, "run", side_effect=run),
            patch.object(flatpak, "output", side_effect=output),
            patch.dict(os.environ, {"GITHUB_SHA": "a" * 40}),
        ):
            result = flatpak.audit_bundle(directory, destination)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            (destination / "artifacts" / bundle.name).read_bytes(), bundle.read_bytes()
        )
        self.assertIn(
            result["sha256"], (destination / "artifacts/SHA256SUMS").read_text()
        )


class BuildDirectoryTests(unittest.TestCase):
    def test_explicit_output_is_new_and_cannot_overlay_existing_files(self):
        builder = flatpak.module("build")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            destination = root / "output"
            with (
                patch.dict(os.environ, {"XDG_CACHE_HOME": str(root / "cache")}),
                patch.object(
                    sys,
                    "argv",
                    [
                        "build.py",
                        "--stage-only",
                        "--output-directory",
                        str(destination),
                    ],
                ),
                patch.object(builder, "stage"),
            ):
                self.assertEqual(builder.main(), 0)
                self.assertEqual(
                    json.loads((destination / "result.json").read_text())["status"],
                    "STAGED",
                )
                sentinel = destination / "preserve"
                sentinel.write_text("synthetic")
                with self.assertRaises(FileExistsError):
                    builder.main()
                self.assertEqual(sentinel.read_text(), "synthetic")

    def test_output_refuses_symlink_parent(self):
        builder = flatpak.module("build")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            link = root / "link"
            link.symlink_to(root, target_is_directory=True)
            with (
                patch.dict(os.environ, {"XDG_CACHE_HOME": str(root / "cache")}),
                patch.object(
                    sys,
                    "argv",
                    [
                        "build.py",
                        "--stage-only",
                        "--output-directory",
                        str(link / "output"),
                    ],
                ),
            ):
                with self.assertRaisesRegex(SystemExit, "Symlink"):
                    builder.main()


if __name__ == "__main__":
    unittest.main()
