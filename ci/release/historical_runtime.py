"""P6 opt-in historical replay. Never imported by the packaged application."""

import configparser
import contextlib
import json
import re
import subprocess
import time

import core
import native_diagnostics
import native_distribution

COMMIT = "76fa01ac42ecf45d2c5020ef80de1c474c0c2ae86a51a79e8fec44c48f9dc473"
REF = "org.kde.Platform/x86_64/6.11"
TRANSACTIONS = {
    "install-a",
    "install-b",
    "probe-update-b",
    "probe-rollback-a",
    "update-b",
    "rollback-a",
    "reinstall-b",
}
MODULES = (
    "QtCore",
    "QtGui",
    "QtWidgets",
    "QtNetwork",
    "QtWebChannel",
    "QtWebEngineCore",
    "QtWebEngineWidgets",
)


def authorize(value):
    core.require(
        value is None or value == COMMIT,
        "Only the owner-approved historical runtime is permitted",
    )
    core.require(
        core.read_json(core.ROOT / "packaging/flatpak/production/toolchain.lock.json")[
            "refs"
        ]["org.kde.Platform//6.11"]
        == COMMIT,
        "Historical policy/lock disagreement",
    )
    return value is not None


class Replay:
    def __init__(self, native, attempt, approved=None):
        self.enabled = authorize(approved)
        self.approved_commit = approved
        self.native, self.attempt, self.events = native, attempt, []

    def snapshot(self):
        self.native.guard()
        value = self.native.run("commit", "info", "--show-commit", REF)
        core.require(
            core.SHA.fullmatch(value) is not None, "Invalid runtime commit readback"
        )
        return value

    def origin_policy(self):
        """Check trust configuration without requiring a pruned local commit."""
        n = self.native
        n.guard()
        remote = core.read_json(core.ROOT / "ci/tools.json")["runtime_remote"]["name"]
        core.require(
            n.run("remote", "info", "--show-origin", REF) == remote,
            "Unexpected runtime origin",
        )
        cfg = configparser.ConfigParser(interpolation=None)
        cfg.read(n.root / "flatpak/repo/config")
        section = 'remote "' + remote + '"'
        core.require(
            cfg.get(section, "url", fallback="") == "https://dl.flathub.org/repo/",
            "Unexpected runtime remote URL",
        )
        core.require(
            cfg.getboolean(section, "gpg-verify", fallback=False)
            and cfg.getboolean(section, "gpg-verify-summary", fallback=False),
            "Runtime signature enforcement required",
        )
        return {
            "origin": remote,
            "runtime_ref": REF,
            "approved_commit": COMMIT,
            "signature_enforcement": "PASS",
        }

    def trusted(self):
        """Verify the restored commit cryptographically, then its live identity."""
        policy = self.origin_policy()
        n, remote = self.native, policy["origin"]
        # Verify against the isolated remote keyring; retain no raw output.
        command = [
            "ostree",
            "--repo=" + str(n.root / "flatpak/repo"),
            "show",
            "--gpg-verify-remote=" + remote,
            COMMIT,
        ]
        try:
            if n.progress:
                n.progress.command("runtime-signature", command, env=n.env, timeout=60)
            else:
                subprocess.run(
                    command, env=n.env, capture_output=True, check=True, timeout=60
                )
        except subprocess.CalledProcessError as error:
            # Keep the next signature failure diagnosable without logging raw text.
            diagnostic = native_diagnostics.capture(
                self.attempt,
                "runtime-signature",
                error.output,
                error.stderr,
                b"",
                error.returncode,
            )
            diagnostic["diagnostic"] = {
                "component": "runtime-commit-signature-check",
                "category": "commit-signature-verification-failed",
            }
            (self.attempt / "runtime-signature-failure.json").write_bytes(
                core.encode(diagnostic)
            )
            raise core.Rejected(
                "Historical runtime signature verification failed; "
                "private diagnostics retained"
            ) from None
        except (OSError, subprocess.SubprocessError):
            raise core.Rejected(
                "Historical runtime signature verification unavailable or timed out"
            ) from None
        # Do not accept a valid signature for an inactive historical commit.
        identity = n.verify_runtime()
        return {**policy, "commit_signature": "PASS", "runtime_identity": identity}

    def flush(self):
        (self.attempt / "runtime-transactions.json").write_bytes(
            core.encode(
                {
                    "policy": "historical-replay-only" if self.enabled else "strict",
                    "transactions": self.events,
                }
            )
        )

    @contextlib.contextmanager
    def transaction(self, name):
        core.require(name in TRANSACTIONS, "Unreviewed runtime transaction")
        event = {
            "operation": name,
            "started_monotonic": time.monotonic(),
            "before": self.snapshot(),
            "transaction": "FAIL",
            "restoration": "NOT_ATTEMPTED",
        }
        self.events.append(event)
        self.flush()
        try:
            yield
            event["transaction"] = "PASS"
        finally:
            # Even interrupted/failed transactions must record the actual readback.
            try:
                event["after"] = self.snapshot()
                event["after_monotonic"] = time.monotonic()
                event["drift"] = event["after"] != COMMIT
                event["ordinary_runtime_compatible"] = not event["drift"]
                self.flush()
                if event["transaction"] != "PASS":
                    event["validation"] = "FAIL"
                else:
                    if event["after"] != COMMIT:
                        if not self.enabled:
                            raise native_distribution.RuntimeIdentityFailure(
                                {
                                    "category": "runtime-commit-drift",
                                    "runtime_ref": REF,
                                    "expected_commit": COMMIT,
                                    "actual_commit": event["after"],
                                }
                            )
                        # Normal dependency updates can prune the old local object.
                        # Check authorization/origin/GPG policy first. Flatpak must
                        # retrieve and verify exactly COMMIT before the independent
                        # signature and live-identity checks can run.
                        core.require(
                            authorize(self.approved_commit),
                            "Historical authorization required",
                        )
                        event["restoration_policy"] = self.origin_policy()
                        event["restoration"] = "STARTED"
                        self.flush()
                        try:
                            try:
                                self.native.command(
                                    "runtime-pin",
                                    "update",
                                    "--noninteractive",
                                    "--no-deps",
                                    "--no-related",
                                    "--commit=" + COMMIT,
                                    REF,
                                    timeout=300,
                                )
                            finally:
                                # A failed restore may still have changed deployment.
                                try:
                                    event["restored_commit"] = self.snapshot()
                                except (core.Rejected, OSError, ValueError):
                                    event["restored_commit"] = "UNAVAILABLE"
                                event["restored_monotonic"] = time.monotonic()
                                self.flush()
                            core.require(
                                event["restored_commit"] == COMMIT,
                                "Historical runtime restoration mismatch",
                            )
                            event["trust"] = self.trusted()
                        except BaseException:
                            event["restoration"] = "FAIL"
                            raise
                        else:
                            event["restoration"] = "PASS"
                    else:
                        event["trust"] = self.trusted()
                # Never turn a failed original transaction into success after repair.
            except BaseException:
                event["validation"] = "FAIL"
                raise
            else:
                event["validation"] = (
                    "PASS" if event["transaction"] == "PASS" else "FAIL"
                )
            finally:
                self.flush()


