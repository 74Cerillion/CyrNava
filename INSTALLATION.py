#!/usr/bin/env python3
"""Run the CyrNava installer with internal-SSD paths and isolated tool settings."""
import argparse
import hashlib
import os
from pathlib import Path
import pwd
import re
import stat
import sys

COMMIT = "2bfbd40987005e8853d5d00abdf365300ee4c43d"
INSTALLER_SHA256 = "f1e6a3fecbf8585fe21f6e4cafe3bc64a76af22725c65ddfe0928cc6ee998891"
HDD_UUID = "654ea074-837a-435e-a6c0-a8ea41cdf5db"


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def mounts():
    result = []
    for line in Path("/proc/self/mountinfo").read_text().splitlines():
        before, after = line.split(" - ", 1)
        fields = before.split()
        point = re.sub(r"\\([0-7]{3})",
                       lambda match: chr(int(match[1], 8)), fields[4])
        result.append(Path(point))
    return result


def ssd_device():
    device = Path("/").stat().st_dev
    major, minor = os.major(device), os.minor(device)
    sysfs = Path(f"/sys/dev/block/{major}:{minor}").resolve(strict=True)
    disks = [p for p in (sysfs, *sysfs.parents)
             if (p / "queue/rotational").is_file()]
    require(bool(disks), "Cannot identify the internal root disk.")
    disk = disks[0]
    require(re.fullmatch(r"nvme\d+n\d+", disk.name)
            and (disk / "queue/rotational").read_text().strip() == "0"
            and (disk / "removable").read_text().strip() == "0",
            "This guard expects your internal NVMe SSD; storage review is needed.")
    return device


def on_ssd(path, device, points, nested=True):
    path = Path(path)
    require(path.is_absolute() and ".." not in path.parts,
            f"Unsafe path: {path}")
    for part in (path, *path.parents):
        require(not part.is_symlink(), f"Symlinked storage path refused: {part}")
        if part.exists():
            require(part.stat().st_dev == device, f"Path is not on the SSD: {part}")
    for point in points:
        if point == Path("/"):
            continue
        overlap = point == path or point in path.parents
        if nested:
            overlap = overlap or path in point.parents
        require(not overlap, f"Mounted/bind-mounted path needs review: {point}")
    return path


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    require(os.geteuid() != 0, "Run as your normal user, without sudo.")
    require(sys.stdin.isatty(), "Use a normal Ubuntu terminal.")
    require(os.environ.get("XDG_SESSION_TYPE") == "wayland"
            and "GNOME" in os.environ.get("XDG_CURRENT_DESKTOP", "").upper(),
            "Use your GNOME Wayland desktop session.")
    require(not Path("/dev/disk/by-uuid", HDD_UUID).exists(),
            "Safely eject and physically disconnect the development HDD first.")
    points = mounts()
    require(Path("/run/media/cerillion/C") not in points,
            "The development HDD is still mounted; eject it normally first.")
    device = ssd_device()
    account = pwd.getpwuid(os.getuid())
    home = on_ssd(Path(account.pw_dir), device, points, nested=False)
    require(Path.home() == home, "HOME differs from your account home.")
    here = Path(__file__).resolve().parent
    installer = on_ssd(here / "install_cyrnava.py", device, points)
    require(installer.is_file(), "Save install_cyrnava.py beside this launcher.")
    with installer.open("rb") as file:
        require(hashlib.file_digest(file, "sha256").hexdigest() == INSTALLER_SHA256,
                "Installer checksum differs from the reviewed script above.")

    data = home / ".local/share"
    state = home / ".local/state"
    cache = home / ".cache"
    config = home / ".config"
    base = state / "cyrnava-setup"
    session = base / COMMIT
    temporary = session / "tmp"
    paths = [
        here, config, cache, data / "applications",
        data / "cyrnava-application", data / "cyrnava/native", base,
        Path("/usr"), Path("/etc/apt"), Path("/etc/ssl"),
        Path("/var/cache/apt"), Path("/var/lib/apt"), Path("/var/lib/dpkg"),
    ]
    for path in paths:
        on_ssd(path, device, points)
    python = Path("/usr/bin/python3").resolve(strict=True)
    on_ssd(python, device, points)

    runtime = Path(f"/run/user/{os.getuid()}")
    require(runtime.is_dir() and runtime.stat().st_uid == os.getuid()
            and not runtime.is_symlink(), "Owner desktop runtime is unavailable.")
    display = os.environ.get("WAYLAND_DISPLAY", "")
    require(re.fullmatch(r"wayland-\d+", display),
            "An ordinary GNOME Wayland display is required.")
    require((runtime / display).is_socket() and (runtime / "bus").is_socket(),
            "Wayland/session-bus sockets are unavailable.")
    for path in (base, session, temporary):
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        on_ssd(path, device, mounts())
        info = path.stat()
        require(info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o700,
                f"Private directory must belong to you and have mode 0700: {path}")

    env = {
        "HOME": str(home), "USER": account.pw_name, "LOGNAME": account.pw_name,
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
        "XDG_DATA_HOME": str(data), "XDG_STATE_HOME": str(state),
        "XDG_CACHE_HOME": str(cache), "XDG_CONFIG_HOME": str(config),
        "XDG_DATA_DIRS": "/usr/local/share:/usr/share",
        "XDG_CONFIG_DIRS": "/etc/xdg",
        "XDG_RUNTIME_DIR": str(runtime),
        "XDG_SESSION_TYPE": "wayland", "XDG_CURRENT_DESKTOP": "GNOME",
        "WAYLAND_DISPLAY": display,
        "DBUS_SESSION_BUS_ADDRESS": f"unix:path={runtime}/bus",
        "TMPDIR": str(temporary), "TMP": str(temporary), "TEMP": str(temporary),
        "PIP_CONFIG_FILE": "/dev/null", "PIP_CACHE_DIR": str(session / "pip-cache"),
        "NPM_CONFIG_USERCONFIG": "/dev/null", "NPM_CONFIG_GLOBALCONFIG": "/dev/null",
        "NPM_CONFIG_CACHE": str(session / "npm-cache"),
    }
    os.chdir(home)
    print(f"SSD verified. Program: {data / 'cyrnava-application'}", flush=True)
    print(f"Live data: {data / 'cyrnava/native'}", flush=True)
    print(f"Source/build tools/temp: {session}", flush=True)
    os.execve(python, [str(python), "-B", "-I", str(installer)], env)


if __name__ == "__main__":
    os.umask(0o077)
    try:
        main()
    except (OSError, RuntimeError, ValueError, EOFError, KeyboardInterrupt) as error:
        print(f"STOP: {error}", file=sys.stderr)
        sys.exit(1)