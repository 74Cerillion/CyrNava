# P5B GitHub staging registration and approval plan

31 October 2026. **Recommendation only; no external configuration or dispatch authorized.**
P5B native verification is owner-accepted PASS. Overall P5B remains CONDITIONAL.
The owner endorses future R2-compatible hosting and offline production signing;
neither endorsement authorizes permanent credentials, paid hosting or publication.

## Observed repository state

- Public personal repository `74Cerillion/CyrNava`; default branch `main`.
- Integration branch and remote both already point to
  `a9de66384b4b1ae4e5bb47909df1eba7d50468f0` (`P5B Approved`). It contains the
  previously reviewed implementation and native evidence. Its message does not
  override the owner's explicit CONDITIONAL acceptance status.
- The checkout started clean. Preserve this existing commit; do not rewrite,
  amend or duplicate its implementation. The currently authorized local follow-up
  commit records endorsements, review and this architecture plan.
- `p5a-accepted` remains local at `1a28f68c5732ccc1275403060e89ff168a846655`.
- Read-only API: zero environments, only the existing CI workflow registered;
  `.github/workflows/release.yml` exists on integration but returns 404 on `main`.
  Evidence: `evidence/p5b/staging-preparation/github-read-only.json`.

## Default-branch constraint and options

GitHub requires a `workflow_dispatch` workflow on the default branch. Once
registered, the operator can choose another branch with the UI or CLI `--ref` /
REST `ref`. Those parameters select execution source; they do not remove the
default-branch prerequisite. [Manual workflow documentation](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow),
[workflow REST API](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event).

| Approach | Implications | Assessment |
| --- | --- | --- |
| Registration-only workflow file on `main`; full execution on integration | Separate, explicitly approved change to one workflow path on main; no application/integration merge or default-branch change | Preferred if owner permits this narrowly scoped main-file change |
| Temporarily make integration the default branch | No main content merge; changes repository-wide default behavior and must remain coordinated through dispatch/verification/restoration | Fallback only with explicit repository-settings approval |
| Isolated staging repository | Additional repository/trust setup; current repository ID/source/CI allowlists reject it; would need separately reviewed policy/workflow changes | Unnecessary infrastructure for this case |
| Dispatch filename/ID/`--ref` without registration, add push/PR triggers, or rely on stale discovery | Does not satisfy the documented prerequisite or changes the accepted manual trust boundary | Not recommended; no workaround execution authorized |

### Preferred registration-only approach

After separate approval, add **only** `.github/workflows/release.yml` to `main`
through its normal review/protection process. This is not a merge/cherry-pick of
the integration implementation. Use a valid inert registration definition with
`workflow_dispatch`, matching input names/types and staging-only choice, read-only
permissions, and an unconditionally skipped registration job. It must contain no
checkout, release commands, secret references or reusable-workflow delegation.
Do not copy the full executable workflow onto main without its dependencies.

This proposed registration definition is not installed or hosted-verified yet.
Review its exact YAML under a separate main-file authorization before use. GitHub
then selects the full workflow at the explicitly dispatched integration ref; that
version contains the real eligibility and protected staging jobs. Selecting main
must perform no signing; the integration preflight independently rejects any ref
other than `refs/heads/desktop/p2-production-integration`.

Record both the main registration commit and immutable integration tooling SHA.
Before dispatch, compare the branch tip to the approved SHA; after creation,
verify the run's `head_sha`/ref and workflow definition match. Reject a mismatch,
do not approve that run, and do not automatically dispatch another. The current
manual ref is branch-based while checkout uses `github.sha`; this run-SHA review
is needed to avoid silently accepting branch movement between approval and dispatch.

This preserves default branch and application history. It still changes a file on
main, which **is not authorized now**. If the owner disallows any main-file change,
retain the block and consider the separately authorized fallback instead.

### Default-branch-switch fallback

