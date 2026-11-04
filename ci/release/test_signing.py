"""Real disposable GPG verification + local filesystem publication models.

Synthetic repository bytes in these tests are not native OSTree verification.
The separate stage.py owner/host procedure tests actual OSTree repositories.
"""

import fcntl
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core
import plan
import recovery


class SigningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="p5b-real-gpg-", dir="/tmp")
        cls.root = Path(cls.temporary.name)
        cls.home = cls.root / "key"
        cls.fingerprint = core.make_key(cls.home)
        cls.other = cls.root / "other-key"
        cls.other_fp = core.make_key(cls.other)
        cls.public_key = cls.root / "public.gpg"
        cls.public_key.write_bytes(core.export_key(cls.home, cls.fingerprint))

    @classmethod
    def tearDownClass(cls):
        for home in [cls.home, cls.other]:
            core.call("gpgconf", "--homedir", home, "--kill", "gpg-agent")
        cls.temporary.cleanup()

    def setUp(self):
        self.work = Path(tempfile.mkdtemp(prefix="case-", dir=self.root))

    def tearDown(self):
        shutil.rmtree(self.work)

    def public_tree(self):
        p = self.work / "public"
        p.mkdir()
        (p / "repo/objects/aa").mkdir(parents=True)
        (p / "repo/objects/aa/synthetic.filez").write_bytes(b"SYNTHETIC MODEL ONLY")
        (p / "repo/summary").write_bytes(b"synthetic summary")
        (p / "repo/summary.sig").write_bytes(
            b"synthetic OSTree envelope, not native verified"
        )
        (p / "staging-public.gpg").write_bytes(self.public_key.read_bytes())
        release = {
            "purpose": "p5b-staging",
            "signing_fingerprint": self.fingerprint,
            "source_commit": core.policy()["approved_staging_sources"][0][
                "source_commit"
            ],
            "version": "0.1.0",
        }
        (p / "release.json").write_bytes(core.encode(release))
        core.seal(p, self.home, self.fingerprint)
        return p

    def test_correct_key_signature_verified(self):
        p = self.work / "message"
        p.write_bytes(b"synthetic release manifest")
        core.sign(self.home, self.fingerprint, p)
        core.verify_signature(
            self.public_key, self.fingerprint, p, Path(str(p) + ".sig"), self.work
        )

    def test_wrong_key_or_unexpected_fingerprint_rejected(self):
        p = self.work / "message"
        p.write_text("synthetic")
        core.sign(self.home, self.fingerprint, p)
        wrong = self.work / "wrong.gpg"
        wrong.write_bytes(core.export_key(self.other, self.other_fp))
        for key, fp in [(wrong, self.other_fp), (self.public_key, self.other_fp)]:
            with self.subTest(fingerprint=fp), self.assertRaises(core.Rejected):
                core.verify_signature(key, fp, p, Path(str(p) + ".sig"), self.work)

    def test_tampered_content_rejected(self):
        p = self.work / "message"
        p.write_text("synthetic")
        core.sign(self.home, self.fingerprint, p)
        p.write_text("tampered")
        with self.assertRaises(core.Rejected):
            core.verify_signature(
                self.public_key, self.fingerprint, p, Path(str(p) + ".sig"), self.work
            )

    def test_invalid_detached_signature_rejected(self):
        p = self.work / "message"
        p.write_text("synthetic")
        core.sign(self.home, self.fingerprint, p)
        signature = Path(str(p) + ".sig")
        signature.write_bytes(b"invalid signature")
        with self.assertRaises(core.Rejected):
            core.verify_signature(
                self.public_key, self.fingerprint, p, signature, self.work
            )

    def test_missing_or_unmarked_credentials_fail_closed(self):
        home = self.work / "empty-key"
        home.mkdir(mode=0o700)
        with self.assertRaises((core.Rejected, FileNotFoundError)):
            core.staging_key(home, self.fingerprint)
        (home / ".p5b-staging-only").write_bytes(
            core.encode({"fingerprint": self.fingerprint, "uid": core.UID})
        )
        with self.assertRaises(core.Rejected):
            core.staging_key(home, self.fingerprint)

    def test_signer_directory_permissions_and_identity_enforced(self):
        with self.assertRaises(core.Rejected):
            core.staging_key(self.home, self.other_fp)
        self.home.chmod(0o755)
        try:
            with self.assertRaises(core.Rejected):
                core.staging_key(self.home, self.fingerprint)
        finally:
            self.home.chmod(0o700)

    def test_valid_descriptors_and_no_permanent_url(self):
        p = self.work / "descriptors"
        p.mkdir()
        core.descriptors(
            p, "https://staging.invalid/cyrnava/", self.public_key.read_bytes()
        )
        for name, section in [
            ("cyrnava-staging.flatpakrepo", "Flatpak Repo"),
            ("cyrnava-staging.flatpakref", "Flatpak Ref"),
        ]:
            c = core.configparser.ConfigParser()
            c.read(p / name)
            self.assertEqual(
                core.base64.b64decode(c[section]["GPGKey"]),
                self.public_key.read_bytes(),
            )
            self.assertIn("STAGING ONLY", c[section]["Title"])
        self.assertEqual(c[section]["Name"], core.APP_ID)
        for url in [
            "https://example.com/repo",
            "http://host.invalid/repo",
            "file://remote/path",
            "https://user:pass@host.invalid/repo",
            "https://host.invalid/repo?token=secret",
        ]:
            with self.subTest(url=url), self.assertRaises(core.Rejected):
                core.descriptors(p, url, self.public_key.read_bytes())

    def test_manifest_detects_missing_unlisted_or_modified_objects(self):
        p = self.public_tree()
        obj = p / "repo/objects/aa/synthetic.filez"
        original = obj.read_bytes()
        core.verify_seal(p, self.public_key, self.fingerprint, self.work)
        for action in [
            lambda: obj.unlink(),
            lambda: obj.write_bytes(b"modified"),
            lambda: (p / "unlisted").write_bytes(b"extra"),
        ]:
            obj.write_bytes(original)
            action()
            with self.assertRaises(core.Rejected):
                core.verify_seal(p, self.public_key, self.fingerprint, self.work)
            (p / "unlisted").unlink(missing_ok=True)

    def test_symlinks_and_private_material_excluded(self):
        p = self.public_tree()
        path = p / "unsafe"
        path.symlink_to(self.home)
        with self.assertRaises(core.Rejected):
            core.tree_manifest(p)
        path.unlink()
        path.write_bytes(b"-----BEGIN PGP PRIVATE KEY BLOCK-----")
        with self.assertRaises(core.Rejected):
            core.tree_manifest(p)
        self.assertFalse(any(x.name == "private-keys-v1.d" for x in p.rglob("*")))

    def test_public_export_contains_no_secret_packets(self):
        packets = core.gpg(self.home, "--list-packets", self.public_key)
        self.assertNotIn(b":secret key packet:", packets)
        self.assertIn(b":public key packet:", packets)
        self.assertIn("private-keys-v1.d/", (core.ROOT / ".gitignore").read_text())

    def test_local_publication_and_idempotent_repeat(self):
        p = self.public_tree()
        store = core.init_store(self.work / "store")
        first = core.publish_local(p, store, self.public_key, self.fingerprint)
        second = core.publish_local(p, store, self.public_key, self.fingerprint)
        self.assertEqual(first["generation"], second["generation"])
        self.assertEqual(core.active_generation(store).name, first["generation"])

    def test_failed_publication_keeps_previous_active_generation(self):
        p = self.public_tree()
        store = core.init_store(self.work / "store")
        first = core.publish_local(p, store, self.public_key, self.fingerprint)
        (p / "repo/summary").write_bytes(b"new synthetic summary")
        (p / "manifest.json").unlink()
        (p / "manifest.json.sig").unlink()
        core.seal(p, self.home, self.fingerprint)

        def fail():
            raise core.Rejected("simulated interruption before activation")

        with self.assertRaises(core.Rejected):
            core.publish_local(
                p, store, self.public_key, self.fingerprint, before_activate=fail
            )
        self.assertEqual(core.active_generation(store).name, first["generation"])

    def test_partial_copy_does_not_activate(self):
        p = self.public_tree()
        store = core.init_store(self.work / "store")
        with patch.object(
            core.shutil, "copytree", side_effect=OSError("synthetic disk full")
        ):
            with self.assertRaises(OSError):
                core.publish_local(p, store, self.public_key, self.fingerprint)
        self.assertIsNone(core.active_generation(store))

    def test_pruning_or_unsafe_rollback_rejected(self):
        p = self.public_tree()
        store = core.init_store(self.work / "store")
        first = core.publish_local(p, store, self.public_key, self.fingerprint)
        (p / "repo/objects/aa/synthetic.filez").unlink()
        (p / "manifest.json").unlink()
        (p / "manifest.json.sig").unlink()
        core.seal(p, self.home, self.fingerprint)
        with self.assertRaises(core.Rejected):
            core.publish_local(p, store, self.public_key, self.fingerprint)
        self.assertEqual(core.active_generation(store).name, first["generation"])

    def test_concurrent_publication_is_rejected(self):
        p = self.public_tree()
        store = core.init_store(self.work / "store")
        descriptor = os.open(store / ".lock", os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaises(core.Rejected):
                core.publish_local(p, store, self.public_key, self.fingerprint)
        finally:
            os.close(descriptor)

    def test_unmarked_or_unsafe_store_is_rejected(self):
        p = self.public_tree()
        store = self.work / "not-a-store"
        store.mkdir()
        with self.assertRaises((core.Rejected, FileNotFoundError)):
            core.publish_local(p, store, self.public_key, self.fingerprint)
        store = core.init_store(self.work / "safe-store")
        (store / "current").symlink_to("../../outside")
        with self.assertRaises(core.Rejected):
            core.active_generation(store)

    def test_recovery_does_not_touch_database_or_remove_client_objects(self):
        public = self.public_tree()
        store = core.init_store(self.work / "store")
        first = core.publish_local(public, store, self.public_key, self.fingerprint)
        result = recovery.activate_retained(
            store, first["generation"], self.public_key, self.fingerprint
        )
        self.assertEqual(result["database_action"], "NONE")
        with self.assertRaises(core.Rejected):
            recovery.activate_retained(
                store, "../../outside", self.public_key, self.fingerprint
            )

    def test_release_plan_creates_no_remote_or_tag(self):
        p = self.public_tree()
        value = plan.release_plan(p, self.public_key, self.fingerprint, self.work)
        self.assertFalse(value["production_publication_enabled"])
        self.assertFalse(value["github_release_created"])
        self.assertFalse(value["tag_created"])
        self.assertIn("redistribution licensing review", value["blocking_approvals"])


if __name__ == "__main__":
    unittest.main()
