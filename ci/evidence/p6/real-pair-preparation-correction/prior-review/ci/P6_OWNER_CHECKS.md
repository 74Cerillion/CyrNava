# P6 owner acceptance checklist

Unchecked items are unexecuted or unresolved, never implied PASS.

- [x] P0–P5C formally accepted; P6 local implementation authorized.
- [x] Local dependency remediation and full local regression evidence produced.
- [ ] Owner reviews that correction and evidence.
- [ ] Shipped inventory, advisory triage and third-party obligations reviewed.
- [ ] Original code/logo license and attribution resolution approved.
- [ ] Production trust anchor, offline ceremony and rotation/recovery approved.
- [ ] Two exact real application build identities approved for native A/B exercise.
- [x] Local isolated real remote install retrieves runtimes and verifies identity.
- [ ] Owner-machine GUI/native operation and independent client verification.
- [ ] Sandboxed native GUI, synthetic persistence, portals, backup/recovery pass.
- [ ] Real A/B update, rollback and reinstall preservation pass.
- [ ] Failure and publication/cache/retention checks pass.
- [ ] Hosting/provider/domain/cost and publication privileges separately approved.
- [ ] Authorized public HTTPS and independent clean-client checks pass.
- [ ] Release-candidate identities, notes, SBOM, notices and runbook reviewed.
- [ ] Commit/push/hosted P6 execution separately authorized and verified.
- [ ] Public tag/release/publication separately authorized.
- [ ] Formal P6 acceptance.

## Grouped next decisions

1. Review local P6 changes and the preserved P5C closeout; separately authorize any
   desired commit/push. Exact groups are in `ci/evidence/p6/proposed-files.json`.
   No commit, push or workflow dispatch is authorized by this checklist.
2. Approve the exact already-built B in `real-B-approval-proposal.json` for a
   disposable real-update exercise, or select a future final CI build instead.
   A is the pinned accepted P5A artifact. Both use 0.1.0/schema 5; no public version
   change is proposed. The false approval field intentionally blocks preparation.
3. On a capable Ubuntu Wayland host execute the runbook's pair/native procedure
   after B approval. Provide only prepared/result/phase JSONs, not raw profiles,
   keys, screenshots or repository/package archives as public evidence. Native
   real-client fault cases and ordinary launcher/offline/logout observations
   remain separate required checks; the scripted happy path is not full P6 PASS.
4. Select original-code license/holder and approve logo rights; resolve upstream
   attribution and corresponding-source obligations with an appropriate review.
5. Approve the offline identity/expiry/custody/backup plan before permanent keys;
   approve provider/domain/budget/conditional gateway before hosting. These are
   decisions for review, not requests to create keys or deploy now.
6. Separately authorize final hosted/public HTTPS and independent-client checks,
   then formal acceptance and any tag/release/publication.

Original P5A artifact expiry: 7 November 2026, 07:53:28 UTC. Keep verified local
replay separate from live eligibility. Never silently replace an expired input.
