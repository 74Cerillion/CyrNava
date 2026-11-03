"""Bounded N4 assembly/export audit/headless installation. No native GUI/signing."""

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


recipe = module("n4_recipe", ROOT / "packaging/native/release.py")


class OfficialOnly(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, url):
        parsed = urllib.parse.urlsplit(url)
        recipe.require(
            parsed.scheme == "https"
            and parsed.hostname == "files.pythonhosted.org"
            and not parsed.username
            and not parsed.password,
            "Unofficial dependency redirect refused",
        )
        return super().redirect_request(request, fp, code, message, headers, url)


def acquire(destination):
    """Exact immutable official wheel URLs; no pip resolution or latest fallback."""
    recipe.require(not destination.exists(), "Fresh wheel output required")
    recipe.require(
        shutil.disk_usage(destination.parent).free >= recipe.FLOOR,
        "Keep free-space floor",
    )
    destination.mkdir(mode=0o700)
    dependencies = json.loads(
        (ROOT / "packaging/native/feasibility/dependencies.json").read_text()
    )
    opener = urllib.request.build_opener(OfficialOnly())
    started = time.monotonic()
    for info in dependencies["files"]:
        recipe.require(
            time.monotonic() - started < 600, "Dependency acquisition deadline"
        )
        parsed = urllib.parse.urlsplit(info["url"])
        recipe.require(
            parsed.scheme == "https"
            and parsed.hostname == "files.pythonhosted.org"
            and not parsed.username
            and not parsed.password,
            "Official HTTPS wheel required",
        )
        recipe.member(info["filename"])
        recipe.require(
            Path(info["filename"]).name == info["filename"]
            and info["filename"].endswith(".whl"),
            "Wheel basename required",
        )
        part = destination / (info["filename"] + ".partial")
        with (
            opener.open(info["url"], timeout=30) as response,
            part.open("xb") as stream,
        ):
            count = 0
            while chunk := response.read(256 * 1024):
                count += len(chunk)
                recipe.require(
                    count <= info["bytes"] and time.monotonic() - started < 600,
                    "Download size/time bound exceeded",
                )
                stream.write(chunk)
        recipe.require(
            count == info["bytes"] and recipe.sha(part) == info["sha256"],
            "Downloaded wheel hash mismatch",
        )
        part.rename(destination / info["filename"])
    recipe.wheels(destination, dependencies)
    return destination


def frontend_build(output, log):
    sources = recipe.source_files(ROOT)
    before = {n: recipe.sha(p) for n, p in sources.items() if n.startswith("frontend/")}
    node = (
        subprocess.check_output(["node", "--version"], text=True)
        .strip()
        .removeprefix("v")
    )
    npm = subprocess.check_output(["npm", "--version"], text=True).strip()
    recipe.require(
        node == (ROOT / ".nvmrc").read_text().strip().removeprefix("v")
        and npm == "11.6.2",
        "Controlled Node/npm required",
    )
    with log.open("xb") as stream:
        subprocess.run(
            ["npm", "run", "build", "--", "--outDir", str(output)],
            cwd=ROOT / "frontend",
            stdout=stream,
            stderr=subprocess.STDOUT,
            timeout=300,
            check=True,
        )
    recipe.require(
        all(recipe.sha(ROOT / n) == h for n, h in before.items()),
        "Frontend source changed during build",
    )
    proof = {
        "status": "PASS",
        "source_files": before,
        "node": node,
        "npm": npm,
        "output_files": {
            str(p.relative_to(output)): recipe.sha(p)
            for p in sorted(output.rglob("*"))
            if p.is_file()
        },
    }
    recipe.write_json(output.parent / "frontend-build.json", proof)
    return output


