# N1 — ACCEPTED / COMPLETE

3 November 2026, Korea time. The owner formally accepted N1 and authorized N2
only. Acceptance applies to the reviewed receipt
`7f713ed31e2ce7d63a1a67e806d671b38ff2f7bafd2d66592f68ff70d575c41e`
and actual application result
`12d10e51bc94b0339dad5dfcff5d0eada91238c310692775423a733ea698db10`.
The technical review and historical evidence below remain unchanged in their
original scopes. Installer progress is separate: [N2_REPORT.md](N2_REPORT.md).
N3/N4 remain unauthorized; N1 acceptance is not public-release approval.

---

# Technical review before formal acceptance — retained

# N1 — VERIFIED PASS / RECOMMENDED FOR OWNER ACCEPTANCE

3 November 2026, Korea time. **Native Qt feasibility and security satisfy the N1
exit criteria for the identified experiment. Formal owner acceptance is pending.**
This closeout supersedes the pending-status wording in the historical records
below. It does not authorize or begin N2, N3 or N4.

## Active release target and decisions

**Native Ubuntu installation via GitHub Releases**, using versioned archives and
the existing PySide6/Qt desktop application on Ubuntu x86_64 / GNOME Wayland.
N1 is native Qt feasibility and security; N2 is versioned installer and desktop
integration; N3 is data-safe manual updater and uninstaller; N4 is native CI and
public-release preparation. The installer and release pipeline are not completed.
Flatpak is paused historical/fallback implementation. Legacy P6 filenames are
documentation containers, not an additional Flatpak completion requirement.

N1 implementation was authorized. The owner has accepted the ordinary-user
filesystem/network privilege tradeoff; this decision need not be requested again.
Qt WebEngine renderer sandboxing, backend authentication and data protections remain
required. MIT is selected for CyrNava's original code. Copyright-holder attribution,
branding rights and applicable third-party redistribution obligations remain separate
release decisions; this closeout creates or changes no license file.

## Actual application evidence and acceptance review

Reviewed `ci-output/p6-native-n1-application-1/result.json`: **PASS**, complete true,
scope `N1-real-launcher-edit-and-reopen`. Both `edit` and `restart` independently
record backend, renderer, Qt providers, normal exit, owned-process cleanup and
unauthenticated-backend rejection **PASS**. Saved content/images, stable origin
and owner visual confirmation are also **PASS**. No failure/error field or skipped
required phase is present. `restart-state-validation` is the final completed stage,
not an unfinished operation.

The recorded driver source was inspected against these fields. Each phase launches
the candidate's private Python with `-B -I` and its unchanged `launch.py`, which calls
the existing `desktop.native.application.run()`. It renders the real built CyrNava
interface; it does not substitute a fixture window or inject editor content. PASS
requires normal exit, actual owned backend/renderer observations, private Qt maps,
HTTP 401 without credentials, descendant cleanup, validated saved state and the
owner's explicit confirmation. No required assertion was removed or made optional.

| N1 criterion | Reviewed evidence and result |
| --- | --- |
| Coherent Python/Qt dependency and ABI closure | Original `providers-final.json` PASS: CPython 3.14; PySide6, Shiboken6, Qt and WebEngine 6.11.3; 3,920 installed wheel files verified, helper/resources/locales/plugins present, no missing libraries, matching `QtPrivate_6_11_3`. Its recorded hash still matches. Both actual GUI phases additionally passed private Qt provider checks. |
| Actual Ubuntu/Wayland application, existing Qt launcher | Two real application launches PASS through the recorded unchanged launcher; owner confirmed native window/icon and editor behavior. Child uses Wayland and verified Ubuntu system schemas. No menu installation is implied. |
| Renderer security | Separate owner-host `owner-system-schemas-role-result.json` PASS: stable page renderer identity, expected helper, exact renderer role, user/PID/network namespaces, NoNewPrivs=1, Seccomp=2 and Chromium namespace-sandbox diagnostic. Saved predicate and private command-line hash/parser agree on review. Both real GUI phases also observed the protected renderer. |
| Authenticated backend and origin protection | Both GUI phases rejected unauthenticated access and cleaned up owned processes. The retained, unchanged target-Python `backend-check.json` additionally verifies wrong-origin rejection, restart/token revocation and data integrity. These additional backend checks were not repeated during the GUI phases. |
| Synthetic folder, rich note and screenshot persistence | Both state records validate schema 5, one folder, one note and one asset; required note/folder relationship, bold text and attached image PASS. Production schema/asset validation and canonical fingerprints are used. The two saved records are byte-identical. |
| Same profile, stable origin and appearance across restart | Driver uses the same fixed synthetic profile, refuses workspace-pointer changes and compares the two state records. Origin hashes match. Dark appearance on both launches is explicitly owner-confirmed; no independent browser-preference hash was captured. |
| Cleanup and owner confirmation | Both launches exited normally and owned descendants were reaped. Owner visual confirmation PASS is required before the driver can write overall PASS. |

