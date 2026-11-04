# N1 accepted — N2 implementation is separate

3 November 2026. N1 is formally **ACCEPTED / COMPLETE**. Its experiment, inputs,
commands and saved evidence remain unchanged. N2 alone is now authorized; see
[N2_REPORT.md](../../../ci/N2_REPORT.md) and the
[focused installed-desktop handoff](../../../ci/N2_OWNER_CHECKS.md).
Do not rerun the N1 commands. N3/N4 remain planned and unauthorized.

---

# Historical N1 closeout review — 3 November 2026

# Current N1 closeout — 3 November 2026

**N1 — VERIFIED PASS / RECOMMENDED FOR OWNER ACCEPTANCE.** The owner completed the
actual edit/reopen application check; both real launches and saved synthetic state
passed. Independent source, dependency, renderer and evidence review is recorded in
[ci/N1_REPORT.md](../../../ci/N1_REPORT.md). Formal owner acceptance is pending.
Do not rerun the completed handoff or reset its profile/output. No code, candidate
inputs, commands or result JSON were changed during documentation closeout.

Active target: native Ubuntu installation via GitHub Releases. N2 installer/desktop
integration, N3 manual updater/uninstaller and N4 native CI/release preparation
remain planned and unauthorized. Flatpak is paused historical/fallback, not a
second completion gate. This experiment does not certify an installed release.

---

# Historical handoffs and corrections — retained; do not rerun

# Current N1 application handoff — 3 November 2026

The owner-host renderer probe is independently verified PASS. Full N1 remains
conditional until the actual application edit/reopen check. Run the single tested
`check_application.py --owner-host` command in
[ci/N1_REPORT.md](../../../ci/N1_REPORT.md). It launches the unchanged candidate
window twice, uses only synthetic data, validates saved records/images with the
existing validator, samples owned processes/security and asks for explicit visual
confirmation. 54 fixtures/lint and a real target-Python offline state check PASS.
No GUI run by the agent; no candidate rebuild, host setting or N2–N4 change.
Earlier handoffs below are completed historical commands, not steps to repeat.

---

# Current N1 role-check correction — 3 November 2026

The schema-corrected owner probe reaches a namespace/seccomp-protected diagnostic,
but its renderer-role assertion is unresolved. Strict role parsing now supports
Chromium's flattened process title, preserves every security predicate and captures
private cmdline evidence. The old argv was not saved, so this is not a retroactive
PASS. 43 local tests/lint pass. Corrected native verification is pending; exact
fresh-output command and the last-three-prompts report are in
[ci/N1_REPORT.md](../../../ci/N1_REPORT.md). The candidate and failed outputs remain
unchanged. Earlier handoffs below are historical; do not repeat them. No N2–N4 work.

---

# Current N1 schema correction — 3 November 2026

The owner startup diagnostic captured the fatal Qt GTK3 -> GTK/GDK -> GSettings
call chain. Its inherited schema override hides modern font keys. N1 is still
BLOCKED/not accepted; this is not a renderer-sandbox result. The explicit
`run_probe.py --ubuntu-system-schemas` mode now selects verified Ubuntu schema
files only for its child and uses fresh `owner-system-schemas*` outputs. The original
candidate, receipt, renderer script and failed evidence remain unchanged. All
renderer-security requirements remain enforced; no GNOME setting or global
process environment is changed. See the exact one-time command in
[the owner checklist](../../../ci/P6_OWNER_CHECKS.md). 33 local N1 tests and Ruff/
formatting pass. The corrected native mode has not executed. N2–N4 remain planned.

The following startup-only handoff has already executed; keep it and the original
probe instructions as historical records, not commands to repeat.

---

# Current N1 startup investigation — 3 November 2026

Owner-host renderer probe executed: BLOCKED, exit -6, GLib/GIO missing antialiasing
schema key; normal application launch NOT EXECUTED. N1 is not accepted. The current
findings and one separate startup-only diagnostic command are in
[the owner checklist](../../../ci/P6_OWNER_CHECKS.md) and
[the report](../../../ci/P6_REPORT.md). `diagnose_startup.py` collects private GDB
startup/library diagnostics without a renderer, window or backend. It has not run
on the owner host. Keep the original candidate and probe outputs unchanged; do not
repeat the historical owner-probe command below. No N2–N4 work is authorized.

---

# Historical 2 November experiment and original owner handoff

# N1 disposable native feasibility

**2 November 2026: assembled; N1 BLOCKED, P6 CONDITIONAL.**
Normal-user filesystem/network privilege tradeoff is owner-approved. Renderer
sandbox weakening is not approved. This is not an installer or release archive.

Actual experiment: `ci-output/p6-native-n1-1/`. Keep it at that path: its private
Python3.14 venv and receipt are not relocatable. No normal installation, desktop
entry, Flatpak runtime, accepted artifact or personal profile is modified.

