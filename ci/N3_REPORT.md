# N3 — Data-safe manual updater and uninstaller

3 November 2026. **N3 VERIFIED PASS / RECOMMENDED FOR OWNER ACCEPTANCE.**
The owner completed the focused native GUI/reinstall verification; 29 independent
evidence/identity/preservation checks PASS. Formal N3 owner acceptance is pending.
N2 is formally ACCEPTED / COMPLETE. The owner's acceptance and N3-only authorization
are recorded in `ci/evidence/n2/formal-owner-acceptance.json`. N4 is not authorized.
The active target remains native Ubuntu 26.04 x86_64 / GNOME Wayland via versioned
GitHub Releases archives. Flatpak remains paused historical/fallback.

## Independent native acceptance review

Actual owner attempt: `ci-output/native-n3-owner-1/result.json`, **PASS / complete**.
Result SHA-256:
`f933f6f48449106860c87b33f22ac2b192ed11cad7bb041e34901df42a295bf7`.
Sanitized copies, original-record hashes, criterion checks and evidence limits:
[native review](evidence/n3/native-review-2026-11-03/review.json).
Review SHA-256:
`b83b0e6174ec5ecd0eb7516093d71cd9b15f38f49fbbf18666a5643972f0eb17`.
The original load, bootstrap, local and native records remain unchanged.

| N3 criterion | Actual evidence and conclusion |
| --- | --- |
| Distinct native builds and manual update | Retained local transactions verify N2 n2.3 → N3 n3.1 → corrected n3.2; maintenance source and archive identities differ, application/data/Qt consumers remain identical |
| Actual imported-workspace GUI | Native GNOME menu launch PASS: authenticated backend, private Qt providers, named enforce profile, renderer protections and owned-process cleanup |
| Actual post-reinstall GUI | Second GNOME menu launch independently PASS for the same live checks; no prior phase substituted |
| Data and recovery | Three identical read-only domain audits: two schema-5 workspaces, each with one folder/note/image; saved database/assets/selection/origin bytes independently match retained pre-GUI inventory |
| Appearance contract | Owner explicitly confirmed imported System → selected Dark → Dark after reinstall; backup exclusion of browser preferences remains unchanged |
| Uninstall/reinstall | Actual completed journals have matching full-profile inventories; retained uninstall checkpoint matches; activation restored, saved data preserved, no incomplete transaction |
| Compatible rollback, schema refusal and interruption guards | Retained actual compatible binary rollback/return, newer-schema refusal and unchanged-source regression evidence retain their documented scopes |
| Desktop and cleanup | Exact installed Desktop Entry unchanged; temporary menu entry removed; candidate GUI absent after completion; no external-child exit code invented |
| Identity and security preservation | Archive/manifest/receipt, all 96 payload and 4,414 dependency-provider files, source/test pins, accepted N2 artifact/profile/policy and integration branch/HEAD verified unchanged |

The owner loaded only the reviewed N3 profile, now independently confirmed in
**enforce** mode. Saved load and non-GUI bootstrap PASS and match their original
hashes. The accepted N2 enforce policy and both namespace controls remain enabled.
The bootstrap itself is not renderer evidence; the two actual GUI phases supply it.

The live observer records cumulative successful observations for each launch.
Its unchanged implementation requires matching helper/renderer role, stable process
identity, NoNewPrivs, seccomp and user/PID/network namespace separation on the same
renderer. Both final records report no missing checks. Closing snapshots contain
one executable ENOENT read; the after-reinstall snapshot has no remaining renderer
role/details. Its cumulative PASS is preserved as recorded, not expanded into
unrecorded numeric process evidence. GNOME child exit codes are unavailable;
actual process disappearance/owned-descendant cleanup passed. Appearance/icon/
grouping are explicit owner observations, not inferred from a preference-file hash.

Existing 175 native and 92 backend test results apply to unchanged source. They
were reviewed, not rerun or substituted for native execution. No application,
installer, dependency, test or host-policy code changed in this review. No GUI,
build, signing, Git write, CI, publication or N4 operation was performed by the
reviewer. N1/N2 acceptance, P1–P5 and R11/R12 records retain their original scopes.

No required N3 evidence remains missing within the support boundary below.
The remaining decision is formal owner acceptance, not another native rehearsal.
N4 requires separate authorization; production authenticity, redistribution
obligations and public release are not certified by this disposable candidate.

## Implementation and support boundary

