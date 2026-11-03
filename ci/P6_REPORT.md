# Current native release — source-first installation

3 November 2026. **N1–N3 ACCEPTED / COMPLETE. N4 CONDITIONAL — source-first installation, revised CI and public-repository readiness.**

The owner selected a **source-first GitHub repository with an online dependency
installer**. From reviewed immutable versioned source (Git checkout or GitHub ZIP),
users run `bash install.sh`; required exact Python dependencies come directly from
official upstream, and the locked frontend is built locally. Saved-data-preserving
manual updates use `bash update.sh`. Ubuntu 26.04 x86_64 / GNOME Wayland, ordinary
CPython 3.14 and the verified Qt/PySide/Shiboken/WebEngine 6.11.3 stack stay fixed.

N1 native feasibility, N2 versioned installation and N3 manual maintenance remain
accepted only in their actual verified scopes. CI **41621033436** remains PASS for
`b7ab94265270866911311b4ca818071868f58361`; it does not certify the changed online
installer. The previous offline bundled-wheel package is historical/tested, not a
required public release target. Flatpak remains paused historical/fallback, with
no duplicate old P6 acceptance requirement.

MIT / Copyright (c) 2026 74Cerillion, name/logo rights and the ordinary-user
filesystem/network tradeoff remain settled. Renderer sandboxing, AppArmor,
authenticated backend and data protections are required and unchanged.

Current implementation/evidence checkpoint: [N4 report](N4_REPORT.md).
User procedure: [native source installation](../docs/native-installation.md).
The [redistribution assessment](../docs/native-source-obligations.md) distinguishes
our actual source/assets from recipient-acquired dependencies. No commit, push,
normal installation, host policy loading, signing or publication is authorized by
this local implementation. Stop at the N4 owner checkpoint.

## Historical status before the source-first distribution decision

The records below retain their original artifact, environment and distribution scope.

# Current native-release status — N1–N3 accepted; N4 hosted CI verified

3 November 2026. **N1/N2/N3 ACCEPTED / COMPLETE. N4 hosted CI and independent
artifact verification PASS; N4 / public release CONDITIONAL.**

Current local checkpoint: **CONDITIONAL — SPECIFIC REDISTRIBUTION OBLIGATIONS
REMAIN.** [N4 report](N4_REPORT.md), [native source/notice catalog](../docs/native-redistribution.json)
and [specific obligations / unsent inquiries](../docs/native-source-obligations.md)
record bounded material preparation. Exact Qt/PySide/WebEngine/Chromium and
bundled native source/build/credit correspondence, applicable module terms,
recipient replacement/rebuild instructions, use-composed-ref attribution, and
pydantic-core bundled-component notice mapping remain unresolved. MIT attribution
and owner name/logo rights are settled. No package was rebuilt; accepted source/
artifacts and security controls remain unchanged. The smallest next action is
owner review of drafted targeted clarification requests or provision of equivalent
authoritative materials. This does not authorize contact, signing or publication.

## Accepted hosted checkpoint — preserved evidence

Exactly one reviewed 17-file commit `b7ab94265270866911311b4ca818071868f58361`
and one normal integration push completed; independent parent/tree/blob/remote
readback PASS and main unchanged. Ordinary CI **41621033436**, attempt 1, passed
all five jobs: workflow, backend/security, frontend/browser, native assembly/audit/
headless installation and required gate. Four actual artifact hashes/provenance,
source/lock/wheel/installer/bootstrap correspondence and native diagnostic records
were independently verified. Development archive `0.1.0-n4.1`, SHA-256
`1e49348570e7f779a352cb0a2d623a6f3973f828628b9ea60bb6e4fc6f2a3897`.
This does not certify the final public-identity package or native GUI.

The actual CI runner schema observation stays **BLOCKED**: compiled schemas UID 0,
mode `0777`; the production trust guard refuses them. Current headless installation
does not execute that preflight, normal launcher or renderer. Initial bounded
artifact-read timeout is preserved; official connector retrieval subsequently
passed, without CI/build retry. Original hosted failures and accepted N1–N3 evidence
remain unchanged. No further implementation or commit/push is authorized by this
completed checkpoint; status/evidence closeout is local and uncommitted.

Active target: **native Ubuntu 26.04 x86_64 / GNOME Wayland installation via
versioned GitHub Releases archives**, with manual full-package updates. N1 is
native Qt feasibility/security; N2 installer/desktop integration; N3 data-safe
manual updater/uninstaller; N4 native CI/public-release preparation. Flatpak is
paused historical/fallback, with no old Flatpak P6 completion gate. Legacy P6
filenames remain documentation containers.

Remaining separate checkpoints: actual third-party notices/licensing/source
closure, genuine signing trust, exact final public-identity native GUI/security
and manual-update verification, and owner publication approval. MIT attribution
**Copyright (c) 2026 74Cerillion**, name/logo rights and the ordinary-user tradeoff
are settled. Renderer sandboxing, authentication and data protections remain
required. No production signing, host-policy change, GUI run or publication occurred.
Stop for owner review; next proposed step is third-party/source-delivery closure.
Current evidence: [N4_REPORT.md](N4_REPORT.md),
[N4_OWNER_CHECKS.md](N4_OWNER_CHECKS.md),
[hosted result](evidence/n4/hosted-41621033436/result.json).

## Historical checkpoint — local schema correction and previous hosted status

3 November 2026. **N1/N2/N3 ACCEPTED / COMPLETE. N4 local implementation VERIFIED;
public release CONDITIONAL.**
Latest local checkpoint: **schema fixtures and safe metadata diagnostics VERIFIED /
READY FOR REVIEW**. Fresh committed-source verification plus exactly two source-file
overlays passes **198 native + 63 feasibility + 38 workflow = 299 tests**, zero skips,
plus lint/format/workflow contract. Deterministic test trust metadata is separated
from actual host observation; unsafe metadata remains BLOCKED. Production trust
predicates/order remain intact. The diagnostic helper is a future package input;
no candidate was rebuilt and no desktop/renderer result is inferred.

Latest authorized commit/push remains `2b3ca78f7c5f4f6227d376a96cc3f8d46454b9b8`.
Ordinary CI `41616088358`, attempt 1, remains **FAIL**: workflow, backend,
frontend/browser and 198 native tests passed; feasibility had 51 passes, 2 errors
and 1 failure at the system-schema trust guard. The exact rejected GitHub
object/UID/mode remains unknown. No native package was produced. Original hosted
failure and diagnostic integrity/provenance records are preserved. No further
staging, commit/push, GitHub execution, build, native rehearsal or host-policy
change occurred. The repository was below its packaging disk floor; bounded tests
used temporary storage. Review the exact corrective batch before separately
authorizing any commit/normal integration push. [N4_REPORT.md](N4_REPORT.md) and
[local evidence](evidence/n4/schema-fixtures-2026-11-03/result.json) record the
scope and remaining requirements. Earlier hosted failures remain unchanged.
The owner formally accepted N3's independently reviewed native GUI/reinstall,
security, update/recovery and data-preservation scope. Exact artifact/result and
owner decision: [N3_REPORT.md](N3_REPORT.md),
[formal acceptance](evidence/n3/formal-owner-acceptance.json).

N4 source assembly/export audit and actual isolated headless installation PASS;
994 local tests PASS. An unsigned v0.1 public-identity proposal exists, with exact
hashes in [N4_REPORT.md](N4_REPORT.md). Final public-identity native evidence,
vendor source/notice closure, clean-source hosted CI, genuine release signing and
separately approved publication remain. Original code MIT attribution is
**Copyright (c) 2026 74Cerillion**;
owner confirms rights to the CyrNava name/logo. Third-party terms/source obligations,
production signing, final native package evidence and hosted verification remain
explicit. Current work: [N4_REPORT.md](N4_REPORT.md), [N4_OWNER_CHECKS.md](N4_OWNER_CHECKS.md).
No commits, pushes, GitHub executions, host-policy changes, signing or publication
are authorized. Flatpak stays paused historical/fallback, with no duplicate P6 gate.
Original evidence and the earlier checkpoints below retain their original scope.

## Historical checkpoints — N2 review

3 November 2026: **N2 VERIFIED PASS / RECOMMENDED FOR OWNER ACCEPTANCE.** Actual
client-5 GNOME menu evidence verifies renderer namespaces/NoNewPrivs/seccomp, exact
AppArmor labels/private providers, authentication, cleanup and unchanged saved
data/origin. Attempt 6 remains FAIL because its final terminal visual confirmation
was missing; the owner has now explicitly supplied that confirmation in this chat.
The close instruction was buried by verbose progress output. The driver correction
passes 153 N2 regressions and Ruff/formatting. No new GUI run is required for this
confirmation failure. Full identities and separate review: [N2_REPORT.md](N2_REPORT.md).
N1 remains ACCEPTED; N2 awaits formal acceptance; N3/N4 remain unauthorized and
unstarted. Native Ubuntu via GitHub Releases remains the active target; Flatpak
remains paused historical/fallback. No release signing or publication is implied.

## Historical checkpoint — policy correction review

3 November 2026: **N2 owner policy correction VERIFIED PASS.** The failed client-4
profile/file is removed; client-5's exact policy is loaded in enforce mode, and
its installed non-GUI bootstrap reports the correct named label and schemas.
Saved-result hashes and actual kernel metadata were independently verified in
[N2_REPORT.md](N2_REPORT.md). Global namespace restrictions remain enabled.
**N2 remains CONDITIONAL** pending actual client-5 GNOME menu/renderer/security
verification and owner acceptance. The existing checker and fresh owner-6 command
are in that report. No GUI, code change, host change or test rerun occurred in this
evidence review. N1 remains accepted; N3/N4 remain unauthorized and unstarted.
Flatpak remains paused historical/fallback, with no duplicate P6 release gate.

## Historical checkpoints — retained under their original scope

Latest: the owner-host profile **loaded**, then its mode check failed because
the kernel reports `unconfined`. N2 remains CONDITIONAL. The confirmed construction
defect is corrected using explicit enforce mode, preserving ordinary-user access
and every renderer predicate. Fresh native candidate/client 5, 146 regressions,
parser/lint, private dependencies and actual synthetic backend/data checks PASS.
The exact authorized removal/loading/non-GUI handoff is in
[N2_REPORT.md](N2_REPORT.md); use GNOME Terminal outside VS Code/Codex. The failed
profile remains loaded pending that handoff. No corrected host load or GUI execution
occurred here. N1 remains accepted; N3/N4 remain unstarted. Earlier records below
retain their original scopes and are not reclassified.

Current, 3 November 2026: **N2 local launcher/AppArmor implementation and offline
candidate-4 installation PASS; host-policy loading BLOCKED by Codex NoNewPrivs.**
Implementation and host loading are both owner-authorized. The exact owner-terminal
load handoff and immutable candidate/policy identities are in
[N2_REPORT.md](N2_REPORT.md). No additional approval for that same load is needed.
140 focused/relevant tests, parser/Ruff checks, all 4,414 providers and actual
synthetic backend/auth/data checks PASS. The changed candidate has no native GUI
result; N2 remains CONDITIONAL pending loaded-context/menu verification and owner
acceptance. N1 stays accepted; N3/N4 remain unstarted. Earlier evidence is unchanged.
The checkpoints below retain their original scope and authorization state.

Current planning checkpoint, 3 November 2026: the owner authorized **planning only**
for the AppArmor integration. The review proposal in [N2_REPORT.md](N2_REPORT.md)
recommends a dedicated native entrypoint and narrowly attached application profile,
with explicit process-family/writable-path limits and staged validation/reversal.
No implementation, host loading or new native test is authorized by that decision.
**N2 remains CONDITIONAL; N1 remains accepted; N3/N4 remain unstarted.** Only
documentation changed; original code, candidates and execution records are intact.
The older checkpoints below remain historical evidence of their recorded scopes.

Latest: **N2 CONDITIONAL — menu attempt 5 fails renderer namespace isolation.**
Expected helper/renderer, NoNewPrivs, seccomp, backend and private Qt providers were
observed, but user/PID/network separation failed without proc-read errors.
Existing native journal/kernel records support AppArmor launch context as the
cause: the accepted N1 probe inherited VS Code's Snap profile; GNOME's candidate PID
was audited entering restricted user namespaces. Exact child-denial ancestry is
not fully proven. Data/origin remains unchanged. Twenty focused diagnostic/menu
tests PASS; no security checks were relaxed. Do not retry unchanged: the proposed
app-specific AppArmor integration needs the owner's separate decision.
Details: [N2_REPORT.md](N2_REPORT.md), [N2_OWNER_CHECKS.md](N2_OWNER_CHECKS.md).
No GUI rerun, package/host-policy change, Git write or N3/N4 work occurred.

Latest: N2 menu attempt 4 is preserved FAIL: discovery and temporary-entry cleanup
PASS, but live evidence incomplete after normal close, without SIGINT. The exact
missing observation was not retained. Post-close data/origin remain identical.
An N2-only all-thread sampler/progress correction passes 18 focused tests; a real
threaded-child omission is reproduced but is not proven as the native failure's
cause. No GUI retry occurred. N2 remains CONDITIONAL; current details and fresh
owner-5 handoff: [N2_REPORT.md](N2_REPORT.md), [N2_OWNER_CHECKS.md](N2_OWNER_CHECKS.md).
Earlier GUI/signed-install PASS records retain their original scope. N3/N4 unstarted.

Current checkpoint, 3 November 2026: **N2 installed GUI/restart PASS and real
signed-install mechanism PASS.** Owner attempt 3 verifies exact saved data/origin,
renderer/providers/authentication, normal exit/cleanup and visual correctness;
its edit phase is explicitly inherited from reviewed attempt 2. A fresh isolated
normal signed install with a one-day test key passes all actual dependency,
provider, backend and bootstrap checks. The temporary private key was removed.
A public-key import/agent defect was corrected; 77 N2 regressions and lint PASS.
The original package, accepted evidence and historical failures remain intact.

**N2 remains CONDITIONAL only pending actual GNOME Applications-menu observation
and owner acceptance.** The one-click development-entry handoff is ready in
[N2_OWNER_CHECKS.md](N2_OWNER_CHECKS.md), with full evidence and exact signature
scope in [N2_REPORT.md](N2_REPORT.md). The test key establishes no production
identity/release trust. No normal installation, host-security change, commit/push,
publication or N3/N4 implementation occurred. N1 stays accepted; Flatpak stays
paused historical/fallback, with no duplicate P6 completion requirement.

The earlier checkpoints below retain their original dates, scopes and results.

Latest: N2 owner attempt 2's actual edit/renderer/auth/normal-close/cleanup checks
PASS. Post-close validation failed only because the saved bold marker was
capitalized differently. SQLite/data/image integrity is verified read-only. The
N2-only capitalization correction and guarded restart-only continuation pass 60
N2 tests; no package/profile change or agent GUI execution occurred. Original
attempts remain FAIL under their identities; N2 stays CONDITIONAL pending remaining
restart/menu and signed-install evidence. Current details and one-window owner
handoff: [N2_REPORT.md](N2_REPORT.md), [N2_OWNER_CHECKS.md](N2_OWNER_CHECKS.md).

The earlier checkpoints below retain their original scope and counts.

Latest checkpoint, 3 November 2026: N2 owner attempt 1 failed before process
construction because the verification adapter omitted `subprocess.STDOUT`.
The defect is reproduced and corrected; 48 N2 tests and lint pass. The original
failed attempt and executed source are preserved. No GUI rerun, application or
package change occurred. [N2_REPORT.md](N2_REPORT.md) distinguishes this driver
failure from application/runtime evidence; [N2_OWNER_CHECKS.md](N2_OWNER_CHECKS.md)
contains the new explicitly supported fresh-output command. N2 remains CONDITIONAL.

3 November 2026. **N1 ACCEPTED / COMPLETE** by explicit owner decision.
**N2 authorized; local implementation verified; CONDITIONAL pending owner native
desktop verification and authentic signed-install evidence.**
[N2_REPORT.md](N2_REPORT.md) records the actual fresh offline installation,
candidate/receipt hashes, 40 N2 + 54 N1 + 128 backend regression passes and retained
initial failures. [N2_OWNER_CHECKS.md](N2_OWNER_CHECKS.md) contains the focused
installed Desktop Entry handoff. No N2 GUI run or signing is inferred from local
checks. N3 data-safe manual updater/uninstaller and N4 native CI/public-release
preparation remain unauthorized and unstarted.

The active target remains native Ubuntu installation via GitHub Releases,
x86_64/GNOME Wayland and the existing Qt/PySide interface. Flatpak is paused
historical/fallback, not an additional gate. The ordinary-user tradeoff is already
accepted; renderer sandboxing, authentication and data safeguards remain required.
MIT is selected; attribution/branding/third-party obligations remain separate.
No normal user installation, security change, signing, Git write or publication.

Earlier acceptance recommendations/pending wording below are historical checkpoints.

---

# Current native-release status — 3 November 2026

**N1 — VERIFIED PASS / RECOMMENDED FOR OWNER ACCEPTANCE.** Formal owner acceptance
is pending. The actual saved application result at
`ci-output/p6-native-n1-application-1/result.json` is PASS, complete true, SHA-256
`12d10e51bc94b0339dad5dfcff5d0eada91238c310692775423a733ea698db10`.
Independent review confirms two launches through the unchanged existing Qt launcher,
private Qt providers, protected renderers, backend authentication, normal exit and
cleanup; validated folder/note/bold/image state and origin match across restart.
Dark appearance and visual correctness are explicitly owner-confirmed. The separate
host renderer and unchanged backend/provider records supply the remaining N1
security/ABI evidence. Full criteria, source identities and limitations:
[N1_REPORT.md](N1_REPORT.md).

Active distribution target: **Native Ubuntu installation via GitHub Releases**,
versioned archives, x86_64/GNOME Wayland, existing PySide6/Qt interface. N1 is native
Qt feasibility and security; N2 is versioned installer and desktop integration;
N3 is data-safe manual updater and uninstaller; N4 is native CI and public-release
preparation. N2–N4 remain planned and unauthorized; no installer or public release
is certified by N1. Flatpak is paused historical/fallback implementation. Legacy
P6 filenames do not impose an additional Flatpak completion requirement.

N1 implementation and the ordinary-user filesystem/network tradeoff were already
approved. Renderer sandboxing and existing authentication/data protections remain
required. MIT is selected for original code; copyright-holder attribution, branding
rights and third-party obligations remain separate release matters. P1–P5 acceptance
and R11/R12 records are preserved under their original identities.

