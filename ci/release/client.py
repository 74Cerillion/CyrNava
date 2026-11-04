"""P5C disposable Flatpak clients. Never launch an app or use normal profiles."""

import base64
import configparser
import os
import re
import stat
import subprocess
import urllib.parse
from pathlib import Path

import core

FIXTURE_ID = core.APP_ID + ".P5CFixture"
MARKER = {"purpose": "P5C disposable Flatpak client"}


class NativeFailure(core.Rejected):
    def __init__(self, operation, category, code):
        self.category = category
        super().__init__(f"Native client failed: {operation} ({category}, exit-{code})")


def failure_category(text):
    if re.search(r"gpg|signature|public key|trusted key", text):
        return "signature"
    if re.search(
        r"checksum|corrupt|invalid.*summary|invalid.*metadata|invalid.*object", text
    ):
        return "integrity"
    if re.search(r"404|no such.*object|couldn.t find.*object|missing.*object", text):
        return "missing-object"
    return "ref-unavailable" if "no such ref" in text else "other"


class Client:
    def __init__(self, root):
        self.root = core.outside_source(root)
        self.root.mkdir(mode=0o700)
        (self.root / ".p5c-client").write_bytes(core.encode(MARKER))
        self.env = {"PATH": os.defpath, "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}
        for key, name in {
            "FLATPAK_USER_DIR": "flatpak",
            "GNUPGHOME": "gnupg",
            "XDG_DATA_HOME": "data",
            "XDG_CONFIG_HOME": "config",
            "XDG_CACHE_HOME": "cache",
            "XDG_RUNTIME_DIR": "runtime",
            "TMPDIR": "tmp",
        }.items():
            path = self.root / name
            path.mkdir(mode=0o700)
            self.env[key] = str(path)
        self.operations = []

    def guard(self):
        core.safe_path(self.root)
        core.require(
            self.root.stat().st_uid == os.getuid()
            and stat.S_IMODE(self.root.stat().st_mode) == 0o700
            and (self.root / ".p5c-client").is_file()
            and core.read_json(self.root / ".p5c-client") == MARKER,
            "Disposable client marker/ownership required",
        )
        for key in self.env:
            if key not in {"PATH", "LANG", "LC_ALL"}:
                core.require(
                    Path(self.env[key]).parent == self.root,
                    "Client environment escaped isolation",
                )
                core.safe_path(self.env[key])

    def run(self, operation, *args):
        core.require(
            operation in {"install", "update", "commit", "location", "remote", "list"},
            "Unreviewed client operation",
        )
        self.guard()
        try:
            r = subprocess.run(
                ["flatpak", "--user", *map(str, args)],
                env=self.env,
                capture_output=True,
                timeout=300,
            )
        except (OSError, subprocess.SubprocessError):
            raise NativeFailure(operation, "unavailable-or-timeout", -1) from None
        text = r.stderr.decode(errors="replace").lower()
        self.operations.append(
            {
                "operation": operation,
                "exit_code": r.returncode,
                "namespace_warning": "bwrap:" in text,
            }
        )
        if r.returncode:
            category = failure_category(text)
            if category in {"other", "ref-unavailable"} and operation in {
                "install",
                "update",
            }:
                # Flatpak can hide a bad signature behind "No such ref". Verify
                # the same isolated remote summary with OSTree before classifying.
                cfg = configparser.ConfigParser(interpolation=None)
                cfg.read(self.root / "flatpak/repo/config")
                remotes = [
                    s[8:-1]
                    for s in cfg.sections()
                    if s.startswith('remote "') and s.endswith('"')
                ]
                if len(remotes) == 1:
                    probe = subprocess.run(
                        [
                            "ostree",
                            "--repo=" + str(self.root / "flatpak/repo"),
                            "remote",
                            "summary",
                            remotes[0],
                        ],
                        env=self.env,
                        capture_output=True,
                        timeout=60,
                    )
                    diagnostic = failure_category(
                        probe.stderr.decode(errors="replace").lower()
                    )
                    self.operations.append(
                        {
                            "operation": "diagnose-summary",
                            "exit_code": probe.returncode,
                            "category": diagnostic,
                        }
                    )
                    if probe.returncode and diagnostic in {"signature", "integrity"}:
                        category = diagnostic
            raise NativeFailure(operation, category, r.returncode)
        return r.stdout.decode().strip()

    def commit(self, app_id):
        core.require(
            app_id in {core.APP_ID, FIXTURE_ID}, "Unapproved client application ID"
        )
        value = self.run("commit", "info", "--show-commit", app_id)
        core.require(core.SHA.fullmatch(value) is not None, "Invalid installed commit")
        return value

    def verify_remote(self, app_id):
        name = self.run("remote", "info", "--show-origin", app_id)
        config = configparser.ConfigParser(interpolation=None)
        config.read(self.root / "flatpak/repo/config")
        section = 'remote "' + name + '"'
        core.require(
            config.getboolean(section, "gpg-verify", fallback=False)
            and config.getboolean(section, "gpg-verify-summary", fallback=False),
            "Both commit and summary GPG verification required",
        )
        return name

    def install(self, descriptor, key, fingerprint, app_id, expected):
        validate_descriptor(descriptor, key, fingerprint, self.root, app_id)
        cfg = configparser.ConfigParser(interpolation=None)
        cfg.read(descriptor)
        ref = cfg["Flatpak Ref"]
        native = configparser.ConfigParser(interpolation=None)
        native.optionxform = str
        native["Flatpak Repo"] = {
            "Title": "P5C disposable verification",
            "Url": ref["Url"],
            "GPGKey": ref["GPGKey"],
        }
        path = self.root / "remote.flatpakrepo"
        with path.open("w") as stream:
            native.write(stream)
        self.run("remote", "remote-add", "--from", "p5c", path)
        self.verify_summary()
        self.run(
            "install",
            "install",
            "--noninteractive",
            "--no-deps",
            "--no-related",
            descriptor,
        )
        core.require(
            self.commit(app_id) == expected, "Installed application commit mismatch"
        )
        self.verify_remote(app_id)
        return {
            "status": "PASS",
            "commit": expected,
            "runtime_fetch": "DISABLED; application launch not tested",
        }

    def verify_summary(self):
        self.guard()
        cfg = configparser.ConfigParser(interpolation=None)
        cfg.read(self.root / "flatpak/repo/config")
        core.require(
            cfg.getboolean('remote "p5c"', "gpg-verify", fallback=False)
            and cfg.getboolean('remote "p5c"', "gpg-verify-summary", fallback=False),
            "Both native signature checks required before installation",
        )
        r = subprocess.run(
            [
                "ostree",
                "--repo=" + str(self.root / "flatpak/repo"),
                "remote",
                "summary",
                "p5c",
            ],
            env=self.env,
            capture_output=True,
            timeout=60,
        )
        if r.returncode:
            raise NativeFailure(
                "summary",
                failure_category(r.stderr.decode(errors="replace").lower()),
                r.returncode,
            )

    def update(self, app_id, expected):
        self.verify_remote(app_id)
        self.run(
            "update", "update", "--noninteractive", "--no-deps", "--no-related", app_id
        )
        core.require(
            self.commit(app_id) == expected, "Updated application commit mismatch"
        )

    def installed_source(self, expected):
        location = Path(
            self.run("location", "info", "--show-location", core.APP_ID)
        ).resolve()
        core.require(
            location.is_relative_to(self.root / "flatpak"),
            "Deployment escaped isolated client",
        )
        value = core.read_json(location / "files/share/cyrnava/build-inputs.json")
        core.require(
            value.get("git_commit") == expected, "Installed application source mismatch"
        )
        return expected


def fingerprint(key, parent):
    home = parent / "pk"
    home.mkdir(mode=0o700, exist_ok=True)
    data = core.gpg(home, "--with-colons", "--show-keys", key).decode()
    core.require(
        sum(line.startswith("pub:") for line in data.splitlines()) == 1,
        "Exactly one staging primary key required",
    )
    return next(
        line.split(":")[9] for line in data.splitlines() if line.startswith("fpr:")
    )


def validate_descriptor(path, key, expected_fingerprint, parent, app_id):
    core.require(
        core.FINGERPRINT.fullmatch(expected_fingerprint) is not None,
        "Full independent staging fingerprint required",
    )
    core.require(
        fingerprint(key, parent) == expected_fingerprint,
        "Staging public key fingerprint mismatch",
    )
    core.require(Path(path).stat().st_size < 128 * 1024, "Descriptor too large")
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.read(path)
    core.require(cfg.sections() == ["Flatpak Ref"], "Invalid Flatpak ref descriptor")
    ref = cfg["Flatpak Ref"]
    core.require(
        ref.get("Name") == app_id
        and ref.get("Branch") == "stable"
        and ref.get("IsRuntime", "").lower() == "false",
        "Descriptor identity mismatch",
    )
    core.require(
        set(ref)
        <= {"title", "name", "branch", "isruntime", "url", "gpgkey", "runtimerepo"},
        "Unexpected descriptor capability",
    )
    core.require(
        base64.b64decode(ref["GPGKey"], validate=True) == Path(key).read_bytes(),
        "Descriptor does not contain trusted staging key",
    )
    url = urllib.parse.urlsplit(ref["Url"])
    core.require(
        not url.username and not url.password and not url.query and not url.fragment,
        "Descriptor credentials or extra URL fields forbidden",
    )
    core.require(
        (
            url.scheme == "file"
            and url.netloc in {"", "localhost"}
            and url.path.startswith("/")
        )
        or (url.scheme == "http" and url.hostname == "127.0.0.1" and url.port),
        "Only filesystem or literal loopback staging transport permitted",
    )
    if url.scheme == "file":
        target = Path(urllib.parse.unquote(url.path)).resolve()
        core.require(
            target.is_relative_to(parent.parent.resolve()),
            "Filesystem descriptor escaped disposable integration root",
        )
    return True