The phase snapshots share content fingerprint
`5248342cd4b7bceceb4aab841afc9286cecca8c8d9720be20dd0b3f6a9ebb4f6`,
image hash `ddc4c829800942687bcc6c0d085528a9ef1a4bd924671cf0cb50f0e85e4761ab`
and origin hash `8703b0f9c40b4e8de0de4f240ee34b9ce29096537c6a4b5ebeab4b272639e81e`.
Read-only closeout inspection confirms the retained image and origin still match
and no active-workspace pointer exists. No profile initialization, migration or
write was performed during review.

## Candidate, source and evidence identities

Candidate: `ci-output/p6-native-n1-1/`. Recorded source baseline:
`bfa0b8005a3ddc519354fd7907e9b972fde8126b`; recorded uncommitted application-patch
SHA-256: `a5e88d7f4102aed8f44f2f54b7991638dee8e5f7df605dbbf4c941a3bde8c43c`.
This is an experimental native candidate, not the accepted historical A/B package
or a newly committed release. All 65 application payload files and all frontend
input hashes in the receipt match on closeout review.

| Identity | SHA-256 |
| --- | --- |
| Candidate receipt `n1.json` | `7f713ed31e2ce7d63a1a67e806d671b38ff2f7bafd2d66592f68ff70d575c41e` |
| Unchanged `launch.py` | `433928adca59ca511b8b4c189dff51472197573d7267f8ddb8268b1c82cd94d1` |
| Executed `check_application.py` | `406e0afd6011dbf9f1e9031d8f6e8c8cdf8eb5ba3b7557b2db4fca67260584ed` |
| Actual application `result.json` | `12d10e51bc94b0339dad5dfcff5d0eada91238c310692775423a733ea698db10` |
| Each edit/restart state JSON | `ca258910c763a7ef0f11c63b561d06afbb34a957196f3e9f6f2d67fe5442d736` |
| Actual owner renderer PASS result | `554d5f2254443467ff485aaea844b5ac81af16a07ef1b7df72e99efd38b27639` |
| Exact WebEngine helper | `f6b864245334ee7bd58fcbd0e7e7ce3772a87380d8d094c513764ed999987900` |
| Runtime requirements lock | `24876b72281d5427fc9c5c41cdb19a918815e9547e74c5eb4d2c93ac22e4a576` |
| Dependency inventory | `621c640f428886a7944b654fe6726f2b3ab82644e4911a051f8281ab392eb8a3` |
| Retained backend check | `35a402b4d22d771063086c00883c23ce6ec3ea06c37613ea0d6662d4272e947c` |
| Retained provider closure | `3ce1fdf85520d1b844c318f36bd10dd529b8f7aaa46e3ff790241adb9f428319` |

Private application logs were inspected locally. Edit log: 1,596 bytes,
`03b0baf51e2ae20a60e449dfd52ebe1ac9d471edb4024e48eb85ad94f15adcd3`.
Restart log: 1,257 bytes,
`9b92b4cb354cf60f406678c1e39f163a4d2bf7a91e40e4d7b0776b438ed5a662`.
Both state-validator logs are empty. Raw logs remain private. They record portal
application-ID registration and Wayland text-input warnings; these did not prevent
the observed launches, editing, persistence or security checks. Their underlying
cause is not established by this closeout; installed desktop integration remains
N2 work, not an inferred PASS here.

## Acceptance boundary and next owner checkpoint

