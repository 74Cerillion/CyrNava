"""N2 archive/trust/transaction regressions. No signing, GUI or normal installation."""

import hashlib
import importlib.util
import json
import os
import stat
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "n2_engine_tests", ROOT / "desktop/install_engine.py"
)
engine = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(engine)
REQUIRED = [
    "launch.py",
    "install_engine.py",
    "provider_check.py",
    "backend_check.py",
    "system_schemas.py",
    "requirements.lock",
    "dependencies.json",
    "application/desktop/native/application.py",
    "application/desktop/native/installed_configuration.py",
    "application/frontend/dist/index.html",
    "application/frontend/dist/assets/branding/cyrnava-256.png",
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


class InstallTests(unittest.TestCase):
    def setUp(self):
        parent = ROOT / "ci-output/native-n2-review-1/test-tmp"
        parent.mkdir(parents=True, exist_ok=True, mode=448)
        self.temporary = tempfile.TemporaryDirectory(dir=parent)
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / 'user install with spaces % $ " /installation'
        self.archive = self.base / "candidate.zip"
        self.manifest = self.base / "manifest.json"
        self.make_archive()

    def make_archive(self, extra=None, mode=None):
        contents = dict.fromkeys(REQUIRED, b"synthetic fixture\n")
        contents.update(extra or {})
        with zipfile.ZipFile(self.archive, "w") as target:
            for name, data in contents.items():
                entry = zipfile.ZipInfo(name)
                entry.create_system = 3
                entry.external_attr = (stat.S_IFREG | 384) << 16
                if mode is not None and name == REQUIRED[0]:
                    entry.external_attr = mode << 16
                target.writestr(entry, data)
        self.value = {
            "format": 1,
            "kind": "candidate",
            "version": "0.1.0-n2.1",
            "app_id": engine.CANDIDATE_ID,
            "target": "ubuntu-26.04-x86_64-wayland-cpython314",
            "archive_sha256": engine.digest(self.archive),
            "expanded_bytes": sum(map(len, contents.values())),
            "files": {
                p: {"sha256": sha(v), "bytes": len(v), "mode": 384}
                for p, v in contents.items()
            },
        }
        self.save_manifest()

    def save_manifest(self):
        self.manifest.write_text(json.dumps(self.value))

    def fixtures(self):
        stack = __import__("contextlib").ExitStack()
        stack.enter_context(patch.object(engine, "host_supported"))
        stack.enter_context(
            patch.object(
                engine,
                "setup_environment",
                return_value={"provider_files": {".venv/fake": "0" * 64}},
            )
        )

        def operation(release, name, *_args, **_kwargs):
            if name == "synthetic-backend":
                (release / "backend-check.json").write_text('{"status":"PASS"}')

        stack.enter_context(
            patch.object(engine, "run_operation", side_effect=operation)
        )
        return stack

    def install(self):
        return engine.install(
            self.archive,
            self.manifest,
            self.root,
            disposable=True,
            candidate_sha256=engine.digest(self.manifest),
        )

    def test_archive_exact_inventory_extracts(self):
        output = self.base / "extracted"
        output.mkdir()
        engine.extract(self.archive, output, engine.validate_manifest(self.value))
        self.assertEqual(
            len([p for p in output.rglob("*") if p.is_file()]), len(REQUIRED)
        )

    def test_archive_traversal_and_noncanonical_names(self):
        for name in (
            "../outside",
            "/tmp/outside",
            "a/../outside",
            "a//b",
            "a/./b",
            "a\\b",
            "x\ny",
            "C:foo",
        ):
            with self.subTest(name=name), self.assertRaises(ValueError):
                engine.member_name(name)

    def test_duplicate_zip_member_rejected(self):
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(self.archive, "a") as target:
                target.writestr(REQUIRED[0], b"duplicate")
        self.value["archive_sha256"] = engine.digest(self.archive)
        with self.assertRaises(ValueError):
            engine.extract(self.archive, self.base / "out", self.value)

    def test_symlink_and_special_members_rejected(self):
        for mode in (stat.S_IFLNK | 511, stat.S_IFIFO | 384, stat.S_IFDIR | 448):
            self.make_archive(mode=mode)
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                engine.extract(self.archive, self.base / "out", self.value)

    def test_wrong_archive_checksum_rejected(self):
        self.value["archive_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "Archive checksum"):
            engine.extract(self.archive, self.base / "out", self.value)

    def test_wrong_member_checksum_rejected(self):
        self.value["files"][REQUIRED[0]]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "checksum"):
            engine.extract(self.archive, self.base / "out", self.value)

    def test_oversized_inventory_rejected(self):
        self.value["expanded_bytes"] = engine.MAX_EXPANDED + 1
        with self.assertRaises(ValueError):
            engine.validate_manifest(self.value)

    def test_wrong_member_size_rejected(self):
        self.value["files"][REQUIRED[0]]["bytes"] += 1
        with self.assertRaises(ValueError):
            engine.extract(self.archive, self.base / "out", self.value)

    def test_missing_required_component_rejected(self):
        del self.value["files"]["provider_check.py"]
        self.value["expanded_bytes"] -= len(b"synthetic fixture\n")
        with self.assertRaisesRegex(ValueError, "component missing"):
            engine.validate_manifest(self.value)

    def test_wrong_target_and_identity_rejected(self):
        for key, value in (
            ("target", "another-platform"),
            ("app_id", engine.APP_ID),
            ("version", "../0.1.0"),
        ):
            edited = dict(self.value, **{key: value})
            with self.subTest(key=key), self.assertRaises(ValueError):
                engine.validate_manifest(edited)

    def test_manifest_duplicate_keys_rejected(self):
        self.manifest.write_text('{"format":1,"format":2}')
        with self.assertRaisesRegex(ValueError, "Duplicate JSON"):
            engine.load(self.manifest)

    def test_symlink_parent_rejected(self):
        (self.base / "link").symlink_to(self.base, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "Symbolic link"):
            engine.checked_path(self.base / "link/x")

    def test_hardlinked_input_rejected(self):
        linked = self.base / "hardlink"
        os.link(self.manifest, linked)
        with self.assertRaises(ValueError):
            engine.regular(linked)

    def test_disposable_path_cannot_escape_repository(self):
        for path in (Path("/tmp/unapproved"), ROOT / "ci-output/a/../../outside"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                engine.deployment_paths(path, True)

    def test_existing_directory_permissions_are_not_changed(self):
        self.root.mkdir(parents=True)
        self.root.chmod(493)
        with self.assertRaisesRegex(ValueError, "Private directory"):
            engine.private_directory(self.root)
        self.assertEqual(stat.S_IMODE(self.root.stat().st_mode), 493)

    def test_wrong_candidate_digest_refused_before_dependencies(self):
        with self.fixtures(), patch.object(engine, "setup_environment") as setup:
            with self.assertRaisesRegex(ValueError, "manifest checksum"):
                engine.install(
                    self.archive,
                    self.manifest,
                    self.root,
                    disposable=True,
                    candidate_sha256="0" * 64,
                )
            setup.assert_not_called()
        self.assertFalse((self.root / "current.json").exists())

    def test_unsigned_release_refused(self):
        self.value.update(kind="release", app_id=engine.APP_ID)
        self.save_manifest()
        with (
            self.fixtures(),
            patch.object(
                engine,
                "deployment_paths",
                return_value=(self.base / "profile", self.base / "menu"),
            ),
            self.assertRaisesRegex(ValueError, "signature required"),
        ):
            engine.install(self.archive, self.manifest, self.root)

    def test_checksum_candidate_cannot_be_normal_install(self):
        with (
            self.fixtures(),
            patch.object(
                engine,
                "deployment_paths",
                return_value=(self.base / "profile", self.base / "menu"),
            ),
            self.assertRaisesRegex(ValueError, "kind mismatch"),
        ):
            engine.install(
                self.archive,
                self.manifest,
                self.root,
                candidate_sha256=engine.digest(self.manifest),
            )

    def test_successful_transaction_and_desktop_quoting(self):
        with self.fixtures():
            result = self.install()
        self.assertEqual(result["status"], "PASS")
        self.assertFalse((self.root / "transaction.json").exists())
        self.assertFalse(Path(result["profile"]).exists())
        self.assertTrue((self.root / "launch.py").is_file())
        completed = subprocess.run(
            ["desktop-file-validate", result["desktop"]],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_desktop_command_accepts_normal_venv_interpreter_link(self):
        with self.fixtures():
            result = self.install()
        release = Path(result["release"])
        (release / ".venv/bin").mkdir(parents=True)
        (release / ".venv/bin/python").symlink_to("/usr/bin/python3.14")
        text = engine.desktop_entry(release, engine.CANDIDATE_ID, True)
        self.assertNotIn(b".venv/bin/python", text)
        self.assertIn(b"Exec=/usr/bin/python3.14", text)

    def test_existing_application_identity_is_preserved(self):
        menu = self.root / "xdg/applications"
        menu.mkdir(parents=True, mode=448)
        self.root.chmod(448)
        desktop = menu / (engine.CANDIDATE_ID + ".desktop")
        desktop.write_text("owner registration")
        with self.fixtures(), self.assertRaisesRegex(ValueError, "Existing desktop"):
            self.install()
        self.assertEqual(desktop.read_text(), "owner registration")

    def test_failed_prerequisite_cannot_activate(self):
        with (
            self.fixtures(),
            patch.object(
                engine,
                "setup_environment",
                side_effect=ValueError("Missing OS library"),
            ),
            self.assertRaisesRegex(ValueError, "Missing OS"),
        ):
            self.install()
        self.assertFalse((self.root / "current.json").exists())
        self.assertTrue((self.root / "transaction.json").exists())

    def test_interruptions_at_all_journal_phases_recover(self):
        original = engine.journal_checkpoint
        for phase in ("staging", "verified", "activated", "desktop-registered"):
            root = self.base / ("interrupt-" + phase)

            def interrupted(target, journal, actual, expected=phase):
                original(target, journal, actual)
                if actual == expected:
                    raise KeyboardInterrupt

            with (
                self.subTest(phase=phase),
                self.fixtures(),
                patch.object(engine, "journal_checkpoint", side_effect=interrupted),
                self.assertRaises(KeyboardInterrupt),
            ):
                engine.install(
                    self.archive,
                    self.manifest,
                    root,
                    disposable=True,
                    candidate_sha256=engine.digest(self.manifest),
                )
            self.assertTrue((root / "transaction.json").exists())
            self.assertEqual(engine.recover(root, disposable=True)["status"], "PASS")
            self.assertFalse((root / "current.json").exists())
            self.assertFalse((root / "launch.py").exists())
            self.assertFalse(
                (
                    root / "xdg/applications" / (engine.CANDIDATE_ID + ".desktop")
                ).exists()
            )

    def test_changed_recovery_target_preserved(self):
        original = engine.journal_checkpoint

        def interrupted(root, journal, phase):
            original(root, journal, phase)
            if phase == "desktop-registered":
                raise KeyboardInterrupt

        with (
            self.fixtures(),
            patch.object(engine, "journal_checkpoint", side_effect=interrupted),
            self.assertRaises(KeyboardInterrupt),
        ):
            self.install()
        (self.root / "launch.py").write_text("changed by owner")
        with self.assertRaisesRegex(ValueError, "Changed transaction"):
            engine.recover(self.root, disposable=True)
        self.assertTrue((self.root / "current.json").exists())
        self.assertEqual((self.root / "launch.py").read_text(), "changed by owner")

    def test_shared_lock_rejects_concurrent_install_and_start(self):
        with (
            engine.installation_lock(self.root),
            self.assertRaises(BlockingIOError),
            engine.installation_lock(self.root),
        ):
            self.fail("Concurrent operation acquired exclusive lock")

    def test_existing_profile_and_active_installation_preserved(self):
        with self.fixtures():
            self.install()
            current = (self.root / "current.json").read_bytes()
            with self.assertRaisesRegex(ValueError, "Existing installation"):
                self.install()
            self.assertEqual((self.root / "current.json").read_bytes(), current)

    def test_low_disk_stops_before_staging(self):
        with (
            self.fixtures(),
            patch.object(
                engine.shutil,
                "disk_usage",
                return_value=type("Disk", (), {"free": 1})(),
            ),
            self.assertRaisesRegex(ValueError, "headroom"),
        ):
            self.install()
        self.assertFalse(self.root.exists())

    def test_pip_is_offline_hash_locked_and_final_location(self):
        self.root.mkdir(parents=True, mode=448)
        (self.root / "providers.json").write_text('{"status":"PASS"}')
        with patch.object(engine, "run_operation") as run:
            engine.setup_environment(self.root)
        command = run.call_args_list[1].args[2]
        for option in (
            "--no-index",
            "--require-hashes",
            "--only-binary=:all:",
            "--no-cache-dir",
        ):
            self.assertIn(option, command)
        self.assertEqual(command[0], self.root / ".venv/bin/python")

    def test_system_bootstrap_reexecs_only_verified_private_interpreter(self):
        release = self.root / "releases/0.1.0-n2.1-1234567890abcdef"
        with (
            patch.object(engine, "host_supported"),
            patch.object(engine, "installed", return_value=({}, {"kind": "candidate"})),
            patch.object(engine.os, "execv", side_effect=SystemExit(0)) as execute,
            self.assertRaises(SystemExit),
        ):
            engine.launch(release, check_only=True)
        self.assertEqual(execute.call_args.args[0], str(release / ".venv/bin/python"))
        self.assertEqual(
            execute.call_args.args[1],
            [
                str(release / ".venv/bin/python"),
                "-B",
                "-I",
                str(self.root / "launch.py"),
                "--check",
            ],
        )

    def test_host_abi_and_unsafe_override_refused(self):
        with (
            patch.object(engine.sys, "version_info", (3, 12)),
            self.assertRaisesRegex(ValueError, "CPython"),
        ):
            engine.host_supported()
        with (
            patch.dict(os.environ, {"QTWEBENGINE_DISABLE_SANDBOX": "1"}),
            patch.object(engine.sys, "version_info", (3, 14)),
            self.assertRaisesRegex(ValueError, "override"),
        ):
            engine.host_supported()


class TrustTests(unittest.TestCase):
    primary = "A" * 40
    signer = "B" * 40

    def evidence(self):
        identities = {
            p: [kind, "u", "", "", "", "100", "300", "", "", ""]
            for p, kind in ((self.primary, "pub"), (self.signer, "sub"))
        }
        status = f"[GNUPG:] VALIDSIG {self.signer} 1970-01-01 120 0 4 0 1 10 00 {self.primary}\n"
        return (status, identities)

    def test_valid_status_and_subkey_identity(self):
        status, keys = self.evidence()
        self.assertEqual(
            engine.signature_status(status, keys, self.primary, 200)["signer"],
            self.signer,
        )

    def test_wrong_primary_rejected(self):
        status, keys = self.evidence()
        with self.assertRaises(ValueError):
            engine.signature_status(status, keys, "C" * 40, 200)

    def test_expired_revoked_invalid_status_rejected(self):
        status, keys = self.evidence()
        for code in (
            "BADSIG",
            "ERRSIG",
            "EXPKEYSIG",
            "EXPSIG",
            "REVKEYSIG",
            "KEYREVOKED",
            "KEYEXPIRED",
            "SIGEXPIRED",
            "NO_PUBKEY",
        ):
            with self.subTest(code=code), self.assertRaises(ValueError):
                engine.signature_status(
                    status + "[GNUPG:] " + code + " detail\n", keys, self.primary, 200
                )

    def test_expired_or_future_primary_and_subkey_rejected(self):
        for identity in (self.primary, self.signer):
            for column, value in ((1, "r"), (6, "150"), (5, "250")):
                status, keys = self.evidence()
                keys[identity][column] = value
                with (
                    self.subTest(identity=identity, column=column),
                    self.assertRaises(ValueError),
                ):
                    engine.signature_status(status, keys, self.primary, 200)

    def test_missing_duplicate_or_weak_valid_signature_rejected(self):
        status, keys = self.evidence()
        for invalid in (
            "",
            status + status,
            status.replace(" 10 00 ", " 2 00 "),
            status.replace(" 120 0 ", " 250 0 "),
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                engine.signature_status(invalid, keys, self.primary, 200)

    def test_gpg_failure_never_returns_verified_trust(self):
        parent = ROOT / "ci-output/native-n2-review-1"
        with tempfile.TemporaryDirectory(dir=parent) as temp:
            base = Path(temp)
            for name in ("manifest", "signature", "public"):
                (base / name).write_text("not a signed release")
            with self.assertRaises(subprocess.CalledProcessError):
                engine.verify_signature(
                    base / "manifest",
                    base / "signature",
                    base / "public",
                    self.primary,
                    base,
                )


if __name__ == "__main__":
    unittest.main()