`dependencies.json` records official supplier URLs, exact filenames, versions,
sizes, hashes and dependency metadata for 19 runtime wheels. `requirements.lock`
pins them for offline binary/hash-checked installation. All four Qt distributions
are6.11.3; backend versions match existing production pins, with cp314 native wheels.
No pytest/Ruff/Node runtime is installed in this environment. Frontend was rebuilt
from a copied current source tree using existing pinned Node/npm/node_modules,
without replacing the checkout's frontend/dist or node_modules.

`prepare.py` is the bounded assembly recipe; **do not repeat it** for the already
assembled candidate. It refuses existing outputs. It builds no Qt/Chromium, creates
its venv at the final path, uses a3GiB allocation cap and1.5GiB disk headroom, copies
only application sources and generated frontend assets, and emits a receipt and
separate development identity. The only shared application change is an explicit
native-N1 build-identity dispatch; normal Flatpak configuration remains enforced.
The N1 configuration template is not in the production packager's source allowlist.

## Actual results

- Private wheel installation/pip check PASS; 267,053,918 bytes downloaded.
- Provider/import/ELF check PASS: Python3.14; PySide/shiboken/Qt/WebEngine6.11.3;
  3,920 installed wheel-file hashes verified; loaded Qt from the private environment;
  no missing selected ELF dependency; QtCore binding/provider private symbols match.
- Real Python3.14 backend/authentication/synthetic folder/rich-note/raster-image
  save, restart, stable origin, stale-token rejection and owned-child cleanup PASS.
- Minimal offscreen HTML/JavaScript load PASS. This is not the CyrNava window,
  actual GNOME Wayland rendering, visual/clipboard verification or N1 acceptance.
- Offscreen Chromium diagnostic: Layer1 None, PID/network namespace No, seccomp Yes.
  Actual matching helper process has NoNewPrivs1 and Seccomp2, but user/PID/net/mount
  namespace separation is false. **Required renderer security gate not passed.**
- Confined parent is bwrap//&unpriv_bwrap. Raw graphics logs contain DRM access
  denials; they do not establish an AppArmor/user-namespace cause. Ordinary host
  behavior is untested. No host policy change is justified from this result alone.
- 17 N1 policy fixtures,147 relevant application/security/migration regressions,
  and36 existing production packaging regressions PASS. The147/36 suites use the
  existing Python3.12 developer environment; the actual target-backend check uses3.14.

Private raw logs and synthetic DB/images remain inside the ignored candidate.
Safe assessment and retained checks are under ci/evidence/p6/native-n1-2026-11-02.
Initial receipt/configuration and results were retained before narrowly hardening
helper-path validation; final provider validation passed after that change.
The original diagnostic scripts preceded the final owner-handoff hardening:
new owner-probe code is fixture-checked, **not claimed executed** on Wayland.

## Smallest owner handoff — one security probe, not an editing rehearsal

The candidate now exists. From the normal Ubuntu terminal, the reviewed command is:

```bash
cd /home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
python3 -B packaging/native/feasibility/run_probe.py \
  --candidate "$PWD/ci-output/p6-native-n1-1" \
  --receipt-sha256 7f713ed31e2ce7d63a1a67e806d671b38ff2f7bafd2d66592f68ff70d575c41e \
  --owner-host
```

**No visible CyrNava window is expected.** It initializes Wayland and a private
Qt WebEngine sandbox-diagnostic page, then exits. Child deadline25 seconds, with
up to10 additional seconds for retained-process cleanup. No network download,
backend, note editing, signing, installation, override or AppArmor/sysctl change.
Receipt/hash/platform/helper/provider/renderer-role/namespace/seccomp evidence
must agree. Missing/inaccessible evidence remains BLOCKED. Source, output and
profile paths are restricted to this disposable experiment. Repeating the command
refuses existing owner results; do not delete them to retry.

Share `ci-output/p6-native-n1-1/owner-sandbox-result.json`; keep `*.private.log`
local. Its PASS would mean the renderer security probe passed, **not full N1**.
If it passes, the next N1 step is a short normal CyrNava-window/GUI persistence
check using this same reviewed stack and synthetic data. If it fails, stop and
inspect the retained evidence before proposing any app-specific integration.
Do not disable sandboxing or permit namespaces for the generic Python interpreter.

Other scripts: providers.py records imports/maps/ELF only; backend_check.py uses
an isolated synthetic backend profile; smoke.py retains the initial supplementary
content probe; sandbox_probe.py is the bounded child; run_probe.py is its safe
owner supervisor; test_n1.py runs offline policy fixtures. These are N1 tooling,
not shipped application features. No N2 installer/updater implementation is included.
