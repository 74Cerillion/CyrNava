"""N2 standalone bootstrap export, synthetic files only; no package rebuild."""

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "n2_export_tests", ROOT / "packaging/native/build_candidate.py"
)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class ExportTests(unittest.TestCase):
    def fixture(self, root):
        source = root / "desktop/install_engine.py"
        source.parent.mkdir()
        source.write_text("# synthetic engine, never executed\n")
        shell = root / "packaging/native/install.sh"
        shell.parent.mkdir(parents=True)
        shell.write_text((ROOT / "packaging/native/install.sh").read_text())
        output = root / "candidate"
        output.mkdir()
        (output / "manifest.json").write_text(
            json.dumps(
                {
                    "files": {
                        "install_engine.py": {
                            "sha256": hashlib.sha256(source.read_bytes()).hexdigest()
                        }
                    }
                }
            )
        )
        return source, output

    def test_standalone_export_matches_archived_engine(self):
        with tempfile.TemporaryDirectory(
            dir=ROOT / "ci-output/native-n2-review-1"
        ) as temporary:
            root = Path(temporary)
            source, output = self.fixture(root)
            with patch.object(builder, "ROOT", root):
                builder.export_installer(output)
            self.assertEqual(
                source.read_bytes(), (output / "install_engine.py").read_bytes()
            )
            self.assertIn(
                '"$entry_dir/install_engine.py"', (output / "install.sh").read_text()
            )
            self.assertEqual(
                json.loads((output / "installer-checksums.json").read_text())["status"],
                "UNSIGNED",
            )

    def test_changed_engine_export_refused(self):
        with tempfile.TemporaryDirectory(
            dir=ROOT / "ci-output/native-n2-review-1"
        ) as temporary:
            root = Path(temporary)
            source, output = self.fixture(root)
            source.write_text("changed")
            with patch.object(builder, "ROOT", root), self.assertRaises(ValueError):
                builder.export_installer(output)
            self.assertFalse((output / "install_engine.py").exists())


if __name__ == "__main__":
    unittest.main()
