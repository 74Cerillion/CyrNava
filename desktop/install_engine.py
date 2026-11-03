"""Native installation/launch engine with explicit N3 stopped-client maintenance."""

import argparse
import contextlib
import fcntl
import hashlib
import importlib.util
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import sysconfig
import tempfile
import time
import uuid
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

APP_ID = "io.github._74Cerillion.CyrNava"
CANDIDATE_ID = "org.cyrnava.CyrNava.Devel"
MAX_ARCHIVE = 512 * 1024**2
MAX_EXPANDED = 1024**3
HEADROOM = 1536 * 1024**2
APPARMOR_CONTRACT = {
    "format": 2,
    "mode": "enforce",
    "abi": "5.0",
    "access": "ordinary-user-allow-all",
}
LEGACY_APPARMOR_CONTRACT = {"format": 1, "mode": "default_allow", "abi": "5.0"}
FORBIDDEN = (
    "FLATPAK_ID",
    "PYTHONPATH",
    "PYTHONHOME",
    "LD_LIBRARY_PATH",
    "LD_PRELOAD",
    "QT_PLUGIN_PATH",
    "QML2_IMPORT_PATH",
    "QML_IMPORT_PATH",
    "QTWEBENGINE_DISABLE_SANDBOX",
    "QTWEBENGINE_CHROMIUM_FLAGS",
    "QTWEBENGINE_REMOTE_DEBUGGING",
    "QTWEBENGINEPROCESS_PATH",
    "QTWEBENGINE_RESOURCES_PATH",
    "QTWEBENGINE_LOCALES_PATH",
)


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def checked_path(path):
    path = Path(path).absolute()
    require(".." not in path.parts, "Parent traversal refused")
    require(
        not any(p.is_symlink() for p in (path, *path.parents)), "Symbolic link refused"
    )
    require(
        not any(ord(c) < 32 or ord(c) == 127 for c in str(path)),
        "Control character in path",
    )
    return path


def private_directory(path):
    path = checked_path(path)
    if not path.exists():
        path.mkdir(mode=0o700, parents=True)
    info = path.stat()
    require(path.is_dir() and info.st_uid == os.getuid(), "Owned directory required")
    require(
        not info.st_mode & 0o077,
        "Private directory required; existing permissions unchanged",
    )
    return path


def regular(path, limit=None):
    path = checked_path(path)
    info = path.stat()
    require(
        stat.S_ISREG(info.st_mode) and info.st_nlink == 1,
        "Regular non-linked file required",
    )
    require(limit is None or info.st_size <= limit, "File exceeds limit")
    return path


def load(path, limit=2 * 1024**2):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result

    return json.loads(regular(path, limit).read_text(), object_pairs_hook=unique)


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic(path, content, mode=0o600):
    path = checked_path(path)
    if path.exists():
        regular(path)
        require(path.stat().st_uid == os.getuid(), "Destination owner mismatch")
    temporary = path.with_name(".n2-" + uuid.uuid4().hex)
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        sync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def durable(path, value):
    atomic(path, (json.dumps(value, sort_keys=True, indent=2) + "\n").encode())


@contextlib.contextmanager
def installation_lock(root):
    private_directory(root)
    path = checked_path(root / ".installation.lock")
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        require(
            stat.S_ISREG(info.st_mode)
            and info.st_uid == os.getuid()
            and info.st_nlink == 1
            and not info.st_mode & 0o077,
            "Unsafe installation lock",
        )
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(fd)


def host_supported():
    require(
        sys.platform == "linux" and platform.machine() == "x86_64",
        "Ubuntu x86_64 required",
    )
    require(
        sys.version_info[:2] == (3, 14)
        and not sysconfig.get_config_var("Py_GIL_DISABLED"),
        "Ordinary CPython 3.14 required",
    )
    require(os.geteuid() != 0, "Per-user operation only")
    release = platform.freedesktop_os_release()
    require(
        release.get("ID") == "ubuntu" and release.get("VERSION_ID") == "26.04",
        "Supported target is Ubuntu 26.04 x86_64",
    )
    require(not Path("/.flatpak-info").exists(), "Native host required")
    require(
        not any(os.environ.get(key) for key in FORBIDDEN),
        "Unsafe loader or sandbox override refused",
    )
    require(
        not os.environ.get("QT_QPA_PLATFORM")
        or os.environ["QT_QPA_PLATFORM"] == "wayland",
        "Only Wayland is supported",
    )


def member_name(name):
    path = PurePosixPath(name)
    require(
        isinstance(name, str)
        and str(path) == name
        and name
        and not path.is_absolute()
        and not any(part in (".", "..") for part in path.parts)
        and "\\" not in name
        and ":" not in name
        and not any(ord(c) < 32 or ord(c) == 127 for c in name),
        "Unsafe archive path",
    )
    return name


