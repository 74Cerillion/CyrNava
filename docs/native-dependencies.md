# Native dependency and notice inventory

The current public model is **source-first GitHub installation with online,
hash-locked upstream dependency acquisition**. The source installer builds the
frontend from `package-lock.json`; Node/npm do not run during normal application
launch. Downloaded wheels, node_modules, venvs and generated application bundles
are local installation/build outputs, not repository release payloads.
The exact Qt/PySide/Shiboken/WebEngine 6.11.3 closure remains unchanged.
See the current [source-first assessment](native-source-obligations.md) and
`source_first` in the [catalog](native-redistribution.json).

The inventory and binary-source gaps below refer to the retained historical
offline package. They remain valid for that artifact, but do not automatically
block publication of a repository that does not distribute those binaries.

The authoritative native lock is `packaging/native/feasibility/dependencies.json`
plus `requirements.lock`. It pins every official wheel filename, size and SHA-256.
N4 preserves the accepted 6.11.3 Qt/PySide/Shiboken/WebEngine closure; no Qt or
Chromium source build or silently substituted dependency is used.

Each assembled set contains `dependency-inventory.json`: exact wheel metadata,
upstream links, notice/SPDX/SBOM paths/hashes actually present, and every wheel ELF
path/size. It includes the full distributed wheel content, not merely imported
modules. Missing notices are recorded as missing, not removed from inspection.
Original code MIT and frontend third-party notices accompany the package.
Existing upstream wheel/license content is retained without modification.

The official PySide6, Essentials, Addons and Shiboken 6.11.3 wheels examined here have
no files whose names identify license, notice, attribution, SPDX or SBOM documents.
Their metadata declares LGPL/GPL alternatives. That declaration is not a full
notice set, exact native-library inventory or redistribution clearance. Full Addons
also carries modules/tools that need individual license review. Qt WebEngine has
Chromium and bundled third-party terms in addition to Qt's terms.

The frontend's `third-party-notices.txt` retains BlockNote MPL-2.0, React/Mantine,
Inter font and other recorded notices. The existing use-composed-ref 1.4.0 attribution
gap remains unresolved until authoritative applicable notice/permission is retained.
Do not relabel it cleared merely because npm metadata says MIT.

The 3 November 2026 [native redistribution catalog](native-redistribution.json)
is scoped to hosted source `b7ab94265270866911311b4ca818071868f58361`, ordinary
CI `41621033436`, and development archive SHA-256
`1e49348570e7f779a352cb0a2d623a6f3973f828628b9ea60bb6e4fc6f2a3897`.
It reconciles 19 exact wheel identities, 498 ELF files, and 18 original upstream
license/notice/SBOM documents with the unchanged lock and hosted file manifest.
The four Qt/PySide/Shiboken wheels account for 471 ELF files; their aggregate
metadata does not supply a complete module-specific license or native credit set.
Pillow's 26 ELF files and pydantic-core's one ELF remain separately identified;
their original license documents and supplied native component/SBOM records are
preserved rather than replaced by a top-level MIT label.

The exact three BlockNote source archives match their lock SHA-512 values and
all 1,454 published installed files (729 source files). All 18 shipped Inter font
files match the core source package. Font metadata identifies Inter 3.019; the
version-appropriate copyright/trademark header and OFL text are retained.
The frontend notice proposal also preserves Vite/Rolldown notices for generated
runtime helpers actually emitted into the JavaScript. This does not classify all
development dependencies as shipped code. The original 75 runtime package notice
sections remain intact. All additions are future package inputs; no accepted
artifact was rebuilt or changed by this documentation pass.

**CONDITIONAL:** exact Qt/PySide/WebEngine/Chromium/FFmpeg/ICU build/source and
credit correspondence, shipped GPL/exception component obligations, the practical
recipient replacement/rebuild route, and use-composed-ref attribution clarification
remain specific redistribution tasks.
Pydantic-core's actual bundled Rust-component attribution mapping also remains
unestablished: the original 99-component SBOM contains additional Unicode, Zlib
and Apache/LLVM-exception terms, but does not prove all entries ship. Its core
MIT license is not claimed to clear those components. Source archive hashes or
standard license copies alone do not clear them. MIT `Copyright (c) 2026 74Cerillion` and owner
rights to the CyrNava name/logo are settled and are not additional owner decisions.

System CPython, glibc, Wayland/X11, EGL/OpenGL, fonts and other platform libraries
remain supplied by Ubuntu. Installed provider/ELF checks record the actual loaded
private Qt libraries and refuse foreign Qt/missing native dependencies. A complete
host/system SBOM is outside this release's scope.

See [source/redistribution obligations](native-source-obligations.md). This inventory
supports review; it is not a legal compliance certificate or vulnerability clearance.
