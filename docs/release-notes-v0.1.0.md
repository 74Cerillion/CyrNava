# CyrNava v0.1.0 — release description draft

**Draft only. Do not publish until the owner clears the release checklist and licensing gates.**

CyrNava v0.1.0 is a local cybersecurity knowledge workspace. The sole supported
release target is Ubuntu 26.04 LTS, x86_64, GNOME Wayland; final-package
verification is pending.
Organize nested folders and rich-text notes, search saved text and code, paste
screenshots or upload PNG/JPEG/WebP files, and continue working offline. Notes use
SQLite schema 5; validated image files and references remain in private storage.

The native application uses PySide6/Qt WebEngine with the built React frontend
and authenticated FastAPI backend on private loopback. It includes visible
autosave state, revision-conflict protection, keyboard navigation, recovery drafts,
verified backup/import and staged workspace migration. The Flatpak production ID
is `io.github._74Cerillion.CyrNava`, branch `stable`. No Node, npm, Vite or host Python
development environment is required for an installed application; Python 3.13,
PySide6 and Qt are supplied by the pinned package/runtime. The required KDE
Platform is `org.kde.Platform/x86_64/6.11`. Ubuntu Wayland native verification and
public distribution checks remain P6 acceptance gates.

The application has no engagement/host/vulnerability entities, scanners, AI,
human-account login or cloud synchronization. Desktop-session API authentication
protects the local backend. Unconfirmed edits have local recovery when storage is
available; storage deletion/failure can still lose drafts, and interrupted image
uploads must be reselected. Data and backups are unencrypted. Images are normalized
rather than preserved as forensic originals. The renderer sandbox, constrained
navigation, portal file handling and Flatpak filesystem/network restrictions are
required and must remain enabled.

The native document format is version 1. Keep a verified pre-upgrade backup and
close all application windows before maintenance. Binary rollback does not reverse
database upgrades; incompatible application versions must refuse newer schemas.
Use verified snapshot restoration when compatibility requires it. No cross-platform,
WCAG, byte-for-byte reproducibility or complete vulnerability certification is claimed.

Search uses SQLite FTS5 in the same private profile, with an offline rebuild
procedure. See the [F-09 validation report](../F09_M4_REPORT.md) and
[synthetic backend timings](search-benchmark.md); these are not latency guarantees.

P6 remediates the minimatch development-tool advisory in its candidate dependency
lock; the accepted historical source/artifact retains its original identity.
Final source, CI, bundle, OSTree commit and production signing identity must be
selected and verified together before distribution. This draft creates no version,
tag, release or publication. Original-code/logo permissions, third-party attribution
and covered-source obligations, production trust and public-release authorization remain
open. See the [P6 report](../ci/P6_REPORT.md), [license review](../ci/P6_LICENSE_REVIEW.md)
and [release runbook](../ci/P6_RELEASE_RUNBOOK.md).

The intended distribution is a signed Flatpak bundle downloaded from GitHub
Releases, with manual verified-bundle updates. Initial installation requires
network access for KDE Platform and graphics dependencies; SDK/BaseApps are build
inputs, not user prerequisites. Editing remains local and offline after installation.
The corrected package is not available yet. The historical Qt/PySide ABI-broken
artifacts are not public release candidates. Matching component version strings
alone do not prove compatibility with future independent runtime updates.

Backup import preserves workspace content but may create fresh browser appearance
preferences. Normal restart/update/reinstall must preserve preferences in the same
profile; a new import's baseline must be observed before later persistence checks.
Uninstall without deleting application data preserves it, but keep a verified
backup before maintenance. No public-download, corrected normal-launch or real
version-to-version update success is claimed by this draft.