The existing `desktop/install_engine.py` owns install, update, recovery, rollback,
uninstall and explicit reinstall dispatch. Its new stdlib-only
`desktop/native_operations.py` reuses the accepted verifier, archive extractor,
provider checks, per-user paths, installation lock and durable file operations.
`desktop/native_profile_check.py` invokes the unchanged packaged domain auditors
under the actual installed CPython 3.14 environment. Small update/uninstall shell
wrappers and the standalone installer export use this same engine.

- Authenticate the supplied full manifest/archive before staging; production mode
  retains the existing trusted primary fingerprint and rejects key substitution,
  missing/expired/revoked signatures, changed hashes and candidate mode.
- Refuse active GUI/backend locks. No process is killed to perform maintenance.
- Validate every existing workspace read-only, including completed recovery metadata.
  Support schema 5 without migration; newer/older/incompatible schemas are refused.
- Check destination capacity; create and hash-verify a stopped whole-profile
  checkpoint, including Qt storage/preferences/drafts and the workspace/origin files.
- Install local hash-locked wheels in the new version's final location; perform
  provider/ELF and real isolated backend/security/data checks before activation.
- Change the active selection durably; retain previous release and the transaction.
  Interrupted activation requires explicit recovery, with unchanged-data and
  changed-target checks. No automatic data or binary rollback occurs.
- Explicit rollback selects only code with identical application/data consumers,
  storage/bootstrap and dependency inputs. It does not reverse database changes.
  Same-artifact reinstall is distinct from a version update and does not repair
  modified code silently. Skipped-version ordering is tested within this boundary.
- Uninstall removes only exact managed launch/menu activation files. **It deliberately
  retains version payloads, data, checkpoints and logs** for explicit reinstall;
  it is not a disk-cleanup/purge command. Reinstall requires explicit data reuse and
  unchanged retained data/code. Host AppArmor policy is never loaded/removed by it.

This first boundary keeps the accepted application/backend/frontend/storage bytes
and matched Qt/PySide/Shiboken/WebEngine 6.11.3 closure unchanged. Real source changes
are in the launcher/maintenance implementation, not a metadata-only B fixture.
Changes to application/data consumers or the dependency stack require a reviewed
compatibility extension. Arbitrary future versions and general schema evolution
are not certified. Production Profile, backup format, permissions and security
logic are unchanged.

## Actual candidate and installed identity

| Item | Identity |
| --- | --- |
| Candidate | `ci-output/native-n3-candidate-3/CyrNava-0.1.0-n3.2-ubuntu-x86_64.zip` |
| Archive SHA-256 | `f87fc9f81e8a633397af66a11211bd7a9cd35c3a77bc061d58ba2170ec86f947` |
| Archive size | 271,609,291 bytes |
| Manifest SHA-256 | `6f18cbd08dbccf4c578b0412805856d143f38f5c1d927ae2e753f85bbcbab096` |
| Installed client | `ci-output/native-n3-client-1/` |
| Selected release | `0.1.0-n3.2-f87fc9f81e8a6333` |
| Installed receipt SHA-256 | `b4572e42f58d0007a48c3d7ee78ba9b3e8b286c2580933c9b89eb6330b68f423` |
| Source HEAD | `bfa0b8005a3ddc519354fd7907e9b972fde8126b`; uncommitted N3 inputs are individually hashed in the manifest |
| Inherited application patch | `a5e88d7f4102aed8f44f2f54b7991638dee8e5f7df605dbbf4c941a3bde8c43c` |
| Assembly source SHA-256 | `2a2e92ea89305d583a753be05fbed7910d4a0c7be3133f045295ceb12b04d98f` |

The candidate is unsigned and restricted to disposable checksum-pinned testing.
No production signing identity, release trust or public distribution is claimed.
The internal development menu/window retain the N2 candidate name because the
accepted application bytes were reused; this is not a public branding change.

## Verification actually executed

