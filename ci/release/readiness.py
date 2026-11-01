"""Review-only release readiness inventory; no production tag or release API."""

import datetime
import json
import re
import urllib.error
import urllib.parse
import urllib.request

import core


def inventory(source):
    lock = core.read_json(source / "frontend/package-lock.json")
    components = {}
    for path, value in lock["packages"].items():
        if not path or not value.get("version"):
            continue
        name = value.get("name") or path.rsplit("node_modules/", 1)[-1]
        purl = "pkg:npm/" + urllib.parse.quote(name, safe="/") + "@" + value["version"]
        components[purl] = {
            "type": "library",
            "name": name,
            "version": value["version"],
            "purl": purl,
            "properties": [
                {
                    "name": "cyrnava:devDependency",
                    "value": str(bool(value.get("dev"))).lower(),
                }
            ],
        }
    wheel_lock = source / "packaging/flatpak/production/requirements.lock"
    for line in wheel_lock.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(
            r"([A-Za-z0-9_.-]+)==([^ ]+) --hash=sha256:([a-f0-9]{64})", line
        )
        core.require(match is not None, "Unsupported runtime lock entry")
        name, version, digest = match.groups()
        purl = "pkg:pypi/" + name.lower().replace("_", "-") + "@" + version
        components[purl] = {
            "type": "library",
            "name": name,
            "version": version,
            "purl": purl,
            "hashes": [{"alg": "SHA-256", "content": digest}],
        }
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "version": 1,
        "metadata": {
            "component": {
                "type": "application",
                "name": "CyrNava",
                "version": core.policy()["version"],
            },
            "properties": [
                {
                    "name": "cyrnava:coverage",
                    ("value"): (
                        "Source-lock inventory including build dependencies; not a "
                        "complete product/runtime SBOM. KDE/PySide/native "
                        "transitive libraries, generated bundles and file-level "
                        "license coverage are not enumerated."
                    ),
                }
            ],
        },
        "components": sorted(components.values(), key=lambda c: c["purl"]),
    }


def advisories(sbom):
    """Bounded read-only OSV queries for the public pinned package inventory."""
    components = sbom["components"]
    findings = []
    completed = 0
    for start in range(0, len(components), 100):
        chunk = components[start : start + 100]
        queries = [{"package": {"purl": c["purl"]}} for c in chunk]
        request = urllib.request.Request(
            "https://api.osv.dev/v1/querybatch",
            data=json.dumps({"queries": queries}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read(10 * 1024**2 + 1)
            core.require(len(raw) <= 10 * 1024**2, "Advisory response exceeds bound")
            results = json.loads(raw)["results"]
            core.require(
                len(results) == len(chunk),
                "Incomplete advisory response (including pagination)",
            )
            core.require(
                not any(result.get("next_page_token") for result in results),
                "Paginated advisory response requires further review",
            )
            for component, result in zip(chunk, results, strict=True):
                ids = sorted({v["id"] for v in result.get("vulns", [])})
                if ids:
                    findings.append({"purl": component["purl"], "advisory_ids": ids})
            completed += len(chunk)
        except (OSError, ValueError, KeyError, TypeError):
            return {
                "status": "INCOMPLETE",
                "source": "OSV querybatch",
                "queried": completed,
                "total": len(components),
                "findings": findings,
                ("meaning"): (
                    "No vulnerability clearance; unavailable or malformed "
                    "advisory response (including pagination)"
                ),
            }
    return {
        "status": "COMPLETE WITH FINDINGS" if findings else "COMPLETE NO MATCHES",
        "source": "OSV querybatch",
        "queried": completed,
        "total": len(components),
        "findings": findings,
        "checked_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        ("meaning"): (
            "Advisory matching only, not vulnerability clearance; "
            "unenumerated runtime/native components remain outside "
            "scope"
        ),
    }


def plan(source, release, scan=False):
    sbom = inventory(source)
    source_sha = core.call("git", "-C", source, "rev-parse", "HEAD").decode().strip()
    core.require(source_sha == release["source_commit"], "Readiness source mismatch")
    checksums = {
        "bundle_sha256": release["bundle_sha256"],
        "frontend_lock_sha256": core.sha(source / "frontend/package-lock.json"),
        "runtime_lock_sha256": core.sha(
            source / "packaging/flatpak/production/requirements.lock"
        ),
    }
    notes = source / "docs/release-notes-v0.1.0.md"
    return {
        "status": "REVIEW ONLY; PRODUCTION DISABLED",
        "source_commit": source_sha,
        "tooling_commit": release["release_tooling_commit"],
        "version": release["version"],
        "candidate_name": "0.1.0-rc.1 (proposed; no version/schema change)",
        "proposed_tag": "v0.1.0-rc.1",
        "tag_target": source_sha,
        "tag_created": False,
        "release_created": False,
        "publication_enabled": False,
        "checksums": checksums,
        "release_notes": {
            "exists": notes.is_file(),
            "sha256": core.sha(notes) if notes.is_file() else None,
        },
        "sbom": sbom,
        "advisories": advisories(sbom)
        if scan
        else {"status": "NOT EXECUTED", "clearance": False},
        ("reproducibility"): (
            "Pinned inputs and payload audit verified; byte-for-byte "
            "reproducibility NOT VERIFIED"
        ),
        ("licensing"): (
            "Code/logo redistribution approval pending; "
            "LicenseRef-proprietary and metadata-only CC0 approval "
            "preserved; upstream notices do not establish distribution "
            "clearance"
        ),
        "production_blockers": [
            "owner per-release authorization and signing trust anchor",
            "hosting/credentials/production authorization",
            "redistribution and third-party license review",
            "complete runtime/native SBOM and advisory review",
            "advisory findings triage and runtime support/update policy",
        ],
        ("runtime_obligations"): (
            "Monitor locked KDE/PySide runtime maintenance and "
            "advisories; verify upstream trust/commits and supported "
            "branches before each release. A pin is not a "
            "security-update policy."
        ),
        ("retention"): (
            "Retain every object exposed by prior generations until a "
            "separately reviewed client retention/GC policy exists. "
            "Recovery is verified snapshot activation; binary rollback "
            "never downgrades application schema."
        ),
        "release_procedure": [
            "review accepted source, CI and all artifact hashes",
            "verify candidate notes, SBOM coverage, advisories and licensing",
            "obtain separate immutable tag/release/signing/hosting approvals",
            "use owner offline production signing; never promote staging keys",
            (
                "publish complete immutable generation and verify before "
                "activating pointer"
            ),
            (
                "verify fresh/existing clients and retain previous objects;"
                " P6 covers broader distribution"
            ),
        ],
    }
