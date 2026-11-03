# N4 — Native CI and public-release preparation

## Minimal CI correction — locally verified / owner checkpoint

N1–N3 remain **ACCEPTED**; N4 remains **CONDITIONAL**. HEAD remains
`9218f7a22e5ebec7ab7482f8611e7aaa3212ddae`. This authorized local correction
changes only `ci/native_source.py`, its existing focused fixture file
`packaging/native/test_source_snapshot.py`, and this report.

**Setup correction: PASS in focused fixtures.** After validating the clean source
snapshot, the driver creates only its missing `ci-output` parent with mode
`0700`, without `exist_ok`. The installer still receives an absent `install-work`
path. Production installer code and its fresh-directory, path and security
checks are unchanged.

**Sanitized diagnostic regression: PASS.** On installation/update child failure,
the existing public `result.json` retains the stage and outer child exit status,
and adds a fixed failure category/reason and an allowlisted child exception type
when available. A bounded 64 KiB tail of the existing private log supplies only
the terminal installer failure JSON. Recognized prerequisite/work-path/frontend
operation messages map to fixed public text; absent, malformed or unrecognized
content produces a generic reason. Raw child output, arbitrary exception text,
commands, environment and private paths are not copied into the diagnostic.
Inner operation exit statuses are not inferred.

Directly relevant verification only:

- `test_source_snapshot.py`: **12 tests PASS**, including the clean snapshot
  initially lacking `ci-output`, parent mode `0700`, absent work/target at the
  simulated child call, sanitized stage/exit/type/reason, unknown/private content
  exclusion, existing path/snapshot refusals and single-attempt interruption
  handling. The child is mocked; this does not establish online installation PASS.
- Existing `test_existing_attempt_is_never_overwritten`: **1 test PASS**.
- Ruff lint/format checks for the two Python files and `git diff --check`: **PASS**.

No new files, installation, dependency acquisition, frontend build, GUI test,
host-policy change, commit, push or workflow retry occurred. Accepted artifacts
and the source-first owner desktop evidence remain unchanged. Hosted run
**41640878968 remains FAIL**; its original artifact is preserved. The first
actual child rejection in that run remains unknown. Hosted installation,
distinct-version update and update data preservation still require a separately
authorized commit/push and CI execution. Stop here for owner review.

The sections below retain their original historical checkpoint scopes; proposed
corrections marked not applied describe the earlier failed-run review.

## Hosted source-first CI 41640878968 — FAIL / owner checkpoint

The approved proposal SHA-256
`7376b7db5e97af4e789113e031a3cdb5ab7fd0eb5373d0e89a4d0bb83f54475f`
matched exactly. All 47 paths and staged/committed bytes were verified; 47
protected N1–N3 artifact/control hashes remained unchanged. One commit,
**`9218f7a22e5ebec7ab7482f8611e7aaa3212ddae`**, parent
`b7ab94265270866911311b4ca818071868f58361`, tree
`9a7211bc747393c5600749fd7a93f60e72e7267c`, contains exactly that set.
One normal fast-forward push to `origin/desktop/p2-production-integration`
succeeded. Independent GitHub commit/ref readback matched the parent, tree,
47 paths and every blob. Default `main` remains unchanged at
`4021bc292267c19b7ebebf219b4f682f8f99bf4c`.

