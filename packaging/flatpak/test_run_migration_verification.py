import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

SPEC = importlib.util.spec_from_file_location(
    "p3_supervisor", Path(__file__).with_name("run_migration_verification.py")
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


@pytest.mark.parametrize(
    "failure", [None, "missing", "incomplete", "nonzero", "failed-check"]
)
@pytest.mark.parametrize("resume", [False, True])
def test_supervisor_requires_complete_success(monkeypatch, tmp_path, failure, resume):
    monkeypatch.setattr(module.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(module, "uuid4", lambda: SimpleNamespace(hex="a" * 32))
    root = (
        tmp_path
        / ".var/app/org.cyrnava.CyrNava.Devel/data/p3-verification/run-aaaaaaaaaaaa"
    )
    root.mkdir(parents=True)
    if resume:
        for phase in ("prepare", "import"):
            (root / (phase + ".json")).write_text(
                json.dumps(
                    {
                        "phase": phase,
                        "status": "PASS",
                        "complete": True,
                        "checks": {key: "PASS" for key in module.REQUIRED[phase]},
                    }
                )
            )
        (root / "verify.json").write_text('{"status": "FAIL"}')
    calls = []

    class Child:
        returncode = 0

        def __init__(self, command, **kwargs):
            self.phase = command[-2]
            calls.append(self.phase)

        def communicate(self, helper, timeout):
            assert b"configuration()" in helper
            if failure == "nonzero":
                self.returncode = 139
            if failure == "missing":
                return
            record = {
                "phase": self.phase,
                "status": "PASS",
                "complete": failure != "incomplete",
                "checks": {
                    key: "FAIL" if failure == "failed-check" else "PASS"
                    for key in module.REQUIRED[self.phase]
                },
            }
            (root / (self.phase + ".json")).write_text(json.dumps(record))

        def poll(self):
            return self.returncode

    monkeypatch.setattr(module.subprocess, "Popen", Child)
    assert module.main("run-aaaaaaaaaaaa" if resume else None) == (
        0 if failure is None else 1
    )
    record = json.loads((root / "supervisor-result.json").read_text())
    assert record["status"] == ("PASS" if failure is None else "FAIL")
    assert len(calls) == ((3 if resume else 5) if failure is None else 1)
    if resume:
        assert calls[0] == "edit"
        assert json.loads(
            (Path(record["resumed_from"]) / "verify.json").read_text()
        ) == {"status": "FAIL"}


def test_development_snapshot_excludes_diagnostic_evidence_only(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "p3_prepare", Path(__file__).with_name("prepare.py")
    )
    prepare = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prepare)
    source = tmp_path / "native"
    source.mkdir()
    (source / "application.py").write_text("# native code")
    evidence = source / "evidence"
    evidence.mkdir()
    (evidence / "test.log").write_text("private diagnostic")
    output = tmp_path / "snapshot"
    prepare.snapshot(source, output, excluded={"evidence"})
    assert (output / "application.py").is_file()
    assert not (output / "evidence").exists()
    (source / "unsafe.log").write_text("must reject")
    with pytest.raises(ValueError, match="User data or secrets"):
        prepare.snapshot(source, tmp_path / "rejected", excluded={"evidence"})


def test_resume_rejects_missing_portal_evidence(monkeypatch, tmp_path):
    monkeypatch.setattr(module.Path, "home", lambda: tmp_path)
    with pytest.raises(FileNotFoundError):
        module.main("run-aaaaaaaaaaaa")
    with pytest.raises(ValueError, match="Invalid disposable"):
        module.main("../real-profile")
