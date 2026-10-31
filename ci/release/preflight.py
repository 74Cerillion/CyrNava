"""Unprivileged read-only checks before the protected staging job."""

import json
import os

import core
import github


def main():
    core.require(
        os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
        and os.environ.get("GITHUB_REF")
        == "refs/heads/" + core.policy()["workflow_branch"],
        "Only the reviewed manual integration-branch workflow is eligible",
    )
    entry = core.approval(
        os.environ.get("RELEASE_SOURCE", ""),
        os.environ.get("RELEASE_VERSION", ""),
        os.environ.get("RELEASE_CHANNEL", ""),
        os.environ.get("RELEASE_AUTHORIZATION", ""),
    )
    core.require(
        os.environ.get("RELEASE_CI_RUN") == str(entry["ci_run_id"]),
        "Incorrect CI run input",
    )
    github.check_environment()
    print(json.dumps(github.live_evidence(entry)))


if __name__ == "__main__":
    main()
