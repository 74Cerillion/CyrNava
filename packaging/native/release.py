"""N4 source-based native assembly/audit; reuses the accepted install engine.

No signing, GUI, host-policy loading, package publication or dependency resolution.
Candidate output does not establish public-release readiness.
"""

import email
import hashlib
import importlib.util
import json
import re
import shutil
import stat
import subprocess
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
TARGET = "ubuntu-26.04-x86_64-wayland-cpython314"
N1_RECEIPT = "7f713ed31e2ce7d63a1a67e806d671b38ff2f7bafd2d66592f68ff70d575c41e"
DEPENDENCIES_SHA = "621c640f428886a7944b654fe6726f2b3ab82644e4911a051f8281ab392eb8a3"
LOCK_SHA = "24876b72281d5427fc9c5c41cdb19a918815e9547e74c5eb4d2c93ac22e4a576"
FLOOR = 5 * 1024**3
MAX_MEMBER = 512 * 1024**2
MAX_TOTAL = 1024**3


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def regular(path):
    path = Path(path).absolute()
    require(not any(p.is_symlink() for p in (path, *path.parents)), "Symlink refused")
    info = path.stat()
    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "Regular file required")
    return path


def member(name):
    path = PurePosixPath(name)
    require(
        name
        and not path.is_absolute()
        and str(path) == name
        and ".." not in path.parts
        and "\\" not in name
        and not any(ord(c) < 32 or ord(c) == 127 for c in name),
        "Unsafe archive member",
    )
    return name


def write_json(path, value):
    with path.open("x") as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2) + "\n")


def source_files(root):
    """Only application/development sources, never workspaces or historical output."""
    result = {}
    roots = [
        "backend/app",
        "backend/tests",
        "desktop/native",
        "packaging/native",
        "frontend/src",
        "frontend/public",
        "frontend/scripts",
    ]
    suffixes = {
        ".py",
        ".json",
        ".toml",
        ".ts",
        ".tsx",
        ".js",
        ".mjs",
        ".css",
        ".svg",
        ".png",
        ".woff",
        ".woff2",
        ".lock",
        ".sh",
        ".c",
    }
    for base in roots:
        for p in (root / base).rglob("*"):
            relative = p.relative_to(root)
            if any(
                n in relative.parts
                for n in [
                    "evidence",
                    "__pycache__",
                    ".venv",
                    "node_modules",
                    ".pytest_cache",
                ]
            ):
                continue
            if p.is_file() and p.suffix in suffixes:
                result[str(relative)] = regular(p)
    for name in [
        "LICENSE",
        "README.md",
        "CHANGELOG.md",
        "BACKUP_RESTORE.md",
        "backend/pyproject.toml",
        "backend/requirements.txt",
        "desktop/install_engine.py",
        "desktop/native_operations.py",
        "desktop/native_profile_check.py",
        "install_cyrnava.sh",
        "update_cyrnava.sh",
        "uninstall_cyrnava.sh",
        ".nvmrc",
        ".github/workflows/ci.yml",
        ".github/actionlint.yaml",
        "ci/native.py",
        "ci/validate.py",
        "ci/verify.py",
        "ci/test_ci.py",
        "ci/bootstrap.py",
        "ci/tools.json",
        "ci/requirements.lock",
        "ci/native-workflow-contract.json",
    ]:
        result[name] = regular(root / name)
    for p in (root / "frontend").iterdir():
        if p.is_file() and p.suffix in {".json", ".ts", ".js"}:
            result[str(p.relative_to(root))] = regular(p)
    for name in [
        "native-installation.md",
        "native-release-notes-v0.1.0.md",
        "native-dependencies.md",
        "native-source-obligations.md",
    ]:
        p = root / "docs" / name
        if p.is_file():
            result[str(p.relative_to(root))] = regular(p)
    return result


