# Changelog

## Unreleased — desktop branding and CyrNava appearance

- Add the selectable CyrNava skin while retaining Light/Dark/System and existing browser preferences.
- Integrate the owner's original logo, local favicon/sidebar assets and seven Lanczos icon sizes.
- Upgrade known desktop placeholders during installation while retaining custom artwork and the existing launcher lifecycle.
- Add reference-view browser verification for layout, menus, contrast, persistence and mobile behavior. No database, dependency or storage-path changes.

## CyrNava rebranding — Unreleased

Application, desktop/menu titles, package metadata and current documentation now use CyrNava. New configuration uses `CYRNAVA_*` with legacy aliases. Existing storage, browser keys and desktop IDs remain stable for compatibility. A dry-run-capable migration script prepares verified backups before local checkout/remote changes; it never pushes or moves application data. See `REBRANDING_REPORT.md` and `docs/migrate-to-cyrnava.md`.

The M6 entry below is a historical milestone record. Current capabilities, including schema 4 templates, browser draft recovery and appearance preferences, are described in README and their later engineering reports.

## 0.1.0 — Unreleased candidate

Initial Phase 1 local cybersecurity knowledge workspace: nested folders, persistent rich-text notes, core BlockNote formatting/code, local clipboard/uploaded images, keyboard navigation, serial autosave with revision conflicts, protected deletion and offline backup/restore.

M6 adds one-origin loopback serving of the built frontend, visible version and save status, editor naming/skip link/dialog description, contained narrow-screen controls, newcomer setup/architecture/ADRs, synthetic screenshots, dependency notices, and expanded real-browser release acceptance.

Compatibility target: Linux/Ubuntu 24.04, Python 3.12, Node 24.19.0, npm 11.6.2, Chromium. Existing schema remains version 3 and document format 1; M6 changes neither saved notes nor assets. Back up using the offline procedure before upgrades. Earlier schemas migrate through existing tested startup migrations; newer schemas are refused.

Limitations: pending original-code license and attribution review prevent publication approval; drafts are memory-only, backups unencrypted/offline, no merge/authentication/cloud features, normalized images are not forensic originals, and comprehensive accessibility/cross-platform certification is not claimed. See M6_REPORT.md for verification and release gates. No release/tag has been published by M6.
