# CyrNava v0.1.0 — native source-first release

## Active source-first release

N1–N4 are owner-ACCEPTED. The approved release is v0.1.0, targeting Ubuntu 26.04
x86_64 / GNOME Wayland, system Python 3.14 and the pinned Qt/PySide/WebEngine
6.11.3 family. Users obtain the reviewed v0.1.0 GitHub source snapshot, run
`bash install.sh`, and later run `bash update.sh` from a newer
reviewed source. The exact dependency closure is downloaded directly from official
upstream services and the locked frontend is built locally. Node/npm are build
prerequisites, not running application services. The existing native Qt interface,
authenticated backend, AppArmor attachment, renderer sandbox and data/recovery
contracts remain. First installation requires network access, Ubuntu prerequisites,
Node 24/npm 11 for building, and explicit review/loading of the exact installed
AppArmor policy before desktop launch. The application works offline afterward.
See [the installation guide](native-installation.md) and
[backup/recovery procedure](../BACKUP_RESTORE.md).

The accepted integration checkpoint is
`383970f4af683aad154eb1bccaafdd5a932d8b76`,
[CI 41648248846](https://github.com/74Cerillion/CyrNava/actions/runs/41648248846):
all required jobs, clean source installation, a distinct compatible source-based
update and byte-for-byte profile preservation PASS. The accepted owner-host
GUI/AppArmor evidence retains its actual application/dependency scope; CI does
not claim a headless GUI PASS. The final publication commit must pass ordinary
required CI before its tag is published. This does not establish arbitrary
future schema, application or dependency upgrade compatibility.

Original code is MIT, Copyright (c) 2026 74Cerillion. The owner confirms rights
to the existing CyrNava name and logo.

The source-first repository does not ship a Qt/PySide wheelhouse, virtual
environment or prebuilt frontend/application archive. Corresponding-source gaps
for the historical bundled-wheel distribution are preserved under that scope,
not treated as requirements to publish binaries that are no longer offered.
Notices for actually copied source/assets are retained; see
[the source/dependency scope](native-source-obligations.md) and
[third-party notices](native-third-party-notices.txt). Historical CI 41621033436
remains PASS only for its original offline-package inputs.

## Historical offline-package release preparation

The following notes retain the prior artifact/distribution scope.

Status: unsigned internal candidate; public release not authorized or published.
Target: Ubuntu 26.04 LTS x86_64 / GNOME Wayland, CPython 3.14 and matched
Qt/PySide/Shiboken/WebEngine 6.11.3. Original code: MIT,
Copyright (c) 2026 74Cerillion. Owner confirms rights to the existing name/logo.

The existing native Qt application provides local notes, folders, rich text, images,
offline operation, persistent workspaces, portable backup/import and safe schema
refusal. Versioned per-user installation and manual full-package maintenance reuse
one verification engine. Renderer isolation and authenticated local service remain.
N1, N2 and N3 are owner-accepted; their evidence applies to the identified packages.

N4 adds source-based native CI assembly, exact wheel inventory, exported package,
source and bootstrap auditing, offline installed provider/backend checks and release
instructions. CI does not claim to verify GNOME/Wayland renderer security headlessly.
Public production identity/signatures and exact final-package native observations
remain separate gates. See [installation/update/recovery](native-installation.md).

The supported updater initially preserves schema 5 with identical application/data
and Qt consumers. It does not promise arbitrary future upgrades or browser-profile
downgrades. Uninstall retains data and program versions. Backups omit browser
preferences/drafts; imports create a separate workspace. No automatic update service,
Flatpak runtime restoration, cloud infrastructure or broad platform matrix is required.

Redistribution remains blocked until actual bundled-component notices and matching
covered-source arrangements are completed, reviewed and packaged. Full Addons wheels
must not be called uniformly LGPL; unused components still require inventory/review.
No vulnerability clearance or byte-for-byte reproducibility certification is claimed.
