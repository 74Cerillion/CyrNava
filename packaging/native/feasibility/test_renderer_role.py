"""Renderer identity parsing/capture fixtures; no Qt or desktop execution."""

import contextlib
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location(
    "n1_role_probe", HERE / "sandbox_probe.py"
)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
spec = importlib.util.spec_from_file_location(
    "n1_role_supervisor", HERE / "run_probe.py"
)
supervisor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(supervisor)


class RendererRoleTests(unittest.TestCase):
    helper = Path("/synthetic candidate/QtWebEngineProcess")

    def test_nul_delimited_renderer_is_verified(self):
        raw = bytes(self.helper) + b"\0--type=renderer\0--lang=en\0"
        result = probe.renderer_role(raw, self.helper)
        self.assertTrue(result["verified"])
        self.assertEqual(result["format"], "nul-delimited-argv")

    def test_chromium_flattened_titles_are_verified_without_a_substring_test(self):
        for program in (bytes(self.helper), b"QtWebEngineProcess"):
            raw = program + b" --type=renderer --lang=en\0\0\0"
            with self.subTest(program=program):
                # The old check fails for precisely this documented representation.
                self.assertNotIn(b"--type=renderer", raw.split(b"\0"))
                result = probe.renderer_role(raw, self.helper)
                self.assertTrue(result["verified"])
                self.assertEqual(result["format"], "chromium-process-title")

    def test_non_renderer_ambiguous_embedded_and_unrecognized_roles_fail_closed(self):
        examples = [
            b"",
            b"\0\0",
            b"x" * 65537,
            bytes(self.helper) + b"\0--type=zygote\0",
            bytes(self.helper) + b"\0--type=renderer-extra\0",
            bytes(self.helper) + b"\0--type=renderer\0--type=zygote\0",
            bytes(self.helper) + b"\0--type=renderer\0--type=renderer\0",
            bytes(self.helper) + b"\0--type=renderer\0--type\0zygote\0",
            bytes(self.helper) + b"\0--url=https://synthetic/--type=renderer\0",
            bytes(self.helper) + b" --url=synthetic --type=renderer\0",
            b"unrecognized-program --type=renderer\0",
            b"QtWebEngineProcess --type=zygote --type=renderer\0",
            b"QtWebEngineProcess --type=renderer-extra\0",
        ]
        for raw in examples:
            with self.subTest(raw=raw[:90]):
                self.assertFalse(probe.renderer_role(raw, self.helper)["verified"])

    def test_raw_evidence_is_private_and_safe_record_does_not_contain_arguments(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "ci-output") as temporary:
            root = Path(temporary)
            raw = b"QtWebEngineProcess --type=renderer --synthetic-private-value=keep-local\0"
            (root / "cmdline").write_bytes(raw)
            private = root / "renderer.private"
            result = probe.capture_role(root, self.helper, private)
            self.assertEqual(private.read_bytes(), raw)
            self.assertEqual(private.stat().st_mode & 0o777, 0o600)
            self.assertEqual(
                result["renderer_cmdline_sha256"], hashlib.sha256(raw).hexdigest()
            )
            self.assertNotIn("keep-local", json.dumps(result))
            self.assertNotIn("synthetic-private-value", json.dumps(result))
            with self.assertRaises(FileExistsError):
                probe.capture_role(root, self.helper, private)
            self.assertEqual(private.read_bytes(), raw)

    def test_private_evidence_symlink_is_refused(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "ci-output") as temporary:
            root = Path(temporary)
            (root / "cmdline").write_bytes(b"QtWebEngineProcess --type=renderer\0")
            target = root / "preserved"
            target.write_bytes(b"preserved")
            link = root / "renderer.private"
            link.symlink_to(target)
            with self.assertRaises(OSError):
                probe.capture_role(root, self.helper, link)
            self.assertEqual(target.read_bytes(), b"preserved")

    def test_process_start_time_handles_parentheses_in_comm(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "ci-output") as temporary:
            root = Path(temporary)
            fields = ["R"] + ["0"] * 18 + ["123456"]
            (root / "stat").write_text("42 (synthetic (name)) " + " ".join(fields))
            self.assertEqual(probe.process_start_time(root), "123456")

    def test_adequate_sandbox_text_cannot_override_missing_process_role(self):
        record = {
            "qt_providers_coherent": True,
            "renderer_helper_matches": True,
            "renderer_role_verified": False,
            "process_status": {"NoNewPrivs": "1", "Seccomp": "2"},
            "namespace_separation": {"user": True, "pid": True, "net": True},
            "sandbox_diagnostic": [
                "Layer 1 Sandbox\tNamespace",
                "PID namespaces\tYes",
                "Network namespaces\tYes",
                "Seccomp-BPF sandbox\tYes",
                "You are adequately sandboxed.",
            ],
        }
        self.assertFalse(probe.security_pass(record))

    def test_record_prefix_requires_explicit_schema_mode_and_cannot_escape(self):
        for extra in (
            ["--record-prefix", "owner-system-schemas-role"],
            ["--ubuntu-system-schemas", "--record-prefix", "../../outside"],
        ):
            argv = [
                "probe",
                "--candidate",
                str(ROOT / "ci-output/synthetic"),
                "--owner-host",
                "--receipt-sha256",
                "0" * 64,
                *extra,
            ]
            with (
                patch.object(sys, "argv", argv),
                patch.object(supervisor.subprocess, "Popen") as process,
                contextlib.redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit),
            ):
                supervisor.main()
            process.assert_not_called()


if __name__ == "__main__":
    unittest.main()
