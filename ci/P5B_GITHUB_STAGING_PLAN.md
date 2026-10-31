# P5B hosted staging preparation — owner-controlled single-maintainer model

31 October 2026. **One integration commit/push is now owner-authorized; main changes,
environment configuration and workflow dispatch remain separately gated.** The owner's later explicit
single-maintainer decision supersedes the earlier independent-reviewer design.
Historical evidence and earlier design records remain preserved in Git history
and `evidence/p5b/staging-preparation/`; they are not the current requirements.

## Verified starting point

- Required CI [41205351385](https://github.com/74Cerillion/CyrNava/actions/runs/41205351385)
  at `7aaefd0f60a735637ee603ac380587a25b73f6cb`: all five required jobs PASS,
  31 workflow contracts, 611 backend tests + 83 subtests, 273 frontend units,
  21 browser tests, production Flatpak/exported audit/upload/final gate.
- Public personal repository `74Cerillion/CyrNava`, ID 1427661036; default `main`.
  Main tip: **`cbf7cccc686080b2b4b07274a9f5a23fec52999f`**. No existing release
  workflow file on main, zero environments, only CI registered. These are actual
  readbacks, not configuration changes. Main tip must be reread before approval/use.
- Integration remains `desktop/p2-production-integration`, HEAD/remote `7aaefd0`.
  Local `p5a-accepted` remains at `1a28f68`; no main checkout/merge or tag push.
- The new single-maintainer policy changes are local and **not** covered by that
  hosted CI run. A separately approved integration commit/push and successful CI
  must precede executing the revised hosted staging workflow.

## Authorization and tradeoff

Manual **owner** authorization and owner-initiated `workflow_dispatch` replace
independent GitHub deployment approval. No second person, required reviewers or
self-review prevention is required or claimed. This concentrates staging authority
in the owner's account; compromise or mistaken use of that account no longer has
a second-person veto. An authorization-reference string is provenance, not a secret
or proof of an independent approval. No permanent signing/publication authority is
available to this workflow. Future production signing remains owner-controlled and
offline, with a separately approved primary/subkey/backup ceremony.

The existing release implementation remains authoritative. Read-only contents/actions,
immutable action pins, approved P5A source/artifact/lock hashes, exported-payload audit,
signatures, negative tests and interrupted local publication protections remain.
Preflight and the live stage independently check owner actor and triggering actor,
manual event, exact repository/ref/workflow path, first attempt, workflow SHA and
checked-out SHA equality; the exact reviewed workflow contract is also checked.
Wrong refs, other actors/forks, changed workflows, wrong artifact/source and missing
staging authorization fail closed. Reruns are rejected; any future rerun needs new review.

There is no post-dispatch human deployment gate in this model: once the owner
explicitly authorizes and initiates the run, eligible staging starts automatically.
Review the immutable tooling tip and settings **before** dispatch. A branch ref can
move between read and dispatch; verify resulting run SHA immediately afterward.
If it differs, do not claim owner-approved execution or PASS. Manual authorization
is operational; it does not mathematically bind a chat approval to GitHub's API.

## A — Exact inert registration-only main change (separate authorization)

Proposed local source: `ci/release/registration-only.yml`.
Only proposed destination on main: **`.github/workflows/release.yml`**.
Add that one file against the main tip above. No application files or integration
commits are merged, and main stays the default branch.

```yaml
name: CyrNava P5B staging rehearsal

on:
  workflow_dispatch:
    inputs:
      source_commit:
        description: Full owner-approved source commit SHA
        required: true
        type: string
      ci_run_id:
        description: Successful approved P5A CI run
        required: true
        type: string
      version:
        description: Approved existing application version
        required: true
        type: string
      channel:
        description: Production publication is disabled
        required: true
        type: choice
        options: [staging]
      authorization_ref:
        description: Reviewed disposable-staging authorization reference
        required: true
        type: string

permissions:
  contents: read

jobs:
  registration:
    if: ${{ false }}
    runs-on: ubuntu-24.04
    timeout-minutes: 1
    steps:
      - name: Inert registration marker
        run: ':'
```

The literal false job condition allocates no runner. A valid job needs a step,
so its only marker is the shell builtin `:`. Even if that condition were removed,
that marker has no checkout, signing, release or network action. There are no
secret references, environment, reusable workflows or deployment capabilities.
Permissions are read-only; inputs match the executable integration definition
exactly, including staging as the only channel choice. No input is evaluated by
the marker. Static checks enforce the entire small shape and reject extra jobs,
steps, actions, permissions, triggers or changed input schemas.

GitHub requires workflow_dispatch registration on the default branch; execution
uses the workflow at the selected ref. Dispatching main therefore selects this
inert definition, while selecting integration uses the reviewed executable release
workflow. The latter still rejects any ref other than the exact integration branch.
This selection behavior is documented by GitHub; **not yet demonstrated by an actual
hosted staging dispatch**. Registration is not release authorization.
[Manual workflow guide](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow),
[workflow source selection](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows),
[execution identity variables](https://docs.github.com/en/actions/reference/workflows-and-actions/variables).

### Owner terminal procedure — review now, execute only after Authorization A

This uses a disposable detached clone, leaving the integration checkout untouched.
The push is normal fast-forward and fails if main has advanced. If protection or
authentication blocks it, stop and use the repository's approved review process;
do not force-push, disable protection or merge integration. The owner needs contents
write and permission to update workflow files; CLI credentials may need workflow
permission. Never paste credentials into chat.

```bash
(
set -euo pipefail
p5b_source=/home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
p5b_main=cbf7cccc686080b2b4b07274a9f5a23fec52999f
test "$(sha256sum "$p5b_source/ci/release/registration-only.yml" | cut -d' ' -f1)" = 3a8c4ad86f958dc7d437c5ee4e5ad2ac57d8753cc4429252edc0005bf385c7c5
p5b_actual="$(git ls-remote https://github.com/74Cerillion/CyrNava.git refs/heads/main | cut -f1)"
test "$p5b_actual" = "$p5b_main"
p5b_registration_dir="$(mktemp -d "$HOME/.cache/cyrnava-registration.XXXXXX")"
git clone --no-checkout https://github.com/74Cerillion/CyrNava.git "$p5b_registration_dir"
git -C "$p5b_registration_dir" checkout --detach "$p5b_main"
test ! -e "$p5b_registration_dir/.github/workflows/release.yml"
install -D -m 644 "$p5b_source/ci/release/registration-only.yml" "$p5b_registration_dir/.github/workflows/release.yml"
git -C "$p5b_registration_dir" add -- .github/workflows/release.yml
test "$(git -C "$p5b_registration_dir" diff --cached --name-only)" = .github/workflows/release.yml
git -C "$p5b_registration_dir" diff --cached --check
git -C "$p5b_registration_dir" diff --cached
git -C "$p5b_registration_dir" commit -m 'ci: register inert P5B staging workflow on main'
test "$(git -C "$p5b_registration_dir" rev-parse HEAD^)" = "$p5b_main"
test "$(git -C "$p5b_registration_dir" diff-tree --no-commit-id --name-only -r HEAD)" = .github/workflows/release.yml
git -C "$p5b_registration_dir" push origin HEAD:refs/heads/main
git -C "$p5b_registration_dir" rev-parse HEAD
git -C "$p5b_registration_dir" ls-remote origin refs/heads/main
)
```

Before granting A, record the approved proposal SHA-256 from the local validation
record; compare it again immediately before copying. After future registration,
read the main file back at the resulting commit and compare bytes/hash; verify
only that file changed, main parent matches the approved base, and Actions lists
its release workflow ID/path. Do not dispatch main merely to test the stub.

## B — Environment UI configuration (separate authorization)

Owner's settings page:
[Settings → Environments](https://github.com/74Cerillion/CyrNava/settings/environments).
Only the personal repository owner can configure its environments. Public
repositories support these controls on current GitHub plans; actual UI/readback
is authoritative. No paid plan or second collaborator is needed for this model.
[GitHub environment guide](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments).

After explicit B approval:

1. Click **New environment**, enter `p5b-staging`, then **Configure environment**.
2. Leave **Required reviewers** unchecked/empty. No self-review prevention is needed;
   no invitation or access grant is required. Do not add a wait timer or custom approval.
3. Under **Deployment branches and tags**, select **Selected branches and tags**.
4. Add exactly one rule: type **Branch**, name `desktop/p2-production-integration`.
   No wildcards, tags, main or pull-request refs. Do not use “Protected branches only”.
5. Add no secrets or variables carrying credentials: no production keys, signing
   passphrases, publication credentials or permanent endpoints. Existing workflow
   refers only to GitHub's read-only job token, never `secrets.*` or OIDC permissions.
6. Save and revisit the page. Confirm the single rule and empty reviewer/secrets lists.
   The administrator-bypass flag controls approval rules that this model does not use;
   it is not an authorization gate, and either API value is accepted. Exact branch
   restrictions are independently enforced in preflight. No admin bypass protection
   or independent deployment approval is claimed.

Read back actual settings (read-only; `gh` uses the owner's authenticated account).
The Python helper needs the reviewed tooling environment with PyYAML 6.0.3 from
`ci/requirements.lock`; if absent, have Astra validate the JSON using its verified
tooling interpreter rather than installing unpinned dependencies:

```bash
gh api repos/74Cerillion/CyrNava/environments/p5b-staging > environment.json
gh api repos/74Cerillion/CyrNava/environments/p5b-staging/deployment-branch-policies > branches.json
gh api repos/74Cerillion/CyrNava/environments/p5b-staging/secrets --jq '{total_count}'
python3 ci/release/registration_policy.py --environment-record environment.json --branches-record branches.json
```

Expected: correct name, protection_rules contains no required_reviewers rule,
deployment_branch_policy `{protected_branches:false, custom_branch_policies:true}`,
exactly one `branch` entry with the name above, secret count zero. No setting is
assumed applied merely because a write succeeded. The workflow token only needs
contents/actions read; public environment GETs are readable without privileged tokens.
An authenticated settings change requires the owner, not a stronger runner token.
[Environment API](https://docs.github.com/en/rest/deployments/environments),
[deployment-branch API](https://docs.github.com/en/rest/deployments/branch-policies).

If a required control cannot be verified, stop; do not expand branch access or
place production secrets into Actions. Environment JSON alone proves configuration,
not successful hosted enforcement. A production credential must never be made
available to staging merely because no reviewer gate remains.

## C — One hosted staging dispatch (separate authorization, not granted)

Prerequisites: approved revised integration commit synchronized with successful CI;
A complete with exact main-file readback; B complete with actual settings readback;
owner-approved immutable tooling SHA; accepted artifact still available and unexpired.
The latest CI package is **not** substituted for the older policy-pinned P5A artifact.

| Input | Required value |
| --- | --- |
| Execution ref | `desktop/p2-production-integration` |
| Tooling commit | Exact future owner-approved revised integration SHA; not 7aaefd0 after this local policy change |
| source_commit | `1ee2077b283b8e5dfc2162119dd439ed3baeb109` |
| ci_run_id | `41181510439` (attempt 1) |
| version | `0.1.0` |
| channel | `staging` |
| authorization_ref | `P5B-owner-authorized-disposable-staging-only` |
| Accepted artifact | ID `13035607417`, ZIP SHA-256 `73e6d58a91ff2e57ca7b801b120ca61eceb399202349345508b8fbf6ce4eba6b` |

The exact future dispatch, **only after C approval**, is:

```bash
gh workflow run release.yml --repo 74Cerillion/CyrNava \
  --ref desktop/p2-production-integration \
  -f source_commit=1ee2077b283b8e5dfc2162119dd439ed3baeb109 \
  -f ci_run_id=41181510439 \
  -f version=0.1.0 \
  -f channel=staging \
  -f authorization_ref=P5B-owner-authorized-disposable-staging-only
```

Immediately before dispatch, compare integration tip to the separately approved
full tooling SHA, verify the workflow bytes/contract at that SHA, registered workflow
ID/path, current settings and actor account. Do not copy a placeholder SHA into an
executable command. The policy now rejects another initiator and any second attempt.
After dispatch, record run ID, workflow ID and head SHA; independently compare them
to the approved inputs. The owner readback helper can check downloaded records:

```bash
gh api repos/74Cerillion/CyrNava/actions/runs/ACTUAL_RUN_ID > run.json
gh api -H 'Accept: application/vnd.github.raw+json' \
  'repos/74Cerillion/CyrNava/contents/.github/workflows/release.yml?ref=APPROVED_FULL_TOOLING_SHA' > run-workflow.yml
python3 ci/release/registration_policy.py \
  --run-record run.json --run-workflow run-workflow.yml \
  --tooling-commit APPROVED_FULL_TOOLING_SHA --workflow-id ACTUAL_REGISTERED_WORKFLOW_ID
```

Those uppercase values are instructions to fill verified values, not executable
ready-made IDs. The CLI requires all fields together. No staging dispatch has occurred.
Require eligibility, accepted artifact audit, signed OSTree generation, wrong-key/
tamper/missing-object/unexpected-ref rejection, native descriptor and interrupted
publication checks, key cleanup and final PASS/complete. Only safe result.json and
eligibility.json are uploaded. No repository tree, private key or application package
is published by staging. Record hashes and source/tooling identities separately.
No automatic rerun, signing fallback or release publication is permitted on failure.

## Local validation and responsibilities

Final local results: **59 release/registration/signing regressions + 31 CI contracts
PASS**, plus Ruff, actionlint and all three policy checks. Proposal SHA-256:
`3a8c4ad86f958dc7d437c5ee4e5ad2ac57d8753cc4429252edc0005bf385c7c5`. Evidence: `evidence/p5b/staging-final-preparation-2026-10-31/`.
The initial CI-contract check hit the unchanged 5 GiB guard on /tmp; it was rerun
with small disposable fixtures on spacious /dev/shm, without weakening the guard.

`registration_policy.py` validates the inert YAML and optional readbacks, with no
network writes or signing. Registration input/privilege mutations, wrong execution
identities/actors and environment ref-policy changes have synthetic regression tests.
Both executable workflows remain hash-pinned and policy-validated; the release step
name/contract now describe owner dispatch rather than independent approval.

Astra can prepare local changes/tests and perform authorized read-only verification.
The owner must authorize each integration commit/push, A, B and C separately. GitHub
settings and dispatch can later use the owner's authenticated UI/CLI, or a separately
authorized connector operation. No collaborator action is needed. Successful native
rehearsal remains accepted; it is not rerun simply to refresh a record. No P5C/P6.