This closeout performed evidence review and documentation edits only. No test,
probe, build, application change, installation, Git operation or publication.
Next checkpoint: owner formal N1 acceptance, followed by separate N2 authorization.

---

# Historical checkpoints and Flatpak records — retained

All earlier pending/status wording and commands below refer to their original
execution scope. They are superseded as current status by the closeout above.

# Current N1 checkpoint — 3 November 2026

**Owner-host renderer probe PASS independently verified; N1 CONDITIONAL / NOT
ACCEPTED pending real application GUI/edit/reopen verification.** Exact helper,
role, stable PID, Qt providers, namespaces and seccomp all agree. Current report
and tested owner application handoff: [N1_REPORT.md](N1_REPORT.md). The checker
launches the unchanged candidate; 54 fixtures, lint and a real target-Python offline
state-validator check pass. No GUI application run by the agent; N2–N4 remain
planned/unauthorized. Earlier statuses below are historical where superseded.

---

# Current N1 update — 3 November 2026

**N1 CONDITIONAL / NOT ACCEPTED.** The schema-corrected owner Wayland probe reached
Chromium's sandbox diagnostic with coherent providers, correct helper, user/PID/net
namespace separation, NoNewPrivs and seccomp. It remains BLOCKED solely on process-role
verification. The verifier now handles a supported Chromium process-title form and
captures private identity evidence; the old run's precise argv representation is
unrecorded and is not assumed. 43 N1 tests and lint pass; corrected native check
pending. Full report for the last three prompts: [N1_REPORT.md](N1_REPORT.md).
All saved statuses/evidence remain intact. No application or host-security change;
N2–N4 remain planned and unauthorized. Earlier current-status wording below is a
historical checkpoint where superseded by this update.

---

# Current N1 finding and correction — 3 November 2026

**N1 — Experiment built; owner-host startup failure diagnosed; corrected renderer
verification pending. Native feasibility is not accepted.** The current target is
native Ubuntu x86_64 / GNOME Wayland, the existing PySide6/Qt application and
versioned GitHub Releases archives. N1–N4 remain the active roadmap; N2–N4 are
planned and unauthorized. Flatpak is paused/fallback history, not a parallel gate.
The ordinary-user privilege tradeoff and MIT selection are already owner decisions;
no branding, copyright-holder or host-security decision is inferred.

## Actual owner evidence

The original renderer probe remains BLOCKED, exit -6 after 1.369 seconds, with no
normal application launch or renderer-isolation result. Its saved receipt, original
probe and private-log hashes still match. The subsequent startup-only diagnostic
is now executed at `ci-output/p6-native-n1-startup-1/`:

- `result.json`: DIAGNOSTIC_ONLY, complete true, final stage
  `qapplication-construction`, normal application NOT EXECUTED, renderer NOT TESTED.
- The private log is 22,848 bytes; SHA-256
  `8b6e9ae208702cb4405b661760062cb3cbea436924e2e4793dbf290781a501ec` matches
  the recorded result. Diagnostic source SHA-256
  `4648888d2129f8193402062e3b22a1ca45690d5c07e04e1b7989b16e2f9d6392`
  also matches. Both original attempts remain unmodified.
- GDB caught SIGTRAP at the fatal GLib/GIO missing-key error, with this actual
  call path: QApplication initialization -> QPlatformThemeFactory -> candidate
  `libqgtk3.so` -> system `gtk_init`/`gtk_init_check` -> system GDK display
  initialization -> `g_settings_get_enum` -> fatal settings-schema lookup.
  Debugger exit 0 means GDB completed its diagnostic commands, not Qt startup PASS.
- The library list identifies candidate-owned Qt/PySide/Shiboken and Ubuntu
  `/usr/lib/x86_64-linux-gnu/` GTK/GDK/GIO/GLib providers. It also records a dconf
  settings module from the editor's Snap cache. No conflicting runtime Qt provider
  or Qt ABI/private-symbol error appears in this captured failure.
