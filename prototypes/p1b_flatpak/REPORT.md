# P1B feasibility assessment — completed host verification

Date: 29 October 2026. Branch: `prototype/p1-pyside6-feasibility`.

**Status: P1B feasibility acceptance PASS on the tested Ubuntu/Wayland/x86_64 host. Architectural approval remains with the owner.** Renderer isolation and private-loopback evidence were independently inspected; native integration and restart results were executed and confirmed by the owner in this conversation. No P2–P6 work, production installer change, personal-data migration, commit, push or publication occurred.

## Evidence from the owner's host recordings

The recordings named `19-06-01`, `19-06-32`, `19-07-13`, `19-07-46` and `19-10-38` on 29 October were inspected at their relevant terminal-result frames. They show:

| Observation | Status / evidence |
| --- | --- |
| Installed tooling | PASS — Flatpak 1.16.6, flatpak-builder 1.4.8, Bubblewrap 0.11.1. |
| Security settings retained | PASS for the displayed settings — namespace enable flag 1, AppArmor namespace restriction flag 1. Ordinary terminal reports `unconfined`; this does not mean AppArmor was disabled system-wide. No claim is made about settings not shown. |
| Bubblewrap private loopback | PASS — the provided isolated user/PID/network namespace test printed `Private loopback PASS`. |
| Runtime references available | PASS — KDE Platform/SDK and PySide/WebEngine BaseApps are available on x86_64, branch 6.11. |
| SDK installation | PASS — final recording shows completed installation. The displayed SDK download/installed figures are SDK costs, not CyrNava package size. |
| Actual SDK Flatpak private loopback | PASS — explicit `--unshare=network --nofilesystem=host --nofilesystem=home`; host namespace `net:[4026531833]`, sandbox namespace `net:[4026533168]`; output `Flatpak private loopback PASS`. This is a Python socket probe, not a Qt/FastAPI application test. |

The journal denials visible in the 19:06 recording are timestamped 18:57 and match the earlier agent probes. They do not contradict the later successful host test. A fresh agent-side Bubblewrap probe still fails; installing host tooling did not remove this session's AppArmor confinement. Host success therefore clears the machine prerequisite while actual namespace-dependent build/run work must use the normal terminal.

Cached ref commits were independently read after the recordings:

| Ref (all x86_64/6.11) | Commit |
| --- | --- |
| org.kde.Platform | `76fa01ac42ecf45d2c5020ef80de1c474c0c2ae86a51a79e8fec44c48f9dc473` |
| org.kde.Sdk | `df314f9c067cba031e153a2f3b0be53bd13c1eca6baa78b68982a1d35b873a86` |
| io.qt.PySide.BaseApp | `a6cddcbcf58032e3f22c66a98779cc07685d376e52718e5aee307ad9aeb1bb8e` |
| io.qt.qtwebengine.BaseApp | `7e78be2bcc31ed2bb9324cb97cc49dde27c57749c94086702ce81d312b328952` |

These identify the observed preflight refs. The host build records the commits it actually uses, which may differ if installed branches change. No shared runtime was downgraded or pinned by modifying another application's installation.

## Actual host application run

The owner subsequently built and launched the real test application successfully. Its saved build evidence, shutdown metrics and backend log were independently read; only these synthetic diagnostics were retained, not the database or documents. The installed app commit is `de98d04b66fe89d4865afdaabbfc6ef1d9706cf92f526270ba45279404a975c9`. Its recorded desktop source SHA-256, `6ac40f0f1dd9ab6bf4161ace0d2974e37135c8f33d4cdba6ee9d9ea5c7e1d2f7`, matches the reviewed source. Runtime/SDK/PySide BaseApp commits match the preflight table.

Actual component versions are **PySide 6.11.2, Qt 6.11.2, WebEngine 6.11.1, Chromium 140.0.7339.225**, on Wayland. These deployed binary versions take precedence over the earlier inference from upstream source manifests. The 6.11-family guard passed; homogeneous patch versions are not established. Version/provenance and security-update review remain required before a production decision.

Chromium's actual diagnostic reports:

