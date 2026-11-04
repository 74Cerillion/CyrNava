# P6 redistribution review — owner decision required

**Public redistribution remains blocked.** This inventory/review supplies evidence
and decision requirements; it does not select a license or certify compliance.

| Component | Evidence and remaining action |
| --- | --- |
| Original CyrNava code | `UNLICENSED` and `LicenseRef-proprietary` remain. Recommend MIT for owner review, preserving dependency obligations. Owner must choose terms and exact copyright holder, authorize a LICENSE/metadata change and redistribution. A public GitHub repository grants no inferred binary-distribution permission. |
| Logo/branding assets | Existing PNGs are retained unchanged. Owner must confirm rights and permission for public redistribution, or supply approved replacements. No rights grant is invented. |
| AppStream description | Owner's metadata-only CC0-1.0 approval remains limited to that description; it grants no code/logo rights. |
| BlockNote 0.56.0 core/react/mantine | MPL-2.0. Existing frontend notices retain versions, source links and terms. Arrange reliable access to exact corresponding covered source and any modifications for recipients; keep required notices. Do not label all of CyrNava MPL automatically. Verify source availability before public publication. |
| use-composed-ref 1.4.0 | Package/upstream declare MIT, but the inspected version/repository lack a standalone copyright/license file. Existing notice records that omission. No new authoritative attribution was found in this review. Owner should obtain upstream attribution/permission or appropriate legal review; an approval string alone must not invent missing rights. No upstream contact was sent. |
| React/Mantine/other frontend dependencies | Existing MIT/BSD/0BSD/CC0 notices remain. Development-only minimatch and its new helper use BlueOak-1.0.0 and do not appear in the production frontend output. |
| Inter fonts | Bundled local WOFF/WOFF2; existing SIL OFL notice remains. Preserve the license and reserved-name restrictions if modified. No font changes. |
| Python dependencies/Pillow | Existing wheel licenses/notices are shipped; metadata inventory is expanded. Bundled native/image libraries can have additional obligations; do not treat the top-level Python license as complete coverage. |
| PySide6/shiboken 6.11.2 | Shipped dist-info declares LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only. Inventory records exact metadata hashes. Review LGPL relinking/replacement, notices and corresponding-source arrangements; the package metadata is not a complete legal assessment. |
| Qt WebEngine/PDF/WebView BaseApp | Shipped SPDX documents identify Qt 6.11.1, including `+dirty` build provenance. Corresponding source must match that upstream build, including downstream patches. Preserve Chromium/other third-party notices. Do not substitute a generic Qt source URL for exact covered source. |
| KDE Platform 6.11 | Pinned commit has Qt 6.11.2 SPDX inventories and its upstream build manifest. Runtime is retrieved independently from the verified upstream; application-bundled Qt/PySide is still CyrNava's redistribution concern. Review all shipped modules/plugins, including potentially GPL-only components. Do not infer LGPL coverage for every Qt module. |

The expanded inventory indexes **3 app and 31 runtime SPDX documents**, **23 app
and 17 runtime Python metadata records**, **186 app and 2,785 runtime ELF files**,
and **31 app and 1,522 runtime notice files**. It preserves 33 app/769 runtime
upstream package records, including NOASSERTION and unknown versions. These are
document records, not unique fully resolved dependencies. Symlinks are counted
without following them. Driver/firmware/host libraries, static embedded code,
upstream relationships, source correspondence and file-level license coverage
remain incomplete. The output is an evidence inventory, not a complete product
SBOM. The upstream SPDX files remain authoritative.

Owner decisions: code license/holder; logo rights; attribution resolution;
corresponding-source and Qt/LGPL/GPL compliance review; approval to distribute the
specific final artifacts. Until resolved, publication stays disabled. No original
license, code, logo, font, packaging permission or existing notice was changed.

Primary references: [Mozilla MPL FAQ](https://www.mozilla.org/en-US/MPL/2.0/FAQ/),
[Qt licensing](https://doc.qt.io/qt-6/licensing.html),
[Qt third-party/SBOM guidance](https://doc.qt.io/qt-6/licenses-used-in-qt.html),
[Qt LGPL obligations](https://www.qt.io/development/open-source-lgpl-obligations),
[use-composed-ref inspected source](https://github.com/Andarist/use-composed-ref/tree/ea2c9d969f2f90a349f4c99338b806423824cea2).
Use the retained exact-version documents to apply those general instructions.
