"""Three bounded GETs, no acquisition/install/build or environment-value dump.

Compare default curl, installed libostree identification, and the driver's clean
environment. Raw response headers/bodies are private; public output is allowlisted.
No changing User-Agent is proposed as an acquisition workaround.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
COMMIT = "fb23e178d082b117df7924f9a84710992ec233ebc007385feb85d349c4c81415"
URL = f"https://dl.flathub.org/repo/objects/{COMMIT[:2]}/{COMMIT[2:]}.commit"
SAFE_HEADERS = {
    "server",
    "via",
    "content-type",
    "content-length",
    "x-cache",
    "cache-control",
    "retry-after",
    "x-mitmproxy-blocked-reason",
}
ENV_NAMES = (
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "no_proxy",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
    "CURL_CA_BUNDLE",
    "SSL_CERT_FILE",
)


def summarize(status, headers, body, exit_code):
    """Never expose cookies, authentication, arbitrary redirects or body text."""
    safe = {}
    redirect = False
    for line in headers.splitlines():
        key, separator, value = line.partition(":")
        if not separator:
            continue
        if key.lower() in SAFE_HEADERS:
            safe[key.lower()] = value.strip()[:200]
        if key.lower() == "location":
            redirect = True
    digest = hashlib.sha256(body).hexdigest()
    return {
        "curl_exit": exit_code,
        "http_status": status,
        "safe_headers": safe,
        "redirect_advertised": redirect,
        "body_bytes": len(body),
        "body_sha256": digest,
        "expected_object_hash": exit_code == 0 and status == "200" and digest == COMMIT,
    }


def command(label, root, *, user_agent=None):
    result = [
        "curl",
        "--disable",
        "--silent",
        "--show-error",
        "--connect-timeout",
        "5",
        "--max-time",
        "15",
        "--max-filesize",
        "1048576",
        "--proto",
        "=https",
        "--dump-header",
        str(root / (label + ".headers.private")),
        "--output",
        str(root / (label + ".body.private")),
        "--write-out",
        "%{http_code}\n%{num_redirects}\n%{ssl_verify_result}\n",
    ]
    if user_agent:
        result.extend(["--user-agent", user_agent])
    result.append(URL)
    return result


def new_output(path):
    path = path.absolute()
    if (
        path.parent != ROOT / "ci-output"
        or not re.fullmatch(r"p6-http-owner-[A-Za-z0-9.-]+", path.name)
        or any(p.is_symlink() for p in (path, *path.parents))
        or path.exists()
    ):
        raise ValueError("Fresh direct ci-output/p6-http-owner-* path required")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "ci-output/p6-http-owner-1"
    )
    args = parser.parse_args()
    root = None
    started = time.monotonic()
    record = {
        "started_at_utc": datetime.now(UTC).isoformat(),
        "status": "DIAGNOSTIC_INCOMPLETE",
        "complete": False,
        "acquisition_verified": False,
        "url": URL,
        "requests": [],
    }
    try:
        os.umask(0o077)
        for tool in ("curl", "ostree"):
            if not shutil.which(tool):
                raise ValueError("Required tool missing")
        path = new_output(args.output)
        version = subprocess.check_output(["ostree", "--version"], text=True, timeout=5)
        match = re.search(r"Version:\s*'([0-9]+\.[0-9]+(?:\.[0-9]+)?)'", version)
        if not match:
            raise ValueError("Cannot identify installed libostree version")
        path.mkdir(mode=0o700)
        root = path
        (root / "home").mkdir(mode=0o700)
        record.update(
            libostree_version=match[1],
            environment_presence_only={k: bool(os.environ.get(k)) for k in ENV_NAMES},
        )
        clean = {
            "PATH": os.defpath,
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "HOME": str(root / "home"),
        }
        requests = (
            ("default-curl", None, None),
            ("libostree-identification", "libostree/" + match[1], None),
            ("clean-environment-curl", None, clean),
        )
        print(
            "P6 diagnostic: three <=1 MiB GETs, <=15s each; no redirects followed. "
            "No installation, pull, build or GUI. Private output: " + str(root),
            flush=True,
        )
        for label, user_agent, env in requests:
            print("P6 diagnostic: " + label, flush=True)
            try:
                result = subprocess.run(
                    command(label, root, user_agent=user_agent),
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=20,
                    check=False,
                )
                (root / (label + ".curl.private")).write_text(
                    result.stdout + result.stderr
                )
                lines = result.stdout.splitlines()
                headers = root / (label + ".headers.private")
                body = root / (label + ".body.private")
                item = summarize(
                    lines[0] if lines else "UNKNOWN",
                    headers.read_text(errors="replace") if headers.exists() else "",
                    body.read_bytes() if body.exists() else b"",
                    result.returncode,
                )
                item.update(
                    operation=label,
                    redirects_followed=0,
                    tls_verification_result=lines[2] if len(lines) > 2 else "UNKNOWN",
                )
            except subprocess.TimeoutExpired:
                item = {"operation": label, "error_category": "timeout"}
            record["requests"].append(item)
            print(json.dumps(item), flush=True)
        record.update(status="DIAGNOSTIC_COMPLETE", complete=True)
    except (
        OSError,
        ValueError,
        subprocess.SubprocessError,
        KeyboardInterrupt,
    ) as error:
        record.update(error_type=type(error).__name__, complete=True)
    finally:
        record["seconds"] = round(time.monotonic() - started, 3)
        if root:
            for path in root.glob("*.private"):
                path.chmod(0o600)
            (root / "result.json").write_text(json.dumps(record, indent=2) + "\n")
        print(json.dumps(record, indent=2), flush=True)
    return 0 if record["status"] == "DIAGNOSTIC_COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
