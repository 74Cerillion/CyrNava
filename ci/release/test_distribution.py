"""P6 publication/transport/trust regressions; real GPG, disposable fake payloads.

OSTree verification is mocked ONLY in these unit fixtures, which are not real
repositories. Native accepted-artifact transport is executed separately.
"""

import contextlib
import fcntl
import io
import json
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core
import distribution
import key_ceremony
import native_distribution
import product_inventory
import real_update
import trust


class PublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="p6-")
        cls.root = Path(cls.temporary.name)
        cls.home = cls.root / "key"
        cls.fingerprint = core.make_key(cls.home)
        cls.key = cls.root / "public.gpg"
        cls.key.write_bytes(core.export_key(cls.home, cls.fingerprint))

    @classmethod
    def tearDownClass(cls):
        core.call("gpgconf", "--homedir", cls.home, "--kill", "gpg-agent")
        cls.temporary.cleanup()

    def setUp(self):
        self.case = Path(tempfile.mkdtemp(dir=self.root))
        self.public = self.case / "public"
        self.object = "repo/objects/ab/" + "c" * 62 + ".filez"
        (self.public / self.object).parent.mkdir(parents=True)
        (self.public / self.object).write_bytes(b"immutable synthetic payload")
        (self.public / "repo/summary").write_bytes(b"synthetic summary")
        self.seal()
        self.store = core.init_store(self.case / "store")
        self.destination = distribution.LocalDestination(self.store)
        self.native = patch.object(core, "verify_repository", return_value=[])
        self.native.start()
        self.addCleanup(self.native.stop)

    def seal(self):
        for name in ("manifest.json", "manifest.json.sig"):
            (self.public / name).unlink(missing_ok=True)
        core.seal(self.public, self.home, self.fingerprint)

    def plan(self):
        return distribution.plan(
            self.public, self.destination, self.key, self.fingerprint, self.case
        )

    def publish(self):
        return distribution.publish(
            self.public,
            self.destination,
            self.key,
            self.fingerprint,
            self.plan(),
            self.case,
        )

    def test_dry_run_verifies_without_activation_or_upload(self):
        value = self.plan()
        self.assertIsNone(self.destination.current())
        self.assertEqual(list((self.store / "generations").iterdir()), [])
        self.assertEqual(next(iter(value["files"])), self.object)
        self.assertEqual(value["deletions"], [])

    def test_destination_seal_and_hash_verified_after_activation(self):
        result = self.publish()
        self.assertEqual(result["generation"], core.sha(self.public / "manifest.json"))
        core.verify_seal(
            core.active_generation(self.store), self.key, self.fingerprint, self.case
        )

    def test_source_changed_after_review_rejected_without_activation(self):
        reviewed = self.plan()
        (self.public / "repo/summary").write_bytes(b"changed")
        self.seal()
        with self.assertRaisesRegex(core.Rejected, "plan changed"):
            distribution.publish(
                self.public,
                self.destination,
                self.key,
                self.fingerprint,
                reviewed,
                self.case,
            )
        self.assertIsNone(self.destination.current())

    def test_tamper_missing_and_unexpected_files_fail_closed(self):
        for fault in ("tamper", "missing", "extra"):
            with self.subTest(fault=fault):
                path = self.public / self.object
                original = path.read_bytes()
                if fault == "tamper":
                    path.write_bytes(b"damaged")
                elif fault == "missing":
                    path.unlink()
                else:
                    (self.public / "unlisted").write_bytes(b"unlisted")
                with self.assertRaises(core.Rejected):
                    self.plan()
                path.write_bytes(original)
                (self.public / "unlisted").unlink(missing_ok=True)
        self.assertIsNone(self.destination.current())

    def test_symlink_refused(self):
        (self.public / "leak").symlink_to(self.key)
        with self.assertRaises(core.Rejected):
            self.plan()

    def test_concurrent_publisher_rejected(self):
        reviewed = self.plan()
        with (self.store / ".lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(core.Rejected, "publisher"):
                self.destination.activate(
                    self.public,
                    self.key,
                    self.fingerprint,
                    reviewed["expected_previous"],
                )
        self.assertIsNone(self.destination.current())

    def test_compare_and_swap_under_lock_rejects_stale_publisher(self):
        self.publish()
        previous = self.destination.current()
        with self.assertRaisesRegex(core.Rejected, "conflict"):
            self.destination.activate(self.public, self.key, self.fingerprint, None)
        self.assertEqual(self.destination.current(), previous)

    def test_interrupted_activation_preserves_previous_and_retains_objects(self):
        self.publish()
        previous = self.destination.current()
        (self.public / "repo/summary").write_bytes(b"generation B")
        self.seal()
        with self.assertRaisesRegex(RuntimeError, "injected"):
            core.publish_local(
                self.public,
                self.store,
                self.key,
                self.fingerprint,
                before_activate=lambda: (_ for _ in ()).throw(RuntimeError("injected")),
            )
        self.assertEqual(self.destination.current(), previous)
        self.assertTrue((core.active_generation(self.store) / self.object).is_file())
        self.publish()
        self.assertNotEqual(self.destination.current(), previous)
        self.assertTrue((self.store / "generations" / previous).is_dir())

    def test_historical_objects_cannot_be_pruned(self):
        self.publish()
        (self.public / self.object).unlink()
        self.seal()
        with self.assertRaisesRegex(core.Rejected, "Historical objects"):
            self.plan()

    def test_get_head_hash_mime_and_cache_contract(self):
        self.publish()
        with distribution.loopback(
            self.destination, self.key, self.fingerprint
        ) as base:
            value = distribution.verify_http(base, self.plan())
        self.assertEqual(value["status"], "PASS")
        self.assertIn("immutable", distribution.response_policy(self.object)[1])
        self.assertIn("no-store", distribution.response_policy("repo/summary")[1])

    def test_missing_response_not_cached_and_new_object_becomes_available(self):
        self.publish()
        with distribution.loopback(
            self.destination, self.key, self.fingerprint
        ) as base:
            with self.assertRaises(urllib.error.HTTPError) as caught:
                urllib.request.urlopen(base + "repo/new")
            self.assertEqual(caught.exception.code, 404)
            self.assertIn("no-store", caught.exception.headers["Cache-Control"])
            (self.public / "repo/new").write_bytes(b"new")
            self.seal()
            self.publish()
            self.assertEqual(urllib.request.urlopen(base + "repo/new").read(), b"new")

    def test_unlisted_private_traversal_and_query_routes_refused(self):
        self.publish()
        with distribution.loopback(
            self.destination, self.key, self.fingerprint
        ) as base:
            for path in (
                "../.lock",
                "%2e%2e/public.gpg",
                "repo/summary?token=x",
                "manifest.json.sig",
            ):
                with self.subTest(path=path), self.assertRaises(urllib.error.HTTPError):
                    urllib.request.urlopen(base + path)

    def test_http_detects_corruption_and_stale_summary(self):
        self.publish()
        reviewed = self.plan()
        target = core.active_generation(self.store) / "repo/summary"
        with distribution.loopback(
            self.destination, self.key, self.fingerprint
        ) as base:
            target.write_bytes(b"corrupted")
            with self.assertRaises(urllib.error.HTTPError):
                distribution.verify_http(base, reviewed)

    def test_old_expected_http_snapshot_is_rejected_after_update(self):
        self.publish()
        old = self.plan()
        (self.public / "repo/summary").write_bytes(b"B")
        self.seal()
        self.publish()
        with distribution.loopback(
            self.destination, self.key, self.fingerprint
        ) as base:
            with self.assertRaisesRegex(core.Rejected, "checksum mismatch|Oversized"):
                distribution.verify_http(base, old)

    def test_client_disconnect_does_not_modify_active_generation(self):
        self.publish()
        previous = self.destination.current()
        with distribution.loopback(
            self.destination, self.key, self.fingerprint
        ) as base:
            request = urllib.request.Request(base + self.object)
            with urllib.request.urlopen(request) as response:
                response.read(1)
        self.assertEqual(self.destination.current(), previous)
        self.plan()

    def test_expired_key_and_wrong_identity_fail_closed(self):
        signature = self.public / "manifest.json.sig"
        manifest = self.public / "manifest.json"
        with self.assertRaisesRegex(core.Rejected, "Expired"):
            trust.verify_current_signature(
                self.key,
                self.fingerprint,
                manifest,
                signature,
                self.case,
                now=time.time() + 172800,
            )
        with self.assertRaises(core.Rejected):
            trust.verify_current_signature(
                self.key, "A" * 40, manifest, signature, self.case
            )

    def test_public_https_not_silently_enabled(self):
        with self.assertRaisesRegex(core.Rejected, "loopback"):
            distribution.verify_http("https://example.invalid/", self.plan())


class InventoryAndClientTests(unittest.TestCase):
    def test_rejected_real_update_cli_emits_final_failure_before_root_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proposal = root / "approval.json"
            proposal.write_text('{"owner_approved_for_disposable_P6_update":false}')
            stdout = io.StringIO()
            with (
                patch.object(
                    sys,
                    "argv",
                    [
                        "real_update.py",
                        "prepare",
                        "--root",
                        str(root / "pair"),
                        "--a-archive",
                        str(root / "a"),
                        "--b-archive",
                        str(root / "b"),
                        "--b-approval",
                        str(proposal),
                    ],
                ),
                contextlib.redirect_stdout(stdout),
            ):
                self.assertEqual(real_update.main(), 1)
            value = json.loads(stdout.getvalue())
            self.assertEqual(value["status"], "FAIL")
            self.assertTrue(value["complete"])
            self.assertFalse((root / "pair").exists())

    def test_native_setup_failure_emits_final_record_without_overwriting_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sentinel = root / "preserve"
            sentinel.write_text("synthetic")
            stdout = io.StringIO()
            with (
                patch.object(
                    sys,
                    "argv",
                    [
                        "native_distribution.py",
                        "--root",
                        str(root),
                        "--public",
                        str(root),
                        "--fingerprint",
                        "A" * 40,
                    ],
                ),
                contextlib.redirect_stdout(stdout),
            ):
                self.assertEqual(native_distribution.main(), 1)
            value = json.loads(stdout.getvalue())
            self.assertEqual(value["status"], "FAIL")
            self.assertTrue(value["complete"])
            self.assertEqual(sentinel.read_text(), "synthetic")
            self.assertFalse((root / "result.json").exists())

    def test_unapproved_real_B_fails_before_extracting_or_generating_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proposal = root / "approval.json"
            proposal.write_text('{"owner_approved_for_disposable_P6_update":false}')
            with (
                patch.object(core, "make_key") as key,
                self.assertRaisesRegex(core.Rejected, "approval is pending"),
            ):
                real_update.prepare(root / "pair", root / "a", root / "b", proposal)
            key.assert_not_called()
            self.assertFalse((root / "pair").exists())

    def test_real_B_cannot_substitute_same_source_or_change_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "approval.json"
            proposal = {
                "owner_approved_for_disposable_P6_update": True,
                "version": "0.1.0",
                "schema": 5,
                "entry": core.policy()["approved_staging_sources"][0],
            }
            path.write_bytes(core.encode(proposal))
            with self.assertRaisesRegex(core.Rejected, "Distinct"):
                real_update.approved_b(path)
            proposal["entry"] = dict(proposal["entry"], source_commit="a" * 40)
            proposal["schema"] = 6
            path.write_bytes(core.encode(proposal))
            with self.assertRaisesRegex(core.Rejected, "Version/schema"):
                real_update.approved_b(path)

    def test_native_gui_cannot_relax_security_to_compensate_for_missing_desktop(self):
        with tempfile.TemporaryDirectory() as directory:
            c = native_distribution.RuntimeClient(Path(directory) / "client")
            with patch.dict("os.environ", {}, clear=True):
                with self.assertRaisesRegex(core.Rejected, "Wayland desktop"):
                    real_update.desktop_environment(c)

    def test_ceremony_failure_has_final_record_and_removes_partial_private_homes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "ceremony"
            with patch.object(
                core, "gpg", side_effect=core.Rejected("injected setup failure")
            ):
                value = key_ceremony.rehearse(root)
            self.assertEqual(value["status"], "FAIL")
            self.assertTrue(value["complete"])
            self.assertEqual(value["checks"]["private_material_removed"], "PASS")
            self.assertFalse((root / "primary").exists())
            self.assertEqual(core.read_json(root / "result.json"), value)

    def test_private_cleanup_failure_cannot_be_reported_as_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "ceremony"
            with (
                patch.object(
                    core, "gpg", side_effect=core.Rejected("injected setup failure")
                ),
                patch.object(key_ceremony.shutil, "rmtree", side_effect=OSError),
            ):
                value = key_ceremony.rehearse(root)
            self.assertEqual(value["status"], "FAIL")
            self.assertEqual(value["checks"]["private_material_removed"], "FAIL")
            self.assertTrue(value["cleanup_attention_required"])
            self.assertTrue(value["complete"])

    def test_spdx_index_preserves_unknown_and_version_without_inference(self):
        value = product_inventory.spdx_packages(
            "PackageName: Qt\nSPDXID: SPDXRef-Qt\nPackageVersion: 6.11.1+dirty\n"
            "PackageLicenseConcluded: NOASSERTION\n"
        )
        self.assertEqual(value[0]["PackageLicenseConcluded"], "NOASSERTION")
        self.assertEqual(value[0]["PackageVersion"], "6.11.1+dirty")

    def test_inventory_records_metadata_native_notices_and_does_not_follow_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "binary").write_bytes(b"\x7fELFsynthetic")
            (root / "LICENSE").write_text("synthetic")
            (root / "linked").symlink_to("/etc/passwd")
            value = product_inventory.inspect_tree(root)
        self.assertEqual(len(value["native_elf_files"]), 1)
        self.assertEqual(value["symlinks_not_followed"], 1)
        self.assertEqual(len(value["notice_files"]), 1)

    def test_native_home_and_all_config_are_disposable(self):
        with tempfile.TemporaryDirectory() as directory:
            c = native_distribution.RuntimeClient(Path(directory) / "client")
            c.guard()
            self.assertEqual(Path(c.env["HOME"]).parent, c.root)
            self.assertNotIn("DBUS_SESSION_BUS_ADDRESS", c.env)
            self.assertNotIn("GITHUB_TOKEN", c.env)

    def test_runtime_setup_refuses_a_nonempty_client(self):
        with tempfile.TemporaryDirectory() as directory:
            c = native_distribution.RuntimeClient(Path(directory) / "client")
            with (
                patch.object(c, "run", return_value="existing"),
                patch.object(c, "command") as command,
            ):
                with self.assertRaisesRegex(core.Rejected, "not empty"):
                    c.runtimes()
                command.assert_not_called()

    def test_runtime_commit_mismatch_cannot_proceed(self):
        with tempfile.TemporaryDirectory() as directory:
            c = native_distribution.RuntimeClient(Path(directory) / "client")
            with (
                patch.object(c, "run", side_effect=["", "wrong"]),
                patch.object(c, "command"),
            ):
                with self.assertRaisesRegex(core.Rejected, "runtime commit mismatch"):
                    c.runtimes()

    def test_sandbox_failure_is_safe_and_never_disables_security(self):
        with tempfile.TemporaryDirectory() as directory:
            c = native_distribution.RuntimeClient(Path(directory) / "client")
            failed = subprocess.CompletedProcess(
                [], 1, b"", b"bwrap: namespace Operation not permitted SECRET"
            )
            with patch.object(subprocess, "run", return_value=failed) as run:
                with self.assertRaisesRegex(
                    core.Rejected, "sandbox-namespace-unavailable"
                ) as error:
                    c.command("launch", "run", core.APP_ID)
                self.assertNotIn("SECRET", str(error.exception))
                self.assertNotIn("--no-sandbox", run.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
