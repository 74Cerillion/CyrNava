# P6 Qt/PySide compatibility assessment and implementation proposal

2 November 2026. **ASSESSMENT COMPLETE; PRODUCTION REMEDY NOT IMPLEMENTED.**
P6 remains CONDITIONAL. The authorization explicitly permits an assessment and
concrete proposal when available evidence does not support a safe implementation.
That stop condition applies: an ordinary-runtime-safe, Flatpak-sandbox-compatible
replacement stack has not been established. No manifest, lock, application code,
launcher, sandbox permission, signing rule or accepted artifact changed here.

## Confirmed cause and exact compatibility boundary

The accepted A/B payload inherits PySide6/shiboken6 **6.11.2** from
`io.qt.PySide.BaseApp//6.11`. They are absent from CyrNava's backend wheel lock;
the BaseApp commit is their effective binary lock. Its Python metadata requires
Python >=3.10,<3.15 and cp310-abi3; these particular BaseApp wheels have the
manylinux_2_42_x86_64 tag. CyrNava explicitly builds for runtime Python **3.13**.
Python's stable ABI does not make Qt's C++ private ABI stable.

| Component | Actual provider | Accepted historical build | Updated runtime observation |
| --- | --- | --- | --- |
| Python / libpython | `/usr`, KDE runtime | 3.13 ABI | 3.13 ABI |
| PySide/shiboken extension/libraries | `/app/lib/python3.13/site-packages` | 6.11.2 | unchanged 6.11.2 |
| Qt Core/Gui/Widgets/Network/Quick/Positioning/WebChannel | `/usr/lib/x86_64-linux-gnu` | 6.11.2 | 6.11.3 |
| Qt WebEngine/PDF/WebView | `/app/lib/x86_64-linux-gnu` | 6.11.1 | unchanged 6.11.1 |
| Qt platform plugins | runtime `/usr` | runtime Qt | runtime Qt |
| QtWebEngineProcess/resources/dictionaries | application BaseApp payload | application build | unchanged application build |

The binding has DT_RPATH
`$ORIGIN/:/usr/lib/x86_64-linux-gnu:$ORIGIN/../shiboken6/` and no app-owned
QtCore. Its undefined symbol is:
`_ZN14QObjectPrivateC2E16QtPrivate_6_11_2@Qt_6_PRIVATE_API`.
The historical QtCore exports it. Updated QtCore exports the equivalent
`QtPrivate_6_11_3` constructor and lacks the required 6.11.2 symbol. Both advertise
SONAME `libQt6Core.so.6`; the SONAME/major/minor match therefore cannot certify this
pair. This static result independently agrees with R4's retained ImportError.
No new load of the accepted binaries was attempted.

