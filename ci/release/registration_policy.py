"""Local review checks only; no GitHub writes, dispatch, signing or publication.

The proposal lives outside .github/workflows. Moving it onto main is separately
authorized. Execution identity and environment snapshots are owner readbacks, not
claims that a protected hosted run has taken place.
"""

import argparse
import copy
import json
import re
from pathlib import Path

import github
import workflow_policy
from core import HERE, ROOT, policy, require


def validate_registration(registration, integration):
    workflow_policy.validate(integration)
    expected = {
        "name": integration["name"],
        "on": copy.deepcopy(integration["on"]),
        "permissions": {"contents": "read"},
        "jobs": {
            "registration": {
                "if": "${{ false }}",
                "runs-on": "ubuntu-24.04",
                "timeout-minutes": 1,
                "steps": [{"name": "Inert registration marker", "run": ":"}],
            }
        },
    }
    require(
        registration == expected,
        "Registration must match the inert reviewed shape and integration inputs",
    )
    return True


def validate_execution(run, workflow_bytes, tooling_commit, workflow_id):
    """Owner readback of the exact run; no independent approval is claimed."""
    value = policy()
    require(
        re.fullmatch(r"[a-f0-9]{40}", tooling_commit) is not None,
        "Full owner-approved release-tooling commit required",
    )
    require(
        run.get("repository", {}).get("id") == value["repository_id"]
        and run.get("head_repository", {}).get("id") == value["repository_id"],
        "Unexpected execution repository",
    )
    require(
        run.get("event") == "workflow_dispatch"
        and run.get("head_branch") == value["workflow_branch"]
        and run.get("head_sha") == tooling_commit
        and run.get("run_attempt") == 1
        and run.get("actor", {}).get("login", "").lower()
        == value["staging_owner"].lower()
        and run.get("triggering_actor", {}).get("login", "").lower()
        == value["staging_owner"].lower(),
        "Unexpected execution ref, tooling commit, trigger or attempt",
    )
    require(
        isinstance(workflow_id, int)
        and workflow_id > 0
        and run.get("workflow_id") == workflow_id
        and run.get("path") == ".github/workflows/release.yml",
        "Unexpected registered workflow identity",
    )
    require(
        workflow_bytes == (ROOT / ".github/workflows/release.yml").read_bytes(),
        "Run workflow differs from reviewed integration definition",
    )
    workflow_policy.validate(
        workflow_policy.read_workflow(ROOT / ".github/workflows/release.yml")
    )
    return True


def validate_environment(environment, branches):
    return github.environment_eligible(environment, branches)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--registration", type=Path, default=HERE / "registration-only.yml"
    )
    parser.add_argument("--run-record", type=Path)
    parser.add_argument("--run-workflow", type=Path)
    parser.add_argument("--tooling-commit")
    parser.add_argument("--workflow-id", type=int)
    parser.add_argument("--environment-record", type=Path)
    parser.add_argument("--branches-record", type=Path)
    args = parser.parse_args()
    validate_registration(
        workflow_policy.read_workflow(args.registration),
        workflow_policy.read_workflow(ROOT / ".github/workflows/release.yml"),
    )
    if any((args.run_record, args.run_workflow, args.tooling_commit, args.workflow_id)):
        require(
            all(
                (
                    args.run_record,
                    args.run_workflow,
                    args.tooling_commit,
                    args.workflow_id,
                )
            ),
            "All four execution readback arguments are required together",
        )
        validate_execution(
            json.loads(args.run_record.read_text()),
            args.run_workflow.read_bytes(),
            args.tooling_commit,
            args.workflow_id,
        )
    if args.environment_record or args.branches_record:
        require(
            args.environment_record and args.branches_record,
            "Environment and branch readbacks are required together",
        )
        validate_environment(
            json.loads(args.environment_record.read_text()),
            json.loads(args.branches_record.read_text()),
        )
    print("P5B local registration/readback checks: PASS (no external action)")


if __name__ == "__main__":
    main()
