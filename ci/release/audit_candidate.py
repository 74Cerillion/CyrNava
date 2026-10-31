"""Run the accepted P5A payload auditor against the approved source checkout."""

import argparse
import os
from pathlib import Path

import core


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    core.policy()
    source = core.safe_path(args.source)
    sha = core.call("git", "-C", source, "rev-parse", "HEAD").decode().strip()
    entry = core.approval(
        sha,
        core.policy()["version"],
        "staging",
        core.policy()["approved_staging_sources"][0]["authorization_ref"],
    )
    core.require(
        os.environ.get("GITHUB_SHA") == sha, "Auditor child source binding mismatch"
    )
    core.require(
        not core.call("git", "-C", source, "status", "--porcelain"),
        "Source checkout must be clean",
    )
    core.validate_candidate(args.candidate, entry)
    auditor = core.p5a()
    auditor.ROOT = source
    result = auditor.audit_bundle(args.candidate, args.output)
    (args.output / "audit-result.json").write_bytes(core.encode(result))


if __name__ == "__main__":
    main()
