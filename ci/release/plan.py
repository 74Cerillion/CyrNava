"""Produce a review-only GitHub Releases plan. No write API or tag creation."""

import argparse
from pathlib import Path

import core


def release_plan(public, public_key, fingerprint, parent):
    core.verify_seal(public, public_key, fingerprint, parent)
    release = core.read_json(public / "release.json")
    core.require(
        release.get("purpose") == "p5b-staging"
        and release.get("signing_fingerprint") == fingerprint,
        "Release plan requires the verified staging identity",
    )
    return {
        "format": 1,
        "status": "REVIEW ONLY — PRODUCTION DISABLED",
        "repository": core.policy()["repository"],
        "source_commit": release["source_commit"],
        "application_id": core.APP_ID,
        "version": release["version"],
        "proposed_tag": "v" + release["version"],
        "tag_created": False,
        "github_release_created": False,
        "production_publication_enabled": False,
        "required_assets": [
            core.BUNDLE,
            "SHA256SUMS",
            "release-provenance.json",
            "RELEASE_NOTES.md",
        ],
        "required_links": [
            "owner-approved HTTPS Flatpak remote",
            "independently verified public key fingerprint",
        ],
        "blocking_approvals": [
            "production key custody and identity",
            "permanent hosting endpoint/cost",
            "redistribution licensing review",
            "per-release signing/publication authorization",
        ],
        "notes": (
            "Checksums establish byte integrity. Publisher authentication requires "
            "the approved signing trust anchor. Staging keys are never production keys."
        ),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public", type=Path, required=True)
    parser.add_argument("--public-key", type=Path, required=True)
    parser.add_argument("--fingerprint", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = core.outside_source(args.output)
    value = release_plan(args.public, args.public_key, args.fingerprint, output.parent)
    with output.open("xb") as stream:
        stream.write(core.encode(value))