```text
Layer 1 Sandbox: Flatpak
PID namespaces: Yes
Network namespaces: Yes
Seccomp-BPF sandbox: Yes
Seccomp-BPF sandbox supports TSYNC: Yes
You are adequately sandboxed.
```

Process observations corroborate additional isolation, rather than relying only on an enabled flag. The GUI uses PID namespace `4026532708` and network namespace `4026532710`. Nested WebEngine processes use PID namespace `4026533555`, network namespace `4026533327`, and a separate mount namespace. Two nested processes report two seccomp filters versus the GUI's one; all captured processes report `NoNewPrivs=1`. The raw snapshot identifies them as WebEngine processes, not their full renderer command-line roles; host-side role correlation remains supplementary evidence to collect.

The app reports no remote-debugging port, only the `lo` network interface, and successful private backend readiness followed by frontend load from `http://127.0.0.1:36131`. The owner's terminal screenshot includes the live `127.0.0.1:36131` listener; the final shutdown snapshot has no TCP listener. Its effective Flatpak context contains no host-network sharing and no broad home/host filesystem grant. Subsequent owner-run note editing, uploads and recovery also succeeded through that application architecture, as recorded below.

The effective runtime inherits a narrow read-only `xdg-config/kdeglobals` grant and three named KDE/AppMenu D-Bus permissions. These are not broad home/general bus access, but their necessity should be reviewed before claiming a minimal production permission set.

Internal timings: backend ready **853.82 ms**, frontend load **944.17 ms**, owned-backend stop/reap **213.9 ms**. The startup timer excludes QApplication construction; these are one-run observations, not cold-start benchmarks. Flatpak reports the main application ref at **737,895,424 bytes (about 703.7 MiB)**. The installed Locale extension reports **309,432,320 bytes**, and Debug reports **1,213,952 bytes**: the three logical sizes total **1,048,541,696 bytes (about 1,000 MiB)**. Shared runtime/SDK costs are separate. These figures are not incremental disk usage, deduplication-adjusted storage or a measured download bundle size. Memory was not measured for this Flatpak run.

FastAPI logs show startup, graceful shutdown, completed application shutdown and process finish. The retained child exit code is `-15` after SIGTERM, as expected for this Uvicorn path. Missing `/proc/10/status` in the final snapshot is expected after reaping; it is not evidence of a crash.

**Full application cleanup subsequently passed the host checks.** Agent-side `flatpak ps` initially listed instances `852976018` and `891127750` after window closure. The owner then ran the inspector in the regular host terminal: no matching processes were found, with zero unreadable processes reported. A separately executed host `flatpak ps` returned no output. No force termination or cleanup code change was needed. The initial enumeration discrepancy was not root-caused; it must not be described as a fixed process leak or a measured shutdown delay. End-state cleanup is verified, while exact full-container shutdown latency remains unmeasured.

## Owner-executed native acceptance sequence

These are manual host results explicitly confirmed in this conversation, not automated runs performed by the agent. The compact transcript-derived record is retained in `evidence/owner-native-results.json`; no personal notes or downloaded document contents were copied into the repository.

1. Created a synthetic note with a heading and bold text, waited for Saved, closed/relaunched, and confirmed formatting remained.
2. Pasted a screenshot of a synthetic region with Ctrl+V, waited for Saved, closed/relaunched, and confirmed the image remained visible.
3. Used `/image` → Image → Upload image and the real native file chooser to select a synthetic PNG; waited for Saved and confirmed the image survived restart.
4. Changed Appearance and hid navigation; confirmed both settings were restored on relaunch.
5. Used the native Stop test backend action, changed the title to `P1B recovery check`, waited for Save Error, explicitly closed the prototype and relaunched. Confirmed the recovery prompt appeared.
6. Ran the scoped FileChooser D-Bus monitor in a second host terminal, clicked Download draft, used the Save dialog and inspected the JSON title. Confirmed successful file save, the expected title and `member=SaveFile` in the monitor. This is owner-reported portal observation; a raw D-Bus trace was not attached.
7. Explicitly recovered the draft, waited for Saved, checked the title/formatted content/images, closed/relaunched and confirmed everything remained saved.

