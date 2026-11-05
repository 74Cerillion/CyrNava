#!/usr/bin/env python3
"""Install CyrNava 0.1.0 on Ubuntu 26.04 x86_64 GNOME Wayland.

Run from your desktop terminal, without sudo:
    /usr/bin/python3 -B -I install_cyrnava.py

Optional read-only preflight:
    /usr/bin/python3 -B -I install_cyrnava.py --check

Requires internet access, sudo permission and at least 4 GiB free space.
All application/build/data paths stay on the Ubuntu OS filesystem.
Existing installations, profiles and conflicting providers are never deleted.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import pwd
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

COMMIT = "2bfbd40987005e8853d5d00abdf365300ee4c43d"
REPO = "https://github.com/74Cerillion/CyrNava.git"
NODE = "24.19.0"
NODE_SHA256 = "14b342e71204f811bde6153be8e04b62aef63c236fef92b55f9c83154b409647"

PACKAGES = """
ca-certificates git python3.14 python3.14-venv build-essential
desktop-file-utils apparmor apparmor-utils libglib2.0-bin
libnss3 libnspr4 libasound2t64 libegl1 libopengl0 libxkbcommon-x11-0
libxcb-cursor0 libxcomposite1 libxdamage1 libxrandr2 libxtst6 libfontconfig1
""".split()

STAGE, SESSION, ENV = "startup", None, None


def check(ok, reason):
    if not ok:
        raise RuntimeError(reason)


def safe_path(value):
    p = Path(value)
    check(
        p.is_absolute() and ".." not in p.parts
        and not any(ord(c) < 32 or ord(c) == 127 for c in str(p)),
        "Unsafe filesystem path.",
    )
    check(
        not any(q.is_symlink() for q in (p, *p.parents)),
        f"Symlinked path refused: {p}",
    )
    return p


def storage(path):
    """Persistent installation paths must stay on the OS filesystem."""
    path = safe_path(path)
    device = Path("/").stat().st_dev
    for part in (path, *path.parents):
        if part.exists():
            check(
                part.stat().st_dev == device,
                f"Path is outside the OS filesystem: {part}",
            )
    for line in Path("/proc/self/mountinfo").read_text().splitlines():
        raw = line.split(" - ", 1)[0].split()[4]
        point = Path(re.sub(
            r"\\([0-7]{3})", lambda m: chr(int(m[1], 8)), raw,
        ))
        if point != Path("/"):
            check(
                not (
                    point == path or point in path.parents
                    or path in point.parents
                ),
                f"Mounted path overlaps installation storage: {point}",
            )
    return path


def private(p):
    storage(p)
    p.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = p.stat()
    check(
        info.st_uid == os.getuid()
        and stat.S_IMODE(info.st_mode) == 0o700,
        f"Directory must belong to you and have mode 0700: {p}",
    )


def run(*args, env=None, capture=False):
    result = subprocess.run(
        [str(a) for a in args],
        check=True,
        text=True,
        env=env,
        stdout=subprocess.PIPE if capture else None,
    )
    return result.stdout.strip() if capture else None


def approve(message, expected):
    check(
        input(f"{message}\nType {expected} to continue: ").strip() == expected,
        "Not approved; stopped.",
    )


def save(path, value):
    fd, name = tempfile.mkstemp(prefix="state-", dir=path.parent)
    with os.fdopen(fd, "w") as out:
        json.dump(value, out, indent=2)
        out.write("\n")
        out.flush()
        os.fsync(out.fileno())
    Path(name).replace(path)


def empty_config(path):
    storage(path)
    try:
        fd = os.open(
            path,
            os.O_CREAT | os.O_EXCL | os.O_RDONLY | os.O_NOFOLLOW,
            0o600,
        )
    except FileExistsError:
        fd = os.open(
            path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
        )
    try:
        info = os.fstat(fd)
        check(
            stat.S_ISREG(info.st_mode)
            and info.st_uid == os.getuid()
            and stat.S_IMODE(info.st_mode) == 0o600
            and info.st_nlink == 1
            and info.st_size == 0,
            f"Unsafe npm configuration: {path}",
        )
    finally:
        os.close(fd)
    return str(path)


def git(source, *args, capture=False):
    env = dict(
        ENV,
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL="/dev/null",
        GIT_TERMINAL_PROMPT="0",
    )
    return run(
        "/usr/bin/git", "-c", "core.hooksPath=/dev/null",
        "-C", source, *args, env=env, capture=capture,
    )


def verify_source(source):
    metadata = safe_path(source / ".git")
    check(
        metadata.is_dir()
        and not (metadata / "objects/info/alternates").exists()
        and not (metadata / "commondir").exists(),
        "External Git metadata/object stores are not supported.",
    )
    check(
        git(source, "rev-parse", "HEAD", capture=True) == COMMIT
        and git(source, "remote", "get-url", "origin", capture=True) == REPO
        and not git(
            source, "status", "--porcelain",
            "--untracked-files=all", capture=True,
        ),
        "Retained source differs from the pinned commit.",
    )


def source_ready(source):
    if not source.exists():
        candidate = Path(tempfile.mkdtemp(prefix="source-", dir=SESSION))
        git(candidate, "init", "--quiet")
        git(candidate, "remote", "add", "origin", REPO)
        git(candidate, "fetch", "--depth=1", "origin", COMMIT)
        git(candidate, "checkout", "--quiet", "--detach", "FETCH_HEAD")
        verify_source(candidate)
        candidate.rename(source)
    verify_source(source)


def fetch(url, path):
    with urllib.request.urlopen(url, timeout=120) as response:
        check(
            response.url.startswith("https://nodejs.org/"),
            "Unexpected Node redirect.",
        )
        with path.open("xb") as out:
            shutil.copyfileobj(response, out)


def node_ok(env):
    try:
        return bool(
            re.fullmatch(
                r"v24\.\d+\.\d+",
                run("node", "--version", env=env, capture=True),
            )
            and re.fullmatch(
                r"11\.\d+\.\d+",
                run("npm", "--version", env=env, capture=True),
            )
        )
    except (OSError, subprocess.CalledProcessError):
        return False


def provide_node(env, session):
    print(
        f"Downloading private official Node {NODE}; "
        "global Node stays unchanged."
    )
    tools = Path(tempfile.mkdtemp(prefix="node-", dir=session))
    name = f"node-v{NODE}-linux-x64"
    archive = tools / (name + ".tar.xz")
    url = f"https://nodejs.org/dist/v{NODE}/"
    fetch(url + archive.name, archive)

    with archive.open("rb") as file:
        actual = hashlib.file_digest(file, "sha256").hexdigest()
    check(actual == NODE_SHA256, "Official Node archive checksum mismatch.")

    with tarfile.open(archive, "r:xz") as package:
        check(
            all(
                m.name == name or m.name.startswith(name + "/")
                for m in package.getmembers()
            ),
            "Unexpected Node archive layout.",
        )
        package.extractall(tools, filter="data")

    env["PATH"] = str(tools / name / "bin") + os.pathsep + env["PATH"]
    check(
        node_ok(env),
        "Downloaded Node/npm versions do not satisfy the installer.",
    )


def identity(source, root, env):
    code = """
