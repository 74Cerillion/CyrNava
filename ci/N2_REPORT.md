# N2 — ACCEPTED / COMPLETE

3 November 2026. The owner formally accepted N2 and authorized N3 only:
“I formally accept N2! Go ahead and begin on N3.”
Acceptance record: `ci/evidence/n2/formal-owner-acceptance.json`.
The accepted candidate remains `0.1.0-n2.3`, archive SHA-256
`02f6594eb0011a90fe70de90c7bd382725be4c88bb0fabb73fd43e6f6d5061cf`;
its original native attempt-6 FAIL and separately supplied visual confirmation
retain their exact identities. No past result is rewritten. N3's independent
implementation/current conditional status is in [N3_REPORT.md](N3_REPORT.md).
N4 remains unauthorized. Earlier acceptance-pending text below is historical.

---

# Historical checkpoint — VERIFIED PASS / recommended for owner acceptance

3 November 2026. The completed client-5 GNOME Applications-menu run independently
verifies the corrected entrypoint and renderer context. The owner subsequently
confirmed **all** requested visual observations in this chat. **N2 technical
verification is complete; formal N2 owner acceptance remains pending.** No further
GUI run is required for this confirmation failure. N3/N4 remain unauthorized and
unstarted. This is not production signing, installer publication or public-release
acceptance.

## Attempt 6: actual results and final confirmation failure

`ci-output/native-n2-owner-6/result.json` remains **FAIL / complete**, SHA-256
`f7bcb8ee8d283f8fb8bb393137f60eb5fdb03f53dfc963db36c1c97a5e543151`.
Private traceback inspection identifies the exact ValueError:
`Menu visual confirmation missing`, from the final confirmation assertion.
Its private log SHA-256 is
`56c0c857e779ceb5f00373078b6be02e4c1147b3dbb20f94e633e4c410798d7b`.
The exact response typed at that original terminal prompt was not retained; an
empty/nonmatching confirmation cannot be distinguished retrospectively.

| Actual saved evidence | Independently verified result |
| --- | --- |
| GNOME discovery | Correct entry path/ID/name; visible; temporary registration removed |
| Installed identity | Client 5 / `0.1.0-n2.3`, manifest `d7d0f2bbc58c17aef58fff83c4e2e805875f013df8aa061830a687e07d3c688f` |
| Live application | Backend, exact private Qt providers and exact AppArmor labels PASS |
| Actual renderer | Correct role/helper, stable identity, user/PID/network namespace separation, NoNewPrivs and seccomp PASS; no proc-read errors |
| Authentication and exit | Unauthenticated backend request rejected; owned-process cleanup PASS; external GNOME child's numeric exit code unavailable, not invented |
| Post-close data/origin | Both exact snapshots SHA-256 `0feb528634201a68d00568fdfea73f34b279fae9cc5fe69bc1e474c34869a710`; required folder/note/bold/image/schema 5 intact |
| Owner visual confirmation | Separately supplied in this chat: “Yes, all were correct” to the explicit menu/window/icon/grouping/note/image/Dark question |

`observation.json` SHA-256 is
`81a29e0e9305f69309f515c99f02062e575aa3146022ec6401300eeae314b80b`.
It has no missing checks and every required live predicate PASS. Reaching the
visual prompt proves the original exact post-close snapshot assertion completed;
the retained matching snapshots independently establish the same result.
Earlier GUI edit/restart and signed-install fixture results retain their original
scope. No old failure is rewritten or promoted: a separate evidence review combines
the actual attempt-6 component passes with the owner's later visual confirmation.

## Confirmed driver defect and local correction

The original driver printed its close instruction only once, then repeatedly
scrolled detailed successful process diagnostics over it. Its 30-second limit
applies to **incomplete security evidence**, not to waiting for the owner to close
after all checks have passed; the latter has the existing ten-minute limit.
Thus the five-minute progress loop is consistent with waiting for close, not an
application or renderer hang. The missing final confirmation caused overall FAIL.

Only `packaging/native/verify_menu.py` and its focused test file changed:
successful live checks now repeat a prominent CLOSE instruction every five seconds;
full diagnostics remain in the evidence. Blank/unrecognized confirmation input
re-prompts up to three times, while NO, missing input, interruption or exhausted
attempts still cannot PASS. Completed data/origin checks and the explicit
owner-confirmation stage are saved before prompting; confirmation errors receive
safe operation categories. Required security predicates are unchanged.

**153 relevant N2 regressions PASS, zero failures/errors/skips; Ruff and formatting
PASS.** Seven new cases cover close reminders, failed authentication, blank input,
invalid input, rejection, EOF and interruption. No native GUI, host-policy change,
package rebuild/download, new key/signature or Git operation was performed.
Candidate/archive/receipt/providers, accepted N1 inputs and earlier failure hashes
were independently rechecked. No application or production storage code changed.

Sanitized review, separate owner confirmation, test result and executed checker
snapshots: `ci/evidence/n2/menu-confirmation-closeout-2026-11-03/`.
The sole next checkpoint is **formal N2 owner acceptance**. Do not rerun the
historical commands below. N3/N4 require separate authorization.

---

# Historical checkpoint — owner policy correction verified PASS

3 November 2026. **Old-profile removal, new enforce-profile loading and installed
non-GUI bootstrap: VERIFIED PASS. N2 remains CONDITIONAL pending the focused
new-candidate GNOME menu/renderer/security check and formal owner acceptance.**
The saved owner results and current kernel metadata were independently read back;
no GUI, host-policy change, rebuild or test rerun was performed in this review.

| Actual owner result | SHA-256 | Verified scope |
| --- | --- | --- |
| `ci-output/native-n2-policy-owner-remove-1/result.json` | `50b3bf0bf6c748554847cdd124282da5b4cd7d712249309b297fcaaee77fde0c` | PASS/complete; exact failed client-4 profile/file removed; kernel ABSENT |
| `ci-output/native-n2-policy-owner-load-2/result.json` | `f1c35d5ad650941901b39a52f33e1e21311e47f559d16f00377520846276a1a3` | PASS/complete; client-5 profile loaded; kernel PRESENT, enforce |
| `ci-output/native-n2-policy-owner-load-2/bootstrap-check.json` | `51003ab96ba1275f6fdf57b7c1dcba78e769296a7c16885faefa9cb5176ee0d1` | PASS; installed bootstrap entered exact named enforce profile; normal window and renderer NOT EXECUTED |

Independent current readback confirms old profile
`cyrnava-native-u1000-7433bedfe88bfbd3a297b6304c49b7f6` and its policy file are
absent. The new profile
`cyrnava-native-u1000-3a204b7f4af431e67379cf52f5c54981` is present exactly once
in readable kernel metadata, mode `enforce`, ABI `v5`; its root-owned source file
has SHA-256 `48cd1e0b685e5f8d4b84f08e2790ff5e5c8e2f220861ae5199f3e6597a619841`.
The global user-namespace and AppArmor user-namespace restriction settings both
remain `1`. No kernel/source serialized-byte equivalence is inferred.

Candidate/client 5 retains the archive, manifest, installed receipt, application
and dependency identities listed below. The saved bootstrap reports the expected
Ubuntu schemas and all required font keys. These results establish policy loading
and bootstrap attachment; they do **not** establish renderer sandbox operation.
Earlier 146 regression passes are retained results, not newly executed tests.
Sanitized review and original-result hashes are preserved in
`ci/evidence/n2/policy-owner-success-2026-11-03/`.

## Remaining focused owner check

In **GNOME Terminal outside VS Code/Codex**, run the existing reviewed checker
against client 5 with a fresh output directory. Do not repeat the policy script,
installation, editing or earlier application rehearsal.

```bash
cd /home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
/usr/bin/python3.14 -B packaging/native/verify_menu.py --owner-host \
  --root "$PWD/ci-output/native-n2-client-5" \
  --manifest-sha256 d7d0f2bbc58c17aef58fff83c4e2e805875f013df8aa061830a687e07d3c688f \
  --output "$PWD/ci-output/native-n2-owner-6"
```

Press Enter when prompted, then use GNOME Activities / Show Applications and click
**CyrNava — N2 Candidate** once. Inspect the existing synthetic note, image, Dark
appearance, icon and window grouping without editing. Close normally when the
terminal prints **renderer/providers/auth PASS** and its close instruction, then
type `CONFIRM N2 MENU` only if the requested visual observations are correct.
The checker prints progress every five seconds and rejects incomplete live evidence
after 30 seconds; if it fails, close the candidate normally and preserve the output.
Do not wait indefinitely or retry automatically. The temporary menu registration
is removed only if unchanged; normal application data is not used.

