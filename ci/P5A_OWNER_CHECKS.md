# P5A owner checks — GitHub-hosted verification

Status: **CONDITIONAL — GITHUB-HOSTED VERIFICATION REQUIRED**.

The local candidate is on `desktop/p2-production-integration` and has not been
committed or pushed by the agent. A push is an external action requiring explicit
owner authorization under the P5A instructions. Publishing an Actions artifact is
included in the proposed verification; creating a public release is not.

## One owner decision

Review `.github/workflows/ci.yml`, the helpers in `ci/`, the two bounded P4 build/
audit changes and import-order-only test cleanup. Then either:

- Authorize a P5A commit and push to the existing integration branch. Its push
  trigger starts CI automatically; no manual dispatch is necessary.
- Commit/push the reviewed changes yourself, then provide the Actions run URL.

No merge to main, tag, signing, release or repository setting change is required.
Do not enable a paid plan or new production secret. This is a public repository,
so workflow logs/artifacts must contain only source/build data and synthetic tests.

If Actions is disabled, enable GitHub Actions only for this repository and allow
its referenced official `actions/*` actions. Keep default workflow token
permissions read-only; no write permission or signing credential is needed.
If fork PR execution awaits approval, review the PR and approve that run instead
of switching to a privileged PR trigger. These are contingency instructions,
not a claim that either condition currently applies.

## Hosted acceptance evidence

Record each item from the actual run:

- Run URL/ID and attempt, source SHA and runner image.
- Workflow validation, backend/security and frontend/browser jobs PASS.
- Production Flatpak build and exported-bundle audit PASS.
- `CI required` PASS; no required job skipped or cancelled.
- Artifact upload successful; the production bundle/provenance/checksum are present.
- Download and independently verify the `.flatpak` against `SHA256SUMS` and
  provenance; source SHA and app ID match the run.
- Record durations, artifact bytes, npm cache hit/miss and overall conclusion.
- Preserve relevant failure logs before correcting/retrying a failed job.

For a downloaded artifact directory:

```bash
sha256sum --check SHA256SUMS
```

Downloading/inspecting the artifact does not require running or installing it.
Real native launcher/portal coverage remains distinct and P4's recorded limits
remain in force. Do not migrate personal data or declare a production release.

The deliberate local failure regression runs a subprocess exiting 17, verifies
nonzero orchestration, prevents its later marker/upload step, and tests the exact
final gate shell with failure/skipped/cancelled statuses. It never commits a
broken integration test. Hosted negative execution remains unclaimed until an
approved run provides evidence.

After hosted evidence is reconciled, review `P5A_REPORT.md` and explicitly accept
P5A. P5B/P5C remain unauthorized.