def provenance(root, *, allow_dirty=False):
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    require(re.fullmatch(r"[0-9a-f]{40}", head), "Immutable source HEAD required")
    status = subprocess.check_output(["git", "status", "--porcelain", "-z"], cwd=root)
    require(
        allow_dirty or not status, "Clean source required; local patch must be explicit"
    )
    patch = subprocess.check_output(["git", "diff", "--binary", "HEAD"], cwd=root)
    sources = source_files(root)
    return {
        "format": 1,
        "source_commit": head,
        "working_tree": "LOCAL PATCH" if status else "CLEAN",
        "tracked_patch_sha256": hashlib.sha256(patch).hexdigest(),
        "source_files": {n: sha(p) for n, p in sorted(sources.items())},
        "untracked_inputs": "Included source snapshots are individually hashed",
    }, sources


def wheels(directory, dependencies):
    require(len(dependencies["files"]) <= 100, "Dependency bound exceeded")
    result = {}
    for info in dependencies["files"]:
        name = info["filename"]
        require(
            member(name) == Path(name).name and name.endswith(".whl"), "Wheel required"
        )
        p = regular(directory / name)
        require(
            p.stat().st_size == info["bytes"] and sha(p) == info["sha256"],
            "Wheel pin mismatch",
        )
        require(name not in result, "Duplicate wheel")
        result[name] = p
    qt = {
        i["name"].lower().replace("_", "-"): i["version"]
        for i in dependencies["files"]
        if i["name"].lower().replace("_", "-")
        in {"pyside6", "pyside6-addons", "pyside6-essentials", "shiboken6"}
    }
    require(
        len(qt) == 4 and set(qt.values()) == {"6.11.3"},
        "Coherent accepted Qt lock required",
    )
    return result


def dependency_inventory(paths):
    result = []
    for name, path in sorted(paths.items()):
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            require(
                len(names) == len(set(names)) and len(names) <= 50000,
                "Invalid wheel inventory",
            )
            metadata = [n for n in names if n.endswith(".dist-info/METADATA")]
            require(len(metadata) == 1, "Wheel metadata missing/ambiguous")
            info = email.message_from_bytes(archive.read(metadata[0]))
            notices, elf = [], []
            for entry in archive.infolist():
                if entry.is_dir():
                    continue
                member(entry.filename)
                require(
                    not stat.S_ISLNK(entry.external_attr >> 16), "Wheel symlink refused"
                )
                require(entry.file_size <= MAX_MEMBER, "Wheel member exceeds bound")
                if any(
                    x in entry.filename.lower()
                    for x in [
                        "license",
                        "copying",
                        "notice",
                        "attribution",
                        "spdx",
                        "sbom",
                    ]
                ):
                    content = archive.read(entry)
                    notices.append(
                        {
                            "path": entry.filename,
                            "bytes": len(content),
                            "sha256": hashlib.sha256(content).hexdigest(),
                        }
                    )
                with archive.open(entry) as stream:
                    if stream.read(4) == b"\x7fELF":
                        elf.append({"path": entry.filename, "bytes": entry.file_size})
            result.append(
                {
                    "wheel": name,
                    "sha256": sha(path),
                    "name": info["Name"],
                    "version": info["Version"],
                    "declared_license": info.get(
                        "License-Expression", info.get("License")
                    ),
                    "upstream": info.get_all("Project-URL", []),
                    "notice_documents": notices,
                    "ELF_files": elf,
                    "notice_coverage": "DOCUMENTS PRESENT; REVIEW REQUIRED"
                    if notices
                    else "MISSING IN WHEEL",
                    "redistribution_clearance": "NOT INFERRED FROM METADATA",
                }
            )
    return {
        "format": 1,
        "scope": "exact distributed wheel contents; host libraries separate",
        "distributions": result,
        "complete_SBOM": False,
        "corresponding_source": "PENDING EXACT SOURCE/BUILD CORRESPONDENCE REVIEW",
    }


def zip_write(archive, name, content, mode=0o600):
    member(name)
    info = zipfile.ZipInfo(name, date_time=(2026, 11, 3, 0, 0, 0))
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | mode) << 16
    archive.writestr(info, content)


