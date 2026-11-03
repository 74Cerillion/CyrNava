"""Independent N3 auditor bootstrap/schema tests; no GUI or application fixture PASS."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class IndependentAuditorTests(unittest.TestCase):
    def test_isolated_subprocess_resolves_packaged_backend_and_refuses_newer_schema(
        self,
    ):
        parent = ROOT / "ci-output/native-n3-local-1/auditor-fixtures"
        parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as tmp:
            base = Path(tmp)
            application = base / "application"
            package = application / "backend/app"
            package.mkdir(parents=True)
            (package / "__init__.py").write_text("")
            migration = package / "migration.py"
            profile = base / "profile"
            (profile / "workspace").mkdir(parents=True)
            (profile / "workspace/engage.sqlite3").write_bytes(b"synthetic fixture")
            (profile / "desktop.json").write_text('{"port":19001}')
            recoveries = profile / "workspaces"
            recoveries.mkdir()
            identifier = "a" * 32
            (recoveries / ("migration-" + identifier + ".json")).write_text(
                '{"status":"activated"}'
            )
            (recoveries / ("pre-migration-" + identifier + ".cyrnava")).write_bytes(
                b"retained synthetic backup"
            )
            command = [
                sys.executable,
                "-B",
                "-I",
                str(ROOT / "desktop/native_profile_check.py"),
                "--application",
                str(application),
                "--profile",
                str(profile),
            ]
            for schema in (5, 6):
                migration.write_text(
                    f'def inspect(path): return {{"schema":{schema},"counts":{{"notes":0,"folders":0,"assets":0}}}}\n'
                )
                output = base / f"schema-{schema}.json"
                result = subprocess.run(
                    command + ["--output", str(output)],
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
                if schema == 5:
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(json.loads(output.read_bytes())["status"], "PASS")
                else:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertFalse(output.exists())
                    self.assertIn("supports schema 5", result.stderr)


if __name__ == "__main__":
    unittest.main()