def run(args):
    output = args.output.absolute()
    recipe.require(
        output.parent == ROOT / "ci-output"
        and not output.exists()
        and not any(p.is_symlink() for p in (output, *output.parents)),
        "Fresh direct repository output required",
    )
    recipe.require(
        shutil.disk_usage(ROOT).free >= recipe.FLOOR + 1536 * 1024**2,
        "Need 6.5GiB free for bounded build/install",
    )
    output.mkdir(mode=0o700)
    record = {
        "status": "FAIL",
        "complete": False,
        "scope": "native source assembly/audit/installed headless checks",
        "steps": [],
        "GUI": "NOT EXECUTED",
        "renderer": "NOT EXECUTED",
        "production_signature": "NOT CREATED",
    }
    started = time.monotonic()
    stage = "preflight"
    try:
        engine = module("n4_engine", ROOT / "desktop/install_engine.py")
        engine.host_supported()
        stage = "frontend-build"
        frontend = frontend_build(output / "frontend", output / "frontend.private.log")
        record["steps"].append({"operation": stage, "status": "PASS"})
        stage = "locked-wheel-acquisition"
        wheelhouse = (
            args.wheelhouse.absolute()
            if args.wheelhouse
            else acquire(output / "wheels")
        )
        stage = "source-assembly-and-export-audit"
        artifacts = output / "artifacts"
        result = recipe.assemble(
            ROOT,
            artifacts,
            wheelhouse,
            frontend,
            version=args.version,
            kind="candidate",
            allow_dirty=args.allow_dirty,
        )
        recipe.write_json(output / "audit.json", result)
        record["steps"].append(
            {
                "operation": stage,
                "status": "PASS",
                "archive_sha256": result["archive_sha256"],
            }
        )
        stage = "installed-headless-verification"
        archive = artifacts / ("CyrNava-" + args.version + "-ubuntu-x86_64.zip")
        with (output / "installation.private.log").open("xb") as stream:
            subprocess.run(
                [
                    sys.executable,
                    "-B",
                    ROOT / "desktop/install_engine.py",
                    "install",
                    "--archive",
                    archive,
                    "--manifest",
                    artifacts / "manifest.json",
                    "--root",
                    output / "client",
                    "--disposable",
                    "--candidate-sha256",
                    recipe.sha(artifacts / "manifest.json"),
                ],
                stdout=stream,
                stderr=subprocess.STDOUT,
                timeout=600,
                check=True,
            )
        current = engine.load(output / "client/current.json")
        release = output / "client/releases" / current["release"]
        receipt, manifest = engine.installed(release)
        recipe.write_json(
            output / "install.json",
            {
                "status": "PASS",
                "scope": (
                    "fresh isolated installed imports/ELF/hash-locked "
                    "providers/backend/data; no GUI/policy load"
                ),
                "archive_sha256": manifest["archive_sha256"],
                "installed_release": current["release"],
                "provider_files": len(receipt["provider_files"]),
                "GUI": "NOT EXECUTED",
                "renderer": "NOT EXECUTED",
            },
        )
        record["steps"].append({"operation": stage, "status": "PASS"})
        # No logs, profiles, private keys or installed trees become upload assets.
        shutil.copyfile(output / "audit.json", artifacts / "audit.json")
        shutil.copyfile(output / "install.json", artifacts / "headless-install.json")
        names = [p.name for p in artifacts.iterdir() if p.is_file()]
        with (artifacts / "SHA256SUMS").open("x") as stream:
            for name in sorted(names):
                recipe.member(name)
                stream.write(recipe.sha(artifacts / name) + "  " + name + "\n")
        recipe.require(
            shutil.disk_usage(ROOT).free >= recipe.FLOOR,
            "Free-space floor crossed; preserve output",
        )
        record.update(
            status="PASS",
            release_readiness=(
                "CONDITIONAL; hosted/native final-package/signature/"
                "redistribution gates remain"
            ),
            archive_sha256=result["archive_sha256"],
        )
    except (
        OSError,
        ValueError,
        subprocess.SubprocessError,
        KeyboardInterrupt,
    ) as error:
        record.update(failed_operation=stage, error_type=type(error).__name__)
        if isinstance(error, subprocess.CalledProcessError):
            record["exit_code"] = error.returncode
        # Raw native/loader output remains in local private logs, never uploaded.
    finally:
        record.update(complete=True, seconds=round(time.monotonic() - started, 3))
        recipe.write_json(output / "result.json", record)
        print(json.dumps(record, indent=2), flush=True)
    return 0 if record["status"] == "PASS" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument("--version", default="0.1.0-n4.1")
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Local explicit patch identity only; CI must use clean checkout",
    )
    args = parser.parse_args()
    try:
        return run(args)
    except (OSError, ValueError) as error:
        print(
            json.dumps(
                {
                    "status": "BLOCKED",
                    "complete": True,
                    "scope": "native build preflight",
                    "error_type": type(error).__name__,
                    "GUI": "NOT EXECUTED",
                }
            )
        )
        return 1


if __name__ == "__main__":
    os.umask(0o077)
    raise SystemExit(main())
