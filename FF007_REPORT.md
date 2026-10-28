# FF-007 — Application-wide appearance

ENGAGE v0.1.0 · Review candidate · 2026-10-28

## A. Implementation summary

Added an always-accessible **Appearance** selector above the editor with **Light**, **Dark**, and **System**. System is the default, follows live browser/OS color-scheme changes, and is overridden by explicit Light/Dark choices. The selection is stored locally and restored at startup. Invalid/missing values safely fall back to System; blocked storage still permits changes for the current page.

Dark mode covers navigation/tree selection/hover/focus, the collapsible layout, toolbar, native controls, dialogs, template selection/management/capture, empty/recovery states, save/error feedback, links, and the editor's native menus and formatting surface. BlockNote receives its supported `light`/`dark` theme prop and reuses the enclosing Mantine provider. Theme changes do not recreate the editor, reset the note, alter JSON, or trigger note writes. Existing upload/save/recovery lifetimes remain unchanged.

No dependency, backend API, database schema, canonical document format, template definition, application name, or runtime external service changed. This implements FF-007 only. Nothing was committed, pushed, published, installed into the everyday desktop copy, or run against real application data.

### Assessment completed before implementation

The checkout was clean at the start. Inspected `App`, global CSS, `KnowledgeEditor`, note/autosave boundaries, FF-006/FF-018 interfaces, browser preferences and existing unit/browser tests. The app used plain CSS with fixed light colors; no application-level Mantine provider existed. `KnowledgeEditor` explicitly passed `theme="light"`; BlockNote supplied a fallback Mantine provider internally. Installed package source confirmed that BlockNote accepts native theme strings, themes its portal roots, and reuses an enclosing provider. Mantine's installed manager supports validated `light`/`dark`/`auto` preferences, storage error handling and system-change listeners.

The selected approach was one application provider plus CSS tokens, a generic presentation prop through the existing adapter, and a small same-origin startup script. No significant architecture/persistence change or additional approval was needed.

## B. Modified files

Paths below are relative to the repository root. New files are marked **new**.

| File | Responsibility and reason |
| --- | --- |
| `.gitignore` | Narrow exception for the application-owned startup script. Other files under that asset directory remain ignored; private assets are not broadly unignored. |
| `frontend/index.html` | Loads the blocking `/assets/appearance-init.js` head script before the application entrypoint. |
| `frontend/public/assets/appearance-init.js` **new** | Reads the preference, resolves System and sets the initial root color-scheme attribute before React. Uses only browser APIs; no storage writes, network service or event subscriptions. |
| `frontend/src/appearance.tsx` **new** | Application-level Mantine provider, dedicated storage key and native select control. Depends only on existing React/Mantine packages. Mantine owns the only persistent theme state. |
| `frontend/src/appearance.test.tsx` **new** | Preference resolution, live OS changes, explicit overrides, remount persistence, blocked storage and execution of the actual startup script using existing Vitest/Testing Library and Node VM. |
| `frontend/src/App.tsx` | Wraps the existing workspace in the provider, resolves its effective scheme, renders Appearance outside the collapsible sidebar, and passes presentation to `PersistentNote`. |
| `frontend/src/App.test.tsx` | Tests changing theme with collapsed navigation and dirty edits while preserving the editor, native document and ordinary autosave. Existing adapter mock now exposes the theme prop for assertions. |
| `frontend/src/components/PersistentNote.tsx` | Forwards optional generic `light`/`dark` presentation to the editor, including recovered drafts. No autosave or persistence algorithm changes. |
| `frontend/src/components/KnowledgeEditor.tsx` | Passes the presentation prop to supported `BlockNoteView.theme`; editor construction and native serialization remain unchanged. |
| `frontend/src/components/KnowledgeEditor.test.tsx` | Verifies a theme rerender changes the native view prop without replacing that view or emitting a document change. |
| `frontend/src/styles.css` | Light/dark semantic tokens for existing application surfaces, wrapping selector layout, hover/focus feedback, native control scheme, readable statuses/errors and small editor muted-text corrections. |
| `frontend/src/test-setup.ts` | Adds the missing jsdom `matchMedia` stub and clears the root theme attribute during cleanup. Theme tests replace the stub with a controllable event source. |
| `frontend/e2e/workspace.spec.ts` | Adds a real-browser appearance journey and computed contrast helper to the existing isolated-profile harness. Existing seven journeys are retained. |
| `README.md` | Feature description, operation, browser-local persistence and installed-update boundary. |
| `docs/architecture.md` | Provider ownership, editor presentation boundary, CSS tokens and CSP-compatible initialization. |
| `FF007_REPORT.md` **new** | This assessment, inventory, execution walkthrough, test matrix, decisions and limitations. |

