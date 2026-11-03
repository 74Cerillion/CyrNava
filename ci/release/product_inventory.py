"""P6 bounded evidence inventory of verified app/runtime trees, not legal clearance."""

import argparse
import email.parser
import json
from pathlib import Path

import core
import readiness


def spdx_packages(text):
    """Extract package fields; retain raw document hashes as authoritative records.

    This is deliberately not a complete SPDX parser or conversion. Relationships,
    files, snippets and multiline licenses are not reinterpreted or discarded from
    upstream documents; consumers must consult the hashed original inventories.
    """
    packages = []
    current = None
    for line in text.splitlines():
        key, separator, value = line.partition(": ")
        if not separator:
            continue
        if key == "PackageName":
            current = {"name": value}
            packages.append(current)
        elif current is not None and key in {
            "PackageVersion",
            "PackageLicenseConcluded",
            "PackageLicenseDeclared",
            "PackageDownloadLocation",
            "SPDXID",
        }:
            current[key] = (
                value if not value.startswith("<text>") else "MULTILINE; see original"
            )
    return packages


def inspect_tree(root):
    root = core.safe_path(root)
    documents, python, native, notices, skipped = [], [], [], [], 0
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            skipped += 1
            continue
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if path.suffix == ".spdx" and "sbom" in path.parts:
            core.require(path.stat().st_size <= 64 * 1024**2, "Upstream SBOM too large")
            documents.append(
                {
                    "path": rel,
                    "sha256": core.sha(path),
                    "packages": spdx_packages(path.read_text(errors="replace")),
                }
            )
        elif path.name == "METADATA" and path.parent.name.endswith(".dist-info"):
            core.require(path.stat().st_size <= 8 * 1024**2, "Wheel metadata too large")
            value = email.parser.Parser().parsestr(path.read_text(errors="replace"))
            python.append(
                {
                    "name": value.get("Name"),
                    "version": value.get("Version"),
                    "license": value.get("License-Expression") or value.get("License"),
                    "metadata_path": rel,
                    "sha256": core.sha(path),
                }
            )
        elif "licenses" in path.parts or path.name.lower().startswith(
            ("license", "copying")
        ):
            notices.append({"path": rel, "sha256": core.sha(path)})
        else:
            with path.open("rb") as stream:
                if stream.read(4) == b"\x7fELF":
                    native.append(
                        {
                            "path": rel,
                            "sha256": core.sha(path),
                            "bytes": path.stat().st_size,
                        }
                    )
    manifest = root / "manifest.json"
    return {
        "upstream_spdx": documents,
        "python_distributions": python,
        "native_elf_files": native,
        "notice_files": notices,
        "symlinks_not_followed": skipped,
        "upstream_build_manifest_sha256": core.sha(manifest)
        if manifest.is_file()
        else None,
    }


def collect(source, app, runtime, runtime_commit):
    lock = core.read_json(source / "packaging/flatpak/production/toolchain.lock.json")
    core.require(
        runtime_commit == lock["refs"]["org.kde.Platform//6.11"],
        "Runtime provenance differs from approved lock",
    )
    inputs = core.read_json(app / "share/cyrnava/build-inputs.json")
    core.require(inputs["app_id"] == core.APP_ID, "Wrong application inventory")
    return {
        "format": "CyrNava P6 product evidence inventory 1",
        "status": "EXPANDED INVENTORY; NOT COMPLETE SBOM OR LICENSE CLEARANCE",
        "application_source": inputs["git_commit"],
        "application_build_inputs_sha256": core.sha(
            app / "share/cyrnava/build-inputs.json"
        ),
        "source_lock_inventory_scope": (
            "candidate source; may differ from accepted binary"
        ),
        "source_lock_sbom": readiness.inventory(source),
        "runtime": {"ref": "org.kde.Platform/x86_64/6.11", "commit": runtime_commit},
        "app_tree": inspect_tree(app),
        "runtime_tree": inspect_tree(runtime),
        "limitations": [
            "SPDX package fields are an index; original documents remain authoritative",
            "Upstream NOASSERTION and missing versions are not inferred",
            "ELF hashes identify shipped files, not all statically embedded components",
            "Host kernel, drivers, optional extensions and firmware not inventoried",
            "No complete vulnerability, reachability or redistribution certification",
            "Source-lock development components are not asserted to be shipped",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=core.ROOT)
    parser.add_argument("--app", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--runtime-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    value = collect(args.source, args.app, args.runtime, args.runtime_commit)
    core.require(not args.output.exists(), "Inventory evidence already exists")
    args.output.write_text(json.dumps(value, indent=2) + "\n")
    print(
        json.dumps({"status": value["status"], "output_sha256": core.sha(args.output)})
    )


if __name__ == "__main__":
    main()