The FileChooser OpenFile method was not separately traced during upload; native chooser behavior itself passed. The tested rich-text sample covers heading/bold content, not an exhaustive editor-command matrix. These limits do not convert unexecuted cases into passes.

## Prepared configuration and architectural changes

The disposable app ID is **org.cyrnava.P1B**, branch **p1b**, using KDE 6.11 and the PySide 6.11 BaseApp. It has Wayland and rendering-device access, explicitly unshares networking and denies broad home/host filesystem grants. It has no external-browser dependency, Node runtime, Vite server, remote-debugging port, general session-bus grant, native JavaScript bridge or sandbox-disabling flag. Native Open/Save uses the platform's portal integration rather than granting broad filesystem access.

The P1 prototype remains the shell. P1B-only initialization verifies its Flatpak identity and packaged source location, rejects effective host-network/broad filesystem grants, and sets a stable marked workspace inside that application's private data directory. SQLite/assets remain managed by the existing backend. Existing React/BlockNote/API/security implementations and the production installer are unchanged.

The GUI still owns the retained FastAPI child, prebound private-loopback socket, nonce readiness probe and parent-death pipe. Normal/failed-save closure and bounded child termination remain. Native P1B buttons provide fixed diagnostic export and a confirmed stop of only the owned synthetic backend. No arbitrary command is accepted from web content.

The prototype's old blanket download cancellation is retained for ordinary P1. P1B accepts only blob exports from its own page, asks for a destination using native QFileDialog and passes the selected destination to Qt's download request. The owner subsequently confirmed SaveFile portal observation, successful export and the expected JSON title; this result comes from the manual host test, not code presence alone.

The BaseApp's specific `/app/bin/QtWebEngineProcess` helper is allowed only in verified P1B mode and only if it resolves to its expected packaged executable. Other inherited WebEngine overrides remain refused. The GUI and isolated `-I` worker explicitly add only the read-only `/app/lib/pythonX.Y/site-packages` prefix, so backend modules do not depend on an ignored `PYTHONPATH` environment variable.