# No QApplication, backend, network call, editor or renderer is created here.
IMPORT_SCRIPT = (
    """
import hashlib, importlib, json, pathlib, re
import PySide6, shiboken6
def digest(path):
    h = hashlib.sha256()
    with pathlib.Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
modules = {}
for name in %r:
    m = importlib.import_module("PySide6." + name)
    modules[name] = digest(m.__file__)
from PySide6.QtCore import qVersion
providers = {}
for line in pathlib.Path("/proc/self/maps").read_text().splitlines():
    path = line.split()[-1]
    pattern = r"lib(?:Qt6[A-Za-z0-9]+|pyside6|shiboken6)[A-Za-z0-9_.-]*\\.so[.0-9]*"
    if path.startswith(("/app/", "/usr/")) and re.fullmatch(
        pattern, pathlib.Path(path).name
    ):
        p = pathlib.Path(path)
        zone = "app/" if path.startswith("/app/") else "runtime/"
        providers[zone + p.name] = digest(p)
versions = dict(pyside=PySide6.__version__,
                shiboken=shiboken6.__version__, qt=qVersion())
print("P6_IMPORT " + json.dumps(dict(status="PASS", modules=modules,
    providers=providers, versions=versions)), flush=True)
"""
    % (MODULES,)
).encode()


def probe(native, monitor, attempt, label):
    core.require(label in {"A", "B"}, "Unreviewed import generation")
    native.verify_runtime()
    operation = "imports-" + label.lower()
    command = [
        "flatpak",
        "--user",
        "run",
        "--branch=stable",
        "--command=python3",
        core.APP_ID,
        "-B",
        "-u",
        "-",
    ]
    try:
        result = monitor.command(
            operation, command, env=native.env, timeout=60, input=IMPORT_SCRIPT
        )
    except subprocess.CalledProcessError as error:
        diagnostic = native_diagnostics.capture(
            attempt,
            operation,
            error.output,
            error.stderr,
            IMPORT_SCRIPT,
            error.returncode,
        )
        (attempt / (operation + "-failure.json")).write_bytes(core.encode(diagnostic))
        raise core.Rejected(
            "Sandbox import check failed; inspect private import diagnostics"
        ) from None
    diagnostic = native_diagnostics.capture(
        attempt, operation, result.stdout, result.stderr, IMPORT_SCRIPT, 0
    )
    (attempt / (operation + "-capture.json")).write_bytes(core.encode(diagnostic))
    records = [
        json.loads(line[len(b"P6_IMPORT ") :])
        for line in result.stdout.splitlines()
        if line.startswith(b"P6_IMPORT ")
    ]
    core.require(len(records) == 1, "Missing/ambiguous sandbox import evidence")
    value = records[0]
    core.require(
        value.get("status") == "PASS" and set(value.get("modules", {})) == set(MODULES),
        "Incomplete sandbox imports",
    )
    core.require(
        all(core.SHA.fullmatch(h) for h in value["modules"].values()),
        "Malformed import module hashes",
    )
    providers = value.get("providers", {})
    core.require(
        all(
            isinstance(k, str)
            and re.fullmatch(r"(?:app|runtime)/lib[A-Za-z0-9_.-]+", k)
            and core.SHA.fullmatch(v)
            for k, v in providers.items()
        ),
        "Unsafe provider evidence",
    )
    core.require(
        all(
            any(k.startswith(zone) for k in providers)
            for zone in (
                "runtime/libQt6Core.so",
                "runtime/libQt6Gui.so",
                "runtime/libQt6Widgets.so",
                "app/libQt6WebEngineCore.so",
            )
        ),
        "Required library providers missing",
    )
    versions = value.get("versions", {})
    core.require(
        set(versions) == {"pyside", "shiboken", "qt"}
        and all(
            isinstance(v, str) and re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,3}", v)
            for v in versions.values()
        ),
        "Unsafe version evidence",
    )
    value = {k: value[k] for k in ("status", "modules", "providers", "versions")}
    value.update(
        generation=label,
        scope="imports only; no GUI/renderer/lifecycle claim",
        runtime=native.verify_runtime(),
    )
    (attempt / (operation + ".json")).write_bytes(core.encode(value))
    return value


def application_update(native, commit, source):
    """Normal dependency resolution; verify exact app identity before proceeding."""
    core.require(core.SHA.fullmatch(commit) is not None, "Invalid application commit")
    native.verify_remote(core.APP_ID)
    native.run(
        "update",
        "update",
        "--noninteractive",
        "--no-related",
        "--commit=" + commit,
        core.APP_ID,
    )
    core.require(
        native.commit(core.APP_ID) == commit, "Application transaction commit mismatch"
    )
    native.installed_source(source)
