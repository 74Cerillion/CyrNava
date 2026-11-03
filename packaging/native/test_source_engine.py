"""Source-online trust/acquisition/compatibility fixtures; no network or GUI."""

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "source_engine_tests", ROOT / "desktop/install_engine.py"
)
engine = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(engine)
SPEC_OPS = importlib.util.spec_from_file_location(
    "source_operations_tests", ROOT / "desktop/native_operations.py"
)
operations = importlib.util.module_from_spec(SPEC_OPS)
SPEC_OPS.loader.exec_module(operations)


def sha(value):
    return hashlib.sha256(value).hexdigest()


class SourceEngineTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.source = self.base / "source without git"
        self.source.mkdir()
        names = {
            "install_engine.py": "desktop/install_engine.py",
            "native_operations.py": "desktop/native_operations.py",
            "native_profile_check.py": "desktop/native_profile_check.py",
            "launch.py": "packaging/native/launch.py",
            "provider_check.py": "packaging/native/provider_check.py",
            "apparmor_support.py": "packaging/native/apparmor_support.py",
            "bootstrap.c": "packaging/native/bootstrap.c",
            "system_schemas.py": "packaging/native/feasibility/run_probe.py",
            "backend_check.py": "packaging/native/feasibility/backend_check.py",
            "dependencies.json": "packaging/native/feasibility/dependencies.json",
            "requirements.lock": "packaging/native/feasibility/requirements.lock",
        }
        self.source_files = {}
        self.payload = {}
        for target, original in names.items():
            data = (ROOT / original).read_bytes()
            self.put_source(original, data)
            self.payload[target] = self.info(data)
        for original in (
            "backend/app/storage.py",
            "desktop/native/application.py",
            "desktop/native/installed_configuration.py",
            "frontend/src/App.tsx",
            "frontend/package.json",
            "frontend/package-lock.json",
        ):
            data = b"synthetic source\n"
            self.put_source(original, data)
            if original.startswith(("backend/", "desktop/")):
                self.payload["application/" + original] = self.info(data)
        for name in (
            "application/frontend/dist/index.html",
            "application/frontend/dist/assets/branding/cyrnava-256.png",
        ):
            self.payload[name] = self.info(b"synthetic generated output")
        self.payload["cyrnava-native"] = self.info(
            b"synthetic ELF identity", mode=0o700
        )
        self.archive = self.base / "local-application.zip"
        self.archive.write_bytes(b"synthetic archive; no extraction in context tests")
        self.inventory = self.base / "source-inventory.json"
        self.inventory.write_text(json.dumps({"format": 1, "files": self.source_files}))
        self.manifest_path = self.base / "manifest.json"
        self.manifest = {
            "format": 1,
            "kind": "candidate",
            "version": "0.1.0-source.1",
            "app_id": engine.CANDIDATE_ID,
            "target": "ubuntu-26.04-x86_64-wayland-cpython314",
            "archive_sha256": engine.digest(self.archive),
            "files": self.payload,
            "expanded_bytes": sum(x["bytes"] for x in self.payload.values()),
            "apparmor": engine.APPARMOR_CONTRACT,
            "maintenance": operations.CONTRACT,
            "installation_mode": "source-online",
            "source_snapshot_sha256": engine.digest(self.inventory),
            "source_contract": engine.source_contract(self.source_files),
        }
        self.save_manifest()

    @staticmethod
    def info(data, mode=0o600):
        return {"sha256": sha(data), "bytes": len(data), "mode": mode}

    def put_source(self, name, data):
        path = self.source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        self.source_files[name] = {"sha256": sha(data), "bytes": len(data)}

    def save_manifest(self):
        self.manifest_path.write_text(json.dumps(self.manifest))

    def context(self):
        return engine.source_context(
            self.source, self.inventory, self.archive, self.manifest_path
        )

    def test_source_zip_without_git_has_explicit_integrity_not_signature_trust(self):
        context = self.context()
        trust = engine.validate_source_context(
            context, self.archive, self.manifest_path
        )
        self.assertFalse((self.source / ".git").exists())
        self.assertEqual(trust["mode"], "source-online-reviewed-code")
        self.assertEqual(trust["production_signature"], "NOT CLAIMED")

    def test_context_cannot_be_claimed_by_plain_manifest_json(self):
        with self.assertRaisesRegex(ValueError, "Explicit reviewed source context"):
            engine.validate_source_context({}, self.archive, self.manifest_path)
        with self.assertRaisesRegex(ValueError, "explicit reviewed source context"):
            engine.SourceInstallContext(
                object(), self.source, self.inventory, self.archive, self.manifest_path
            )

    def test_legacy_archive_entrypoint_cannot_accept_source_flag(self):
        with (
            patch.object(engine, "host_supported"),
            patch.object(
                engine,
                "deployment_paths",
                return_value=(self.base / "profile", self.base / "applications"),
            ),
            patch.object(engine, "verify_signature") as signature,
            patch.object(engine, "setup_environment") as environment,
            self.assertRaisesRegex(ValueError, "explicit source entry point"),
        ):
            engine.install(
                self.archive,
                self.manifest_path,
                self.base / "install",
                signature="synthetic",
                key="synthetic",
                fingerprint="0" * 40,
            )
        signature.assert_not_called()
        environment.assert_not_called()

    def test_changed_source_manifest_archive_and_inventory_are_refused(self):
        for name in ("source", "manifest", "archive", "inventory"):
            with self.subTest(name=name):
                context = self.context()
                path = {
                    "source": self.source / "frontend/src/App.tsx",
                    "manifest": self.manifest_path,
                    "archive": self.archive,
                    "inventory": self.inventory,
                }[name]
                original = path.read_bytes()
                path.write_bytes(original + b" changed")
                with self.assertRaises(ValueError):
                    engine.validate_source_context(
                        context, self.archive, self.manifest_path
                    )
                path.write_bytes(original)

    def test_missing_source_inventory_member_and_payload_substitution_refused(self):
        for edit in ("missing", "payload", "wheelhouse"):
            with self.subTest(edit=edit):
                original = copy.deepcopy(self.manifest)
                if edit == "missing":
                    value = json.loads(self.inventory.read_text())
                    del value["files"]["desktop/native_operations.py"]
                    self.inventory.write_text(json.dumps(value))
                    self.manifest["source_snapshot_sha256"] = engine.digest(
                        self.inventory
                    )
                elif edit == "payload":
                    self.manifest["files"]["install_engine.py"]["sha256"] = "0" * 64
                else:
                    self.manifest["files"]["wheels/unapproved.whl"] = self.info(
                        b"unapproved"
                    )
                    self.manifest["expanded_bytes"] += len(b"unapproved")
                self.save_manifest()
                with self.assertRaises(ValueError):
                    self.context()
                self.manifest = original
                self.inventory.write_text(
                    json.dumps({"format": 1, "files": self.source_files})
                )
                self.manifest["source_snapshot_sha256"] = engine.digest(self.inventory)
                self.save_manifest()

    def test_source_symlink_escape_refused(self):
        path = self.source / "frontend/src/App.tsx"
        data = path.read_bytes()
        outside = self.base / "outside"
        outside.write_bytes(data)
        path.unlink()
        path.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "Symbolic link"):
            self.context()

    def official_release(self):
        release = self.base / "release"
        release.mkdir()
        for target, original in (
            ("dependencies.json", "dependencies.json"),
            ("requirements.lock", "requirements.lock"),
        ):
            (release / target).write_bytes(
                (ROOT / "packaging/native/feasibility" / original).read_bytes()
            )
        files, requirements = engine.source_online_requirements(release)
        self.assertEqual(len(files), 19)
        self.assertEqual(len(requirements.splitlines()), 19)
        self.assertTrue(
            all(
                line.startswith("https://files.pythonhosted.org/packages/")
                and " --hash=sha256:" in line
                for line in requirements.splitlines()
            )
        )
        return release

    def test_approved_official_nineteen_wheel_closure_matches_lock(self):
        self.official_release()

    def test_mirror_hash_and_incomplete_dependency_closure_refused(self):
        release = self.official_release()
        original = (release / "dependencies.json").read_bytes()
        for edit in (
            "mirror",
            "http",
            "credentials",
            "hash",
            "incomplete",
            "duplicate",
        ):
            value = json.loads(original)
            if edit == "mirror":
                value["files"][0]["url"] = value["files"][0]["url"].replace(
                    "files.pythonhosted.org", "mirror.invalid"
                )
            elif edit == "http":
                value["files"][0]["url"] = value["files"][0]["url"].replace(
                    "https:", "http:"
                )
            elif edit == "credentials":
                value["files"][0]["url"] = value["files"][0]["url"].replace(
                    "https://", "https://user:secret@"
                )
            elif edit == "hash":
                value["files"][0]["sha256"] = "0" * 64
            elif edit == "incomplete":
                value["files"].pop()
            else:
                value["files"][-1] = value["files"][0]
            (release / "dependencies.json").write_text(json.dumps(value))
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                engine.source_online_requirements(release)

    def test_source_frontend_output_can_vary_only_with_identical_inputs(self):
        old = copy.deepcopy(self.manifest)
        new = copy.deepcopy(old)
        new["files"]["application/frontend/dist/index.html"]["sha256"] = "1" * 64
        operations.compatible(engine, old, new)
        for key in ("frontend", "application", "runtime", "bootstrap"):
            changed = copy.deepcopy(new)
            changed["source_contract"][key + "_sha256"] = "2" * 64
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "inputs"):
                operations.compatible(engine, old, changed)

    def test_source_backend_bootstrap_and_dependency_bytes_remain_strict(self):
        for name in (
            "requirements.lock",
            "dependencies.json",
            "launch.py",
            "cyrnava-native",
            "application/backend/app/storage.py",
        ):
            changed = copy.deepcopy(self.manifest)
            changed["files"][name]["sha256"] = "3" * 64
            with (
                self.subTest(name=name),
                self.assertRaisesRegex(ValueError, "data/Qt/bootstrap"),
            ):
                operations.compatible(engine, self.manifest, changed)

    def test_legacy_compatibility_still_requires_frontend_output_byte_identity(self):
        old = copy.deepcopy(self.manifest)
        old.pop("installation_mode")
        new = copy.deepcopy(old)
        new["files"]["application/frontend/dist/index.html"]["sha256"] = "4" * 64
        with self.assertRaisesRegex(ValueError, "data/Qt/bootstrap"):
            operations.compatible(engine, old, new)
        with self.assertRaisesRegex(ValueError, "trust-mode transition"):
            operations.compatible(engine, old, self.manifest)

    def test_acquisition_failure_cannot_install_or_claim_success(self):
        release = self.official_release()
        calls = []

        def operation(_release, name, command, **_kwargs):
            calls.append(name)
            if name == "acquire-exact-official-wheels":
                for flag in (
                    "--isolated",
                    "--no-index",
                    "--no-deps",
                    "--no-cache-dir",
                    "--require-hashes",
                    "--only-binary=:all:",
                ):
                    self.assertIn(flag, list(map(str, command)))
                raise ValueError("synthetic acquisition refusal")

        with (
            patch.object(engine, "run_operation", side_effect=operation),
            self.assertRaisesRegex(ValueError, "acquisition refusal"),
        ):
            engine.setup_source_environment(release)
        self.assertEqual(calls, ["venv", "acquire-exact-official-wheels"])
        self.assertFalse((release / "dependency-acquisition.json").exists())

    def test_downloaded_content_hash_precedes_install_and_exact_receipt(self):
        for corrupt in (False, True):
            with self.subTest(corrupt=corrupt):
                release = self.base / (
                    "corrupt-release" if corrupt else "valid-release"
                )
                release.mkdir()
                declarations, contents = [], {}
                for index in range(19):
                    name = "fixture" + str(index)
                    filename = name + "-1.0-py3-none-any.whl"
                    content = ("synthetic wheel " + str(index)).encode()
                    contents[filename] = content
                    declarations.append(
                        {
                            "name": name,
                            "version": "1.0",
                            "filename": filename,
                            "bytes": len(content),
                            "sha256": sha(content),
                            "url": "https://files.pythonhosted.org/packages/fixture/"
                            + filename,
                        }
                    )
                (release / "dependencies.json").write_text(
                    json.dumps({"files": declarations})
                )
                (release / "requirements.lock").write_text(
                    "\n".join(
                        x["name"] + "==1.0 --hash=sha256:" + x["sha256"]
                        for x in declarations
                    )
                    + "\n"
                )
                calls = []

                def operation(_release, name, command, **_kwargs):
                    calls.append(name)
                    if name == "acquire-exact-official-wheels":
                        for filename, content in contents.items():
                            (release / "upstream-wheels" / filename).write_bytes(
                                b"?" * len(content) if corrupt else content
                            )
                    elif name == "providers":
                        (release / "providers.json").write_text(
                            '{"status":"PASS","provider_files":{".venv/synthetic":"fixture"}}'
                        )
                    elif name == "install-locked":
                        self.assertIn("--no-deps", command)
                        self.assertIn("--require-hashes", command)

                with patch.object(engine, "run_operation", side_effect=operation):
                    if corrupt:
                        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                            engine.setup_source_environment(release)
                        self.assertNotIn("install-locked", calls)
                        self.assertFalse(
                            (release / "dependency-acquisition.json").exists()
                        )
                    else:
                        self.assertEqual(
                            engine.setup_source_environment(release)["status"], "PASS"
                        )
                        record = engine.load(release / "dependency-acquisition.json")
                        self.assertEqual(record["files"], declarations)
                        self.assertEqual(
                            record["requirements_sha256"],
                            engine.digest(release / "requirements.lock"),
                        )


if __name__ == "__main__":
    unittest.main()
