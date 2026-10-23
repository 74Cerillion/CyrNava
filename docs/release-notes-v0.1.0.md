# ENGAGE v0.1.0 — release description draft

**Draft only. Do not publish until the owner clears the release checklist and licensing gates.**

ENGAGE's first Phase 1 release is a local cybersecurity knowledge workspace. Organize nested folders and rich-text notes, paste screenshots or upload PNG/JPEG/WebP files, and continue working offline. Notes use SQLite; validated images remain on the local filesystem outside the repository.

Includes visible autosave state, revision conflict protection, keyboard tree navigation, deliberate deletion confirmation and an offline backup/restore CLI. The built React frontend and FastAPI API run together on `127.0.0.1` without Vite. See the README for installation, usage and supported prerequisites.

This is not a complete penetration-testing engagement management system. It has no engagement/host/vulnerability entities, scanners, AI, authentication or cloud synchronization. Unsaved drafts can be lost on forced shutdown. Data and backups are unencrypted. Images are normalized rather than preserved as forensic originals.

Target platform: Linux/Ubuntu 24.04, Python 3.12, Node 24.19.0/npm 11.6.2; Chromium is tested. No clean-OS/cross-platform/WCAG certification is claimed. Schema remains version 3; stop the backend and make a verified backup before upgrades.

Original-code license remains pending owner selection; third-party source/notice obligations and attribution verification must be cleared before publishing. Do not attach bundled build artifacts until their notices/source-availability obligations are approved. See M6_REPORT.md and M6_VERIFICATION.md for candidate evidence and limitations.
