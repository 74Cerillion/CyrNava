"""Synthetic local controls for the proposed inert registration and readbacks."""

import copy
import unittest

import core
import registration_policy as registration
import workflow_policy


class RegistrationTests(unittest.TestCase):
    def setUp(self):
        self.proposal = workflow_policy.read_workflow(
            core.HERE / "registration-only.yml"
        )
        self.integration = workflow_policy.read_workflow(
            core.ROOT / ".github/workflows/release.yml"
        )

    def test_inert_definition_and_exact_input_schema(self):
        self.assertTrue(
            registration.validate_registration(self.proposal, self.integration)
        )

    def test_release_capabilities_or_mutable_skip_are_rejected(self):
        mutations = [
            lambda v: v["on"].update(push={}),
            lambda v: v["permissions"].update(contents="write"),
            lambda v: v["permissions"].update(**{"id-token": "write"}),
            lambda v: v.update(env={"TOKEN": "${{ secrets.EXAMPLE }}"}),
            lambda v: v["jobs"]["registration"].update(**{"if": "always()"}),
            lambda v: v["jobs"]["registration"].pop("if"),
            lambda v: v["jobs"]["registration"].update(environment="p5b-staging"),
            lambda v: v["jobs"]["registration"].update(uses="./other.yml"),
            lambda v: v["jobs"]["registration"]["steps"].append(
                {"uses": "actions/checkout@main"}
            ),
            lambda v: v["jobs"]["registration"]["steps"][0].update(
                run="python ci/release/stage.py"
            ),
            lambda v: v["jobs"].update(unexpected={"steps": [{"run": "exit 0"}]}),
        ]
        for index, mutate in enumerate(mutations):
            changed = copy.deepcopy(self.proposal)
            mutate(changed)
            with self.subTest(case=index), self.assertRaises(core.Rejected):
                registration.validate_registration(changed, self.integration)

    def test_input_drift_is_rejected(self):
        mutations = [
            lambda v: v.pop("source_commit"),
            lambda v: v.update(tooling_commit={"type": "string"}),
            lambda v: v["channel"].update(options=["staging", "production"]),
            lambda v: v["source_commit"].update(required=False),
            lambda v: v["ci_run_id"].update(type="number"),
            lambda v: v["version"].update(default="0.2.0"),
        ]
        for index, mutate in enumerate(mutations):
            changed = copy.deepcopy(self.proposal)
            mutate(changed["on"]["workflow_dispatch"]["inputs"])
            with self.subTest(case=index), self.assertRaises(core.Rejected):
                registration.validate_registration(changed, self.integration)

    def test_integration_contract_must_also_be_valid(self):
        self.integration["permissions"]["contents"] = "write"
        with self.assertRaises(core.Rejected):
            registration.validate_registration(self.proposal, self.integration)


class ExecutionIdentityTests(unittest.TestCase):
    def setUp(self):
        # Synthetic IDs/commit: this fixture is not a hosted staging execution.
        self.commit = "a" * 40
        self.workflow_id = 123
        self.workflow = (core.ROOT / ".github/workflows/release.yml").read_bytes()
        self.run = {
            "repository": {"id": core.policy()["repository_id"]},
            "head_repository": {"id": core.policy()["repository_id"]},
            "event": "workflow_dispatch",
            "actor": {"login": "74Cerillion"},
            "triggering_actor": {"login": "74Cerillion"},
            "head_branch": core.policy()["workflow_branch"],
            "head_sha": self.commit,
            "run_attempt": 1,
            "workflow_id": self.workflow_id,
            "path": ".github/workflows/release.yml",
        }

    def verify(self):
        return registration.validate_execution(
            self.run, self.workflow, self.commit, self.workflow_id
        )

    def test_independent_run_identity_readback(self):
        self.assertTrue(self.verify())

    def test_wrong_repository_ref_sha_workflow_event_or_rerun_rejected(self):
        mutations = [
            ("repository", {"id": 1}),
            ("head_repository", {"id": 1}),
            ("head_branch", "main"),
            ("head_branch", "refs/pull/1/merge"),
            ("head_branch", "refs/tags/staging"),
            ("head_sha", "b" * 40),
            ("workflow_id", 124),
            ("path", ".github/workflows/ci.yml"),
            ("event", "push"),
            ("actor", {"login": "another-account"}),
            ("triggering_actor", {"login": "another-account"}),
            ("run_attempt", 2),
        ]
        original = copy.deepcopy(self.run)
        for key, value in mutations:
            self.run = {**original, key: value}
            with self.subTest(key=key, value=value), self.assertRaises(core.Rejected):
                self.verify()

    def test_changed_workflow_or_mutable_tooling_name_rejected(self):
        for workflow, commit in [
            (self.workflow + b"# altered", self.commit),
            (self.workflow, "main"),
        ]:
            with self.subTest(commit=commit), self.assertRaises(core.Rejected):
                registration.validate_execution(
                    self.run, workflow, commit, self.workflow_id
                )


class EnvironmentReadbackTests(unittest.TestCase):
    def setUp(self):
        self.environment = {
            "name": "p5b-staging",
            "protection_rules": [{"type": "branch_policy"}],
            "deployment_branch_policy": {
                "protected_branches": False,
                "custom_branch_policies": True,
            },
        }
        self.branches = {
            "total_count": 1,
            "branch_policies": [
                {
                    "name": core.policy()["workflow_branch"],
                    "type": "branch",
                }
            ],
        }

    def verify(self):
        return registration.validate_environment(self.environment, self.branches)

    def test_single_maintainer_and_exact_branch(self):
        self.assertTrue(self.verify())
        for bypass in [True, False]:
            self.environment["can_admins_bypass"] = bypass
            self.assertTrue(self.verify())

    def test_missing_branch_protection_or_unexpected_reviewer_gate_rejected(self):
        original = copy.deepcopy(self.environment)
        changes = [
            lambda v: v.pop("protection_rules"),
            lambda v: v.update(protection_rules=[{"type": "required_reviewers"}]),
            lambda v: v.update(deployment_branch_policy=None),
            lambda v: v.update(name="production"),
        ]
        for index, mutate in enumerate(changes):
            self.environment = copy.deepcopy(original)
            mutate(self.environment)
            with self.subTest(case=index), self.assertRaises(core.Rejected):
                self.verify()

    def test_main_tags_wildcards_pull_refs_and_extra_policy_rejected(self):
        for name, kind in [
            ("main", "branch"),
            ("*", "branch"),
            ("refs/pull/*/merge", "branch"),
            (core.policy()["workflow_branch"], "tag"),
        ]:
            self.branches["branch_policies"][0] = {"name": name, "type": kind}
            with self.subTest(name=name, kind=kind), self.assertRaises(core.Rejected):
                self.verify()
        self.branches["total_count"] = 2
        with self.assertRaises(core.Rejected):
            self.verify()


if __name__ == "__main__":
    unittest.main()
