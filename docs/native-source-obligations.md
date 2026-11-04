# Native source and redistribution obligations

## Current model — source-first repository and online dependency installer

The owner superseded the public bundled-wheel archive with a versioned GitHub
source repository. Recipients run `bash install.sh`; the installer obtains the
exact approved Python wheels from official PyPI distribution services, uses the
reviewed npm lock to build the frontend locally, and creates the native private
environment. Manual updates use `bash update.sh`. The offline implementation and
its unresolved findings remain historical, not additional native-release gates.
Source-first CI
[41648248846](https://github.com/74Cerillion/CyrNava/actions/runs/41648248846)
passed clean installation, a distinct compatible online update and profile-byte
preservation for commit `383970f4af683aad154eb1bccaafdd5a932d8b76`.
These results apply to that exact source and compatibility scope. CI 41621033436
passed only its original offline-package inputs.

| Actual material or issue | Classification for source-first v0.1 | Evidence and required action |
| --- | --- | --- |
| CyrNava original code and branding | Satisfied locally | MIT LICENSE, Copyright (c) 2026 74Cerillion; owner-confirmed name/logo rights. Retain attribution. |
| Qt/PySide/Shiboken, Chromium, FFmpeg, ICU and pydantic-core wheel binaries | Outside our active distributed payload, conditional on exclusion | No tracked wheels/venvs/native libraries. Recipient downloads directly upstream. Do not publish caches, installed trees or the old dependency bundle as source-release assets. Previous binary/source and Rust notice gaps remain unresolved for actual binary redistribution. |
| Qt GPL-only families | No incompatible direct application use identified; scope limited | Direct application imports are Core/Gui/Widgets/WebEngineCore/WebEngineWidgets. Unused GPL-only libraries in an upstream wheel do not establish MIT-source relicensing. This is not a classification of every indirect native link or permission to convey a combined binary without applicable terms. |
| use-composed-ref 1.4.0 | MIT declaration and available notices satisfied; holder clarification optional | Immutable upstream metadata declares MIT; full MIT text/component identity retained. No holder/year supplied. Absence of a separate LICENSE is not evidence of no permission, and no fresh maintainer grant is established as required. Do not invent attribution. |
| BlockNote MPL, Inter fonts and copied frontend notices | Required for material actually distributed; retained in the reviewed source | Preserve existing full notices and exact version/source links. New frontend bundles are local build outputs. Any covered source/executable material actually conveyed still needs its applicable source availability and notice conditions. |
| Historical Playwright traces | Excluded from the current public tree after preservation | Retained privately as development evidence. Earlier Git snapshots can still contain captured HTML/CSS and Inter fonts; retain applicable notices and source references. `.gitignore` neither removes tracked files nor erases history. |
| Source/version authenticity | Explicit repository trust required | A co-located source inventory detects changed inputs but does not independently authenticate the installer. Use reviewed immutable version/commit instructions; a GitHub ZIP requires no `.git`. No production signing identity is invented. |

GPLv3 section 0 permits running/private modification; its sections 5–6 concern
conveying covered source/object code. LGPLv3 section 4 preserves library
modification/debugging rights and specifies alternative recombination mechanisms.
These terms are not eliminated by online installation. The project adds no
reverse-engineering restriction, changes no dependency license, and does not
represent its integrity checks as revoking recipients' license rights. A future
binary distribution would need its own corresponding-source/notice assessment.

For source publication, retain MIT plus notices for actual copied material and
the versioned upstream source references. Do not attach the 1 GB Qt source archive
merely to satisfy a binary distribution that is no longer being offered. Do not
delete that archive or earlier evidence. No vendor contact, publication, signing
or history rewrite is authorized. Historical binary-source correspondence remains outside the active source-only
payload; it would require review before any future binary distribution.

Primary provisions: [GPLv3 §§0, 5–6](https://doc.qt.io/qt-6.11/gpl.html),
[LGPLv3 §4](https://doc.qt.io/qt-6.11/lgpl.html),
[MIT notice condition](https://opensource.org/license/mit),
[npm license declaration](https://docs.npmjs.com/cli/v11/configuring-npm/package-json/#license),
[MPL §§3.1–3.2](https://www.mozilla.org/en-US/MPL/2.0/),
[OFL](https://openfontlicense.org/open-font-license-official-text/).

## Historical bundled-wheel redistribution checkpoint — preserved

The following findings and proposed delivery arrangement describe the unchanged
offline hosted artifact. They do not describe the active public payload.

3 November 2026: **CONDITIONAL — specific redistribution obligations remain.**
Hosted CI `41621033436` and artifact verification passed for source
`b7ab94265270866911311b4ca818071868f58361`; this does not establish exact
Qt/PySide/WebEngine/Chromium source and build correspondence or complete bundled
third-party notices. Original-code MIT attribution is `Copyright (c) 2026
74Cerillion`; name and logo redistribution rights are owner-confirmed.
N1–N3 remain ACCEPTED / COMPLETE.

Original code MIT attribution and name/logo redistribution are owner-approved.
They do not relicense bundled third-party code. Before public redistribution:

1. Retain each exact shipped wheel and generated dependency/file/notice inventory.
2. Obtain the matching PySide/Shiboken 6.11.3 and Qt 6.11.3 source/build correspondence,
   including Qt WebEngine's matching Chromium/third-party sources, downstream changes
   and applicable licenses/notices. Record verified source hashes and upstream build
   identities. A matching version number or generic latest source link is insufficient.
3. Review every shipped module/tool/plugin, including unused Addons components and
   bundled native image/ICU/etc. libraries. Preserve applicable LGPL/GPL/MPL/BSD/OFL
   and other notices. Do not call the whole wheelhouse MIT or LGPL-only.
4. Provide a practical reliable source-delivery arrangement with the release for
   covered components. Delivering exact covered source alongside the binary is the
   straightforward proposed route; no Qt compilation is required to distribute source.
   Review the actual chosen license's source-offer/delivery terms before publishing.
5. Supply BlockNote's matching covered source/modifications and resolve the recorded
   use-composed-ref attribution gap. Preserve the font and frontend notices.
6. Document and validate recipient modification/replacement/rebuild rights for LGPL
   components. All application/installer source is supplied. Integrity checks must
   not be represented as a legal prohibition on users rebuilding with their own
   compatible libraries and signing/trusting their own package. No reverse-engineering
   prohibition is added. Replacement/rebuild instructions still need exact-source review.

`CyrNava-source.zip` contains the actual application/frontend/build/installer/test
source snapshot with a per-file manifest, source commit and explicit local patch
identity. It is **CyrNava's source**, not a substitute for Qt/Chromium covered source.
CI permits clean source only; local preparation explicitly records uncommitted files.
No private profiles, keys, logs, environment dumps or historical evidence trees belong
in the source or binary publication set.

The current source/notice gaps remain publication blockers. No unbounded Qt source
download/build, speculative binary stripping, paid infrastructure or licensing
declaration is authorized as a shortcut. Measure exact compressed source sizes and
available storage before acquiring a large source set; do not unpack Qt/Chromium here.

## Exact reviewed package and source-delivery proposal

The reviewed hosted development package is `CyrNava-0.1.0-n4.1-ubuntu-x86_64.zip`,
SHA-256 `1e49348570e7f779a352cb0a2d623a6f3973f828628b9ea60bb6e4fc6f2a3897`.
Its 19 locked Python distributions contain 498 ELF files and 18 upstream
license/notice/SBOM documents. The four Qt/PySide/Shiboken wheels contain no
such notice documents. The [native redistribution catalog](native-redistribution.json)
records exact component and source identities and the material prepared locally.
New notice text is a future build input; the existing artifact is unchanged.

Pydantic-core's original SBOM lists 99 components and includes Unicode-3.0,
Unicode-DFS-2016, Zlib and Apache/LLVM-exception terms. Its sole core MIT license
and component metadata do not establish complete applicable bundled-component
attributions. The actual native-extension component/notice mapping remains a
specific uncertainty; SBOM presence does not prove every listed build dependency
is shipped. The original SBOM is retained in the unchanged wheel. No additional
dependency project, download or build is started to fill that gap in this pass.

The proposed simple delivery arrangement is to attach the intact Qt 6.11.3 and
PySide 6.11.3 source archives and three exact BlockNote 0.56.0 source packages to
the same eventual GitHub Release as the binary, with checksums and a source index.
No custom source server or separate duplicate source archive is needed. The
archives are retained and hash-verified locally, but no assets are published and
their presence alone does not prove correspondence to the Qt wheels.

The 2,519 previously selected Qt/PySide notice documents are an incomplete
selection: standard GPL/LGPL/exception texts and REUSE/attribution metadata were
not all selected. The prepared standard license copies improve the material but
do not establish complete Chromium/WebEngine, FFmpeg, ICU or other native credits.
Actual shipped GPL-only-or-commercial module families include CanvasPainter,
Charts, DataVisualization, Graphs, HttpServer, NetworkAuth, Quick3D,
VirtualKeyboard, Lottie, QuickTimeline and WaylandCompositor; shipped QML
compiler/tools also have GPL/Qt-exception terms. These files cannot be called
LGPL-only merely because aggregate wheel metadata offers LGPL/GPL alternatives.
Wayland client libraries have a separate LGPL-capable scope. CyrNava directly
imports Core, Gui, Widgets, WebEngineCore and WebEngineWidgets. Presence of a
module or that import list alone does not establish every linking classification
or require changing CyrNava's original-code MIT license.

## Recipient replacement and rebuild rights — draft, not validated

Recipients retain the rights granted by the applicable third-party licenses,
including permitted modification and reverse engineering for debugging such
modifications. CyrNava adds no contractual reverse-engineering prohibition.
Current installation integrity checks deliberately reject modified installed
libraries; automatic drop-in replacement has not been demonstrated. Do not
represent those integrity checks as removing recipients' license rights.

The proposed alternative is to use the supplied application/installer source,
obtain the exact upstream Qt/PySide build inputs, replace compatible components,
update the recipient's own dependency locks, rebuild/repackage, and trust the
recipient's own package/key. The project does not promise to sign modified
packages. This route remains UNVALIDATED until exact build inputs and a practical
replacement/rebuild procedure are established. No security check is weakened to
make that claim.

Primary references checked 3 November 2026:

- [MIT text](https://opensource.org/license/mit).
- [Qt LGPL/GPL obligations](https://www.qt.io/development/open-source-lgpl-obligations).
- [Qt 6.11.3 WebEngine licensing and Chromium notices](https://doc.qt.io/qt-6.11/qtwebengine-licensing.html).
- [Official PySide source releases](https://download.qt.io/official_releases/QtForPython/pyside6/).
- [MPL guidance](https://www.mozilla.org/en-US/MPL/2.0/FAQ/).

These primary references explain the review; they do not establish missing exact
source correspondence or a completed source-delivery commitment for this artifact.
