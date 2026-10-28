#!/usr/bin/env python3
"""One-time per-user source installation. Never opens or moves a CyrNava profile."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

from launcher import (
    LaunchError,
    locked,
    private_directory,
    process_matches,
    read_state,
    stop,
)

REPOSITORY = Path(__file__).resolve().parents[1]


def xdg(name, fallback):
    value = Path(os.environ.get(name, ""))
    return value if value.is_absolute() else Path.home() / fallback


def run(command, cwd=None):
    subprocess.run([str(part) for part in command], cwd=cwd, check=True)


def desktop_quote(value):
    if any(c in str(value) for c in "\n\r\0"):
        raise LaunchError("Installation path cannot contain control characters.")
    text = str(value).replace("\\", "\\\\\\\\")
    for character in ['"', "`", "$"]:
        text = text.replace(character, "\\\\" + character)
    return '"' + text.replace("%", "%%") + '"'


def write_atomic(path, content, mode=0o600):
    if path.is_symlink():
        raise LaunchError(f"Refusing symlink destination: {path}")
    temporary = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(content)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def entry(root, python, icon, *, stop=False):
    command = f"{desktop_quote(python)} {desktop_quote(root / 'launcher.py')} "
    command += f"--config {desktop_quote(root / 'config.json')}"
    if stop:
        return (
            "[Desktop Entry]\nType=Application\nName=Stop CyrNava\n"
            "Comment=Wait for Saved, then stop the local CyrNava server\n"
            f"Exec={command} stop\n"
            f"Icon={icon}\n"
            "Terminal=false\nCategories=Office;\n"
        )
    return (
        "[Desktop Entry]\nVersion=1.0\nType=Application\nName=CyrNava\n"
        "Comment=Local-first cybersecurity knowledge workspace\n"
        f"Exec={command} open\nIcon={icon}\nTerminal=false\n"
        "Categories=Office;\nActions=Stop;Logs;\n\n"
        "[Desktop Action Stop]\nName=Stop CyrNava (wait for Saved)\n"
        f"Exec={command} stop\n\n[Desktop Action Logs]\nName=Open diagnostic logs\n"
        f"Exec={command} logs\n"
    )


def install(args):
    if not sys.platform.startswith("linux") or sys.version_info[:2] != (3, 12):
        raise LaunchError(
            "Use Python 3.12 on Ubuntu Linux: python3.12 desktop/install.py"
        )
    if not 1 <= args.port <= 65535:
        raise LaunchError("Port must be between 1 and 65535.")
    node, npm = shutil.which("node"), shutil.which("npm")
    opener, zenity = shutil.which("xdg-open"), shutil.which("zenity")
    browser = shutil.which("firefox")
    if not browser:
        raise LaunchError("Firefox is required for normal CyrNava desktop launches.")
    if not node or not npm:
        raise LaunchError(
            "Build tools missing: install Node 24.19.0/npm 11.6.2, then retry. "
            "If using nvm, run nvm use once for installation only."
        )
    if not opener or not zenity:
        raise LaunchError(
            "Desktop tools missing: sudo apt install xdg-utils zenity. "
            "The installer never runs sudo itself."
        )
    if subprocess.check_output([node, "--version"], text=True).strip() != "v24.19.0":
        raise LaunchError("Build requires pinned Node 24.19.0 (.nvmrc).")
    if subprocess.check_output([npm, "--version"], text=True).strip() != "11.6.2":
        raise LaunchError("Build requires pinned npm 11.6.2.")
    data_home = xdg("XDG_DATA_HOME", ".local/share").resolve()
    # Stable installation/state/desktop IDs update existing icons in place.
    root = data_home / "engage-application"
    state = xdg("XDG_STATE_HOME", ".local/state").resolve() / "engage-launcher"
    private_directory(root)
    private_directory(state)
    # The same lock coordinates installer updates, launcher startup and shutdown.
    with locked(state / "launcher.lock"):
        config_path = root / "config.json"
        existing_config = {}
        if config_path.exists():
            existing_config = json.loads(config_path.read_text())
            config = existing_config
            if config["data_home"] != str(data_home) or config["state_dir"] != str(
                state
            ):
                raise LaunchError(
                    "Existing configuration differs. Refusing a data-path change."
                )
            if process_matches(read_state(config)):
                raise LaunchError(
                    "CyrNava is running. Wait for Saved, then use Stop CyrNava "
                    "before updating."
                )
        release = (
            root
            / "releases"
            / (time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8])
        )
        release.mkdir(parents=True, mode=0o700)
        old_config = config_path.read_text() if config_path.exists() else None
        launcher = root / "launcher.py"
        old_launcher = launcher.read_text() if launcher.exists() else None
        try:
            # Source only: no repository venv, database, captures or personal config.
            shutil.copytree(
                REPOSITORY / "backend/app",
                release / "backend/app",
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
            shutil.copy2(
                REPOSITORY / "backend/requirements.txt",
                release / "backend/requirements.txt",
            )
            run([sys.executable, "-m", "venv", release / "backend/.venv"])
            python = release / "backend/.venv/bin/python"
            run(
                [
                    python,
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    release / "backend/requirements.txt",
                ]
            )
            run([python, "-m", "pip", "check"])
            run([npm, "ci"], REPOSITORY / "frontend")
            run([npm, "run", "build"], REPOSITORY / "frontend")
            shutil.copytree(REPOSITORY / "frontend/dist", release / "frontend/dist")
            shutil.copy2(
                REPOSITORY / "frontend/package.json", release / "frontend/package.json"
            )
            # Verify startup using a fresh synthetic profile, never the user's DB.
            import socket
            import tempfile

            with tempfile.TemporaryDirectory(
                prefix="cyrnava-install-check-"
            ) as temporary:
                check = Path(temporary)
                with socket.socket() as probe:
                    probe.bind(("127.0.0.1", 0))
                    port = probe.getsockname()[1]
                check_config = {
                    "release": str(release),
                    "data_home": str(check / "data"),
                    "state_dir": str(check / "state"),
                    "port": port,
                    "opener": opener,
                    "zenity": zenity,
                }
                private_directory(check / "state")
                (check / "config.json").write_text(json.dumps(check_config))
                source_launcher = REPOSITORY / "desktop/launcher.py"
                try:
                    run(
                        [
                            sys.executable,
                            source_launcher,
                            "--config",
                            check / "config.json",
                            "start",
                        ]
                    )
                finally:
                    # Stop only the synthetic worker owned by this installation check.
                    stop(check_config)
            write_atomic(
                launcher, (REPOSITORY / "desktop/launcher.py").read_text(), 0o700
            )
            applications = data_home / "applications"
            applications.mkdir(parents=True, exist_ok=True)
            configured_icon = Path(existing_config.get("icon", ""))
            icon = (
                Path(args.icon).resolve()
                if args.icon
                else configured_icon
                if configured_icon.is_file()
                else REPOSITORY / "desktop/icons/cyrnava.svg"
            )
            if not icon.is_file() or icon.suffix.lower() not in (".svg", ".png"):
                raise LaunchError("Icon must be a readable PNG or SVG file.")
            icons = release / "desktop-icons"
            icons.mkdir(mode=0o700)
            target = icons / ("cyrnava" + icon.suffix.lower())
            if target.is_symlink():
                raise LaunchError("Refusing symlink icon destination")
            if icon.suffix.lower() == ".svg":
                write_atomic(target, icon.read_text())
            else:
                temporary_icon = target.with_suffix(".tmp-" + uuid.uuid4().hex)
                with temporary_icon.open("xb") as output:
                    output.write(icon.read_bytes())
                temporary_icon.replace(target)
            config = {
                "release": str(release),
                "data_home": str(data_home),
                "state_dir": str(state),
                "port": args.port,
                "opener": opener,
                "zenity": zenity,
                "browser": browser,
                "icon": str(target),
            }
            write_atomic(config_path, json.dumps(config, indent=2) + "\n")
            base_python = Path(sys.executable).resolve()
            text = entry(root, base_python, target)
            write_atomic(applications / "org.engage.Workspace.desktop", text, 0o700)
            write_atomic(
                applications / "org.engage.Stop.desktop",
                entry(root, base_python, target, stop=True),
                0o700,
            )
            desktop = (
                Path(args.desktop_dir).expanduser().resolve()
                if args.desktop_dir
                else None
            )
            if desktop is None:
                finder = shutil.which("xdg-user-dir")
                if finder:
                    result = subprocess.check_output(
                        [finder, "DESKTOP"], text=True
                    ).strip()
                    if result:
                        desktop = Path(result)
            if desktop and desktop.is_dir() and desktop != Path.home():
                destination = desktop / "org.engage.Workspace.desktop"
                write_atomic(destination, text, 0o700)
                # GNOME may still require the user to choose Allow Launching.
                print(
                    f"Desktop entry: {destination} "
                    "(choose Allow Launching if requested)"
                )
            else:
                print(
                    "No enabled Desktop folder found. "
                    "CyrNava is in the application menu. "
                    "rerun with --desktop-dir PATH for an existing desktop folder."
                )
            updater = shutil.which("update-desktop-database")
            if updater:
                subprocess.run([updater, str(applications)], check=False)
            print(
                f"Installed CyrNava. Open it from the desktop/application menu. "
                f"Logs: {state}"
            )
            print(
                "Previous installation releases are retained for rollback; "
                "application data is untouched."
            )
        except BaseException:
            if old_config is not None:
                write_atomic(config_path, old_config)
            else:
                config_path.unlink(missing_ok=True)
            if old_launcher is not None:
                write_atomic(launcher, old_launcher, 0o700)
            else:
                launcher.unlink(missing_ok=True)
            shutil.rmtree(release, ignore_errors=True)
            raise


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(
        description="Install CyrNava for this Ubuntu desktop user"
    )
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--desktop-dir", help="Override detected XDG desktop folder")
    parser.add_argument(
        "--icon", help="Owner-approved PNG/SVG; otherwise use placeholder"
    )
    args = parser.parse_args()
    try:
        install(args)
    except (LaunchError, OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"CyrNava installation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
