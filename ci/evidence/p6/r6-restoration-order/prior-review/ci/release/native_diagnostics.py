"""P6 child-bootstrap evidence; raw output stays private, never in public logs."""

import base64
import hashlib
import json
import os
import re
import subprocess
from uuid import uuid4

import core
import progress

PREFIX = "P6_NATIVE_DIAGNOSTIC "
LIMIT = 1024 * 1024
STAGES = {"python-entered", "helper-system-exit", "helper-exception"}
EXCEPTIONS = {
    "ImportError",
    "ModuleNotFoundError",
    "SyntaxError",
    "NameError",
    "ValueError",
    "RuntimeError",
    "OSError",
    "PermissionError",
    "FileNotFoundError",
    "AssertionError",
    "TypeError",
    "SystemExit",
    "KeyboardInterrupt",
    "Exception",
}


def wrap_script(script):
    """Execute the byte-identical P4 checker with unchanged argv and security checks."""
    digest = hashlib.sha256(script).hexdigest()
    encoded = base64.b64encode(script).decode("ascii")
    return f"""
import base64 as _p6_b64, json as _p6_json
def _p6_emit(stage, **fields):
    value = dict(stage=stage, helper_sha256={digest!r}, **fields)
    print({PREFIX!r} + _p6_json.dumps(value), flush=True)
_p6_emit("python-entered")
try:
    exec(compile(_p6_b64.b64decode({encoded!r}), "<p6-p4-native-check>", "exec"),
         dict(__name__="__main__", __file__="<p6-p4-native-check>"))
except BaseException as _p6_error:
    _p6_tb = _p6_error.__traceback__
    _p6_line = 0
    while _p6_tb is not None:
        if _p6_tb.tb_frame.f_code.co_filename == "<p6-p4-native-check>":
            _p6_line = _p6_tb.tb_lineno
        _p6_tb = _p6_tb.tb_next
    _p6_type = type(_p6_error).__name__
    if _p6_type not in {sorted(EXCEPTIONS)!r}:
        _p6_type = "Exception"
    _p6_stage = ("helper-system-exit" if isinstance(_p6_error, SystemExit)
                 else "helper-exception")
    _p6_emit(_p6_stage, exception_type=_p6_type, helper_line=_p6_line)
    raise
""".encode()


def summarize(stdout, stderr, script):
    """Copy only fixed categories and bounded numeric fields from child output."""
    expected = hashlib.sha256(script).hexdigest()
    result = {"component": "unresolved-native-child", "helper_sha256": expected}
    for line in stdout[-LIMIT:].decode(errors="replace").splitlines():
        if not line.startswith(PREFIX):
            continue
        try:
            item = json.loads(line[len(PREFIX) :])
        except (ValueError, TypeError):
            continue
        if not isinstance(item, dict) or item.get("helper_sha256") != expected:
            continue
        if not isinstance(item.get("stage"), str) or item["stage"] not in STAGES:
            continue
        result.update(component="host-streamed-P4-verifier", stage=item["stage"])
        if (
            isinstance(item.get("exception_type"), str)
            and item["exception_type"] in EXCEPTIONS
        ):
            result["exception_type"] = item["exception_type"]
        number = item.get("helper_line")
        if type(number) is int and 0 <= number <= 100000:
            result["helper_line"] = number
    text = stderr[-LIMIT:].decode(errors="replace").lower()
    if "traceback (most recent call last)" in text:
        result["stderr_category"] = "python-traceback"
    elif "bwrap:" in text:
        result["stderr_category"] = "flatpak-bwrap-diagnostic"
    elif "qt.qpa" in text or "could not load the qt platform plugin" in text:
        result["stderr_category"] = "qt-platform-diagnostic"
    elif re.search(r"error:.*(?:not installed|unknown option|failed to execute)", text):
        result["stderr_category"] = "flatpak-startup-diagnostic"
    else:
        result["stderr_category"] = "unclassified" if stderr else "empty"
    return result


def capture(attempt, operation, stdout, stderr, script, exit_code):
    core.require(
        operation in progress.OPERATIONS
        and (operation.startswith("gui-") or operation in {"imports-a", "imports-b"}),
        "Unreviewed native diagnostic operation",
    )
    private = core.safe_path(core.outside_source(attempt) / "private-subprocess")
    private.mkdir(mode=0o700, exist_ok=True)
    core.require(
        private.stat().st_uid == os.getuid()
        and private.stat().st_mode & 0o777 == 0o700,
        "Private diagnostic directory required",
    )
    prefix = operation + "-" + uuid4().hex[:12]
    files = {}
    for label, data in (("stdout", stdout or b""), ("stderr", stderr or b"")):
        name = prefix + "." + label
        fd = os.open(private / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data[-LIMIT:])
        files[label] = {
            "file": name,
            "original_bytes": len(data),
            "truncated": len(data) > LIMIT,
            "retained_sha256": hashlib.sha256(data[-LIMIT:]).hexdigest(),
        }
    return {
        "operation": operation,
        "exit_code": int(exit_code),
        "diagnostic": summarize(stdout or b"", stderr or b"", script),
        "private_files": files,
        "privacy": (
            "Raw files are owner-private; do not upload or commit. "
            "Public summaries contain no raw output."
        ),
    }


class NativePhaseFailure(core.Rejected):
    def __init__(self, diagnostic):
        self.diagnostic = diagnostic
        super().__init__(
            f"Native verification child failed: {diagnostic['operation']} "
            f"(exit-{diagnostic['exit_code']}); owner-private diagnostics retained"
        )


def run(monitor, attempt, operation, command, *, env, script):
    try:
        result = monitor.command(
            operation, command, env=env, input=wrap_script(script), timeout=900
        )
    except subprocess.CalledProcessError as error:
        diagnostic = capture(
            attempt, operation, error.output, error.stderr, script, error.returncode
        )
        raise NativePhaseFailure(diagnostic) from None
    return result
