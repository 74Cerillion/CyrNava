# Qt 6.11.3 feasibility — binary-first checkpoint

The Qt/Chromium source-build route described below is PAUSED under the narrowed
v0.1 scope. This directory remains planning metadata, not a built candidate.
Bounded binary evaluation on 2 November found exact published upstream refs, but
object requests returned HTTP 403 and the current process cannot create namespaces.
No binary import/renderer/build success is inferred. Full current results are in
[the P6 report](../../../../ci/P6_REPORT.md) and
[the owner checklist](../../../../ci/P6_OWNER_CHECKS.md).

A separate isolated metadata cache is at ci-output/p6-binary-evaluation/; accepted
production locks, application artifacts and user installations are unchanged.
No new manifest overrides the accepted lock. New remote commits are only proposed
candidate inputs until actual versions/providers/maintenance are verified.

## Historical source-build proposal — do not execute


2 November 2026. **NO APPLICATION CANDIDATE BUILT. P6 CONDITIONAL.**

This directory contains planning metadata only. It is not an executable Flatpak
manifest, a complete dependency lock, a build recipe ready to run, or a production
replacement. The owner explicitly required stopping before expensive downloads or
builds if available capacity is insufficient. That condition is met.

Measured snapshot: root/repository disk **3.50 GiB free**; total RAM **14.91 GiB**;
available RAM **3.16 GiB**; existing 4 GiB swap has **12,288 bytes free**. `/tmp`
has about 3.41 GiB free and `/dev/shm` reports 7.46 GiB, but both are tmpfs and
compete for the same RAM/swap. Repository and /var/tmp share one disk. No other
block filesystem was observed in the permitted mount inventory. No cgroup capacity
was inferred where its conventional limit files were unavailable.

`resource-budget.json` records a conservative **79–137 GiB** planning envelope:
2–4 downloads, 10–20 unpacked source, 35–70 objects/link temporaries, 8–15 isolated
SDK/toolchain/cache, 4–8 staged install/audit/artifacts, and 20 GiB headroom. These
are engineering estimates, not measurements of a completed build or an upstream
minimum. Start only with **150 GiB free persistent space**, then measure actual
consumption. The first run uses **one compile job and one linker job**, including
nested Chromium Ninja. Outer `cmake --parallel` alone does not enforce nested
parallelism. No compiler cache is planned for the first build. Proposed memory
readiness floor: 10 GiB MemAvailable, without counting exhausted swap; this does not
guarantee the unknown link peak. Stop if measured pressure breaches safe headroom.

For context, Qt's [source-build guidance](https://wiki.qt.io/QtPDF_Build_Instructions)
reports about 7.1 GB for an initialized QtWebEngine repository. That is not a
measurement of this candidate's tar extraction. Only a HEAD request was made for
the pinned 6.11.3 WebEngine archive: Content-Length **580,447,120 bytes**. No archive
body was downloaded. Its unpacked size and build peak remain unmeasured.

## Exact source planning and renderer integration

`source-identities.json` records the six official Qt **6.11.3** source archive URLs
and publisher SHA-256 sidecar values. They are expected payload hashes; no archive
has been downloaded/hash-verified. QtBase's tag resolves to
`138f955f0b5e50e4a6c2ee1e78a2279db52ae9e3`; QtWebEngine to
`6de08a0e135c48890ba49f394d969ed5964c1cc5`; PySide/shiboken to pyside-setup
`c76f06aa6ca36abbccdf211c6ea24c34d71ee43f`. Git tag objects and metadata hashes are
recorded separately from source archive hashes. No different version was selected.

The exact maintained WebEngine BaseApp recipe revision
`1f4a783f05d97ecb7a887096c2cd933406c727f8` itself targets **6.11.3**. Its SHA-256 is
`6b6663fd9d8ee02e5531cd71a8ca45d26776733920722d8e06f55efd5c5da2f7`.
The pinned PySide BaseApp recipe likewise targets 6.11.3. The previous assessment
incorrectly labeled both recipes 6.11.2; raw-source readback establishes 6.11.3 and
the old wording remains archived. This corrects a description, not accepted payload
versions: R12's installed binding was actually 6.11.2 and WebEngine 6.11.1.

All ten patches referenced by that WebEngine recipe have individual hashes and
application-directory options in `source-identities.json`. The Flatpak sandbox
patch SHA-256 remains
`b086829daf0404b3ed89fb5b135aa0015fe4df00accff75a3d8b4b7ae23dcff3`.
Their use by a same-version upstream recipe improves the basis for a future
candidate, but does not prove they apply to a new source tree, build against an
app-owned Qt, or securely render here. Those checks remain NOT EXECUTED. Do not
copy the old helper or replace this integration with an ad hoc sandbox.

