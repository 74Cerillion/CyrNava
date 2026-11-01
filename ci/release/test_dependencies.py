"""Independent runner setup and redacted failures; no network/signing rehearsal."""

import contextlib
import copy
import io
import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
import venv
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core
import github
import stage
import workflow_policy

INSTALL = (
    "python -m pip install --require-hashes --only-binary=:all: -r ci/requirements.lock"
)


class DependencyWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.workflow = workflow_policy.read_workflow(
            core.ROOT / ".github/workflows/release.yml"
        )

    def test_each_independent_python_job_bootstraps_its_own_locked_parser(self):
        for name, job in self.workflow["jobs"].items():
            with self.subTest(job=name):
                steps = job["steps"]
                setup = next(
                    i
                    for i, s in enumerate(steps)
                    if s.get("uses", "").startswith("actions/setup-python@")
                )
                install = next(
                    i for i, s in enumerate(steps) if INSTALL in s.get("run", "")
                )
                entry = next(
                    i
                    for i, s in enumerate(steps)
                    if "python ci/release/" in s.get("run", "")
                )
                self.assertLess(setup, install)
                self.assertLessEqual(install, entry)
                script = steps[entry]["run"]
                self.assertLess(
                    script.index(INSTALL), script.index("python ci/release/")
                )

    def test_missing_late_or_unpinned_install_rejected_for_either_job(self):
        for name in self.workflow["jobs"]:
            for defect in (
                "missing",
                "late",
                "no-hashes",
                "allow-source",
                "other-lock",
            ):
                changed = copy.deepcopy(self.workflow)
                step = next(
                    s
                    for s in changed["jobs"][name]["steps"]
                    if INSTALL in s.get("run", "")
                )
                if defect == "missing":
                    step["run"] = step["run"].replace(INSTALL, "true")
                elif defect == "late":
                    step["run"] = "python ci/release/preflight.py\n" + step["run"]
                else:
                    old, new = {
                        "no-hashes": ("--require-hashes", ""),
                        "allow-source": ("--only-binary=:all:", ""),
                        "other-lock": ("ci/requirements.lock", "unreviewed.txt"),
                    }[defect]
                    step["run"] = step["run"].replace(old, new)
                with (
                    self.subTest(job=name, defect=defect),
                    self.assertRaises(core.Rejected),
                ):
                    workflow_policy.validate(changed)


class FreshInterpreterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="p5b-no-parser-")
        cls.root = Path(cls.temporary.name)
        venv.EnvBuilder(with_pip=False).create(cls.root / "venv")
        cls.python = cls.root / "venv/bin/python"

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        self.work = Path(tempfile.mkdtemp(dir=self.root))
        self.entry = core.policy()["approved_staging_sources"][0]
        self.environment = {"PATH": os.defpath, "RUNNER_TEMP": str(self.work)}

    def arguments(self, output):
        return [
            "--live",
            "--source-commit",
            self.entry["source_commit"],
            "--ci-run-id",
            str(self.entry["ci_run_id"]),
            "--version",
            "0.1.0",
            "--channel",
            "staging",
            "--authorization-ref",
            self.entry["authorization_ref"],
            "--output",
            str(output),
        ]

    def test_actual_missing_yaml_import_fails_before_download_or_signing(self):
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=core.ROOT, text=True
        ).strip()
        environment = {
            **self.environment,
            "GITHUB_ACTIONS": "true",
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "GITHUB_REPOSITORY": "74Cerillion/CyrNava",
            "GITHUB_REF": "refs/heads/desktop/p2-production-integration",
            "GITHUB_ACTOR": "74Cerillion",
            "GITHUB_TRIGGERING_ACTOR": "74Cerillion",
            "GITHUB_RUN_ATTEMPT": "1",
            "GITHUB_SHA": commit,
            "GITHUB_WORKFLOW_SHA": commit,
            "GITHUB_WORKFLOW_REF": (
                "74Cerillion/CyrNava/.github/workflows/release.yml"
                "@refs/heads/desktop/p2-production-integration"
            ),
        }
        output = self.work / "out"
        sentinel = self.work / "release-processing"
        # Actual import/identity path, with tripwires on all later side effects.
        code = f"""
import importlib.util, pathlib, sys
assert importlib.util.find_spec('yaml') is None
sys.path.insert(0, {str(core.HERE)!r})
import stage, github, core
def forbidden(*args, **kwargs):
    pathlib.Path({str(sentinel)!r}).touch()
    raise AssertionError('Release processing reached without dependency')
github.check_environment = forbidden
github.live_evidence = forbidden
github.download = forbidden
core.extract_artifact = forbidden
core.make_key = forbidden
core.generate_repository = forbidden
sys.exit(stage.main())
"""
        result = subprocess.run(
            [self.python, "-c", code, *self.arguments(output)],
            cwd=core.ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        record = json.loads((output / "result.json").read_text())
        self.assertEqual(record, json.loads(result.stdout))
        self.assertEqual(record["error_type"], "ModuleNotFoundError")
        self.assertIn("ci/requirements.lock", record["error"])
        self.assertEqual(record["status"], "FAIL")
        self.assertTrue(record["complete"])
        self.assertEqual(record["steps"], [])
        self.assertFalse(sentinel.exists())
        self.assertEqual(list((output / "private").iterdir()), [])
        self.assertNotIn("Traceback", result.stderr)

    def test_failed_install_blocks_both_real_workflow_command_sequences(self):
        workflow = workflow_policy.read_workflow(
            core.ROOT / ".github/workflows/release.yml"
        )
        for name, job in workflow["jobs"].items():
            with self.subTest(job=name):
                work = self.work / name
                work.mkdir()
                sentinel = work / "release-processing"
                shim = work / "python"
                # Fail pip; run the failure recorder with real stdlib Python.
                shim.write_text(
                    "#!/bin/sh\n"
                    'if [ "$1" = "-m" ] && [ "$2" = "pip" ]; then exit 23; fi\n'
                    'if [ "$1" = "ci/release/stage.py" ] && '
                    '[ "$2" = "--setup-failed" ]; then\n'
                    f'  exec {shlex.quote(str(self.python))} "$@"\nfi\n'
                    f"touch {shlex.quote(str(sentinel))}\nexit 91\n"
                )
                shim.chmod(0o700)
                script = next(
                    s["run"] for s in job["steps"] if INSTALL in s.get("run", "")
                )
                environment = {
                    **self.environment,
                    "PATH": str(work) + os.pathsep + os.defpath,
                    "RUNNER_TEMP": str(work),
                    "RELEASE_SOURCE": self.entry["source_commit"],
                    "RELEASE_CI_RUN": str(self.entry["ci_run_id"]),
                    "RELEASE_VERSION": "0.1.0",
                    "RELEASE_CHANNEL": "staging",
                    "RELEASE_AUTHORIZATION": self.entry["authorization_ref"],
                }
                result = subprocess.run(
                    ["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", script],
                    cwd=core.ROOT,
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(sentinel.exists(), result.stderr)
                if name == "staging":
                    output = work / "cyrnava-p5b"
                    record = json.loads((output / "result.json").read_text())
                    self.assertEqual(record["stage"], "python-dependencies")
                    self.assertEqual(record["status"], "FAIL")
                    self.assertTrue(record["complete"])
                    self.assertIn(
                        "Hash-locked CI dependency installation failed", record["error"]
                    )
                    self.assertEqual(record["steps"], [])
                    self.assertFalse((output / "private").exists())

    def test_import_failure_details_are_not_copied_into_diagnostics(self):
        output = self.work / "redacted"
        failure = ModuleNotFoundError("SENSITIVE path or credential", name="SENSITIVE")
        stdout = io.StringIO()
        with (
            patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=True),
            patch.object(sys, "argv", ["stage.py", *self.arguments(output)]),
            patch.object(github, "check_execution", side_effect=failure),
            patch.object(github, "download") as download,
            patch.object(core, "make_key") as key,
            contextlib.redirect_stdout(stdout),
        ):
            self.assertEqual(stage.main(), 1)
        download.assert_not_called()
        key.assert_not_called()
        self.assertNotIn("SENSITIVE", stdout.getvalue())
        self.assertNotIn("SENSITIVE", (output / "result.json").read_text())
        self.assertEqual(
            json.loads(stdout.getvalue())["error_type"], "ModuleNotFoundError"
        )


if __name__ == "__main__":
    unittest.main()
