# Changelog

## 0.1.0 — Unreleased candidate

Initial Phase 1 local cybersecurity knowledge workspace: nested folders, persistent rich-text notes, core BlockNote formatting/code, local clipboard/uploaded images, keyboard navigation, serial autosave with revision conflicts, protected deletion and offline backup/restore.

M6 adds one-origin loopback serving of the built frontend, visible version and save status, editor naming/skip link/dialog description, contained narrow-screen controls, newcomer setup/architecture/ADRs, synthetic screenshots, dependency notices, and expanded real-browser release acceptance.

Compatibility target: Linux/Ubuntu 24.04, Python 3.12, Node 24.19.0, npm 11.6.2, Chromium. Existing schema remains version 3 and document format 1; M6 changes neither saved notes nor assets. Back up using the offline procedure before upgrades. Earlier schemas migrate through existing tested startup migrations; newer schemas are refused.

Limitations: pending original-code license and attribution review prevent publication approval; drafts are memory-only, backups unencrypted/offline, no merge/authentication/cloud features, normalized images are not forensic originals, and comprehensive accessibility/cross-platform certification is not claimed. See M6_REPORT.md for verification and release gates. No release/tag has been published by M6.
