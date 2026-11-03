# P6 — Distribution, installation and update validation

Authorized 1 November 2026. Baseline `bfa0b8005a3ddc519354fd7907e9b972fde8126b`;
accepted P5A source remains `1ee2077b283b8e5dfc2162119dd439ed3baeb109`.
Preserve the uncommitted P5C formal acceptance closeout separately.

## Acceptance criteria established before implementation

| Gate | Required evidence |
| --- | --- |
| Dependency readiness | Narrow minimatch remediation; dependency-chain/reachability assessment; clean install, full frontend/browser regression and production build |
| Inventory and licensing | Application, Python, Qt/PySide/native/runtime inventory with exact provenance and coverage limits; notices and owner license decision |
| Publication | Reuse accepted signed generation verification and retained snapshots; provider-neutral dry-run, destination hashes, immutable generations, conditional activation, interruption/concurrency/cache/HTTP negative tests |
| Signing | Executable offline primary/signing-subkey, expiry, backup/restore, revocation and trust ceremony; disposable rehearsal only |
| Clean remote install | Real production ID, trusted descriptor, actual runtime retrieval, installed commit/source/version/ref/permissions on isolated client |
| Native operation | Real sandboxed GUI launch and synthetic functional/recovery/portal checks, shutdown/single-instance/offline checks |
| Real update | Two distinct approved real application builds; A launch/data, B update/launch/data, compatible binary rollback, reinstall preserving data; schema remains 5 |
| Distribution resilience | Wrong/expired/replaced trust, damaged/missing/stale objects, concurrent/interrupted publication/client/update, unavailable endpoint, incompatible schema refusal |
| Release candidate | Consistent source/tooling/CI/artifact/OSTree/key/version/generation/endpoint identities; release notes, hashes, notices, SBOM and operational instructions |
| External acceptance | Separately authorized hosted verification, actual public HTTPS and independent clean client, explicit owner acceptance |

## Execution

1. Inspect accepted storage, backup, packaging and release primitives; preserve baselines.
2. Resolve the development dependency advisory narrowly, characterize reachability.
3. Extend accepted local publication/client tooling and inventory; add focused regressions.
4. Rehearse with disposable keys, local transport and synthetic data. Attempt runtime
   retrieval and native execution without weakening sandbox controls.
5. Run complete relevant suites from a clean candidate checkout. Retain exact results.
6. Deliver one grouped owner decision package and executable native procedure for
   genuinely unavailable capabilities; do not label blocked gates PASS.

No commits, pushes, external workflow execution, main/environment changes, permanent
keys, public endpoints/publication, version/schema changes, or personal data access.
Local HTTP tests do not establish public HTTPS readiness. Binary rollback never
means database rollback. Public redistribution remains blocked by license/trust/
hosting/release authorization. Do not repeat accepted native/Flatpak builds unless
necessary for changed inputs.

## Checkpoint disposition

Available local implementation is verified. Actual runtime download and real
application remote installation pass; sandboxed GUI launch is blocked by the
Codex host namespace restriction. Real B approval/native updates and client fault
cases remain gated. Public HTTPS, licensing, production trust/owner signing and
final source/CI/release approval are unresolved. P6 remains CONDITIONAL.

The expanded runtime scan also retains three unpatched OS/build-specific advisory
matches with a bounded Linux-use applicability assessment. Do not describe source
lock matching as complete product vulnerability clearance.
