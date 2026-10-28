# Dependencies and licensing review

Recorded against the M6 candidate on 2026-10-23. No dependency version was upgraded or added in M6. Package root version changed to 0.1.0; `UNLICENSED` marks the owner's pending original-code decision, not dependency licensing.

## Inventory and compatibility

[Machine-readable inventory](dependency-inventory.json) records all 327 npm lock entries (including optional platform packages and development tooling), and all 24 pinned Python requirements. The Linux npm installation reports 305 packages including the root. Runtime traversal finds 75 npm packages: 70 MIT, three MPL-2.0, one 0BSD, one MIT OR CC0-1.0. These counts are package metadata, not a legal opinion. No XL package is declared, locked or installed. Direct declared dependencies are used by source/config/tests; no obvious unused direct dependency or resolver conflict was found. `pip check` and clean `npm ci` validate the actual resolution. npm's install audit reported zero known vulnerabilities; that is a bounded registry check, not a comprehensive security audit.

| Component | Exact version | Role | License |
| --- | --- | --- | --- |
| React / React DOM | 19.3.1 | UI runtime | MIT |
| BlockNote core / react / mantine | 0.56.0 | Editor/schema/adapter | MPL-2.0 |
| Mantine core / hooks | 8.3.11 | Existing editor UI | MIT |
| Vite / TypeScript | 8.3.4 / 5.9.3 | Build/type checking | MIT / Apache-2.0 |
| Vitest / Playwright | 5.0.5 / 1.64.1 | Unit / real-browser tests | MIT / Apache-2.0 |
| FastAPI / Pydantic | 0.156.3 / 2.14.1 | HTTP validation | MIT |
| Uvicorn | 0.54.0 | Local ASGI server | BSD-3-Clause |
| Pillow | 13.0.0 | Raster decode/normalization | MIT-CMU and bundled notices |
| pytest / HTTPX / Ruff | 9.1.1 / 0.28.1 / 0.17.1 | Backend tests/lint | MIT / BSD-3-Clause / MIT |
| Inter | bundled in BlockNote 0.56.0 | Local WOFF2 fonts | SIL OFL-1.1 |

Exact transitive versions and raw license labels are retained in the inventory. npm lock integrity hashes verify package downloads. Python requirements pin the resolution without hashes; there is no claim of a reproducible wheel supply chain. No XL licensing, AI, remote syntax highlighter or cloud SDK was introduced.

## Third-party obligations

The three BlockNote packages are **MPL-2.0**, not MIT. File-level copyleft does not automatically license all original CyrNava code under MPL. Preserve notices and provide recipients a way to obtain the corresponding covered source; covered modifications would need appropriate source availability. M6 uses unmodified published packages. The bundled [frontend notices](../frontend/public/third-party-notices.txt) give exact package versions, npm source links, license texts and source-availability information, plus copyright/license information for Inter. They are copied by Vite and linked in the application. [Mozilla's FAQ](https://www.mozilla.org/en-US/MPL/2.0/FAQ/) explains larger works and source obligations; [BlockNote terms](https://www.blocknotejs.org/legal/terms-and-conditions) distinguish core from XL.

MIT/BSD/0BSD/CC0 and OFL notices remain independent of the owner's license choice. [Python notices](python-third-party-notices.txt) retain available installed wheel license texts for all pinned requirements, including development packages. The notices are a release audit artifact, not a replacement for shipping each dependency's own license when redistributing its files. Preserve them when packaging bundles/environments.

Installed Mantine and react-remove-scroll-bar packages omit standalone license files; upstream license text was retrieved and retained with source/version information. **use-composed-ref 1.4.0 declares MIT but its package and inspected upstream repository omit a copyright/license file.** The notice states that omission rather than inventing an owner. Resolve its attribution provenance or obtain legal approval before binary/bundle distribution; the audit cannot certify complete legal clearance. No dependency code was modified to work around licensing.

## Original-code license — owner decision pending

The owner explicitly chose “Leave the license decision pending.” No LICENSE file or original-code permission grant has been added. Public v0.1.0 release approval remains blocked.

| Option | Practical benefit | Obligations / tradeoff |
| --- | --- | --- |
| MIT (recommended for review) | Short permissive grant; easy adoption | Preserve original notices; no explicit patent grant. It does not waive MPL/other dependency duties. |
| Apache-2.0 | Permissive with explicit patent terms | More terms, change notices and applicable NOTICE handling; dependency obligations still apply. |
| MPL-2.0 | Reciprocity for modified covered files | Source availability for covered files; proprietary larger works possible, but more file-boundary compliance work. |

MIT is a recommendation, not a selection. See [MIT terms](https://opensource.org/license/mit), [Apache-2.0 terms](https://www.apache.org/licenses/LICENSE-2.0), and the Mozilla FAQ above. Before public release the owner must choose a license, add the correct copyright/holder and LICENSE, update package metadata/README, and review third-party distribution obligations. Do not claim CyrNava is already open-source merely because its repository is publicly visible.