def build_identity(kind):
    app_id = (
        "org.cyrnava.CyrNava.Devel"
        if kind == "candidate"
        else "io.github._74Cerillion.CyrNava"
    )
    title = "CyrNava — N2 installation candidate" if kind == "candidate" else "CyrNava"
    channel = "development" if kind == "candidate" else "stable"
    return (
        f"from pathlib import Path\nAPP_ID = {json.dumps(app_id)}\n"
        f'CHANNEL = {json.dumps(channel)}\nDEPLOYMENT = "native-installed"\n'
        f"WINDOW_TITLE = {json.dumps(title, ensure_ascii=False)}\n"
        "ICON_PATH = str(Path(__file__).resolve().parents[2] / "
        '"frontend/dist/assets/branding/cyrnava-256.png")\n'
    ).encode()


def assemble(
    root, output, wheelhouse, frontend, *, version, kind="candidate", allow_dirty=False
):
    require(
        re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[a-z0-9.]+)?", version),
        "Safe version required",
    )
    require(kind in {"candidate", "release"}, "Explicit deployment kind required")
    output = output.absolute()
    require(
        not output.exists()
        and not any(p.is_symlink() for p in (output, *output.parents)),
        "Fresh output required",
    )
    require(
        output.parent.is_dir() and shutil.disk_usage(output.parent).free >= FLOOR,
        "Keep 5GiB free floor",
    )
    source, sources = provenance(root, allow_dirty=allow_dirty)
    require((frontend / "index.html").is_file(), "Built frontend required")
    frontend_proof = json.loads((frontend.parent / "frontend-build.json").read_text())
    require(frontend_proof["status"] == "PASS", "Fresh frontend build proof required")
    require(
        all(
            source["source_files"].get(n) == h
            for n, h in frontend_proof["source_files"].items()
        ),
        "Frontend source changed since build",
    )
    require(
        sha(root / "packaging/native/feasibility/dependencies.json") == DEPENDENCIES_SHA
        and sha(root / "packaging/native/feasibility/requirements.lock") == LOCK_SHA,
        "Accepted dependency lock changed",
    )
    dependencies = json.loads(
        (root / "packaging/native/feasibility/dependencies.json").read_text()
    )
    wheel_paths = wheels(wheelhouse, dependencies)
    inventory = dependency_inventory(wheel_paths)
    paths = {}
    for n, p in sources.items():
        if n.startswith(("backend/app/", "desktop/native/")) and p.suffix in {
            ".py",
            ".json",
        }:
            require(
                not any(x in n for x in ["sqlite_fault", "test_", "n1_configuration"]),
                "Test helper in application",
            )
            if not n.endswith("/build_identity.py"):
                paths["application/" + n] = p
    for p in frontend.rglob("*"):
        if p.is_file():
            paths["application/frontend/dist/" + str(p.relative_to(frontend))] = (
                regular(p)
            )
    for name in [
        "install_engine.py",
        "native_operations.py",
        "native_profile_check.py",
    ]:
        paths[name] = regular(root / "desktop" / name)
    for name in [
        "launch.py",
        "provider_check.py",
        "apparmor_support.py",
        "bootstrap.c",
    ]:
        paths[name] = regular(root / "packaging/native" / name)
    for name, original in [
        ("system_schemas.py", "run_probe.py"),
        ("backend_check.py", "backend_check.py"),
        ("requirements.lock", "requirements.lock"),
        ("dependencies.json", "dependencies.json"),
    ]:
        paths[name] = regular(root / "packaging/native/feasibility" / original)
    paths.update({"wheels/" + n: p for n, p in wheel_paths.items()})
    paths["notices/LICENSE"] = regular(root / "LICENSE")
    paths["notices/frontend-third-party-notices.txt"] = regular(
        frontend / "third-party-notices.txt"
    )
    output.mkdir(mode=0o700)
    apparmor = module("n4_apparmor", root / "packaging/native/apparmor_support.py")
    compiled = output / "cyrnava-native"
    bootstrap = apparmor.compile_bootstrap(
        root / "packaging/native/bootstrap.c", compiled
    )
    paths["cyrnava-native"] = compiled
    app_id = (
        "org.cyrnava.CyrNava.Devel"
        if kind == "candidate"
        else "io.github._74Cerillion.CyrNava"
    )
    identity = build_identity(kind)
    generated = {
        "application/desktop/native/build_identity.py": identity,
        "notices/dependency-inventory.json": (
            json.dumps(inventory, sort_keys=True, indent=2) + "\n"
        ).encode(),
    }
    archive_path = output / ("CyrNava-" + version + "-ubuntu-x86_64.zip")
    files = {}
    with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_STORED) as archive:
        for name in sorted(set(paths) | set(generated)):
            content = generated[name] if name in generated else paths[name].read_bytes()
            mode = 0o700 if name == "cyrnava-native" else 0o600
            zip_write(archive, name, content, mode)
            files[name] = {
                "bytes": len(content),
                "mode": mode,
                "sha256": hashlib.sha256(content).hexdigest(),
            }
    operations = module("n4_contract", root / "desktop/native_operations.py")
    manifest = {
        "format": 1,
        "kind": kind,
        "version": version,
        "target": TARGET,
        "app_id": app_id,
        "apparmor": apparmor.CONTRACT,
        "maintenance": operations.CONTRACT,
        "archive_sha256": sha(archive_path),
        "expanded_bytes": sum(x["bytes"] for x in files.values()),
        "files": files,
        "bootstrap_build": bootstrap,
        "source_head": source["source_commit"],
        "n1_receipt_sha256": N1_RECEIPT,
        "source_provenance": source,
        "frontend_build": frontend_proof,
        "assembly_source_sha256": sha(Path(__file__)),
        "frontend_files": {
            n: v for n, v in files.items() if n.startswith("application/frontend/dist/")
        },
    }
    require(
        manifest["expanded_bytes"] <= MAX_TOTAL,
        "Payload size exceeds accepted installer bound",
    )
    write_json(output / "manifest.json", manifest)
    write_json(output / "dependency-inventory.json", inventory)
    with zipfile.ZipFile(
        output / "CyrNava-source.zip", "x", compression=zipfile.ZIP_DEFLATED
    ) as archive:
        for name, path in sorted(sources.items()):
            require(
                sha(path) == source["source_files"][name],
                "Source changed during assembly",
            )
            zip_write(archive, name, path.read_bytes())
        zip_write(
            archive,
            "SOURCE-MANIFEST.json",
            (json.dumps(source, sort_keys=True, indent=2) + "\n").encode(),
        )
    # Existing installer export is shared with N2/N3; no second installer or trust path.
    old = module("n4_installer_export", root / "packaging/native/build_candidate.py")
    old.export_installer(output)
    shutil.copyfile(
        root / "packaging/native/policy_setup.py", output / "policy_setup.py"
    )
    exported_record = json.loads((output / "installer-checksums.json").read_text())
    exported_record["files"]["policy_setup.py"] = sha(output / "policy_setup.py")
    (output / "installer-checksums.json").write_text(
        json.dumps(exported_record, sort_keys=True, indent=2) + "\n"
    )
    with zipfile.ZipFile(
        output / "CyrNava-installer.zip", "x", compression=zipfile.ZIP_DEFLATED
    ) as archive:
        exported = json.loads((output / "installer-checksums.json").read_text())[
            "files"
        ]
        for name, expected in exported.items():
            require(sha(output / name) == expected, "Exported bootstrap changed")
            zip_write(archive, name, (output / name).read_bytes())
    write_json(
        output / "provenance.json",
        {
            "source": source,
            "archive_sha256": manifest["archive_sha256"],
            "manifest_sha256": sha(output / "manifest.json"),
            "source_archive_sha256": sha(output / "CyrNava-source.zip"),
            "installer_archive_sha256": sha(output / "CyrNava-installer.zip"),
            "signature": "NOT CREATED",
            "renderer": "NOT EXECUTED",
            "release_readiness": "PENDING OWNER/THIRD-PARTY/SIGNATURE/HOSTED GATES",
        },
    )
    return audit(root, output, archive_path)


