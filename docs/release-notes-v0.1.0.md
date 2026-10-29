# CyrNava v0.1.0 — release description draft

**Draft only. Do not publish until the owner clears the release checklist and licensing gates.**

CyrNava's first Phase 1 release is a local cybersecurity knowledge workspace. Organize nested folders and rich-text notes, paste screenshots or upload PNG/JPEG/WebP files, and continue working offline. Notes use SQLite; validated images remain on the local filesystem outside the repository.

Includes visible autosave state, revision conflict protection, keyboard tree navigation, deliberate deletion confirmation and an offline backup/restore CLI. The built React frontend and FastAPI API run together on `127.0.0.1` without Vite. See the README for installation, usage and supported prerequisites.

This is not a complete penetration-testing engagement management system. It has no engagement/host/vulnerability entities, scanners, AI, authentication or cloud synchronization. Unconfirmed edits have browser-local recovery when storage is available; storage deletion/failure can still lose drafts, and interrupted image uploads must be reselected. Data and backups are unencrypted. Images are normalized rather than preserved as forensic originals.

Target platform: Linux/Ubuntu 24.04, Python 3.12, Node 24.19.0/npm 11.6.2; Chromium is tested. No clean-OS/cross-platform/WCAG certification is claimed. The current F-09 candidate uses schema 5 and native document format 1. Stop all backends and retain a verified pre-upgrade backup: older application code refuses schema 5.

The F-09 candidate adds global full-text search of saved titles and rich-text/code content, ranked previews, local keyboard navigation and safe result opening through the existing save guard. Search is SQLite FTS5, stored in the same private external profile, with an offline rebuild command. See the [F-09 validation report](../F09_M4_REPORT.md) and [synthetic backend timings](search-benchmark.md). These observations are not latency guarantees or public-release approval.

Original-code license remains pending owner selection; third-party source/notice obligations and attribution verification must be cleared before publishing. Do not attach bundled build artifacts until their notices/source-availability obligations are approved. See M6_REPORT.md and M6_VERIFICATION.md for candidate evidence and limitations.
