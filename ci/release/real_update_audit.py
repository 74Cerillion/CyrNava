"""P6-only owner-approved B audit; never expands P5B staging eligibility.

Reuse the unchanged, hash-pinned exported-payload auditor. Child diagnostics
contain fixed operation/stage identifiers and failure categories, never argv,
stderr, exception messages, paths, or environment values.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import core

OPERATION = "p6-generation-B-payload-audit"
STAGES = {
    "output-guard",
    "owner-approval",
    "source-binding",
    "source-cleanliness",
    "candidate-validation",
    "exported-payload-audit",
    "audit-result-validation",
}


def failure_category(error):
    if isinstance(error, subprocess.CalledProcessError):
        return f"exit-{int(error.returncode)}"
    if isinstance(error, subprocess.TimeoutExpired):
        return "timeout"
    if isinstance(error, OSError):
        return "unavailable"
    if isinstance(error, core.Rejected):
        return "rejected"
    if isinstance(error, (ValueError, KeyError, TypeError)):
        return "invalid-data"
    if isinstance(error, KeyboardInterrupt):
        return "interrupted"
    return "exception"


class AuditFailure(core.Rejected):
    def __init__(self, diagnostic):
        self.diagnostic = diagnostic
        super().__init__(f"P6 operation failed: {OPERATION} ({diagnostic['category']})")


def run(source, candidate, output, approval, entry, approval_sha256):
    """Run only the dedicated P6 child and accept an exact, complete audit result."""
    try:
        subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--source",
                str(source),
                "--candidate",
                str(candidate),
                "--output",
                str(output),
                "--b-approval",
                str(approval),
                "--approval-sha256",
                approval_sha256,
            ],
            env={**os.environ, "GITHUB_SHA": entry["source_commit"]},
            check=True,
            capture_output=True,
            timeout=300,
        )
    except (OSError, subprocess.SubprocessError) as error:
        diagnostic = {"operation": OPERATION, "category": failure_category(error)}
        try:
            child = core.read_json(output / "audit-result.json")
            if (
                isinstance(child, dict)
                and child.get("status") == "FAIL"
                and child.get("complete") is True
                and child.get("operation") == OPERATION
                and child.get("stage") in STAGES
            ):
                diagnostic["child_stage"] = child["stage"]
        except (OSError, ValueError, KeyError, TypeError):
            pass
        raise AuditFailure(diagnostic) from None
    result = core.read_json(output / "audit-result.json")
    core.require(
        isinstance(result, dict)
        and result.get("status") == "PASS"
        and result.get("complete") is True
        and result.get("operation") == OPERATION
        and result.get("source_commit") == entry["source_commit"]
        and result.get("sha256") == entry["bundle_sha256"]
        and result.get("ostree_commit") == entry["ostree_commit"]
        and result.get("B_approval_sha256") == approval_sha256,
        "P6 B audit result differs from approved identity",
    )
    return result


def audit_candidate(source, candidate, output, approval, approval_sha256):
    # Import lazily: the parent imports this module to invoke its isolated child.
    from real_update import approved_b

    record = {"status": "FAIL", "complete": True, "operation": OPERATION}
    stage = "output-guard"
    writable = False
    try:
        output = core.outside_source(output)
        core.require(
            output.is_dir() and not any(output.iterdir()),
            "Fresh empty P6 audit output required",
        )
        writable = True
        stage = "owner-approval"
        core.require(
            core.SHA.fullmatch(approval_sha256) is not None
            and core.sha(core.safe_path(approval)) == approval_sha256,
            "P6 B approval record changed",
        )
        entry = approved_b(approval)
        stage = "source-binding"
        source = core.safe_path(source)
        sha = core.call("git", "-C", source, "rev-parse", "HEAD").decode().strip()
        core.require(
            sha == entry["source_commit"] == os.environ.get("GITHUB_SHA"),
            "P6 B auditor source binding mismatch",
        )
        stage = "source-cleanliness"
        core.require(
            not core.call(
                "git", "--no-optional-locks", "-C", source, "status", "--porcelain"
            ),
            "P6 B source checkout must be clean",
        )
        stage = "candidate-validation"
        core.validate_candidate(candidate, entry)
        stage = "exported-payload-audit"
        auditor = core.p5a()
        auditor.ROOT = source
        result = auditor.audit_bundle(candidate, output)
        stage = "audit-result-validation"
        core.require(
            result.get("status") == "PASS"
            and result.get("source_commit") == entry["source_commit"]
            and result.get("sha256") == entry["bundle_sha256"]
            and result.get("ostree_commit") == entry["ostree_commit"],
            "P6 B exported audit identity mismatch",
        )
        record.update(result, B_approval_sha256=approval_sha256)
    except (Exception, KeyboardInterrupt) as error:
        record.update(stage=stage, category=failure_category(error))
    if writable:
        (output / "audit-result.json").write_bytes(core.encode(record))
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "candidate", "output", "b-approval"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--approval-sha256", required=True)
    args = parser.parse_args()
    os.umask(0o077)
    result = audit_candidate(
        args.source, args.candidate, args.output, args.b_approval, args.approval_sha256
    )
    print(json.dumps(result, indent=2), flush=True)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
