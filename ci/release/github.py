"""Read-only GitHub eligibility and artifact retrieval; no publication API."""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

from core import Rejected, ci_eligibility, policy, require, sha

PREFIX = "https://api.github.com/repos/74Cerillion/CyrNava/"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request(path):
    require(
        not path.startswith(("/", "http")) and ".." not in path,
        "Only fixed repository read endpoints allowed",
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "CyrNava-P5B-staging",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    return urllib.request.Request(PREFIX + path, headers=headers, method="GET")


def get(path, raw=False):
    req = request(path)
    if raw:
        req.add_header("Accept", "application/vnd.github.raw+json")
    try:
        with urllib.request.build_opener(NoRedirect()).open(
            req, timeout=30
        ) as response:
            value = response.read(4 * 1024**2 + 1)
        require(len(value) <= 4 * 1024**2, "GitHub response exceeds bound")
        return value if raw else json.loads(value)
    except (OSError, ValueError) as error:
        if isinstance(error, Rejected):
            raise
        raise Rejected("GitHub eligibility read failed; no release fallback") from None


def environment_eligible(environment, branches):
    require(
        environment.get("name") == policy()["environment"],
        "Unexpected approval environment",
    )
    require(
        environment.get("can_admins_bypass") is False,
        "Administrator bypass must be disabled",
    )
    reviewers = [
        r
        for r in environment.get("protection_rules", [])
        if r.get("type") == "required_reviewers"
    ]
    require(
        len(reviewers) == 1
        and reviewers[0].get("prevent_self_review") is True
        and len(reviewers[0].get("reviewers", [])) > 0,
        "Required independent reviewer protection missing",
    )
    require(
        environment.get("deployment_branch_policy")
        == {"protected_branches": False, "custom_branch_policies": True},
        "Explicit deployment branch restriction required",
    )
    require(
        branches.get("total_count") == 1
        and len(branches.get("branch_policies", [])) == 1
        and branches["branch_policies"][0].get("name") == policy()["workflow_branch"]
        and branches["branch_policies"][0].get("type") == "branch",
        "Deployment branch allowlist mismatch",
    )
    return True


def check_environment():
    name = policy()["environment"]
    return environment_eligible(
        get("environments/" + name),
        get("environments/" + name + "/deployment-branch-policies"),
    )


def live_evidence(entry):
    run = get(f"actions/runs/{entry['ci_run_id']}/attempts/{entry['ci_run_attempt']}")
    jobs = get(
        f"actions/runs/{entry['ci_run_id']}/attempts/{entry['ci_run_attempt']}/jobs?per_page=100"
    )
    require(
        jobs.get("total_count") == len(jobs.get("jobs", [])), "Incomplete job evidence"
    )
    artifact = get(f"actions/artifacts/{entry['artifact_id']}")
    workflow = get(
        "contents/.github/workflows/ci.yml?ref=" + entry["source_commit"], raw=True
    )
    ci_eligibility(run, jobs["jobs"], artifact, workflow, entry)
    return {
        "status": "PASS",
        "source_commit": entry["source_commit"],
        "ci_run_id": entry["ci_run_id"],
        "ci_run_attempt": entry["ci_run_attempt"],
        "artifact_id": entry["artifact_id"],
        "workflow_sha256": policy()["ci_workflow_sha256"],
        "required_jobs": [
            {"name": j["name"], "conclusion": j["conclusion"]} for j in jobs["jobs"]
        ],
    }


def download(entry, destination):
    # Never forward the API bearer token across GitHub's signed CDN redirect.
    try:
        response = urllib.request.build_opener(NoRedirect()).open(
            request(f"actions/artifacts/{entry['artifact_id']}/zip"), timeout=30
        )
    except urllib.error.HTTPError as error:
        require(error.code in (301, 302, 303, 307), "Artifact download denied")
        url = error.headers.get("Location", "")
        parsed = urllib.parse.urlsplit(url)
        require(
            parsed.scheme == "https"
            and parsed.port in (None, 443)
            and not parsed.username
            and parsed.hostname is not None
            and parsed.hostname.endswith(
                (".blob.core.windows.net", ".actions.githubusercontent.com")
            ),
            "Unexpected artifact download endpoint",
        )
        # No Authorization header or original request headers reach this endpoint.
        response = urllib.request.build_opener(NoRedirect()).open(url, timeout=60)
    except OSError:
        raise Rejected("Artifact download failed") from None
    try:
        with response, destination.open("xb") as stream:
            size = 0
            while block := response.read(1024**2):
                size += len(block)
                require(size < 1024**3, "Artifact download exceeds bound")
                stream.write(block)
    except OSError:
        raise Rejected("Artifact download/storage failed") from None
    require(
        sha(destination) == entry["artifact_zip_sha256"],
        "Downloaded artifact digest mismatch",
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["check-environment"])
    parser.parse_args()
    check_environment()
    print('{"environment":"PASS"}')