P1's pip Qt pins were 6.11.3. P1B deliberately uses the upstream 6.11 BaseApp family instead; observed PySide/WebEngine BaseApp sources are 6.11.2 with Flatpak renderer-support patches. It does not layer standalone Qt wheels over those libraries. This is an explained prototype dependency deviation, not a security-update policy. The SDK uses Python 3.13 rather than P1's Python 3.12; all existing pinned backend requirements have matching wheels fetched for that ABI. Build assertions reject a different Python ABI or Qt minor family; actual component versions are recorded at runtime. [PySide source manifest](https://raw.githubusercontent.com/flathub/io.qt.PySide.BaseApp/branch/6.11/io.qt.PySide.BaseApp.yaml), [WebEngine source manifest](https://raw.githubusercontent.com/flathub/io.qt.qtwebengine.BaseApp/branch/6.11/io.qt.qtwebengine.BaseApp.json).

Existing backend development requirements are included without trimming for this feasibility run. No new testing framework or production Python/npm dependency was added. Source/wheel hashes and installed ref commits are recorded after a successful local build. This is not a production reproducible-build lock or a dependency vulnerability/license audit. App-private XDG locations and native portals follow Flatpak's documented boundaries. [Sandbox and portals](https://docs.flatpak.org/en/latest/sandbox-permissions.html), [runtime XDG behavior](https://docs.flatpak.org/en/latest/flatpak-command-reference.html).

## Files created or modified

| File | Change / responsibility |
| --- | --- |
| `prototypes/p1_desktop/desktop.py` | Modified only the existing feasibility shell: verified opt-in Flatpak mode, app-private stable workspace, trusted module/helper paths, native blob export, fixed native test controls, component/process/network diagnostics. Ordinary P1 behavior retains temporary profiles and cancelled downloads. |
| `prototypes/p1b_flatpak/prepare.py` | New stdlib source snapshot/manifest generator and explicit host-only `--build` workflow. Fetches pinned ABI-specific wheels, builds/installs only the test ID, records inputs/commits/permissions/size. Uses existing frontend assets and backend source. |
| `prototypes/p1b_flatpak/test_prepare.py` | New pytest safety tests for manifest permissions, snapshot exclusion/symlinks/database files, Flatpak identity, effective unsafe permissions, stable synthetic workspace and evidence failure reporting. |
| `prototypes/p1b_flatpak/inspect_host.py` | New read-only host-side process evidence collector, restricted to the test app's verified identity; no signals or note reads. |
| `prototypes/p1b_flatpak/README.md` | Host build/run instructions, security gate, native tests, portal observations and evidence return procedure. |
| `prototypes/p1b_flatpak/REPORT.md` | Completed assessment, evidence distinctions, acceptance matrix and adoption recommendation. |
| `prototypes/p1b_flatpak/evidence/host-build.json` | Retained actual host build inputs, ref commits, effective permissions and installed size. |
| `prototypes/p1b_flatpak/evidence/host-shutdown.json` | Retained actual component/sandbox/process/network/timing observations from normal shutdown. |
| `prototypes/p1b_flatpak/evidence/host-backend.txt` | Synthetic backend startup and completed graceful-shutdown evidence. |
| `prototypes/p1b_flatpak/evidence/host-sizes.json` | Observed logical sizes of the installed main, Locale and Debug refs; no deduplication/download-size claim. |
| `prototypes/p1b_flatpak/evidence/owner-native-results.json` | Transcript-derived owner-confirmed manual outcomes, including cleanup and portal SaveFile; not a raw automated test log. |

Generated manifests, downloaded wheels and staging snapshots stay under `/tmp/cyrnava-p1b/`. Runtime synthetic data stays below `~/.var/app/org.cyrnava.P1B/`. Neither is committed to the repository. Original P1 evidence files remain historical evidence; they were not replaced with P1B claims.

## Executed checks and limitations

| Check | Result |
| --- | --- |
| Existing P1 safety/backend tests plus P1B unit tests | PASS — **34 passed**, final run 0.65 seconds. Initial run had 32 passes and two socket-permission failures; the session's tool network grant enabled the same loopback tests to pass. Host security settings were not changed. |
| Ruff check / format check | PASS — prototype checks passed; no production formatting changes. A first formatter invocation attempted a read-only cache; `--no-cache` corrected the invocation. |
| Source-only staging | PASS — explicit snapshot created outside the repository. No application Flatpak was installed by this step. |
| Backend wheels for SDK ABI | PASS — all 24 existing pinned requirements downloaded as compatible Python 3.13/x86_64 wheels. No Qt wheel replacement. |
| flatpak-builder manifest parser | PASS — `--show-manifest` accepted the generated manifest and its permissions. An initial parser command used an unsupported option combination; the corrected manifest-only invocation succeeded. This is not a package build. |
| Agent-side namespace probe | FAIL — Bubblewrap still denied namespace creation. No policy/security workaround attempted. |
| Standalone P1 Qt regression run | FAIL at screenshot paste — three earlier journeys passed, then the image count remained zero. Logs show Wayland focus warnings; focus/compositor restrictions are a suspected cause, not a proven diagnosis. The owned backend shut down and was reaped. No complete new GUI regression pass is claimed. |
| Owner's actual Flatpak build/install | PASS — installed commit and input hashes retained in `evidence/host-build.json`. |
| Actual Flatpak startup and sandbox | PASS for startup and observed renderer isolation — readiness, frontend load, Chromium diagnostic and nested namespace/seccomp evidence retained. |
| Actual owned backend shutdown | PASS — log/retained child status and empty final TCP listeners agree. Subsequent host process inspection and empty Flatpak listing confirmed end-state cleanup. |
| Owner-run Flatpak native acceptance sequence | PASS — rich text, clipboard screenshot, native chooser/upload, portal export, preferences, recovery, persistence and restart explicitly confirmed in conversation. |

The native run above used standalone P1 wheels and the agent environment, not the proposed Flatpak. Its result reinforces the need for actual focused native input on the host; no CDP clipboard substitute is used for P1B acceptance.

## P1B acceptance matrix

| Criterion | Status | Evidence / scope |
| --- | --- | --- |
| Host tooling and namespace preflight | PASS | Owner recordings plus local installed metadata. |
| SDK Flatpak private loopback | PASS | Owner recording, distinct host/sandbox namespaces. |
| Disposable application build/install | PASS | Actual installed app commit, input hashes and owner-run success. |
| Effective Qt renderer sandbox | PASS | Actual adequate Chromium report and corroborating nested PID/network/mount namespaces, seccomp and NoNewPrivs. Live host command-line role correlation was not separately captured. |
| Qt shell ↔ FastAPI private communication | PASS | Private readiness/frontend delivery plus successful owner-run editing, upload, recovery and persistence. |
| No host-network sharing / external backend | PASS for observed configuration | No network sharing; only lo; observed listener 127.0.0.1:36131; private app network namespace differs from the recorded host namespace. |
| Rich-text editing | PASS — owner-run | Heading and bold formatting remained after Saved/close/relaunch. |
| Screenshot clipboard paste | PASS — owner-run | Real Ctrl+V screenshot input; image remained after restart. |
| Native chooser | PASS — owner-run | Real file chooser used to select a synthetic PNG. OpenFile D-Bus trace not separately captured. |
| Image upload | PASS — owner-run | Selected synthetic PNG rendered, saved and survived restart. |
| Portal export/download | PASS — owner-run | Successful JSON save, expected title and SaveFile monitor observation confirmed. |
| SQLite persistence | PASS — owner-run | Saved content/images survived full close/relaunch; existing backend uses the explicit synthetic SQLite path. |
| Persistent Qt preferences | PASS — owner-run | Appearance and hidden navigation restored. |
| Recovery draft | PASS — owner-run | Controlled outage, offline title edit, explicit close, recovery prompt, SaveFile export, explicit recover/save/restart. |
| Backend termination | PASS | Owned FastAPI child reaped, graceful log, no final listener. |
| Full Qt/Flatpak cleanup | PASS — owner-run | Host inspector found no matching processes; subsequent host Flatpak listing was empty. Exact cleanup latency not measured. |
| Application restart | PASS — owner-run | Multiple restarts retained saved/recovered formatting, images and preferences. |
| Actual application size | PASS — measurement collected | Main ref 737,895,424 bytes; main/Locale/Debug logical total 1,048,541,696 bytes. Shared runtime, SDK, deduplication and download sizes are separate. |

Namespace-dependent execution remains BLOCKED **inside the agent session**; the actual build and manual native tests were executed on the owner's ordinary host. All required P1B feasibility criteria pass for that configuration. Supplemental behavior remains NOT TESTED: X11/other distributions/architectures, exhaustive editor commands and large data sets, power loss, live renderer command-line role correlation, a separate OpenFile portal trace, Flatpak memory usage, compressed bundle/download size and full-container shutdown latency. The standalone P1 automation failure remains recorded and is not relabeled as a passing automated run.

## Risks and recommendation

The existing general API remains unauthenticated. Private loopback reduces the host-network surface but does not establish protection from a malicious same-user host process or a compromised in-app renderer. The prototype remains synthetic-data-only. Neither Flatpak membership nor a seccomp field alone proves the inner renderer boundary; this run provides corroborating Chromium and namespace evidence. SaveFile portal operation and end-state cleanup now have explicit owner confirmation. Actual deployed WebEngine/Chromium version provenance and maintenance, dependency vulnerability review, licensing, permission trimming and production flush semantics remain release/integration review items, not completed remediation. The approximately 1,000 MiB logical app/Locale/Debug size is also an optimization and distribution tradeoff; no production trimming was attempted.

**Recommend adopting PySide6 + Qt WebEngine as the desktop architecture for the next explicitly approved integration stage.** The two P1 feasibility gates and required native workflows passed on the tested host. This is an architecture feasibility recommendation, not a claim that the prototype is production-secure or ready for public distribution. No security policy was relaxed to obtain these results. P1B is complete for review; stop here and await the owner's architectural approval. P2–P6 have not begun.
