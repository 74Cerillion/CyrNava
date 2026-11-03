# Current HTTP stop — do not repeat the build yet

Normal-host candidate-1 passed namespace and identity checks, then failed pull-0
with HTTP 403. The pinned signed commit is available: direct curl gets 200/exact
hash, but libostree-identified requests get 403. The denying rule/operator remains
unconfirmed. No acquisition driver/dependency/security change is justified yet.
Run only `bash p6_http_diagnostic.sh` from the repository for the reviewed three-GET
host comparison. It creates fresh ci-output/p6-http-owner-1, not a candidate or build.
See the current P6_REPORT.md diagnosis. Prior build commands below remain paused.
A later continuation must use the existing --output option with a fresh path;
never overwrite candidate-1. No continuation is issued until acquisition works.

---

# P6 bounded binary candidate — owner-host entry point

2 November 2026. **Recipe implemented; acquisition/build NOT EXECUTED here. No
candidate exists.** Production packaging, locks, auditor and A-only signing policy
remain unchanged. This is the reduced binary route, not adoption of the paused
whole-Qt source-build proposal.

Run from a normal Ubuntu terminal:

```bash
cd /home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
bash p6_binary_candidate.sh
```

Creates exactly one NEW attempt directory:
`ci-output/p6-binary-candidate-1/`, containing isolated `home`, `flatpak`, `data`,
`config`, `cache`, `runtime`, `tmp`, `gnupg-unused`, `source`, `production-build`
and `export-audit`. Refuses an existing attempt or any symlink ancestor. Does not
modify normal user/system Flatpak installations, remotes, overrides or profiles.
No GUI launches, keys, signatures, publication, Git writes or historical rehearsals.
No cleanup is invoked. Logs stay private; never upload the whole attempt.

The sequence is namespace probe → trusted remote/public-key readback → four exact
live-ref comparisons → three signature-verified full binary pulls/deployments →
exact installed-ref readback → fresh frontend build → P4 allowlisted staging →
BaseApp imports/provider check → existing P4 assemble/finish → final runtime
imports/provider check → SDK readelf → unchanged P5A exported-bundle audit → actual
exported notice/dependency inventory. WebEngine is already in the PySide BaseApp;
its payload is not installed a second time. Only the app/frontend is built.

`candidate.lock.json` records the exact owner-approved four commits, upstream key
file hash, source baseline, original packager/manifest/lock/auditor hashes and limits.
Metadata/branch names alone cannot establish actual versions. Actual imports must
show Python 3.13 and PySide/shiboken/Qt/WebEngine 6.11.3. Loaded maps must show runtime
Qt Core and application WebEngine, with no duplicate or wheel-bundled Qt providers.
Check helper/resources/locales, missing ELF dependencies and maintained Flatpak
integration marker. The marker is only a prerequisite, not renderer evidence.
SDK readelf records NEEDED, RPATH/RUNPATH and symbol-version requirements separately.
No LD_LIBRARY_PATH override or sandbox-disable option is introduced.

## Resource boundary

All large files, temporary work, caches and exports use the persistent attempt
volume, never /tmp or /dev/shm. Initial free requirement 9 GiB; added allocation stop
limit 7.5 GiB; free headroom 1.5 GiB; one build job; total operation deadline 60 min.
Subprocess groups are owned by this driver; timeout/interruption stops only those
children. Each operation is identified before starting; ten-second running events
remain visible. Network retries are disabled for OSTree/pip/npm. An error stops
without a second attempt or fallback source/version.

Published installed-size estimates: Platform ~1.1 GB, SDK ~3.2 GB, layered PySide
~995 MB (about 4.93 GiB together). Compressed transfers ~1.97 GB are not added again
as a permanent duplicate source archive. Thin staging, frontend dependencies/cache,
compressed exports and independent audit add roughly 2–3 GiB depending on actual
cleanup and hardlink behavior. **7.5 GiB is a stop limit, not a guarantee this cold
route fits.** Usage is measured before/after commands and while children run. No
quota/mount changes are made; sampling can detect a limit only after a write. If a
limit is reached, stop and preserve the attempt; do not silently expand it or clean
old artifacts. No reuse credit is assumed for other installations. Corresponding
source downloads are not performed: exact recipe/patch/source arrangements remain
part of the redistribution review, not an invented completed source archive.

Result: `result.json`; operations and bounded private-log filenames are recorded.
On namespace/HTTP/GPG/ref/provider/resource failure, result is BLOCKED with the
operation/category. A 403 object endpoint is copied to safe diagnostics only if it
matches the fixed upstream host and hash-path allowlist. Raw arguments/environment
are never copied. Logs may contain private local paths and must remain private.
Do not retry automatically. If a ref moved, compare inputs and obtain a decision.

On success only, bundle:
`production-build/io.github._74Cerillion.CyrNava.flatpak`. Its actual SHA-256 and
OSTree commit will appear in result/provenance; neither exists yet. Recipe hashes,
actual allowlisted staged-source hashes, local source-snapshot identity, dependency
commits, component versions, permission audit and exported-content inventory remain
bound to that distinct unsigned candidate. It is not approved historical B.

## Native and update scope after a candidate exists

Imports do not instantiate a renderer. No GUI command is issued before the bundle
exists and its audit passes. The next owner handoff must bind its actual hash and
installed commit and use a new isolated normal-dependency installation/profile.
Test its NORMAL packaged launcher and desktop entry/icon, actual renderer process
isolation, backend/Host-Origin/shutdown, synthetic rich note/folder/image upload,
offline restart and persistence, one native backup/import, incompatible schema
refusal, then same-package reinstall preserving data and the observed new preference
baseline. Dark must persist in the original profile; import creates fresh browser
preferences. Preserve R9/R11/R12 evidence and do not repeat their full sequence.

The arrangement still uses runtime Qt Core with app bindings/WebEngine. Inspect
private-symbol coupling; do not claim it disappeared because 6.11.3 imports pass.
Support is limited to an actually tested Ubuntu 26.04 x86_64/GNOME Wayland pair.
Before publishing another matched bundle, test its current runtime/provider closure,
renderer, data and normal install. An independent runtime change with fixed app
bytes must be recorded separately; a no-op is NOT an update-compatibility PASS.
Do not restore old runtimes as a fix. A breaking upstream change suspends support
for that combination until a tested coherent package is available. This is a
maintenance responsibility and release risk, not a guarantee about future runtimes.

## Source and CI handoff

The recipe accepts the current bfa0b800 source baseline plus exact local staged
input hashes. This checkpoint allows an unsigned local build. A public release
needs an owner-approved final source commit/CI and a verified mapping of every
packaged executable input to that source. Do not tag bfa0b800 and pretend it contains
uncommitted corrections. No final tag target is selected. If executable inputs
change, repeat affected candidate/provider/export/native checks; documentation-only
edits do not require a rebuild.

Existing CI backend/frontend/browser/workflow contracts remain relevant. The
existing Flatpak job still builds historical P4 locks and cannot certify this new
candidate. Later, propose a small adapter to that SAME job using this separate
candidate recipe/approved source binding and its exact contracts; preserve existing
P4 regression tests and historical locks. No workflow modification/dispatch is made
here. Do not expand the accepted P5B application-source allowlist.