Temporarily selecting integration as default would satisfy workflow presence
without merging main. It also changes the default target/source for repository UI,
new pull requests and default-branch-dependent automation/protection. Review branch
rules, repository consumers and outstanding PRs first; do not assume rules referring
to the default branch remain equivalent. Record original settings and a restoration
plan; neither switch is authorized now.

All execution still uses the exact integration branch and protected environment.
Do not rely on a workflow remaining runnable after restoring main while its file
is absent there. This is broader operational change than an inert registration
file, so it is not the first choice. Changing default branch is not deployment
approval and never substitutes for an independent reviewer.

## Required staging environment

After separate owner authorization, configure `p5b-staging` with:

1. Required reviewers: nominate a trusted independent person/team. GitHub permits
   up to six entries but requires only one approval, not approval from all entries.
2. Enable **Prevent self-review**. The initiating actor cannot approve their own
   deployment. Prefer owner initiation plus a separate trusted reviewer. Another
   trusted initiator and owner reviewer also preserves two-person separation, but
   requires separately approved access. A sole person acting through another token
   is not independent approval.
3. Disable **Allow administrators to bypass configured protection rules**; API
   must report `can_admins_bypass: false`. If unsupported or unverifiable, remain
   blocked; never silently accept an omitted field or weaker configuration.
4. Choose **Selected branches and tags**. Create exactly one policy of type
   `branch`, name `desktop/p2-production-integration`, without wildcards. No tag,
   main, pull-ref or additional branch policy. Do not choose “Protected branches
   only”: GitHub can allow all branches if no branch protections exist.
5. Add **no production secrets**. Disposable keys are generated only after the
   protected job starts. Workflow token permissions remain `contents: read` and
   `actions: read`; no release/network-publication write credentials are needed.

GitHub documents these controls for public repositories on current plans, but
actual account/UI/API behavior must be verified. Required reviewers need at least
read access; available personal-repository collaborator roles must be checked
before inviting anyone. No invite, permission change or environment creation is
authorized by this plan. [Environment protection documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments),
[environment API](https://docs.github.com/en/rest/deployments/environments).

Repository administrators can still edit rules/workflow source; disabling deployment
bypass is not a guarantee against a malicious administrator. Keep source/settings
review, audit records and least privilege. No production key is exposed even in
this disposable-staging model.

## Verification sequence requiring later authorization

- Obtain authorization for the pending integration documentation push; observe
  its normal verification-only CI without dispatching or rerunning anything.
- Approve one registration strategy, its exact changes and independent reviewer.
  Configure environment only after its own approval. Read back actual settings.
  `github.py environment_eligible()` requires reviewer/non-self-review/no-bypass and
  exactly the single branch policy; current mocks are not hosted proof.
- Authorize one manual staging execution. Keep the existing full application SHA
  `1ee2077b283b8e5dfc2162119dd439ed3baeb109`, run 41181510439, version 0.1.0,
  staging channel and reviewed authorization reference. The tooling commit is the
  separately approved integration tip, not that older application source.
- Verify the unprivileged eligibility job passes live CI/source/artifact and
  environment checks, then the staging job actually waits for independent approval.
  Preserve initiating/reviewing actors and the reviewed run-SHA/ref; no bypass.
- The nominated reviewer independently reviews and approves the authorized run.
  The future run authorization covers execution through this gate; it does not
  replace the reviewer's decision. This document grants neither authorization.
- Require native signing/negative checks, descriptor remote validation, interruption
  protection, key cleanup, live artifact digest/provenance and safe diagnostic upload
  to pass. Record run/attempt, immutable tooling SHA, workflow hash, approved source,
  public fingerprint, result/eligibility hashes and final job conclusions. Diagnostic
  artifacts contain only the two safe JSON records, no key homes or package trees.
- If GitHub cannot enforce any required protection, document the specific limitation
  and stop for a separately approved design; do not remove protection or mark PASS.
  No automatic retry/rerun is authorized on failure.

P5B remains CONDITIONAL until protected hosted verification and formal owner
acceptance. Permanent key creation, public R2 hosting, GitHub Releases and real
update/install deployment remain separately gated; P5C/P6 have not begun.
