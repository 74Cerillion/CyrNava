"""P4 build orchestration and an independent audit of the exported bundle.

Runtime installation is explicit and limited to disposable GitHub-hosted runners.
No application is run, installed, published or signed by this module.
"""

import argparse
import ast
import configparser
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGING = ROOT / "packaging/flatpak/production"
APP_ID = "io.github._74Cerillion.CyrNava"


class VerificationError(ValueError):
    """Safe diagnostic messages authored by this verifier, without input contents."""


def module(name):
    spec = importlib.util.spec_from_file_location(
        "ci_" + name, PACKAGING / (name + ".py")
    )
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def run(*args):
    subprocess.run([str(a) for a in args], check=True)


def output(*args):
    return subprocess.check_output([str(a) for a in args], text=True).strip()


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def prepare_runtimes():
    if (
        os.environ.get("GITHUB_ACTIONS") != "true"
        or os.environ.get("RUNNER_ENVIRONMENT") != "github-hosted"
    ):
        raise VerificationError(
            "Runtime provisioning is restricted to disposable GitHub-hosted runners"
        )
    remote = json.loads((ROOT / "ci/tools.json").read_text())["runtime_remote"]
    run(
        "flatpak",
        "remote-add",
        "--user",
        "--if-not-exists",
        remote["name"],
        remote["descriptor"],
    )
    lock = json.loads((PACKAGING / "toolchain.lock.json").read_text())
    for ref, commit in lock["refs"].items():
        # GPG verification remains on. No latest-version or security-weakening fallback.
        run(
            "flatpak",
            "install",
            "--user",
            "--noninteractive",
            "--no-related",
            remote["name"],
            ref,
        )
        run(
            "flatpak",
            "update",
            "--user",
            "--noninteractive",
            "--no-related",
            "--commit=" + commit,
            ref,
        )
    return module("build").verify_refs()


def validate_payload(checkout):
    files = checkout / "files"
    inventory = module("install_payload").audit(files)
    required = (
        "bin/cyrnava",
        "bin/QtWebEngineProcess",
        "share/cyrnava/frontend/dist/index.html",
        "share/cyrnava/backend/app/main.py",
        "lib/python3.13/site-packages/PySide6/__init__.py",
        f"share/applications/{APP_ID}.desktop",
        f"share/metainfo/{APP_ID}.metainfo.xml",
        f"share/icons/hicolor/256x256/apps/{APP_ID}.png",
    )
    if any(not (files / name).is_file() for name in required):
        raise VerificationError("Bundle lacks required runtime/application files")
    module("host_verify").permissions((checkout / "metadata").read_text())
    metadata = configparser.ConfigParser()
    metadata.read(checkout / "metadata")
    if (
        metadata["Application"]["name"] != APP_ID
        or metadata["Application"]["command"] != "cyrnava"
    ):
        raise VerificationError("Bundle metadata identity/command mismatch")
    manifest = json.loads((PACKAGING / (APP_ID + ".json")).read_text())
    expected = {
        "runtime": f"{manifest['runtime']}/x86_64/{manifest['runtime-version']}",
        "sdk": f"{manifest['sdk']}/x86_64/{manifest['runtime-version']}",
        "base": f"app/{manifest['base']}/x86_64/{manifest['base-version']}",
    }
    if any(
        metadata["Application"].get(key) != value for key, value in expected.items()
    ):
        raise VerificationError("Bundle runtime/SDK/BaseApp mismatch")
    expected_environment = dict(
        value.removeprefix("--env=").split("=", 1)
        for value in manifest["finish-args"]
        if value.startswith("--env=")
    )
    actual_environment = (
        dict(metadata.items("Environment"))
        if metadata.has_section("Environment")
        else {}
    )
    if actual_environment != {
        key.lower(): value for key, value in expected_environment.items()
    }:
        raise VerificationError("Bundle WebEngine environment mismatch")
    tree = ast.parse(
        (files / "share/cyrnava/desktop/native/build_identity.py").read_text()
    )
    constants = {
        node.targets[0].id: ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    }
    if constants.get("APP_ID") != APP_ID or constants.get("CHANNEL") != "production":
        raise VerificationError("Bundle native identity mismatch")
    return inventory


