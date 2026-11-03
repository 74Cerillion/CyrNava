"""Explicit owner-reviewed native AppArmor setup, separate from installation.

Reuses the verified installed policy renderer/root helper. Never auto-loads policy.
"""

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path


def module(path):
    spec = importlib.util.spec_from_file_location("cyrnava_policy_install_engine", path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def prepare(engine, root, expected, output, *, disposable=False):
    """Normal root must be canonical; candidate support remains repository-isolated."""
    root = engine.checked_path(root)
    engine.deployment_paths(root, disposable)
    current = engine.load(root / "current.json")
    release = root / "releases" / engine.member_name(current["release"])
    receipt, manifest = engine.installed(release)
    engine.require(
        receipt["manifest_sha256"] == expected, "Exact reviewed manifest required"
    )
    engine.require(
        manifest["kind"] == ("candidate" if disposable else "release"),
        "Policy deployment kind mismatch",
    )
    policy_api = engine.support(release, "apparmor_support")
    policy_api.require_contract("load", manifest.get("apparmor"))
    content = policy_api.render_policy(root, release, contract=manifest["apparmor"])
    output = engine.checked_path(output)
    engine.require(not output.exists(), "Previous policy evidence preserved")
    output.mkdir(mode=0o700, parents=True)
    name = policy_api.profile_name(root)
    path = output / name
    path.write_bytes(content)
    subprocess.run(
        ["/usr/sbin/apparmor_parser", "-Q", "-K", "-j1", path],
        capture_output=True,
        check=True,
        timeout=30,
    )
    return (
        policy_api,
        content,
        {
            "status": "PREPARED",
            "profile": name,
            "policy_sha256": hashlib.sha256(content).hexdigest(),
            "manifest_sha256": expected,
            "parser": "PASS",
            "native_launch": "NOT EXECUTED",
            "host_policy": "NOT MODIFIED",
            "kernel_before": policy_api.read_loaded_profile(name),
        },
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["prepare", "load", "remove"])
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--policy-sha256")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--owner-host", action="store_true")
    parser.add_argument("--disposable", action="store_true")
    args = parser.parse_args()
    peer = Path(__file__).with_name("install_engine.py")
    engine = module(
        peer
        if peer.is_file()
        else Path(__file__).resolve().parents[2] / "desktop/install_engine.py"
    )
    engine.host_supported()
    api, content, record = prepare(
        engine, args.root, args.manifest_sha256, args.output, disposable=args.disposable
    )
    try:
        if args.operation != "prepare":
            engine.require(
                args.owner_host and sys.stdin.isatty(),
                "Explicit owner terminal required",
            )
            engine.require(
                args.policy_sha256 == record["policy_sha256"],
                "Explicit reviewed policy digest required",
            )
            status = Path("/proc/self/status").read_text()
            label = Path("/proc/self/attr/current").read_text().strip()
            engine.require(
                label == "unconfined" and "NoNewPrivs:\t0" in status,
                "Use a normal unconfined owner terminal; no host flags changed",
            )
            record["host_policy"] = "ATTEMPTED; NOT CONFIRMED"
            result = subprocess.run(
                [
                    "/usr/bin/sudo",
                    "/usr/bin/python3.14",
                    "-I",
                    "-c",
                    api.ROOT_HELPER,
                    args.operation,
                    record["profile"],
                    record["policy_sha256"],
                ],
                input=content,
                capture_output=True,
                timeout=90,
            )
            (args.output / "operation.private.log").write_bytes(
                result.stdout + result.stderr
            )
            engine.require(
                result.returncode == 0,
                "Exact policy operation failed; retain private log",
            )
            after = api.read_loaded_profile(record["profile"])
            required = (
                {"state": "PRESENT", "profile": record["profile"], "mode": "enforce"}
                if args.operation == "load"
                else {"state": "ABSENT", "profile": record["profile"]}
            )
            engine.require(after == required, "Kernel mode/identity readback failed")
            record.update(
                status="PASS", host_policy=args.operation.upper(), kernel_after=after
            )
    except (
        OSError,
        ValueError,
        subprocess.SubprocessError,
        KeyboardInterrupt,
    ) as error:
        record.update(
            status="FAIL",
            failed_operation=args.operation,
            error_type=type(error).__name__,
        )
    record.update(complete=True, operation=args.operation)
    engine.durable(args.output / "result.json", record)
    print(json.dumps(record, indent=2))
    return 0 if record["status"] in {"PASS", "PREPARED"} else 1


def safe_main():
    try:
        return main()
    except (
        OSError,
        ValueError,
        subprocess.SubprocessError,
        KeyboardInterrupt,
    ) as error:
        # Preparation may refuse an existing/unsafe output; never overwrite it to
        # record a failure or print raw paths/arguments from the exception.
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "complete": True,
                    "failed_operation": "policy-driver",
                    "error_type": type(error).__name__,
                    "native_launch": "NOT EXECUTED",
                    "host_policy": "NOT CONFIRMED; retain exact-profile evidence",
                }
            )
        )
        return 2


if __name__ == "__main__":
    os.umask(0o077)
    raise SystemExit(safe_main())