There are no backend changes, migration changes, package manifest changes or lockfile changes.

## C. Architecture walkthrough

### User selects Dark

1. `AppearanceControl` in `appearance.tsx` receives the select's change event and calls Mantine's `setColorScheme('dark')`.
2. The one `MantineProvider` updates its preference, applies `data-mantine-color-scheme="dark"` to `<html>`, and persists the value through its localStorage manager under `engage.appearance.v1`.
3. The dark CSS token block in `styles.css` changes application surfaces. Native inputs/selects also inherit CSS `color-scheme: dark`.
4. `Workspace` in `App.tsx` reads `useComputedColorScheme`. Explicit Dark resolves to `dark` regardless of the OS. The resolved string flows through `PersistentNote`/`NoteEditor` to `KnowledgeEditor`.
5. `KnowledgeEditor` updates only `BlockNoteView.theme`. BlockNote applies its native editor/menu/portal themes and uses the existing enclosing Mantine context. `useCreateBlockNote` options and component keys do not depend on appearance, so its editor/document remain mounted.
6. No `changeDocument`, `changeTitle`, API request or database write belongs to this flow. Pending autosave still runs on the existing schedule; its textual status remains visible in the selected palette.

### System and startup

The UI's **System** value is Mantine's `auto`. Mantine and its computed-scheme hook use native `matchMedia('(prefers-color-scheme: dark)')` and change events. An OS change updates the resolved theme only while System is selected. There is no second React theme context or manually synchronized copy of the preference.

On navigation/restart, `appearance-init.js` runs as a blocking same-origin head script. It validates the same three stored values, resolves System and sets the same root attribute before the React entrypoint loads. It does not become an ongoing state owner; Mantine takes over after mounting. The browser test deliberately stalls the React entrypoint and confirms the dark background/root attribute with an empty React root. This reduces flashes without allowing inline release JavaScript or modifying CSP/backend routes: `/assets` is already served by the release app and Vite copies the public asset unchanged.

The storage key and accepted values are repeated in the tiny non-module startup script so it can execute before the React bundle. Tests run that actual file and check its key/resolution against the provider constant. No local note, template or recovery-draft key is read or cleared.

### Independence from navigation and templates

Appearance remains in the main toolbar when FF-006 hides the sidebar. Neither appearance nor navigation is part of the note's React key. Template dialogs inherit the root palette. Built-in/custom native documents are unchanged, and saving a custom template captures content without injecting theme RGB values. New instances use their existing independent note/block/image identities. User-selected document colors remain document formatting, separate from the appearance preference.

## D. Testing report

All application/browser tests used isolated temporary profiles and synthetic documents. No tests targeted the installed application or personal notes. This session used the pinned Node binary directly and an approved task-local `TMPDIR` because the tool sandbox restricts ordinary temporary writes; normal terminal commands below do not require that override.

| Executed check | Result |
| --- | --- |
| Focused appearance/App/editor unit tests | **49 passed** after adding the jsdom media-query stub. |
| Full frontend `vitest run` | **203 passed across 18 files**; 14 new feature cases over the previous 189. |
| TypeScript `tsc --noEmit` | Passed. |
| ESLint with zero warnings allowed | Passed. |
| Production Vite build | Passed; existing large-chunk warning remains. |
| Full Chromium release Playwright suite | **8 passed**: the new appearance journey plus all seven existing lifecycle/workspace journeys. |
| Firefox release appearance journey | **1 passed**; includes the same live-theme, menu, formatting, persistence and contrast assertions. |
| Chromium Vite development appearance journey | **1 passed**; uses the real development proxy and local startup asset. |
| Visual inspection | Inspected actual synthetic browser captures of Light/Dark, editor formatting/color picker, slash menu, template manager, error state and 390-pixel layout. |
| Git whitespace/scope checks | `git diff --check` passed; no backend or dependency changes. |

