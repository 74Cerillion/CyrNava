"""Read-only checks for the owner-dispatched, branch-restricted staging job."""

import json
import os

import core
import github


def main():
    github.check_execution()
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