- In that owner's inherited environment, GSETTINGS_SCHEMA_DIR is set. Read-only
  schema-key queries succeed but expose none of the three modern font keys and
  none of the old xsettings font keys. The modern keys are present when inspected
  through Ubuntu's system schemas. This explains GTK's legacy fallback and its
  invalid key lookup. GLib documents that schema discovery depends on
  [GSETTINGS_SCHEMA_DIR and XDG_DATA_DIRS](https://docs.gtk.org/gio/type_func.SettingsSchemaSource.get_default.html).

**Confirmed diagnosis:** a GTK/GSettings schema-visibility mismatch in the inherited
editor launch context, during QApplication construction, before renderer creation.
The actual Qt/GTK/GIO call chain is now captured, consistent with the
[Qt GTK3 theme initializer](https://github.com/qt/qtbase/blob/6.11/src/plugins/platformthemes/gtk3/qgtk3theme.cpp)
and [GTK 3.24.52's Wayland font-settings fallback](https://github.com/GNOME/gtk/blob/3.24.52/gdk/wayland/gdkscreen-wayland.c).
The exact inherited schema-directory value was intentionally not logged; the
record does not prove which editor packaging component introduced it. A bounded
attempt to inspect live editor processes could not see their environment in this
confined process view. No claim of an exact Snap revision regression is made.

## Narrow N1 diagnostic correction

`run_probe.py` now offers explicit `--ubuntu-system-schemas`. It selects
`/usr/share/glib-2.0/schemas` only in the probe child's copied environment. It
verifies OS ownership/non-writability, compiled-schema identity/stability and the
three modern font keys before launching Qt. No setting values are queried or
changed. The schema check is bounded to 3 seconds. Filesystem-root ownership is
compared rather than assuming numeric UID 0, because this confined view maps the
OS owner to overflow UID 65534; the invoking user is never accepted as OS owner.

The default command retains its original filenames and refusal to reuse previous
outputs. The explicit mode uses only new candidate-local result paths:
`owner-system-schemas-result.json`, `owner-system-schemas.private.log` and
`owner-system-schemas.json`. The actual renderer child `sandbox_probe.py` remains
byte-identical (`70ad934d0bb9fe4c09e5978526969c63c6ba71b660335619da896fe1bd4844b3`). All namespace,
NoNewPrivs, seccomp, helper/provider identity, private-profile and receipt checks
remain required. No sandbox flag is removed or added, no alternate theme forced,
and no backend/authentication/data safeguard changed. Unsafe inherited flags remain
visible for the existing configuration checks to reject.

The correction is limited to N1 tooling; the candidate, receipt, dependencies,
launcher and packaged application sources are unchanged. It is not yet a validated
production launcher correction. A later native launch design can reuse the tested
selection only after real host verification. No N2 implementation is included.

Supervisor SHA-256: `3cb946c87a959589816f88fe6b3d2895be4919b48357b8fc67956b4779c60a14`.
**33 N1 tests PASS: 17 existing + 8 startup-diagnostic + 8 schema-selection tests.
Ruff and formatting PASS.** The new tests include real GLib queries against a
synthetic old-schema overlay: missing modern keys are reproduced, then system
schema selection restores their visibility. Other coverage checks OS protection,
missing/changed schemas, query failure, immutable historical outputs, explicit
fresh outputs, unchanged parent environment/unsafe-flag rejection and refusal to
promote an incomplete renderer result to PASS. Initial local ownership-guard
failures were corrected for the observed UID mapping; the final full 33-test run
passes. No Qt/GUI/renderer execution or application rebuild was performed here.

**Next owner action:** one corrected renderer-security probe using the fresh
explicit mode in P6_OWNER_CHECKS.md. It remains 25 seconds plus up to 10 seconds
cleanup, with at most 3 additional seconds of schema preflight. No application
window is expected. Its result must be reviewed; even a probe PASS is not full
N1 acceptance or authority to start N2–N4. No host environment, normal installation,
AppArmor setting, personal data, Git ref or accepted P1–P5/R11/R12 evidence changed.

---

# Historical initial 3 November investigation — retained before the startup result

The earlier uncertainty and already-executed startup handoff below are historical;
the captured stack and current correction above supersede them. Do not rerun the
startup diagnostic or the original renderer command.

# Current N1 investigation — 3 November 2026

**N1 — Experiment built; owner-host renderer probe BLOCKED. Native feasibility
is not accepted.** The current target remains native Ubuntu x86_64 / GNOME Wayland
with the existing PySide6/Qt interface, versioned GitHub Releases archives and the
N1–N4 roadmap. Flatpak remains paused/fallback history, not a parallel release gate.
N2–N4 are planned and unauthorized. The ordinary-user filesystem/network tradeoff
is already accepted; MIT is selected for original code. No additional license,
branding, AppArmor or host-security decision is inferred.

The owner's issued probe actually ran: `owner-sandbox-result.json` records BLOCKED,
complete true, exit -6, 1.369 seconds and normal application launch NOT EXECUTED.
The receipt, original probe and private-log hashes match that owner result. The
157-byte log reports a fatal GLib/GIO settings-schema lookup for `antialiasing` in
`org.gnome.settings-daemon.plugins.xsettings`. This is not renderer-isolation
failure evidence: there is no successful owner sandbox diagnostic or application
launch result. The previous confined renderer failure remains a separate result.

Focused read-only findings:

- The pinned candidate's `libqgtk3.so` is from PySide6 Essentials 6.11.3,
  SHA-256 `6ea4469ff5f0469aa901edf1f1df670c4cf3819efd6976667c8739c97e2dac33`.
  Its ELF dependencies include host GTK3/GDK/GIO and its imports include `gtk_init`;
  the wheel records contain no bundled GTK/GDK/GIO libraries.
- Installed Ubuntu packages: GTK3 3.24.52-0ubuntu1, GLib 2.88.0-1ubuntu0.1,
  gnome-settings-daemon-common 50.0-1ubuntu1. These are local installed identities,
  not a record of which libraries the failed owner child loaded.
- The [Qt 6.11 branch's GTK3 theme constructor](https://github.com/qt/qtbase/blob/6.11/src/plugins/platformthemes/gtk3/qgtk3theme.cpp)
  calls `gtk_init`. The exact v6.11.3 source URL was unavailable during this review;
  the candidate binary's direct GTK import was independently inspected, rather
  than treating the branch source as an exact candidate-source identity.
- [GTK 3.24.52's Wayland `update_xft_settings`](https://github.com/GNOME/gtk/blob/3.24.52/gdk/wayland/gdkscreen-wayland.c)
  prefers modern desktop-interface font keys; its fallback reads `antialiasing`
  from the old xsettings schema. This identifies a matching source path, not a
  captured stack trace of the owner failure.
- Installed schemas have the modern font keys; the old xsettings schema lacks
  antialiasing/hinting/rgba-order and those legacy keys are in a deprecated schema.
  Read-only GIO key-presence checks in two separate local processes (inherited
  Codex environment and explicit system-schema search path) both confirm the modern
  keys are present. Neither check accesses a desktop, reads preference values or
  reproduces the failed owner's environment. No mixed-library/Snap cause is proven.

**Remaining uncertainty:** the old log has no backtrace, provider map or effective
schema search context. It cannot establish whether Qt's GTK theme, another GTK
caller, different loaded GTK/GLib libraries, or inherited schema discovery caused
the observed fallback. No speculative theme override, dependency upgrade, schema
repair or production application correction has been applied.

A separate owner-only `diagnose_startup.py` is prepared. It uses the same reviewed
candidate and original receipt, preserves the original probe and its outputs, and
writes only a fresh `ci-output/p6-native-n1-startup-1/`. It reads only schema key
names, then runs Qt imports/QApplication construction under offline GDB; it creates
no WebEngine profile/page/renderer, CyrNava window or backend, and runs no event loop.
The child uses fresh diagnostic XDG data/config/cache paths. GDB initialization
scripts, automatic script loading, debuginfod downloads and core dumps are disabled.
Private output is capped at 2 MiB; tracing is bounded to 20 seconds, schema reads to
2 seconds each and emergency owned-group cleanup to 5 seconds. Host settings,
renderer sandbox rules, application payload and dependency locks remain unchanged.

Diagnostic SHA-256: `4648888d2129f8193402062e3b22a1ca45690d5c07e04e1b7989b16e2f9d6392`.
**Verification: 25 offline N1 fixtures PASS (17 existing + 8 diagnostic fixtures);
Ruff and formatting PASS.** No Qt import/GUI/renderer execution was used in these
fixtures. Guard coverage includes changed receipt/evidence, preserved outputs,
symlinks/wrong paths, restricted debugger setup, value-free schema reporting,
startup-only execution, inherited resource limits, deadline cleanup and refusal to
promote diagnostics to renderer/N1 success. No application/backend suite was rerun:
application behavior is unchanged and its earlier scoped evidence remains historical.

**Next owner action:** the single startup diagnostic in P6_OWNER_CHECKS.md, then
review its result before deciding on a correction or another renderer execution.
This is not a replacement renderer test or N1 PASS. No native diagnostic has been
executed by the agent. No rebuild, installation, host-security change, cleanup,
Git operation, publication or N2–N4 implementation occurred.

---

# Historical pre-execution status — retained 2 November wording

The pending-only status and issued probe below predate the owner result above.
Keep the original command/evidence unchanged; do not rerun that command.

# Current native-release checkpoint — 2 November 2026

**N1 — Experiment built; owner-host renderer verification pending.
Native feasibility is not yet accepted.** The owner will run the already-issued
probe in the morning, Korea time; no owner-host result has been supplied. Further
development is on hold pending review. N2, N3 and N4 remain planned and are not
authorized to begin.

The release target is the native Ubuntu x86_64 / GNOME Wayland desktop application
with the existing PySide6/Qt interface, distributed as versioned archives through
GitHub Releases. The shared installation engine and shell entry points remain
proposed. The active roadmap is N1 — Native Qt feasibility; N2 — Versioned installer
and desktop integration; N3 — Data-safe manual updater and uninstaller; N4 — Native
CI integration and public-release preparation.

Flatpak is paused and superseded for this target, retained as fallback/history.
Its HTTP acquisition, runtime restoration, OSTree publication and package-specific
checks are not native prerequisites. Legacy P6 filenames are documentation
containers, not an additional Flatpak acceptance phase after N1–N4. General
installation, compatibility, data, security, redistribution and trusted-distribution
requirements are addressed within N1–N4.

N1 implementation and the ordinary-user filesystem/network privilege tradeoff
are already authorized. Renderer sandboxing, backend authentication and data
protections remain required; host-security changes and AppArmor integration are
separate decisions. MIT is selected for the original code; copyright-holder
attribution, branding rights and third-party obligations remain separate. No
license-file changes are part of this terminology update.

Actual experiment: `ci-output/p6-native-n1-1/`, private Python3.14, matched official
PySide/shiboken/Qt/WebEngine6.11.3. The receipt SHA-256 is
`7f713ed31e2ce7d63a1a67e806d671b38ff2f7bafd2d66592f68ff70d575c41e`;
launcher SHA-256 `433928adca59ca511b8b4c189dff51472197573d7267f8ddb8268b1c82cd94d1`.
Source base remains bfa0b8005a3ddc519354fd7907e9b972fde8126b plus the recorded
uncommitted application/configuration snapshot; this is NOT accepted A/B or a
release package. Keep the candidate at its final path; the venv is not relocatable.

| N1 gate | Actual result and limit |
| --- | --- |
| Matched binaries/imports/provider/ELF closure | PASS: all four versions6.11.3; 3,920 installed wheel hashes verified; selected ELF dependencies resolve; loaded Qt is private; binding and Core provider both expose QtPrivate_6_11_3 |
| Authenticated owned backend and synthetic persistence | PASS on actual target Python3.14: wrong credential/origin rejected; folder/rich note/raster image saved; restart preserves data/origin and changes/revokes token; child reaped |
| Minimal local HTML/JavaScript | PASS offscreen, supplementary only; not the existing CyrNava window, pixels/clipboard or GNOME Wayland verification |
| Required renderer sandbox | FAIL in this confined offscreen run: Layer1 None; PID/network namespaces No; all observed namespace separation false. Matching helper reports NoNewPrivs1/Seccomp2; seccomp alone cannot pass |
| Normal CyrNava window, Wayland and GUI save/clipboard/reopen | NOT EXECUTED; do not proceed to a full editing exercise before the focused host security check |

The parent context is bwrap//&unpriv_bwrap. Graphics stderr contains DRM permission
errors, not evidence identifying the namespace failure's cause. Actual ordinary
Ubuntu/AppArmor/Qt responsibility remains unproven. No AppArmor profile, sysctl,
sandbox flag, signature check or filesystem/network permission was changed.

Implementation: seven-line explicit native-N1 build dispatch in
`desktop/native/application.py`; the default Flatpak identity and all old checks
remain. Separate `packaging/native/feasibility/` recipe, hash locks, configuration,
provider/ELF verification, bounded renderer probes, target-backend check and fixtures.
The native configuration exists only in the N1 assembled payload, outside the
production source allowlist. Existing production packaging tests still pass.
Frontend was built from copied source with existing pinned tools/dependencies,
leaving current frontend/dist/node_modules unchanged. No global dependency install.

Assembly43.274s; wheels267,053,918 bytes; initial allocation1,010,987,008 bytes;
final experiment about1.014GB, below3GiB cap, with about20.2GiB still free. Maximum
assembly child RSS565,076KiB is not a combined GUI/host memory peak. No Qt/Chromium
source build or duplicate runtime/SDK acquisition occurred.

Verification: **17 N1 fixtures PASS;147 relevant existing application/security/
migration regressions PASS;36 production packaging regressions PASS; new-file
Ruff PASS.** Existing pytest suites use the developer Python3.12 environment;
the separate real target-backend check and provider/import checks use3.14.
Initial probe results/raw logs and pre-hardening receipt/config remain preserved;
final provider check passed after helper-path guard hardening. The improved owner
probe is fixture-verified and has not executed on Wayland. No production native,
menu/update/recovery or release PASS is inferred.

**Existing owner handoff, unchanged:** one25-second Wayland renderer-security probe in the
normal Ubuntu terminal, with up to10 seconds for cleanup. No visible CyrNava window
is expected, no data editing and no downloads/installation/security change. Exact
command and effect boundaries: [N1 handoff](../packaging/native/feasibility/README.md).
It refuses existing owner outputs. Share only owner-sandbox-result.json; keep raw
private logs local. The owner will run this issued probe in the morning, Korea
time. Review its result before proposing or performing further development. A
probe PASS would cover only that probe, not complete N1 or authorize N2–N4. The
confined renderer result does not establish a normal-host failure. No replacement
command or probe-input change is made.

Safe source/results: `ci/evidence/p6/native-n1-2026-11-02/summary.json`.
P1–P5 decisions, all approved A/B identities, R11 component passes/R12 PASS, old
failures and unresolved observations remain intact. No normal installation, real
profile migration, Git write, Actions execution, key creation or publication.

---

# Historical checkpoints — preserved records

The sections below retain their original wording, results and acceptance records
for their original artifacts and execution environments. Their older status,
license-selection questions, Flatpak gates and execution requests are historical;
the current native terminology and development hold above govern. P1–P5 acceptance
and R11/R12 evidence remain preserved and do not certify a new native package.

# Current P6 status — native Linux investigation, 2 November 2026

**P6 CONDITIONAL. Native route: VIABLE IN PRINCIPLE / READY FOR BOUNDED FEASIBILITY;
no native feasibility PASS or replacement package is claimed.** The requested
assessment is complete in [P6_NATIVE_DISTRIBUTION_ROADMAP.md](P6_NATIVE_DISTRIBUTION_ROADMAP.md),
including verified Ubuntu26.04.1 x86_64/GNOME Wayland/Python3.14 baseline, file-level
reuse matrix, security tradeoff, N1–N4 milestones and the N1-only implementation prompt.
Next decision is bounded N1 authorization: matched official Qt/PySide wheels,
actual provider/sandbox proof and minimal synthetic persistence before installer work.

Flatpak acquisition diagnostics, alternate-network commands and upstream escalation
in all earlier P6 documents are **PAUSED during this investigation**. Preserve that
route, accepted P1–P5 records, R11/R12 and all historical failures. This checkpoint
changes documentation only; no code, dependencies, installations, tests, workflows,
Git refs, personal data, signing or publication changed. Earlier sections below
retain their original evidence and then-current instructions, not active authority.

---

# P6 current checkpoint — host HTTP review, 2 November 2026

**P6 CONDITIONAL. Acquisition unresolved; no replacement candidate exists.** This
checkpoint supersedes the earlier request to repeat the default host diagnostic.
The original host run and failed acquisition remain unchanged. No further object
GET, acquisition/build, native rehearsal, host change, signing, Git write or
upstream contact was performed during this review.

## Zero-request ValueError: existing-output protection, not a new network failure

The default output `ci-output/p6-http-owner-1` already exists. `new_output()` in
http_probe.py raises `ValueError("Fresh direct ci-output/p6-http-owner-* path required")`
before the version subprocess, directory creation or HTTP requests. `root` is
still None, so the finalizer prints an incomplete result but does not overwrite
the existing result.json. Both required tools are present. A local reproduction
with subprocess entrypoints mocked produced exit 1 / ValueError / requests=[] and
zero subprocess calls; all original host files kept identical hashes. The owner
repeat's own timestamp was not retained; the reproduction is separately timestamped.
There is no reason to weaken the fresh-output guard or rerun the default command.

Original host diagnostic: started **2026-11-02 10:08:32.559289 UTC**, duration
0.151s, DIAGNOSTIC_COMPLETE; acquisition_verified=false. Its result SHA-256 remains
`8d7397919688073013930124b02d05879298c357a608e5110270eda424df0b6a`.

## Consolidated retained HTTP evidence

All times below are actual response Date headers on 2 November, not the later
JSON-report creation time. All six responses use HTTP/2, without advertised redirects.

| Environment | Default curl | libostree/2025.7 identification | Clean environment curl |
| --- | --- | --- | --- |
| Codex | 09:55:04 UTC / 200 | 09:55:34 UTC / 403 | 09:55:34 UTC / 200 |
| Ubuntu host | 10:08:32 UTC / 200 | 10:08:32 UTC / 403 | 10:08:32 UTC / 200 |

All 200 bodies are 5,020 bytes, SHA-256
`fb23e178d082b117df7924f9a84710992ec233ebc007385feb85d349c4c81415`.
Both refusals are 420-byte Varnish HTML, MISS, one Via hop; their hashes differ
(Codex `367a78224de90bc2518abb57a61818b0c495749f4b1671852e7b345c66118f1a`,
host `bc5f0f8b34907bd541e593447b7b9b1a4115dcb854b137e406d228ed5c895b33`).
Success reports nginx, HIT/HIT and two Via hops. Host TLS verification is 0 in
all cases. No checked host proxy/CA override variables were present; no inference
about VPNs, transparent intermediaries or host-wide configuration follows.

The first two helper calls intentionally differ only in --user-agent; URL,
options and inherited environment match. Local output filenames do not affect HTTP.
The clean comparison changes PATH, locale and HOME as well as removing inherited
variables. Host curl version, executable identity and default identification were
not captured. Calls use separate connections in fixed order; peer/client addresses,
IPv4/IPv6, DNS, TLS details and all actual transmitted headers were not captured.
Different ICN cache nodes served the success and refusal responses (listed in the
safe evidence). Thus header-sensitive refusal is strongly supported, but **User-Agent
as the only material cause and the exact responsible rule/operator are unproven**.
The native OSTree request's full headers/transport remain unknown; a curl request
with the same identification is not a byte-for-byte native-client reproduction.

Earlier exact-object hash, official advertised ref, GPG verification and signed
ref-binding remain valid recorded evidence. Successful metadata checks established
identity and metadata availability, not complete dependency download or ABI success.
No newer ref, artifact, signature policy or acquisition identification was substituted.

## Supported methods and smallest next action

[Official Ubuntu setup](https://flathub.org/en/setup/Ubuntu) uses the trusted
Flathub descriptor and normal Flatpak client. Metadata success does not prove that
switching this driver to another normal client will fix full acquisition.
[Flathub's network guide](https://docs.flathub.org/docs/for-users/slow-connection)
suggests another network and links an infrastructure issue template. Its general
[troubleshooting guide](https://docs.flathub.org/docs/for-users/troubleshooting)
asks for reproduction/version evidence and privacy review. No documented official
403 workaround was found that conclusively resolves this case. Do not perform
repair, DNS changes, global remote changes or identity masking without evidence.

Optional ONE comparison, only if the owner independently chooses another trusted
network path (for example an available hotspot); the script changes no network settings:

```bash
cd /home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
bash p6_http_diagnostic.sh --output "$PWD/ci-output/p6-http-owner-alt-network-1"
```

This supported output option selects a verified-absent fresh location, preserving
owner-1 and candidate-1. It makes three bounded GETs of the same exact reviewed URL,
using authentic libostree/2025.7 identification for the comparison; no build/pull/GUI.
An alternate-path change would identify a path-related condition, not prove the
normal native client can acquire the full dependency closure. Keep raw files local;
share result.json only. No automatic retry or build continuation follows.

The smallest external action is owner review of the sanitized, reproducible draft
`ci/evidence/p6/http-host-review-2026-11-02/upstream-support-draft.md`, followed by
an owner-authorized infrastructure report if desired. No report has been submitted.
The upstream dependency is delivery of the exact trusted runtime/SDK/BaseApp commits
through the supported client, not a missing CyrNava application feature.

A conditional alternative retains Flatpak: [official offline sideloading](https://docs.flatpak.org/en/latest/usb-drives.html)
from a trusted machine holding the exact approved refs and required signed metadata,
with collection-ID/receiving-remote prerequisites verified. No such complete source
has been established here; it is not a ready substitute. Any transfer/import needs
review and must preserve exact commits and normal signature checks. [Application
bundles omit runtime dependencies](https://docs.flatpak.org/en/latest/single-file-bundles.html),
so hosting CyrNava on GitHub alone cannot remove this requirement. No alternative
.deb/AppImage/wheel stack has passed ABI and renderer-isolation checks; proposing
one as ready would be unsupported. The large source build stays deferred.

## Verification and preservation

18 offline fixtures PASS, Ruff/helper tests PASS, Bash syntax PASS. No helper or
acquisition-driver code change was needed. All 355 existing indexed evidence hashes
matched before documentation updates; original host/private and previous Codex
private hashes were independently verified unchanged. Safe consolidated review:
`ci/evidence/p6/http-host-review-2026-11-02/review.json`.
All six release gates, accepted artifacts, R11/R12 observations, resource limits and
owner authorization boundaries remain unchanged. **Stop before another acquisition
or native execution.**

---

# Previous diagnostic checkpoint — host-comparison command below is historical

# P6 current checkpoint — normal-host HTTP refusal, 2 November 2026

**P6 CONDITIONAL. No replacement candidate. Do not retry acquisition/build yet.**
Owner attempt `ci-output/p6-binary-candidate-1` is retained unchanged: namespace PASS,
trusted remote/key checks PASS, all four exact advertised identities matched,
then raw OSTree `pull-0` returned HTTP 403 in 7.055 seconds. Normal-host execution
has therefore resolved the namespace prerequisite; “run outside Codex” is not an
adequate explanation or next step for this failure.

## Bounded download diagnosis — actual observations

The driver constructed the correct official URL from the approved SHA. Its isolated
remote is https://dl.flathub.org/repo/, with commit and summary GPG verification
true, matching reviewed public-key hash and no configured alternate content URL,
proxy or mirror. All seven retained operation-log hashes match their records.
Successful ref checks established advertised identity, not payload availability.
No response headers/body or redirect trace were retained in the failed pull itself.

A separate small read-only HTTP comparison now establishes:

| Controlled request to the exact runtime commit URL | Response |
| --- | --- |
| Default curl identification, TLS verification enabled | 200; 5,020 bytes; SHA-256 fb23e178d082b117df7924f9a84710992ec233ebc007385feb85d349c4c81415 |
| Default curl with the driver's stripped environment | Same 200 and exact hash |
| curl identifying as installed libostree/2025.7 | 403; Varnish response |
| curl identifying as libostree/2025.7 flatpak/1.16.6 | 403; no acquisition workaround adopted |
| curl truthfully identifying CyrNava plus libostree, in either order | 403 |

No redirect was advertised in these controlled responses. Denial headers identify
Varnish, while the successful response passes through the repository CDN and nginx.
This is a confirmed User-Agent-sensitive refusal on the tested HTTPS delivery path;
the exact rule/responsible CDN operator or intermediary is NOT established. Do not
infer VPN/proxy involvement or claim the origin's internal policy has been inspected.
No proxy variables were set in this Codex environment; that says nothing about the
owner terminal. Clean-environment success rules out stripping those variables as
the cause of THIS controlled curl result only.

The descriptor still points at the reviewed endpoint. Fresh official ref readback
advertises the same runtime SHA. Directly downloaded commit bytes match that SHA;
its separately fetched official commitmeta passes `ostree show --gpg-verify-remote`
using the approved upstream public key, and signed ref-binding names exactly
runtime/org.kde.Platform/x86_64/6.11. Parent remains 76fa01ac42ecf45d2c5020ef80de1c474c0c2ae86a51a79e8fec44c48f9dc473.
Thus this commit is available and correctly bound; no newer commit was substituted.
These metadata-only checks in a new diagnostic repo do NOT establish a complete
runtime payload acquisition or candidate compatibility. No namespace, build,
installation, GUI, source-build fallback, signing key or publication was executed.

Raw headers/bodies/private logs remain under ignored ci-output/p6-http-diagnosis-1
with private permissions. Safe evidence: ci/evidence/p6/http-refusal-2026-11-02/diagnosis.json.
No acquisition-driver defect is established, so the driver and all dependencies,
TLS/GPG/expiry/hash checks remain unchanged. Do not spoof a browser/curl identity
or weaken verification to get a build through an unexplained refusal.

## One smallest host comparison — not a build continuation

```bash
cd /home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
bash p6_http_diagnostic.sh
```

Reviewed implementation: exactly THREE GETs of the same 5 KiB commit, no retries,
redirect following or installation. Each request has a 5s connection/15s transfer
limit and 1 MiB size limit. Compares default curl, libostree identification, and
clean-environment curl. Creates NEW ci-output/p6-http-owner-1; refuses an existing
or symlinked output. Reports status, allowlisted headers, body digest and only
presence of proxy/CA environment variables, never their values or raw body/headers.
Share only result.json. It neither reads nor changes candidate-1 or normal Flatpak
state. No native preparation/GUI/build or signature bypass occurs.

If the host reproduces 200/403/200 with matching object hashes, the smallest external
action is an upstream/CDN support review of the libostree-identified request refusal.
Provide the exact official URL, UTC diagnostic time, client versions, status/header
summary and immutable hash proof; do not send private headers/environment. No support
message was sent by the agent. If the host differs, compare its three observations
before attributing a cause or modifying the acquisition environment.

No build continuation command is issued: raw acquisition is not shown to work.
Once resolved, any continuation must use the builder's existing supported --output
option with a NEW audited path, never candidate-1. No new option is invented.
Focused offline tests: **18 PASS (14 existing +4 diagnostic)**; Ruff, Bash syntax
and --help PASS. No application/full-suite/native rerun was needed for this diagnosis.
The six v0.1 gates remain as below, with gate B now blocked by this delivery refusal,
not by host capacity or the already-passed normal-host namespace probe.

Primary implementation references: [OSTree fetcher](https://github.com/ostreedev/ostree/blob/v2025.7/src/libostree/ostree-fetcher-curl.c),
[Flatpak client](https://github.com/flatpak/flatpak/blob/1.16.6/common/flatpak-dir.c),
[remote security configuration](https://ostreedev.github.io/ostree/man/ostree.repo-config.html).

---

# Earlier P6 checkpoint (prior execution advice superseded above)

# P6 — current reduced v0.1 release checkpoint

**2 November 2026 — BLOCKED at native namespace/acquisition prerequisite; P6 CONDITIONAL.**
No replacement candidate exists. `p6_binary_candidate.sh` is implemented and locally
tested for the owner terminal. It performs one bounded, isolated binary acquisition
and thin build only when prerequisites pass. No new binary fetch, application build,
GUI run, cleanup, Git write, signing or publication was executed in this checkpoint.

| Six v0.1 gates | Current state and evidence | Remaining action |
| --- | --- | --- |
| A. Ubuntu 26.04 LTS x86_64 / GNOME Wayland clean install and normal desktop launcher | PENDING; accepted P4 and R11/R12 apply only to their historical bytes | Install the actual new exported candidate with normal dependencies, normal entry/menu/name/icon, close/relaunch |
| B. Supported coherent Qt/PySide/shiboken/WebEngine | BLOCKED; four owner-pinned inputs retained in separate candidate.lock.json. Prior Codex object 403 and namespace denial preserved, not retried | Owner-run reviewed binary entry point; actual versions/maps/ELF/resources/private-symbol closure then native renderer. Matching versions are not proof of removal of private-ABI coupling |
| C. Final-package data/recovery | PENDING for new bytes; R11 component passes/R12 targeted PASS preserved. Current source/browser persistence/recovery regressions pass in their stated scope | Focused synthetic note/folder/rich text/image/offline/restart/backup-import/schema/reinstall checks; respect fresh post-import preferences |
| D. Existing application security | Baseline unchanged; current source backend/security and browser checks passed up to the separately reported combined-suite stop | Actual replacement-renderer namespaces/seccomp/NoNewPrivs plus normal packaged origin/navigation/bridge/external-link/file/private-loopback checks |
| E. Identifiable lawful distributable | BLOCKED; unsigned candidate absent; code/branding decisions unresolved; notices/source arrangements need actual shipped inventory | Final source/patch/dependency identity, actual notices and exact corresponding-source/attribution review; no invented rights |
| F. Signed bundles on GitHub Releases, manual install/update | PENDING; established channel accepted; no authentic production signing identity or release authorization | Owner approves signing/source/publication, sign final bytes, clean-client/manual-update verification and later public download-back checks |

## Actual preflight and baseline

Local integration HEAD and independent GitHub connector readback both remain
`bfa0b8005a3ddc519354fd7907e9b972fde8126b`. Remote main is
`4021bc292267c19b7ebebf219b4f682f8f99bf4c`. No refs/index or existing source work
were changed. Accepted P5A/P5B/P5C remain accepted; detailed P1–P5 matrix below retains
its actual report/evidence identities. No completed phase is reopened.

Measured persistent repository/output mount: **/dev/nvme0n1p5, ext4**, not the owner's
partition-number assumption. Initial available **23,037,739,008 bytes (21.46 GiB)**.
/tmp is tmpfs and is excluded from candidate build/cache/export/temp. RAM ~16 GB,
available ~3.69 GB; swap ~4 GB and nearly full. No source compilation, parallel build
or swap/host change. Bounds remain 9 GiB free / 7.5 GiB added / 1.5 GiB headroom /
one job / 60 minutes. Polling stops at limits; it is not a filesystem quota and a
single write may cross a sampled threshold. No silent budget expansion is allowed.

All twenty exact cleanup targets are now absent. No owner final cleanup transcript
was found, so neither exact reclaimed space nor the cleanup executor is inferred.
This task did not invoke cleanup or delete retained work. The old 3.49 GiB and
pre-cleanup projections in historical text below are superseded by measurements here.
The same Codex process remains under the recorded namespace/AppArmor restriction;
its denied namespace operation and pinned-object 403s were NOT repeated. Owner-host
namespace and exact-ref checks are first in the new procedure, before large work.

## Implementation and actual verification

New Bash entry point: `p6_binary_candidate.sh`. New recipe, lock, provider/ELF probe
and regressions: `packaging/flatpak/compatibility/binary-6.11.3/`. Uses unchanged P4
stage/assemble/finish, payload audit and P5A exported-bundle auditor; no historical
A-only signing-policy change. Production manifest/locks/permissions/source untouched.
The new recipe removes no WebEngine bindings/helper/resources/locales, uses no Qt
wheel swap and does not build Qt/Chromium. Failure logs remain private and structured
operation/category diagnostics are sanitized. Any generated candidate is unsigned.

- New candidate driver/provider policy: **14 tests PASS**, including mismatch,
  wrong key/policy, moved ref, namespace/signature stop, isolated environment,
  missing resources/provider, sandbox-disablement, private-log diagnostics and
  no promotion of import success to renderer/release success. These are fixtures.
- Bash syntax/help and Ruff: **PASS**. ShellCheck unavailable; not installed.
- Frontend lint, **273 unit tests**, TypeScript: **PASS**.
- Production-mode Playwright: **21/21 PASS**, one worker, zero retries; isolated
  synthetic profiles, output under ci-output/p6-resume-tests/browser-results.
- Combined backend/security/lifecycle/migration/packaging/workflow/release run on
  verified persistent external fixtures: **587 tests +45 subtests PASS, one setup
  ERROR** at disposable GPG key initialization in
  `test_distribution.PublicationTests`. Remaining combined-suite tests unexecuted;
  this is NOT a complete-suite PASS. No signing or fixture security bypass.
- Two preceding regression attempts are retained: wrong in-repository fixture
  location rejected by application storage protection (stopped); outside-directory
  request was not writable, fallback /tmp caused the existing 5 GiB builder check
  after **580 tests +31 subtests PASS**. Correct persistent test placement passed
  that check. These are not application/Qt launch failures or rewritten old results.

Safe evidence: `ci/evidence/p6/resume-2026-11-02/`. Raw test traces/logs and JUnit
records with local paths remain in ignored ci-output/p6-resume-tests, not a public
upload proposal. No new renderer/installed-package/update/native PASS is claimed.
Old R9 missing-object observation remains unexplained. Prior R11 overall FAIL and
R12 exact B-only historical-runtime PASS remain unchanged; ordinary compatibility
of those old bytes remains false. No historical credential is extended/reused.

## Smallest next owner action

Run ONE reviewed command from the Ubuntu terminal:

```bash
cd /home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
bash p6_binary_candidate.sh
```

It creates only `ci-output/p6-binary-candidate-1` and stops if it exists. No GUI,
normal installation, secret key or publication. Share its result.json/sanitized
failure category, not private logs or the whole tree. On upstream movement/403,
namespace/signature/provider/resource failure stop; no automatic retry or alternate
version. Recipe README describes measured/estimated storage and all effect boundaries.
After a candidate actually exists, bind a focused native handoff to its real bundle
hash/commit. No candidate GUI command or fabricated checksum is supplied now.

## Consolidated owner decisions and release material

P6_OWNER_CHECKS.md contains the one remaining decision package; existing AppStream
CC0-only approval, production application ID, single-maintainer model and GitHub
bundle channel are retained. P6_RELEASE_RUNBOOK.md contains the prospective asset,
source/CI, signing, install/manual-update and download-back steps. No release source
or production fingerprint has been invented. Corresponding-source arrangements and
use-composed-ref attribution remain specific redistribution issues, not optional
warnings. Final package inventory is generated from actual exported bytes on success.

All cloud gateways/automatic updates/large source builds/platform expansion remain
deferred. The deadline does not close any pending gate. **P6 remains CONDITIONAL.**

---

# Historical P6 checkpoint and evidence (superseded operational instructions)

# P6 — v0.1 release assessment and repository cleanup

**2 November 2026 — P6 CONDITIONAL. Bounded binary evaluation completed; thin build BLOCKED.**
The six owner-defined gates below are the only v0.1 release gates. No custom cloud,
update server, broad platform matrix, new feature, enterprise compliance pipeline
or Qt/Chromium source build is required or being resumed. This checkpoint includes
actual remote metadata inspection, two failed bounded object fetches, a namespace
probe, artifact rehashing and local regressions. It is not just a proposed plan.
No new candidate exists, so there is no new bundle path, checksum, installed commit,
release signature or native-package PASS to report.

| Gate required for v0.1 | Evidence already satisfied for its actual input | Current remaining blocker | Deferred |
| --- | --- | --- | --- |
| 1. Ubuntu 26.04 LTS x86_64 / GNOME Wayland clean install and normal desktop launcher | P4 remains owner-ACCEPTED; historical R11/R12 GUI evidence retained. Host reports Ubuntu 26.04.1 and Wayland. | Final replacement package absent. Codex namespace creation denied despite Wayland environment variables; normal application-menu launch is unexecuted. | Other platforms/architectures/sessions |
| 2. Coherent maintained Qt/PySide/Shiboken/WebEngine | New signed-remote metadata identifies exact 6.11.3-recipe BaseApps and runtime/SDK commits below; old private-ABI defect is independently established. | Both pinned object downloads returned HTTP 403. New binary versions/ELF/provider closure, imports and renderer remain unverified. Cold-client budget also exceeds available disk, even after proposed cleanup. No historical restoration remedy. | Large source build; arbitrary-future-runtime certification |
| 3. Data and recovery in final package | R11 editing/restart/initial B update/rollback/backup-import/recovery component PASS; R12 targeted PASS, owner-result SHA ef771b4014432d4498d15d1e8c73ece4a557e504b893c9d60f446ac2baa14537. Current 107 targeted backend security/data tests PASS. | Focused new-package notes/folders/editor/image/offline/restart/backup/restore/future-schema checks await the new package. R9 exact missing object remains historically unresolved; R11 overall FAIL unchanged. | Full old A/B rehearsal without a changed input/regression |
| 4. Existing basic security | Accepted authentication/Host-Origin/private-loopback, path/image/data-isolation controls retained; local security tests PASS; R12 historical renderer assertions retained. | Actual replacement renderer namespaces/seccomp/no-new-privileges, navigation/origin/bridge/external-link/file boundaries must be exercised. No disabled sandbox or permission expansion. | New enterprise security infrastructure |
| 5. Identifiable distributable with branding/licenses/notices/sources | Exact accepted package identities rehashed; production manifests/lock/auditor and uncommitted work preserved. Existing notices and licensing assessment retained. | No final package. Owner code-license/holder and logo-rights decisions, actual shipped dependency notice/source correspondence and attribution gaps still require resolution. No production signing identity is recorded. | Exhaustive SBOM machinery or byte-reproducible-build certification |
| 6. Signed bundles on GitHub Releases; documented manual install/update | Accepted P5A CI, P5B signing and P5C isolated install/update primitives retained. Flatpak command syntax checked against installed CLI and official docs. | Authentic final signature, clean-client acquisition/install and relevant manual update still unexecuted. Publication/production credentials remain separately authorized. No old ABI-broken package is claimed to pass an end-to-end ordinary update. | R2/S3/gateways, unattended update service, publication automation |

## P1–P5 reconciliation — current decisions, not stale chronology

The latest report headers, checklists and final artifact-specific records were read.
Earlier statements that P4/P5/P6 were not started describe their original dates.
They do not reopen accepted phases. P4 acceptance is preserved in full, with its
original distinction between owner attestation and independent machine evidence.
P1's original sandbox failure is not rewritten: P1B passed with a different native
artifact. P3's final record says verification PASS and owner visual confirmation;
no invented separate formal-acceptance JSON is attributed to it.

| Phase | Evidenced status | Source/artifact identity | Retained evidence | Cleanup decision |
| --- | --- | --- | --- | --- |
| P1 | Feasibility completed; original sandbox gate BLOCKED, followed by P1B acceptance on its own artifact | baseline cbf7ccc; ten native journeys; prototype source/evidence hashes retained | `prototypes/p1_desktop/REPORT.md`; `prototypes/p1_desktop/evidence/verification.json` | No prototype source/report/evidence deletion |
| P1B | PASS on tested Ubuntu/Wayland/x86_64; owner-native acceptance | installed de98d04b66fe89d4865afdaabbfc6ef1d9706cf92f526270ba45279404a975c9; actual PySide/Qt 6.11.2 | `prototypes/p1b_flatpak/REPORT.md`; `prototypes/p1b_flatpak/evidence/owner-native-results.json` | No accepted input/evidence deletion |
| P2 | ACCEPTED; final native portal PASS | run-64a7b56d5fc0; checkpoint 808e906dbe977edd4a20ec23f134ad565c54a675; corrected driver d4e5025c567074f7dc653b265e3429c2979e6bc5c70f0c9c6775fab251d8089b | `desktop/native/P2_REPORT.md`; `desktop/native/evidence/p2-final-2026-10-30/supervisor-result.json` | Regenerable listed bytecode only; final records KEEP |
| P3 | PASS; final supervised five-phase verification and owner visual confirmation | run-a2e0fcaea12a; helper 2695e2495ea5f056475bce86483b5ea76cd1bcc074b1c79cb672cec4852dc56b | `desktop/native/P3_REPORT.md`; `desktop/native/evidence/p3/final-native-2026-10-30/acceptance.json` | Regenerable listed bytecode only; migration tests/reports/evidence KEEP |
| P4 | ACCEPTED / CLOSED by owner, 2026-10-30; retain documented machine-evidence limitations | A e0529b136effc347a5f7a32b52d95ddd5fead5230410e752ce8eb8f9a4c35e19; bundle 856cc0ccd82bca263320e2d692a5b3d316543ae320cd76d9cd42bf42e54a3170 | `desktop/native/P4_REPORT.md`; `desktop/native/evidence/p4/closeout-2026-10-30/owner-acceptance.json` | Verified build/files extraction and listed packaging bytecode DELETE; exact P4 bundle/source/native evidence and parent kept |
| P5A | ACCEPTED / COMPLETE | source 1ee2077b283b8e5dfc2162119dd439ed3baeb109; CI 41181510439; artifact 13035607417; local accepted tag peels to 1a28f68c5732ccc1275403060e89ff168a846655 | `ci/P5A_REPORT.md`; `ci/evidence/p5a/hosted-provisioning-2026-10-31/owner-acceptance.json` | Accepted archive/reference and provenance KEEP |
| P5B | ACCEPTED / COMPLETE | tooling 3ea472efcd6c3338debe16161de601286a5f177d; staging 41265875118 attempt 1 SUCCESS; application source 1ee2077 | `ci/P5B_REPORT.md`; `ci/evidence/p5b/owner-acceptance-2026-11-01/acceptance.json` | Four superseded ordinary-CI ZIPs and two node_modules trees DELETE; acceptance/native/history metadata KEEP; signing fixtures REVIEW |
| P5C | ACCEPTED / COMPLETE | tooling bfa0b8005a3ddc519354fd7907e9b972fde8126b; integration 41287523702 attempt 1 SUCCESS; diagnostic 13074794320 | `ci/P5C_REPORT.md`; `ci/evidence/p5c/formal-owner-acceptance.json` | Approved P6 B ZIP from ordinary CI 41285343063 KEEP; uncommitted closeout KEEP |

Full report/evidence hashes: `ci/evidence/p6/binary-route-2026-11-02/phase-reconciliation.json`.
No completed phase was rerun. P5A/B/C remain separately ACCEPTED / COMPLETE.
Local integration HEAD is bfa0b8005a3ddc519354fd7907e9b972fde8126b, branch
`desktop/p2-production-integration`; local p5a-accepted peels to
1a28f68c5732ccc1275403060e89ff168a846655. No Git mutation occurred.

## Accepted package references — both preserved, no substitution

The owner's requested `/tmp/cyrnava-p5a-hosted-41181510439/package.zip` exists.
Its SHA-256 is **73e6d58a91ff2e57ca7b801b120ca61eceb399202349345508b8fbf6ce4eba6b**;
streamed contained bundle SHA-256 is
**93957ce5590818e016c5b9e86ed9c6c1d32a684f6c644af44531c316020b26db**;
source 1ee2077b283b8e5dfc2162119dd439ed3baeb109; artifact 13035607417;
OSTree da1bf73e3169096522f82249b39f9c9c8546b0317ee6461905bbc6952d6de1ac.
The native evidence exists at **ci/evidence/p5b/owner-native-2026-10-31/**
(the root `evidence/...` spelling does not exist in this checkout).

That requested reference was called **A** by the historical P6 real-update driver.
The distinct owner-approved historical **B** remains
`ci-output/p5c-hosted-41285343063/package.zip`, source bfa0b800..., CI 41285343063,
artifact 13075346402, ZIP
**2d11ce5057ae66cd4dc526dac607a2344b89dbc1fcef5e62038ad59583c93fbe**,
bundle **ef732c240d8a01e33a638cd10e83fb985c7ba9e678b573ba508cd48c3934f47c**,
OSTree f759380dca9aa36e4674ad6dffb24d3e2340342da5fe04537ac17031a3bada15.
Both ZIPs and actual contained bundles were rehashed. B-approved.json differs from
its unchanged original proposal only in the authorized boolean. Neither is being
substituted for the other or described as the new P6 candidate. No /tmp sweep.
See `artifact-preservation.json` in the current binary-route evidence directory.

## Binary-route result and exact stop conditions

Metadata was read using a dedicated, credential-free Flatpak user installation
under `ci-output/p6-binary-evaluation/`. The normal user/system remotes, installations,
permissions and security settings were not changed. The upstream descriptor configures
https://dl.flathub.org/repo/ with both commit and summary GPG verification true.
BaseApps are **app refs**, not runtime refs; initial runtime-kind queries returned
no such ref and were corrected before evaluation.

| x86_64 ref | Exact observed remote commit | Upstream displayed download / installed size |
| --- | --- | --- |
| app/io.qt.PySide.BaseApp/x86_64/6.11 | 25537519d4e093f4b32515f89d24ae7ca6eddfa2ff5dd21e1a82a7bad9189572 | 355.7 MB / 995.2 MB |
| app/io.qt.qtwebengine.BaseApp/x86_64/6.11 | 06c99098f7ed648656bbb4ddb77f9c463216f88eea553c899bd20106ea82de6c | 233.1 MB / 634.3 MB; already layered in PySide BaseApp, not added twice |
| runtime/org.kde.Platform/x86_64/6.11 | fb23e178d082b117df7924f9a84710992ec233ebc007385feb85d349c4c81415 | 414.5 MB / 1.1 GB |
| runtime/org.kde.Sdk/x86_64/6.11 | f77a65229fcb9dc1468944cd6a2b5aa327d1877725d681467805dae6ed68aebe | 1.2 GB / 3.2 GB |

Published PySide commit subject identifies recipe 732cd70984eab55693b55062026bd289ef98d974,
recipe SHA 37c854d009d542dcc4ec57bbe12b479f1dc4a4918332164932cf27fb8c5c8cbe;
WebEngine identifies 1f4a783f05d97ecb7a887096c2cd933406c727f8, recipe SHA
6b6663fd9d8ee02e5531cd71a8ca45d26776733920722d8e06f55efd5c5da2f7.
Those exact recipes specify PySide/shiboken source c76f06aa6ca36abbccdf211c6ea24c34d71ee43f
and WebEngine source 6de08a0e135c48890ba49f394d969ed5964c1cc5 at 6.11.3.
The existing source-identities.json records all ten maintained renderer/integration
patches; the initial sandbox patch SHA is
b086829daf0404b3ed89fb5b135aa0015fe4df00accff75a3d8b4b7ae23dcff3.
No patch was applied locally. No wheel/helper/provider mixing or WebEngine removal.

**This does not establish the versions of downloaded binary files.** Partial,
pinned fetches for PySide QtCore/metadata/manifest and runtime QtCore/manifest each
failed at the commit object with HTTP 403. Both returned promptly; zero retry and
50-second command bounds were used. Why this endpoint rejects these object requests
in this session is unknown. Metadata availability is not payload availability.
No binary was loaded; Python ABI, new binding/helper/resource/plugin providers,
private symbols, RPATH and complete library closure remain BLOCKED. Retained R4
ELF evidence establishes QtCore 6.11.3 for this exact runtime commit only.

One minimal bwrap namespace probe reported namespace creation denied. Its
individual exit status was not captured by the combined discovery command; the
explicit denial is retained and is not interpreted as a successful probe.
No repeat, host-security change, global library workaround or GUI was attempted.
This is a limitation of the current process, not proof of an application/runtime
failure. Actual sandbox imports/rendering and normal launcher remain unexecuted.

Maintenance: upstream exports are dated 1–2 November 2026 and no EOL warning
appears in the returned ref information. A branch name/recent build does not prove
ongoing security maintenance. [Qt's own table](https://wiki.qt.io/Qt5Releasing)
lists **commercial** support for 6.11 through March 2027; it does not establish
community/runtime security coverage through that date. That coverage still needs
confirmation before declaring a supported package. No silent 6.12 substitution.

### Numerical resource boundary

Initial repository allocation **6,505,811,968 bytes**; persistent free
**3,746,414,592 bytes (3.49 GiB)**. /tmp is tmpfs with 3,666,583,552 bytes free,
competing for laptop RAM/swap, and is not counted as extra persistent build capacity.
Historical SDK/runtime are installed; a retained P6 client has the exact current
runtime. No unmeasured object reuse or modification of retained clients is credited.

Cold isolated binary-route allowance: **9 GiB free before bulk acquisition**,
**7.5 GiB additional allocation cap**, **1.5 GiB minimum remaining headroom**.
Approximate components: SDK 3.2 GB, runtime 1.1 GB, layered BaseApp 0.995 GB,
thin build copy 1 GB, export 0.35 GB, bundle 0.22 GB, source materials 0.6 GB,
temporary downloads 0.4 GB and backend wheels 0.03 GB. Object/deployment hardlink
reuse on the same filesystem is an assumption to verify, not a promised saving.
SDK/runtime/BaseApp total displayed downloads are ~1.97 GB. Raw upstream size
labels are rounded; exact transferred/reused bytes are unavailable because fetch failed.
Do not run duplicate WebEngine installation or download its source archive.

Even the full proposed cleanup estimate would leave only ~5.98 GiB free, below
this conservative cold route. A verified existing-object reuse measurement could
reduce it; none was established. Stop on unverified refs/providers, failed signature,
missing dependency, missing sandbox integration, less than headroom, allocation
cap or 60-minute total bound (15 acquisition, 30 thin build/export, 10 focused
verification, 5 metadata; one job). No repeated downloads or alternative-build series.
This is a single-digit GiB binary budget, not the paused 79–137 GiB source build.
No source-build staging exists here: the existing planning directory is 36,864 bytes.

**Recommendation:** binary route remains a plausible upstream-backed candidate,
**feasibility BLOCKED in this environment**, not adopted and not production viable yet.
No thin build is justified until exact binary/provider and execution preconditions
can be checked. `binary-evaluation.json` and `resource-budget.json` retain actual
readbacks/failures, exact identities, assumptions and stop conditions.

## Repository-only cleanup — exact batch, confirmation outstanding

The original **19** DELETE targets initially matched the prior audit,
retaining their **1,677,996,032-byte** baseline. After regression subprocesses,
the guard detected changed release bytecode and stopped without deletion. Four
recent cp312 caches were explicitly verified equal to compilation of current
source and matching source timestamp/size headers; their re-audit adds 24,576 bytes
(cache-reaudit.json). No changed fingerprint was blindly refreshed. One newly verified P4 extracted
payload adds **997,265,408 bytes**. The final **20-target** batch has
**2,675,286,016 allocated/estimated reclaim bytes (2.492 GiB)**.
No assessed target was deleted. Allocated blocks are not guaranteed free-space gains
(hardlinks, shared extents and unrelated writes matter). The script prints actual
allocated repository usage and filesystem available bytes before/after deletion,
including partial completion if an external change stops the batch.

No on-disk cleanup_cyrnava.sh was supplied in this checkout. A minimal wrapper with
that requested name now delegates to the existing Python engine. It has no deletion
logic or extra confirmation. Root/content/inode/metadata/HEAD/source guards,
symlink/mount/activity refusal and nofollow deletion remain. Added guard/target
intersection and overlapping-batch rejection. Changed targets stop rather than
being silently rediscovered. Only newly created test fixtures were removed by tests.

| DELETE exact repository-relative target | Allocated bytes | Reason |
| --- | ---: | --- |
| `ci-output/p5b-clean/checkout/frontend/node_modules` | 365,522,944 | Obsolete P5B test checkout dependencies; recreate from retained checkout lockfile; current frontend/node_modules kept |
| `ci-output/p5b-appearance-clean/checkout/frontend/node_modules` | 365,531,136 | Obsolete appearance-investigation dependencies; recreate from retained lockfile; all source/Git and evidence kept |
| `ci-output/p6-npm-cache` | 73,252,864 | Regenerable npm HTTP/content cache; installed working dependencies kept |
| `ci-output/p6-pip-cache` | 29,450,240 | Regenerable pip download cache; installed Python environments kept |
| `ci-output/p5b-hosted-41205351385/package.zip` | 210,239,488 | Superseded ordinary-CI bundle output; exact result/build-input/provenance JSON retained and verified; not approved A/B or current release input |
| `ci-output/p5b-hosted-41207770532/package.zip` | 210,247,680 | Superseded ordinary-CI bundle output; exact result/build-input/provenance JSON retained and verified; not approved A/B or current release input |
| `ci-output/p5b-hosted-ci-41258927530/package.zip` | 210,247,680 | Superseded ordinary-CI bundle output; exact result/build-input/provenance JSON retained and verified; not approved A/B or current release input |
| `ci-output/p5b-hosted-ci-41264318875/package.zip` | 210,239,488 | Superseded ordinary-CI bundle output; exact result/build-input/provenance JSON retained and verified; not approved A/B or current release input |
| `.pytest_cache` | 49,152 | Regenerable test/lint/bytecode cache; source files verified present; no source or environment deletion |
| `.ruff_cache` | 131,072 | Regenerable test/lint/bytecode cache; source files verified present; no source or environment deletion |
| `backend/.pytest_cache` | 86,016 | Regenerable test/lint/bytecode cache; source files verified present; no source or environment deletion |
| `backend/.ruff_cache` | 53,248 | Regenerable test/lint/bytecode cache; source files verified present; no source or environment deletion |
| `backend/app/__pycache__` | 512,000 | Regenerable test/lint/bytecode cache; source files verified present; no source or environment deletion |
| `backend/tests/__pycache__` | 933,888 | Regenerable test/lint/bytecode cache; source files verified present; no source or environment deletion |
| `desktop/native/__pycache__` | 303,104 | Regenerable test/lint/bytecode cache; source files verified present; no source or environment deletion |
| `desktop/__pycache__` | 49,152 | Regenerable test/lint/bytecode cache; source files verified present; no source or environment deletion |
| `ci/__pycache__` | 200,704 | Regenerable test/lint/bytecode cache; source files verified present; no source or environment deletion |
| `ci/release/__pycache__` | 679,936 | Four recent cp312 files explicitly re-audited against current source; other cache entries retained from original review; later changes abort |
| `packaging/flatpak/production/__pycache__` | 290,816 | Regenerable test/lint/bytecode cache; source files verified present; no source or environment deletion |
| `.p4-cache/cyrnava-builds/p4/local-A-6m4ne70o/build/files` | 997,265,408 | Regenerable extracted P4 app payload; all 5320 inventory entries match retained acceptance inventory; exact bundle/hash and source/staged inputs remain; native checker consumes bundle, not this tree; do-not-repeat finish history retired |

| KEEP exact repository-relative path | Allocated bytes (overlapping rows; do not sum) | Reason |
| --- | ---: | --- |
| `backend/.venv` | 99,753,984 | Current backend working environment |
| `frontend/node_modules` | 365,867,008 | Current frontend dependency environment |
| `frontend/dist` | 4,313,088 | Built frontend needed by current application/backend |
| `ci-output/p6-clean` | 563,200,000 | Current P6 verification Python environment and checkout; retained as working dependency |
| `ci-output/p5c-hosted-41285343063/package.zip` | 210,239,488 | Approved Generation B artifact consumed by local verification |
| `ci-output/p6-owner` | 12,288 | Approved B authorization input |
| `.git` | 40,644,608 | Repository history, refs and metadata |
| `backend/app` | 692,224 | Application backend source |
| `backend/tests` | 1,204,224 | Application regression tests |
| `frontend/src` | 360,448 | Application frontend source |
| `docs` | 2,015,232 | Professional/user-facing guides, screenshots and architecture; unchanged |
| `ci/evidence` | 40,517,632 | Retained identities/acceptances and unique uncommitted findings; only about 40 MiB |
| `ci/release` | 1,245,184 | Existing release/security/verification code and useful tests; deferred modules retained |
| `backend/.venv-before-cyrnava-c3e071c93b7f4669bf3cca388daec4c4` | 96,477,184 | KEEP: docs/migrate-to-cyrnava.md retains this exact environment for rebranding rollback/restoration; no evidence that recovery dependency can be retired |
| `ci-output/p6-binary-evaluation` | 8,065,024 | Current isolated metadata/preflight input; no normal host changes |

All application source/tests/locks/manifests and all phase reports/checklists,
user guides/README/CHANGELOG/licenses/notices remain KEEP even if not listed as a
separate directory row. Report dependency/recoverable-commit proofs remain in
`phase_report_review` in the inventory. User-facing documents are unchanged.

| REVIEW exact repository-relative path | Allocated bytes (overlapping rows; do not sum) | Reason |
| --- | ---: | --- |
| `.p4-cache` | 1,544,142,848 | Parent remains REVIEW/KEEP; exact bundle/native metadata/staged source remain. Only verified build/files child is DELETE; escaping var/run link untouched. |
| `frontend/test-results` | 5,230,592 | Unique untracked browser screenshot/trace diagnostics, referenced by M5_REPORT.md, M6_VERIFICATION.md and CI diagnostic conventions; retained equivalent not proven. |
| `ci-output/p5b-clean/test-tmp` | 208,482,304 | Inspected pytest, Playwright and node cache layout. Pytest subtree contains backup/database and signing fixtures; not every private-key/data object independently proven disposable. Preserve whole group; do not equate pytest naming with safety. |
| `ci-output/p5b-appearance-clean` | 577,822,720 | Checkout Git metadata and possible unique overlays retained; only explicitly listed child dependency caches may be removed |
| `ci-output/p5b-clean` | 766,353,408 | Checkout Git metadata and possible unique overlays retained; only explicitly listed child dependency caches may be removed |
| `ci-output/p5b-dependency-correction` | 119,832,576 | Checkout Git metadata and possible unique overlays retained; only explicitly listed child dependency caches may be removed |
| `ci-output/p5b-main-registration-a` | 9,973,760 | Checkout Git metadata and possible unique overlays retained; only explicitly listed child dependency caches may be removed |
| `ci-output/p5b-source-checkout-correction` | 169,742,336 | Checkout Git metadata and possible unique overlays retained; only explicitly listed child dependency caches may be removed |
| `ci-output/p5c-clean` | 109,072,384 | Checkout Git metadata and possible unique overlays retained; only explicitly listed child dependency caches may be removed |
| `ci-output/p5c-main-registration-a` | 10,043,392 | Checkout Git metadata and possible unique overlays retained; only explicitly listed child dependency caches may be removed |
| `ci-output/p6-generation-A-diagnostics-clean` | 84,815,872 | Checkout Git metadata and possible unique overlays retained; only explicitly listed child dependency caches may be removed |
| `ci-output/p6-gui-prelaunch-clean` | 84,795,392 | Checkout Git metadata and possible unique overlays retained; only explicitly listed child dependency caches may be removed |
| `ci-output/p6-historical-clean` | 84,865,024 | Checkout Git metadata and possible unique overlays retained; only explicitly listed child dependency caches may be removed |
| `ci-output/p6-preparation-correction-clean` | 84,770,816 | Checkout Git metadata and possible unique overlays retained; only explicitly listed child dependency caches may be removed |
| `ci-output/p6-r11-clean` | 89,243,648 | Checkout Git metadata and possible unique overlays retained; only explicitly listed child dependency caches may be removed |
| `ci-output/p6-r4-ABI-clean` | 84,824,064 | Checkout Git metadata and possible unique overlays retained; only explicitly listed child dependency caches may be removed |
| `ci-output/p6-r6-clean` | 84,885,504 | Checkout Git metadata and possible unique overlays retained; only explicitly listed child dependency caches may be removed |
| `ci-output/p6-r9-clean` | 89,214,976 | Checkout Git metadata and possible unique overlays retained; only explicitly listed child dependency caches may be removed |
| `ci-output/p6-targeted-b-clean` | 89,325,568 | Checkout Git metadata and possible unique overlays retained; only explicitly listed child dependency caches may be removed |

No REVIEW item was promoted by filename alone. The P4 build/files child was
promoted only after the unchanged payload auditor rehashed every entry and matched
both staged and retained inventories; source, exact bundle and native checker
inputs remain. See P4-extracted-payload-proof.json in the current evidence. The older 96,477,184-byte environment
was moved to **KEEP**, because docs/migrate-to-cyrnava.md explicitly retains it for
restoration. The P4 artifact's actual checksum matches retained final build evidence;
its 1,544,142,848-byte parent includes native inputs and a /run symlink, which
remain untouched. Only the verified 997,265,408-byte extracted child is proposed. The
208,482,304-byte fixture group contains potentially sensitive backup/database/key
fixtures not fully proved disposable. The 5,230,592-byte browser diagnostics have
no proven retained equivalent. No broad glob, git clean, GC, outside-repository
cleanup, credential/key/data deletion or report deletion.

Owner entry point (review preview, close app/build/test activity, then run once):

```bash
bash /home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava/cleanup_cyrnava.sh --preview
bash /home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava/cleanup_cyrnava.sh
```

The second command asks for the single exact `DELETE AUDITED TARGETS` confirmation.
It has not been auto-answered. No build/test will use these targets concurrently.
Only unreviewed/changed targets need a refreshed audit; do not force them through.

## Verification actually executed at this checkpoint

- **402 release/packaging tests +198 subtests PASS**, unchanged accepted policy,
  signing/provenance/source checkout/workflow and package assertions included.
  Final combined run: **424 tests +198 subtests PASS** (402 release/packaging
  and 22 cleanup). First combined run was 422 with then-20 cleanup cases.
- **22 cleanup fixture tests PASS** on final behavior: existing change/symlink/
  mount/activity protections plus wrapper delegation/wrong-root rejection,
  guarded-source/overlap refusal and allocated/free-space measurement.
- **107 backend security/navigation/migration/assets/backup tests PASS**, using
  backend/ as cwd. Initial root-cwd attempt passed 106 and failed one CLI subprocess
  import because app was not on that subprocess's module path; corrected invocation
  passed all 107. No application change made to hide that invocation failure.
- Ruff and Bash syntax checks on changed cleanup files; results in verification.json.
- Both accepted archives and actual bundles, P4 A artifact and B approval reverified.
- The two earlier 5 GiB CI build-directory precondition failures remain historical
  FAIL, not relabeled. Their precondition remains unmet; they were not repeated.
- No new frontend/browser/native/package launch or real-update PASS. Prior frontend
  and R11/R12 results retain only their exact source/artifact scope.

Commands and result counts are retained in the current evidence. No native rehearsal,
preparation, normal-host install, source build, GitHub execution, commit/push,
permanent signing, hosting or publication occurred.

## Short remaining actions and release materials

The next technical action is **a bounded binary preflight from a namespace-capable
Ubuntu terminal**, then the thin rebuild only if its exact provider checks and disk
budget pass. Do not change AppArmor/seccomp/user namespace policy to make Codex pass.
Owner steps are in P6_OWNER_CHECKS.md; no new application GUI command is issued
because no new candidate exists. Successful preflight alone is not renderer success.

Once built, focus on that exported artifact: isolated clean install, normal menu
launch/name/icon, local content and actual renderer sandbox/process evidence,
notes/folders/rich text/screenshot/offline/restart, one backup/restore/future-schema
refusal and a meaningful manual update preserving disposable data. No old historical
runtime restoration or complete historical A/B rehearsal. If the previous package
cannot launch normally, record that limit and do not claim an end-to-end update or
schema rollback. If no actual runtime commit change is exercised, runtime-update
compatibility is NOT EXECUTED; no arbitrary future-version promise.

Current release runbook contains a simple signed-bundle install/manual-update draft,
network/runtime prerequisites and recovery limits. Command flags were checked against
the installed Flatpak CLI; successful installation of a new signed package remains
pending. It does not configure any public service. Existing licensing/notices work
is retained, but cannot certify a still-absent payload. No production fingerprint
or private key is recorded in reviewed project evidence; personal GnuPG homes were
not accessed. Disposable rehearsal keys are not release trust. No fabricated signature,
license decision or branding permission. Consolidated owner decisions remain code
license/holder and logo rights, specific dependency/source obligations, production
signing identity/backup/replacement, and eventual publication after technical gates.

## Historical investigation appendix — not current release gates

The earlier chronology below is retained in this existing report because it
contains uncommitted findings. Its prior checklists, full-platform/publication
plans, exhaustive retention requests and source-build resource requirements are
superseded by the six-gate owner scope reset above wherever they conflict. It does
not authorize old commands or reintroduce deferred v0.1 work.

**Latest checkpoint — experimental Qt feasibility RESOURCE BLOCKED.**
The owner authorized bounded candidate implementation/build, but required stopping
if it cannot fit. Measured repository disk free **3.50 GiB**, available RAM
**3.16 GiB**, existing swap free **12,288 bytes**. Tmpfs is not additional persistent
capacity. Conservative planning envelope **79–137 GiB**, including 20 GiB headroom;
recommend **150 GiB free persistent space** and initially one compile/link job with
nested Chromium concurrency separately bounded. Estimates are not measured peaks.

No expensive source download, extraction, configure, build, package or native check
was attempted. The dedicated
[candidate planning directory](../packaging/flatpak/compatibility/qt-6.11.3-feasibility/README.md)
contains exact 6.11.3 archive expectations, source/tag revisions, ten upstream patch
hashes, provider/helper plan and unresolved SDK/closure locks. It is **not an
executable recipe or a built candidate**. Raw pinned recipe readback also corrects
the earlier mistaken 6.11.2 labels: both inspected upstream recipes specify 6.11.3.
Accepted installed binary versions and all artifact identities remain unchanged.

Recommendation: **NOT VIABLE within the current resource envelope**; architecture
and sandboxed rendering remain unproven. Next owner decision is a suitable existing
build volume/machine, not another historical GUI test. No candidate native command
is issued. New candidate regressions and all build/import/renderer/update checks
are NOT EXECUTED; earlier test passes keep only their exact recorded scope. See
`ci/evidence/p6/qt-feasibility-resource-preflight/` for measurements and preservation.
The prior report is archived there; historical checkpoints below remain evidence
of their original scopes. **P6 remains CONDITIONAL.**


**2 November 2026 — P6 — CONDITIONAL / FURTHER ACTION REQUIRED.**


**Current compatibility checkpoint — 2 November 2026:** R12's owner-executed
historical-runtime B-only test is independently read back as PASS (two GUI launches,
post-import Light baseline/reinstall, synthetic data and accepted inputs preserved).
Ordinary-runtime compatibility remains FALSE. R9 and R11 remain historical FAIL
records. Do not repeat the historical rehearsal.

The production compatibility assessment is complete; a safe replacement package
has NOT been implemented. See [P6_QT_COMPATIBILITY.md](P6_QT_COMPATIBILITY.md) for
ELF/source causality, four exact-version wheel experiments, options, local tests
and the concrete whole-stack build proposal. Generic wheels omit observed BaseApp
Flatpak renderer-integration markers; host import success does not validate that
security boundary. Accepted manifest/locks/artifacts/security remain unchanged.

Historical assessment checkpoint: owner review of the app-owned coherent Qt
source-build proposal was subsequently approved; resource preflight above now blocks execution. No native command is requested yet: there is no
verified replacement package. Normal runtime installation/update, replacement
Flatpak imports/launcher/renderer checks and production release requirements remain
OPEN. Historical implementation checkpoints below describe their recorded states;
this checkpoint supersedes earlier “targeted test not run” statements.

## Baseline and preservation

Local and independently reread remote integration HEAD remain
`bfa0b8005a3ddc519354fd7907e9b972fde8126b`; main remains
`4021bc292267c19b7ebebf219b4f682f8f99bf4c`. The local `p5a-accepted` tag still
resolves to `1a28f68c5732ccc1275403060e89ff168a846655`.
P5C's uncommitted formal closeout is preserved separately, byte for byte. No
commit, push, tag, workflow execution, GitHub setting, installation in the normal
Flatpak profile, personal workspace, permanent key or public endpoint was changed.

Accepted P5A source `1ee2077b283b8e5dfc2162119dd439ed3baeb109`, CI `41181510439`,
artifact `13035607417`, ZIP `73e6d58a…4eba6b`, bundle `93957ce5…20b26db` and
OSTree `da1bf73e…de1ac` remain distinct from release tooling and P6 candidate code.
Full values are in `ci/evidence/p6/release-candidate-manifest.json` and the unchanged
P5B policy. A fresh readback confirms the original artifact is unexpired and its
identity/digest are unchanged; it expires **7 November 2026, 07:53:28 UTC**.
Local cached replay is not new hosted eligibility. Expiration must never cause
silent substitution.

P3 migration/backup/schema safeguards, P4 production identity/package auditor,
P5A CI provenance, P5B eligibility/signing/seals/retained snapshots and P5C client
isolation are reused. Application code, schema 5, version 0.1.0, production
packaging, permissions, signing policy, CI workflows and accepted guards are
unchanged.

## Implementation

| Files | Result |
| --- | --- |
| `frontend/package.json`, `frontend/package-lock.json` | Exact minimatch 11.0.1 override and security regression in the normal test command; no wholesale upgrade |
| `frontend/scripts/check-minimatch.mjs` | All three consumer resolutions, ordinary matching and adversarial compilation in a bounded subprocess |
| `ci/release/distribution.py` | Provider-neutral reviewed publication plan and local reference adapter around accepted publisher; conditional activation, retained snapshots, verified HTTP GET/HEAD, MIME/cache/404 policy |
| `ci/release/trust.py` | Additional current primary/subkey identity, expiry and revocation checks on top of accepted cryptographic verification |
| `ci/release/product_inventory.py` | Bounded inventory of source locks and actual app/runtime metadata, SPDX records, native ELF hashes and notices; no symlink traversal or complete-SBOM claim |
| `ci/release/key_ceremony.py` | Fixed disposable certificate/signing-subkey rehearsal, encrypted backup/restore, primary-secret stub verification, expiry/revocation negatives and mandatory private cleanup |
| `ci/release/native_distribution.py` | Empty isolated client, actual upstream runtime retrieval and pin verification, real remote install, source/version/schema/permission validation and sandboxed launch probe |
| `ci/release/real_update.py` | Owner-gated real two-artifact preparation and GUI update/rollback/reinstall supervisor; exact B approval before signing; P5B audits/signing and P4 native assertions reused |
| `ci/release/real_update_audit.py` | Separate P6 B approval-bound child; unchanged exported-payload audit and candidate validation, exact source/approval binding and safe operation/stage diagnostics |
| `ci/release/test_real_update_audit.py` | 20 synthetic regressions for the B audit boundary, evidence validation, redaction, cleanup and failed-directory preservation; native payload auditing mocked in positive fixtures |
| `ci/release/progress.py`, `ci/release/test_progress.py` | Allowlisted operation events, heartbeats, deadlines, child-group cancellation and 12 synthetic interruption/prelaunch regressions; no application launch in tests |
| `ci/release/native_diagnostics.py`, `ci/release/test_native_diagnostics.py` | Private bounded child-output retention, safe Python bootstrap/exception markers and 11 synthetic regressions; production P4 checker unchanged |
| `ci/release/test_distribution.py` | 30 new publication, transport, trust, inventory, isolation, approval and cleanup regressions |
| P6 plan/report/checklist/runbook/license review, release notes and evidence | Acceptance criteria, exact results, unresolved gates, executable owner procedure and release-candidate manifest |

Publication does not create a second signer. The adapter calls the accepted
signed seal, native OSTree verifier and durable publisher. It verifies the whole
source, destination and historical object set, then conditionally activates a
complete immutable snapshot under the existing exclusive lock. Dry-run does not
upload or activate. Production endpoints/credentials are not implemented/enabled.
A future provider must supply equivalent conditional-pointer/gateway semantics;
independent live summary/signature PUTs are explicitly rejected as a design.

HTTP serves only manifest-listed files beneath the current generation; it rejects
traversal, unlisted/private content and damaged objects. Immutable hash objects
are cacheable, while metadata and errors are no-store. The server verifies each
immutable manifest once and hashes every response. Signature pairs spanning two
HTTP requests can still cross an activation boundary and fail closed; the adapter
does not claim transactionality across client requests or universal anti-rollback
freshness for ordinary Flatpak clients. No public CDN behavior has been verified.

The owner approved the already-built real B from accepted P5C implementation
`bfa0b800…`, CI `41285343063`, artifact `13075346402`, distinct OSTree
`f759380d…ada15`, version 0.1.0/schema 5, for this disposable compatibility exercise.
The original proposal remains false and byte-identical; the authorized copy at
`ci-output/p6-owner/B-approved.json` changes only the Boolean to true. This does
not replace the P5A allowlist or select the eventual final P6 release source.
The owner's first preparation **FAIL** and the local correction are described
below. The full corrected native flow and GUI remain unverified.

## Owner preparation failure and local correction

The original failed output remains untouched at `~/.cache/p6/real-pair`.
`prepared.json` reports complete FAIL with `Operation failed: python
(CalledProcessError)` and disposable-key cleanup PASS. A's audit result reports
PASS, its sealed generation and P6 provenance exist, B's detached source resolves
to the exact approved SHA and is clean, `p/audit-b` is empty, and generation B's
public directory does not exist. The signing-key home `p/key` is absent.

There are exactly two Python audit subprocesses in preparation:

1. A: `core.generate_repository` invokes the unchanged `audit_candidate.py`.
   The retained A audit result and completed generation establish that it passed.
2. B: `real_update.prepare` incorrectly invoked the same P5B-only child. That
   child calls `core.approval`, whose unchanged allowlist intentionally contains
   only accepted A. It rejects B with `Source is not approved for staging` before
   candidate validation or exported-payload auditing, despite the separate P6
   owner approval. Isolated execution of this exact child under the owner's
   Python 3.12.15 reproduced exit 1 and that authored rejection; its empty output
   remained unchanged. No full preparation or native audit was repeated.

This is a confirmed **P6 driver integration defect**, not a demonstrated artifact,
checkout, Python-dependency, payload, or signing failure. B's native payload audit
was never reached; passing the correction's unit fixtures does not certify it.

The correction invokes `real_update_audit.py` for B only. The child revalidates
the exact approved JSON hash and true-valued owner authorization, version/schema,
source SHA/environment binding and clean checkout, then calls the unchanged
`core.validate_candidate` and hash-pinned P5A exported-bundle auditor. The parent
requires complete PASS evidence matching the approved source, bundle, OSTree
commit and approval hash before B signing. P5B's A-only auditor/allowlist, signing,
application sources, packaging, permissions and workflows remain byte-identical.

Diagnostics identify `p6-generation-B-payload-audit`, a fixed child stage and
exit/timeout/unavailable categories. Arguments, paths, environment values, raw
stderr and exception messages are excluded. Other preparation failures retain a
fixed operation label; the accepted shared subprocess wrapper is unchanged.

Verification from a new disposable checkout with independent Git objects:

- New focused regressions: **20 PASS + 12 subtests**.
- Complete release and CI/workflow regressions: **177 PASS + 216 subtests**;
  one existing duplicate-ZIP warning, no failures.
- Ruff and formatting on the three correction Python files: **PASS**.
- Both cached A/B ZIPs, retained bundle/metadata hashes, immutable source identities,
  original/approved approval JSONs and accepted security controls: **unchanged**.
- Failed records and retained candidate files: hash-verified unchanged; key home
  absent, B audit still empty, no new native preparation or GUI execution.

The initial wider test attempt is preserved: 140 passed, two disk-precondition
failures and 35 GPG fixture setup errors. `/tmp` had less than the existing 5 GiB
precondition and the sandbox blocked local GPG-agent sockets. With local socket
permission and `/var/tmp` (over 38 GiB free), the unchanged checks passed. No
timeouts, retries, test exclusions, application behavior or security checks changed.

Evidence is in `ci/evidence/p6/real-pair-preparation-correction/`, including the
exact isolated rejection, retained failure JSONs, prior review/checksum/source
snapshots, clean-checkout hashes, test logs and integrity/preservation checks.
The earlier 693-test/full-frontend verification below remains historical evidence
for its recorded source hashes; those full suites were not repeated for this
P6-only driver correction.

**Historical checkpoint:** the owner subsequently authorized and completed
`real-pair-r2` preparation with PASS. The agent did not run it. The next section
records the interrupted GUI command and current checkpoint. Preserve both the
original failed pair and successful r2 pair. P6 remains CONDITIONAL.

## Interrupted GUI command: prelaunch runtime retrieval

The owner reports waiting about five minutes with no window, then pressing Ctrl+C.
The retained r2 `owner-result.json` contains complete FAIL, empty checks and no
error field. This is consistent with the original driver's control flow:
`KeyboardInterrupt` bypasses its ordinary exception handler, but its `finally`
writes the initial FAIL/checks object before propagating the interruption to the
outer CLI handler. There is no custom SIGINT handler. `complete: true` means the
record was finalized, not that launch or verification completed.

The exact pre-window order is:

1. Validate pair marker/preparation PASS, create isolated client, validate Wayland.
2. List empty client; fetch the upstream runtime descriptor; install KDE Platform
   and related extensions; pin and verify the exact runtime commit/signatures.
3. Validate and activate generation A in a local signed store, start loopback HTTP.
4. Validate descriptors/summary, install A, verify source/commit/schema/permissions.
5. Print the EDIT instructions, invoke `flatpak run` with the unchanged native
   checker, then initialize PySide/Qt, the private backend and application window.

Retained state narrows the interrupted operation to **runtime installation**:
the upstream remote exists with both GPG checks enabled; GL/VAAPI/codec/style and
locale extensions are deployed; the KDE Platform deployment is absent; an OSTree
transfer staging directory remains. The app deployment, active store pointer,
edit-phase result and application profile are all absent. Since `runtime_retrieval`
is the first checks assignment and evaluates its RHS first, an interruption there
leaves checks empty. Generation A did not reach installation or launch through
this sequence. This is not evidence of an application, Qt or sandbox defect.

The most likely wait was runtime transfer/import before Platform deployment.
Which network endpoint/object, disk step, lock or helper IPC was pending cannot be
reconstructed from the old wrapper: it captured stdout/stderr without streaming
or progress and allowed 1,800 seconds for runtime installation. Five minutes is
below that existing bound. Download and pin commands already used --noninteractive;
there is no evidence of a prompt. Descriptor fetch/helper IPC could block within
their own subprocess limits, but descriptor setup had already progressed here.

The P6-only correction emits flushed, fixed operation names, start/running/end
state and monotonic elapsed/deadline information to stdout and an attempt-local
`operations.jsonl`/`progress.json`. Long runtime/GUI children report every ten
seconds, without restarting the process or extending its deadline. Descriptor
setup is bounded at 300 seconds, matching existing metadata commands; runtime
download/pin retain 1,800 seconds and synthetic GUI phases retain 900 seconds.
Captured raw output, arguments, URLs, credentials, environment and note contents
are never included in diagnostic events. Runtime child stdin is /dev/null, so a
terminal prompt cannot wait invisibly; GUI checker stdin still carries its script.

Ctrl+C now records `interrupted: true`, the most specific failed operation,
elapsed time and `generation_A_launch_attempted: false` for prelaunch cancellation.
The monitored child's separate process group receives TERM, then KILL only if it
does not exit within a bounded five-second grace; descendants are not left running
by the wrapper. Timeout and nonzero exit have separate categories. Existing P5C
client security/error classification and all signature checks remain unchanged.

GUI now requires a **fresh --attempt-root** containing its own empty client/store,
progress and results, bound to the successful prepared.json hash and current GUI
driver hashes. Signed A/B preparations are read-only inputs. No failed profile,
result or partial runtime installation is overwritten or reused.

Focused tests from a disposable clean checkout: **32 PASS + 12 subtests** (12 new
progress/prelaunch tests plus the existing 20 B-audit tests). Complete release/CI
regressions: **189 PASS + 216 subtests**, one existing duplicate-ZIP warning.
Ruff/formatting pass. Tests use synthetic process fixtures and mock runtime/GUI
execution; no native preparation or GUI was run. Successful preparation, signed
generation metadata, original failed result and both approved artifact identities
are preserved. Evidence and prior review snapshots are in
`ci/evidence/p6/gui-prelaunch-correction/`.

**Historical owner checkpoint (subsequently executed as r3):** review the diagnostics and authorize one GUI command
against r2 with a new `gui-attempt-r3` root. Do not rerun preparation or delete any
old directory. Expect progress before a window, including runtime downloads that
may take substantially longer than five minutes. On interruption/timeout, retain
the attempt's results and stop; never classify an unattempted launch as failure of
Qt or the sandbox. P6 remains CONDITIONAL / native GUI verification incomplete.

## Generation A verification child exits 1: r3 investigation

The owner executed r3 with successful progress output. Retained evidence confirms:
runtime retrieval/pinned KDE verification PASS (109.869 s), A activation PASS,
A installation/source/version/schema/permission checks PASS (18.650 s), then
`gui-edit` started and failed with exit 1 after 1.022 s. The overall record is
complete FAIL, launch-attempt flag true; B update was not reached. No native edit
result or separate child stdout/stderr log was found in the disposable attempt.

The exact command template, with private per-run arguments replaced, was:

```text
flatpak --user run --branch=stable --command=python3 io.github._74Cerillion.CyrNava -u - edit <synthetic-run-id> <host-network-namespace> <synthetic-host-canary>
```

`packaging/flatpak/production/native_check.py` was streamed over stdin. This is
the **host-streamed P4 verification child**, not execution of the normal `cyrnava`
launcher and not a verifier shipped in the production payload. It imports
backend/PySide/application modules, validates configuration and creates initial
phase evidence before its native GUI checks. Without stderr or that phase record,
Flatpak startup, helper imports/configuration, Qt initialization and later native
initialization cannot be reliably distinguished. A one-second exit does not prove
an application defect, sandbox defect, or driver/helper incompatibility.

The confirmed implementation defect is diagnostic loss: `Progress.command`
captures stderr/stdout in `CalledProcessError`, but `exercise` formerly recorded
only the exception class and dropped both buffers. r3's discarded bytes cannot
be recovered by inspecting its JSON. No native rerun was used to guess a cause.

The narrow P6-only correction catches that child failure and saves the last
1 MiB of each output stream in unique, mode-0600 files under an owner-only
0700 `private-subprocess` directory in the **new external attempt root**. Original
byte counts, truncation and retained hashes are explicit. Raw files are never
copied into repository/CI evidence, printed, uploaded or committed automatically.
They can contain private paths or runtime output and require private owner review.

A standard-library bootstrap executes the byte-identical existing P4 checker with
unchanged argv/main/exit semantics, emitting a hash-bound `python-entered` marker
and allowlisted exception type/helper line on Python exceptions. Sanitized result
JSON contains fixed component/stage/stderr categories and private file basenames,
never exception messages, arguments, environment values or raw output. Markers
are diagnostic only: they cannot make a native check PASS. Existing P4 checks,
required evidence, timeout, security configuration and failure policy remain.

No production code, accepted P4 checker, packaging, permission, source/artifact,
signing or sandbox change is made. There is **no confirmed application correction**
and no evidence-based reason to modify application behavior at this checkpoint.

Clean-checkout verification: **43 focused tests + 15 subtests PASS**, including 11
new diagnostics tests; complete release/workflow suite **200 tests + 219 subtests
PASS**, one existing duplicate-ZIP warning. Ruff/formatting pass. Synthetic Python
children test bootstrap/import/exit/redaction behavior; Flatpak/Qt are never run.
Retained r3 and successful r2 hashes remain unchanged. Evidence and prior review
snapshots: `ci/evidence/p6/generation-A-launch-investigation/`.

**Historical checkpoint (subsequently executed as r4):** authorize one instrumented GUI attempt using r2's
prepared inputs and fresh `gui-attempt-r4`. Do not rerun preparation, reuse/delete
r3, or publish private logs. Inspect only safe result JSON publicly; inspect the
new private stderr locally if failure recurs. The exact failing runtime component
remains unresolved until suitable native child evidence exists. P6 is CONDITIONAL.

## R4 exact QtCore ImportError and runtime drift

The helper mapping is confirmed byte for byte. SHA-256 is
`8cec1f8e659063a05c9279aa5d89127a0325b5c7e8c138bdb48d0853d00bd248`; line 15 is
`from PySide6.QtCore import QTimer, QUrl`. Private stderr (281 bytes) hashes to
`e6256b39e537f8e51a8e434093850f0e1d331c13480290ebeb29274c9f4b75ab`; stdout
(322 bytes) hashes to
`663c6fc53ea085e210e7d96cfe10dbb1bd8ad93e345d5e753c427c2345481967`.
Neither was truncated. Both were inspected in place; raw contents remain private
and were not copied to repository evidence.

The sanitized actual error is `ImportError` from `QtCore.abi3.so`: undefined symbol
`_ZN14QObjectPrivateC2E16QtPrivate_6_11_2`, version `Qt_6_PRIVATE_API`. Demangled,
this is `QObjectPrivate::QObjectPrivate(QtPrivate_6_11_2)`.

Read-only ELF inspection independently establishes the native loading failure:

- Installed PySide6/shiboken metadata is 6.11.2. `QtCore.abi3.so` has an undefined
  requirement for exactly that versioned private constructor and needs
  `libQt6Core.so.6`.
- Its RPATH searches its origin, `/usr/lib/x86_64-linux-gnu`, and the neighboring
  shiboken directory. Neither origin directory contains the QtCore library. The
  active runtime provides `libQt6Core.so.6.11.3`.
- That provider exports the `QtPrivate_6_11_3` constructor, not the required
  `QtPrivate_6_11_2` constructor. The failure precedes QtWebEngine initialization
  and application-window creation.

Retrieval verified locked runtime commit
`76fa01ac42ecf45d2c5020ef80de1c474c0c2ae86a51a79e8fec44c48f9dc473`.
The active deployment after A installation is instead
`fb23e178d082b117df7924f9a84710992ec233ebc007385feb85d349c4c81415`, providing
Qt 6.11.3. A's normal dependency-resolving installation is the intervening
runtime-changing transaction in the recorded driver sequence. The driver checked
the application commit and runtime branch name, but did not re-read the runtime
commit after installation. Its install PASS did not establish that the previously
verified runtime remained active. r3 has the same later runtime, but its missing
stderr is not retroactively classified as a recorded identical ImportError.

The app ships no separate Python executable; runtime `python3` resolves to
Python 3.13. The packaged launcher matches source and runs
`python3 -B -m desktop.native` after changing to the application directory. The
verifier runs `python3 -u -`, adds app/backend module paths and has no
LD_LIBRARY_PATH override. Both use the installed PySide binding, native RPATH and
runtime provider. Buffering/bytecode flags and working directory do not supply the
missing C++ constructor. The normal launcher was not executed here; its QtCore
import is expected to encounter the same library combination, an inference from
the common load configuration rather than a newly executed application result.

Classification: an **incompatible installed application/runtime native-library
combination**, plus a confirmed **P6 post-install runtime-validation defect**.
This is not an observed Python-version error, sandbox denial or application logic
failure. The exact symbol mismatch and runtime drift are established without a
native probe, GUI rerun, library loading, package upgrade or rebuild.

The local correction is deliberately fail-closed. `RuntimeClient.verify_runtime`
re-reads the app's runtime ref and exact current runtime commit after installation;
`install_real` cannot return PASS on drift. The same guard runs before every native
phase, covering update/rollback/reinstall transactions, and records expected and
actual hashes on failure. It does not silently repin, disable dependency
resolution, edit the approved lock, change artifacts or override library paths.
It detects invalid test inputs; it does **not** claim to repair compatibility.
Signatures, permissions, sandbox settings and accepted P4 checks remain unchanged.

Seven new synthetic drift regressions pass. From a disposable clean checkout:
**50 focused tests + 15 subtests PASS**; complete release/workflow suite
**207 tests + 219 subtests PASS**, one existing duplicate-ZIP warning.
Ruff/formatting pass. Compatible Qt import after remediation is **UNEXECUTED**.
All r2/r3/r4 evidence and approved inputs are preserved. Sanitized ELF/hash/test
evidence: `ci/evidence/p6/r4-QtCore-ABI/`.

**Current owner checkpoint:** review a runtime-compatibility remediation plan,
not another full GUI run. For the exact locked A/B experiment, one candidate is an
explicitly reviewed restoration of the already approved runtime after dependency
transactions, with drift recorded and import-only validation before GUI. That
would not establish compatibility with updated Qt 6.11.3. Supported-runtime
compatibility and any rebuilt binding/package are separate decisions. None of
these mutations or native tests were performed. No additional native probe is
needed to identify this retained error; any future probe requires its own exact
reviewed command/scope and authorization first. P6 remains CONDITIONAL.

## Advisory and licensing

The [upstream advisory](https://github.com/advisories/GHSA-g3hv-75wg-m249) affects
minimatch before 11.0.1. No patched 10.x release was available in the registry.
The narrow override changes minimatch 10.2.6 to 11.0.1 and adds its development-only
`@isaacs/nonrecursive-glob-match` helper. Node 24 satisfies the fixed package's
engine requirement. All other package resolutions remain unchanged.

ESLint, config-array and typescript-estree consume this matcher in development
checks. Inspected direct calls do not request optimizationLevel >=2. No
application/editor/API path into those callers was found; this is a bounded
reachability assessment, not a formal exploitability proof. Clean installed
consumers resolve the patched version. The adversarial regression tests repeated
`**/../` patterns at levels 0/1/2 within a hard child-process budget. Full frontend
regressions pass. **All 33 production frontend files are byte-identical to the
accepted application payload**, so a redundant Flatpak rebuild was avoided.
The historical P5C finding and accepted source lock remain intact; only the new
P6 source candidate is remediated.

Candidate OSV matching completed for 341 source-lock components with no matches,
and clean npm installation reported no registry audit findings. Neither clears
unenumerated runtime/native vulnerabilities. The historical inventory identifies
PySide/shiboken 6.11.2, bundled Qt WebEngine 6.11.1 and pinned-runtime Qt 6.11.2 with
exact metadata/SPDX hashes. It indexes 34 upstream SPDX documents, 40 Python
metadata records, 2,971 ELF files and 1,553 notices across app/runtime trees. Unknown
licenses/versions, upstream NOASSERTION, static embedding, driver/extensions,
relationships and source correspondence remain limitations. R4's later runtime
drift to Qt 6.11.3 is separately recorded above, not substituted into that snapshot.
See the inventory and
[license review](P6_LICENSE_REVIEW.md).

A separate scan of the **40 actual app/runtime Python metadata records** found
three matches in runtime-only Mako 1.4.1.dev0 and setuptools 80.10.2:
[Mako Windows lookup](https://github.com/advisories/GHSA-5639-2j2p-m4mx),
[setuptools macOS sdist exclusion](https://github.com/advisories/GHSA-h35f-9h28-mq5c)
and [setuptools Windows legacy wheel installation](https://github.com/advisories/GHSA-xmj3-9gf7-h52w).
Their documented OS/build preconditions are absent from the declared Linux
application use, and direct application source has no matching imports or API
calls. Packaging consumes prebuilt hash-locked wheels rather than building sdists
inside the runtime. These are **bounded not-reachable assessments; the packages
remain unpatched**. This is not proof about every native/third-party caller or
complete vulnerability clearance. No accepted runtime pin was silently changed.
Details and reassessment triggers are in `runtime-advisory-triage.json`.

Original-code/logo rights, use-composed-ref attribution provenance, MPL covered
source and Qt/LGPL/GPL/module obligations still prevent redistribution clearance.
Existing notices/fonts and metadata-only CC0 approval remain unchanged. MIT is a
recommendation for owner review, not a selected license. No missing attribution
or legal permission is invented.

## Local verification

A disposable detached checkout with independent Git objects starts at accepted
`bfa0b800…`; exact candidate files are overlaid explicitly. A new Python 3.12 venv
installs existing exact backend requirements and hash-locked PyYAML requirements;
`pip check` passes. npm ci installs the candidate from its lock in that checkout.
Tests do not use the development venv, node_modules or prebuilt frontend assets.
The first build begins with absent frontend/dist.

| Check | Actual result |
| --- | --- |
| Focused P6 regressions | **30 PASS** in 6.652 s |
| Complete backend/security/lifecycle/migration/packaging/CI/release suite | **693 PASS + 204 subtests**, 52.76 s, three existing warnings |
| Workflow contracts | **31 PASS**, also included above |
| Frontend lint and security regression | **PASS** |
| Frontend unit tests | **273 PASS** |
| TypeScript and production frontend build | **PASS**, existing large-chunk warning retained |
| Complete production-server Chromium suite, retries 0 | **21 PASS**, 2.4 min, including all five lifecycle tests and appearance/image regressions |
| Ruff, formatting, actionlint on all three installed workflows; exact CI contract | **PASS** |
| Disposable RSA-3072 primary/subkey backup/restore/sign/expiry/revocation/cleanup rehearsal | **PASS**, 1.770 s |
| Native actual runtime retrieval and real application HTTP remote install | **PASS** component checks, 233.451 s including launch attempt |
| Independent installed source/version/schema/runtime/commit/permission readback | **PASS** |
| Full real repository HTTP GET/HEAD/hash/MIME/cache verification | **5,559 files PASS**, 9.441 s final implementation |
| Real native GUI/application initialization | **BLOCKED / launch probe FAIL**, namespace restriction before Qt |
| Real A/B GUI update, rollback/reinstall persistence | **INCOMPLETE**; r4 QtCore import fails from a Qt private-ABI mismatch after runtime drift; no window or B update verified |
| Hosted P6 / public HTTPS / independent machine | **NOT EXECUTED** |

The first full Python run had 684 passes and two failures because `/tmp` had less
than the existing 5 GiB packaging precondition. Re-execution on an isolated
larger-volume TMPDIR passed; no test, threshold, retry configuration or production
code was weakened. Initial HTTP verification took 101.350 s before verified
manifest caching; final transport verification passed in 9.441 s with per-object
hash checks preserved. Intermediate records are retained as history.

Commands and full non-sensitive result summaries are retained in
`ci/evidence/p6/verification.json`, test records and checksums. No GUI result is
inferred from browser/headless results. No native negative-security result is
substituted from unit mocks: the accepted P5C 13 native negatives remain historical
and new actual-client distribution fault gates remain separately unexecuted.

## Actual native installation

The empty private client independently fetched KDE Platform 6.11 and graphics/
codec/style extensions over the network, then pinned and verified Platform commit
`76fa01ac42ecf45d2c5020ef80de1c474c0c2ae86a51a79e8fec44c48f9dc473` with both GPG
checks enabled. BaseApp is already bundled into the application. The real
production app installed through a generated trusted flatpakref and HTTP remote,
without --no-deps and without development dependencies in the client. Installed
source is accepted `1ee2077…`, version 0.1.0, schema 5, branch stable, x86_64 and
commit `da1bf73e…de1ac`. Effective permissions pass the unchanged P4 validator.

The subsequent `flatpak run` failed with the classified
`sandbox-namespace-unavailable` error. An independent `unshare -Ur` probe reports
`Operation not permitted`. The driver correctly records overall FAIL for that
combined launch execution, preserving the passing installation components. No
sandbox flags or host security were changed. The exact isolated Ubuntu owner
commands and manual observations are in the [runbook](P6_RELEASE_RUNBOOK.md).

Measured local snapshot is 302,485,829 bytes / 5,561 files including seals; these
are **local P6 measurements**, not fabricated hosted P5C measurements. Hosting
planning uses these figures. R2 Standard remains preferred subject to owner
approval of provider/domain/budget/gateway; no infrastructure was provisioned.

## Release candidate and remaining approvals

`ci/evidence/p6/release-candidate-manifest.json` ties reference source, CI, artifact,
bundle, OSTree, disposable key, generation, descriptors, notes and inventory.
Production key and endpoint are null; publication is disabled. It is an
owner-review candidate, not a final newly built P6 release. The eventual committed
P6 source, successful CI, final artifact/audit, production trust and corresponding
source/notices must be selected together before release.

One grouped owner package is in [P6_OWNER_CHECKS.md](P6_OWNER_CHECKS.md):

1. Review the exact local source/docs/evidence; authorize a commit/push only if
   desired. No such authorization has been received. Ordinary CI will test the
   new regressions and build/audit the final candidate; no manual P6 run is implied.
2. B is approved and r2 preparation is complete PASS. Review the confirmed r4 Qt
   private-ABI mismatch/runtime drift and a bounded compatibility remediation
   before any new native execution. No full GUI retry is currently justified.
   Complete actual-client interrupted update, bad trust,
   availability/cache and other unexecuted distribution cases on capable hosts.
3. Resolve license/logo/attribution/source obligations; approve permanent offline
   identity/custody/expiry and the separately reviewed production signing policy.
4. Approve provider, HTTPS endpoint, budget, gateway/conditional-write and credential
   boundaries before any external setup. Then separately authorize public HTTPS
   and independent-client verification. No deployment is currently ready to run.
5. Review the final artifact manifest and explicitly authorize tag/release/
   publication only after all required gates and formal P6 acceptance.

P5C closeout and P6 changes remain separate review groups in the proposed file
inventory. No main merge, production key, public tag/release or publication occurs.


## Owner-authorized historical-runtime remediation — local only

1 November 2026. P6 remains CONDITIONAL. The owner authorized an explicit historical
replay policy and read-only production compatibility assessment, with no native
execution. The consolidated design, exact owner commands, stop conditions,
production recommendation and open release blocker are in
[P6_RUNTIME_REMEDIATION.md](P6_RUNTIME_REMEDIATION.md).

`historical_runtime.py` provides an exact-commit opt-in, transaction before/after
readbacks, separate drift/restoration records, origin/URL/signature verification,
a bounded restore and bounded sandbox imports for both generations before any GUI.
Normal application dependency resolution is preserved; default runtime drift still
fails closed. Existing preparations/attempts are never reused as writable clients.
This host verifier is outside the production payload; production source, package
permissions, locks, P5B allowlist and signed A/B identities remain unchanged.

New regressions cover explicit opt-in, lock agreement, all six transaction labels,
wrong origin/trust, missing history, failed/wrong restoration, interrupted
transactions, module/provider validation, private import failures, data/evidence
preservation, normal dependency resolution and the two-generation GUI gate.
The earlier 223-test run was an intermediate successful regression run. Final
clean-checkout counts and exact source hashes are recorded in
`ci/evidence/p6/historical-runtime-remediation/tests.json` and `clean-source.json`.
No native import, GUI, renderer, ordinary runtime-update compatibility or production
packaging remedy is classified as PASS on the strength of these local tests.
Historical success/failure records remain preserved; earlier recommendations against
another unchanged GUI retry are superseded only by this explicit proposed mode.


Final local verification: **74 focused tests + 24 subtests PASS; 231 release/workflow
tests + 228 subtests PASS** in a disposable detached checkout with the exact P6
source overlay. Ruff check and formatting PASS. Twenty-four new tests were added.
The sole warning is the existing intentional duplicate-ZIP negative fixture.
No native runtime restoration, import or GUI was executed. No commit/push occurred.


## R6 historical restoration ordering correction — local verification

R6 remains a recorded native FAIL. Installation and app identity verification
succeeded; explicit historical authorization and `defer_runtime_check=True` reached
the install path. The strict post-install guard did **not** cause the failure.
The actual failed child was `ostree show --gpg-verify-remote=flathub <approved SHA>`
within `runtime-signature` (sequence 54, exit 1, 0.008 seconds). The local historical
commit and detached signature objects are absent after dependency installation,
with no parent object repository. The driver's pre-restoration full signature
check therefore required an unavailable local object and stopped before any
restoration. Original child stderr was not retained; no exact original error text
or independently failed restoration is claimed.

`historical_runtime.py` now checks explicit authorization, origin, URL and enabled
GPG enforcement before restoration without reading the missing old object. The
bounded Flatpak transaction retrieves/restores only the approved commit with GPG
checks intact. Exact commit/origin, independent OSTree signature verification and
fresh live runtime identity checks follow before import eligibility. Unexpected
drift or any failed check still stops execution. The successful original install
and ordinary runtime compatibility **false** remain separate from restoration.
Signature child failures now retain private raw output through the existing safe
diagnostic helper; public evidence contains categories/hashes only.

Implementation changes are confined to `historical_runtime.py`,
`native_diagnostics.py`, existing `test_historical_runtime.py`, and new
`test_historical_install.py`. `real_update.py`, `native_distribution.py`, production
application/packaging/runtime locks, P5B signing policy and accepted artifacts are
unchanged by this correction. Existing transaction mocks are adjusted for the
new policy/result boundary; eleven new integration/security regressions exercise
the actual install/replay/import gate using synthetic I/O.

The archived R6 implementation reproduces the early failure under the same
synthetic missing-object condition; corrected ordering reaches imports without
changing ordinary compatibility to true. Readback/evidence, reproduction, tests
and exact clean-source hashes are in `ci/evidence/p6/r6-restoration-order/`.
No native restoration, import, GUI, preparation, build, commit, push or GitHub action
was executed. See P6_RUNTIME_REMEDIATION.md for the updated proposed r7 command and
r8 GUI gate. P6 remains CONDITIONAL.


R6 correction final clean-checkout verification: **85 focused tests + 24 subtests
PASS; 242 release/workflow tests + 228 subtests PASS**. Ruff and formatting PASS.
Eleven new R6 regressions were added. The single existing duplicate-ZIP warning
comes from a deliberate negative fixture. Exact source overlays, test commands,
results and preservation hashes are in `ci/evidence/p6/r6-restoration-order/`.
No new native verification was executed.


## R9 post-reinstall profile-open investigation — 2 November 2026

**P6 remains CONDITIONAL. R9 overall FAIL is preserved.** R9's initial B update
passed, followed by rollback, native backup/import and recovery PASS. The failing
`gui-updated` was the second `updated` invocation, after uninstall/reinstall B.
It had already verified the window, renderer sandbox, backend authentication,
private network/filesystem, single-instance lock, Dark preference and owned-backend
cleanup. It failed between `owned_backend_reaped` and `saved_owner_edit_checks`,
where the unchanged production `Profile(profile_root)` is constructed.

The active-workspace pointer is valid and selects an existing schema-5 imported
workspace. Read-only source inspection and integrity validation **on disposable
copies** establish that the original and active imported database bytes, logical
content fingerprints and image trees match. Each contains one synthetic note,
folder and asset; SQLite integrity/foreign-key and existing P3 validation pass.
The inactive schema-6 workspace is the deliberate future-schema refusal fixture.
All three generations retain the synthetic records and asset. The complete retained
profile remains 96 files / 8,660,684 bytes with unchanged aggregate tree hash.
No data loss, bad pointer or missing workspace was found.

**The exact missing object and originating syscall are undetermined.** The original
helper suppressed filename, errno and traceback, and set its stage only after
construction. Private stderr's only diagnostic is the known Chromium system D-Bus
warning, not a Python traceback. Present-day file existence cannot reconstruct a
transient missing entry. Removal of a Qt profile/cache entry during Profile's
strict recursive scan is a plausible hypothesis; a deterministic synthetic test
reproduces that error path, but does not prove historical causality. An application
filesystem defect versus verifier teardown timing cannot yet be distinguished.

Only the confirmed diagnostic gap is corrected. The host-streamed native helper
persists an allowlisted stage **before** each direct profile reopen and records
OSError errno, bounded path category and storage-function/source-line frames. It
never emits raw filename, traceback path, message, note content or environment.
It still calls the unchanged Profile and propagates failures; no retry, delay,
exception suppression or filesystem/security relaxation was added. The P6 parent
now labels `reinstall-b` separately and keeps `phase-reinstall-b.json` distinct
from the earlier `phase-updated.json`; active/completed phase context is retained.
Existing security, saved-content and integrity assertions remain mandatory.

Exact implementation changes:

- `packaging/flatpak/production/native_check.py`
- `ci/release/real_update.py`
- New `packaging/flatpak/production/test_profile_diagnostics.py`
- New `ci/release/test_native_phase_context.py`

The report, owner checklist, runbook, runtime-remediation status and current review
indexes are updated. Prior helper/driver/docs and original R9 success/failure
summaries are preserved in `ci/evidence/p6/r9-profile-investigation/` alongside
integrity, preservation, clean-source and test evidence. Raw child output and
synthetic image bytes remain outside the repository. Production storage/application
code, package/permissions/runtime locks, historical policy, accepted A/B archives
and signed preparation are unchanged. No preparation, GUI, native import or
runtime transaction was repeated; no commit/push/GitHub action occurred.

Clean-checkout results: **17 focused tests PASS; 109 storage/migration/packaging
tests PASS; 244 release/workflow tests + 228 subtests PASS.** The helper's 14
pre-existing E402/E501 lint findings are unchanged (no new findings); the other
changed Python files pass Ruff and all four changed Python files pass formatting.
Existing duplicate-ZIP and FastAPI/Starlette deprecation warnings are recorded.

Another separately authorized instrumented native observation is necessary to
complete post-reinstall saved-content verification and obtain exact operation
information if the error recurs. It must use a fresh attempt; preserve R9 and r2
preparation. No speculative application fix is proposed. A passing rerun alone
would not establish the historical transient's cause. Native execution is not
currently authorized by this local investigation.


## R10 authorization and Codex bootstrap restriction — 2 November 2026

The owner authorized one fresh historical-runtime GUI verification at
`historical-gui-attempt-r10`. Preflight PASS: reviewed helper/driver match the
clean-tested source; corrected pre-profile diagnostics and reinstall context are
enabled; successful signed A/B preparation and approved archives are unchanged;
prior attempt evidence is intact; R10 did not exist; production storage, sandbox,
signing and runtime controls are unchanged. Host Wayland/session sockets exist.

One driver invocation was attempted through Codex. It returned complete FAIL with
`error: OSError` before creating the attempt directory. Independent filesystem
readback shows that Codex's mount of `~/.cache/p6` is read-only and not writable.
The child-only permission grant did not make the parent writable to create R10.
This is a host execution/bootstrap restriction, not an application, import,
renderer or R9 profile failure. Exact driver errno/traceback was not retained;
the read-only parent is independently established.

**R10 native verification: NOT RUN.** No RuntimeClient, native runtime transaction,
imports, GUI, data, update/rollback, maintenance/recovery, uninstall/reinstall or
final saved-content check was created or executed. No phase is marked PASS from
historical evidence. No runtime drift/restoration or new profile-failure result
exists. No automatic retry was performed. The original terminal FAIL and separate
NOT RUN classification are retained under `ci/evidence/p6/r10-native/`; no fake
owner-result was written into a nonexistent native attempt.

The owner can perform the already-authorized one native execution from the Ubuntu
terminal using the same corrected command and still-fresh R10 root. Do not run
again if an actual native attempt has since started; an actual failure needs a
separate owner decision. Do not repeat preparation or alter prior attempts. The
Codex bootstrap failure is not a completed native GUI observation.

P6 remains CONDITIONAL. Remaining gates include actual R10 completion, ordinary
supported-runtime-update compatibility (historical restoration does not close it),
licensing/notices/inventory review, production trust/final source-CI-release
approval, and authorized public HTTPS/independent-client distribution checks.
No application code or security settings changed; no commit/push/GitHub execution,
production keys, hosting or publication occurred.


## R11 preference-contract investigation — 2 November 2026

**Confirmed cause: verification-harness contract mismatch; no production defect
established.** P4's ordinary saved-edit assertion requires explicit Dark. P6 also
compared every restart/update/rollback preference hash with the original edit
hash. Those expectations remain correct before import. They are incorrect after
native backup/import activates a new workspace: `app.migration.pack` and its
validator explicitly exclude browser preferences, recovery drafts and unfinished
uploads. `Profile.activate_workspace` selects a separate workspace-specific Qt
WebEngine profile/cache without copying the previous profile's localStorage.
The production backup/storage/frontend implementation is unchanged.

Read-only R11 evidence (`ci/evidence/p6/r11-preference-contract/`):

| Observation | Actual result |
| --- | --- |
| Edit, restart, first B update, rollback | PASS including Dark; identical preference hash `70992515ae26d5f17712ddff6e52182309267109d0eb035fce68d6c884bfca85` |
| Native backup/import | PASS; new workspace activated, owner edits and database records preserved |
| Recovery | PASS; verified restore, future-schema refusal and previous profile recovery |
| Final B after reinstall | GUI/security/identity/backend cleanup and saved title/folder/image checks PASS; overall FAIL solely for Dark at `saved_owner_edit_checks` |
| Final saved preference state | Hash `6c70b52b441be65cbbcbaf8b798a9127ac0ca4195d4684a175fcb607fd95f3fa` exactly matches `{appearance: null, theme: null}` — no override, default System |
| Resolved light/dark at final launch | NOT RECORDED; OS-dependent, cannot infer from localStorage hash |
| Live post-import/pre-uninstall preference sample | NOT RECORDED; do not claim end-to-end preference persistence from a missing sample |
| R9 FileNotFoundError | Did not recur in R11; historical cause still unresolved |

The active pointer is valid and selects a genuinely new generation. Its separate
`web-profile-<generation>` directory exists alongside the original `web-profile`.
Read-only validation on disposable workspace copies confirms identical original
and imported schema-5 database bytes and logical content fingerprints: one note,
one folder, one referenced 354,837-byte image each, SQLite integrity/foreign keys
and existing P3 validation PASS. Rich-text/image references and asset hashes are
preserved. The intentional inactive schema-6 recovery fixture remains intact.
Profile inventory is unchanged: 95 files, 8,563,881 bytes, aggregate tree SHA-256
`d73d1aa3253db0719ff74b874e60af768a13fb57eeb8725eb75f2c4b5035dbf8`.
The original R11 driver reached final verification only after its before/after
uninstall/reinstall file-tree equality assertions passed. This supports storage
preservation but does not replace a missing live preference baseline.

### Narrow local correction

- `ci/release/preference_contract.py` (new): bounded read-only observations of the
  two appearance keys, resolved DOM scheme and system color preference. Separate
  explicit reset/preserve modes, tied to hashed workspace AND Qt profile identities.
- `ci/release/real_update.py`: original edit/restart/initial B update/rollback still
  require Dark and the original preference hash. After successful import/recovery,
  a distinct `post-import-baseline` GUI phase first verifies absent keys and correct
  System rendering; the owner then explicitly selects Light. The new Light state
  must be observed and recorded before uninstall. Final B requires that exact
  imported-workspace state and identity, not the original Dark hash. The original
  security/content requirements remain mandatory, and every failed check fails
  the phase. Host-streamed composite checker hashes are recorded.
- `packaging/flatpak/production/native_check.py`: a keyword-only explicit test hook
  and hashed workspace identities allow P6 to reuse P4's security and saved-data
  checks. Direct P4 `main()` still defaults to its original strict Dark assertion.
  No command-line/environment bypass or privileged JavaScript bridge is added.
- `ci/release/test_preference_contract.py` (new) and
  `ci/release/test_native_phase_context.py`: reset versus persistence, System
  resolution, new Light baseline, missing/invalid evidence, wrong profile, lost
  preferences during reinstall, cancelled callbacks, original P4 strictness,
  unchanged other requirements and phase-record preservation regressions.

No old failed Dark assertion is changed to PASS or removed from R11. The corrected
future phases use explicitly named reset/preserve checks. No production application,
backup, Profile storage, API, package, sandbox, runtime lock or signing policy changed.
Raw child output, note contents, screenshots and browser storage are not published.

### Local verification

Fresh detached no-hardlink checkout of the current accepted integration HEAD with
exact local P6 source overlays; existing `frontend/dist` copied only for backend
test prerequisites. No application rebuild, owner GUI/native rehearsal, preparation,
GitHub action, commit or push was performed.

- Focused: **52 PASS** (35 additional cases beyond the previous 17).
- Storage/migration/production packaging: **109 PASS**.
- Release/workflow: **279 PASS + 228 subtests PASS**.
- New/changed driver and tests: Ruff PASS; five changed Python files format PASS.
  Host checker retains its 14 pre-existing E402/E501 findings, with no new findings.
- Initial broad runs encountered genuine environmental disk limits: below 5 GiB
  build prerequisite and OSTree's 3% free-space floor. Original failed outputs are
  retained. Unchanged tests pass using a disposable empty memory-backed test volume;
  no safety check was reduced. Existing duplicate-ZIP/deprecation warnings remain.

Commands, source hashes, outputs, private-log hash verification and before/after
preservation records are saved under the R11 investigation directory. These are
local synthetic results, not native acceptance or proof that the new GUI sampling
has run successfully.

### Smallest next native proposal — NOT AUTHORIZED / NOT EXECUTED

A full A/B rehearsal is unnecessary to establish R11's earlier passing phases.
Retain those actual results. For the remaining gap, propose two GUI launches around
one B uninstall/reinstall in a NEW isolated, identity-verified client:

1. Read-only validate and copy only R11's verified synthetic imported workspace
   into a fresh private profile, with fresh Qt storage. Never open or modify R11
   itself with Profile/Qt. Preserve and independently hash the source before/after.
2. Verify the approved signed B repository, source/OSTree/application identity and
   exact historical runtime origin/signatures; ordinary compatibility stays FALSE.
3. First launch: prove System default and correct OS resolution, then explicitly
   select Light; require saved note/folder/image/database/security/backend checks
   and capture a workspace-bound live Light baseline.
4. Uninstall/reinstall the same approved B without deleting data. Require whole
   private-data tree equality, exact B identity and authorized runtime restoration
   with independent commit/origin/signature validation before the second launch.
5. Second launch: require the same Light snapshot/hash, workspace identity, all
   saved-content/image/database/security checks and backend cleanup. Stop on any
   discrepancy; no retries. Keep diagnostic output private and evidence separate.

This bounded targeted entry point has not been implemented or executed. The
current `gui` command still performs the complete sequence; do not run it as a
substitute. Prepare/review the exact targeted command and its fresh directory
before requesting one native execution authorization. No preparation repeat is
needed. A new successful observation cannot rewrite R11's original FAIL or prove
R9's transient filesystem cause.

Remaining P6 blockers: targeted native verification of the corrected preference
contract; supported ordinary-runtime-update compatibility (historical replay is
not resolution); final redistribution/license/notices/inventory/trust review and
approved production source/CI/release; separately authorized public HTTPS and
independent-client distribution validation. P6 remains CONDITIONAL.


## Targeted B-only implementation and owner handoff — 2 November 2026

**LOCAL IMPLEMENTATION PASS / NATIVE NOT EXECUTED / P6 CONDITIONAL.** This section
supersedes the prior R11 checkpoint's statement that the targeted entry point was
not yet implemented. All historical R9/R11 results remain unchanged.

### Implementation and exact changed paths

New files:

- `ci/release/targeted_b.py`: separate explicit B-only CLI and supervisor; no full
  A/B GUI command or preparation call. Two real B launches surround one normal
  uninstall/reinstall, using the existing approved signed repository only.
- `ci/release/targeted_workspace.py`: strict bounded read-only retained inventory,
  existing-lock protection, P3 immutable SQLite/reference validation, exact
  synthetic-only copying and complete file/empty-directory preservation checks.
- `ci/release/targeted-b-policy.json`: fixed approved B/preparation/trust/R11 hashes,
  schema/version/identity and original synthetic data fingerprints. No personal
  contents, browser storage, signing credentials or private paths.
- `ci/release/test_targeted_b.py`: **103** synthetic cases covering identity,
  artifacts, unsafe/missing data, isolation, runtime/signature/import faults,
  preinteraction evidence, preference loss/reselection, missing baseline,
  complete tree preservation, failures, interruption and retained diagnostics.
- `ci/P6_TARGETED_B_CHECKS.md`: exact proposed owner command, capacity and signing
  validity prerequisites, click-by-click instructions for both windows and stops.

Modified files:

- `ci/release/preference_contract.py`: also records the actual selected Appearance
  option. Before input it requires absent keys + selected System + correct OS
  resolution, or the original Light baseline on launch two. Workspace AND Qt
  profile identities are bound. Any observed later preference mismatch stays
  failed even after reselection. The original baseline is never replaced.
- `packaging/flatpak/production/native_check.py`: the explicit P6 hook disables
  its test window before `show()`, records actual live Profile identity from the
  owned backend, persists preinteraction evidence, then shows owner instructions
  and enables input. Wrong evidence quits the failing test; missing readiness
  fails after a 45-second bounded gate. P4's default path is unchanged. This
  host-streamed checker is not in the production payload.
- `ci/release/historical_runtime.py`: add only `install-b` to the reviewed
  transaction allowlist; reuse the existing drift/restoration/signature/live
  identity protocol without changing its guards or production runtime locks.
- `ci/release/progress.py`: add fixed operation labels for the targeted supervisor;
  existing bounded child execution and interruption behavior remain unchanged.
- `ci/release/test_preference_contract.py`,
  `ci/release/test_native_phase_context.py`: adapt synthetic observations to the
  stronger selected-mode/preinteraction evidence; retain every prior case.
- `ci/release/test_historical_runtime.py`: require seven recorded transactions,
  preserving the original six plus initial B. New exact-allowlist regression
  prevents removing an old transaction or silently adding capabilities.
- `ci/P6_REPORT.md`, `ci/P6_OWNER_CHECKS.md`, `ci/P6_RELEASE_RUNBOOK.md` and
  `ci/evidence/p6/{proposed-files.json,SHA256SUMS.json}`; new non-sensitive evidence
  under `ci/evidence/p6/targeted-B-verification/`.

`ci/release/real_update.py` was not modified in this checkpoint; its complete A/B
mode remains distinct. Production application/backend/frontend/Profile/backup
code, workflows, packaging/permissions, runtime locks and signing policy are
unchanged. Earlier P6 frontend dependency work and P5C closeout are preserved.

### Sequence and fail-closed properties

The new attempt must be a fresh `targeted-b-attempt-*` sibling of the approved
`real-pair-r2` and retained R11 root, outside the source tree. The driver refuses
existing roots, symlinks, traversal and normal application paths. It checks a
5 GiB free-space floor before any native operation. Input preflight binds source,
CI run/attempt/artifact ID, ZIP and bundle hashes, build inputs/inventory, OSTree
commit, version, schema, public key and original approval SHA. Successful signed
preparation, source data and original failure evidence are pinned. The raw public
ZIP's reviewed ordinary readable modes are allowed only for an owned regular
single-link file; world-writable/executable/special objects are refused. Private
source/profile/approval modes remain strict.

Signed B is verified and activated solely in the fresh attempt's local store,
then served on literal loopback. It creates no new signing key and publishes
nothing publicly. A new RuntimeClient has private HOME/Flatpak/XDG directories;
normal application profiles/installations are never queried. The default package
network/filesystem/renderer/authentication protections remain mandatory.

Normal runtime dependency resolution is retained. Initial B installation and
reinstall are journaled separately; drift may only be restored under the explicit
approved historical policy, followed by independent origin/GPG/signature/live
commit validation and bounded compatible Qt import probes. Before/after probes
use separate evidence directories. The top-level ordinary-runtime compatibility
result remains FALSE even if historical restoration passes.

Only the approved synthetic active workspace is copied. R11's existing instance
lock is opened read-only; no production Profile is instantiated on R11. Its full
file and empty-directory state is checked before/after copy. New Qt storage/cache
is empty; original Qt files, other workspace generations and browser state are
not copied. The copy receives a new private profile and is independently validated
before launch. Strict source snapshot ordering matches the original R11 pathlib
inventory; a regression covers Qt profile directory prefix ordering.

The first test window cannot accept input before System/reset/OS/identity evidence
is persisted. The owner confirms synthetic content and selects Light. Only a
complete native PASS, exact saved Light baseline and copied-data validation permit
uninstall. The driver preserves the baseline file and hash, rechecks current key
trust, installed B identity and complete private-data state. Uninstall never uses
`--delete-data`; same-B reinstall rechecks commit/source/version/schema/permissions,
authorized runtime restoration and signing trust. Any changed file, empty directory
or baseline stops the second launch.

The second window is likewise blocked until original Light and both identities
are verified before input. A later selection cannot repair an observed loss. The
same original native security/saved-data requirements remain mandatory; only the
incorrect original-workspace Dark requirement is replaced with explicit imported
preference checks. The final database/record/asset fingerprint is independently
validated. Missing assertions, filesystem failures or interruption produce FAIL;
there is no retry. Safe child stage/errno/storage-line metadata and private raw
output are retained on failures. Bootstrap rejection emits a complete stdout FAIL
without writing to an unsafe/existing root.

### Verified inputs and preservation

Read-only inspection confirms B source `bfa0b8005a3ddc519354fd7907e9b972fde8126b`,
CI `41285343063` attempt 1, artifact `13075346402`, ZIP
`2d11ce5057ae66cd4dc526dac607a2344b89dbc1fcef5e62038ad59583c93fbe`, bundle
`ef732c240d8a01e33a638cd10e83fb985c7ba9e678b573ba508cd48c3934f47c`, and OSTree
`f759380dca9aa36e4674ad6dffb24d3e2340342da5fe04537ac17031a3bada15`.
Version remains 0.1.0/schema 5; production identity remains
`io.github._74Cerillion.CyrNava`.

Preparation SHA `0740b8d035d7db2904ca45d1f7bdd7265fba9157f1313d2440a83e1f2b8d5099`,
original B approval SHA `53aa5025f977629cf6ba3920b390493b6da257987663279d7e1e85c28f231a22`,
A ZIP, R11 evidence/private-output hashes and profile fingerprint are unchanged.
The original approval's legacy authorization-reference wording remains pinned;
it is not rewritten to manufacture new consent.

An actual copy of the retained **synthetic** workspace was locally tested in a
throwaway memory-backed directory, independently validated and removed. Original
R11 file/directory state remains unchanged; database bytes, note/folder/image
counts, rich text, references and asset hashes match. This was only a local data
copy check, with no Profile/Qt/application/runtime operation. Raw contents were
not placed in repository evidence. The proposed R12 native attempt does not exist.

Existing signed-manifest verification and the entire signed B public file tree
PASS. Independent current-signature verification PASS at
`2026-11-02T03:14:08Z`; fingerprint
`B8882601428AC0F08E9209FC353B6BEE05E7D9FC`, public key SHA
`26760a8972ac9ea2eedc63830fb0abf8b0f918e9c06808c81a0c884abc3311d4`.
The key expires **2026-11-02 09:32:43 UTC / 18:32:43 KST**. No key renewal,
clock override, expiry bypass, re-signing or re-preparation is authorized. Native
OSTree/client validation is still required during the future targeted execution;
read-only signed-manifest validation is not reported as a new native rehearsal.

### Clean local results

Fresh detached no-hardlink checkout at `bfa0b8...`, exact source/policy overlays,
existing frontend assets copied only for backend-test prerequisites. Final source
hashes and commands are recorded in the new evidence directory.

- **202 focused tests + 10 subtests PASS.**
- **109 storage/migration/production packaging tests PASS.**
- **382 release/workflow tests + 229 subtests PASS.**
- Changed/new driver/tests pass Ruff and formatting. The host helper retains its
  14 pre-existing E402/E501 findings, with no new findings or global suppression.
- Existing duplicate-ZIP and framework deprecation warnings remain documented.

Existing storage/security/signing/lifecycle/workflow regressions remain enabled.
These are synthetic local results; native PASS is not inferred from mocks. No
application rebuild, real A/B preparation, native runtime installation/restoration,
GUI, commit, push or GitHub execution occurred.

### Owner checkpoint and remaining blockers

The exact command and both GUI procedures are in
[P6_TARGETED_B_CHECKS.md](P6_TARGETED_B_CHECKS.md). Request separate authorization
for one execution only after capacity is sufficient and current signing trust is
valid. The host currently has about **1.2 GiB free**, below the 5 GiB gate; native
execution is therefore not currently ready. Do not delete retained evidence or
personal data without separate approval. If the key expires first, stop for a
separate trust/preparation decision rather than bypassing policy.

Outstanding: actual targeted native preference/reinstall verification; ordinary
supported-runtime compatibility; redistribution/licensing/notices/inventory and
production trust/final source-CI-release approval; authorized public HTTPS and
independent-client distribution verification. R11 remains original FAIL, its
previous actual passing phases are retained, and R9's missing object remains
unresolved. P6 is not accepted or ready for public release.