def audit_bundle(directory, destination):
    started = time.monotonic()
    record = json.loads((directory / "result.json").read_text())
    bundle = directory / (APP_ID + ".flatpak")
    if (
        record.get("status") != "PASS"
        or sha(bundle) != record.get("sha256")
        or bundle.stat().st_size != record.get("bytes")
    ):
        raise VerificationError("Missing, failed or changed Flatpak bundle")
    # Import and check out the EXPORTED bundle rather than trusting the build tree.
    repo = destination / "imported-repo"
    checkout = destination / "bundle-checkout"
    run("ostree", "init", "--mode=archive", "--repo=" + str(repo))
    run("flatpak", "build-import-bundle", repo, bundle)
    commit = output(
        "ostree", "--repo=" + str(repo), "rev-parse", f"app/{APP_ID}/x86_64/stable"
    )
    if commit != record.get("ostree_commit"):
        raise VerificationError("Exported commit mismatch")
    run("ostree", "--repo=" + str(repo), "checkout", "--user-mode", commit, checkout)
    inventory = validate_payload(checkout)
    if inventory != json.loads((directory / "package-inventory.json").read_text()):
        raise VerificationError("Exported payload differs from audited build tree")
    inputs = json.loads((directory / "build-inputs.json").read_text())
    packaged = json.loads(
        (checkout / "files/share/cyrnava/build-inputs.json").read_text()
    )
    # Installation adds wheel hashes to the build record before packaging it.
    if packaged != inputs:
        raise VerificationError("Packaged provenance differs from build record")
    source_commit = output("git", "-C", ROOT, "rev-parse", "HEAD")
    if inputs.get("git_commit") != source_commit:
        raise VerificationError("Build source commit mismatch")
    if os.environ.get("GITHUB_SHA", source_commit) != source_commit:
        raise VerificationError("Checkout does not match workflow source commit")
    metadata = {
        "status": "PASS",
        "app_id": APP_ID,
        "version": inputs["version"],
        "source_commit": source_commit,
        "sha256": sha(bundle),
        "artifact_bytes": bundle.stat().st_size,
        "ostree_commit": commit,
        "runtime": inputs["runtime_lock"],
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "ostree_timestamp": module("build").EXPORT_TIMESTAMP,
        "workflow_run_id": os.environ.get("GITHUB_RUN_ID"),
        "workflow_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "runner_os": os.environ.get("RUNNER_OS"),
        "runner_image": os.environ.get("ImageOS"),
        "runner_image_version": os.environ.get("ImageVersion"),
        "audit_seconds": round(time.monotonic() - started, 3),
        "native_renderer_portals": "NOT TESTED by package audit",
    }
    artifacts = destination / "artifacts"
    artifacts.mkdir()
    import shutil

    shutil.copyfile(bundle, artifacts / bundle.name)
    (artifacts / "SHA256SUMS").write_text(
        metadata["sha256"] + "  " + bundle.name + "\n"
    )
    for name in ("build-inputs.json", "package-inventory.json", "result.json"):
        shutil.copyfile(directory / name, artifacts / name)
    (artifacts / "provenance.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("prepare", "build", "audit"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    destination = args.output.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    result = {"status": "FAIL", "operation": args.operation}
    then = time.monotonic()
    try:
        if args.operation == "prepare":
            result["runtime_lock"] = prepare_runtimes()
        else:
            directory = destination / "production-build"
            if args.operation == "build":
                if output(
                    "git", "-C", ROOT, "status", "--porcelain", "--untracked-files=no"
                ):
                    raise VerificationError(
                        "CI build requires an unchanged tracked checkout"
                    )
                run(
                    sys.executable,
                    PACKAGING / "build.py",
                    "--build-id",
                    "ci-"
                    + output("git", "-C", ROOT, "rev-parse", "--short=12", "HEAD"),
                    "--output-directory",
                    directory,
                )
            else:
                result.update(audit_bundle(directory, destination))
        result["status"] = "PASS"
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        result["error_type"] = type(error).__name__
        if isinstance(error, VerificationError):
            result["error"] = str(error)
        print("CI Flatpak operation failed: " + type(error).__name__, file=sys.stderr)
    finally:
        result.update(complete=True, seconds=round(time.monotonic() - then, 3))
        (destination / (args.operation + ".json")).write_text(
            json.dumps(result, indent=2) + "\n"
        )
        print(json.dumps(result, indent=2), flush=True)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