This actual run must verify the changed entrypoint's GUI/backend/helper enforce
labels, renderer user/PID/network namespaces, NoNewPrivs, seccomp, exact private
providers, backend authentication, cleanup and identical saved data/origin. Earlier
GUI/edit/restart evidence is inherited explicitly only for unchanged application
and data inputs. N1 remains accepted; N3/N4 remain unstarted and unauthorized.
No code, probe inputs, signing, Git writes or publication changed in this review.

---

# Historical checkpoint — owner load reached kernel; policy-mode correction ready

3 November 2026. **N2 CONDITIONAL.** The owner-host operation successfully created
the reviewed policy file and loaded its named profile. It then failed the
post-load mode assertion: the kernel reports **unconfined**. This owner attempt
was not blocked by sudo elevation. Its original BLOCKED/complete result remains
unchanged; the actual failure classification is a post-load verification failure.
No CyrNava GUI execution occurred.

## Confirmed failure and correction

`ci-output/native-n2-policy-owner-load-1/result.json` SHA-256:
`639a21c86312bc61840978657bfa360240f46a5cbc2a420e1253b58810318060`.
Private stderr says `Loaded profile mode unverified; preserve file`; its SHA-256
is `24b8eefdbf4a64450126fa28e59b620ff19fe34482ff4a9eeeb67c6034f9acd6`.
The root-owned policy file has the approved SHA-256
`4ca488c1d40b5b82dbd18369e698c8a8ec69ad965e74fe27b974a1ee0de30d7b`.
The public per-profile kernel metadata independently exposes the exact name,
mode `unconfined`, ABI `v5` and recorded kernel hashes. The global profile listing
is still unreadable inside Codex; per-profile metadata is a separate readable
interface. No owner probe was needed to collect this existing information.

