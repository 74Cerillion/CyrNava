# Native source and redistribution checkpoint

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

Primary references checked 3 November 2026:

- [MIT text](https://opensource.org/license/mit).
- [Qt LGPL/GPL obligations](https://www.qt.io/development/open-source-lgpl-obligations).
- [Qt 6.11.3 WebEngine licensing and Chromium notices](https://doc.qt.io/qt-6.11/qtwebengine-licensing.html).
- [Official PySide source releases](https://download.qt.io/official_releases/QtForPython/pyside6/).
- [MPL guidance](https://www.mozilla.org/en-US/MPL/2.0/FAQ/).

These primary references explain the review; they do not establish missing exact
source correspondence or a completed source-delivery commitment for this artifact.