The new journey measures computed foreground/background text contrast with a **4.5:1** minimum for sampled app help text, note inputs, selected tree item, save/error indicators, editor links/code/placeholders, native formatting/color menus, slash-menu labels/descriptions and template dialogs/selects. It waits for popup fade completion before visual capture. These are sampled checks, not a complete accessibility certification.

### Requested acceptance matrix

| Test | Executed evidence and scope |
| --- | --- |
| T-007-01 Light | Browser checks, original light token values and visual review. |
| T-007-02 Dark | Real editor/app/dialog/menu rendering, contrast assertions and visual review. |
| T-007-03 System follows OS | Unit event-source tests and browser media emulation. |
| T-007-04 Live OS change | Browser changes media preference with the editor focused; resolved app/editor attributes change and focus stays in the editor. |
| T-007-05 Explicit override | Light against dark OS and Dark against light OS, unit and browser assertions. |
| T-007-06 Persistence | Fresh provider mount, browser reload with System and explicit Dark, plus backend stop/restart during recovery. Invalid/missing/blocked storage cases have unit coverage. |
| T-007-07 Editor preservation | Same connected editor DOM across changes, preserved bold/list/link/code content, exact API note/revision/document equality and no new PATCH during the theme-only phase. Adapter test asserts no document-change callback. |
| T-007-08 Mantine surfaces | Native formatting toolbar, Colors dropdown, slash-menu portal theme attributes, text contrast and screenshots in both themes. |
| T-007-09 Navigation | Collapse/expand in each palette, selector stays visible, collapsed state reloads with System. Existing FF-006/FF-018 combined journey also passes. |
| T-007-10 Templates | Enumeration rendering, builtin selection/management dialogs, custom capture and equivalent generated native JSON in both modes. Existing template CRUD/restart/image journey passes. |
| T-007-11 Formatting | Existing native formatted note survives theme-only changes exactly; canonical custom template copies compare equal after fresh block IDs are excluded. |
| T-007-12 Autosave | Dirty-title unit test, unchanged API revision/PATCH count during switching, real Save Error with backend down, theme switches preserving pending edits, retry after restart, unchanged document and reload. Existing rapid-edit/stale-acknowledgement journeys pass. |
| T-007-13 Keyboard | Native selector participates in Tab order with a visible focus outline; navigation toggle activates with Enter. Existing tree/formatting/keyboard journey passes. |
| T-007-14 Light consistency | Kept original layout/font/major light palette and native BlockNote light theme; reviewed light captures. Small form-border, link/hover and muted-text/error contrast corrections are intentional. This is visual review, not pixel-diff certification. |

### Failures encountered and corrections

- ESLint initially reported browser globals in the new standalone JavaScript file because the project's browser-global configuration applies only to TypeScript. Added a precise globals declaration to that one script; no lint rule was disabled.
- App unit tests initially failed because jsdom does not supply a usable `matchMedia`, now needed by the app-level provider/hooks. Added a default test stub and controllable appearance-specific listeners. Real browser code was not weakened to accommodate the test environment.
- The first browser attempt used exact label-text lookup for a select nested inside its label. The accessible combobox name was correct, but that locator did not match the label's option text. Switched to its accessible combobox role/name.
- The first formatting-toolbar check selected DOM text while focus was still in the theme selector. Replaced that setup with a real double-click in editor text; the native toolbar opened normally.
- Initial popup captures were taken during native fade transitions. Added a condition waiting for full opacity and checked actual menu text contrast; no fixed sleep or retry count was introduced.
- Visual/source review identified low-contrast native disabled/muted text and placeholder affordances, and an existing header paragraph rule overriding error-text inheritance. Added small targeted presentation corrections and reran browser checks.