def hash_string(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def validate_manifest(manifest):
    require(
        manifest.get("format") == 1
        and manifest.get("kind") in {"candidate", "release"},
        "Unsupported native manifest",
    )
    require(
        re.fullmatch(
            r"[0-9]+\.[0-9]+\.[0-9]+(?:-[a-z0-9.]+)?", manifest.get("version", "")
        ),
        "Unsafe version",
    )
    require(
        manifest.get("target") == "ubuntu-26.04-x86_64-wayland-cpython314",
        "Unsupported target",
    )
    require(hash_string(manifest.get("archive_sha256")), "Missing archive checksum")
    require(
        manifest.get("app_id")
        == (CANDIDATE_ID if manifest["kind"] == "candidate" else APP_ID),
        "Application identity mismatch",
    )
    files = manifest.get("files")
    require(
        isinstance(files, dict) and 1 <= len(files) <= 20000, "Invalid file inventory"
    )
    total = 0
    for name, info in files.items():
        member_name(name)
        require(
            type(info.get("bytes")) is int
            and 0 <= info["bytes"] <= MAX_ARCHIVE
            and hash_string(info.get("sha256"))
            and info.get("mode") in {0o600, 0o700},
            "Invalid file declaration",
        )
        total += info["bytes"]
    require(
        total <= MAX_EXPANDED and total == manifest.get("expanded_bytes"),
        "Expanded size mismatch",
    )
    for required in (
        "launch.py",
        "install_engine.py",
        "provider_check.py",
        "backend_check.py",
        "system_schemas.py",
        "requirements.lock",
        "dependencies.json",
        "application/desktop/native/application.py",
        "application/desktop/native/installed_configuration.py",
        "application/frontend/dist/index.html",
        "application/frontend/dist/assets/branding/cyrnava-256.png",
    ):
        require(required in files, "Required application component missing")
    if "apparmor" in manifest:
        require(
            manifest["apparmor"] in (APPARMOR_CONTRACT, LEGACY_APPARMOR_CONTRACT),
            "Unsupported AppArmor contract",
        )
        for name in ("cyrnava-native", "bootstrap.c", "apparmor_support.py"):
            require(name in files, "Required AppArmor component missing")
        require(
            files["cyrnava-native"]["mode"] == 0o700,
            "Native bootstrap must be executable",
        )
    if "maintenance" in manifest:
        operations = support(Path(__file__).parent, "native_operations")
        require(
            manifest["maintenance"] == operations.CONTRACT,
            "Unsupported maintenance contract",
        )
        for name in ("native_operations.py", "native_profile_check.py"):
            require(name in files, "Maintenance component missing")
    return manifest


def source_contract(files):
    """Compatibility inputs, independent of local frontend output filenames."""
    groups = {
        "application": [
            n for n in files if n.startswith(("backend/app/", "desktop/native/"))
        ],
        "frontend": [n for n in files if n.startswith("frontend/")],
        "runtime": [
            n
            for n in files
            if n
            in {
                "packaging/native/feasibility/dependencies.json",
                "packaging/native/feasibility/requirements.lock",
            }
        ],
        "bootstrap": [n for n in files if n == "packaging/native/bootstrap.c"],
    }
    result = {"format": 1}
    for group, names in groups.items():
        require(
            names and (group != "runtime" or len(names) == 2),
            "Source compatibility inputs missing",
        )
        result[group + "_sha256"] = hashlib.sha256(
            json.dumps(
                {n: files[n] for n in sorted(names)},
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
    return result


_SOURCE_CONTEXT_TOKEN = object()


class SourceInstallContext:
    """In-process explicit user trust in source, never a signature substitute."""

    def __init__(self, token, source_root, inventory_path, archive, manifest_path):
        require(token is _SOURCE_CONTEXT_TOKEN, "Use explicit reviewed source context")
        self.source_root = checked_path(source_root)
        self.inventory_path = regular(inventory_path, 8 * 1024**2)
        self.archive = regular(archive, MAX_ARCHIVE)
        self.manifest_path = regular(manifest_path)
        self.inventory_sha256 = digest(self.inventory_path)
        self.archive_sha256 = digest(self.archive)
        self.manifest_sha256 = digest(self.manifest_path)


def source_context(source_root, inventory_path, archive, manifest_path):
    context = SourceInstallContext(
        _SOURCE_CONTEXT_TOKEN, source_root, inventory_path, archive, manifest_path
    )
    validate_source_context(context, archive, manifest_path)
    return context


def validate_source_context(context, archive, manifest_path):
    require(
        type(context) is SourceInstallContext,
        "Explicit reviewed source context required",
    )
    require(
        checked_path(archive) == context.archive
        and checked_path(manifest_path) == context.manifest_path
        and digest(regular(archive, MAX_ARCHIVE)) == context.archive_sha256
        and digest(regular(manifest_path)) == context.manifest_sha256
        and digest(context.inventory_path) == context.inventory_sha256,
        "Source preparation changed; preserve it and prepare a fresh attempt",
    )
    inventory = load(context.inventory_path, 8 * 1024**2)
    require(
        inventory.get("format") == 1 and isinstance(inventory.get("files"), dict),
        "Invalid source inventory",
    )
    files = inventory["files"]
    require(1 <= len(files) <= 20000, "Invalid source inventory size")
    source_bytes = 0
    for name, info in files.items():
        member_name(name)
        require(
            isinstance(info, dict)
            and type(info.get("bytes")) is int
            and 0 <= info["bytes"] <= 16 * 1024**2
            and hash_string(info.get("sha256")),
            "Invalid source input declaration",
        )
        source_bytes += info["bytes"]
        require(
            source_bytes <= 128 * 1024**2,
            "Source inventory exceeds bounded input capacity",
        )
        path = regular(context.source_root / name, 16 * 1024**2)
        require(
            path.stat().st_size == info["bytes"] and digest(path) == info["sha256"],
            "Source input changed",
        )
    for name in (
        "desktop/install_engine.py",
        "desktop/native_operations.py",
        "packaging/native/feasibility/dependencies.json",
        "packaging/native/feasibility/requirements.lock",
    ):
        require(name in files, "Required source trust input missing")
    require(
        digest(context.source_root / "desktop/install_engine.py")
        == digest(Path(__file__)),
        "Source engine differs from executing reviewed code",
    )
    manifest = validate_manifest(load(manifest_path))
    require(
        manifest.get("installation_mode") == "source-online"
        and manifest.get("source_snapshot_sha256") == context.inventory_sha256
        and manifest.get("source_contract") == source_contract(files)
        and manifest.get("apparmor") == APPARMOR_CONTRACT
        and manifest.get("maintenance")
        == support(Path(__file__).parent, "native_operations").CONTRACT,
        "Source preparation or security contract mismatch",
    )
    require(
        not any(n.startswith("wheels/") for n in manifest["files"]),
        "Source payload must not redistribute a wheelhouse",
    )
    for target, original in (
        ("dependencies.json", "packaging/native/feasibility/dependencies.json"),
        ("requirements.lock", "packaging/native/feasibility/requirements.lock"),
    ):
        require(
            manifest["files"][target]["sha256"] == files[original]["sha256"],
            "Source runtime lock correspondence failed",
        )
    source_names = {
        "install_engine.py": "desktop/install_engine.py",
        "native_operations.py": "desktop/native_operations.py",
        "native_profile_check.py": "desktop/native_profile_check.py",
        "launch.py": "packaging/native/launch.py",
        "apparmor_support.py": "packaging/native/apparmor_support.py",
        "provider_check.py": "packaging/native/provider_check.py",
        "bootstrap.c": "packaging/native/bootstrap.c",
        "backend_check.py": "packaging/native/feasibility/backend_check.py",
        "system_schemas.py": "packaging/native/feasibility/run_probe.py",
    }
    for target, info in manifest["files"].items():
        original = source_names.get(target)
        if (
            target.startswith(
                ("application/backend/app/", "application/desktop/native/")
            )
            and target != "application/desktop/native/build_identity.py"
        ):
            original = target.removeprefix("application/")
        if original:
            require(
                original in files
                and info["sha256"] == files[original]["sha256"]
                and info["bytes"] == files[original]["bytes"],
                "Prepared application differs from reviewed source inventory",
            )
    return {
        "mode": "source-online-reviewed-code",
        "initial_trust": (
            "User-selected source checkout or source ZIP; same-source hashes "
            "are integrity checks, not independent authentication"
        ),
        "source_snapshot_sha256": context.inventory_sha256,
        "production_signature": "NOT CLAIMED",
    }


def install_from_source(archive, manifest_path, root, *, context, disposable=False):
    validate_source_context(context, archive, manifest_path)
    return install(
        archive, manifest_path, root, disposable=disposable, _source_context=context
    )


def update_from_source(
    archive, manifest_path, root, *, context, disposable=False, reinstall=False
):
    validate_source_context(context, archive, manifest_path)
    return support(Path(__file__).parent, "native_operations").update(
        maintenance_api(),
        archive,
        manifest_path,
        root,
        disposable=disposable,
        reinstall=reinstall,
        _source_context=context,
    )


def source_online_requirements(release):
    """Exactly the reviewed closure from official PyPI file URLs; no resolver."""
    dependencies = load(release / "dependencies.json")
    files = dependencies.get("files")
    require(
        isinstance(files, list) and len(files) == 19,
        "Exact nineteen-wheel dependency closure required",
    )
    expected, lines, seen = {}, [], set()
    for entry in files:
        name = entry.get("name", "")
        normalized = re.sub(r"[-_.]+", "-", name).lower()
        filename = entry.get("filename", "")
        url = urlsplit(entry.get("url", ""))
        require(
            re.fullmatch(r"[A-Za-z0-9_.-]+", name)
            and normalized not in seen
            and re.fullmatch(r"[A-Za-z0-9_.+-]+", entry.get("version", ""))
            and re.fullmatch(r"[A-Za-z0-9_.-]+\.whl", filename)
            and hash_string(entry.get("sha256"))
            and type(entry.get("bytes")) is int
            and 0 < entry["bytes"] <= MAX_ARCHIVE
            and url.scheme == "https"
            and url.netloc == "files.pythonhosted.org"
            and url.path.startswith("/packages/")
            and url.path.endswith("/" + filename)
            and not url.query
            and not url.fragment,
            "Only exact approved official PyPI wheel URLs are supported",
        )
        seen.add(normalized)
        require(filename not in expected, "Duplicate dependency wheel")
        expected[filename] = entry
        lines.append(entry["url"] + " --hash=sha256:" + entry["sha256"])
    declared = {}
    for line in regular(release / "requirements.lock").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(
            r"([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+-]+) --hash=sha256:([0-9a-f]{64})", line
        )
        require(match is not None, "Exact hash-locked requirements required")
        normalized = re.sub(r"[-_.]+", "-", match[1]).lower()
        require(normalized not in declared, "Duplicate locked requirement")
        declared[normalized] = (match[2], match[3])
    require(
        declared
        == {
            re.sub(r"[-_.]+", "-", e["name"]).lower(): (e["version"], e["sha256"])
            for e in files
        },
        "Wheel closure differs from requirements lock",
    )
    return expected, "\n".join(lines) + "\n"


def setup_source_environment(release):
    expected, requirements = source_online_requirements(release)
    run_operation(
        release, "venv", [sys.executable, "-B", "-I", "-m", "venv", release / ".venv"]
    )
    python = release / ".venv/bin/python"
    acquired = private_directory(release / "upstream-wheels")
    require(not any(acquired.iterdir()), "Existing acquisition output preserved")
    request = release / "upstream-requirements.lock"
    atomic(request, requirements.encode())
    run_operation(
        release,
        "acquire-exact-official-wheels",
        [
            python,
            "-B",
            "-I",
            "-m",
            "pip",
            "--isolated",
            "download",
            "--no-index",
            "--no-deps",
            "--no-cache-dir",
            "--require-hashes",
            "--only-binary=:all:",
            "--retries",
            "0",
            "--timeout",
            "30",
            "--dest",
            acquired,
            "-r",
            request,
        ],
        timeout=600,
    )
    require(
        {p.name for p in acquired.iterdir()} == set(expected),
        "Acquired wheel closure differs",
    )
    records = []
    for filename, entry in expected.items():
        path = regular(acquired / filename, entry["bytes"])
        require(
            path.stat().st_size == entry["bytes"] and digest(path) == entry["sha256"],
            "Official wheel size/checksum mismatch",
        )
        records.append(
            {
                k: entry[k]
                for k in ("name", "version", "filename", "bytes", "sha256", "url")
            }
        )
    durable(
        release / "dependency-acquisition.json",
        {
            "format": 1,
            "mode": "source-online",
            "status": "PASS",
            "complete": True,
            "source": (
                "official PyPI files over verified HTTPS; "
                "no index/dependency resolution"
            ),
            "dependencies_sha256": digest(release / "dependencies.json"),
            "requirements_sha256": digest(release / "requirements.lock"),
            "files": records,
        },
    )
    run_operation(
        release,
        "install-locked",
        [
            python,
            "-B",
            "-I",
            "-m",
            "pip",
            "--isolated",
            "install",
            "--no-index",
            "--no-deps",
            "--no-cache-dir",
            "--no-compile",
            "--require-hashes",
            "--only-binary=:all:",
            "--find-links",
            acquired,
            "-r",
            release / "requirements.lock",
        ],
    )
    run_operation(
        release, "pip-check", [python, "-B", "-I", "-m", "pip", "--isolated", "check"]
    )
    run_operation(
        release,
        "providers",
        [python, "-B", "-I", release / "provider_check.py"],
        timeout=120,
    )
    record = load(release / "providers.json")
    require(record.get("status") == "PASS", "Native provider prerequisites failed")
    return record


def verify_signature(manifest_path, signature, key, fingerprint, parent):
    """Use only an explicitly trusted public key; never retrieve or generate keys."""
    require(
        re.fullmatch(r"[A-F0-9]{40}", fingerprint or ""),
        "Full trusted primary fingerprint required",
    )
    for path in (manifest_path, signature, key):
        regular(path, 2 * 1024**2)
    with tempfile.TemporaryDirectory(prefix="verify-", dir=parent) as temporary:
        home = Path(temporary)
        base = [
            "/usr/bin/gpg",
            "--no-options",
            "--homedir",
            str(home),
            "--batch",
            "--no-auto-key-retrieve",
            "--no-autostart",
        ]

        def gpg(args):
            return subprocess.run(
                base + list(map(str, args)), capture_output=True, timeout=15, check=True
            )

        # Public verification needs no signing agent. Import can try to start
        # one (and fail on confined/long-path installations) even for public
        # keys. Read only this explicitly supplied keyring instead.
        keyring = home / "trusted.gpg"
        gpg(["--output", keyring, "--dearmor", key])
        base += ["--no-default-keyring", "--keyring", str(keyring)]
        identities, pending = {}, None
        for line in gpg(["--with-colons", "--list-keys"]).stdout.decode().splitlines():
            fields = line.split(":")
            if fields[0] in {"pub", "sub"}:
                pending = fields
            elif fields[0] == "fpr" and pending is not None:
                identities[fields[9]] = pending
                pending = None
        require(
            fingerprint in identities and identities[fingerprint][0] == "pub",
            "Trusted primary key absent",
        )
        completed = gpg(["--status-fd", "1", "--verify", signature, manifest_path])
        return signature_status(
            completed.stdout.decode(), identities, fingerprint, int(time.time())
        )


def signature_status(status, identities, fingerprint, now):
    lines = [
        line.split() for line in status.splitlines() if line.startswith("[GNUPG:] ")
    ]
    require(
        not any(
            p[1]
            in {
                "BADSIG",
                "ERRSIG",
                "EXPKEYSIG",
                "EXPSIG",
                "REVKEYSIG",
                "KEYREVOKED",
                "KEYEXPIRED",
                "SIGEXPIRED",
                "NO_PUBKEY",
            }
            for p in lines
        ),
        "Invalid, expired or revoked signature",
    )
    valid = [p for p in lines if p[1] == "VALIDSIG"]
    require(
        len(valid) == 1 and len(valid[0]) >= 11, "Exactly one valid signature required"
    )
    fields = valid[0]
    signer, primary = fields[2], fields[11] if len(fields) > 11 else fields[2]
    require(
        primary == fingerprint and fields[9] in {"8", "9", "10", "11"},
        "Wrong signing primary or unsupported digest",
    )
    require(
        int(fields[4]) <= now and (int(fields[5]) == 0 or int(fields[5]) > now),
        "Signature outside validity period",
    )
    for identity in {fingerprint, signer}:
        row = identities.get(identity)
        require(
            row is not None
            and row[1] not in {"r", "e", "d"}
            and int(row[5]) <= now
            and (not row[6] or int(row[6]) > now),
            "Signing key outside validity period",
        )
    return {"primary": primary, "signer": signer}


def extract(archive, destination, manifest):
    regular(archive, MAX_ARCHIVE)
    require(digest(archive) == manifest["archive_sha256"], "Archive checksum mismatch")
    with zipfile.ZipFile(archive) as source:
        members = source.infolist()
        require(
            len(members) == len(manifest["files"]), "Unexpected archive member count"
        )
        seen = set()
        for entry in members:
            name = member_name(entry.filename)
            require(
                name not in seen and name in manifest["files"],
                "Duplicate/unexpected archive member",
            )
            seen.add(name)
            info = manifest["files"][name]
            mode = entry.external_attr >> 16
            require(
                stat.S_IFMT(mode) in {0, stat.S_IFREG}
                and not entry.is_dir()
                and not entry.flag_bits & 1
                and entry.file_size == info["bytes"],
                "Link, special, encrypted or oversized member refused",
            )
        require(seen == set(manifest["files"]), "Incomplete archive")
        for entry in members:
            info = manifest["files"][entry.filename]
            path = checked_path(destination / entry.filename)
            path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with source.open(entry) as incoming, path.open("xb") as output:
                count = 0
                while chunk := incoming.read(1024 * 1024):
                    count += len(chunk)
                    require(
                        count <= info["bytes"], "Expanded member exceeds declaration"
                    )
                    output.write(chunk)
                output.flush()
                os.fsync(output.fileno())
            require(
                count == info["bytes"] and digest(path) == info["sha256"],
                "Extracted file checksum mismatch",
            )
            path.chmod(info["mode"])


def desktop_quote(value):
    # Same two-layer Desktop Entry/Exec quoting used by desktop/install.py.
    value = str(Path(value).absolute())
    require(
        ".." not in Path(value).parts
        and not any(ord(c) < 32 or ord(c) == 127 for c in value),
        "Unsafe desktop command path",
    )
    # venv/bin/python is intentionally an interpreter symlink. Quoting does not
    # open it; installation/storage checks reject links at their actual boundaries.
    value = value.replace("\\", "\\\\\\\\")
    for character in ('"', "`", "$"):
        value = value.replace(character, "\\\\" + character)
    return '"' + value.replace("%", "%%") + '"'


def desktop_entry(release, app_id, candidate, *, native=False):
    icon = release / "application/frontend/dist/assets/branding/cyrnava-256.png"
    require(not any(c in str(icon) for c in "\\"), "Unsupported icon path")
    # GIO resolves the first executable before percent expansion. Keep it an
    # absolute system adapter, and the exact-path ELF an argument, without a shell.
    command = (
        "/usr/bin/env -- " + desktop_quote(release.parent.parent / "cyrnava-native")
        if native
        else "/usr/bin/python3.14 -B -I "
        + desktop_quote(release.parent.parent / "launch.py")
    )
    return (
        "[Desktop Entry]\nVersion=1.0\nType=Application\n"
        + ("Name=CyrNava — N2 Candidate\n" if candidate else "Name=CyrNava\n")
        + "Comment=Local-first knowledge repository\n"
        + f"Exec={command}\n"
        + f"Icon={icon}\nTerminal=false\nCategories=Office;\nStartupNotify=true\n"
        + f"StartupWMClass={app_id}\nX-CyrNava-Native=true\n"
    ).encode()


def run_operation(release, name, command, timeout=180):
    print("N2: " + name, flush=True)
    environment = dict(
        os.environ,
        PIP_CONFIG_FILE=os.devnull,
        PIP_DISABLE_PIP_VERSION_CHECK="1",
        PYTHONDONTWRITEBYTECODE="1",
        TMPDIR=str(release / "tmp"),
    )
    with (release / (name + ".private.log")).open("xb") as log:
        process = subprocess.Popen(
            list(map(str, command)),
            stdout=log,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            env=environment,
            start_new_session=True,
        )
        try:
            code = process.wait(timeout)
        except BaseException:
            import signal

            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(5)
            raise
    require(code == 0, "Operation failed: " + name + "; retain private log")


def setup_environment(release):
    # Final location is deliberate: venv entry points cannot be relocated safely.
    run_operation(
        release, "venv", [sys.executable, "-B", "-I", "-m", "venv", release / ".venv"]
    )
    python = release / ".venv/bin/python"
    run_operation(
        release,
        "install-locked",
        [
            python,
            "-B",
            "-I",
            "-m",
            "pip",
            "--isolated",
            "install",
            "--no-index",
            "--no-cache-dir",
            "--no-compile",
            "--require-hashes",
            "--only-binary=:all:",
            "--find-links",
            release / "wheels",
            "-r",
            release / "requirements.lock",
        ],
    )
    run_operation(
        release, "pip-check", [python, "-B", "-I", "-m", "pip", "--isolated", "check"]
    )
    run_operation(
        release,
        "providers",
        [python, "-B", "-I", release / "provider_check.py"],
        timeout=120,
    )
    record = load(release / "providers.json")
    require(record.get("status") == "PASS", "Native provider prerequisites failed")
    return record


def deployment_paths(root, disposable):
    root = checked_path(root)
    if disposable:
        # This engine's source location is the trust boundary, never cwd/env supplied.
        repo = Path(__file__).resolve().parents[1]
        require(
            (repo / "desktop/install_engine.py").is_file(),
            "Disposable install requires repository engine",
        )
        output = checked_path(repo / "ci-output")
        require(
            root.is_relative_to(output) and root != output,
            "Disposable root must be inside repository ci-output",
        )
        return root / "client/profile", root / "xdg/applications"
    data = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    require(data.is_absolute(), "XDG data path must be absolute")
    data = checked_path(data)
    require(
        root == data / "cyrnava-application",
        "Use the canonical per-user native installation root",
    )
    return data / "cyrnava/native", data / "applications"


def journal_checkpoint(root, journal, phase):
    journal["phase"] = phase
    durable(root / "transaction.json", journal)


def install(
    archive,
    manifest_path,
    root,
    *,
    disposable=False,
    candidate_sha256=None,
    signature=None,
    key=None,
    fingerprint=None,
    _source_context=None,
):
    host_supported()
    root = checked_path(root)
    profile, applications = deployment_paths(root, disposable)
    manifest = validate_manifest(load(manifest_path))
    require(
        (manifest.get("installation_mode") == "source-online")
        == (_source_context is not None),
        "Source-online installation requires the explicit source entry point",
    )
    if _source_context is not None:
        validate_source_context(_source_context, archive, manifest_path)
    require(
        not root.exists() or not (root / "current.json").exists(),
        "Existing installation preserved; N2 does not implement updates",
    )
    require(
        not profile.exists(),
        "Existing profile preserved; N2 first installation requires a fresh data location",
    )
    require(
        manifest["kind"] == ("candidate" if disposable else "release"),
        "Deployment kind mismatch",
    )
    require(
        shutil.disk_usage(root.parent if root.parent.exists() else Path.home()).free
        >= manifest["expanded_bytes"] * 4 + HEADROOM,
        "Insufficient staging/environment headroom",
    )
    private_directory(root)
    with installation_lock(root):
        require(
            not (root / "current.json").exists(),
            "Installation appeared while acquiring lock",
        )
        require(
            not (root / "transaction.json").exists(),
            "Interrupted transaction retained; run recover first",
        )
        if _source_context is not None:
            trust = validate_source_context(_source_context, archive, manifest_path)
        elif disposable:
            require(
                hash_string(candidate_sha256)
                and digest(manifest_path) == candidate_sha256,
                "Explicit reviewed candidate manifest checksum required",
            )
            trust = {
                "mode": "disposable-checksum-only",
                "production_signature": "NOT VERIFIED",
            }
        else:
            require(
                signature and key and fingerprint, "Owner-trusted signature required"
            )
            trust = verify_signature(manifest_path, signature, key, fingerprint, root)
        private_directory(root / "releases")
        release = (
            root
            / "releases"
            / (manifest["version"] + "-" + manifest["archive_sha256"][:16])
        )
        require(
            not release.exists(),
            "Existing release retained; use fresh disposable root or review recovery",
        )
        applications = checked_path(applications)
        # Shared applications/ may be 0755; inspect ownership and write bits, never chmod it.
        applications.mkdir(parents=True, mode=0o700, exist_ok=True)
        require(
            applications.stat().st_uid == os.getuid()
            and not applications.stat().st_mode & 0o022,
            "Unsafe application-menu directory",
        )
        desktop = applications / (manifest["app_id"] + ".desktop")
        require(
            not desktop.exists() and not desktop.is_symlink(),
            "Existing desktop identity preserved; coexistence decision required",
        )
        if not disposable:
            alternatives = [
                Path.home() / ".local/share/flatpak/exports/share",
                Path("/var/lib/flatpak/exports/share"),
            ]
            alternatives += [
                Path(p)
                for p in os.environ.get(
                    "XDG_DATA_DIRS", "/usr/local/share:/usr/share"
                ).split(":")
                if p
            ]
            require(
                not any(
                    (p / "applications" / desktop.name).exists() for p in alternatives
                ),
                "Another desktop provider uses this application identity; owner coexistence decision required",
            )
        require(
            not (root / "launch.py").exists() and not (root / "launch.py").is_symlink(),
            "Existing bootstrap preserved",
        )
        native = "apparmor" in manifest
        for name in ("cyrnava-native", "apparmor-profile"):
            require(
                not (root / name).exists() and not (root / name).is_symlink(),
                "Existing native bootstrap preserved",
            )
        active = {"format": 1, "release": release.name, "receipt_sha256": None}
        journal = {
            "format": 1,
            "root": str(root),
            "release": release.name,
            "desktop": str(desktop),
            "desktop_sha256": hashlib.sha256(
                desktop_entry(release, manifest["app_id"], disposable, native=native)
            ).hexdigest(),
            "active_sha256": None,
            "bootstrap_sha256": manifest["files"]["launch.py"]["sha256"],
        }
        journal_checkpoint(root, journal, "staging")
        release.mkdir(mode=0o700)
        extract(archive, release, manifest)
        atomic(release / "manifest.json", regular(manifest_path).read_bytes())
        if native:
            # Generate only application-local metadata. No policy install/load.
            label = support(release, "apparmor_support").profile_name(root)
            journal["native_bootstrap_sha256"] = manifest["files"]["cyrnava-native"][
                "sha256"
            ]
            journal["apparmor_profile_sha256"] = hashlib.sha256(
                (label + "\n").encode()
            ).hexdigest()
        (release / "tmp").mkdir(mode=0o700)
        providers = (
            setup_source_environment(release)
            if _source_context is not None
            else setup_environment(release)
        )
        run_operation(
            release,
            "synthetic-backend",
            [
                release / ".venv/bin/python",
                "-B",
                "-I",
                release / "backend_check.py",
                release,
            ],
            timeout=90,
        )
        require(
            load(release / "backend-check.json").get("status") == "PASS",
            "Synthetic startup/security check failed",
        )
        receipt = {
            "format": 1,
            "root": str(root),
            "release": release.name,
            "manifest_sha256": digest(release / "manifest.json"),
            "profile": str(profile),
            "trust": trust,
            "provider_files": providers["provider_files"],
        }
        durable(release / "installed.json", receipt)
        active["receipt_sha256"] = digest(release / "installed.json")
        active_bytes = (json.dumps(active, sort_keys=True, indent=2) + "\n").encode()
        journal["active_sha256"] = hashlib.sha256(active_bytes).hexdigest()
        journal_checkpoint(root, journal, "verified")
        atomic(root / "launch.py", (release / "launch.py").read_bytes())
        if native:
            atomic(
                root / "cyrnava-native",
                (release / "cyrnava-native").read_bytes(),
                0o700,
            )
            atomic(root / "apparmor-profile", (label + "\n").encode())
        atomic(root / "current.json", active_bytes)
        journal_checkpoint(root, journal, "activated")
        atomic(
            desktop,
            desktop_entry(release, manifest["app_id"], disposable, native=native),
            0o644,
        )
        journal_checkpoint(root, journal, "desktop-registered")
        (root / "transaction.json").unlink()
        sync_directory(root)
        return {
            "status": "PASS",
            "scope": "N2-installation-only",
            "release": str(release),
            "desktop": str(desktop),
            "profile": str(profile),
            "archive_sha256": manifest["archive_sha256"],
            "manifest_sha256": digest(manifest_path),
            "trust": trust,
            "native_menu_launch": "PENDING OWNER",
            "application_data_opened": False,
            "apparmor_policy": "PENDING EXPLICIT HOST LOAD"
            if native
            else "LEGACY CANDIDATE",
        }


def recover(root, *, disposable=False):
    """Rollback only exact transaction-owned activation/menu files; retain release/logs."""
    if (
        load(checked_path(root) / "transaction.json", limit=32 * 1024**2).get("format")
        == 3
    ):
        return support(Path(__file__).parent, "native_operations").recover(
            maintenance_api(), root, disposable=disposable
        )
    root = checked_path(root)
    _, applications = deployment_paths(root, disposable)
    with installation_lock(root):
        journal = load(root / "transaction.json")
        require(
            journal.get("format") == 1 and journal.get("root") == str(root),
            "Recovery identity mismatch",
        )
        require(
            re.fullmatch(
                r"[0-9]+\.[0-9]+\.[0-9]+(?:-[a-z0-9.]+)?-[0-9a-f]{16}",
                journal.get("release", ""),
            ),
            "Unsafe recovery release",
        )
        desktop = checked_path(journal["desktop"])
        require(
            desktop.parent == applications
            and desktop.name in {APP_ID + ".desktop", CANDIDATE_ID + ".desktop"},
            "Unexpected recovery menu path",
        )
        targets = [
            (root / "current.json", journal.get("active_sha256")),
            (root / "launch.py", journal.get("bootstrap_sha256")),
            (desktop, journal["desktop_sha256"]),
        ]
        if "native_bootstrap_sha256" in journal:
            targets.extend(
                [
                    (root / "cyrnava-native", journal["native_bootstrap_sha256"]),
                    (root / "apparmor-profile", journal["apparmor_profile_sha256"]),
                ]
            )
        # Inspect the whole set before deleting anything; unexpected changes abort.
        for path, expected in targets:
            if path.exists() or path.is_symlink():
                require(
                    hash_string(expected) and digest(regular(path)) == expected,
                    "Changed transaction target preserved",
                )
        for path, _ in targets:
            if path.exists():
                path.unlink()
                sync_directory(path.parent)
        archived = root / ("recovered-" + uuid.uuid4().hex + ".json")
        os.replace(root / "transaction.json", archived)
        sync_directory(root)
        return {
            "status": "PASS",
            "scope": "interrupted-first-install-recovery",
            "release_and_logs": "RETAINED",
        }


def installed(release, *, check_providers=True):
    release = private_directory(release)
    root = private_directory(release.parent.parent)
    require(release.parent.name == "releases", "Installed release layout required")
    require(
        not (root / "transaction.json").exists(), "Installation transaction incomplete"
    )
    active = load(root / "current.json")
    require(
        active.get("format") == 1
        and active.get("release") == release.name
        and active.get("receipt_sha256") == digest(release / "installed.json"),
        "Inactive or changed release",
    )
    receipt = load(release / "installed.json")
    require(
        receipt.get("root") == str(root)
        and receipt.get("release") == release.name
        and receipt.get("manifest_sha256") == digest(release / "manifest.json"),
        "Installed receipt mismatch",
    )
    manifest = validate_manifest(load(release / "manifest.json"))
    require(
        digest(root / "launch.py") == manifest["files"]["launch.py"]["sha256"],
        "Stable bootstrap changed",
    )
    for name, info in manifest["files"].items():
        require(
            digest(regular(release / member_name(name))) == info["sha256"],
            "Installed application changed",
        )
    if "apparmor" in manifest:
        executable = regular(root / "cyrnava-native")
        require(
            digest(executable) == manifest["files"]["cyrnava-native"]["sha256"]
            and stat.S_IMODE(executable.stat().st_mode) == 0o700
            and executable.stat().st_uid == os.getuid(),
            "Stable native bootstrap changed",
        )
        require(
            regular(root / "apparmor-profile").read_text()
            == support(release, "apparmor_support").profile_name(root) + "\n",
            "AppArmor profile identity changed",
        )
    if check_providers:
        require(receipt["provider_files"], "Provider inventory missing")
        for name, expected in receipt["provider_files"].items():
            member_name(name)
            require(
                name.startswith(".venv/")
                and digest(regular(release / name)) == expected,
                "Installed dependency changed",
            )
    return receipt, manifest


def support(release, name):
    spec = importlib.util.spec_from_file_location(
        "cyrnava_installed_" + name, release / (name + ".py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def maintenance_api():
    # Also works for importlib-loaded engines whose caller does not register a
    # sys.modules entry; no environment or additional framework is imported.
    from types import SimpleNamespace

    return SimpleNamespace(**globals())


def launch(release, *, check_only=False):
    host_supported()
    release = Path(release).absolute()
    with installation_lock(release.parent.parent):
        receipt, manifest = installed(release)
        policy = (
            support(release, "apparmor_support").check_label(release.parent.parent)
            if "apparmor" in manifest
            else None
        )
        if Path(sys.prefix) != release / ".venv":
            # GIO resolves the executable before expanding %% in arguments. A
            # system-interpreter bootstrap therefore supports percent-containing
            # install roots and remains stable across later release selection.
            # Verify the selected payload/providers BEFORE entering its venv.
            os.execv(
                str(release / ".venv/bin/python"),
                [
                    str(release / ".venv/bin/python"),
                    "-B",
                    "-I",
                    str(release.parent.parent / "launch.py"),
                    *(["--check"] if check_only else []),
                ],
            )
        require(
            Path(sys.prefix) == release / ".venv",
            "Installed private interpreter required",
        )
        environment, schema = support(
            release, "system_schemas"
        ).ubuntu_system_schema_environment(os.environ)
        if check_only:
            return {
                "status": "PASS",
                "scope": "installed-bootstrap-without-GUI",
                "app_id": manifest["app_id"],
                "manifest_sha256": receipt["manifest_sha256"],
                "schema": schema,
                "normal_window": "NOT EXECUTED",
                "renderer": "NOT EXECUTED",
                "apparmor": policy,
            }
        require(os.environ.get("WAYLAND_DISPLAY"), "Wayland owner session required")
        if manifest["kind"] == "candidate":
            for key, suffix in (
                ("XDG_DATA_HOME", "data"),
                ("XDG_CONFIG_HOME", "config"),
                ("XDG_CACHE_HOME", "cache"),
            ):
                path = private_directory(release.parent.parent / "client" / suffix)
                os.environ[key] = str(path)
        os.environ["GSETTINGS_SCHEMA_DIR"] = environment["GSETTINGS_SCHEMA_DIR"]
        os.environ["QT_QPA_PLATFORM"] = "wayland"
        sys.path.insert(0, str(release / "application"))
        from desktop.native.application import run

        return run()


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    package_commands = [sub.add_parser(name) for name in ("install", "update")]
    package_commands[1].add_argument("--reinstall", action="store_true")
    for command_parser in package_commands:
        command_parser.add_argument("--archive", required=True, type=Path)
        command_parser.add_argument("--manifest", required=True, type=Path)
        for name in ("signature", "key"):
            command_parser.add_argument("--" + name, type=Path)
        command_parser.add_argument("--fingerprint")
        command_parser.add_argument("--candidate-sha256")
    restore = sub.add_parser("reinstall")
    restore.add_argument("--reuse-preserved-data", action="store_true", required=True)
    for command_parser in (
        *package_commands,
        restore,
        sub.add_parser("recover"),
        sub.add_parser("uninstall"),
        sub.add_parser("rollback"),
    ):
        command_parser.add_argument("--root", required=True, type=Path)
        command_parser.add_argument("--disposable", action="store_true")
    args = parser.parse_args()
    try:
        if args.operation == "recover":
            result = recover(args.root, disposable=args.disposable)
        elif args.operation in {"uninstall", "reinstall", "rollback"}:
            operations = support(Path(__file__).parent, "native_operations")
            function = {
                "uninstall": operations.uninstall,
                "reinstall": operations.restore_installation,
                "rollback": operations.rollback,
            }[args.operation]
            options = (
                {}
                if args.operation != "reinstall"
                else {"reuse_preserved_data": args.reuse_preserved_data}
            )
            result = function(
                maintenance_api(), args.root, disposable=args.disposable, **options
            )
        else:
            options = {}
            function = install
            if args.operation == "update":
                operations = support(Path(__file__).parent, "native_operations")
                function = lambda *a, **kw: operations.update(
                    maintenance_api(), *a, **kw
                )
                options["reinstall"] = args.reinstall
            result = function(
                args.archive,
                args.manifest,
                args.root,
                disposable=args.disposable,
                candidate_sha256=args.candidate_sha256,
                signature=args.signature,
                key=args.key,
                fingerprint=args.fingerprint,
                **options,
            )
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "error_type": type(error).__name__,
                    "error": str(error)
                    if isinstance(error, ValueError)
                    else "Operation failed; retain private logs",
                }
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
