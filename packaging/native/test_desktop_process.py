"""Real GIO Exec expansion/child ownership with a synthetic non-GUI executable."""

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


engine = module("n2_desktop_fixture_engine", "desktop/install_engine.py")
adapter = module("n2_desktop_fixture_adapter", "packaging/native/desktop_process.py")


class DesktopTests(unittest.TestCase):
    def test_gio_expands_quoted_paths_and_returns_real_child_status(self):
        parent = ROOT / "ci-output/native-n2-review-1/test-tmp"
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as temporary:
            root = Path(temporary) / 'spaces % dollars $ and "quotes"'
            root.mkdir(mode=0o700)
            script = root / "synthetic.py"
            script.write_text(
                "import os,sys,json\nprint(json.dumps({'argv':sys.argv,'pid':os.getpid(),'session':os.getsid(0)}),flush=True)\nsys.exit(7)\n"
            )
            python = root / "python"
            python.symlink_to("/usr/bin/python3.14")
            desktop = root / "fixture.desktop"
            desktop.write_text(
                "[Desktop Entry]\nType=Application\nName=N2 non-GUI fixture\nTerminal=false\n"
                + "Exec=/usr/bin/python3.14"
                + " -I -B "
                + engine.desktop_quote(script)
                + "\n"
            )
            with (root / "child.log").open("wb") as log:
                child = adapter.DesktopProcess(desktop, dict(os.environ), log)
                self.assertEqual(child.wait(5), 7)
                self.assertEqual(child.poll(), 7)
            record = json.loads((root / "child.log").read_text())
            self.assertEqual(record["argv"], [str(script)])
            self.assertEqual(record["pid"], child.pid)
            self.assertEqual(record["session"], child.pid)

    def test_missing_entry_refused_without_child(self):
        with open(os.devnull, "wb") as log, self.assertRaises(ValueError):
            adapter.DesktopProcess(
                ROOT / "ci-output/nonexistent-n2-entry.desktop", dict(os.environ), log
            )


if __name__ == "__main__":
    unittest.main()
