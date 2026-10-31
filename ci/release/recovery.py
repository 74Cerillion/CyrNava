"""Guarded local staging activation. Never edits application profiles/databases."""

import argparse
import json
from pathlib import Path

import core


def activate_retained(store, generation, public_key, fingerprint):
    core.require(
        core.SHA.fullmatch(generation) is not None, "Full generation digest required"
    )
    public = core.safe_path(store / "generations" / generation)
    core.require(
        core.sha(public / "manifest.json") == generation,
        "Retained generation digest mismatch",
    )
    result = core.publish_local(public, store, public_key, fingerprint)
    return {
        **result,
        "database_action": "NONE",
        "warning": (
            "Binary rollback does not reverse schema migration. "
            "Use verified P3 backup/recovery procedures for data compatibility."
        ),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--generation", required=True)
    parser.add_argument("--public-key", type=Path, required=True)
    parser.add_argument("--fingerprint", required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            activate_retained(
                args.store, args.generation, args.public_key, args.fingerprint
            ),
            indent=2,
        )
    )
