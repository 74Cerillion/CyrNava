"""Bounded owner-host binary acquisition and thin P6 build, never a Qt build.

Uses the unchanged P4 stage/assemble/finish and P5A exported-payload auditors.
All Flatpak state/cache/tmp/build/export directories are under ONE fresh root.
No normal installation, desktop launch, signing key or publication is touched.
"""

import argparse
import configparser
import hashlib
import importlib.util
import json
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PRODUCTION = ROOT / "packaging/flatpak/production"
DEFAULT_OUTPUT = ROOT / "ci-output/p6-binary-candidate-1"
GIB = 1024**3


class Stopped(ValueError):
    pass


def require(value, message):
    if not value:
        raise Stopped(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def safe_new_output(path):
    path = path.absolute()
    require(
        path.parent == ROOT / "ci-output", "Output must be a direct ci-output child"
    )
    require(
        not any(p.is_symlink() for p in (path, *path.parents)), "Symlink root refused"
    )
    require(not path.exists(), "Attempt exists; preserve it and stop")
    require(
        re.fullmatch(r"p6-binary-candidate-[a-zA-Z0-9.-]+", path.name),
        "Invalid output name",
    )
    return path


def capacity(available, added, budget):
    require(available >= budget["minimum_headroom_bytes"], "Disk headroom exhausted")
    require(
        added <= budget["maximum_added_bytes"], "7.5 GiB added-allocation cap reached"
    )


def check_remote(config, expected_url, keys, expected_keys):
    parser = configparser.ConfigParser(interpolation=None)
    parser.read_string(config)
    section = 'remote "flathub"'
    require(parser.get(section, "url") == expected_url, "Unexpected upstream endpoint")
    for field in ("gpg-verify", "gpg-verify-summary"):
        require(parser.getboolean(section, field, fallback=False), "GPG policy refused")
    require(sha(keys) == expected_keys, "Unreviewed upstream trust keys")


class Attempt:
    def __init__(self, root, lock):
        self.root, self.lock = root, lock
        self.started = time.monotonic()
        self.operation = "preflight"
        self.env = {
            "PATH": os.environ.get("PATH", os.defpath),
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_RETRIES": "0",
            "PIP_DEFAULT_TIMEOUT": "30",
            "npm_config_fetch_retries": "0",
            "PYTHONUNBUFFERED": "1",
            "CMAKE_BUILD_PARALLEL_LEVEL": "1",
            "MAKEFLAGS": "-j1",
        }
        for key, folder in {
            "HOME": "home",
            "FLATPAK_USER_DIR": "flatpak",
            "GNUPGHOME": "gnupg-unused",
            "XDG_DATA_HOME": "data",
            "XDG_CONFIG_HOME": "config",
            "XDG_CACHE_HOME": "cache",
            "XDG_RUNTIME_DIR": "runtime",
            "TMPDIR": "tmp",
        }.items():
            location = root / folder
            location.mkdir(mode=0o700)
            self.env[key] = str(location)
        self.record = {
            "status": "FAIL",
            "complete": False,
            "candidate": None,
            "scope": "isolated unsigned P6 candidate; no native GUI or publication",
        }

    def usage(self):
        allocated = int(
            subprocess.check_output(
                ["du", "-sx", "-B1", str(self.root)], text=True
            ).split()[0]
        )
        v = os.statvfs(self.root)
        free = v.f_bavail * v.f_frsize
        capacity(free, allocated, self.lock["budget"])
        require(
            time.monotonic() - self.started < self.lock["budget"]["seconds"],
            "60-minute total bound reached",
        )
        return {
            "allocated_bytes": allocated,
            "available_bytes": free,
            "device": self.root.stat().st_dev,
        }

    def run(self, operation, *args, input=None, timeout=300, cwd=None, **unused):
        self.operation = operation
        self.usage()
        print("P6: " + operation, flush=True)
        log = self.root / (operation + ".private.log")
        log.touch(mode=0o600, exist_ok=False)
        started = time.monotonic()
        with log.open("wb") as output:
            child = subprocess.Popen(
                [str(a) for a in args],
                cwd=cwd,
                env=self.env,
                stdin=subprocess.PIPE if input is not None else subprocess.DEVNULL,
                stdout=output,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            try:
                if input is not None:
                    child.stdin.write(input)
                    child.stdin.close()
                while child.poll() is None:
                    self.usage()
                    if time.monotonic() - started > timeout:
                        raise TimeoutError("Operation deadline reached")
                    time.sleep(1)
                    if int(time.monotonic() - started) % 10 == 0:
                        print("P6: " + operation + " running", flush=True)
                if child.returncode:
                    text = log.read_text(errors="replace").lower()
                    category = "subprocess"
                    if "403" in text:
                        category = "http-403"
                    elif "404" in text:
                        category = "http-404"
                    elif "signature" in text or "gpg" in text:
                        category = "signature"
                    elif "bwrap:" in text:
                        category = "namespace"
                    self.record["failure_category"] = category
                    if operation.startswith(("pull-", "remote-")):
                        self.record["upstream_endpoint"] = self.lock["remote"]
                        endpoint = re.search(
                            r"https://dl\.flathub\.org/repo/objects/[0-9a-f]{2}/"
                            r"[0-9a-f]{62}\.(?:commitmeta|commit|dirtree|dirmeta|filez)",
                            text,
                        )
                        if endpoint:
                            self.record["failed_object_endpoint"] = endpoint[0]
                    raise Stopped("Operation returned nonzero: " + operation)
            finally:
                if child.poll() is None:
                    os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait(timeout=5)
                event = {
                    "operation": operation,
                    "exit": child.returncode,
                    "seconds": round(time.monotonic() - started, 3),
                    "private_log": log.name,
                    "sha256": sha(log),
                }
                with (self.root / "operations.jsonl").open("a") as stream:
                    stream.write(json.dumps(event) + "\n")
        self.usage()
        return log.read_text()

    def verify_refs(self):
        for i, (ref, expected) in enumerate(self.lock["refs"].items()):
            actual = subprocess.check_output(
                ["flatpak", "info", "--user", "--show-commit", ref],
                env=self.env,
                text=True,
                timeout=30,
            ).strip()
            require(actual == expected, "Installed dependency drift: " + str(i))

    def acquire(self):
        self.run(
            "namespace",
            "bwrap",
            "--unshare-user",
            "--unshare-net",
            "--ro-bind",
            "/",
            "/",
            "/usr/bin/true",
            timeout=15,
        )
        self.run(
            "remote-add",
            "flatpak",
            "remote-add",
            "--user",
            "--from",
            "flathub",
            self.lock["descriptor"],
            timeout=50,
        )
        repo = self.root / "flatpak/repo"
        check_remote(
            (repo / "config").read_text(),
            self.lock["remote"],
            repo / "flathub.trustedkeys.gpg",
            self.lock["trusted_keys_sha256"],
        )
        # Compare live refs before any large download: never silently take latest.
        refs = {
            **self.lock["refs"],
            self.lock["layered_webengine"]["ref"]: self.lock["layered_webengine"][
                "commit"
            ],
        }
        for i, (ref, commit) in enumerate(refs.items()):
            actual = self.run(
                f"remote-identity-{i}",
                "flatpak",
                "remote-info",
                "--user",
                "--show-commit",
                "flathub",
                ref,
                timeout=50,
            ).strip()
            require(
                actual == commit,
                "Upstream ref moved; comparison/owner decision required",
            )
        # Full exact-commit pulls: GPG + object hashes verified by OSTree. Avoid
        # duplicating the already-layered WebEngine payload or LLVM/source builds.
        for i, (ref, commit) in enumerate(self.lock["refs"].items()):
            self.run(
                f"pull-{i}",
                "ostree",
                "--repo=" + str(repo),
                "pull",
                "--disable-static-deltas",
                "--network-retries=0",
                "--depth=0",
                "flathub",
                commit,
                timeout=1800,
            )
            self.run(
                f"signature-{i}",
                "ostree",
                "--repo=" + str(repo),
                "show",
                "--gpg-verify-remote=flathub",
                commit,
            )
            binding = self.run(
                f"binding-{i}",
                "ostree",
                "--repo=" + str(repo),
                "show",
                "--print-metadata-key=ostree.ref-binding",
                commit,
            )
            require(ref in binding, "Upstream commit/ref binding mismatch")
            self.run(
                f"bind-ref-{i}",
                "ostree",
                "--repo=" + str(repo),
                "refs",
                "--create=flathub:" + ref,
                commit,
            )
            self.run(
                f"deploy-{i}",
                "flatpak",
                "install",
                "--user",
                "--noninteractive",
                "--no-related",
                "--no-deps",
                "--no-pull",
                "flathub",
                ref,
            )
        self.verify_refs()

    def probe(self, directory, label):
        result = self.run(
            label,
            "flatpak",
            "build",
            "--runtime",
            "--readonly",
            "--unshare=network",
            "--nofilesystem=host",
            "--nofilesystem=home",
            "--env=PYTHONPATH=/app/lib/python3.13/site-packages",
            directory,
            "python3",
            "-B",
            "-",
            input=(HERE / "provider_probe.py").read_bytes(),
        )
        record = json.loads(result.strip().splitlines()[-1])
        load("p6_provider", HERE / "provider_probe.py").verify(record)
        (self.root / (label + ".json")).write_text(json.dumps(record, indent=2) + "\n")

    def build(self):
        builder = load("p6_p4_build", PRODUCTION / "build.py")
        sys.path.insert(0, str(PRODUCTION))
        snapshot = self.root / "source"
        snapshot.mkdir()
        # Explicit application/build directories only. Never copy profiles/.git/
        # repository outputs, private keys or an entire owner checkout.
        for folder in ("backend/app", "desktop/native"):
            target = snapshot / folder
            target.mkdir(parents=True)
            for path in (ROOT / folder).iterdir():
                if path.is_file() and path.suffix in {".py", ".json"}:
                    builder.copy_file(path, target / path.name)
        front = snapshot / "frontend"
        front.mkdir()
        for folder in ("src", "public", "scripts"):
            for path in sorted((ROOT / "frontend" / folder).rglob("*")):
                require(not path.is_symlink(), "Frontend source symlink refused")
                if path.is_file():
                    builder.copy_file(path, front / path.relative_to(ROOT / "frontend"))
        for name in (
            "package.json",
            "package-lock.json",
            "index.html",
            "tsconfig.json",
            "vite.config.ts",
        ):
            builder.copy_file(ROOT / "frontend" / name, front / name)
        for path in (ROOT / "frontend").glob("tsconfig.*.json"):
            builder.copy_file(path, front / path.name)
        (snapshot / "docs").mkdir()
        for name in ("python-third-party-notices.txt", "dependencies-and-licenses.md"):
            builder.copy_file(ROOT / "docs" / name, snapshot / "docs" / name)
        source_hashes = {
            str(p.relative_to(snapshot)): sha(p)
            for p in sorted(snapshot.rglob("*"))
            if p.is_file()
        }
        source_id = hashlib.sha256(
            json.dumps(source_hashes, sort_keys=True).encode()
        ).hexdigest()
        (self.root / "source-snapshot.json").write_text(
            json.dumps(
                {
                    "head": self.lock["source_head"],
                    "snapshot_sha256": source_id,
                    "files": source_hashes,
                },
                indent=2,
            )
            + "\n"
        )
        require(
            self.run("node-version", "node", "--version").strip().startswith("v24."),
            "Node 24 required",
        )
        require(
            self.run("npm-version", "npm", "--version").strip().startswith("11."),
            "npm 11 required",
        )
        self.run(
            "frontend-install",
            "npm",
            "ci",
            "--ignore-scripts",
            "--no-audit",
            "--no-fund",
            "--cache",
            self.root / "cache/npm",
            cwd=front,
            timeout=300,
        )
        self.run("frontend-build", "npm", "run", "build", cwd=front, timeout=300)
        directory = self.root / "production-build"
        directory.mkdir()
        builder.stage(directory, source=snapshot, build_id="p6-qt613-" + source_id[:12])
        record = json.loads((directory / "build-inputs.json").read_text())
        record.update(
            runtime_lock=self.lock,
            source_snapshot_sha256=source_id,
            candidate_only=True,
            source_state="uncommitted executable inputs; not a release commit",
        )
        record["candidate_recipe_sha256"] = {
            p.name: sha(p) for p in sorted(HERE.iterdir()) if p.is_file()
        }
        (directory / "build-inputs.json").write_text(
            json.dumps(record, indent=2) + "\n"
        )
        builder.verify_refs = self.verify_refs
        builder.EXPORT_TIMESTAMP = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        count = 0

        def run(*args, **kwargs):
            nonlocal count
            count += 1
            # Keep existing production operations and checks, scoped to private env.
            self.run(f"assemble-{count}", *args, **kwargs, timeout=600)
            if str(args[0]) == "flatpak" and str(args[1]) == "build-init":
                self.probe(directory / "build", "baseapp-provider")

        builder.run = run
        builder.output = lambda *args: subprocess.check_output(
            list(map(str, args)), env=self.env, text=True, timeout=30
        ).strip()
        result = builder.assemble(directory)
        (directory / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        self.probe(directory / "build", "final-provider")
        elf = self.run(
            "elf-layout",
            "flatpak",
            "build",
            "--readonly",
            "--unshare=network",
            "--nofilesystem=host",
            "--nofilesystem=home",
            directory / "build",
            "python3",
            "-B",
            "-",
            "--elf-only",
            input=(HERE / "provider_probe.py").read_bytes(),
        )
        (self.root / "elf-layout.json").write_text(
            json.dumps(json.loads(elf.strip().splitlines()[-1]), indent=2) + "\n"
        )
        # Audit the exported bytes independently, with the accepted auditor left
        # unchanged. P5B's historical A-only signing/source policy is never invoked.
        auditor = load("p6_p5a_audit", ROOT / "ci/flatpak.py")
        auditor.run = run
        auditor.output = builder.output
        (self.root / "export-audit").mkdir()
        audited = auditor.audit_bundle(directory, self.root / "export-audit")
        audited["ostree_timestamp"] = builder.EXPORT_TIMESTAMP
        (self.root / "export-audit/artifacts/provenance.json").write_text(
            json.dumps(audited, indent=2) + "\n"
        )
        sys.path.insert(0, str(ROOT / "ci/release"))
        inventory = load(
            "p6_candidate_inventory", ROOT / "ci/release/product_inventory.py"
        )
        (self.root / "dependency-notice-inventory.json").write_text(
            json.dumps(
                {
                    "scope": "actual exported app files; not license clearance",
                    "app": inventory.inspect_tree(
                        self.root / "export-audit/bundle-checkout/files"
                    ),
                    "runtime_commit": self.lock["refs"][
                        "runtime/org.kde.Platform/x86_64/6.11"
                    ],
                    "source_and_redistribution_review": "PENDING",
                },
                indent=2,
            )
            + "\n"
        )
        self.record.update(
            candidate=result,
            export_audit=audited,
            provider_checks="PASS",
            native_renderer="NOT EXECUTED",
            signature="UNSIGNED CANDIDATE",
            runtime_update="NOT EXECUTED",
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    lock = json.loads((HERE / "candidate.lock.json").read_text())
    attempt = None
    try:
        os.umask(0o077)
        root = safe_new_output(args.output)
        require(platform.machine() == "x86_64", "Only x86_64 is supported")
        for tool in (
            "flatpak",
            "ostree",
            "bwrap",
            "du",
            "git",
            "node",
            "npm",
            "desktop-file-validate",
            "appstreamcli",
            "findmnt",
        ):
            require(shutil.which(tool), "Required tool unavailable: " + tool)
        require(sys.version_info >= (3, 11), "Python 3.11+ required")
        require(
            importlib.util.find_spec("pip"),
            "Host Python pip required before acquisition",
        )
        require(
            subprocess.check_output(
                ["git", "-C", ROOT, "rev-parse", "HEAD"], text=True
            ).strip()
            == lock["source_head"],
            "Unexpected source HEAD",
        )
        require(
            subprocess.check_output(
                ["git", "-C", ROOT, "branch", "--show-current"], text=True
            ).strip()
            == "desktop/p2-production-integration",
            "Integration branch required",
        )
        for relative, expected in lock["production_guards"].items():
            require(sha(ROOT / relative) == expected, "Production baseline changed")
        v = os.statvfs(root.parent)
        require(
            v.f_bavail * v.f_frsize >= lock["budget"]["minimum_free_bytes"],
            "9 GiB initial free space required",
        )
        fs = subprocess.check_output(
            ["findmnt", "-n", "-o", "FSTYPE", "-T", root.parent], text=True
        ).strip()
        require(fs not in {"tmpfs", "ramfs"}, "Persistent output volume required")
        print("P6 isolated paths: " + str(root), flush=True)
        print(
            "Creates only home/flatpak/data/config/cache/runtime/tmp/source/production-build/export-audit beneath that root. No normal Flatpak or GUI changes.",
            flush=True,
        )
        root.mkdir(mode=0o700)
        attempt = Attempt(root, lock)
        attempt.record["initial_usage"] = attempt.usage()
        attempt.acquire()
        attempt.build()
        attempt.usage()  # Parent-side staging/audit writes also count toward limits.
        attempt.record["status"] = "CANDIDATE BUILT"
    except (
        OSError,
        ValueError,
        subprocess.SubprocessError,
        KeyboardInterrupt,
    ) as error:
        result = {
            "status": "BLOCKED",
            "complete": True,
            "error_type": type(error).__name__,
            "error": str(error)
            if isinstance(error, Stopped)
            else "Operation failed or interrupted",
        }
        if attempt:
            attempt.record.update(result, failed_operation=attempt.operation)
        else:
            print(json.dumps(result), flush=True)
        return 1
    finally:
        if attempt:
            attempt.record.update(
                complete=True,
                seconds=round(time.monotonic() - attempt.started, 3),
                failed_operation=attempt.record.get("failed_operation"),
            )
            try:
                attempt.record["final_usage"] = attempt.usage()
            except Stopped as error:
                attempt.record["resource_limit"] = str(error)
                attempt.record["status"] = "BLOCKED"
            (attempt.root / "result.json").write_text(
                json.dumps(attempt.record, indent=2) + "\n"
            )
            print(json.dumps(attempt.record, indent=2), flush=True)
    return 0 if attempt and attempt.record["status"] == "CANDIDATE BUILT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