No N1 exit criterion remains missing within this experiment's scope. Evidence is
specific to the tested Ubuntu 26.04.1 x86_64/GNOME Wayland environment, CPython 3.14,
matched 6.11.3 stack and child-only Ubuntu schema selection. The renderer diagnostic
records the editor-launched `snap.code.code (complain)` parent context. It does not
certify arbitrary launch contexts, future dependencies, an installed menu entry,
an updater, licensing clearance or a public release. Visual appearance persistence
is owner-attested, not independently measured from a preference database. GUI phase
records retain predicate results rather than full per-phase process maps.

The original confined namespace failure, initial host startup BLOCKED, earlier
role-verification BLOCKED and their original evidence remain unchanged. The earlier
unsaved process-title interleaving remains unproven. P1–P5 acceptance and historical
R11 component/R12 PASS evidence are preserved under their original artifact scope.
They were not reopened or used as substitutes for these native GUI results.

Prior local results remain scoped evidence: 54 N1 fixtures, Ruff/formatting, the
target-Python offline state validator, 147 application regressions and 36 packaging
regressions as recorded below. **No tests, native probes, builds or downloads were
executed during this closeout.** Only evidence reads, hashes, saved-policy evaluation
and documentation edits were performed; no generated result JSON was changed.

Recommendation: formally accept **N1 — Native Qt feasibility and security**, then
separately authorize **N2 — Versioned installer and desktop integration**. The
ordinary-user privilege tradeoff is already accepted. N2–N4 remain unstarted and
unauthorized. No commit, push, installation, signing or publication occurred.

Proposed N2 initialization prompt, for owner review only:

> I formally accept N1 and authorize N2 only: versioned per-user native installation
> and desktop integration for the verified Ubuntu x86_64/GNOME Wayland target.
> Reuse the verified N1 Qt stack and existing application, preserve uncommitted work,
> and follow the existing N2 roadmap with the shared installation engine and thin
> shell entry points. Implement and test archive/trust validation, isolated staging,
> safe activation and normal desktop-menu launch with disposable data. Preserve
> renderer sandboxing, backend authentication and data isolation. Present exact
> owner-only trust, system-prerequisite or native-menu checks when needed. Do not
> begin N3/N4, change host security, touch personal application data, commit, push,
> generate production keys or publish without separate authorization. Stop at the
> N2 verification and owner-review checkpoint.

---

# Historical application handoff and earlier investigation — retained

The following dated checkpoint text and commands are historical. Pending statuses
describe those earlier moments, not the verified result above. Do not rerun them.

# N1 current status — renderer PASS; application verification prepared

3 November 2026, Korea time. **N1 remains CONDITIONAL / NOT ACCEPTED.**
The owner-host Wayland renderer-security probe now has an independently verified
**PASS**. The normal CyrNava application-window/edit-and-reopen check is prepared,
locally tested and awaiting the owner's visible GUI interactions. N2–N4 remain
planned and unauthorized. Previous investigation records below remain historical;
no earlier FAIL/BLOCKED result is rewritten.

## Verified native renderer PASS

Actual evidence: `ci-output/p6-native-n1-1/owner-system-schemas-role-result.json`,
`owner-system-schemas-role.json` and matching private log/command-line evidence.
The saved JSON reports PASS, complete true, exit 0, **0.516 s**. Independent review
recomputed the security predicate, checked executable/tooling/log hashes and parsed
the private command-line bytes against the reviewed expected helper. The safe
classification is **chromium-process-title / renderer / exact-renderer-role**.
This supports the parser correction with an actual host observation; the precise
unsaved argv of the preceding blocked run remains a historical uncertainty.

| Native probe check | Actual result |
| --- | --- |
| Wayland platform | PASS |
| Candidate Qt/provider coherence | PASS |
| Expected WebEngine helper and stable page renderer PID | PASS |
| Exact renderer role | PASS; flattened Chromium process title |
| User / PID / network namespace separation | PASS / PASS / PASS |
| NoNewPrivs / seccomp | 1 / 2; PASS under the unchanged policy |
| Chromium diagnostic | Namespace layer, PID/network isolation and Seccomp-BPF Yes; adequately sandboxed |
| Mount namespace separation | false, retained observation; not required by the existing predicate |
| Normal CyrNava application launcher | NOT EXECUTED by this renderer-only probe |