The implementation incorrectly assumed `default_allow` would produce an enforced
or allow-mode label on this host. Upstream documents an implementation of that
flag using the unconfined flag; the observed host behavior matches that mapping.
See [AppArmor's default_allow implementation note](https://gitlab.com/apparmor/apparmor/-/merge_requests/1109)
and [AppArmor 5 mode documentation](https://apparmor.net/man/5.0/apparmor.d/).
The readback guard correctly stopped. Accepting `unconfined` as success would hide
the construction mismatch and is not the correction.

The replacement uses **explicit enforce mode with `allow all,`**, plus the exact
namespace allowance and interpreter/helper inheritance rules. This retains the
already-approved ordinary-user filesystem/network access model: it does not add
host capabilities, remove Linux DAC checks or claim an outer application sandbox.
Attachment remains one exact per-user native ELF path. Renderer namespaces,
seccomp, NoNewPrivs, backend authentication and data protections stay mandatory.
The native ELF, Python bootstrap and menu observer now accept **only the exact
named `(enforce)` label**. The older default_allow policy can be reproduced only
for checksum-pinned removal; new loading of that legacy contract is refused.

The policy helper records actual kernel state before/after operations and emits
an explicit `loaded-policy-mode-rejected` category with safe actual-mode values
if a future post-load check fails. This distinguishes a successful add followed
by rejected mode from privilege failure. Unexpected raw child output stays private.

## Actual local verification and immutable replacement

**146 focused/relevant N2 tests PASS, zero skipped; Ruff/format PASS.** Regressions
cover the exact successful-add/unconfined-readback failure, strict C/Python/helper
mode rejection, kernel metadata, legacy-removal-only eligibility, namespaces and
NoNewPrivs with otherwise correct labels, transaction recovery and actual non-GUI
GIO quoting. Parser-only validation of the enforce policy PASSes without warnings;
no kernel load/cache write occurs in that check.

| Replacement item | Identity |
| --- | --- |
| Archive | `ci-output/native-n2-candidate-5/CyrNava-0.1.0-n2.3-ubuntu-x86_64.zip` |
| Archive SHA-256 | `02f6594eb0011a90fe70de90c7bd382725be4c88bb0fabb73fd43e6f6d5061cf` |
| Manifest SHA-256 | `d7d0f2bbc58c17aef58fff83c4e2e805875f013df8aa061830a687e07d3c688f` |
| Installed client | `ci-output/native-n2-client-5/` |
| Installed receipt SHA-256 | `c4a9d2ef3cebebe6e3fc2c3c202d88d18431f1b77771fc3a4076a943b433678a` |
| ELF SHA-256 | `be28c1875f1a8ba9b17aa227b1981675c110579f71fa3ca28090530a1f877c05` |
| New profile | `cyrnava-native-u1000-3a204b7f4af431e67379cf52f5c54981` |
| New policy SHA-256 | `48cd1e0b685e5f8d4b84f08e2790ff5e5c8e2f220861ae5199f3e6597a619841` |
| New policy state at this historical checkpoint | Prepared/parser PASS; ABSENT from readable kernel metadata; not loaded |

This is a thin offline assembly and fresh disposable installation, with no
Qt/Chromium/frontend rebuild or downloads. Application bytes, the N1 receipt,
dependency locks and Qt/PySide/Shiboken/WebEngine 6.11.3 inputs remain unchanged.
Candidate 5 remains unsigned/disposable; no production trust is asserted.
All 4,414 provider hashes and actual target-Python backend/auth/origin/data/restart/
cleanup checks PASS. A cold copy of the existing synthetic profile was independently
inspected read-only: `ci-output/native-n2-owner-4005/result.json` verifies the same
saved folder/rich note/image/schema/database/origin state hash
`0feb528634201a68d00568fdfea73f34b279fae9cc5fe69bc1e474c34869a710`.
This is not new GUI evidence. Candidate/client 4 and all failed records are retained.

New candidate plus client allocate 1,277,722,624 bytes (about 1.19 GiB), below this
correction's 2 GiB allowance. Available repository space after verification is
12,982,280,192 bytes; `/tmp` has 3,618,746,368 bytes available. The existing 5 GiB
floor is satisfied. Only the small 16,944-byte bootstrap was compiled (0.080 seconds,
128 MiB address-space/60-second CPU ceilings). No retained output was deleted.

Original owner evidence, safe review and executed source snapshots are preserved
under `ci-output/native-n2-policy-mode-review-1/` and
`ci/evidence/n2/policy-mode-correction-2026-11-03/`. Kernel raw hashes were recorded
separately; a local serialized-stream hash did not match, so byte-for-byte kernel
policy equivalence is not claimed. Actual loaded name/mode and source-file hashes
are direct observations. No completed P1–P5/N1 phase is reopened.

## Already-authorized correction handoff — no GUI

Open the **GNOME Terminal application**, for example with Ctrl+Alt+T, outside the
VS Code integrated terminal and Codex. The script checks its parent context and
refuses inherited confinement/NoNewPrivs before changing any policy. It never
clears a flag or bypasses the terminal's confinement.

```bash
bash "/home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava/ci-output/native-n2-policy-mode-review-1/correct-policy-on-owner-host.sh"
```

The script checks current source hashes, removes **only the exact failed client-4
profile/file** using its original manifest/policy pins, then loads **only the new
client-5 profile**. It uses fresh `native-n2-policy-owner-remove-1` and
`native-n2-policy-owner-load-2` evidence directories. Collisions, changed files,
live profile processes or unexpected modes stop the sequence. There is no global
reload, generic Python grant, setting change or automatic retry.

After a successful load it runs the installed ELF's **non-GUI `--check`** and saves
`native-n2-policy-owner-load-2/bootstrap-check.json`. Expected results: old policy
REMOVED, new policy LOADED in enforce mode, bootstrap PASS with normal-window and
renderer fields **NOT EXECUTED**. The parent's ordinary admin context and the
renderer requirement for NoNewPrivs=1 are distinct; no security flag is changed by
this script. Bash syntax and the refusal guard have been checked locally.

The old client-4 profile remains loaded until this exact removal succeeds. Do not
repeat the old loading script or use an old menu command. The corrected host
sequence has not run here because Codex cannot elevate. After its result is reviewed,
the focused normal-menu renderer/security test still has to run on the new candidate.
No GUI, signing, publication, commit/push or N3/N4 work was performed in this review.
N1 remains accepted; formal N2 acceptance remains pending.

---

# Historical checkpoint — launcher implemented; privileged Codex load blocked

3 November 2026. The owner authorized **local implementation and host policy
loading**. Local implementation/installation verification PASS. **N2 remains
CONDITIONAL**: Codex cannot elevate to load the policy, and the changed candidate
has no native GUI/menu security result yet. Loading is already owner-authorized;
the remaining terminal handoff is a privilege-boundary requirement, not a request
to approve the same host change again. N1 remains accepted; N3/N4 remain unstarted.

## Implemented and verified locally

- `packaging/native/bootstrap.c`: dedicated 16,944-byte ELF; locates its root from
  `/proc/self/exe`, rejects unsafe arguments/environment/layout, and requires the
  exact named AppArmor label before executing system Python. No script-name
  attachment, generic Python grant, sandbox-disable flag or setuid fallback.
- `desktop/install_engine.py`: installs and hashes the bootstrap/profile identity,
  uses `/usr/bin/env --` in the Desktop Entry, preserves journal/recovery guards,
  and checks policy identity again before and after private-interpreter reexec.
  Direct Python invocation cannot bypass the new candidate's policy requirement.
  Historical manifests/entrypoints remain readable for their original evidence.
- `packaging/native/apparmor_support.py`: exact-path ABI 5.0/default_allow policy,
  namespace allowance and three explicit inherited-exec paths; separate prepare,
  load and removal operations. Loading requires pinned manifest/policy hashes,
  root-owned exclusive creation, parser validation, add-only loading and root
  readback. Root runs a literal under isolated system Python, never imports a
  user-writable repository module. No installer-triggered sudo or global reload.
- `packaging/native/build_candidate.py`: assembles a fresh n2.2 candidate offline
  with the unchanged N1 application/dependency inputs, native source/executable
  hashes, compiler provenance and assembly-source identity.
- `packaging/native/verify_menu.py`: accepts an explicit new client/manifest and
  additionally verifies the expected GUI/backend/helper AppArmor context, retaining
  all original renderer/authentication/provider/data checks and bounded diagnostics.
  Unreadable or wrong labels cannot PASS. Earlier GUI results are inherited only
  for unchanged inputs; the changed entrypoint/context needs its own actual run.
- `packaging/native/test_apparmor.py` and `test_menu_observation.py`: regression
  coverage for the above boundaries, real non-GUI GIO Exec expansion, policy
  collisions, interrupted transactions, changed-target preservation and reversal.

**140 focused/relevant N2 regressions PASS; zero skipped.** Scoped Ruff and format
checks PASS. The C build uses warnings-as-errors, PIE, RELRO, immediate binding,
stack protection and a non-executable stack. Missing-profile refusal was also
observed with the actual installed ELF before Python/GUI execution. GIO quoting
with spaces, percent signs, dollar signs and quotes passes with a synthetic child;
this is not a normal-menu application result.

The first broad test invocation included a nonexistent class name and returned a
loader error; its 134 real cases passed. That invocation is retained in
`ci-output/native-n2-apparmor-review-1/tests.log` and `tests.json`. The corrected
134-test run and final 140-test run have separate records. No real signing test,
new key, GUI/probe or historical Flatpak rehearsal ran.

## Actual new candidate and installation identity

| Item | Identity |
| --- | --- |
| Archive | `ci-output/native-n2-candidate-4/CyrNava-0.1.0-n2.2-ubuntu-x86_64.zip` |
| Archive SHA-256 | `4e66cbb270d050f9d1a954c0060c3fd0fcdbcd8bf7971d4afd3ba407e48d9c39` |
| Manifest SHA-256 | `c9744e49abd66698107408b4a502b3cce46816e116a036c2fe20fd51ca9496db` |
| Installed client | `ci-output/native-n2-client-4/` |
| Installed receipt SHA-256 | `b3f56b57115bc22df4bc6c086014fb05837cb24d7f70889c39f1d36eabd2ae97` |
| ELF SHA-256 | `353298fb2dfc87718f6f98e2ad3d291e20ffc6059a14bbce40f0bc2307a6ae5c` |
| Profile | `cyrnava-native-u1000-7433bedfe88bfbd3a297b6304c49b7f6` |
| Exact policy SHA-256 | `4ca488c1d40b5b82dbd18369e698c8a8ec69ad965e74fe27b974a1ee0de30d7b` |
| Trust scope | Unsigned, checksum-pinned disposable candidate; no production trust asserted |

Application source remains the recorded N1 baseline/patch; the manifest separately
identifies all current N2 source bytes and the assembler. No Git commit was made.
Offline installation, pip consistency, all **4,414 hashed provider files**, private
Qt/PySide/Shiboken/WebEngine **6.11.3**, ELF closure and required resources PASS.
The real target-Python synthetic backend passes authentication rejection, origin
rejection, folder/rich-note/image saving, restart/data integrity, stable origin,
stale-token rejection and owned-backend cleanup. No QApplication or renderer was
started by these checks.

A cold copy of the existing owner-confirmed synthetic client-3 profile was made
inside client 4, preserving the source. All 47 file hashes match. Read-only target
inspection at `ci-output/native-n2-owner-4004/` confirms the exact earlier saved
folder/note/image/schema/database/origin snapshot:
`0feb528634201a68d00568fdfea73f34b279fae9cc5fe69bc1e474c34869a710`.
This is input preparation/read-only validation, not a new GUI or restart PASS.
Normal application data and existing attempts were not modified.

The available compiler was Ubuntu GCC 15.2.0. The bounded bootstrap compilation
took **0.079 seconds**, with a 128 MiB address-space and 60-second CPU ceiling.
These are enforced bounds, not a claim of measured peak RSS. The archive is
271,569,357 bytes. Candidate plus client allocate **1,277,718,528 bytes** (about
1.19 GiB), within the 2 GiB budget. Available repository filesystem space after
assembly/installation was 14,272,696,320 bytes; `/tmp` remained at 3,619,303,424
available bytes. The 5 GiB repository free-space floor was satisfied. No Qt,
Chromium, application/frontend rebuild, dependency download or cleanup occurred.

## Policy preparation PASS; actual loading BLOCKED

`ci-output/native-n2-policy-prepare-1/result.json`: PREPARED / complete; actual
AppArmor 5.0.2 parser check PASS (`-Q -K -j1`, no kernel load/cache write).
The attachment is only the new client-4 ELF. Explicit `ix` paths cover system
Python, this release's private interpreter and its matching WebEngine helper.
The process-family allowance and user-writable-path limitations in the proposal
below remain applicable; it is not an outer sandbox or signature boundary.

The authorized noninteractive load was attempted once:
`ci-output/native-n2-policy-load-1/result.json`: **BLOCKED / complete**.
Private stderr confirms sudo refused elevation because **NoNewPrivs is set**.
This Codex process also has zero effective capabilities and inherited confinement.
The root helper never executed; no policy file was created and this attempt loaded
no profile. Kernel profile-registry readback is denied here and is not fabricated.
Raw stderr is retained privately; sanitized diagnosis is in
`ci-output/native-n2-apparmor-review-1/policy-load-review.json`.
No elevation retry, global sysctl change or security bypass was attempted. Both
namespace-related sysctl values remain `1` as before.

## Already-authorized owner-terminal loading handoff

Single-script entry point:
`ci-output/native-n2-apparmor-review-1/load-policy-on-owner-host.sh`.
It locates this repository, checks the reviewed installer/helper source hashes,
prints the sudo/no-GUI scope, then executes the exact pinned command below.
`bash -n` PASS. It has not been executed by the agent. This wrapper is an owner
handoff, not an automatic installer action.

Run in a normal Ubuntu terminal. This may ask for the Ubuntu sudo password and
**does not open CyrNava**. The output location is fresh and explicitly supported;
the confined failed attempt is preserved. If it fails, retain its result/private
log and stop rather than repeating or replacing an existing policy.

```bash
cd /home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
/usr/bin/python3.14 -B packaging/native/apparmor_support.py load --owner-host \
  --root "$PWD/ci-output/native-n2-client-4" \
  --manifest-sha256 c9744e49abd66698107408b4a502b3cce46816e116a036c2fe20fd51ca9496db \
  --policy-sha256 4ca488c1d40b5b82dbd18369e698c8a8ec69ad965e74fe27b974a1ee0de30d7b \
  --output "$PWD/ci-output/native-n2-policy-owner-load-1"
```

Expected: PASS / complete, host_policy LOADED, with the exact profile and policy
digest above. Root verifies the loaded name/mode. After that succeeds, the existing
non-GUI bootstrap check is `ci-output/native-n2-client-4/cyrnava-native --check`;
it verifies actual interpreter/profile inheritance but explicitly reports renderer
and normal-window checks NOT EXECUTED. Do not infer renderer success from loading
or this check.

The focused owner GNOME menu check remains pending using the new client/manifest,
the prepared synthetic profile and a fresh attempt; no GUI command is run or
reissued here. It must demonstrate actual namespace/seccomp/NoNewPrivs protection,
AppArmor inheritance, authentication, providers, persistence and cleanup. Reversal
uses the helper's `remove` operation with the same root/manifest/policy pins and
a fresh output; it refuses changed files or live profile processes and never
reloads unrelated policy. No N3 uninstaller is introduced.

Source snapshots and compact sanitized evidence are retained under
`ci/evidence/n2/apparmor-integration-2026-11-03/`. Earlier accepted/source/candidate
hashes and all previous PASS/FAIL/BLOCKED records are unchanged. No commit, push,
signing, publication or N3/N4 implementation occurred.

The pre-task installer bytes were independently recovered from signed-install
fixture 2, SHA-256 `718f7284bd140f9b88265c420344b1b08b4dc7515255872e9508f739a6781acf`.
Ten safety-sensitive functions, including signature verification/status, extraction,
host/loader guards, path/JSON checks, deployment selection and offline environment
setup, are AST-identical to that baseline. Candidate 3 intentionally contains an
older verifier engine; it was not mistaken for the pre-task corrected source.

---

# Historical review proposal — dedicated launcher and AppArmor namespace allowance

3 November 2026. **Planning authorized; proposal prepared for owner review only.**
N1 remains ACCEPTED / COMPLETE. **N2 remains CONDITIONAL** because the normal GNOME
menu launch failed renderer namespace isolation. Implementation, policy loading and
another native execution require separate authorization. N3/N4 remain unstarted.
This proposal changes no executable, candidate, policy, evidence or test command.
The checkpoints below retain their original results and execution scopes.

## Decision proposed

Use a small, application-specific native ELF launcher as the AppArmor attachment
point. Give its application process family an explicit user-namespace allowance
through one narrowly attached, root-owned profile. Keep the existing system
CPython, private dependency environment, Qt stack and application launcher. Keep
Ubuntu's global namespace restriction enabled. Do not attach a policy to generic
Python, rely on VS Code's inherited profile, copy a WebEngine helper, or disable
renderer sandboxing.

The evidence supports this integration as the next bounded experiment; it does
not establish that an unimplemented profile fixes the menu failure. Attempt 5's
exact renderer had seccomp and NoNewPrivs but lacked user/PID/network separation.
Its candidate PID was audited entering Ubuntu's restricted namespace context.
The following capability denial's precise child ancestry remains unproven. The
full evidence identities and limits are preserved in the retained checkpoint below.

## Launcher and attachment design

Proposed execution sequence:

1. GNOME launches the installed Desktop Entry through absolute `/usr/bin/env`,
   with `--` and the quoted absolute `cyrnava-native` executable as its argument.
2. The dedicated ELF enters its exact-path AppArmor profile and checks its actual
   policy label before starting Python. An absent, wrong or unreadable label must
   refuse launch, not fall back to generic unconfined execution. It locates the
   install root from `/proc/self/exe`, accepts only no arguments or the existing
   `--check` operation, and invokes absolute
   `/usr/bin/python3.14 -B -I <root>/launch.py`.
3. The existing Python bootstrap selects the installed version, verifies the
   receipt/payload/providers and reexecutes that version's private interpreter.
4. The existing Qt launcher starts the authenticated backend and matching
   application-owned QtWebEngine helper. All required descendants must retain the
   intended AppArmor context; the actual renderer must still satisfy every
   namespace/seccomp/NoNewPrivs predicate.

These are proposed steps, not observed execution. There is no shell evaluation,
PATH search, arbitrary command argument, setuid bit or privileged application
process. The launcher will not derive its root from the current directory or an
environment override. It must fail closed on invalid identity, arguments, root
layout or exec failure, with safe operation diagnostics.

The `/usr/bin/env --` adapter preserves an existing GIO constraint: GIO resolves
the first executable before expanding Desktop Entry percent escapes. A per-user
executable path containing `%` therefore cannot simply replace system Python as
that first executable. The absolute native path would instead be an argument to
the absolute system adapter. GIO parsing, spaces, percent signs, quotes, dollar
signs, process ownership and application grouping require focused validation;
this proposed adapter is not yet verified. Existing Desktop Entry escaping must
not be replaced with shell quoting.

The first candidate profile will attach to **one exact disposable install root's
ELF**, with no home-wide or version wildcard. Proposed policy filename:
`/etc/apparmor.d/cyrnava-native-u<UID>-<root-digest>`; placeholders are not loadable
policy. A UID in the filename/profile name is an identifier, not an access-control
check. The reviewed final profile must identify the exact absolute launcher path,
namespace permission and intended exec inheritance rules for the actual interpreter
and helper paths. Python script names and venv symlinks are not attachment points.

The installed AppArmor package is `5.0.2-0ubuntu1~26.04.1`. Its local
`apparmor.d(5)` manual describes `default_allow`, `userns create,` and `ix` execution
inheritance; it discourages regular deployment of legacy `unconfined` mode.
**Propose `default_allow` with the namespace allowance and explicit inherited exec
rules**, subject to exact parser/kernel ABI support and transition validation.
Do not copy Ubuntu 24.04's older ABI/mode example unexamined. No policy file is
created here, and no final syntax, successful attachment or inheritance is claimed.
Future parser validation must avoid policy loading and host cache writes.

## Security boundary and alternatives

This profile preserves ordinary-user application/filesystem/network access; it
does not add a Flatpak-like outer sandbox. That ordinary-user tradeoff is already
accepted. The **new** decision is permitting user-namespace operations from this
named application context. The allowance applies to the application process family,
including its interpreter/backend, rather than only the renderer. It does not
grant host root or host `CAP_SYS_ADMIN` and is not permission to change host-wide
namespace, AppArmor or seccomp settings.

A per-user writable executable, libraries and payload are replaceable by the same
user. An exact-path allowance is **not code-signature enforcement or a security
boundary against that user**. Root ownership of the profile does not change this.
Existing package/receipt/provider checks remain required but do not turn writable
installation files into a root-enforced trust boundary. Chromium's official
guidance explicitly discusses this limitation of writable executable attachments.

| Option | Assessment |
| --- | --- |
| Dedicated native launcher + exact application profile | Recommended bounded experiment; retains OS Python updates and adds one small compiled asset. Attachment and exec inheritance must be demonstrated. |
| Copy Python into each versioned environment | Python supports copies, but this adds OS executable/ABI/security-update synchronization duties. No demonstrated benefit justifies it over the launcher. |
| Grant generic system Python, reuse another app's profile, or disable the global restriction | Rejected: extends the scope beyond this application's intended integration. |
| Disable WebEngine sandboxing or introduce a setuid fallback | Rejected: violates existing renderer requirements. |

Sources: [Ubuntu namespace restriction behavior and selective application profiles](https://documentation.ubuntu.com/release-notes/24.04/),
[Chromium's AppArmor integration and writable-path warning](https://chromium.googlesource.com/chromium/src/+/main/docs/security/apparmor-userns-restrictions.md),
[Python 3.14 virtual-environment options](https://docs.python.org/3.14/library/venv.html).
AppArmor 5 mode/grammar statements above come from the installed primary manual,
`/usr/share/man/man5/apparmor.d.5.gz`, rather than treating the older Ubuntu example
as tested syntax on this host.

## Proposed implementation scope and resource bound

No files in this table are modified by this planning task.

| Proposed touch point | Narrow purpose |
| --- | --- |
| New `packaging/native/bootstrap.c` and its build step | Small ELF entrypoint; strict root/argument handling, absolute interpreter exec and safe failures. Filename is proposed. |
| `desktop/install_engine.py` | Install/verify the ELF and render the Desktop Entry; preserve offline locks, signature/provider validation, activation and data isolation. |
| `packaging/native/build_candidate.py` | Include executable/source/compiler provenance and hashes in a fresh candidate identity. No Qt/Python rebuild. |
| Candidate-only policy proposal under `packaging/native/` | Generate exact-path policy for review; never auto-install/load policy. Final filename to be reviewed with implementation. |
| Focused native packaging tests and N2 observation diagnostics | Exec/quoting/identity failures and policy-context evidence; accepted N1 predicates remain unchanged. |
| Existing N2/current-status documentation | Record actual results, owner decisions and rollback instructions. |

Aim to preserve `packaging/native/launch.py` and application behavior. Any necessary
deviation must be explained in the implementation review. Production Profile
storage, authentication, WebEngine permissions, accepted N1/P1–P5 evidence and all
failed attempts stay unchanged. No updater/uninstaller or release-CI work is added.

Estimated bootstrap allowance: one compiler job, at most 128 MiB scratch and five
minutes; expected executable below 1 MiB. Stop and reassess on exceeding those
bounds. Use an already available compiler; if missing, stop for a revised plan
rather than installing build dependencies. No Qt/Chromium build or dependency
download is proposed. Prior N2 archive
plus installed tree occupied about 1.27 GiB; reserve **at most 2 GiB additional**
for a fresh candidate/client and retain the existing **5 GiB free-space floor**
before future assembly. These are planning estimates using earlier observations,
not a new disk measurement. Measure the actual affected filesystems first; reuse
verified wheels, never remove accepted artifacts or retained attempts to fit.

## Review, verification and rollback checkpoints

**1. Separate implementation approval.** Build only the small launcher, assemble
one fresh candidate and run focused local fixtures/parser-only checks. Verify
argument rejection, absent/wrong/unreadable policy labels, root binding,
symlink/escape handling, immutable payload/provider checks and Desktop Entry/GIO
parsing. No installation/loading of host policy or
native application execution follows automatically from that approval.

**2. Review exact host change before authorizing it.** Present the final launcher,
candidate/manifest hashes, profile bytes/hash, attachment, ABI/mode, interpreter/helper
exec rules, changed-file diff and exact install/load/reversal commands. Check for an
existing file/profile-name collision; do not silently replace it. Verify namespace
allowance inheritance across interpreter reexecs and helper startup, including
NoNewPrivs transition constraints. Do not clear NoNewPrivs to make a transition work.
Root-owned installation/loading of this one profile requires explicit owner approval;
there is no global service reload, sysctl edit or generic-Python permission grant.

**3. Separately approved focused owner-host check.** Use the new candidate with
disposable data and a fresh attempt. Observe the actual GNOME menu launch, window
identity/icon/grouping, correct loaded Qt providers and exact helper/renderer role.
Record safe AppArmor labels at the GUI/interpreter/helper stages and require the
same renderer instance to pass stable identity, user/PID/network separation,
NoNewPrivs and seccomp. Require backend authentication, normal close, owned-process
cleanup and exact saved-data/origin persistence. Verify the global restriction
remains enabled. Confirm unrelated Python or a different executable path does not
automatically receive this profile, without claiming protection against deliberate
same-user replacement of the allowed launcher. A denied or incomplete observation
fails; no retry or relaxed predicate substitutes for evidence.

This is a focused changed-entrypoint check, not another historical A/B, R12 or full
editing/recovery rehearsal. Earlier tests remain evidence only for their recorded
bytes and contexts. The changed candidate needs its own identity and live results.

**4. Owner-approved reversal if unsuccessful.** Close only the candidate normally
and verify owned-process cleanup. Remove only the unchanged temporary menu entry
created for this check. Unload only the newly added, exactly identified profile and
remove only its unchanged policy file, using commands reviewed before loading;
refuse on hash/identity mismatch. Running processes may retain policy context, so
unloading must not be assumed to revoke a live process's allowance. Preserve the
candidate, synthetic data and all evidence. No global profile reload/disable,
unrelated policy change, broad cleanup or N3 uninstall implementation is involved.

## Current outcome and owner decision

**Proposal ready for review; implementation and host loading are not authorized.**
Open technical gates are AppArmor 5 ABI/mode support, actual exec/profile inheritance,
GIO adapter behavior and protected renderer operation from a normal menu launch.
The per-user writable-path/process-family permission tradeoff is explicit above.
No further unchanged native retry is justified. Owner review should decide whether
to authorize the bounded launcher/policy implementation for inspection first;
host loading and native validation remain later, explicit checkpoints.

This turn performed document/source/manual reads and bounded primary-source
research only. No tests, builds, probes, dependency resolution, policy commands or
application execution were performed. Historical failures remain failures.

---

# Retained checkpoint — menu attempt 5 fails renderer namespace isolation

3 November 2026. **N2 CONDITIONAL — normal-menu renderer security remains blocked.**
The new record identifies the failed predicate; another unchanged menu retry is
not justified. No native application/probe was launched by the agent.

## Actual attempt 5 evidence

`ci-output/native-n2-owner-5/result.json`: FAIL / complete, SHA-256
`fbe46c10616d87477d04c137b880bb4219a34426636bd37b3096382bacc0a8aa`.
`observation.json` SHA-256:
`d562a691156526eb8a7beb1e2beff4d078ca8edb3cfd96c2c1785cd3fd5c590f`.
The executed driver matches its recorded hash. Discovery and temporary menu-entry
cleanup PASS. Five processes/three expected helpers were seen; one helper had the
exact renderer role and stable identity. Backend and private Qt providers PASS.
Renderer NoNewPrivs and seccomp PASS, but **user, PID and network namespace
separation all fail**, with no proc-read errors. The unchanged security predicate
correctly refuses PASS. Authentication was NOT TESTED, because the combined live
gate never completed. This is neither an import failure nor a SIGINT interruption.
The 30-second observation bound operated as intended.

Read-only post-close validation at `ci-output/native-n2-owner-4003` verifies the
exact prelaunch folder, rich note, image, schema/database content and origin remain
unchanged. The candidate/manifest/installed provider identities are preserved.
This data result does not substitute for failed renderer isolation.

## Supported diagnosis: AppArmor launch-context difference

Existing native logs were inspected privately; no new GUI execution was needed.
The accepted N1 probe's `parent_confinement` records **snap.code.code**. GNOME's
candidate journal identifies its Python GUI process; the kernel logs audit that
same PID creating a user namespace from generic `unconfined` and transitioning to
`unprivileged_userns`. A `sys_admin` capability denial in that restricted profile
follows 2.299 ms later, 0.122 seconds before the first candidate journal message.
The second event is a different PID: its exact parent/child relationship is not
recoverable from these saved messages and is not asserted as proven.

Host reads show `unprivileged_userns_clone=1` and
`apparmor_restrict_unprivileged_userns=1`. Ubuntu documents that the default policy
can permit namespace creation while denying capabilities within it; an application
profile is its selective integration mechanism. See
[Ubuntu AppArmor documentation](https://documentation.ubuntu.com/security/security-features/privilege-restriction/apparmor/)
and [Ubuntu release notes](https://documentation.ubuntu.com/release-notes/24.04/).
[Qt 6.11.3 platform notes](https://doc.qt.io/qt-6.11/qtwebengine-platform-notes.html)
require Linux namespace/seccomp support and do not support a setuid-sandbox fallback.

These independent records strongly support AppArmor context as the cause of the
normal-menu difference. They do not prove every syscall/zygote transition after
the processes exited. The proc comparison has no demonstrated defect: fixtures
verify the exact all-false namespace case fails. The earlier positive probe used
a different inherited policy context; it does not certify this menu launch. N1's
original acceptance/evidence and previous N2 GUI/signature records remain intact.

## Narrow correction made locally

Only the N2 diagnostic code changes: a renderer that is present but fails namespace
checks is now reported as `renderer_namespace_separation_failed`, with final
renderer status FAIL and a safe result category, rather than an unexplained
NOT OBSERVED. Missing processes/denied reads remain separate incomplete categories;
no host-policy cause is guessed in code and no security assertion is relaxed.
**20 focused tests PASS** (11 menu fixtures + 9 observation regressions), including
the exact attempt-5 shape. Scoped Ruff/format PASS. No signature test/key generation,
package rebuild, normal installation change or GUI retry was performed.
Original executed source and sanitized review are preserved in
`ci/evidence/n2/owner-5-menu-security/`; raw candidate/kernel logs stay private under
`ci-output/native-n2-review-1/`. All historical failed attempts are unchanged.

## Proposed bounded N2 remediation — owner decision required

Prepare a **CyrNava-specific AppArmor integration** that grants user-namespace use
only through a dedicated native application entrypoint. Preserve Ubuntu's global
restriction, renderer namespaces/seccomp, authentication and storage policies.
Do not grant the permission to generic system Python, reuse VS Code's profile,
disable AppArmor or introduce a setuid/sandbox-disable workaround.

The existing private interpreter is a symlink. The implementation must first
establish a dedicated executable/verified attachment path, rather than accidentally
targeting system Python or assuming a script filename controls AppArmor attachment.
Then prepare exact launcher/profile bytes, parser validation, attachment tests and
an owner-reviewed load/reversal procedure. No profile has been created or loaded;
no host-policy command is approved by this report. This is a scoped integration
proposal, not a claim that the fix has already been demonstrated.

The owner's standing instruction reserves host-security changes and AppArmor
integration for a separate explicit decision. Stop here for that decision. After
an approved implementation/policy, one focused native menu/security check is needed;
the editing/install/recovery rehearsals need not be repeated without changed inputs.
Do **not** rerun attempt 5 or issue an unchanged fresh attempt as a substitute.
N3/N4 remain unstarted; no commits, pushes, production keys or publication occurred.

---

# Historical checkpoint — menu attempt 4 preserved; observation correction verified locally

3 November 2026. **N2 remains CONDITIONAL.** Owner menu attempt
`ci-output/native-n2-owner-4/result.json` is FAIL / complete, SHA-256
`8cde89422e14ccf60060ff2153b75d5f97985aa94e5a9a540467a9a6afc0b3a5`.
Actual GIO menu discovery/identity and removal of the temporary entry PASS. The
driver detected a menu-launched process; the owner showed the expected candidate
window and saved synthetic content. After normal close, its live-evidence
completeness assertion failed. The private traceback confirms RuntimeError, not
SIGINT/KeyboardInterrupt. Closing normally did not itself fail an assertion.

The executed driver did not save its individual backend/renderer/provider
observations; therefore the exact missing live check is **unknown**, and this
result cannot prove a renderer, application or authentication defect. It also
cannot be promoted to PASS. The earlier exact candidate GUI/edit/restart PASS and
signed-install mechanism PASS remain unchanged in their scopes.

Local investigation reproduced a process-observation defect: Linux children lists
are per-thread, while the reused traversal inspected only each process's main
thread. A real synthetic non-GUI child launched by another thread is missed by
the old sampler and found by the corrected N2 sampler. This is a confirmed
limitation, **not proof that it caused attempt 4**, whose live metrics were lost.
The accepted N1 sampler/source is unchanged. N2 now follows children of all threads
with bounded traversal, records safe operation/errno diagnostics, and requires the
same exact helper/renderer role, NoNewPrivs, seccomp, separate user/PID/network
namespaces, stable PID birth, private Qt providers and backend authentication.
Denied reads, missing evidence and traversal limits never become PASS.

The menu driver saves `observation.json`, prints observation/missing-check progress
every five seconds and stops after 30 seconds if required live evidence remains
incomplete. It does not kill an externally launched application; if incomplete,
the owner should close the candidate normally. It accepts an explicit fresh
`--output`, preserving failed attempt 4. No automatic retry or GUI execution was
performed by the agent.

**18 focused regressions PASS** (11 menu/monitor fixtures + 7 observation tests),
including a real non-main-thread child, denied-read diagnostics, bounded failure,
and refusal of wrong helper/role, missing namespace separation, NoNewPrivs or
seccomp. Scoped Ruff/format checks PASS. No signing fixture was repeated.
The actual installed-Python post-close read-only state check at
`ci-output/native-n2-owner-4002` also PASSes: note/folder/rich content/image/database
and origin state are identical to attempt 4's prelaunch snapshot. No profile was
modified by this inspection. This is not a new GUI result.

Original executed source and failure review are retained under
`ci/evidence/n2/owner-4-menu-observation/`. Follow only the fresh owner-5 menu command
in [N2_OWNER_CHECKS.md](N2_OWNER_CHECKS.md) if continuing. No preparation, install,
editing round or full N1 rehearsal is needed. N3/N4 remain unstarted; no package,
application, signature/security policy, normal installation or Git writes changed.

---

# Historical checkpoint — installed GUI and signed-install verification PASS

3 November 2026. **N2 remains CONDITIONAL pending the actual GNOME menu check
and formal owner acceptance.** N1 is accepted; N3/N4 remain unauthorized. The owner
authorized completion of remaining N2 verification. No completed phase was reopened.

## Actual installed application — verified

`ci-output/native-n2-owner-3/result.json` is PASS / complete, SHA-256
`cfb76d3616e0c98e307653397d45bee96b8b1f8165e4de5124d828c8ce3ecdde`.
Edit checks are explicitly inherited from reviewed attempt 2; attempt 3 actually
performed restart. Both phases passed backend, renderer, private Qt providers,
authentication rejection, normal exit and process cleanup. Owner visual confirmation
passed. Exact edit/restart state files match, SHA-256
`0feb528634201a68d00568fdfea73f34b279fae9cc5fe69bc1e474c34869a710`:
schema 5, one folder, rich note and attached image; exact content/assets and origin
preserved. Dark appearance, icon and grouping are owner-confirmed. The verified
package, manifest and installed files remain unchanged. Attempts 1/2 remain FAIL.
Do not repeat the completed editing/restart exercise.

## Actual cryptographic install — verified in its test scope

Fresh `ci-output/native-n2-signed-install-2/result.json`: PASS / complete,
25.710 seconds, SHA-256
`628a3ee9b18aebfd99320196abcb7f86b0ee00e23fcef68aab12e0675a23a31c`.
The real standalone shell/installer CLI ran normal signed-install mode without
mocking GPG, host checks, pip, provider checks, backend startup or activation.
HOME/XDG were isolated inside that output; no regular installation/menu changed.
All locked wheels/application bytes are reused except the explicit test application
identity and corrected public-verifier engine. This fixture does not replace the
GUI-verified development candidate; no GUI result is inferred for its different bytes.

| Signed-install fixture identity | Value |
| --- | --- |
| Archive SHA-256 | `bf7192a570dc42c4c6a9d512bcdb101e096886ecdc58d98e20006508fc5d8492` |
| Manifest SHA-256 | `302ca13fa17425df9d201269a3cb7b81906ae32c37131bc57d445289c88d2799` |
| Detached signature SHA-256 | `64ab655d01d2dd299b537e632e1be2a1f7a890563bc7b27d8aab1c6fc49dac3c` |
| Disposable test fingerprint | `9C993E8F4CB3988F52EC091FF7E6EE30D61AE1D2` |
| Installed receipt SHA-256 | `be63e8a10830e8e5a3e888be3511ab908e640ebc5c5ab278ff98438506bd9191` |

A one-day test key produced a real detached signature, verified against its explicit
fingerprint. Wrong-fingerprint and tampered-manifest rejection passed. Actual offline
hash-locked installation, 4,414 provider files/ELF checks, backend authentication,
origin, note/image persistence, restart/cleanup and stable bootstrap passed. The
disposable private key home was removed; public materials/private logs remain.
**This proves the signed-install mechanism, not production identity, public trust or
a production release signature.** Those remain later owner-controlled release work.

First fixture `native-n2-signed-install-1` remains FAIL. Public-key import succeeded,
then unnecessary gpg-agent startup failed (exit 2), before dependency installation.
Private diagnostic review and bounded public-keyring comparison establish this
operation. `desktop/install_engine.py` now dearmors the supplied public key into its
private temporary keyring, disables default keyrings and agent autostart, and keeps
no-auto-key-retrieve. Full trusted fingerprint, digest, expiry/revocation and every
archive/installation check remain enforced. The old GUI candidate stays byte-identical
and does not use this signature branch in its isolated checksum-only mode.

**77 N2 tests PASS**, including six real GPG regressions for armored/binary keys,
long paths, no import/agent, wrong identity, tampering and expiry; 11 additional
menu/monitor fixtures cover real isolated GIO discovery by ID, collision/changed-file/
symlink/permission protections, bounded startup and renderer/provider/auth failures.
Scoped N2 Ruff and format checks PASS. A broader read-only scan also reported 26
pre-existing lint findings in unchanged N1 feasibility files (BLE001, RUF059,
RUF100, SIM117); these accepted hash-pinned sources were preserved, not rewritten.
That broader scan is not claimed PASS. Earlier N1/backend results retain their scope.
Filesystem free space was 17,725,026,304 bytes before fixture 1 and 16,177,184,768
after retained fixtures/checks. This is measured free space, not guaranteed reclaim.
No download, Qt rebuild, accepted-artifact replacement or cleanup occurred.

## Only remaining native observation

`packaging/native/verify_menu.py --owner-host` is implemented and fixture-tested,
not executed against GNOME. It temporarily registers the byte-identical development
Desktop Entry, refuses collisions, verifies real GIO discovery by ID, and waits for
the owner to select it in GNOME Applications. It monitors that actual window's
renderer/providers/authentication and cleanup, checks exact saved state/origin and
records visual menu/icon/grouping confirmation. An external GNOME child has no
waitable exit code for this driver; it explicitly reports that limitation, retaining
the separate earlier normal-exit evidence. No exit status is fabricated.

The entry is removed only if unchanged and owned; changed entries are preserved.
The package/profile remain client 3's existing disposable data. No new editing or
installation is needed. The owner must make the menu selection in the normal
Wayland session; the agent has no native desktop control. Exact command:
[N2_OWNER_CHECKS.md](N2_OWNER_CHECKS.md), fresh `ci-output/native-n2-owner-4`.
The actual installed-Python saved-state subprocess used by this handoff was also
checked read-only at `ci-output/native-n2-owner-4001`: PASS, matching owner 3's exact
state. That record is explicitly not a GUI/menu attempt and leaves owner 4 unused.
No production key, normal installation, host-security change, commit, push,
publication or N3/N4 implementation occurred. Formal N2 acceptance is not claimed.

---

# Historical checkpoint — editing passed; capitalization rule corrected

3 November 2026. **N2 remains CONDITIONAL pending restart/menu and signed-install
evidence.** Owner attempt `ci-output/native-n2-owner-2/result.json` remains
FAIL/complete, SHA-256
`7a85ddb0ae9ead9a096bb66a197396bcc49474fc33bde9479fae3d4be10a62b2`.
Its actual `edit` phase passed backend, renderer, Qt providers, normal exit,
owned-process cleanup and unauthenticated-backend rejection. The application
closed normally. The subsequent saved-state child failed; restart was not reached.

The retained private child traceback identifies the exact assertion: required
bold text. Read-only SQLite inspection found the correct folder/note, the stored
bold span **N2 Desktop Verified**, and its attached image. SQLite integrity is
`ok`. The checker expected case-sensitive **N2 desktop verified**. This is a
human-marker validation mismatch, not evidence of lost formatting, lost data or an
application close failure. The original first-round FAIL is not rewritten.

Only the N2 verifier now treats marker capitalization as presentation-neutral.
Bold remains mandatory, incorrect text and missing images still fail, and the
actual stored span plus complete canonical database/asset fingerprint remain
case-sensitive for restart comparison. The unchanged N1 checker is reused with
the actual matching N2 span bound only in its verifier-local state; its accepted
source and semantics remain unchanged. Specific failed-check categories now pass
from the snapshot child into the safe result instead of only CalledProcessError.

**60 N2 tests PASS**, including capitalization variants, rejection of absent bold,
wrong text/missing image, detection of actual capitalization/content changes during
restart, read-only behavior, safe diagnostics and continuation identity/data guards.
Ruff/formatting PASS. A separate actual installed-CPython-3.14 **read-only** review
also passed production schema/assets validation and the corrected saved-state
check: schema 5, one folder, one rich note, one image. Canonical fingerprint:
`8fc8a3883f5403526fe9300c7ea8569cce0392f07b802da273a209991b9342b3`.
Every existing profile file had the same bytes before/after this review.

The explicit `--resume-after-edit` mode accepts only reviewed attempt 2: pinned
result/log/driver identities, all six original edit checks PASS, the same package,
desktop entry and GIO adapter, and the exact reviewed workspace file hashes.
An installation lock rejects concurrent application use during this preflight.
The continuation validates saved state before opening a window and performs only
the remaining restart phase. Its result labels the first phase **INHERITED** with
the original result hash; it does not claim to rerun it. Any changed workspace,
artifact or first-phase evidence stops the continuation. A fresh output is required.

No GUI was run by the agent, and no package rebuild, reinstall, database/profile
edit, signing, host-security change or N3/N4 work occurred. The executed old driver
and safe read-only review are retained at `ci/evidence/n2/owner-2-state-validation/`;
the actual target-Python state review is at
`ci-output/native-n2-review-1/owner-2-postclose-state.json`. Both owner attempts and
all original private logs remain intact. Earlier N1/backend passes retain their
original scope and were not repeated for this verifier-only correction.

Use the restart-only command in [N2_OWNER_CHECKS.md](N2_OWNER_CHECKS.md). Do not
recreate/edit the note or repeat the original editing round.

---

# Historical owner attempt 1 correction — retained

# N2 current checkpoint — owner attempt 1 driver failure corrected

3 November 2026. **N2 remains CONDITIONAL.** Owner attempt
`ci-output/native-n2-owner-1/result.json` is FAIL/complete, stage
`edit-desktop-launch`, AttributeError, no completed phases. Its SHA-256 is
`40637aa138d1a07d85c35fda0281545562702e84167398069a5d08fa44e0d58a`.
The private child log is empty and the GUI profile does not exist.

**Confirmed verification-driver defect:** the executed driver (SHA-256
`f6215c8444863d48fcd4d7185ceb92bebe9db02fff8b9d1b1da166b2028351a2`)
substituted a subprocess adapter without the `STDOUT` constant. The unchanged N1
monitor evaluates `stderr=subprocess.STDOUT` before calling the process constructor.
A local reproduction produced the same missing-STDOUT AttributeError with the
constructor never called and an empty child log. Thus this failure happened before
GIO or CyrNava startup; it is not evidence of an application, Qt or renderer failure.
The previous tests covered GIO and the installer but missed this adapter integration.

Correction is limited to `packaging/native/verify_desktop.py` and its new regression
tests: complete the subprocess adapter interface; preserve the unchanged monitor's
provider/auth/exit/cleanup checks; add explicit `--output` for a fresh numbered
repository-local attempt and propagate it to saved-state subprocesses. The original
default output remains unchanged and existing attempts still refuse reuse.
Future exceptions retain a private traceback and expose only allowlisted attribute
and source-line diagnostics in the safe result.

**48 N2 tests PASS**, including eight new monitor/adapter regressions. Ruff and
formatting PASS. Tests use synthetic processes; no Qt GUI or native application
was launched. Earlier 54 N1 and 128 backend passes retain their original scope and
were not rerun for this driver-only correction. The original driver source is
preserved at `ci/evidence/n2/owner-1-driver-failure/verify_desktop.py.txt`;
safe reproduction/correction records are beside it. The original attempt is intact.

The package, manifest, receipt, desktop entry and installed engine remain unchanged.
No rebuild, reinstall, signature, GUI retry, host change or N3/N4 work occurred.
Use the reviewed fresh-output command in [N2_OWNER_CHECKS.md](N2_OWNER_CHECKS.md).
Native GUI/menu and authentic signed-install acceptance evidence remain pending.

---

# Initial local implementation verification — retained

# N2 — LOCAL IMPLEMENTATION VERIFIED / OWNER REVIEW PENDING

3 November 2026, Korea time. N1 is **ACCEPTED / COMPLETE** by the owner's explicit
decision. N2 only is authorized: versioned per-user native installation and desktop
integration. **N2 is CONDITIONAL, not accepted.** N3 updater/uninstaller and N4
CI/public-release preparation remain planned and unauthorized. Flatpak is paused
historical/fallback; it is not an additional release gate.

Active target: native Ubuntu 26.04 x86_64 / GNOME Wayland installation via versioned
GitHub Releases archives, existing PySide6/Qt application, ordinary CPython 3.14.
The ordinary-user filesystem/network tradeoff is already accepted. Renderer
sandboxing, authenticated backend and data isolation remain required. MIT is
selected for original code; attribution, branding rights and third-party release
obligations remain separate decisions. No signing or publication was performed.

## What was implemented

- `desktop/install_engine.py`: one stdlib engine for installation, first-install
  transaction recovery, installed-receipt verification and launching. It does not
  implement updates/uninstallation. Normal deployment requires a release manifest,
  detached GPG signature, independently trusted public key and full primary
  fingerprint. Wrong/expired/revoked identity and invalid signature status are
  rejected. No keys are generated, retrieved from servers or provisioned.
- `install_cyrnava.sh` and `packaging/native/install.sh`: thin shell delegates.
  A standalone engine/shell export is also available alongside the candidate;
  installation needs no source checkout, Node, Git, compiler or Firefox. These
  exported bootstrap bytes are currently unsigned and must not be publicly trusted
  from their accompanying checksums alone.
- `packaging/native/build_candidate.py`: offline assembly from the accepted N1
  wheelhouse and built frontend. Exact N1 payload/wheel hashes are checked first.
  Only the native configuration dispatch, installed configuration and explicit N2
  development identity change application packaging; frontend/backend behavior,
  schema, navigation/security policies and the accepted N1 candidate are preserved.
- `desktop/native/installed_configuration.py`, the five-line installed-deployment
  dispatch in `desktop/native/application.py`, and `packaging/native/launch.py`:
  explicit installed layout, stable bootstrap, private interpreter and profile.
  No environment variable can opt the default Flatpak entry into native mode.
  The bootstrap validates active receipt/payload/providers before re-executing the
  selected private Python. The existing Qt application still creates the window.
- `packaging/native/provider_check.py`: complete locked installed-file hashes,
  actual binding/Qt/plugin providers, helper/resources/locales, runtime versions
  and selected ELF dependency closure checked before activation. No QApplication
  or renderer is created by this check.
- `packaging/native/desktop_process.py` and `verify_desktop.py`: focused owner
  handoff through GIO's actual Desktop Entry parser/launcher, with an owned waitable
  process group. Reuses the unchanged N1 process/provider/renderer/auth/cleanup
  monitor and production saved-state validator. Only verifier target constants are
  adapted; application classes and JavaScript are not patched. Two actual launches,
  synthetic saved-state/origin comparison and owner visual confirmation are needed
  for the future N2 GUI result to PASS. It has **not run against the GUI** yet.

The [GIO API](https://docs.gtk.org/gio-unix/method.DesktopAppInfo.launch_uris_as_manager_with_fds.html)
provides child-PID callbacks and redirected descriptors. The handoff requires one
spawned child, verifies its process group and retains its real exit status; a
successful desktop-launch request alone is not treated as application success.

## Installation boundaries and recovery

Default program root: `$XDG_DATA_HOME/cyrnava-application`; stable data root:
`$XDG_DATA_HOME/cyrnava/native`. Neither legacy source nor Flatpak data is adopted.
Releases live at `releases/<version>-<artifact-hash>/`, with a venv created at its
final absolute path. `current.json` pins the installed receipt; the stable
program-root `launch.py` selects and validates the release. A native Desktop Entry
uses an absolute system-Python/bootstrap command and the existing artwork.

The proposed separate `~/.local/bin/cyrnava` alias is not installed in this N2
implementation: the desktop entry directly invokes the stable program-root
bootstrap. The transaction journal/lock is beside `current.json`, rather than in
another XDG state tree, keeping activation coordination within one owned root.
These choices do not change application data or introduce a release service.

Archive paths, exact member inventory, duplicates, links/special files, declared
sizes and content hashes are checked. Installer state must be private and owned;
existing permissions are not silently changed. Parent traversal and symlink
ancestors are refused. Pip uses `--isolated --no-index --no-cache-dir --no-compile
--require-hashes --only-binary=:all:` with only the packaged wheelhouse. Prerequisite,
provider and real synthetic backend checks precede activation.

One exclusive lock coordinates installation/recovery and application lifetime.
Durable journal stages cover staging, verified payload, activation and menu
registration. Interrupted transactions block launch. Explicit `recover` rolls back
only hash-matching transaction-owned pointer/bootstrap/menu files and retains the
release, logs and journal history. Changed targets are preserved and recovery
refuses. This is first-install recovery, not N3 update rollback.

Existing desktop registrations and alternate providers of the production desktop
ID are refused pending an explicit coexistence decision. Existing data/profile
or active installation is preserved; N2 does not silently reinstall or upgrade it.
Candidate checksum mode is restricted to the repository engine and a disposable
root inside this checkout's `ci-output`. It requires a development identity and
separate profile/menu/XDG paths; it cannot authorize normal installation.

## Final candidate and actual installation

Candidate: `ci-output/native-n2-candidate-3/CyrNava-0.1.0-n2.1-ubuntu-x86_64.zip`.
**Unsigned experimental candidate, not a public release.**

| Identity | Actual value |
| --- | --- |
| Archive SHA-256 | `9d92a4f5d925e42f1cb8c9abdc84d913a3c111a5a52f4ed88b2d30840d36c0be` |
| Manifest SHA-256 | `a1e066a3d769319a761b8643469f055201ef04b2b80ff92c0ac9604e1a4f8d82` |
| Archive bytes | 271,531,611 |
| Declared expanded bytes | 271,516,147 |
| N1 source baseline | `bfa0b8005a3ddc519354fd7907e9b972fde8126b` plus recorded N1 patch and exact N2 file hashes in manifest/evidence |
| Accepted N1 receipt SHA-256 | `7f713ed31e2ce7d63a1a67e806d671b38ff2f7bafd2d66592f68ff70d575c41e` |
| Runtime | CPython 3.14; PySide6/Shiboken6/Qt/WebEngine 6.11.3; unchanged N1 wheel pins |
| Disposable installation | `ci-output/native-n2-client-3/` |
| Installed release | `releases/0.1.0-n2.1-9d92a4f5d925e42f/` |
| Installed receipt SHA-256 | `454fd5fcccae82c017f093d0c09f1be86fb3dcc8dc5413b57905b8111ea24286` |
| Installer engine SHA-256 | `6ab9667c0af9bf5babe377b200d5283a00464720f55a040ea5c7e1444710d824` |

Fresh installation **PASS**, exit 0 in **12.389 seconds**. Actual steps: fresh venv,
offline hash-locked pip installation, pip check, 4,414 installed dependency-file
hashes/provider/ELF checks, actual target-Python backend startup, unauthenticated and
wrong-origin rejection, folder/rich note/image persistence, backend cleanup,
restart/data integrity and stable-origin/token-revocation checks. Those backend
checks use a separate synthetic backend profile, not the GUI profile.

The actual system-Python stable bootstrap -> verified private interpreter `--check`
**PASS**, exit 0 in approximately 3.05 seconds; Ubuntu system-schema selection also
passed. It explicitly records normal window and renderer **NOT EXECUTED**. Actual
Desktop Entry passes `desktop-file-validate`. Main candidate GUI profile remains
unused. The owner handoff will exercise it for the first time.

## Tests executed and preserved failures

- **40 N2 tests PASS:** archive/path/hash/trust rejection, offline pip contract,
  shared lock, existing registration/profile protection, low disk, changed-target
  refusal, interruptions at all four journal phases and recovery, stable bootstrap
  re-exec, standalone export, real GIO quoting/Exec expansion and child exit/session
  ownership using a synthetic non-GUI executable.
- **54 existing N1 tests PASS**; accepted N1 result/receipt evidence remains unchanged.
- **128 backend/desktop/security/backup/migration tests PASS**, Python 3.12, 19.14 s.
  Existing warning output is retained. This supplements the fresh installed target-
  Python 3.14 backend check; it is not misrepresented as an N2 GUI run.
- Ruff, formatting and shell syntax checks PASS for the new implementation.

First real installation reached verified providers/backend and activation but
failed menu registration: quoting incorrectly applied storage symlink rejection
to Python's normal venv link. The interrupted journal prevents launch; this failed
client remains intact. Correction separates quoting from filesystem validation.
A real GIO fixture then showed percent-containing executable paths fail GIO's
initial executable lookup even when syntax validation passes. Final menu command
uses the stable system-Python bootstrap; private re-exec follows receipt verification.
The percent/space/dollar/quote argument fixture now passes GIO's actual expansion.
Candidate/client 2, which predated that final bootstrap correction, is retained as
an intermediate PASS limited to its exact input. Candidate/client 3 is current.

The initial broad regression run used an in-repository basetemp and was correctly
rejected by the production asset-store path guard. The second run lacked the
external basetemp parent. Both harness-failure logs remain. After creating the
dedicated authorized `/tmp/cyrnava-n2-regressions-20261103` parent, the third run
passed all 128 tests. No asset guard or failing assertion was weakened.

Private build/install/test logs and original outputs remain at
`ci-output/native-n2-review-1/` and the corresponding candidate/client directories.
Safe hashes/results are summarized in `ci/evidence/n2/local-verification.json`.
No original N1 GUI or renderer attempt was rerun; no earlier failure was relabeled.

## Resources and remaining N2 gates

No dependencies downloaded, frontend rebuilt or Qt/Chromium compiled. One final
archive plus installed client allocates approximately **1.274 GB**. All three
archives/clients and review outputs retained for diagnostic history allocate
**3,831,324,672 bytes (~3.57 GiB)** at measurement. Filesystem free space changed
from **21,601,550,336** to **17,750,233,088 bytes**; other host activity can affect
that delta. Initial available memory was ~3.6 GiB and swap was full; operations
were sequential and bounded (180 s pip, 120 s providers, 90 s backend, 600 s owner
interaction per launch). Aggregate peak RAM was not measured. No hardware, swap,
host-security or normal installation change was made. No outputs were deleted.

Remaining evidence, without additional implementation scope:

1. Owner native GIO Desktop Entry launch/restart, correct icon/window grouping,
   real editor/image persistence, runtime renderer security and cleanup for this
   exact installation. The isolated Desktop Entry is not added to the owner's
   normal GNOME menu; global Applications-menu listing remains unverified. The
   remaining menu check needs an isolated session or a controlled development
   entry, preserving existing registrations and resolving any identity collision.
2. Authentic signed-package installation with a trusted identity. Signature
   parsing/negative rejection is tested; a valid cryptographic signed-install
   end-to-end result is **NOT EXECUTED**, because this authorization forbids signing.
   A separately authorized disposable signing fixture could verify this without
   creating production keys or publishing anything. Owner bootstrap trust remains
   explicit, not inferred from the unsigned checksum files.

See [N2_OWNER_CHECKS.md](N2_OWNER_CHECKS.md) for the single focused native handoff.
N2 stays CONDITIONAL until the remaining evidence is reviewed. No N3/N4 work,
commit, push, GitHub execution, production key, signing or publication occurred.