[CyrNava CI 41640878968](https://github.com/74Cerillion/CyrNava/actions/runs/41640878968),
attempt 1, event push, exact new commit: **completed FAILURE**.

| Actual hosted requirement | Result |
| --- | --- |
| Workflow validation | PASS |
| Backend/security | PASS: 575 current + 41 subtests; 351 historical + 198 subtests |
| Frontend/browser | PASS: lint, units, TypeScript/production build and all 21 browser tests |
| Native installer/security/transactions and feasibility regressions | PASS: 238 + 63 tests |
| Clean source snapshot | PASS: 167 files / 3,543,993 bytes, no Git/wheelhouse/built frontend; all uploaded source hashes independently match the committed inputs |
| Actual online source installation | FAIL: child exit 1 / CalledProcessError; failed operation `online-source-install`; driver elapsed 0.275 seconds |
| Distinct-version source-online update | NOT REACHED |
| Profile/data preservation through that update | NOT EXECUTED; no inherited reinstall result substituted |
| Required CI completion gate | FAIL, correctly reflecting the native installation failure |

Original diagnostic artifact **13232443088**, 9,392 bytes, SHA-256
`5aa2f0293805143fb97ebb81aa2423b5ae7208fce44e0da36b542215bba1e977`,
was independently downloaded/verified and retained unchanged at
`ci-output/native-n4-hosted-41640878968/source-install-diagnostics.zip`.
It contains only the original `result.json` and `source-snapshot.json`.
The child output is redirected to runner-local `install.private.log` and was
not uploaded. Consequently the first actual child rejection/message cannot be
independently established from the retained artifact or job log. It is not
inferred merely from CalledProcessError.

Read-only control-flow review did confirm a deterministic **CI setup defect**:
`ci/native_source.py` copies a source-only snapshot without `ci-output`, then
passes `source/ci-output/install-work` to the installer without creating its
parent. `source_install.py:557–558` deliberately requires that parent to exist
before creating the fresh work directory. That invocation must reject at that
guard if its earlier source/npm/prerequisite checks succeed. The available
evidence does not prove which of those checks was the first actual rejection.

Smallest proposed correction, **not applied**: create only the fresh snapshot's
`ci-output` parent with mode `0700` before the first installer call, leaving
installation/work directories fresh and all refusal/security checks unchanged.
Retain an allowlisted sanitized child-failure detail in the existing diagnostic
result on a subsequent authorized execution so earlier prerequisite rejection
can be distinguished from this proven missing-parent defect. No raw environment
or private child-output publication is proposed.

N4 remains **CONDITIONAL**. The one commit/push authorization is consumed.
No retry, second commit/push, correction, additional test, GUI rehearsal or
publication occurred. This report update remains local/uncommitted. Next owner
decision: authorize the bounded CI setup/diagnostic correction and review it
before any separately authorized new commit/push/ordinary CI run. The successful
local source install/owner desktop evidence and N1–N3 acceptance remain intact.

The following source review and desktop sections preserve their earlier scopes.

## Final source review — READY FOR COMMIT AND CI

The exact existing change set is ready for owner review: **47 paths**, including
this report and the reconciled existing review proposal. Each proposed path has
an explicit necessity reason and SHA-256 in
[the exact commit proposal](evidence/n4/source-first-2026-11-03-review-proposal.json).
HEAD remains `b7ab94265270866911311b4ca818071868f58361`; target is
`origin/desktop/p2-production-integration`. The index is empty. No code correction,
new file, new test, build, GUI execution, commit, push or Actions run was needed
for this final review. All 167 consumed source inputs are present in the intended
tree and its source inventory still verifies. The earlier 238 native and 39
workflow test results apply to unchanged implementation/CI bytes; they were not
rerun. Forty-seven protected artifact/control hashes remain unchanged.

The nine tracked trace ZIPs were reviewed in memory and remain unchanged. They
contain synthetic loopback browser tests and captured application/fixture images,
not private user workspaces. Network records contain no authentication/cookie
headers or stored cookie configuration; no actual credentials were identified.
The only private-key-pattern hit in the current source tree is an intentional
header-only rejection-test literal in `ci/release/test_signing.py`, not a key.
The trace CSS matches the accepted frontend CSS. All 30 captured font copies match
the retained Inter inventory; full OFL/copyright and MPL notices and exact
BlockNote source-package URLs are included. No JavaScript response bodies are
retained in these ZIPs. No deletion or history rewrite is justified by this review.
This is a bounded current-tree/content review, not a universal secret/history or
future dependency-redistribution clearance.

Revised CI keeps the existing required security/test gates and read-only action
permissions. Its native job performs a real clean no-Git online installation,
seeds a synthetic schema-5 folder/note/image plus persisted origin and Qt-profile
settings sentinel, then runs the real online updater with a distinct **synthetic
packaging version**. It verifies every profile byte is preserved, the old release
remains, the new installed providers verify, and the transaction completes. The
application/frontend/runtime/bootstrap compatibility contracts remain identical;
this does not establish arbitrary future app/schema/dependency update support.
Only safe JSON is uploaded. CI 41621033436 remains PASS for its original inputs;
the revised hosted install/update check is still **NOT EXECUTED**.

No actual blocker to committing this source-first batch was identified. N1–N3
remain ACCEPTED; N4 remains CONDITIONAL pending the revised hosted result and
owner acceptance. Commit/push/CI and eventual publication each still require
their separate owner authorization. Existing evidence/report links account for
the included historical JSON records; no redundant evidence package was created.

## Minimum desktop checkpoint — VERIFIED PASS

Owner-host load and independent readback: **PASS**. The saved result
`ci-output/native-n4-source-first-1/policy-owner-load/result.json` has SHA-256
`b08439e91bd960c920ec9dda8d0423ddb9387857703f2543e2a4fdcbe2a4bdf4`.
The exact approved manifest/policy hashes match, and the live kernel reports
`cyrnava-native-u1000-f7923bc267d726793d455fbc543917c8` PRESENT in enforce mode.
The owner completed the one focused GNOME Applications launch. Independent
review of `ci-output/native-n4-source-first-1/desktop-owner-1/result.json`
confirms **PASS / complete true**. Result SHA-256:
`14efd244146bc23464c7381b86462b38091b427749ad42c1db912a09558bfd08`.
Final observation SHA-256:
`123efd8633783a78c5daec281ffe238924474e651e85c8d667a0dce6f27df03b`.
Manifest/receipt/policy/desktop/observer bindings match. Live backend, expected
Qt providers, renderer protections, exact AppArmor attachment and rejection of
unauthenticated requests passed. Owner confirmed the GUI/icon, existing bold
note/image, default System appearance and normal close. Before/after read-only
domain audit bytes are identical (SHA-256
`af37ad53871a2b426156aed5840667df6fb7c1c3751894a20ce6279406076696`),
with one schema-5 workspace, folder, note and asset. The saved-data/workspace/
origin equality assertion passed. Owned-process cleanup and temporary menu-entry
removal passed and their absence was independently confirmed. The nested audit's
`GUI: NOT EXECUTED` describes its read-only audit subprocess, not the live launch.
No unavailable numeric exit code is invented for the external GNOME child.

**Focused desktop verification is complete. N4 remains CONDITIONAL.** The next
essential technical check is the prepared distinct-version source-online update
in revised CI; an exact-artifact reinstall alone does not claim that result.
Prepare/reconcile the final source-first change set for owner review, then obtain
separate commit/push/CI authorization. Final public-source/notices review and
publication approval follow. No additional GUI rehearsal is required for this
unchanged candidate. N1–N3 acceptance and historical records remain unchanged.

The completed owner-host command is retained below. Existing N2/N3 CLI wrappers
hard-pin their original clients/evidence, so this command calls their unchanged
menu/live-observer and stopped-profile-audit functions directly for N4. It does
not substitute old GUI results, modify application code, or create a new
implementation file. It registers one temporary menu entry and removes only
that unchanged entry afterward. Existing installation and all earlier evidence
are retained. No new policy operation, installation, build or GUI execution has
been performed by the agent.

At preflight the synthetic profile already had **N1 synthetic folder / N1 synthetic note**,
bold **N1 persisted text**, and an attached small synthetic PNG. Its Qt profile
was unused, so the expected appearance was **System**; no pre-existing Dark
preference is claimed or required. Do not edit content or change appearance.

Historical executed command — **do not rerun**. It executes the exact reviewed
Python block in this report while keeping terminal input available:

```bash
cd /home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
/usr/bin/python3.14 -B -I -c "$(sed -n '/^# BEGIN N4 DESKTOP OWNER COMMAND$/,/^# END N4 DESKTOP OWNER COMMAND$/p' ci/N4_REPORT.md)"
```

Press Enter once when prompted; open GNOME Applications and click
**CyrNava — N2 Candidate** once. Select the existing note, inspect its image and
System appearance, then close only that candidate normally when **LIVE CHECKS
PASS / CLOSE** appears. Return to the terminal and enter **CONFIRM N4 DESKTOP**
only if all visual observations were correct. Blank/mistyped input is reprompted
up to three times; **NO** records non-confirmation. Security acquisition is
bounded to 30 seconds after launch; manual launch has two minutes, and the open
window has three minutes. If a failure appears, close the candidate normally,
preserve the attempt and do not retry automatically.

Only actual verification evidence is written to the fresh
`ci-output/native-n4-source-first-1/desktop-owner-1/` directory. The command
refuses an existing attempt or colliding menu entry. Raw exception/audit logs
remain private. Successful observation of an external GNOME child does not
invent an unavailable numeric exit code; owner normal-close confirmation and
owned-process cleanup are recorded separately. This single launch does not
claim a new restart, update or reinstall test.

<details>
<summary>Exact focused desktop command body (review before execution)</summary>

```python
# BEGIN N4 DESKTOP OWNER COMMAND
import hashlib, importlib.util, json, os, sys, traceback
from pathlib import Path

repo = Path.cwd()
base = repo / "ci-output/native-n4-source-first-1"
source = base / "zip-source"
client = source / "ci-output/client"
output = base / "desktop-owner-1"
manifest_sha = "3416caf94afc6c037f59d9b4ac4ff1a0ba844b6afc60b690e154efd89f8c4306"
policy_sha = "c3cf7b596799d69b693a08b5930ea991f7656b21abd53e4755ad821ca692cffb"
profile_name = "cyrnava-native-u1000-f7923bc267d726793d455fbc543917c8"

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

engine = module("n4_owner_engine", source / "desktop/install_engine.py")
engine.host_supported()
engine.require(
    sys.stdin.isatty() and os.environ.get("WAYLAND_DISPLAY")
    and os.environ.get("XDG_SESSION_TYPE") == "wayland"
    and "gnome" in os.environ.get("XDG_CURRENT_DESKTOP", "").casefold(),
    "Use ordinary GNOME Wayland Terminal",
)
engine.require(
    Path("/proc/self/attr/current").read_text().strip() == "unconfined"
    and "NoNewPrivs:\t0" in Path("/proc/self/status").read_text(),
    "Use an ordinary owner terminal; no host settings changed",
)
engine.checked_path(output)
engine.require(not output.exists(), "Existing desktop attempt preserved; do not retry")
current = engine.load(client / "current.json")
release = client / "releases" / engine.member_name(current["release"])
receipt, manifest = engine.installed(release)
engine.require(
    receipt["manifest_sha256"] == manifest_sha
    and manifest["kind"] == "candidate"
    and receipt["profile"] == str(client / "client/profile"),
    "Exact disposable N4 installation required",
)
api = engine.support(release, "apparmor_support")
loaded = engine.load(base / "policy-owner-load/result.json")
engine.require(
    loaded["status"] == "PASS" and loaded["complete"] is True
    and loaded["manifest_sha256"] == manifest_sha
    and loaded["policy_sha256"] == policy_sha
    and engine.digest(base / "policy-owner-load" / profile_name) == policy_sha
    and api.read_loaded_profile(profile_name)
    == {"state": "PRESENT", "profile": profile_name, "mode": "enforce"},
    "Exact reviewed policy must already be loaded; no policy operation here",
)
for name, expected in {
    "verify_menu.py": "1456d268cda4654eacd1ba4f330116db5570a23a0a4ef4302ea60721c84920f2",
    "feasibility/check_application.py": "406e0afd6011dbf9f1e9031d8f6e8c8cdf8eb5ba3b7557b2db4fca67260584ed",
}.items():
    engine.require(engine.digest(source / "packaging/native" / name) == expected,
                   "Accepted observer changed")
menu = module("n4_existing_menu_observer", source / "packaging/native/verify_menu.py")
check = module("n4_existing_live_checks",
               source / "packaging/native/feasibility/check_application.py")
operations = engine.support(release, "native_operations")
profile = Path(receipt["profile"])
desktop = client / "xdg/applications" / (manifest["app_id"] + ".desktop")
engine.require(desktop.read_bytes() == engine.desktop_entry(
    release, manifest["app_id"], True, native=True), "Installed Desktop Entry changed")
data = engine.checked_path(Path(os.environ.get(
    "XDG_DATA_HOME", Path.home() / ".local/share")))
entry = engine.checked_path(data / "applications" / desktop.name)
engine.require(not entry.exists() and not entry.is_symlink(),
               "Existing menu entry preserved")
engine.require(menu.find_gui(client / "launch.py") is None,
               "Close the N4 candidate before this check")
check.CANDIDATE = release
check.EXPECTED_APPARMOR = profile_name
check.unauthenticated_rejected = lambda: menu.unauthenticated(receipt, engine)
menu.CLOSE_INSTRUCTION = (
    "N4: LIVE CHECKS PASS. Once the existing note/image and System appearance "
    "look correct, CLOSE ONLY the N2 Candidate window normally. Do not edit. "
    "Then return here for the confirmation prompt."
)

def saved_data():
    return {name: info for name, info in operations.inventory(engine, profile)["files"].items()
            if name in {"active-workspace.json", "desktop.json"}
            or name.startswith(("workspace/", "workspaces/"))}

os.umask(0o077)
output.mkdir(mode=0o700)
record = {
    "status": "FAIL", "complete": False, "stage": "prelaunch",
    "scope": "N4 source-first single GNOME Applications launch; existing synthetic data",
    "manifest_sha256": manifest_sha, "policy_sha256": policy_sha,
    "receipt_sha256": engine.digest(release / "installed.json"),
    "policy_result_sha256": engine.digest(base / "policy-owner-load/result.json"),
    "observer_sha256": engine.digest(source / "packaging/native/verify_menu.py"),
    "desktop_sha256": engine.digest(desktop),
    "appearance_scope": "Previously unused Qt profile: verify default System; no prior Dark claimed",
    "checks": {},
}
registered = None
try:
    with operations.stopped(engine, profile):
        before = saved_data()
        record["before"] = operations.inspect_profile(
            engine, release, profile, output / "before-data.json")
    input("N4: press Enter to register ONE temporary candidate menu entry: ")
    record["stage"] = "menu-registration"
    registered = menu.register(engine, desktop, entry)
    record["discovery"] = menu.gio_discovery(entry)
    engine.require(all(record["discovery"][k] for k in
                       ("correct_path", "correct_id", "should_show")),
                   "GNOME menu discovery failed")
    record["checks"]["menu_discovery"] = "PASS"
    record["stage"] = "owner-menu-launch"
    engine.durable(output / "progress.json", record)
    print("Open GNOME Applications, search CyrNava, and click "
          "'CyrNava — N2 Candidate' ONCE within two minutes.\n"
          "Open 'N1 synthetic folder' > 'N1 synthetic note'. "
          "Inspect bold 'N1 persisted text', the small synthetic image, and System appearance. "
          "Do not edit or change appearance. Follow the terminal CLOSE instruction.",
          flush=True)
    record["live_checks"] = menu.observe_menu_launch(
        check, client / "launch.py", window_seconds=180, evidence_seconds=30,
        record_observation=lambda value: engine.durable(output / "observation.json", value))
    record["stage"] = "post-close-data"
    with operations.stopped(engine, profile):
        engine.require(saved_data() == before, "Saved data/workspace/origin changed")
        record["after"] = operations.inspect_profile(
            engine, release, profile, output / "after-data.json")
    record["checks"]["saved_data_workspace_origin"] = "PASS"
    record["stage"] = "owner-visual-confirmation"
    for _ in range(3):
        answer = " ".join(input(
            "Only if you used GNOME Applications, saw the correct GUI/icon, bold note, "
            "image and System appearance, and closed normally, type CONFIRM N4 DESKTOP "
            "(or NO if incorrect/unsure): ").split()).casefold()
        if answer == "confirm n4 desktop":
            record["checks"]["owner_visual_and_normal_close"] = "PASS"
            break
        engine.require(answer not in {"no", "cancel"}, "Owner did not confirm")
        print("No confirmation recorded. Use CONFIRM N4 DESKTOP or NO.", flush=True)
    engine.require(record["checks"].get("owner_visual_and_normal_close") == "PASS",
                   "Owner visual confirmation missing")
    record.update(status="PASS", stage="complete")
except (Exception, KeyboardInterrupt) as error:
    (output / "exception.private.log").write_text(traceback.format_exc())
    record["error_type"] = type(error).__name__
finally:
    if registered is not None:
        try:
            menu.unregister(engine, entry, registered)
            record["checks"]["temporary_menu_entry_removed"] = "PASS"
        except (OSError, ValueError):
            record.update(status="FAIL", menu_cleanup="Changed entry preserved; review required")
    record["complete"] = True
    engine.durable(output / "result.json", record)
    print(json.dumps(record, indent=2), flush=True)
raise SystemExit(0 if record["status"] == "PASS" else 2)
# END N4 DESKTOP OWNER COMMAND
```

</details>

The installation evidence and earlier pre-load handoff below describe their
original checkpoints. **Do not rerun the already completed policy-load command.**

## Current source-first checkpoint — local installation verified

3 November 2026. **N1–N3 ACCEPTED / COMPLETE. N4 CONDITIONAL.**
Active delivery is the source-first GitHub repository with an online dependency
installer. Root `bash install.sh` and `bash update.sh` now prepare recipient-local
builds and reuse the existing engine. No bundled-wheel public release is required.
The offline package and its successful CI 41621033436 remain accepted only for
their original inputs. No old Flatpak completion gate is active.

Actual local experiment: `ci-output/native-n4-source-first-1/`.
A source-only ZIP fixture was exported and extracted without Git metadata,
wheelhouse, node_modules, venv or built frontend. This is a local compatibility
fixture, not a falsely attributed GitHub-hosted download. Its 167 consumed files
are 3,543,906 logical bytes. Prerequisite checks passed on Ubuntu 26.04.1,
system CPython 3.14.4, Node 24.19.0 and npm 11.6.2.

| Changed boundary actually verified | Result |
| --- | --- |
| Locked frontend acquisition/build | PASS: all 328 npm entries use official HTTPS registry URLs and SHA-512; fresh npm ci with lifecycle scripts disabled, then explicit production build with pre/post hooks disabled |
| Python acquisition | PASS: exact 19 pinned wheels downloaded from official PyPI file URLs over TLS with isolated/hash-required/binary-only/no-index/no-deps/no-cache settings; size/SHA-256 checked before installation |
| Versioned private installation | PASS: wheel-free internal staging ZIP, 79 payload files, final-location venv, 4,414 provider-file checks, exact coherent 6.11.3 provider versions and ELF dependencies |
| Actual backend/data | PASS: unauthenticated and wrong-origin rejection, folder/rich-note/image persistence, restart/image integrity, stable origin/token revocation and owned-backend cleanup |
| Existing application preservation | All 64 compared application files except the expanded third-party notice match the accepted hosted artifact; current core-source binding has zero mismatches |
| Maintenance/data preservation | PASS: actual exact-source-artifact reinstall via N3 audits/checkpoint/journal/activation path; one schema-5 workspace with one folder/note/image, all six profile files / 94,319 bytes unchanged |
| AppArmor | Actual policy generation/parser PASS; named enforce profile ABSENT; no load or GUI attempted |
| Regressions | 238 native installer/security/transaction tests + 39 workflow tests PASS (277 total), including the 40 new source/engine/snapshot cases; not a repeat of N1–N3 GUI procedures |
| Static preparation | Configured new-source/CI lint, formatting, shell syntax and exact workflow security/dependency contract PASS |

Source fixture SHA-256:
`6725533dfe6399b36360c44275ef8e551e95bda1b4911e4b6deb9eddd6ca20f3`
(2,168,611 bytes).
Actual source-release metadata SHA-256:
`394669fa65915fd0c911e79b8410c1ec0c8e3787eeef1bf5bb2dd51e094680a9`.
Source inventory:
`db9218b1942ac8f58ef7fddd266b94336efbfaba0eae5dda8f29f1bf8623468a`.
Local internal payload:
`096a75dbf338caeb980c058be45d00a08ea9f8be7bb0e80b9ec74e00d494b04e`.
Manifest:
`3416caf94afc6c037f59d9b4ac4ff1a0ba844b6afc60b690e154efd89f8c4306`.
Selected disposable release `0.1.0-n4.2-096a75dbf338caeb`,
identity `org.cyrnava.CyrNava.Devel`; application version remains 0.1.0.
These hashes identify local test inputs, not a production signature.

After that execution, only the catalog's current-status wording and explicit
`bash ./` maintenance-wrapper instructions changed in the two consumed documents
`docs/native-redistribution.json` and `docs/native-installation.md`. The final
metadata inventory was refreshed and independently verified as
`cd11a26a230936ec13d28c27e0054462e7a1bb6f10852e878c1d7ebe039e2ceb`.
No installer, application, lock, runtime or frontend input changed after the
actual installation. The original test fixture/result hashes remain unchanged;
this documentation-only refresh is not represented as another execution.

### Reuse and adaptations

| Existing component | Source-first treatment |
| --- | --- |
| N2 platform/path/extraction/provider/backend checks, installed verification and native launcher | Reused; original legacy functions and sandbox/authentication controls preserved |
| Signed offline archive authentication | Preserved unchanged; source flags alone cannot bypass it |
| Source authenticity | Explicit new boundary: user-selected reviewed immutable source; same-source inventory detects changes but cannot authenticate a malicious installer |
| Environment setup | New exact official-file acquisition; existing verified local hash-only wheel installation/provider checks reused |
| N3 stopped-profile audit, checkpoint, transaction, recovery, rollback and uninstall | Reused; source updates require identical app/frontend/runtime/bootstrap input contracts; generated frontend bytes may differ only within that unchanged contract |
| Native identity/AppArmor bootstrap | Same bounded C compilation, exact-path attachment and enforce requirement; no privileged load |
| Frontend | New clean source build; existing editor/dependencies untouched; no Node process at runtime |
| CI native job | Prepared no-Git online install plus distinct synthetic source-release update; same graph/pins/required gate, JSON-only upload; no Actions execution |

`source-release.json` records the release version and per-file consumed-source
inventory, including the existing locks. Git is optional during installation.
No moving-branch fetch, package upgrade, mirror, TLS bypass, global pip install,
database migration, policy bypass or automatic updater is introduced.
Default cache creation works for a fresh user; explicit disposable paths leave
normal cache/application data alone.

Distinct-version online installation/update is prepared in `ci/native_source.py`
but **NOT EXECUTED locally or hosted**. Local actual maintenance was exact-artifact
reinstall, while distinct-version, corruption, compatibility, interruption,
checkpoint and trust-mode behavior have focused regression coverage. The CI
driver deliberately requires 11 GiB free for two environments. Do not promote
the earlier hosted PASS into a result for this new workflow.

### Resources and retained observations

One actual source installation took 60.911 seconds. Peak sampled new allocation
was 1,446,285,312 bytes; after maintenance/policy evidence, 1,447,481,344 bytes.
Free space was 5,271,318,528 bytes immediately before acquisition and
3,879,882,752 after it; concurrent host activity can affect the delta.
Largest child RSS was 566,784,000 bytes, not aggregate memory.
The local experiment stayed below its 2 GiB new-output cap and above 1.5 GiB
headroom. Its source-specific 3.5 GiB initial precondition does not alter the
old offline build's 5 GiB floor or relabel either historical floor failure.
No cache, accepted artifact or historical attempt was removed.

A bounded no-network npm probe exposed a real configuration defect: using
/dev/null for both user/global configs fails with “double-loading config.”
Distinct empty owned configs and explicit hook suppression corrected it, with
regression coverage. Source-change checks before/after assembly prevent a mixed
frontend/source snapshot. Initial broad lint probes used different rule scope;
configured checks pass after the new string/import fixes. Existing unrelated
legacy lint observations were not silently rewritten or security tests removed.

### Redistribution/public source boundary

The [revised assessment](../docs/native-source-obligations.md) and
[catalog](../docs/native-redistribution.json) separate our distributed source/assets
from recipient-acquired wheels/npm packages. No Qt wheel/source-correspondence
clearance or Rust binary attribution closure is claimed for the historical
offline package; those are no longer automatic active gates when such binaries
are not distributed. Original MIT / Copyright (c) 2026 74Cerillion and branding
rights remain settled. Applicable copied notices, MPL source availability and
font terms remain.

The tracked HEAD has 1,622 paths / 48,140,360 logical bytes, no wheels/venvs/
node_modules/dist/native executables. Nine preserved historical trace ZIPs
(25,925,790 bytes) contain captured HTML/CSS and exact Inter font bytes. Ordinary
GitHub ZIP/clone includes tracked records; an installation allowlist or .gitignore
does not remove them. No history/secret-content clearance is claimed. The owner
must review the actual final public tree/history, retaining required notices or
separately deciding an appropriate publication/exclusion strategy. No deletion,
export/history rewrite or publication was performed.

### N4 owner checkpoint

Minimum desktop preflight, 3 November 2026: **PASS**. Read-only verification
confirmed the unchanged source fixture, manifest, 79 installed payload files and
4,414 provider files. Active receipt SHA-256 is
`7d75578e3b2cd5b4b7528f069bce8e8d1d9722ab4acd6661fd8019854121ca03`.
The exact policy bytes match the accepted N2/N3 renderer: one literal native
bootstrap attachment, enforce mode, ordinary-user access plus `userns create`,
and `ix` inheritance for the exact interpreter/helper paths. The named kernel
profile is currently ABSENT; `policy-owner-load` does not exist. Owner-host
policy verification and desktop verification remain **NOT EXECUTED**, pending
owner approval/execution of the command below. No candidate regeneration,
application change, policy load, GUI launch or additional rehearsal occurred.

Local implementation/headless installation and exact-artifact maintenance PASS.
N4 remains CONDITIONAL for focused owner-host desktop/renderer verification,
the distinct-version online update and revised hosted CI, and final public-source
review/publication approval. No production binary signing gate is introduced for
a source-only release. The old successful package, original failures and N1–N3
acceptance retain their exact scopes.

The first next action is separate approval to load the prepared exact policy
and perform a focused desktop check on the new disposable client. Proposed
normal-owner-terminal command (NOT EXECUTED):

```bash
cd /home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
/usr/bin/python3.14 -B -I ci-output/native-n4-source-first-1/zip-source/packaging/native/policy_setup.py load \
  --owner-host --disposable \
  --root "$PWD/ci-output/native-n4-source-first-1/zip-source/ci-output/client" \
  --manifest-sha256 3416caf94afc6c037f59d9b4ac4ff1a0ba844b6afc60b690e154efd89f8c4306 \
  --policy-sha256 c3cf7b596799d69b693a08b5930ea991f7656b21abd53e4755ad821ca692cffb \
  --output "$PWD/ci-output/native-n4-source-first-1/policy-owner-load"
```

Prepared profile is `cyrnava-native-u1000-f7923bc267d726793d455fbc543917c8`.
Review the generated file in `ci-output/native-n4-source-first-1/policy-review/`
before approving load. Do not repeat if the proposed load output already exists.
After actual load readback, the focused check can use this client's real Desktop
Entry, verify loaded renderer/authentication/cleanup, and inspect the retained
synthetic note/image without another full historical rehearsal. No GUI command is
executed by this task; old N2/N3 manifest/policy commands must not be reused.

Current saved evidence: [source-first result](evidence/n4/source-first-2026-11-03-result.json),
[source payload audit](evidence/n4/source-first-2026-11-03-source-audit.json).
Exact changed paths/hashes and preserved inputs are in the review proposal linked
by the result. Commit/push, Actions, normal installation, host policy loading,
production signing and publication remain separately unauthorized.

Final preservation verification passed for 47 protected artifacts/control inputs,
14 prior evidence records and 11 unchanged legacy engine function ASTs. The two
engine files contain the explicitly authorized source-mode adaptations; they are
not misreported as byte-identical. Core application, frontend source/locks, Qt
locks, bootstrap and AppArmor implementation remain unchanged. The exact current
working tree, including prior uncommitted materials, is bound in the
[review proposal](evidence/n4/source-first-2026-11-03-review-proposal.json).

## Historical offline-package redistribution checkpoint — preserved

The following status and inquiries refer to the previous distribution model.

3 November 2026. **CONDITIONAL — SPECIFIC REDISTRIBUTION OBLIGATIONS REMAIN.
Hosted CI and independent artifact verification PASS; N1–N3 ACCEPTED / COMPLETE.**

## Current checkpoint — bounded third-party source and notice preparation

The hosted `b7ab94265270866911311b4ca818071868f58361` / CI `41621033436`
checkpoint remains PASS. This local documentation/material pass does not modify
that artifact or certify the final public package. The reviewed dependency set
is 19 locked distributions, 498 ELF files and 18 upstream license/notice/SBOM
documents; four Qt/PySide/Shiboken wheels contain no such documents. Existing
source hashes were reverified without downloading, building or unpacking Qt.
Three exact BlockNote archives match all 1,454 published installed files (729
source files); all 18 shipped Inter fonts match the core source archive.

MIT `Copyright (c) 2026 74Cerillion` and owner rights to the CyrNava name/logo
are settled. Prepared material preserves source identities and existing notices,
adds version-appropriate font and generated-frontend-runtime attribution, and
proposes intact corresponding-source assets alongside the eventual binary in
the same GitHub Release. The accepted package does not yet contain new material.
See [current obligations and unsent clarification drafts](../docs/native-source-obligations.md).
The [exact source/notice catalog](../docs/native-redistribution.json) maps all 18
original documents: 15 license texts prepared in [one notice file](../docs/native-third-party-notices.txt)
and three original upstream SBOM members retained in the unchanged wheels.
That file also preserves seven version-scoped standard license/exception texts.
See [material/hash evidence](evidence/n4/redistribution-2026-11-03-materials.json)
and [uncommitted review proposal](evidence/n4/redistribution-2026-11-03-commit-proposal.json).

Remaining redistribution work is specific: exact four-wheel Qt/PySide/WebEngine/
Chromium revision/patch/build/source and native-credit correspondence (including
FFmpeg and ICU); actual GPL/LGPL/Qt-exception component obligations; a practical
recipient replacement/rebuild route; and use-composed-ref attribution clarification.
The pydantic-core SBOM lists 99 components, including Unicode-3.0, Zlib and
Apache/LLVM-exception terms; the sole core MIT license is not complete evidence
of corresponding bundled-component notices. The SBOM alone does not establish
which build-scope components are present in the native extension. That specific
notice/mapping uncertainty remains, without claiming every SBOM entry is shipped.
The use-composed-ref MIT declaration is confirmed; no absent copyright holder is invented.
Source archive versions and standard license copies alone do not clear these
items. No large source build, reproducibility certification or new infrastructure
is added as a gate. Existing hash/security checks remain unchanged.

No GUI, package build, dependency change, host-policy operation, Git mutation,
signing, publication or upstream contact occurred. Historical records remain
under their original identities. Signing, final public-package native/security/
manual-update verification and publication approval remain later checkpoints.
The next owner action is review/authorization of the two unsent targeted inquiries
or provision of equivalent authoritative source/build/notice material. This does
not imply contact or a new commit/push; Rust component attribution mapping remains
a separate identified material gap.

## Accepted hosted checkpoint — authorized schema-correction push and verification

The exact reviewed 17-file proposal was independently reconciled against every
bound hash, staged path and staged byte. Preflight verified 45 protected hashes;
final review also rechecked four accepted N2 artifact/native-evidence hashes.
Existing 299-test local evidence matches the committed source; tests were not
unnecessarily repeated. Independent read-only content/security review found no
blocker. Protected `.git` access initially blocked staging before any index
mutation; the explicit metadata grant resolved that permission issue.

One commit **`b7ab94265270866911311b4ca818071868f58361`**, parent
`2b3ca78f7c5f4f6227d376a96cc3f8d46454b9b8`, tree
`09722d4c91f21caac693e9cd4107996e9ada24ba`, contains exactly the 17 approved paths.
One normal fast-forward push updated `desktop/p2-production-integration`.
Independent remote Git and GitHub API/blob readback match the exact source,
parent, tree and file inventory. `main` remains default and unchanged at
`4021bc292267c19b7ebebf219b4f682f8f99bf4c`.
[Exact committed inventory/readback](evidence/n4/hosted-41621033436/remote-readback.json).

[Ordinary CI 41621033436](https://github.com/74Cerillion/CyrNava/actions/runs/41621033436),
attempt 1, push event, completed **SUCCESS** (3 November, 19:39:05–19:44:37 Korea).
Workflow ID `402398273`, path `.github/workflows/ci.yml`, source bound to that commit.

| Actual hosted scope | Result |
| --- | --- |
| Workflow validation | PASS; 38 tests |
| Backend/security and historical regressions | PASS; 574 current + 37 subtests; 351 historical + 198 subtests |
| Frontend/browser | PASS; 277 units, lint, TypeScript/production build, 21 Chromium tests |
| Native installer/security/transaction regressions | PASS; 198 tests, including disposable-signature fixtures |
| Native feasibility | PASS; 63 tests, including corrected schema fixtures; zero skips |
| Native assembly/exported-package/source/installer audit | PASS; 99 payload files, 285 source files, 19 hash-pinned wheels |
| Fresh isolated installed imports/providers/ELF/backend/data | PASS; 4,414 provider files; no GUI/policy load |
| Required CI completion gate | PASS; all five jobs succeeded |

### Actual runner schema observation remains BLOCKED

The unmocked observation reports `compiled-schemas`, reason
`group-or-world-writable`, UID/expected OS UID `0`, mode **`0777`**, errno null.
The production guard rejects these writable compiled schemas. This is an actual
current-run rejection, separate from successful deterministic unit fixtures and
headless package installation. **Normal launcher schema preflight cannot pass on
this runner in that observed state.** CI headless installation does not invoke
schema preflight, normal bootstrap, GNOME launch or renderer execution. No such
PASS is inferred. Previous run 41616088358's exact rejected metadata remains
unrecorded; the new values are not retroactively attributed to it. No trust guard,
host permissions or security controls were changed.
[Actual observation](evidence/n4/hosted-41621033436/schema-host-observation.json).

### Independently verified hosted development package

- Artifact `13222454924`, outer ZIP 276,466,671 bytes, SHA-256
  `8db73e247afd3c637c327e53d75b8c69559b32b7099a19cffdf1ecafa4a2264c`.
- Package `CyrNava-0.1.0-n4.1-ubuntu-x86_64.zip`, SHA-256
  `1e49348570e7f779a352cb0a2d623a6f3973f828628b9ea60bb6e4fc6f2a3897`.
- Manifest SHA-256 `9bc9bad42c7d8fdf3b4601d4ab4804ecda6cdfd6b2a931d383f52fe88bb185a8`.
- Source ZIP SHA-256 `7fe4b4b861756b129f7c3e4e3a113b8c20b434a6ab690d61d71f05e5d3b722dc`.
- Installer ZIP SHA-256 `1b9a0bedafe997757690a3dd8e04607c59cdc09a685cf05597e90f4ef587086e`.
- Clean source at the new commit; installed release `0.1.0-n4.1-1e49348570e7f779`.
  Identity **`org.cyrnava.CyrNava.Devel`**, target
  `ubuntu-26.04-x86_64-wayland-cpython314`; PySide6/Addons/Essentials/shiboken6
  remain the pinned 6.11.3 stack. This is a development verification package,
  not the final public-identity release.

All four downloadable artifacts match their GitHub API sizes/digests and CRCs.
Full byte checks cover exported checksums, immutable Git source, dependency locks,
wheel bytes, application/helper/bootstrap source correspondence, frontend build
proof and standalone installer bytes. Native result/audit/install JSON agree
across the two native artifacts. Headless installation PASS follows audited engine
conditions requiring provider and synthetic backend child PASS, including auth,
origin, persistence, image and cleanup checks. Individual private child reports
were not uploaded; no independent local replay or GUI evidence is claimed.
[Native verification](evidence/n4/hosted-41621033436/native-artifact-verification.json),
[all artifact integrity](evidence/n4/hosted-41621033436/artifact-integrity.json).

The first bounded CLI read of the large artifact timed out at 180 seconds; its
record remains preserved. The official GitHub connector then materialized the
same artifact, read in 25.955 seconds and verified against the original API digest.
This changed read-only retrieval transport only; **no CI or build retry** occurred.
Large ZIPs stayed in bounded RAM; observed verifier peak RSS was 586,354,688 bytes.
Only metadata and compressed private logs are retained locally. The native CI
artifact expires 10 November at 10:44:26 UTC; no durable local ZIP copy is claimed.
The local packaging disk floor remains unmet, and no local package build ran.

### Owner checkpoint — hosted checkpoint passed; release remains conditional

Original hosted failures `41607482461`, `41612661098`, `41616088358`, accepted
N1–N3 artifacts/decisions and all earlier evidence remain unchanged. New status
and evidence updates are **local and uncommitted**; the one commit/push authority
is consumed. No additional implementation, commit/push, workflow dispatch/retry,
native GUI, host-policy change, production signing or publication occurred.

Remaining separate checkpoints are third-party notices/licensing/corresponding
source, genuine owner-controlled signing and authentic release trust, exact final
public-identity native installation/GUI/security, final-input manual-update
verification, and explicit publication approval. Earlier N2/N3 GUI acceptance
cannot certify this changed package. MIT / **Copyright (c) 2026 74Cerillion**,
owner-confirmed name/logo rights and the ordinary-user filesystem/network tradeoff
remain settled; renderer sandboxing, authentication and data protections remain
required. Native Ubuntu 26.04 x86_64 / GNOME Wayland via GitHub Releases archives
and manual full-package updates is the active target. Flatpak remains paused
historical/fallback, with no duplicate old P6 completion gate.

**Smallest next action:** review this successful hosted checkpoint, then separately
authorize closure of the outstanding third-party/source-delivery requirements for
the final package. No further CI correction is justified by this successful run.
[Consolidated evidence](evidence/n4/hosted-41621033436/result.json).
Earlier checkpoints below retain their original artifact and environment scope.

## Historical checkpoint — local correction status before this push

3 November 2026. **SCHEMA FIXTURES/DIAGNOSTICS LOCALLY VERIFIED / READY FOR REVIEW.
Latest hosted CI remains FAIL; N4 / public release CONDITIONAL.**

## Historical checkpoint — authorized schema fixtures and safe diagnostics

The owner authorized isolating the host-dependent schema tests and adding safe
metadata diagnostics. Only `packaging/native/feasibility/run_probe.py` and
`test_system_schemas.py` change implementation. No workflow, installer, dependency
lock, renderer configuration, application data/schema or host-policy changes.

The existing trust checks retain their acceptance conditions and order. A
`SchemaTrustError(ValueError)` now identifies a rejection using only a fixed
system-object category, fixed reason, UID, expected OS UID, octal permission mode
and errno. Unknown paths become `unreviewed-path`; raw paths, environment and
filesystem error text are excluded, including chained OSError output. Original
ownership/write-error prefixes remain compatible. The two original owner/write
predicates were also compared as syntax trees and are unchanged. Independent
read-only review found no blocker.

Unit query/environment/content-change tests now use deterministic synthetic trust
metadata. Negative coverage independently exercises wrong ownership, group/world
writes and symlinks at the fixed system objects, plus missing/nonregular compiled
schemas, metadata/read failures, query errors and content changes. Query/content
tests must reach their intended operation rather than pass at an unrelated early
host-metadata rejection. The real GLib test compiles two isolated synthetic schema
sets and uses real compiler/query/compiled bytes with explicitly synthetic trust
metadata. This is GLib selection coverage, not certification of actual host trust.

A separate unmocked observation records actual system-schema preflight status in
the unit job log. **A rejected host remains `BLOCKED` in that observation**, even
when the observation test itself completes successfully. Unknown exceptions still
fail the test. Future CI green cannot turn that observation into bootstrap,
application-launch, renderer or host-trust PASS. The normal launcher continues to
reject the same unsafe metadata. Printed observations will be in the job log;
they are not automatically an uploaded native diagnostic JSON artifact.

A controlled test-only `/usr` group-write profile reproduced the old three-case
result (2 errors, 1 failure). All 19 corrected focused schema tests pass under that
profile, while its trust observation remains **BLOCKED**, with category
`usr-directory`, UID/expected UID `0`, mode `0775`. These are synthetic profile
values, **not discovered values from GitHub**. The actual rejected object/UID/mode
in run 41616088358 remains unknown until a separately approved hosted execution
records it. The actual confined local schema-only observation passes; it does not
establish owner-host application or renderer behavior.

| Fresh committed-source snapshot plus two-file patch | Actual result |
| --- | --- |
| Exact native CI regression command, `ci-output` initially absent | 198 PASS, zero skips |
| Native feasibility | 63 PASS, zero skips; includes 19 focused schema tests |
| Workflow/negative-contract regressions | 38 PASS, zero skips |
| Workflow security/dependency contract, Ruff and formatting | PASS |

Unique local total: **299 passing tests**. Six actual disposable-signature tests
are included in the native total; their fresh synthetic one-day key fixture was
cleaned up. The snapshot contained 1,612 committed files / 48,073,056 source bytes;
all source bytes were unchanged after testing apart from the explicit overlays.
Observed temporary allocation peaked at 52,432,896 bytes within a 128 MiB bound;
verification took 3.975 seconds. Snapshot/test scratch was removed by normal test
cleanup. Early local fixture/wrapper iterations remain preserved privately.

The repository was below the 5 GiB packaging preparation floor. Tests used the
separate temporary filesystem and existing tools; no package preparation/build,
dependency download or retained-output cleanup was performed. Both resource
observations remain recorded. All ten pre-existing uncommitted files were
unchanged before these report updates; 45 protected files, including N1/N3
receipts/results and accepted package/security inputs, retain their hashes.

Source remains `2b3ca78f7c5f4f6227d376a96cc3f8d46454b9b8` plus the explicit patch:

- Diagnostic helper SHA-256: `81a4f6c6c3cad96fc6b6d4efba32c1511886d5cd341fbe8abe5dd8b1fde6d0b3`.
- Schema tests SHA-256: `995ae8eed99e17ed2aac7ce56403bf3a5b2522164e593c2c7f10d68ae5773cf8`.
- Two-file patch SHA-256: `555327bbc552fd4f3ca9a6825adbd45763fd51b451b0341bafba50cc106441e7`.

[Verification evidence](evidence/n4/schema-fixtures-2026-11-03/result.json).
[Exact uncommitted batch proposal](evidence/n4/schema-fixtures-2026-11-03/commit-proposal.json).
The helper is shipped as `system_schemas.py`; this diagnostic change is a future
package input. No candidate was rebuilt, and older artifacts are not represented
as testing these new bytes. CI's current headless install checks imports,
providers, ELF, installed identities and backend/data; it does **not** execute
system-schema preflight, bootstrap or the normal desktop launcher.

**Owner checkpoint:** review the uncommitted corrective batch. Any new commit,
normal integration push and hosted verification require separate authorization.
No staging, commit, push, GitHub execution, GUI/native rehearsal, production
signing or host security change occurred. All three original hosted FAIL records remain unchanged.
N1–N3 remain accepted; N4 and public release remain CONDITIONAL, pending hosted
native assembly/audit/install, final package verification and source/notice/signing
and publication requirements.

## Historical checkpoint — fixture-parent push and hosted verification

The owner authorized the reviewed corrective course: one commit and one normal
integration push, followed by ordinary CI and independent artifact verification.
Commit **`2b3ca78f7c5f4f6227d376a96cc3f8d46454b9b8`**, parent
`b5ad466b5c5694900e4463ffdef10f0b7c84a732`, tree
`1e97bd6898f1b075a457c14a0c4876eb73d91add`, contains exactly the 14 reviewed paths
and approved bytes. Staged review, independent read-only review, normal
fast-forward push and independent GitHub API/remote Git readback passed. `main`
remains default and unchanged at `4021bc292267c19b7ebebf219b4f682f8f99bf4c`.

[Ordinary CI 41616088358](https://github.com/74Cerillion/CyrNava/actions/runs/41616088358),
attempt 1, push event, completed **FAIL** (3 November, 19:03:46–19:08:43 Korea time).

| Hosted scope | Actual result |
| --- | --- |
| Workflow validation | PASS; 38 tests |
| Backend and security | PASS; 574 current tests plus 37 subtests; 351 historical tests plus 198 subtests |
| Frontend and browser | PASS; 277 units, lint, TypeScript/production build and 21 Chromium tests |
| Native regression command | **198 PASS**, including the five-case fresh-fixture regression and six disposable-signature tests |
| Following native feasibility command | **FAIL**; 54 tests ran: 51 passed, 2 errors, 1 failure |
| Native assembly/audit/isolated headless installation | NOT EXECUTED after feasibility failure; no package produced |
| CI required | FAIL; no bypass |

**The fixture-parent correction passed on the actual hosted runner.** The next
failure is the unchanged schema trust guard in
`packaging/native/feasibility/run_probe.py:31`. All three failed feasibility tests
hit `info.st_uid != Path("/").stat().st_uid or info.st_mode & 0o022` before the
font-key/query/content-change checks they intended to exercise. The error is
`ValueError: System schemas must be protected by the OS owner`.

The checked objects, in order, are `gschemas.compiled`, its system schema
directory, `/usr/share/glib-2.0`, `/usr/share`, `/usr`, and `/`. At least one has an
owner mismatch or group/world write bit under this runner's view. **The retained
logs do not identify which object, UID or mode.** Do not infer that the compiled
file itself is runner-owned or writable. No application or renderer failure has
been established; neither was executed.

The failed tests are `test_only_schema_search_override_changes` and
`test_real_glib_overlay_reproduces_missing_keys_and_system_selection_restores_visibility`
(errors), plus `test_schema_change_during_preflight_refused` (its expected later
changed-content error was preempted by the ownership/write-bit rejection).
Two unit tests mock query/contents while retaining dependence on actual host
trust metadata. The real GLib overlay test also stops before its system-selection
query. The earlier local clean source snapshot reused local OS metadata, so its
54 feasibility passes did not reproduce this hosted environment difference.

The smallest justified follow-up scope is deterministic trust-metadata fixtures
with explicit wrong-owner, writable and symlink negatives; separate real GLib
visibility coverage; and safe fixed-system-path category/UID/mode diagnostics to
identify the actual runner rejection. **Preserve the production trust guard.**
No host permission/security change or relaxation is justified by this result.
This is a proposed follow-up only: no implementation correction, test rerun,
second commit/push or workflow retry occurred after the hosted failure.

The always-run native diagnostic upload also failed because unstarted assembly
had produced no result/audit/install JSON. Both successful diagnostic artifacts
were independently downloaded into bounded RAM and verified against GitHub API
digests, sizes, CRCs and exact run/commit provenance:

- Backend artifact `13221780782`, 24,292 bytes, SHA-256
  `a4d0d0f1e8f07b497a25afcd689576b9bf648c4f66a11b2d80d67fc1615196f0`.
- Frontend artifact `13221128077`, 4,892,624 bytes, SHA-256
  `e4878bdc41ec81937eddb6f1b927a24b4f02503fee625c045d76a6792b27df58`.

Successful JUnit records are retained privately; diagnostic screenshot ZIPs were
not duplicated on disk. JUnit totals include subtests: 611 current backend, 549
historical and 21 browser, all without failures/errors/skips. No native artifact
exists to verify. Raw job logs remain private in `ci-output/native-n4-fixture-push-1/`.
[Hosted result](evidence/n4/hosted-41616088358/result.json),
[diagnostic integrity](evidence/n4/hosted-41616088358/artifact-integrity.json),
[remote readback](evidence/n4/hosted-41616088358/remote-readback.json).

Post-run documentation/evidence stays local and uncommitted. Earlier hosted FAIL
records and accepted artifacts remain unchanged. Owner review of the proposed
schema-test investigation/correction scope is next. Any later commit/push needs
separate authority. Native package verification, vendor source/notice closure,
genuine signing and separately authorized publication remain pending.

## Historical checkpoint — authorized fixture-parent correction

After reviewing run 41612661098, the owner authorized the small fixture-parent
correction and local clean-checkout regression verification. Only
`packaging/native/test_apparmor.py` changes implementation: its five fixture
`mkdir` calls now use `parents=True`. Production application, installer, dependency
locks, workflow and AppArmor policy bytes are unchanged. A new regression runs
each of the five affected setup paths in a separate minimal source fixture with
`ci-output` absent, so execution order cannot conceal missing-parent assumptions.

Before the five-call fix, that regression reproduced **five expected failures**,
each the original `FileNotFoundError`, errno 2. The failed test output and exact
pre-fix source remain private and preserved. After the correction, the full
committed source tree at `b5ad466b5c5694900e4463ffdef10f0b7c84a732` was extracted
with `git archive` into a fresh disposable directory, with only the corrected
test file overlaid. No existing output, environment, personal profile or `.git`
metadata was copied. All source bytes were checked unchanged after testing.

| Fresh source-snapshot check | Actual result |
| --- | --- |
| Exact native CI unittest command, starting with no `ci-output` | 198 PASS, zero skips; includes the new five-case regression |
| Following native feasibility command | 54 PASS, zero skips |
| Current workflow/negative-contract unit tests | 38 PASS, zero skips |
| Exact workflow security/dependency contract | PASS |
| Ruff on changed test file and diff whitespace check | PASS |

Unique passing test total: **290**. The six real disposable-signature tests are
included in the 198 native tests. They generated fresh one-day synthetic fixtures
and removed their private key directory successfully; no production identity was
used. No test assertion, renderer check, host-policy requirement or signature
guard was bypassed. This corrects test setup only and does not establish a new
application or renderer result.

The disposable snapshot contained 1,604 committed files / 48,039,524 source bytes.
Observed peak temporary allocation was 53,477,376 bytes, below its 128 MiB bound;
the snapshot and newly generated scratch were removed by normal test cleanup.
The recorded verification took 3.996 seconds. Existing dependency environments
were reused. All nine pre-existing uncommitted files were verified unchanged
before these report updates, and 43 protected artifact/application/security files
still match their original hashes. No retained evidence, accepted artifact,
working environment or owner data was deleted.

Source remains at `b5ad466b5c5694900e4463ffdef10f0b7c84a732`; corrected test SHA-256
is `3fc70892596a674d48d81eb3e7355b5d66d2021ffd3f003c7ea7cee6f6b48b37`;
test-only patch SHA-256 is
`1dcd33962a4cf375fe4aafd8a5bd687934cdcc4f76d719cdb72c6a1f238435aa`.
[Local verification evidence](evidence/n4/fixture-parent-2026-11-03/result.json).

**Owner checkpoint:** review this uncommitted test-only correction and the
preserved hosted-failure documentation. The exact paths/hashes are in the
[commit proposal](evidence/n4/fixture-parent-2026-11-03/commit-proposal.json).
A further commit/normal push and hosted verification need separate authorization.
No build, GUI, host-policy load,
dependency download, commit, push, signing or GitHub execution occurred in this
correction pass. Runs 41607482461 and 41612661098 remain **FAIL** under their
original identities. No native hosted package exists from those runs. Final
package verification, vendor notice/source closure, genuine release signing and
publication remain pending; N1–N3 stay accepted.

## Historical checkpoint — corrective push and hosted result

The owner authorized one corrective commit and one normal integration push.
Commit **`b5ad466b5c5694900e4463ffdef10f0b7c84a732`**, parent
`7d3bd86ad335b1a518c5dd7df09106b847d2256d`, tree
`8c1ebd9bc9a71b0b8e1cc707086f3fb2b17c3f62`, contains exactly the 26 reviewed
paths and approved bytes. Staged review, protected-file checks, normal fast-forward
push, and independent GitHub API/remote Git readback passed. `main` remains default
and unchanged at `4021bc292267c19b7ebebf219b4f682f8f99bf4c`.

[Ordinary CI 41612661098](https://github.com/74Cerillion/CyrNava/actions/runs/41612661098),
attempt 1, push event, completed **FAIL** (3 November, 18:38:29–18:42:57 Korea time).

| Hosted job | Actual result |
| --- | --- |
| Workflow validation | PASS; 38 contract/fixture tests |
| Backend and security | PASS; 574 current tests plus 37 subtests, 351 historical tests plus 198 subtests |
| Frontend and browser | PASS; 277 unit tests, lint, TypeScript/production build, 21 Chromium tests |
| Native Ubuntu package and exported-archive audit | FAIL during regression setup; 189 tests reported, 12 errors; suite incomplete |
| CI required | FAIL; no bypass |

**Confirmed new failure: clean-checkout fixture setup.**
`packaging/native/test_apparmor.py` lines 128, 151, 170, 216 and 359 call
`parent.mkdir(mode=0o700, exist_ok=True)` for
`ci-output/native-n2-apparmor-tests-1`. The fresh native checkout has no `ci-output`
parent, so those calls raise `FileNotFoundError`, errno 2. All 12 retained errors
name that same missing fixture directory. This includes a class setup failure;
the full 197-test native suite did not complete. The later feasibility command,
assembly, exported-package audit and isolated headless installation were skipped.
No hosted native package was produced. The always-run diagnostic upload also
failed because the unstarted assembly had produced no result/audit/install JSON.

The local native suite had an existing output parent and did not exercise this
clean-checkout precondition. Its earlier PASS remains valid only in that scope.
The failed setup does not establish a renderer or application failure: the affected
security assertions and package execution were not reached. No policy or security
check was disabled, and no application/host-policy correction is justified by this
record. The proposed smallest correction is to make these test fixtures create
their missing parent and verify the native suite with `ci-output` initially absent.
**No implementation correction, test rerun, second commit/push or workflow retry
was performed after this failure.** A new corrective batch requires owner review
and separate authorization before any further commit/push.

Both actual diagnostic ZIPs match GitHub API digests, sizes and exact run/commit
provenance, with valid CRCs and no JUnit failures/errors/skips:

- Backend artifact `13220185867`, 24,345 bytes, SHA-256
  `1b4b4315f011dcf956e8b26cc7a02a91fa712b55cbab2f34306077f33e9f0762`.
- Frontend artifact `13219129189`, 4,894,336 bytes, SHA-256
  `42553f6d20a016aa2e1aac5952fb3148b5f777cdcbc1227cce21972973f93c63`.

JUnit totals include subtests: 611 current backend, 549 historical, 21 browser.
They must not be added to the corresponding parent-test totals as unique tests.
Original job logs and downloads remain private in
`ci-output/native-n4-corrective-push-1/`; no native artifact was downloaded or
inferred. A prepared in-memory native artifact checker was not executed because
there is no package to verify. The previous hosted FAIL, all local findings,
accepted artifacts and N1–N3 acceptance remain intact.

[Hosted result](evidence/n4/hosted-41612661098/result.json),
[diagnostic integrity](evidence/n4/hosted-41612661098/artifact-integrity.json),
[remote readback](evidence/n4/hosted-41612661098/remote-readback.json).
These post-run report/evidence changes remain local and uncommitted. Vendor
notice/source closure, final public-identity native verification, genuine
production signing and publication remain separate release requirements.

## Historical checkpoint — authorized local corrective preparation

The owner authorized investigation and preparation after run 41607482461 failed.
No further project commit, push or GitHub execution was authorized or performed.
The integration checkout remains at `7d3bd86ad335b1a518c5dd7df09106b847d2256d`;
the index is empty and the corrective batch is uncommitted.

**Historical release-test cause confirmed for all 74 failures.** The original
JUnit traces identify the unchanged accepted-CI hash guard in 52 failures. A
focused observer then reproduced the remaining 22 failures on the active checkout
and recorded the same original guard rejection in every case, without replacing
its result. These are preserved expected-failure causal observations, not passing
regressions. [Causal evidence](evidence/n4/correction-2026-11-03/remaining-22-causal.json).

`ci/historical_release.py` now copies the **current unchanged** legacy code/tests,
locks and auditors into a small disposable source fixture. Only its CI file is
replaced with the exact accepted bytes recovered from
`b27e33bb0b31ecd93a3792c6b6a889686dfae575:.github/workflows/ci.yml`, hash
`3f11c9ab58d2f7c8cebca0b153a09ccffae06e314545067ddd6b42f7b8e809f4`.
This is a unit-test fixture, not a restored release target or old-code substitute.
Every copied source is hash-checked after testing. Current/native CI validation
runs separately; the accepted real policy still rejects the new native CI bytes.
No policy, workflow identity, artifact/source allowlist, signature guard or useful
historical test is relaxed or removed. `ci/verify.py` requires both test selections
to succeed before backend PASS. All 351 legacy regressions pass in that fixture.

**Frontend correction is test synchronization only.** A controlled delayed initial
selection-focus handoff reproduced the original expected-input/observed-tree
failure, while the immediate case passed. The autosave test now explicitly waits
for initial tree focus before editing, and still requires the title to retain
focus after saving. Immediate/deferred handoffs and independent tree refresh,
tab-stop and blocking-operation focus behavior are covered. The hosted record
did not retain initial event ordering, so that exact ordering remains unproved;
no production focus defect or application-code fix is claimed.

Two path-only build unit tests also depended on the actual temporary filesystem's
5 GiB capacity. Their stage is mocked; capacity is now an explicit synthetic
precondition, with a new independent low-space refusal assertion. The production
guard and original disk-precondition failures remain unchanged. The fixture's
first long temporary layout caused 17 real-GPG setup errors; these remain recorded.
A short child-only temporary path corrected that fixture compatibility. All real
signature tests use fresh disposable one-day synthetic keys, with successful test
cleanup; no production identity or expired accepted rehearsal credential is used.

| Final local selection | Actual result |
| --- | --- |
| Current backend, packaging and workflow | 574 PASS; includes 38 workflow/fixture tests |
| Historical release/security/current-code fixture | 351 PASS; 198 subtests PASS separately |
| Frontend unit | 277 PASS, 22 files, one worker |
| Production Chromium browser | 21 PASS, 2.2 minutes, one worker, zero retries |
| Native installation/security/maintenance tooling | 197 PASS, including the 6 actual disposable-signature tests omitted in the earlier preparation |
| Native feasibility | 54 PASS |
| New source-closure/audit focused subset | 16 PASS, included in native count |
| Ruff, frontend lint, TypeScript/Vite, actionlint and exact workflow contract | PASS |

Unique local total: **1,474 passing tests**, without adding subset counts twice.
The CI-equivalent test selections used the existing dependency environments rather
than reinstalling them. A fresh TypeScript/Vite output matches every preserved
`frontend/dist` byte used by backend/browser tests. No native GUI, A/B preparation,
new Qt build, dependency download, host-policy operation or normal installation ran.
The native assembly/install job itself has not been rerun in this correction pass.

The fresh review packet is `ci-output/native-n4-corrected-metadata-1/`:

- Application ZIP remains `ci-output/native-n4-release-proposal-1/CyrNava-0.1.0-ubuntu-x86_64.zip`,
  SHA-256 `994e526870bd82828a2c2c90c1a71860ea2e1ac828c0e1bfaf7e504261ecf790`.
- Corrected review manifest SHA-256:
  `dd1d694a141f9cfbe0edc44b1ee892f4fade3e26380e6ef7fbb0e32d3eef7f0b`.
- Source ZIP SHA-256:
  `1ddee3e29fc1492e2af7c712c2480b53513e02645f5cb617d368dc6ba4355400`.
  Its 285 source files now include the retained historical-test inputs required
  by the new helper; it still excludes evidence trees, environments and private data.
- Installer ZIP is byte-identical, SHA-256:
  `9c508116919ff4aedc085b7b9bb29800307a45f7d6ed1b7ba743eb9476df261a`.

This is an **audited unsigned local review packet**, based on 7d3bd86 plus explicit
uncommitted source/file hashes. It reuses the immutable application ZIP, with no
binary rebuild or replacement of accepted artifacts. Its source/manifest is distinct
from earlier packets, which remain intact. It is not a new hosted/signed release.

Browser scratch briefly reduced observed free space to 5,361,344,512 bytes, below
the 5 GiB preparation floor. No new packet/build was started then. The running
test's own successful cleanup restored 5,435,625,472 bytes before source-packet
creation; no retained evidence or cache was deleted. This transient observation is
retained rather than reported as uninterrupted resource-floor PASS. Final allocation
and free-space measurements are in the corrective evidence.

[Correction result](evidence/n4/correction-2026-11-03/result.json),
[test scopes](evidence/n4/correction-2026-11-03/tests.json),
[review packet](evidence/n4/correction-2026-11-03/review-packet.json).
Exact files/hashes for a proposed corrective commit are in
`ci/evidence/n4/correction-2026-11-03/commit-proposal.json`. **Next owner checkpoint:
review and separately authorize one corrective commit and normal integration push
for ordinary CI.** The original hosted run remains FAIL; no acceptance is inferred
from local tests. Vendor notices/source correspondence, final public-identity native
verification, genuine production signing and publication remain separate.

## Historical checkpoint — authorized integration commit and push

The owner approved the reviewed 46-file batch and one normal integration push.
Commit **`7d3bd86ad335b1a518c5dd7df09106b847d2256d`**, parent
`b27e33bb0b31ecd93a3792c6b6a889686dfae575`, tree
`1585cd42985f7a8b4ab6dbf9c4bdd27ee39badf3`, was created unsigned and pushed once to
`origin/desktop/p2-production-integration`. Remote parent/tree/exact paths were
independently read back. `main` remains default and unchanged at
`4021bc292267c19b7ebebf219b4f682f8f99bf4c`. No merge or release signing occurred.

[Ordinary CI run 41607482461](https://github.com/74Cerillion/CyrNava/actions/runs/41607482461),
attempt 1, push event, completed **FAIL** (3 November, 18:00:11–18:02:04 Korea time).

| Hosted job | Actual result |
| --- | --- |
| Workflow validation | PASS |
| Backend and security | FAIL: 846 tests passed, 74 failed; 154 subtests passed |
| Frontend and browser | FAIL: unit tests 272 passed, 1 failed; later production-build/browser steps not executed in this job |
| Native Ubuntu package and exported-archive audit | SKIPPED by required dependencies; no hosted native package produced |
| CI required | FAIL; no bypass |

The frontend failure is `frontend/src/App.test.tsx:409`, “does not steal editor
focus when autosave refreshes the directory titles.” Expected focus was the note
title input; actual focus was the corresponding note tree item. The retained result
does not establish whether this is an application race or a test synchronization
defect. Do not call it flaky or silently retry it.

Fifty-two of the 74 backend/release failure traces explicitly contain the historical
guard at `ci/release/core.py:147`: “Accepted CI workflow changed; policy review
required.” The unchanged accepted Flatpak policy expects CI hash
`3f11c9ab58d2f7c8cebca0b153a09ccffae06e314545067ddd6b42f7b8e809f4`;
the reviewed native workflow is
`94e6a3404f138b615450a9ee409405e0cd15de76f04e3fb4665647ebea62e64d`.
The other 22 failures concern early owner-approval/phase expectations and need
specific triage; their exact cause has not been independently reproduced.
No historical policy/hash or accepted application artifact was altered to suppress
these failures. The future correction should isolate historical-policy fixtures
from the new active CI target while retaining useful tests and security assertions.

The earlier 422 backend application passes did **not** cover the complete
920-case backend/release selection in `ci/verify.py`. This local coverage gap was
missed. The earlier 994 local passes remain valid in their recorded scopes; they
do not override this hosted FAIL or certify the final native package.

Both actual diagnostic ZIPs were retained and independently matched GitHub's API
digests, sizes and exact commit/run provenance:

- Backend artifact `13217735615`, 24,724 bytes, SHA-256
  `ae278d25699d0503db40b2a24bf3c61cb555f9b5d76e00eec68c106b200da5a3`.
- Frontend artifact `13217641247`, 337 bytes, SHA-256
  `c909c2f14827cf3cf4ac720d83d056cdbedf40d4cb2da0f25fba88936be98d26`.

Sanitized evidence: [hosted result](evidence/n4/hosted-41607482461/result.json),
[artifact integrity](evidence/n4/hosted-41607482461/artifact-integrity.json),
[remote readback](evidence/n4/hosted-41607482461/remote-readback.json).
Original job output/downloads remain private under `ci-output/native-n4-push-1/`.
The initial local staging attempt was blocked by a read-only `.git`; explicit
sandbox access was then granted before the single commit. No Git/source defect
was inferred from that permission failure.

**Stopped at the failure checkpoint:** no implementation correction, CI rerun,
second commit or second push. These post-run report/evidence updates remain local
and uncommitted. Proposed next bounded work is to reproduce/correct the focus
failure, make historical release tests hermetic without weakening accepted policy,
and run the full CI-equivalent selection before presenting a corrective batch.
Signing, final native testing, vendor source/notice closure and publication remain
separate; no keys or owner GUI interaction are needed for this investigation.

## Prior local preparation checkpoint — preserved scope

N1–N3 are owner-accepted. Current owner-committed baseline:
`b27e33bb0b31ecd93a3792c6b6a889686dfae575`, branch
`desktop/p2-production-integration`; the working tree was initially clean.
No accepted artifact/source identity is replaced by this new preparation.

Local scope: source-based native assembly; audited package/source/installer artifacts;
exact native CI policy on supported Ubuntu 26.04; focused regressions; original MIT
and branding decisions; native install/manual update/recovery and dependency/source
materials. No Qt/Chromium build, old Flatpak rehearsal or custom hosting.

Protected baselines and resource plan: `ci-output/native-n4-1/baseline.json`.
Maximum local added allocation 3 GiB; keep at least 5 GiB free. Exact existing
wheels were reused without dependency upgrades or repeat wheel downloads. Matching
compressed upstream source/notice materials were acquired within that allocation;
no Qt/Chromium compilation or full source-tree extraction occurred. Operations had
individual time bounds; the 1,800-second build-work estimate is not a claim that the
entire investigation/source-review elapsed time stayed below 30 minutes.

Owner selected MIT with **Copyright (c) 2026 74Cerillion** and confirms ownership of
the CyrNava name/logo. Third-party notices/source correspondence remain separate.
No production key/signature exists for these outputs. No commits/pushes/CI executions,
host policy load, normal installation, signing or publication are authorized.

## What is implemented

- `packaging/native/release.py` assembles current application/frontend source with
  the accepted hash-locked 19-wheel dependency closure. It exports the package,
  source snapshot, installer kit, dependency/ELF/notice inventory and checksums.
  Its independent exported-file audit rejects unreviewed/private paths, duplicate
  ZIP members, tampering, wrong source/provider identities and changed bootstrap.
- `ci/native.py` performs a controlled frontend build in a new output directory,
  package/source audit and real isolated offline installation with installed
  imports/ELF/provider/backend/data checks. Clean source is mandatory in CI;
  explicit local patch preparation records the source commit, tracked diff hash
  and every included source file. It never promotes headless imports to renderer PASS.
- The ordinary CI proposal retains backend/security/browser/lifecycle tests and
  immutable actions/read-only permissions/credential-free checkout. Native package
  assembly replaces the required Flatpak artifact job on Ubuntu 26.04 with full Git
  history, independent prerequisites, fail-closed audit/upload and required-job gates.
  Accepted P5B/P5C release workflows and useful historical tests remain unchanged.
  [Exact workflow contract](native-workflow-contract.json) and mutation tests cover it.
- `policy_setup.py` exports a narrow standalone normal-installation adapter to the
  already accepted policy renderer/root helper. It requires verified installation,
  manifest and policy identities; install never loads policy automatically. Explicit
  owner-host load/remove remains separate. Local prepare/parser checks passed;
  there was no host policy load. Safe errors do not publish raw arguments or paths.
- MIT, approved attribution and name/logo decisions are recorded. Native
  [installation/manual maintenance](../docs/native-installation.md),
  [release notes](../docs/native-release-notes-v0.1.0.md),
  [inventory](../docs/native-dependencies.md) and
  [source obligations](../docs/native-source-obligations.md) are supplied. Public
  fingerprint/download examples deliberately remain parameterized until real trust
  and publication approval exist. No signing identity is invented.

The accepted installation/maintenance engine, application/backend/data/schema code,
renderer predicates and existing built `frontend/dist` are unchanged. The CI lint
scope excludes frozen `ci/evidence` source snapshots while checking live code and
the new N4 modules. A path-specific E501 exception preserves the previously audited
cleanup engine's cosmetic diagnostic. No broad lint/security suppression is added.

## Actual artifacts and source identity

| Material | Exact identity / observed scope |
| --- | --- |
| Committed base | `b27e33bb0b31ecd93a3792c6b6a889686dfae575`, `desktop/p2-production-integration`; initially clean, unchanged HEAD |
| Development package | `ci-output/native-n4-build-1/artifacts/CyrNava-0.1.0-n4.1-ubuntu-x86_64.zip`; SHA-256 `b59a3bd4a3178d704d0dfab736f6e6d546578cf5744a6dcda1264b83e3c9736d`; 271,836,075 bytes |
| Development manifest | SHA-256 `cce75b79af6461783d5d331eeeb93ce92aa3d0d5e6ab1a2827a3abcfdcd5fe88` |
| Actual isolated installation | `ci-output/native-n4-build-1/client/releases/0.1.0-n4.1-b59a3bd4a3178d70`; 4,414 provider files; installed headless checks PASS; GUI/policy load NOT EXECUTED |
| Unsigned public-identity proposal | `ci-output/native-n4-release-proposal-1/CyrNava-0.1.0-ubuntu-x86_64.zip`; SHA-256 `994e526870bd82828a2c2c90c1a71860ea2e1ac828c0e1bfaf7e504261ecf790`; audited, not installed/launched/signed as a public identity |
| Current proposal metadata | `ci-output/native-n4-release-metadata-3/manifest.json`; SHA-256 `db5076086f16c0f2c01f2278f7b3591450b2444f6aaf3c03bbe7185469029967` |
| Current source snapshot | Same metadata directory, `CyrNava-source.zip`; 196 source files; SHA-256 `18b53aeefde74708561339561488c435d85f4527dd223ba6f7e2f0accdc562e6` |
| Current standalone installer | Same directory, `CyrNava-installer.zip`; SHA-256 `9c508116919ff4aedc085b7b9bb29800307a45f7d6ed1b7ba743eb9476df261a` |
| Dependency pins | `dependencies.json`: `621c640f428886a7944b654fe6726f2b3ab82644e4911a051f8281ab392eb8a3`; requirements lock: `24876b72281d5427fc9c5c41cdb19a918815e9547e74c5eb4d2c93ac22e4a576`; matched Qt/PySide/Shiboken/WebEngine 6.11.3, CPython 3.14 |

The latest packet refreshes only source/development configuration and standalone
policy diagnostics; it reuses the immutable public-identity ZIP read-only, without
duplicating or rebuilding it. Original proposal/metadata packets remain intact.
`asset-locations.json` maps the physical files; `SHA256SUMS` is presently **unsigned**.
Source provenance records assembly-time local tracked patch
`27e3f3800252174a73b6783e32bf63f952611afdf30729dafca11043d8744fb3`
and individual included source hashes. Later report/evidence additions are separate;
this is not falsely described as a clean committed/reproducible release.

All 96 accepted N3 runtime files are byte/mode-identical in the N4 development
candidate; it adds three notice/inventory files. The public-identity proposal changes
only generated `application/desktop/native/build_identity.py` relative to that runtime
(application ID/channel/title). N1–N3 GUI/security/data evidence is inherited only for
its exact unchanged inputs; public identity/desktop/trust still needs focused evidence.
See [runtime comparison](evidence/n4/local-2026-11-03/runtime-equivalence.json).

## Executed verification and retained failures

| Local verification | Actual result |
| --- | --- |
| Thin frontend/package/audit/installed checks | PASS, 21.661 seconds; 99 payload files; no Qt source build |
| Native installation/security/maintenance suites | 191 PASS, including 16 new N4 focused tests |
| Native feasibility fixtures | 54 PASS |
| Workflow/security contract tests | 33 PASS |
| Backend/security/data tests | 422 PASS, 2 known warnings; run from documented `backend/` context |
| Frontend unit tests | 273 PASS across 22 files |
| Production Chromium browser tests | 21 PASS; browser evidence, not Qt/AppArmor native evidence |
| Ruff, frontend lint, TypeScript/Vite, workflow validator/actionlint | PASS |
| Exported-auditor negatives | All 5 rejected: private extra, duplicate member, binary tamper, source-provenance tamper, installer tamper |
| Host/native GUI, release signing, hosted CI | NOT EXECUTED in N4 |

Total **994 local tests passed**, without double-counting the 16-test N4 subset.
Six real signing/key-generation fixtures were explicitly not executed under the
current no-signing authorization; they are listed in [test evidence](evidence/n4/local-2026-11-03/tests.json).
No signature claim comes from these fixtures or an unsigned checksum.

Failures remain under `ci-output/native-n4-1/`: initial fixture `/tmp` space refusals,
backend repository-TMPDIR isolation refusal, wrong-cwd backend subprocess imports,
overbroad historical-source lint scope, upload-validator exception and old-linter
runner label handling. Corrected harness/config invocations passed in stated scopes.
No application defect was inferred from those invocation failures. Original failed
logs and XML remain; corrected results do not overwrite them or old P6 disk failures.

## Redistribution materials: collected versus still unresolved

The actual wheel inspection records 19 distributions, 498 ELF files and 18 notice
documents. All four Qt/PySide/Shiboken wheels lack license/notice-named documents;
their declared license metadata alone is insufficient. Their full Addons content
must be mapped to applicable module/third-party terms; unused files were not hidden
or stripped to pass the audit.

Bounded compressed source acquisition completed without compiling/unpacking Qt:

- Qt 6.11.3 source: 1,020,081,224 bytes; SHA-256
  `ad0112f2aef1b94b42a7ab653cebda2f7fc9ba88ef509ec456b17be80b0bfdab`.
- PySide/Shiboken 6.11.3 source: 18,063,176 bytes; SHA-256
  `050819cb05e14d6689f42b56e4fa9c8ff63be2bb339e0c094c45b990b7cabde1`.
- Published sizes/hashes matched exact official Qt release metadata; approved
  HTTPS MirrorBrain redirect was recorded. 2,519 notice documents (11,126,280 bytes)
  were inspected by bounded archive streaming. Sources remain at
  `ci-output/native-n4-source-2/`; the first timed-out 498,597,888-byte partial is
  preserved in `native-n4-source-1/`. One exact HTTP 206 Range continuation succeeded.
- All three BlockNote 0.56.0 source tarballs match lockfile integrity and every
  installed package build-input byte (1,454 files compared). Original 8 MiB map
  inspection refusal is retained; independent bounded 16 MiB inspection passed.

Exact wheel-to-source/build/patch correspondence, shipped-module license selection,
notice completeness and practical recipient replacement/rebuild instructions remain
open. `use-composed-ref@1.4.0` still lacks an authoritative retained attribution notice.
These are specific public redistribution blockers, not an enterprise SBOM requirement.
No complete vulnerability clearance, universal compatibility or license clearance is
claimed. The previously unresolved minimatch advisory is not reclassified.

Smallest vendor clarification, for owner review only (not sent): ask Qt for exact
6.11.3 wheel build source revisions/patches and complete module/Chromium notices;
ask the pinned `use-composed-ref` maintainer for its applicable MIT copyright notice.
The matching compressed sources and actual per-file inventory are already available.

## Supported release boundary and remaining checkpoints

Target: **native Ubuntu 26.04 x86_64 / GNOME Wayland via GitHub Releases**, system
CPython 3.14 and bundled locked Qt 6.11.3 family. Manual full-package updates only;
schema 5 and the accepted identical application/storage/browser consumer family.
No arbitrary future runtime promise, automatic update server, platform expansion or
Flatpak completion requirement is added. N1–N3 and P1–P5/R11/R12 retain acceptance
and their actual artifact scope.

| Remaining essential checkpoint | Current status / smallest next action |
| --- | --- |
| Clean-source hosted native CI | Local implementation/contract/tests PASS. Owner review and separate authorization for one N4 commit and normal integration-branch push; hosted execution then independently checked. No main merge/publication. |
| Vendor notices/corresponding source | Materials collected; resolve the specific Qt/module/attribution issues above before distributing. |
| Final exact public-identity package | Audited unsigned proposal exists. After reviewed committed build/trust selection, focused isolated signed install, GNOME launch/renderer/auth/data/relaunch and supported manual-update check; do not repeat the full historical rehearsal. |
| Authentic release trust | Owner selects an existing full primary fingerprint and separately authorizes exact-asset signing. No private-key search/creation or expired rehearsal key reuse. Verify actual signatures, not just checksums. |
| Publication | Separate owner approval only after above gates; then independently download and authenticate published assets. No release/tag/upload has occurred. |

The actual final-package handoff must bind its package/manifest/installer/source
identities and freshly prepared exact installation-root policy. Old N2/N3 root policy
commands must not be reused. Existing key-protection/replacement procedures and backup/
recovery documentation remain proportionate to a single-maintainer local application.

Protected hashes, actual test/artifact results and evidence sources are preserved in
[local N4 evidence](evidence/n4/local-2026-11-03/preservation.json).
Final measured resource usage and the exact uncommitted review batch are in
`resources.json` and `commit-proposal.json` in that directory. No cleanup was performed;
allocated bytes are not a disk-reclamation claim. No application runtime source,
host security setting, accepted artifact, private profile or signing material was changed.

**Next owner decision:** review this local N4 batch for a separately authorized
integration commit/push and ordinary CI. Signing, final owner-host execution and
publication remain distinct checkpoints. N4 is not recommended for acceptance yet.