The observed parent remains `snap.code.code (complain)`: acceptance evidence is
specific to this editor-launched Ubuntu/GNOME Wayland context and the reviewed
child-only Ubuntu system-schema selection. No AppArmor rule, user namespace policy,
renderer flag or host setting changed. Imports, the old confined offscreen result
and this new host result retain their distinct scopes.

Evidence identities:

- Candidate receipt: `7f713ed31e2ce7d63a1a67e806d671b38ff2f7bafd2d66592f68ff70d575c41e`.
- Renderer diagnostic: `fbb2fa1b20d7cf760c612d3f7efcebad0986eb5971ef0003b6fa169e94cec5d8`.
- Supervisor: `36ac17bf50f9fb780f952b06e7b326f6c8ff7e37b61e0e7f558898218835f530`.
- Actual PASS result JSON: `554d5f2254443467ff485aaea844b5ac81af16a07ef1b7df72e99efd38b27639`.
- Private command-line evidence: `8f9ab1107fb56475fbc61da640fd495e4708dc93c5bf7456a3a034df527c00fd`, 1,288 bytes, kept private.
- Private log: empty; `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- Compiled system schemas: `21865d7b212dfafb37dbc3394cf386b9d1a4fdfcb4f61192f286bffb2b0d61a6`.

## Remaining N1 application verification

`packaging/native/feasibility/check_application.py` is a separate owner-only check,
not an installer/updater and not a replacement application. It invokes the actual
existing private Python and **unchanged candidate `launch.py`** twice. It does not
monkeypatch application configuration, Qt window classes, backend ownership,
security policies or JavaScript. System-schema selection is identical to the
passing probe. The existing candidate profile is reserved for synthetic data;
read-only preflight confirmed it has no initial workspace database or active
workspace pointer. An existing database or previous attempt is refused, never
reset. The candidate payload, receipt, launcher, Qt stack and earlier evidence are
unchanged.

First window, owner actions (instructions appear before the window opens):

1. Create folder **N1 GUI folder**.
2. Create a note inside it titled **N1 GUI owner edit**.
3. Enter **N1 GUI verified** and make that phrase bold.
4. Paste a screenshot of only this synthetic window into the note with Ctrl+V.
5. Set Appearance to Dark; wait for Saved and finished uploads; close normally.

The checker then reuses the actual candidate's established migration/profile
validator and content fingerprint under its Python 3.14 to validate the database,
schema, assets, note-folder relationship, saved bold text and referenced image.
The second window reopens the same profile/origin: visually confirm the note,
bold text, pasted image and Dark appearance, then close without editing.
The checker compares canonical records, image hashes and origin across restart.
It requests one explicit owner visual confirmation, accepting normalized case/
spacing. Visual title/icon, clipboard and appearance observations are attributed
to the owner, separately from automated persistence checks; a normal exit alone
cannot pass. No personal data, backup import or old A/B exercise is involved.

For each launch, it samples only its retained GUI's descendant process tree to
observe the expected renderer role/helper, namespaces/seccomp, candidate Qt
providers and owned backend. It rejects a foreign Qt provider. A direct loopback
request without credentials must return 401; no session credential is inspected
or emitted. Normal close must exit successfully and the observed owned processes
must be gone before the next phase. Ctrl+C/deadline handling asks the owned GUI to
close first, then bounds cleanup and records FAIL rather than retrying or treating
interruption as application failure evidence without context. No global process
kill, root GUI, sandbox-disable flag or host-security change is used. Core dumps
are disabled for the child only; private log growth is capped at 2 MiB and each
owner interaction window has an explicit ten-minute deadline.

## Local verification completed for the application checker

- **54 N1 fixtures PASS:** the previous 43 plus 11 application-driver fixtures.
  Tests cover candidate/PASS evidence checks, preserved existing attempts/data,
  required saved folder/note/bold/image, underlying validator failure, refusal to
  pass on clean exit alone, the exact unchanged launcher command, interrupt cleanup,
  noninteractive desktop refusal, 401 versus 403/200, restart-state changes and
  required owner visual confirmation.
- Ruff and formatting PASS for both new files.
- **Real candidate CPython 3.14 offline state-validator fixture PASS**, using the
  candidate's Database/AssetStore/profile validator, generated raster image and
  real SQLite records. The database/assets remained byte-identical across checks,
  and content fingerprints were stable. This executed no Qt/GUI/clipboard code.
  New safe record: `ci/evidence/n1/2026-11-03/application-state-check.json`.
- Application preflight PASS in read-only mode against the actual candidate,
  native PASS evidence and private command-line hash. No GUI attempt directory
  exists yet. No owner-desktop execution was performed by the agent.

Application checker SHA-256: `406e0afd6011dbf9f1e9031d8f6e8c8cdf8eb5ba3b7557b2db4fca67260584ed`.
New files are `check_application.py` and `test_application_check.py`; existing
application/backend/frontend source and the successful renderer verifier remain
unchanged. No dependency download, rebuild, installation, real-data migration,
commit/push, Actions execution, signing or publication occurred. Existing P1–P5
acceptance and R11/R12 evidence remain preserved; they are not relabelled as this
new native application's GUI results.

## Single owner command

```bash
cd /home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
python3 -B packaging/native/feasibility/check_application.py --owner-host
```

**This time an actual CyrNava window is expected**, titled
**CyrNava — Native N1 feasibility**. Follow the terminal instructions; it waits
for Enter before each launch. Complete the synthetic edits in the first window,
and visually check/reclose the second. Do not open the candidate by hand first,
use personal content or rerun any completed renderer/startup probe.

Fresh output: `ci-output/p6-native-n1-application-1/result.json`, with progress and
separate phase/state records. Keep all `.private.log` files and the synthetic
profile/images local. Existing outputs refuse reuse. If blocked, preserve them for
review. This GUI/edit/reopen run is **NOT EXECUTED / pending owner**. A future PASS
must be inspected before N1 is recommended for acceptance; it does not authorize
N2–N4.

---

# Historical investigation and correction report — retained

The following is the earlier last-three-prompts report, before the newly supplied
renderer PASS and application handoff. Its original statuses remain as records of
their artifacts and execution scopes; current status is given above.

# N1 — Native Qt feasibility: investigation and correction report

3 November 2026, Korea time. Covers the last three owner prompts: **“Do it”**,
**“Command ran, do your thing”**, and the present schema-corrected result/report
request. Repository paths in this report are relative to CyrNava.

**N1 STATUS: CONDITIONAL / NOT ACCEPTED.** The native experiment exists. Ubuntu
Wayland initialization and the sandbox diagnostic now execute with coherent Qt
providers and positive namespace/seccomp observations. The latest saved owner test
is still BLOCKED because renderer-role identity was not verified. The diagnostic
has been corrected locally; its corrected native result does not yet exist.
Normal CyrNava window/GUI editing/persistence checks remain NOT EXECUTED.

## Target, decisions and boundaries

The active target is the existing PySide6/Qt desktop application on Ubuntu
26.04.1 LTS, x86_64, GNOME Wayland, distributed eventually as versioned GitHub
Releases archives. N1 is native Qt feasibility; N2 installer/desktop integration,
N3 data-safe manual update/uninstall and N4 native CI/public-release preparation
remain proposed and unauthorized. No installer/updater feature is claimed here.
Flatpak is paused/fallback history, with no additional old P6 process required
after N1–N4. Legacy P6 document names are containers, not duplicate release gates.

N1 and the ordinary-user filesystem/network tradeoff are already owner-authorized.
Qt renderer sandboxing, backend authentication and data safeguards remain required.
MIT is selected for original code; copyright-holder attribution, branding rights
and third-party redistribution/source obligations remain separate. No license
files or host security settings were changed. P1–P5 acceptance and R11/R12 evidence
remain intact, and do not independently certify this native experiment.

## Experiment identity

| Item | Identity |
| --- | --- |
| Existing experiment | `ci-output/p6-native-n1-1/` (not rebuilt or moved) |
| Source base | `bfa0b8005a3ddc519354fd7907e9b972fde8126b` plus recorded uncommitted application snapshot |
| Recorded application patch SHA-256 | `a5e88d7f4102aed8f44f2f54b7991638dee8e5f7df605dbbf4c941a3bde8c43c` |
| Receipt SHA-256 | `7f713ed31e2ce7d63a1a67e806d671b38ff2f7bafd2d66592f68ff70d575c41e` |
| Stack | CPython 3.14; PySide6, Shiboken, Qt and WebEngine 6.11.3 |
| Runtime requirements SHA-256 | `24876b72281d5427fc9c5c41cdb19a918815e9547e74c5eb4d2c93ac22e4a576` |
| Dependency inventory SHA-256 | `621c640f428886a7944b654fe6726f2b3ab82644e4911a051f8281ab392eb8a3` |
| Existing candidate launcher SHA-256 | `433928adca59ca511b8b4c189dff51472197573d7267f8ddb8268b1c82cd94d1` |
| Latest executed renderer diagnostic SHA-256 | `70ad934d0bb9fe4c09e5978526969c63c6ba71b660335619da896fe1bd4844b3` |
| Latest executed supervisor SHA-256 | `3cb946c87a959589816f88fe6b3d2895be4919b48357b8fc67956b4779c60a14` |
| Corrected renderer diagnostic SHA-256 | `fbb2fa1b20d7cf760c612d3f7efcebad0986eb5971ef0003b6fa169e94cec5d8` |
| Corrected supervisor SHA-256 | `36ac17bf50f9fb780f952b06e7b326f6c8ff7e37b61e0e7f558898218835f530` |

The candidate receipt's application-file hashes and existing launcher identity are
preserved. Only host-side N1 tooling changed; the experiment application, Python
venv, Qt wheels, helper, requirements and database format were not replaced.
The small executed-source snapshots under
`ci/evidence/n1/2026-11-03/executed-before-role-fix/` match the recorded old source
hashes, so the new verifier is not confused with the verifier that produced BLOCKED.

## Work across the last three prompts

| Owner prompt | Work completed | Actual outcome and limit |
| --- | --- | --- |
| 1. “Do it” — investigate the first owner-host abort | Inspected the existing private log and exact launch sequence; inspected Qt GTK theme/GTK Wayland settings sources and installed schema keys. Added bounded startup-only GDB diagnostic, privacy/timeout guards and offline fixtures. | Original renderer probe remains BLOCKED, exit -6, 1.369 s. Its fatal GLib missing-key error identified a settings integration path, not a renderer-sandbox failure. 25 N1 fixtures and lint passed. No native diagnostic was executed by the agent. |
| 2. “Command ran, do your thing” — startup diagnostic returned | Verified the saved private-log/source hashes; inspected the backtrace and actual library providers. Added explicit child-only Ubuntu system-schema selection, preflight and fresh outputs. Added real GLib synthetic-overlay and failure/preservation regressions. | Backtrace confirms failure during QApplication construction. The inherited schema override hid all modern font keys. GDB exit 0 means diagnostic completion, not application success. 33 N1 tests and lint passed. |
| 3. Current request — schema-corrected renderer probe returned | Verified the latest saved result, diagnostic and empty private log; isolated the remaining failed role assertion. Corrected strict process-title parsing, added private command-line capture/PID-stability checks and explicit fresh output prefix. Preserved executed sources and wrote this report. | GTK startup problem is avoided in the tested child configuration. Native namespace/seccomp/provider observations are positive; saved overall status remains BLOCKED. 43 local N1 tests and lint pass. Corrected verifier has not run natively. |

### Confirmed startup failure and child-only correction

The retained startup backtrace follows QApplication -> QPlatformThemeFactory ->
candidate `libqgtk3.so` -> Ubuntu `gtk_init`/`gtk_init_check` -> Ubuntu GDK ->
`g_settings_get_enum` -> fatal GLib/GIO schema lookup. It stopped at
`qapplication-construction`, before renderer creation. Qt/PySide libraries came
from the candidate, GTK/GDK/GIO/GLib from the OS, and an editor Snap-cache dconf
module was present. No Qt ABI/private-symbol failure is shown by that trace.

The owner inherited GSETTINGS_SCHEMA_DIR. Key-only queries could find neither the
modern font keys nor the old xsettings font keys, while the OS system schemas
contain the modern keys. This is a schema-visibility mismatch in the launch context.
[GLib documents these schema search overrides](https://docs.gtk.org/gio/type_func.SettingsSchemaSource.get_default.html).
The actual directory value was not logged; exact editor-component/Snap-revision
provenance is unproven and is not asserted.

`--ubuntu-system-schemas` changes only the diagnostic child's copied environment,
selecting `/usr/share/glib-2.0/schemas`. It checks OS ownership, non-writability,
compiled-schema stability/hash and modern font-key presence first. It reads key
names, not preference values. The parent shell, GNOME settings and host policies
are untouched. Numeric OS ownership is namespace-aware; the invoking user is never
accepted as the OS owner. A synthetic older-schema overlay reproduces hidden keys
in real GLib, and system selection restores visibility without changing the overlay.

### Latest actual owner-host observations

Evidence: `ci-output/p6-native-n1-1/owner-system-schemas-result.json` and
`owner-system-schemas.json`. The run completed in **0.667 s**, exit **2**, overall
**BLOCKED**, and recorded:

| Check | Saved observation |
| --- | --- |
| Platform | Wayland |
| Loaded Qt provider coherence | true; candidate-owned Qt libraries and Wayland plugin |
| Correct helper executable | true |
| Chromium diagnostic | Layer 1 Namespace; PID namespaces Yes; Network namespaces Yes; Seccomp-BPF Yes; “adequately sandboxed” |
| Actual process protection | NoNewPrivs 1; Seccomp 2 |
| User / PID / network namespace separation | true / true / true |
| Mount namespace separation | false; not a requirement in the existing `security_pass` policy |
| Renderer role | **false — the only unsatisfied existing policy predicate** |
| Parent context | `snap.code.code (complain)`; this is the tested editor-launched context |
| Normal CyrNava application launch | NOT EXECUTED |

The original `renderer_sandbox: FAIL` and overall BLOCKED records are unchanged.
These records establish positive process-isolation observations, but not a full
verified renderer identity or standalone desktop-launch certificate. No sandbox
weakening or AppArmor change is justified by this result.

### Renderer-role diagnostic defect, correction and uncertainty

The old code searched NUL-delimited `/proc/PID/cmdline` entries for a standalone
`--type=renderer`. [Chromium's Linux process-title implementation](https://chromium.googlesource.com/chromium/src/base/+/main/process/set_process_title.cc)
also represents arguments as one flattened process-title string after zygote fork.
For that supported representation, the old check demonstrably returns false even
with a renderer role present. This is a confirmed parser limitation. However, the
actual old command-line bytes were not retained, and the process has exited.
**Whether that precise representation caused this owner run's false role assertion
remains unproven.** No saved failure is converted into PASS by inference.

The corrected diagnostic accepts exact role switches in ordinary NUL-delimited
argv, or a recognized helper-prefixed flattened title with the role as its first
switch. It rejects missing, conflicting, duplicate, embedded, truncated/oversized,
non-renderer and unrecognized role forms. It does not accept a role substring in
a URL or unrelated argument. Executable identity remains independently required;
Qt's page renderer PID is sampled before/after with process start time/executable
checks to reject PID change/reuse. [Qt documents the page's renderer PID](https://doc.qt.io/qt-6.11/qwebenginepage.html#renderProcessPid-prop).

A fresh private file captures up to 65,537 bytes (one-byte overflow detection above
the 64 KiB acceptance cap) of command-line evidence, mode 0600, exclusive/no-follow
creation. Public JSON contains only byte length/hash and safe role classification.
Existing evidence or symlinks are refused. All original namespace, seccomp,
NoNewPrivs, helper/provider and inadequate-sandbox checks remain required. The
role predicate was not removed; positive namespace text alone still cannot pass.

## Corrections and documentation files

Across the three prompts:

- `packaging/native/feasibility/diagnose_startup.py` and
  `test_startup_diagnostic.py`: startup-only diagnosis, private logging and guards.
- `packaging/native/feasibility/run_probe.py` and `test_system_schemas.py`:
  explicit system-schema child environment and fresh-output/preservation coverage.
- `packaging/native/feasibility/sandbox_probe.py` and `test_renderer_role.py`:
  role representation handling, private evidence and process-identity checks.
- `ci/evidence/n1/2026-11-03/executed-before-role-fix/sandbox_probe.py.txt` and
  `run_probe.py.txt`: exact small source snapshots for the latest executed run.
- This `ci/N1_REPORT.md`, current-status wording in `ci/P6_REPORT.md`,
  `ci/P6_OWNER_CHECKS.md`, `ci/P6_NATIVE_DISTRIBUTION_ROADMAP.md` and the N1 README.

No application source, candidate payload, native dependency, production manifest,
installer, updater, workflow, license, security policy or personal workspace changed
within these three prompts. No native execution was performed by the agent.

## Verification and preserved evidence

Latest local commands:

```bash
backend/.venv/bin/python -B -m unittest discover -s packaging/native/feasibility -p 'test*.py'
backend/.venv/bin/ruff check --no-cache packaging/native/feasibility/sandbox_probe.py packaging/native/feasibility/run_probe.py packaging/native/feasibility/test_renderer_role.py packaging/native/feasibility/test_system_schemas.py
backend/.venv/bin/ruff format --check --no-cache packaging/native/feasibility/sandbox_probe.py packaging/native/feasibility/run_probe.py packaging/native/feasibility/test_renderer_role.py packaging/native/feasibility/test_system_schemas.py
```

**43 N1 tests PASS:** 17 original policy fixtures, 8 startup fixtures, 10 schema/
output fixtures and 8 role/capture fixtures. Ruff and formatting PASS. These are
local tests with synthetic data/mocked Qt; the real GLib tests inspect only schema
keys. No native renderer success is claimed from them. Prior recorded matched
provider/ABI/backend-data checks and 147 application plus 36 packaging regressions
remain scoped historical results, not rerun or relabelled as tests of this correction.
No new backend/frontend change requires repeating those suites here.

| Preserved evidence | Integrity / scope |
| --- | --- |
| `ci-output/p6-native-n1-1/owner-sandbox-result.json` and original private log | Original BLOCKED result and receipt retained; private log hash `3ba4ce26dfbf3079a2badfe58ad8709b1e312e41ccd2ae36fa2df0cc78b3f5e5` |
| `ci-output/p6-native-n1-startup-1/result.json`, `progress.json`, `startup.private.log` | Startup source hash `4648888d2129f8193402062e3b22a1ca45690d5c07e04e1b7989b16e2f9d6392`; private log hash `8b6e9ae208702cb4405b661760062cb3cbea436924e2e4793dbf290781a501ec` |
| Latest schema-corrected JSON result | SHA-256 `9e2c59c62a34393e8862aa01a597d004d655cfd295214823364f63ce5e924feb` |
| Latest child diagnostic JSON | SHA-256 `fe141a3f12fffe44e442044fe2c03e184f0996ef132c203844908a62e194eaab` |
| Latest private log | Empty, SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; no raw data published |
| System compiled schemas used in owner run | SHA-256 `21865d7b212dfafb37dbc3394cf386b9d1a4fdfcb4f61192f286bffb2b0d61a6` |

## Next bounded owner step

One fresh corrected **renderer-security probe**, no visible CyrNava window and
no application editing. Same candidate and receipt; no rebuild or installation.
Run once in the same normal host terminal context:

```bash
cd /home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
python3 -B packaging/native/feasibility/run_probe.py \
  --candidate "$PWD/ci-output/p6-native-n1-1" \
  --receipt-sha256 7f713ed31e2ce7d63a1a67e806d671b38ff2f7bafd2d66592f68ff70d575c41e \
  --owner-host \
  --ubuntu-system-schemas \
  --record-prefix owner-system-schemas-role
```

Expected outputs next to the candidate:
`owner-system-schemas-role-result.json`, `owner-system-schemas-role.json`,
`owner-system-schemas-role.private.log` and
`owner-system-schemas-role.renderer-cmdline.private`. Keep both private files local.
Three-second schema preflight, 25-second child deadline, up to ten seconds cleanup;
no automatic retry. This corrected native execution has **NOT EXECUTED**.
If blocked, inspect the new private command-line identity evidence before proposing
another action. Do not remove the identity assertion or disable sandboxing.

Even a probe PASS does not complete N1. Review it before the remaining short normal
CyrNava-window and synthetic editor/image/save/reopen checks. N2–N4, commits, pushes,
GitHub Actions, host-security changes, permanent signing and publication remain
unauthorized. No old Flatpak acquisition or historical A/B rehearsal is required.