def allowed_payload(name):
    if name in {
        "launch.py",
        "install_engine.py",
        "native_operations.py",
        "native_profile_check.py",
        "provider_check.py",
        "backend_check.py",
        "system_schemas.py",
        "requirements.lock",
        "dependencies.json",
        "bootstrap.c",
        "apparmor_support.py",
        "cyrnava-native",
    }:
        return True
    if name.startswith("wheels/"):
        return name.count("/") == 1 and name.endswith(".whl")
    if name.startswith(("application/backend/app/", "application/desktop/native/")):
        return name.endswith((".py", ".json")) and not any(
            x in name for x in ["test_", "sqlite_fault", "n1_configuration"]
        )
    if name.startswith("application/frontend/dist/"):
        return Path(name).suffix in {
            ".html",
            ".js",
            ".css",
            ".png",
            ".svg",
            ".woff",
            ".woff2",
            ".txt",
        }
    return name in {
        "notices/LICENSE",
        "notices/frontend-third-party-notices.txt",
        "notices/dependency-inventory.json",
    }


def audit(root, output, archive_path):
    engine = module("n4_audit_engine", root / "desktop/install_engine.py")
    manifest = engine.validate_manifest(engine.load(output / "manifest.json"))
    require(
        sha(regular(archive_path)) == manifest["archive_sha256"],
        "Archive hash mismatch",
    )
    with zipfile.ZipFile(archive_path) as archive:
        require(
            len(archive.namelist()) == len(set(archive.namelist())), "Duplicate member"
        )
        require(
            set(archive.namelist()) == set(manifest["files"]),
            "Exported file inventory mismatch",
        )
        for entry in archive.infolist():
            name = member(entry.filename)
            require(allowed_payload(name), "Unreviewed payload path")
            require(
                not stat.S_ISLNK(entry.external_attr >> 16), "Archive symlink refused"
            )
            info = manifest["files"][name]
            require(
                entry.file_size == info["bytes"] <= MAX_MEMBER, "Member size mismatch"
            )
            require(
                stat.S_IMODE(entry.external_attr >> 16) == info["mode"],
                "Member mode mismatch",
            )
            with archive.open(entry) as stream:
                require(
                    hashlib.file_digest(stream, "sha256").hexdigest() == info["sha256"],
                    "Exported file hash mismatch",
                )
        dependencies = json.loads(archive.read("dependencies.json"))
        require(
            hashlib.sha256(archive.read("dependencies.json")).hexdigest()
            == DEPENDENCIES_SHA
            and hashlib.sha256(archive.read("requirements.lock")).hexdigest()
            == LOCK_SHA,
            "Unapproved dependency closure",
        )
        expected = {"wheels/" + i["filename"]: i for i in dependencies["files"]}
        require(
            {n for n in manifest["files"] if n.startswith("wheels/")} == set(expected),
            "Wrong wheel closure",
        )
        for name, info in expected.items():
            require(
                manifest["files"][name]["sha256"] == info["sha256"]
                and manifest["files"][name]["bytes"] == info["bytes"],
                "Wheel identity mismatch",
            )
        identity = archive.read("application/desktop/native/build_identity.py")
        require(
            identity == build_identity(manifest["kind"]), "Wrong application identity"
        )
        require(
            archive.read("notices/LICENSE") == (root / "LICENSE").read_bytes(),
            "Original code license mismatch",
        )
        require(
            archive.read("cyrnava-native")[:4] == b"\x7fELF"
            and manifest["bootstrap_build"]["source_sha256"]
            == manifest["files"]["bootstrap.c"]["sha256"]
            and manifest["bootstrap_build"]["executable_sha256"]
            == manifest["files"]["cyrnava-native"]["sha256"],
            "Compiled launcher provenance mismatch",
        )
        proof = manifest["frontend_build"]
        require(proof["status"] == "PASS", "Frontend build not successful")
        actual_frontend = {
            n.removeprefix("application/frontend/dist/"): v["sha256"]
            for n, v in manifest["files"].items()
            if n.startswith("application/frontend/dist/")
        }
        require(
            actual_frontend == proof["output_files"], "Built frontend identity mismatch"
        )
        require(
            all(
                manifest["source_provenance"]["source_files"].get(n) == h
                for n, h in proof["source_files"].items()
            ),
            "Frontend source provenance mismatch",
        )
    provenance_record = json.loads((output / "provenance.json").read_text())
    with zipfile.ZipFile(output / "CyrNava-source.zip") as source:
        source_record = json.loads(source.read("SOURCE-MANIFEST.json"))
        require(
            source_record
            == manifest["source_provenance"]
            == provenance_record["source"],
            "Source provenance mismatch",
        )
        require(
            set(source.namelist())
            == set(source_record["source_files"]) | {"SOURCE-MANIFEST.json"},
            "Source inventory mismatch",
        )
        for name, expected in source_record["source_files"].items():
            member(name)
            require(
                hashlib.sha256(source.read(name)).hexdigest() == expected,
                "Source snapshot changed",
            )
        current_sources = source_files(root)
        require(
            set(current_sources) == set(source_record["source_files"])
            and all(
                sha(p) == source_record["source_files"][n]
                for n, p in current_sources.items()
            ),
            "Audit checkout differs from exact source snapshot",
        )
    with zipfile.ZipFile(archive_path) as archive:
        bindings = {
            n: n.removeprefix("application/")
            for n in manifest["files"]
            if n.startswith(("application/backend/app/", "application/desktop/native/"))
            and not n.endswith("/build_identity.py")
        }
        bindings.update(
            {
                n: "desktop/" + n
                for n in [
                    "install_engine.py",
                    "native_operations.py",
                    "native_profile_check.py",
                ]
            }
        )
        bindings.update(
            {
                n: "packaging/native/" + n
                for n in [
                    "launch.py",
                    "provider_check.py",
                    "apparmor_support.py",
                    "bootstrap.c",
                ]
            }
        )
        bindings.update(
            {
                "system_schemas.py": "packaging/native/feasibility/run_probe.py",
                "backend_check.py": "packaging/native/feasibility/backend_check.py",
                "requirements.lock": "packaging/native/feasibility/requirements.lock",
                "dependencies.json": "packaging/native/feasibility/dependencies.json",
                "notices/LICENSE": "LICENSE",
            }
        )
        require(
            all(
                manifest["files"][n]["sha256"] == source_record["source_files"].get(p)
                for n, p in bindings.items()
            ),
            "Payload/source correspondence mismatch",
        )
        exported = json.loads((output / "installer-checksums.json").read_text())[
            "files"
        ]
        require(
            set(exported)
            == {
                "install.sh",
                "install_engine.py",
                "native_operations.py",
                "native_profile_check.py",
                "update.sh",
                "uninstall.sh",
                "policy_setup.py",
            },
            "Unexpected standalone installer contents",
        )
        with zipfile.ZipFile(output / "CyrNava-installer.zip") as installer:
            require(
                len(installer.namelist()) == len(set(installer.namelist()))
                and set(installer.namelist()) == set(exported),
                "Installer archive inventory mismatch",
            )
            for name, expected in exported.items():
                content = installer.read(name)
                require(
                    hashlib.sha256(content).hexdigest()
                    == expected
                    == sha(output / name),
                    "Installer export hash mismatch",
                )
                if name in {
                    "install_engine.py",
                    "native_operations.py",
                    "native_profile_check.py",
                }:
                    require(
                        content == archive.read(name),
                        "Standalone installer differs from payload",
                    )
                else:
                    original = (root / "packaging/native" / name).read_text()
                    if name == "install.sh":
                        original = original.replace(
                            "$entry_dir/../../desktop/install_engine.py",
                            "$entry_dir/install_engine.py",
                        )
                    require(
                        content == original.encode(),
                        "Standalone shell differs from reviewed entry point",
                    )
    require(
        sha(output / "CyrNava-source.zip")
        == provenance_record["source_archive_sha256"],
        "Source artifact changed",
    )
    require(
        sha(output / "CyrNava-installer.zip")
        == provenance_record["installer_archive_sha256"],
        "Installer artifact changed",
    )
    result = {
        "status": "PASS",
        "scope": "native exported-package/source/bootstrap audit",
        "archive_sha256": manifest["archive_sha256"],
        "manifest_sha256": sha(output / "manifest.json"),
        "payload_files": len(manifest["files"]),
        "source_files": len(source_record["source_files"]),
        "GUI": "NOT EXECUTED",
        "renderer": "NOT EXECUTED",
        "signature": "NOT CREATED",
        "redistribution_clearance": "PENDING; audit is not legal clearance",
    }
    return result
