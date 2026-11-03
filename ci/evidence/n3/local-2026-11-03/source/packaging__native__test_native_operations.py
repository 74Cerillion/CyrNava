"""N3 transaction regressions with disposable synthetic data; no GUI or signing."""

import contextlib
import fcntl
import importlib.util
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

import test_install_engine as baseline

ROOT = Path(__file__).resolve().parents[2]
engine = baseline.engine
spec = importlib.util.spec_from_file_location(
    "n3_operations_tests", ROOT / "desktop/native_operations.py"
)
operations = importlib.util.module_from_spec(spec)
spec.loader.exec_module(operations)


class MaintenanceTests(unittest.TestCase):
    make_archive = baseline.InstallTests.make_archive
    save_manifest = baseline.InstallTests.save_manifest
    install = baseline.InstallTests.install

    def setUp(self):
        baseline.InstallTests.setUp(self)
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(engine, "host_supported"))
        self.stack.enter_context(
            patch.object(
                engine, "setup_environment", side_effect=self.setup_environment
            )
        )
        self.stack.enter_context(
            patch.object(engine, "run_operation", side_effect=self.operation)
        )
        self.stack.enter_context(
            patch.object(operations, "inspect_profile", return_value={"status": "PASS"})
        )

    def setup_environment(self, release):
        (release / ".venv").mkdir()
        (release / ".venv/fake").write_bytes(b"synthetic provider")
        return {"provider_files": {".venv/fake": engine.digest(release / ".venv/fake")}}

    def operation(self, release, name, *_args, **_kwargs):
        if name == "synthetic-backend":
            (release / "backend-check.json").write_text('{"status":"PASS"}')

    def first(self):
        self.install()
        profile = self.root / "client/profile"
        profile.mkdir(parents=True, mode=0o700)
        (profile / "workspace").mkdir(mode=0o700)
        for name, data in {
            ".instance.lock": b"",
            "workspace/.engage.lock": b"",
            "workspace/synthetic-data": b"notes folders images",
            "desktop.json": b'{"port":19001}',
            "appearance-and-drafts": b"synthetic preference and unsaved draft",
        }.items():
            p = profile / name
            p.write_bytes(data)
            p.chmod(0o600)
        return operations.inventory(engine, profile)

    def next_package(self, version="0.1.0-n3.1"):
        self.make_archive(
            extra={
                "native_operations.py": (
                    ROOT / "desktop/native_operations.py"
                ).read_bytes(),
                "native_profile_check.py": (
                    ROOT / "desktop/native_profile_check.py"
                ).read_bytes(),
                "install_engine.py": b"actual new maintenance engine fixture\n",
            }
        )
        self.value.update(version=version, maintenance=operations.CONTRACT)
        self.save_manifest()

    def update(self, **options):
        return operations.update(
            engine,
            self.archive,
            self.manifest,
            self.root,
            disposable=True,
            candidate_sha256=engine.digest(self.manifest),
            **options,
        )

    def assert_profile(self, before):
        self.assertEqual(
            operations.inventory(engine, self.root / "client/profile"), before
        )

    def test_real_activation_preserves_every_profile_byte_and_old_release(self):
        before = self.first()
        old = engine.load(self.root / "current.json")
        self.next_package()
        result = self.update()
        self.assertEqual(result["status"], "PASS")
        self.assert_profile(before)
        current = engine.load(self.root / "current.json")
        self.assertNotEqual(current["release"], old["release"])
        self.assertEqual(current["previous"], old)
        engine.installed(self.root / "releases" / current["release"])
        self.assertTrue((self.root / "releases" / old["release"]).is_dir())
        self.assertEqual(
            operations.inventory(engine, Path(result["checkpoint"]) / "profile"), before
        )

    def test_supported_skipped_version_is_a_full_package(self):
        self.first()
        self.next_package("0.1.0-n3.9")
        self.assertEqual(self.update()["status"], "PASS")

    def test_same_artifact_reinstall_is_explicit_and_does_not_change_selection(self):
        self.first()
        self.next_package()
        self.update()
        before = (self.root / "current.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "reinstall"):
            self.update()
        self.assertEqual(self.update(reinstall=True)["status"], "PASS")
        self.assertEqual((self.root / "current.json").read_bytes(), before)

    def test_downgrade_and_changed_same_version_refused(self):
        self.first()
        old = (self.root / "current.json").read_bytes()
        for version in ("0.0.9", "0.1.0-n2.1"):
            self.next_package(version)
            with self.assertRaisesRegex(ValueError, "downgrade"):
                self.update()
            self.assertEqual((self.root / "current.json").read_bytes(), old)

    def test_data_or_Qt_or_security_input_change_refused(self):
        self.first()
        self.next_package()
        for name in (
            "requirements.lock",
            "application/desktop/native/application.py",
            "launch.py",
        ):
            original = self.value["files"][name]["sha256"]
            self.value["files"][name]["sha256"] = "0" * 64
            self.save_manifest()
            with self.assertRaisesRegex(ValueError, "data/Qt/bootstrap"):
                self.update()
            self.value["files"][name]["sha256"] = original
        self.assertFalse((self.root / "transaction.json").exists())

    def test_wrong_candidate_hash_or_archive_does_not_stage(self):
        self.first()
        self.next_package()
        with self.assertRaisesRegex(ValueError, "manifest checksum"):
            operations.update(
                engine,
                self.archive,
                self.manifest,
                self.root,
                disposable=True,
                candidate_sha256="0" * 64,
            )
        with self.archive.open("ab") as stream:
            stream.write(b"tampered")
        with self.assertRaisesRegex(ValueError, "Archive checksum"):
            self.update()
        self.assertFalse((self.root / "transaction.json").exists())

    def test_insufficient_space_preserves_active_data(self):
        before = self.first()
        self.next_package()
        with (
            patch.object(
                operations.shutil,
                "disk_usage",
                return_value=shutil._ntuple_diskusage(1, 1, 0),
            ),
            self.assertRaisesRegex(ValueError, "headroom"),
        ):
            self.update()
        self.assert_profile(before)
        self.assertFalse((self.root / "transaction.json").exists())

    def test_running_GUI_or_backend_refused_without_killing_it(self):
        self.first()
        self.next_package()
        for name in (".instance.lock", "workspace/.engage.lock"):
            with (self.root / "client/profile" / name).open("rb") as lock:
                fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
                with self.assertRaisesRegex(ValueError, "close all"):
                    self.update()
            self.assertFalse((self.root / "transaction.json").exists())

    def test_newer_or_invalid_schema_is_rejected_before_checkpoint(self):
        self.first()
        self.next_package()
        with (
            patch.object(
                operations,
                "inspect_profile",
                side_effect=ValueError("Unsupported schema"),
            ),
            self.assertRaisesRegex(ValueError, "schema"),
        ):
            self.update()
        self.assertFalse((self.root / "transaction.json").exists())

    def test_interruption_at_each_phase_recovers_exact_prior_selection(self):
        for phase in (
            "preparing-checkpoint",
            "checkpoint-verified",
            "verified",
            "activated",
        ):
            with self.subTest(phase=phase):
                # Fresh fixture paths for each independent interruption.
                self.root = self.base / ("interrupted-" + phase)
                self.make_archive()
                before = self.first()
                original = engine.load(self.root / "current.json")
                self.next_package()
                checkpoint = engine.journal_checkpoint

                def interrupt(
                    root, journal, current, checkpoint=checkpoint, phase=phase
                ):
                    checkpoint(root, journal, current)
                    if current == phase:
                        raise KeyboardInterrupt

                with (
                    patch.object(engine, "journal_checkpoint", side_effect=interrupt),
                    self.assertRaises(KeyboardInterrupt),
                ):
                    self.update()
                operations.recover(engine, self.root, disposable=True)
                self.assertEqual(engine.load(self.root / "current.json"), original)
                self.assert_profile(before)
                self.assertFalse((self.root / "transaction.json").exists())

    def test_recovery_refuses_changed_data_and_changed_activation(self):
        self.first()
        self.next_package()
        checkpoint = engine.journal_checkpoint

        def interrupt(root, journal, phase):
            checkpoint(root, journal, phase)
            if phase == "verified":
                raise KeyboardInterrupt

        with (
            patch.object(engine, "journal_checkpoint", side_effect=interrupt),
            self.assertRaises(KeyboardInterrupt),
        ):
            self.update()
        p = self.root / "client/profile/appearance-and-drafts"
        original = p.read_bytes()
        p.write_bytes(b"newer uncommitted draft")
        with self.assertRaisesRegex(ValueError, "Data changed"):
            operations.recover(engine, self.root, disposable=True)
        p.write_bytes(original)
        active = engine.load(self.root / "current.json")
        engine.durable(
            self.root / "current.json", dict(active, receipt_sha256="0" * 64)
        )
        with self.assertRaisesRegex(ValueError, "Changed selection"):
            operations.recover(engine, self.root, disposable=True)

    def test_uninstall_and_explicit_reinstall_keep_data_versions_and_policy(self):
        before = self.first()
        self.next_package()
        self.update()
        active = (self.root / "current.json").read_bytes()
        removed = operations.uninstall(engine, self.root, disposable=True)
        self.assertEqual(removed["program_activation"], "REMOVED")
        self.assertFalse((self.root / "current.json").exists())
        self.assertFalse((self.root / "launch.py").exists())
        self.assertTrue((self.root / "releases").is_dir())
        self.assert_profile(before)
        with self.assertRaisesRegex(ValueError, "Explicit reuse"):
            operations.restore_installation(engine, self.root, disposable=True)
        operations.restore_installation(
            engine, self.root, disposable=True, reuse_preserved_data=True
        )
        self.assertEqual((self.root / "current.json").read_bytes(), active)
        self.assert_profile(before)

    def test_uninstall_preserves_changed_menu_and_refuses_unknown_path(self):
        self.first()
        menu = next((self.root / "xdg/applications").iterdir())
        menu.write_bytes(b"owner edited menu")
        with self.assertRaisesRegex(ValueError, "Changed desktop"):
            operations.uninstall(engine, self.root, disposable=True)
        self.assertTrue((self.root / "launch.py").exists())
        target = {
            "path": str(self.root / "client/profile/appearance-and-drafts"),
            "before": None,
            "after": None,
            "mode": 0o600,
        }
        with self.assertRaisesRegex(ValueError, "Unexpected activation"):
            operations.apply_targets(
                engine, self.root, True, [target], direction="after"
            )

    def test_uninstall_interruption_can_restore_registration_without_data_restore(self):
        before = self.first()
        checkpoint = engine.journal_checkpoint

        def interrupt(root, journal, phase):
            checkpoint(root, journal, phase)
            if phase == "unregistered":
                raise KeyboardInterrupt

        with (
            patch.object(engine, "journal_checkpoint", side_effect=interrupt),
            self.assertRaises(KeyboardInterrupt),
        ):
            operations.uninstall(engine, self.root, disposable=True)
        operations.recover(engine, self.root, disposable=True)
        self.assertTrue((self.root / "current.json").exists())
        self.assertTrue((self.root / "launch.py").exists())
        self.assertFalse((self.root / "uninstalled.json").exists())
        self.assert_profile(before)

    def test_explicit_compatible_rollback_and_return_keep_data(self):
        before = self.first()
        old = engine.load(self.root / "current.json")
        self.next_package()
        self.update()
        newer = engine.load(self.root / "current.json")
        operations.rollback(engine, self.root, disposable=True)
        self.assertEqual(
            engine.load(self.root / "current.json")["release"], old["release"]
        )
        operations.rollback(engine, self.root, disposable=True)
        self.assertEqual(
            engine.load(self.root / "current.json")["release"], newer["release"]
        )
        self.assert_profile(before)

    def test_rollback_rejects_no_prior_release_or_changed_data_contract(self):
        self.first()
        with self.assertRaisesRegex(ValueError, "No verified prior"):
            operations.rollback(engine, self.root, disposable=True)
        self.next_package()
        self.update()
        with (
            patch.object(
                operations, "inspect_profile", side_effect=ValueError("newer database")
            ),
            self.assertRaisesRegex(ValueError, "newer database"),
        ):
            operations.rollback(engine, self.root, disposable=True)

    def test_profile_link_and_mount_escape_rejected_without_copying(self):
        self.first()
        profile = self.root / "client/profile"
        (profile / "outside").symlink_to(self.base / "never-delete")
        with self.assertRaisesRegex(ValueError, "Symbolic link"):
            operations.inventory(engine, profile)

    def test_normal_update_cannot_change_trusted_key_or_skip_expiry_checks(self):
        # No actual key or signature is created. Existing GPG verification and
        # signature-status regressions supply the cryptographic mechanism scope.
        self.value.update(kind="release", app_id=engine.APP_ID)
        self.save_manifest()
        signature, key = self.base / "signature.asc", self.base / "public.asc"
        profile = self.root / "client/profile"
        exists = Path.exists

        def isolated_desktop(path):
            if path.name == engine.APP_ID + ".desktop" and not path.is_relative_to(
                self.base
            ):
                return False
            return exists(path)

        with (
            patch.object(Path, "exists", isolated_desktop),
            patch.object(
                engine,
                "deployment_paths",
                return_value=(profile, self.root / "xdg/applications"),
            ),
            patch.object(
                engine,
                "verify_signature",
                return_value={"primary": "A" * 40, "signer": "A" * 40},
            ),
        ):
            engine.install(
                self.archive,
                self.manifest,
                self.root,
                signature=signature,
                key=key,
                fingerprint="A" * 40,
            )
        self.next_package()
        self.value.update(kind="release", app_id=engine.APP_ID)
        self.save_manifest()
        with (
            patch.object(
                engine,
                "deployment_paths",
                return_value=(profile, self.root / "xdg/applications"),
            ),
            patch.object(
                engine, "verify_signature", side_effect=ValueError("expired or revoked")
            ) as verify,
        ):
            with self.assertRaisesRegex(ValueError, "key transition"):
                operations.update(
                    engine,
                    self.archive,
                    self.manifest,
                    self.root,
                    signature=signature,
                    key=key,
                    fingerprint="B" * 40,
                )
            verify.assert_not_called()
            with self.assertRaisesRegex(ValueError, "expired or revoked"):
                operations.update(
                    engine,
                    self.archive,
                    self.manifest,
                    self.root,
                    signature=signature,
                    key=key,
                    fingerprint="A" * 40,
                )
            verify.assert_called_once()


if __name__ == "__main__":
    unittest.main()
