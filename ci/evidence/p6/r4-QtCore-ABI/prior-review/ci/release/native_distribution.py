"""P6 isolated runtime retrieval and real application remote-install probe.

No production trust is established. Existing profiles, remotes and owner data are
never reused. Accepted P5C client isolation and P4 permission checks are reused.
"""

import argparse
import base64
import configparser
import importlib.util
import json
import os
import subprocess
import time
from pathlib import Path

import client
import core
import distribution


class RuntimeClient(client.Client):
    def __init__(self, root, progress=None):
        super().__init__(root)
        self.progress = progress
        home = self.root / "home"
        home.mkdir(mode=0o700)
        self.env["HOME"] = str(home)

    def run(self, operation, *args):
        if self.progress is None:
            return super().run(operation, *args)
        with self.progress.operation("flatpak-" + operation, timeout=300):
            return super().run(operation, *args)

    def command(self, operation, *args, timeout=1800):
        self.guard()
        core.require(
            operation in {"runtime-remote", "runtime-install", "runtime-pin", "launch"},
            "Unreviewed native distribution operation",
        )
        try:
            command = ["flatpak", "--user", *map(str, args)]
            if self.progress is None:
                result = subprocess.run(
                    command,
                    env=self.env,
                    capture_output=True,
                    timeout=timeout,
                    stdin=subprocess.DEVNULL,
                )
            else:
                result = self.progress.command(
                    operation, command, env=self.env, timeout=timeout
                )
        except subprocess.TimeoutExpired:
            raise client.NativeFailure(operation, "timeout", -1) from None
        except subprocess.CalledProcessError as error:
            result = subprocess.CompletedProcess(
                [], error.returncode, error.output, error.stderr
            )
        text = result.stderr.decode(errors="replace").lower()
        self.operations.append({"operation": operation, "exit_code": result.returncode})
        if result.returncode:
            category = (
                "sandbox-namespace-unavailable"
                if "bwrap:" in text and ("permitted" in text or "namespace" in text)
                else client.failure_category(text)
            )
            raise client.NativeFailure(operation, category, result.returncode)
        return result.stdout.decode().strip()

    def runtimes(self):
        core.require(not self.run("list", "list", "--columns=ref"), "Client not empty")
        tools = core.read_json(core.ROOT / "ci/tools.json")
        remote = tools["runtime_remote"]
        self.command(
            "runtime-remote",
            "remote-add",
            "--from",
            remote["name"],
            remote["descriptor"],
            timeout=300,
        )
        runtime = "org.kde.Platform//6.11"
        self.command(
            "runtime-install", "install", "--noninteractive", remote["name"], runtime
        )
        lock = core.read_json(
            core.ROOT / "packaging/flatpak/production/toolchain.lock.json"
        )
        expected = lock["refs"][runtime]
        self.command(
            "runtime-pin",
            "update",
            "--noninteractive",
            "--no-deps",
            "--no-related",
            "--commit=" + expected,
            runtime,
        )
        actual = self.run("commit", "info", "--show-commit", runtime)
        core.require(actual == expected, "Retrieved runtime commit mismatch")
        cfg = configparser.ConfigParser(interpolation=None)
        cfg.read(self.root / "flatpak/repo/config")
        section = 'remote "' + remote["name"] + '"'
        core.require(
            cfg.getboolean(section, "gpg-verify", fallback=False)
            and cfg.getboolean(section, "gpg-verify-summary", fallback=False),
            "Runtime signatures not enforced",
        )
        return {
            "status": "PASS",
            "runtime": runtime,
            "commit": actual,
            "initial_client": "EMPTY",
            "retrieval": "NETWORK; no local runtime copy",
            "installed_refs": self.run("list", "list", "--columns=ref").splitlines(),
        }

    def install_real(self, base, public, fingerprint, expected, source):
        key = public / "staging-public.gpg"
        ref = self.root / "application.flatpakref"
        ref.write_text(
            "[Flatpak Ref]\nTitle=CyrNava P6 DISPOSABLE\nName="
            + core.APP_ID
            + "\nBranch=stable\nIsRuntime=false\nUrl="
            + base
            + "repo/\nGPGKey="
            + base64.b64encode(key.read_bytes()).decode()
            + "\n"
        )
        client.validate_descriptor(ref, key, fingerprint, self.root, core.APP_ID)
        descriptor = self.root / "application.flatpakrepo"
        descriptor.write_text(
            "[Flatpak Repo]\nTitle=CyrNava P6 DISPOSABLE\nUrl="
            + base
            + "repo/\nGPGKey="
            + base64.b64encode(key.read_bytes()).decode()
            + "\n"
        )
        self.run("remote", "remote-add", "--from", "p5c", descriptor)
        self.verify_summary()
        # No --no-deps: normal client dependency resolution remains enabled.
        self.run("install", "install", "--noninteractive", ref)
        core.require(
            self.commit(core.APP_ID) == expected, "Real installed commit mismatch"
        )
        self.installed_source(source)
        location = Path(
            self.run("location", "info", "--show-location", core.APP_ID)
        ).resolve()
        core.require(
            location.is_relative_to(self.root / "flatpak"),
            "Deployment escaped disposable installation",
        )
        inputs = core.read_json(location / "files/share/cyrnava/build-inputs.json")
        core.require(
            inputs.get("version") == "0.1.0" and inputs.get("schema") == 5,
            "Installed version/schema mismatch",
        )
        self.verify_remote(core.APP_ID)
        permissions = self.run("list", "info", "--show-permissions", core.APP_ID)
        path = core.ROOT / "packaging/flatpak/production/host_verify.py"
        spec = importlib.util.spec_from_file_location("p6_permissions", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.permissions(permissions)
        return {
            "status": "PASS",
            "application_id": core.APP_ID,
            "branch": "stable",
            "architecture": "x86_64",
            "commit": expected,
            "source_commit": source,
            "version": inputs["version"],
            "schema": inputs["schema"],
            "permissions": permissions,
            "runtime": self.run("list", "info", "--show-runtime", core.APP_ID),
        }


def execute():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--public", type=Path, required=True)
    parser.add_argument("--fingerprint", required=True)
    parser.add_argument("--probe-launch", action="store_true")
    args = parser.parse_args()
    os.umask(0o077)
    root = core.outside_source(args.root)
    root.mkdir(mode=0o700)
    record = {
        "status": "FAIL",
        "complete": False,
        "checks": {},
        "scope": "LOCAL NATIVE",
    }
    start = time.monotonic()
    try:
        public = core.safe_path(args.public)
        key = public / "staging-public.gpg"
        store = core.init_store(root / "store")
        destination = distribution.LocalDestination(store)
        reviewed = distribution.plan(public, destination, key, args.fingerprint, root)
        distribution.publish(public, destination, key, args.fingerprint, reviewed, root)
        release = core.read_json(public / "release.json")
        core.require(
            release["source_commit"]
            == core.policy()["approved_staging_sources"][0]["source_commit"],
            "Unapproved application source",
        )
        native = RuntimeClient(root / "client")
        record["checks"]["runtime_retrieval"] = native.runtimes()
        with distribution.loopback(destination, key, args.fingerprint) as base:
            record["checks"]["real_remote_install"] = native.install_real(
                base,
                public,
                args.fingerprint,
                release["ostree_commit"],
                release["source_commit"],
            )
            if args.probe_launch:
                native.command("launch", "run", core.APP_ID, timeout=30)
                # An exit code alone never establishes GUI functionality.
                record["checks"]["launch"] = {"status": "UNVERIFIED", "exit": 0}
        record["status"] = "LOCAL INSTALL PASS; GUI/UPDATE/HTTPS UNVERIFIED"
    except (core.Rejected, OSError, ValueError, KeyError) as error:
        record["error"] = (
            str(error) if isinstance(error, core.Rejected) else type(error).__name__
        )
    finally:
        record["complete"] = True
        record["seconds"] = round(time.monotonic() - start, 3)
        (root / "result.json").write_bytes(core.encode(record))
        print(json.dumps(record, indent=2), flush=True)
    return 0 if record["status"].startswith("LOCAL INSTALL PASS") else 1


def main():
    try:
        return execute()
    except (Exception, KeyboardInterrupt) as error:
        print(
            core.encode(
                {
                    "status": "FAIL",
                    "complete": True,
                    "error": str(error)
                    if isinstance(error, core.Rejected)
                    else type(error).__name__,
                    "evidence": "stdout; output root not assumed safe",
                }
            ).decode(),
            flush=True,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