import importlib.util, sys
from pathlib import Path
source, root = map(Path, sys.argv[1:])
spec = importlib.util.spec_from_file_location(
    "setup_engine", source / "desktop/install_engine.py")
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
engine.host_supported()
engine.deployment_paths(root, False)
current = engine.load(root / "current.json")
release = root / "releases" / engine.member_name(current["release"])
receipt, manifest = engine.installed(release)
assert manifest["kind"] == "release"
assert receipt["trust"]["mode"] == "source-online-reviewed-code"
print(receipt["manifest_sha256"])
"""
    value = run(
        "/usr/bin/python3.14", "-B", "-I", "-c", code,
        source, root, env=env, capture=True,
    )
    check(re.fullmatch(r"[0-9a-f]{64}", value), "Invalid installed manifest.")
    return value


def setup_policy(source, root, manifest, env):
    parent = Path(tempfile.mkdtemp(prefix="policy-", dir=SESSION))
    tool = [
        "/usr/bin/python3.14", "-B", "-I",
        source / "packaging/native/policy_setup.py",
    ]
    options = ["--root", root, "--manifest-sha256", manifest]
    prepared = parent / "prepare"
    run(*tool, "prepare", *options, "--output", prepared, env=env)

    result = json.loads((prepared / "result.json").read_text())
    name, digest = result["profile"], result["policy_sha256"]
    check(
        result["status"] == "PREPARED"
        and result["parser"] == "PASS"
        and re.fullmatch(r"cyrnava-native-u\d+-[0-9a-f]{32}", name)
        and re.fullmatch(r"[0-9a-f]{64}", digest),
        "Policy preparation failed.",
    )
    with (prepared / name).open("rb") as stream:
        check(
            hashlib.file_digest(stream, "sha256").hexdigest() == digest,
            "Prepared policy hash mismatch.",
        )

    expected = {"state": "PRESENT", "profile": name, "mode": "enforce"}
    existing = safe_path(Path("/etc/apparmor.d") / name)

    if result["kernel_before"] == expected:
        info = existing.stat()
        with existing.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        check(
            stat.S_ISREG(info.st_mode)
            and info.st_uid == 0
            and info.st_nlink == 1
            and not info.st_mode & 0o022
            and actual == digest,
            "Existing AppArmor policy differs.",
        )
        print("Exact application AppArmor policy is already loaded in enforce mode.")
        return digest

    check(
        result["kernel_before"] == {"state": "ABSENT", "profile": name}
        and not existing.exists(),
        "Existing/partially loaded policy needs review; preserved.",
    )
    print(
        "\nReview this application-specific AppArmor policy:\n"
        + (prepared / name).read_text()
    )
    print("It retains ordinary-user access ('allow all') and permits the app's")
    print("sandbox namespaces; it is not a restrictive filesystem policy.")
    approve("Approve loading this exact policy? SHA-256:", digest)

    run("/usr/bin/sudo", "-v", env=env)
    loaded = parent / "load"
    run(
        *tool, "load", "--owner-host", *options,
        "--policy-sha256", digest, "--output", loaded, env=env,
    )
    result = json.loads((loaded / "result.json").read_text())
    check(
        result["status"] == "PASS" and result["kernel_after"] == expected,
        "AppArmor load/enforce verification failed.",
    )
    return digest


def main():
    global STAGE, SESSION, ENV

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true",
        help="Read-only host/package preflight; do not install",
    )
    args = parser.parse_args()

    check(os.geteuid() != 0, "Run as your normal desktop user, without sudo.")
    check(sys.stdin.isatty(), "Run the saved script in an Ubuntu terminal.")
    check(sys.version_info >= (3, 12), "System Python 3.12 or newer is required.")

    release = platform.freedesktop_os_release()
    check(
        release.get("ID") == "ubuntu"
        and release.get("VERSION_ID") == "26.04"
        and platform.machine() == "x86_64",
        "This release requires Ubuntu 26.04 x86_64.",
    )
    check(
        os.environ.get("XDG_SESSION_TYPE") == "wayland"
        and "GNOME" in os.environ.get("XDG_CURRENT_DESKTOP", "").upper()
        and not Path("/.flatpak-info").exists(),
        "Use a native GNOME Wayland desktop terminal.",
    )
    check(
        Path("/proc/self/attr/current").read_text().strip() == "unconfined"
        and "NoNewPrivs:\t0" in Path("/proc/self/status").read_text(),
        "Use a normal unconfined owner terminal, not a sandbox.",
    )
    check(
        Path("/sys/module/apparmor/parameters/enabled").read_text().strip() == "Y"
        and Path("/proc/sys/kernel/apparmor_restrict_unprivileged_userns")
        .read_text().strip() == "1",
        "Expected Ubuntu AppArmor settings unavailable; no bypass supplied.",
    )

    account = pwd.getpwuid(os.getuid())
    home = safe_path(Path(account.pw_dir))
    check(Path.home() == home, "HOME differs from your account home.")

    data, state = home / ".local/share", home / ".local/state"
    root, profile = data / "cyrnava-application", data / "cyrnava/native"
    base = state / "cyrnava-setup"
    SESSION = base / COMMIT

    for path in (
        root, profile, data / "applications", base,
        home / ".cache", home / ".config",
        Path("/usr"), Path("/etc/apt"), Path("/etc/ssl"),
        Path("/etc/apparmor.d"), Path("/var/cache/apt"),
        Path("/var/lib/apt"), Path("/var/lib/dpkg"),
    ):
        storage(path)

    runtime = safe_path(Path(f"/run/user/{os.getuid()}"))
    display = os.environ.get("WAYLAND_DISPLAY", "")
    check(
        runtime.is_dir()
        and runtime.stat().st_uid == os.getuid()
        and re.fullmatch(r"wayland-\d+", display)
        and (runtime / display).is_socket()
        and (runtime / "bus").is_socket(),
        "Owner Wayland/session-bus sockets unavailable.",
    )

    print(
        f"Version: 0.1.0\nSource: {COMMIT}\nApplication: {root}"
        f"\nData: {profile}\nSource/build tools/cache: {SESSION}"
    )

    missing = []
    for package in PACKAGES:
        query = subprocess.run(
            [
                "/usr/bin/dpkg-query", "-W",
                "-f=${db:Status-Status}", package,
            ],
            text=True, capture_output=True,
        )
        if query.returncode or query.stdout.strip() != "installed":
            missing.append(package)

    print("Missing Ubuntu packages: " + (" ".join(missing) if missing else "none"))

    if args.check:
        print("Host preflight passed. No installation or changes performed.")
        return

    os.chdir(home)
    for directory in (base, SESSION, SESSION / "tmp"):
        private(directory)

    fd = os.open(base / "lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    lock = os.fdopen(fd, "r+")
    info = os.fstat(lock.fileno())
    check(
        stat.S_ISREG(info.st_mode)
        and info.st_uid == os.getuid()
        and info.st_nlink == 1
        and not info.st_mode & 0o077,
        "Unsafe setup lock.",
    )
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)

    env = {
        "HOME": str(home),
        "USER": account.pw_name,
        "LOGNAME": account.pw_name,
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "TERM": os.environ.get("TERM", "xterm"),
        "XDG_DATA_HOME": str(data),
        "XDG_STATE_HOME": str(state),
        "XDG_CACHE_HOME": str(home / ".cache"),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "XDG_DATA_DIRS": "/usr/local/share:/usr/share",
        "XDG_CONFIG_DIRS": "/etc/xdg",
        "XDG_RUNTIME_DIR": str(runtime),
        "XDG_SESSION_TYPE": "wayland",
        "XDG_CURRENT_DESKTOP": "GNOME",
        "WAYLAND_DISPLAY": display,
        "DBUS_SESSION_BUS_ADDRESS": f"unix:path={runtime}/bus",
        "TMPDIR": str(SESSION / "tmp"),
        "TMP": str(SESSION / "tmp"),
        "TEMP": str(SESSION / "tmp"),
        "PIP_CONFIG_FILE": "/dev/null",
        "PIP_CACHE_DIR": str(SESSION / "pip-cache"),
        "NPM_CONFIG_USERCONFIG": empty_config(SESSION / "npm-user.conf"),
        "NPM_CONFIG_GLOBALCONFIG": empty_config(SESSION / "npm-global.conf"),
        "NPM_CONFIG_CACHE": str(SESSION / "npm-cache"),
    }
    ENV = env
    os.environ.clear()
    os.environ.update(env)

    source = safe_path(SESSION / "source")
    record_path = safe_path(SESSION / "state.json")
    record = json.loads(record_path.read_text()) if record_path.exists() else None

    if record is not None:
        check(
            record.get("commit") == COMMIT
            and record.get("root") == str(root)
            and record.get("phase") in {"installing", "installed", "ready"},
            "Different setup receipt found; preserve it for review.",
        )

    fresh = record is None or record["phase"] == "installing"
    if fresh:
        check(
            not root.exists() and not profile.exists(),
            "Application/data already exist; nothing will be erased or adopted. "
            "Use the existing installation/update/recovery procedure.",
        )
        check(
            shutil.disk_usage(SESSION).free >= 4 * 1024**3,
            "At least 4 GiB free setup space is required.",
        )
        approve(
            "Install pinned CyrNava and any missing packages listed above?",
            "INSTALL",
        )

        STAGE = "Ubuntu dependencies"
        if missing:
            run("/usr/bin/sudo", "/usr/bin/apt-get", "update", env=env)
            run(
                "/usr/bin/sudo", "/usr/bin/apt-get", "install",
                "--no-install-recommends", "--yes", *missing, env=env,
            )

        STAGE = "pinned GitHub source"
        source_ready(source)

        STAGE = "private Node download/integrity verification"
        provide_node(env, SESSION)

        STAGE = "source integrity and prerequisites"
        run(
            "/bin/bash", source / "install.sh",
            "--check-prerequisites", env=env,
        )

        record = {"commit": COMMIT, "root": str(root), "phase": "installing"}
        save(record_path, record)

        STAGE = "source-first native installation"
        parent = Path(tempfile.mkdtemp(prefix="build-", dir=SESSION))
        run(
            "/bin/bash", source / "install.sh",
            "--root", root, "--work-dir", parent / "work", env=env,
        )
        record["manifest"] = identity(source, root, env)
        record["phase"] = "installed"
        save(record_path, record)

    STAGE = "installed integrity verification"
    verify_source(source)
    check(
        identity(source, root, env) == record["manifest"],
        "Installed identity differs from setup receipt.",
    )

    STAGE = "application-specific AppArmor setup"
    record["policy_sha256"] = setup_policy(
        source, root, record["manifest"], env,
    )
    record["phase"] = "ready"
    save(record_path, record)

    STAGE = "native desktop launch"
    desktop = safe_path(
        data / "applications/io.github._74Cerillion.CyrNava.desktop",
    )
    check(desktop.is_file(), "Native desktop entry is missing.")
    run("/usr/bin/gio", "launch", desktop, env=env)

    print("\nNative CyrNava installed; desktop launch requested.")
    print("Future launches: open CyrNava from Applications.")
    print("Confirm its window opens and a test note saves/reopens.")
    print("Private setup receipts:", SESSION)


if __name__ == "__main__":
    os.umask(0o077)
    try:
        main()
    except (
        OSError, RuntimeError, ValueError, KeyError, EOFError,
        subprocess.SubprocessError, tarfile.TarError, KeyboardInterrupt,
    ) as error:
        print(f"\nSTOP during {STAGE}: {error}", file=sys.stderr)
        if SESSION is not None:
            print("Retain setup evidence:", SESSION, file=sys.stderr)
        sys.exit(1)