| Gate | Result and scope |
| --- | --- |
| Clean local dependency acquisition | Fresh isolated A install from accepted N2 archive; no-index/hash-required/binary-only wheel install and all providers PASS |
| Actual upgrades | N2 `0.1.0-n2.3` → N3 `0.1.0-n3.1` → corrected `0.1.0-n3.2`; independent full archives and installed environments, no Qt/frontend rebuild |
| Stopped source/data validation | Both retained schema-5 workspaces valid; one folder/note/image in each; all 4,414 installed provider hashes PASS |
| Full-profile preservation | Actual update, same-artifact reinstall, compatible rollback/return, uninstall and explicit reinstall retain every stopped profile byte |
| Backup/import | Unchanged actual packaged `pack`/`migrate` APIs PASS; content fingerprint `8fc8a3883f5403526fe9300c7ea8569cce0392f07b802da273a209991b9342b3`; original workspace/Qt profile retained; port unchanged |
| Imported preferences | Backup excludes browser preferences/drafts; separate imported Qt profile. Actual System → chosen Dark → post-reinstall Dark confirmed in owner attempt 1 |
| Newer database | Final-package helper rejects an isolated schema-6 copy without changing its database bytes or the active selection |
| Regressions | **175 native installer/transaction/auditor/handoff tests PASS, zero skips; 92 backend backup/migration/native-security/navigation/dialog tests PASS** |
| Static checks | Ruff, formatting, shell syntax, Desktop Entry validation PASS |
| Security inheritance | Signature verification/status, extraction, host checks, path/file validation, installed verification, launch, offline environment setup and installation locking are AST-identical to accepted N2 source |
| Native GUI/new renderer context | **Owner attempt 1 PASS in both phases**, independently reviewed. The agent did not rerun it; fixtures/headless imports are not promoted to renderer PASS |

The 92 backend regressions use the existing development CPython 3.12 environment;
actual package provider/backend/domain transactions separately use fresh installed
CPython 3.14 environments. Two existing test warnings concern TestClient deprecation
and an intentionally duplicated malformed ZIP entry. No dependency was upgraded.
Native draft recovery was not newly simulated; exact stopped Qt/draft-storage bytes
are preserved, and unchanged domain/earlier evidence retain their original scope.

## Failures found and preserved

The first real update attempt failed **before any transaction/activation** because
the new isolated auditor omitted `application/backend` from its module search path:
`ModuleNotFoundError: No module named 'app'`. Old A remained selected and its data
unchanged. The explicit packaged-backend root and independent subprocess regression
correct this confirmed defect. Candidate 1 and its private failure log remain.

Review of actual portable recovery also identified its intentionally retained
`migration-<uuid>.json` and `pre-migration-<uuid>.cyrnava` files. The final auditor
recognizes completed recovery metadata, preserves it, and refuses unfinished or
unexpected generations. The successful n3.1 archive is retained separately; the
corrected n3.2 source/package identity is not substituted into that earlier result.

Local records are under `ci-output/native-n3-local-1/`; compact sanitized evidence
is under `ci/evidence/n3/local-2026-11-03/`. Accepted N1/N2 artifacts, the original
47-file N2 synthetic profile, historical attempts and unrelated/uncommitted source
were independently verified unchanged. P1–P5 and R11/R12 are not reopened.

## Historical local preparation and resource measurements

This section records the state before the completed owner execution reviewed above.
Its proposed commands and ABSENT policy state are historical, not instructions to
repeat the load or GUI check. Original preparation evidence is preserved.

Measured allocation for the three retained candidate outputs, three-version
disposable client and local evidence is about **3.85 GB (3.59 GiB)**, within the
revised **4 GiB** local cap. Filesystem availability fell from 12,971,311,104 to
about 9,115,066,368 bytes; other filesystem activity means this is not a promised
reclaim amount. The 5 GiB free-space floor remains satisfied. No download,
Qt/Chromium build, native GUI or deletion of accepted output occurred. Only the
small unchanged C bootstrap was compiled, with its existing 128 MiB/60-second
limits. Peak RSS/total assembly wall time were not independently measured.

The new disposable client has a different exact AppArmor attachment from accepted
N2. Policy preparation/parser PASS; host profile remains **ABSENT**, no host setting
changed. Exact proposal:
`cyrnava-native-u1000-7180461d3e5719da3d409effaeb8b936`, policy SHA-256
`2e8eba098eafda2302478f1b4be7ce4320e7c8250acfa7733a30d3231ba0d1bd`.
It uses the already-reviewed enforce/ordinary-user model, exact launcher path and
matching interpreter/helper inheritance. Renderer sandbox assertions are unchanged.

The owner decision at this preparation checkpoint was approval to load **this exact
new profile** and perform the two-launch imported-workspace/reinstall check. Proposed
commands and limits: [N3_OWNER_CHECKS.md](N3_OWNER_CHECKS.md). No production user data
or normal installation is used. Formal N3 acceptance follows actual native evidence.
N4, signing, commits/pushes, CI execution and publication remain unauthorized.