No acceptance assertion was removed, and no persistence, revision protection, validation, lifecycle or browser security setting was bypassed.

### Reproduction

From the repository's `frontend/` directory:

```bash
npm run lint
npm test
npm run build
npm run test:release
ENGAGE_E2E_RELEASE=1 npx playwright test e2e/workspace.spec.ts --grep 'appearance follows' --browser=firefox
npx playwright test e2e/workspace.spec.ts --grep 'appearance follows'
```

Browser installation is development tooling only; the installed browsers were reused. The final command uses Vite development mode. Backend-only pytest was not rerun because no backend code changed; the release browser suite exercised the real unchanged backend, including lifecycle and backup/restore.

## E. Design decisions

| Decision | Reason and tradeoff |
| --- | --- |
| Reuse Mantine preference infrastructure | Already installed and used by BlockNote. Handles valid values, storage, system changes and effective schemes without custom state management or a second theme store. `auto` is the internal spelling of System. |
| App-level provider wrapping existing Workspace | Keeps one authoritative preference above all app/editor/portal surfaces. The existing workspace's state and keys stay stable; no unrelated component restructuring. |
| Generic presentation prop through note/adapter | The app passes only `light`/`dark`; BlockNote's APIs stay inside its dedicated adapter. Theme is never inserted into a document or save payload. |
| Plain CSS semantic tokens | Reuses the existing styling system and preserves light colors. Adding another styling framework, component library or utility layer would be unnecessary. |
| Native BlockNote string theme | Uses supported editor integration for actual editing/menus, rather than reconstructing native UI with CSS. A few muted-text variables and the empty-block hint selector improve contrast; these small exceptions should be rechecked when upgrading pinned BlockNote. |
| `withCssVariables={false}` | Preserves the same scoped Mantine variables already supplied by BlockNote's stylesheet and avoids introducing a global style/reset layer that could change the light UI. |
| Small blocking local startup script | A post-mount effect alone would allow an avoidable light flash. Mantine's inline color-scheme script would conflict with current release CSP. The external local file uses the existing `/assets` route and needs no backend/security-policy changes. There is one extra tiny local asset request. |
| Browser-local appearance | No schema/API changes for a per-browser preference. It is origin/profile-specific and intentionally excluded from workspace backup. Storage failure means session-only appearance changes. |

## F. Known limitations and human review

- Automated contrast assertions sample important surfaces; they are not a full WCAG audit. Screen-reader behavior, high-contrast/forced-colors modes and every native platform dropdown were not certified.
- Explicit document foreground/background choices remain user formatting and may be hard to read against either palette. Appearance must not silently rewrite them. Native color swatch previews intentionally show the selected formatting colors.
- The startup script reduces an avoidable app flash; it cannot guarantee browser chrome/loading-page color, zero flash under every browser timing condition, or a dark page with JavaScript disabled. The app already requires JavaScript.
- Blocked/cleared browser storage, private browsing, a different browser profile or a changed origin/port can lose the preference. SQLite backups restore notes/templates, not browser appearance preferences.
- Native popup animations remain library defaults. No new product animations were introduced. The few contrast selectors/variables are tied to the pinned editor version and have unit/browser coverage; recheck them during a future library upgrade.
- Visual review used captured real-browser output. A human-operated installed desktop session, fresh Ubuntu installation and physical OS setting change remain owner acceptance work; browser tests emulate the same native media-query events.
- Existing large-build-chunk and testing-library performance notices remain. There was no unrelated dependency or bundle restructuring.
- Installed program files and the real XDG profile remain untouched. After reviewing this candidate, use the existing installer to update the desktop copy; no data migration is required for FF-007. Original-code licensing remains pending as previously requested.

## G. Git commit recommendation

```text
feat(ui): implement persistent application-wide dark mode
```

Includes the authoritative Mantine preference, native editor integration, startup asset, application tokens, accessibility refinements, tests and documentation. No commit or push was performed. Work stops at FF-007 for architectural review.
