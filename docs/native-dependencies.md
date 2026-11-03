# Native dependency and notice inventory

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

System CPython, glibc, Wayland/X11, EGL/OpenGL, fonts and other platform libraries
remain supplied by Ubuntu. Installed provider/ELF checks record the actual loaded
private Qt libraries and refuse foreign Qt/missing native dependencies. A complete
host/system SBOM is outside this release's scope.

See [source/redistribution obligations](native-source-obligations.md). This inventory
supports review; it is not a legal compliance certificate or vulnerability clearance.