`build-plan.json` identifies the intended minimal source/binding set, supporting
Qt modules, provider split, helper paths and future regression gates. The eventual
SDK commit, libclang/build dependencies and complete configure-selected closure
remain unverified; therefore these records deliberately do not masquerade as a
complete executable lock. Build tests/examples/debug payloads are unnecessary,
but no accepted application feature or security assertion may be disabled.

Keep the existing application helper contract: `/app/bin/QtWebEngineProcess`
resolves to `/app/lib/libexec/QtWebEngineProcess`. Use an app-owned Qt layout and
origin-relative loading compatible with that contract; do not relax application
configuration or use unexplained loader overrides. Runtime supplies Python 3.13
and compatible non-Qt OS/graphics dependencies. All loaded Qt libraries/plugins
must resolve to the coherent application set. Actual providers are NOT OBSERVED
because no candidate has been built or launched.

## Results and preservation

| Gate | Actual state |
| --- | --- |
| Resource measurement and planning | COMPLETE; insufficient resources |
| Exact upstream source/tag/patch metadata | Recorded; source archives not downloaded |
| Executable candidate manifest/complete dependency lock | NOT CREATED |
| Source extraction/configure/build/package audit | NOT EXECUTED |
| Candidate ELF/provider/helper/plugin checks | NOT EXECUTED |
| Candidate-sandbox imports/rendering/security/launcher/cleanup | NOT EXECUTED |
| Ordinary runtime update with fixed app bytes | NOT EXECUTED |
| New candidate regression tests | NOT IMPLEMENTED/EXECUTED; stopped before candidate implementation |
| Candidate artifact size/build peak/duration | UNAVAILABLE; no artifact or build |

Earlier host-venv imports are not candidate-sandbox results. Earlier 382 release/
workflow +229 subtests, 158 backend/packaging and 273 frontend unit passes retain
only their recorded source/input scope; they were not rerun or promoted to a
candidate PASS. This capacity-only checkpoint changes no executable application,
packaging, signing, workflow or driver code. Metadata/preservation validation is
reported separately in the evidence directory. All artifact and native assertions
remain mandatory for a later candidate.

Accepted A/B artifacts/locks/signing, r2 preparation and R9/R11/R12 evidence are
preserved. No retained cache/profile was removed to obtain space. No normal
Flatpak installation, runtime, remote or override changed. No GUI, GitHub execution,
commit/push, signing credential, source archive download, build or publication.

Source/patch/notices provenance and maintainer responsibility must be reviewed
for every library actually bundled. App-owned Qt/WebEngine moves security updates,
Qt/Chromium and third-party corresponding-source/notices/licensing work into the
candidate. Recorded patch hashes do not establish redistribution clearance.
Original code/logo and prior licensing blockers remain open. No new binary notices
inventory or measured artifact size is claimed before a build exists.

## Concrete alternative and next owner decision

**Current recommendation: NOT VIABLE within the measured local resource envelope.**
The architecture remains unproven rather than rejected on ABI or renderer grounds.

Provide an **existing**, persistent Linux build volume (for example a mounted SSD)
with at least **150 GiB free**, dedicated disposable output beneath an owner-chosen
path, and sufficient idle memory. Do not repartition, delete retained work, change
swap, or buy/provision infrastructure for this plan. On the 16 GB laptop, remeasure
after other work is idle; use the proposed 10 GiB available-RAM floor and single-job
build, then monitor actual peaks. If that memory cannot be made available without
disrupting work, use an existing Linux development machine with 32 GiB RAM and the
same disk budget instead; execution there requires an explicit scope/path decision.
No SSH, remote access or external build has been initiated.

Once a suitable path is authorized: remeasure, pin the exact supported SDK/Python
and remaining build dependencies, create the separate manifest/build wrapper,
verify downloads, test patch application, configure/build only the required closure,
measure resources, audit full payload/provider paths and run candidate regressions.
Then attempt permitted isolated imports/rendering/launcher/process-security checks.
Do not automatically extend beyond the disk/memory envelope or retry restrictions.

Only after an actual candidate exists, prepare exact separately approved owner-host
commands for one fresh isolated-client launch/rendering/security check and a normal
runtime update while keeping app bytes fixed. Require distinct observed runtime
commits; an unchanged runtime is NOT an update PASS. No historical restoration,
R12/A-B repeat or personal workspace. There is **no native execution command** at
this checkpoint because there is no application candidate to execute.