The dependency originates upstream: PySide's
[QIOPipe implementation](https://github.com/pyside/pyside-setup/blob/v6.11.2/sources/pyside6/PySide6/QtCore/glue/qiopipe.cpp#L38)
subclasses QObjectPrivate; its constructor calls that private base constructor.
[Qt's private header](https://github.com/qt/qtbase/blob/v6.11.2/src/corelib/kernel/qobject_p.h#L38)
forms the version enum from major, minor **and patch**, uses that enum as the
constructor parameter, and explicitly excludes this header from the stable API.
This is an intentional private-ABI guard, not an exception to suppress or a
symbol to alias. Qt's [public compatibility guidance](https://doc.qt.io/qt-6/qt-releases.html)
does not remove that private-header limitation.

WebEngine also depends on runtime Qt modules. The accepted WebEngine has no
DT_RPATH/RUNPATH; it needs ICU77, NSS/NSPR, GL/GBM, Wayland/X11 support libraries,
DBus/GLib, codecs, image/font/XML and compression libraries in addition to Qt.
The provider's build configuration, symbol versions and native dependency closure
matter as well as advertised version numbers. A differing WebEngine patch number
alone is not proof of this observed error: the proven failure is QtCore's missing
private constructor. Existing historical execution is preserved as evidence of
that particular installed stack, not universal mixed-version compatibility.

## Upstream packaging investigation

The inspected [PySide BaseApp recipe](https://github.com/flathub/io.qt.PySide.BaseApp/blob/732cd70984eab55693b55062026bd289ef98d974/io.qt.PySide.BaseApp.yaml)
uses KDE 6.11 and builds PySide v6.11.2 commit
`24627cd36e1593adf22eb1f2950e4248e7bcc1ec` with `/usr/bin/qtpaths` and `--flatpak`.
It layers the WebEngine BaseApp. Its separate
[WebEngine recipe](https://github.com/flathub/io.qt.qtwebengine.BaseApp/blob/1f4a783f05d97ecb7a887096c2cd933406c727f8/io.qt.qtwebengine.BaseApp.json)
currently names v6.11.2 source and Flatpak-specific patches. That recipe is distinct
from the accepted binary's measured 6.11.1 WebEngine. Branch names are not binary
version evidence. Raw recipe/source hashes and immutable revisions are recorded
in `ci/evidence/p6/production-qt-compatibility/upstream-source-records.json`.

**Correction to earlier documentation:** the inspected BaseApp README merely
states its packaging purpose. It does not promise coordinated patch updates or
say that consumers must track KDE patch releases. The earlier attribution of that
requirement to its README was unsupported. The version coupling here is established
by source/ELF evidence. The previous wording remains archived in prior-review.
No upstream update policy that atomically updates already-bundled bindings with a
separate runtime was established. Flatpak [documents BaseApps as copied bundled
dependencies](https://docs.flatpak.org/en/latest/dependencies.html#baseapps).

## Alternatives and decision

| Option | Correctness and ordinary runtime updates | Maintenance, provenance, security, size and licensing | Decision |
| --- | --- | --- | --- |
| A. Existing upstream KDE/PySide/WebEngine stack, rebuilt together | Can match a snapshot. Independent later KDE Qt patch still changes private ABI beneath immutable app bindings. | Least build work and sharing; immutable refs aid reproducibility. Current inherited stack is already proven incompatible. No atomic compatibility guarantee established. Existing licensing work remains. | Reject as a complete production remedy. |
| B. Rebuild only PySide/shiboken against current KDE | Removes this missing-symbol error for the chosen snapshot; next runtime patch remains the same exposure. | Bindings build/toolchain provenance and coordinated release burden increase, but does not solve delivery coupling. Small app size delta; no licensing simplification. | Useful diagnostic, insufficient remedy. |
| C. Complete app-owned coherent Qt + PySide/shiboken + WebEngine | Removes dependency on runtime-owned Qt private ABI if **all** Qt modules/plugins/helper use that closure. Runtime OS ABI/security compatibility must still be tested. | More app bytes and maintainer responsibility for Qt/Chromium updates, complete source/patch hashes, notices and licensing review. No custom runtime needed. Secure Flatpak renderer support is mandatory. | Recommended architecture, pending bounded build feasibility and native validation. |
| D. Another maintained BaseApp/runtime/extension | A different name alone does not fix ownership. A maintained whole-stack app-local BaseApp could implement C. A separately updated extension could reproduce the split. | Prefer upstream reuse where proven; avoid a custom runtime. No examined ready-to-use stack established both whole-stack ownership and preserved Flatpak renderer behavior. | No verified drop-in replacement identified. |

Flatpak's [Qt guidance](https://docs.flatpak.org/en/latest/qt.html#contents)
explicitly supports bundling needed Qt components on Freedesktop Platform; this is
a supported dependency strategy, not proof that a particular proposed build works.
Keep the existing KDE 6.11/Python 3.13 base for an initial disposable feasibility
build to limit variables. Evaluate Freedesktop only after independently verifying
its exact Python/native ABI and support lifetime; no new runtime branch is selected
by this assessment. No indefinite historical runtime pin is proposed.

Long-term maintenance: Qt's [published support table](https://doc.qt.io/qt-6/qt-releases.html#supported-versions)
lists 6.11.3 with standard support until **17 March 2027** and identifies 6.12 as
the newer LTS line. Extended LTS patch access is generally commercial, with
WebEngine treated differently. A 6.11.3 feasibility snapshot is therefore not a
long-term version freeze; record a supported upgrade/security-update plan before
release. Do not infer free access to every LTS patch or change all components to
6.12 without a new coherent build and licensing/compatibility review.

## Official wheel experiment and why it is not installed in production

Downloaded the four official PyPI **6.11.3** x86_64 cp310-abi3-manylinux_2_34 wheels
(PySide6, Essentials, Addons, shiboken6), requiring the exact metadata versions,
file sizes and SHA-256 values in `packages.json`. No package was installed in the
host interpreter or accepted Flatpak; the wheels were unpacked in a disposable
tree. Unlike the BaseApp build, the upstream standalone wheels bundle Qt under
`PySide6/Qt/lib`, consistent with [Qt's package documentation](https://doc.qt.io/qtforpython-6/package_details.html).

Measured totals: **256,444,791 compressed bytes**, **680,754,077 uncompressed
file bytes**, **3,892 ZIP entries**, before any application integration or pruning.
These are wheel measurements, not a Flatpak bundle-size estimate or net size delta.
Their QtCore needs bundled ICU73 (the historical BaseApp uses runtime ICU77).
The wheel contains its ICU73 libraries; the whole native closure must be retained
and audited. It also contains Wayland and xdgdesktopportal plugins, matching
WebEngineProcess, resources and locales. Plugin presence does not prove portal or
Wayland behavior. Binding RPATH uses `$ORIGIN/Qt/lib`; bundled Qt libraries use
`$ORIGIN` RUNPATH and the helper uses its adjacent Qt lib directory.

Four host imports (QtCore, QtWidgets, QtWebEngineCore, QtWebEngineWidgets) and a
QCoreApplication succeeded under **Python 3.14.4 / glibc 2.43**, with all loaded Qt
libraries observed inside the disposable wheel tree. This is host import-only
execution, **not** Python 3.13 Flatpak validation, GUI startup or renderer testing.
No LD_LIBRARY_PATH or Qt library override was used. Four static private-symbol
comparisons also behaved as expected: accepted/historical match; accepted/updated
mismatch; new wheel/own Qt match; new wheel/historical Qt mismatch.

Crucially, the accepted WebEngine includes the maintained BaseApp
[Flatpak Chromium sandbox patch](https://github.com/flathub/io.qt.qtwebengine.BaseApp/blob/1f4a783f05d97ecb7a887096c2cd933406c727f8/patches/chromium-flatpak-add-initial-sandbox-support.patch).
It implements Flatpak portal-based child sandboxing. The accepted binary contains
its Flatpak source/portal/diagnostic markers; the inspected official wheel lacks
all three. Absence of markers is not a complete proof that the wheel cannot work,
but it is insufficient evidence to replace the verified renderer arrangement.
Import success cannot answer that security question. A wheel swap would also need
audited helper/resource paths and plugin configuration changes. **Do not deploy
this experiment or weaken sandbox checks to make it launch.**

## Concrete implementation proposal — next review scope

1. Build a separate disposable source-based app-owned closure, initially Qt/PySide/
   shiboken **6.11.3**, retaining Python 3.13, identity/version/schema and finish-args.
   Pin every source archive/commit, SDK commit, build tool and downstream patch in
   a new candidate lock. Preserve the accepted manifest/lock as historical inputs.
   Verify availability/source correspondence before finalizing any candidate lock.
2. Reuse maintained WebEngine BaseApp sandbox/path patches against the matching
   source, recording whether they apply unchanged. A conflict, removed integration
   or unsupported compiler combination stops the build for review. Build all used
   Qt libraries, Qt platform/theme/image/TLS plugins and WebEngine/helper/resources
   against this same app-owned Qt, rather than reusing runtime Qt plugins.
3. Install into a distinct app-owned Qt prefix and build native origin-relative
   loader paths. Do not overwrite `/usr`, interpose symbols, set LD_LIBRARY_PATH,
   copy an old runtime or disable dependency resolution. Explicitly constrain plugin
   discovery and verify actual loaded providers. Keep portal support and renderer
   isolation. Treat this closure/search-path design as reviewable before adoption.
4. Candidate files: a separate manifest and source/patch lock beneath
   `packaging/flatpak/compatibility/`; a disposable build entry point; additional
   provider/private-symbol audit checks; candidate-only import and normal-launcher
   checks. Only integrate with production build.py/install_payload.py/launcher
   after that candidate passes. Preserve existing package auditor in full; add
   mixed-provider, missing-symbol, missing-plugin/helper and wrong-source negatives.
5. Measure peak build memory, required disk, build time and output size before
   declaring this maintainable. Current free root disk was about 3.6 GiB and
   disposable /tmp about 4.3 GiB before wheel extraction, insufficient evidence of
   capacity for a Chromium source build. No build was attempted or blocked result
   invented. A reviewed temporary build volume may be required; no paid hosting.
6. If the complete source build is disproportionate, pause with measurements and
   investigate upstream inclusion/support of the missing Flatpak integration in
   standalone wheels. Do not maintain an unreviewed binary patch or stripped-down
   sandbox substitute. No issue/contact was sent externally.

This is an implementation proposal, **not a completed correction**. No production
dependency/version change is made now. The 6.11.3 wheel hashes lock only this local
experiment, not a new release candidate. No speculative future compatibility claim.

## Verification and required native gate

Recorded clean-checkout regressions: **382 release/workflow tests + 229 subtests**,
**158 backend/security/storage/lifecycle/packaging tests**, and **273 frontend unit
tests PASS**. Dependencies were reused, source came from a fresh detached clone
with exact overlay hashes, frontend/dist was copied only as a backend-test
prerequisite. The first backend invocation used the wrong working directory:
157 passed/1 failed (CLI could not import app). The unchanged suite passed from
backend/. Both logs are retained, with local paths redacted. No tests were skipped
or weakened. New production behavior/regression tests are not claimed: no production
correction exists. Four empirical ELF assertions are separate from pytest counts.
The evidence reproducer passes Ruff/check/format; no application lint changed.

| Check | Actual result |
| --- | --- |
| R12 historical targeted B, two GUI launches | Owner-executed PASS, independently reread; original source/import/reinstall data preserved |
| Accepted binding against updated runtime Qt | Static incompatible; R4 native ImportError retained |
| New official wheel imports/Qt providers | Host import-only PASS; no GUI/renderer |
| New coherent Flatpak package build/content audit | NOT EXECUTED; no approved safe candidate yet |
| Flatpak Python 3.13 imports / normal packaged launcher / portals / renderer | NOT EXECUTED for a replacement stack |
| Ordinary dependency update with unchanged replacement app | NOT EXECUTED; central gate OPEN |
| Browser integration suite | NOT REPEATED; application/frontend/browser source unchanged in this assessment |

No exact native candidate execution command is issued: there is no verified
candidate package to name. Reusing real_update.py's historical runtime procedure
would test the wrong property. Before requesting native execution, implement and
review a candidate-only supervisor with exact package/source hashes and **two
upstream-signed runtime commits** from ordinary update history on the same supported
branch. It must create a new isolated client, install the older supported runtime
normally, install the immutable candidate with dependency resolution, confirm the
actual starting runtime, then perform ordinary `flatpak update` with signatures
enabled. If dependency resolution already installs the newer runtime, report that
the two-state update test was not exercised; do not roll it back to manufacture a
PASS. A genuinely distinct before/after runtime must be observed.

Before/after: bounded module imports and actual loaded provider paths/hashes; normal
packaged launcher, Wayland/portal functionality, renderer sandbox, authenticated
backend/loopback/origin checks, synthetic notes/images/autosave/recovery and process
cleanup. Hash the app bytes unchanged across runtime update. Reject mixed Qt
providers. Follow with real application update/rollback and schema-safe data checks
when a second candidate is separately approved. Use fresh disposable data only.
Do not repeat R12 or touch personal/normal Flatpak data. A successful finite pair
cannot guarantee arbitrary future ABI changes; track upstream support and security
updates continuously. Owner approval of exact native commands is still required.

A reproducible **static-only** command for the current evidence, after recreating
the hash-verified wheel tree, is:

```bash
cd /home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
python3 ci/evidence/p6/production-qt-compatibility/inspect_elf.py \
  --wheel-site /tmp/cyrnava-qt-assessment-z5k48vq1/site \
  --output /tmp/cyrnava-qt-static-readback.json
```

This performs readelf only, rejects an existing output, and relies on retained
R4/R12 exact deployments. It does not install, launch, sign or update anything.
The disposable wheel path is specific to this assessment, not a permanent owner
handoff. No owner execution is requested now.

## Files changed in this assessment

- New: `ci/P6_QT_COMPATIBILITY.md` and
  `ci/evidence/p6/production-qt-compatibility/` (safe JSON, sanitized logs,
  read-only ELF reproducer and archived prior documentation).
- Updated: `ci/P6_REPORT.md`, `ci/P6_OWNER_CHECKS.md`,
  `ci/P6_RELEASE_RUNBOOK.md`, `ci/P6_RUNTIME_REMEDIATION.md`,
  `ci/P6_LICENSE_REVIEW.md`, `ci/P6_TARGETED_B_CHECKS.md` and
  `packaging/flatpak/production/README.md`.
- Refreshed current review indices: `ci/evidence/p6/proposed-files.json` and
  `ci/evidence/p6/SHA256SUMS.json`. Archived indices remain unchanged.
- No production or P6 driver implementation changed. The only executable new file
  is a static evidence reproducer excluded from the production payload by the
  existing source allowlist/package auditor. No new CI workflow or entry point.

## Security, licensing and next authorization

All accepted source/artifact hashes, signing/source eligibility, package auditing,
permissions and application storage remain unchanged. R9/R11 remain FAIL historical
records; R9's exact missing filesystem object remains unresolved. R12 closes the
historical post-import/reinstall observation only. No GUI/preparation/build/GitHub
execution, key generation, commit, push, publication or normal host installation
change occurred in this assessment.

App-local Qt moves security-update responsibility and corresponding-source/notices
obligations into CyrNava's shipped closure. Review each selected module/plugin's
actual license (not all Qt modules have identical terms), LGPL replacement/relinking
requirements, Chromium and bundled ICU/other third-party coverage, source/patch
availability and codec choices. Qt's [WebEngine licensing guidance](https://doc.qt.io/qt-6.11/qtwebengine-licensing.html)
requires both Qt and Chromium obligations. Current inventory is not a complete
SBOM or redistribution clearance. Original-code/logo rights and other existing
publication blockers remain independent. See P6_LICENSE_REVIEW.md.

**Next owner decision:** review the complete app-owned, source-built Qt closure
proposal and authorize its bounded disposable feasibility build, including adequate
local temporary capacity and retention of maintained Flatpak renderer integration.
No new native rehearsal is justified yet. Production compatibility, licensing,
release-source approval, normal installation/update/launcher validation, final
candidate CI/native matrix and production distribution/trust gates remain OPEN.
