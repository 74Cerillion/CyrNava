# CyrNava rebranding and Ubuntu migration preparation

Date: 2026-10-29. Implementation is ready for owner review. The actual checkout has not been renamed, its origin has not been changed, the installed program has not been updated, and no commits or pushes were made.

## A. Implementation summary

The application header, browser title, FastAPI title, desktop/menu messages, current guides, package metadata, diagnostic messages and synthetic documentation screenshots now use **CyrNava**. The frontend package is `cyrnava`. New environment variables use `CYRNAVA_*`, with existing `ENGAGE_*` aliases retained for compatibility. Styling and application functionality are preserved. No dependencies or pinned versions changed.

The executable `migrate_to_cyrnava.sh` prepares the owner-controlled local transition. It accepts the repository path, supports a read-only dry run, verifies private backups before moving the checkout, preserves HTTPS/SSH, checks Git HEAD/branch/status, and safely recognizes an already-completed migration. Read the [full Ubuntu guide](docs/migrate-to-cyrnava.md) before running it. The script has been executed only against synthetic test repositories/profiles.

## B. Complete file inventory

Paths below are relative to this repository. “Compatibility” changes are comments or aliases; persistent identifiers remain unchanged.

| File | Responsibility and reason for change |
|---|---|
| `.gitignore` | Ignore newly named sensitive draft/conflict exports and retained old venv directories; retain legacy exclusions. |
| `README.md` | Current branding, clone URL, canonical environment variables, and compatibility/migration overview. |
| `BACKUP_RESTORE.md` | Current human-facing name while preserving established backup filenames and commands. |
| `CHANGELOG.md` | Unreleased rebranding entry and historical-release clarification. |
| `REBRANDING_REPORT.md` | This implementation, compatibility, validation and limitation record. |
| `migrate_to_cyrnava.sh` | New executable Bash entrypoint with a Python 3.12 helper; uses Git/GNU tar/mv and existing backup validation. |
| `backend/app/__main__.py` | Current name in the existing application CLI description. |
| `backend/app/main.py` | FastAPI application title; routes and persistence contract unchanged. |
| `backend/app/database.py` | Current error messages and explanation of stable legacy default data paths. |
| `backend/app/documents.py` | Current name in local-image validation errors; canonical JSON unchanged. |
| `backend/app/backup.py` | Current CLI/help/error wording; existing offline backup/restore behavior retained. |
| `backend/app/profile.py` | Current name in profile-lock diagnostics. |
| `backend/app/lifecycle.py` | Current lifecycle messages and canonical private supervisor header with legacy-header fallback. |
| `backend/tests/test_health.py` | Assert the FastAPI title is CyrNava. |
| `backend/tests/test_release.py` | Rebranded synthetic release fixtures/assertions. |
| `backend/tests/test_desktop.py` | Assert CyrNava/Stop CyrNava desktop display names and retain stable desktop IDs. |
| `backend/tests/test_lifecycle.py` | Verify the canonical supervisor header; legacy header coverage retained. |
| `backend/tests/test_rebranding_migration.py` | New 15-case synthetic migration/dry-run/data-preservation/refusal suite. |
| `desktop/install.py` | Current menu/help/error text, renamed default icon, stable installation IDs and custom-icon preservation. |
| `desktop/launcher.py` | Current messages/readiness identity and canonical supervisor variable/header with legacy variable fallback. |
| `desktop/icons/engage.svg` → `desktop/icons/cyrnava.svg` | Rename the existing placeholder asset and its accessible label; artwork unchanged. |
| `desktop/icons/README.md` | Explain placeholder naming and preservation of configured owner icons. |
| `docs/architecture.md` | Current application name; existing architecture preserved. |
| `docs/dependencies-and-licenses.md` | Current application name; pending project-license decision unchanged. |
| `docs/desktop-launcher.md` | Current menu/launcher name; established paths and operational commands retained. |
| `docs/document-format.md` | Current name in local asset documentation; format unchanged. |
| `docs/python-third-party-notices.txt` | Own document heading rebranded; third-party license text unchanged. |
| `docs/release-notes-v0.1.0.md` | Current name in the release draft. |
| `docs/migrate-to-cyrnava.md` | New exact Ubuntu commands, preconditions, backup contents, environment rebuild, VS Code and rollback guide. |
| `docs/screenshots/workspace.png` | Regenerated synthetic workspace with current branding. |
| `docs/screenshots/hierarchy.png` | Regenerated synthetic navigation with current branding. |
| `docs/screenshots/rich-text.png` | Regenerated synthetic rich-text example with current branding. |
| `docs/screenshots/images.png` | Regenerated synthetic local-image example with current branding. |
| `frontend/index.html` | Browser title CyrNava. |
| `frontend/package.json` | Package name `cyrnava` and canonical release-test environment variable. |
| `frontend/package-lock.json` | Match the two root package-name fields; no resolution/version changes. |
| `frontend/vite.config.ts` | Canonical `CYRNAVA_API_PORT` with legacy fallback and existing localhost proxy. |
| `frontend/src/viteConfig.test.ts` | Four default/legacy/canonical-precedence/invalid-value checks. |
| `frontend/src/App.tsx` | Visible application heading; document retained browser-storage keys. |
| `frontend/src/appearance.tsx` | Explain retained preference key; theme behavior unchanged. |
| `frontend/src/drafts.ts` | Rebrand downloaded draft names; retain browser recovery key. |
| `frontend/src/components/ConflictRecovery.tsx` | Rebrand downloaded conflict export names; recovery behavior unchanged. |
| `frontend/src/hooks/useLifecycle.ts` | Current name in stopped/relaunch messages. |
| `frontend/public/third-party-notices.txt` | Own heading/introduction rebranded; third-party notices unchanged. |
| `frontend/e2e/workspace.spec.ts` | Canonical release/API variables with legacy release alias, real title/header assertions, rebranded synthetic fixtures. |
| `frontend/e2e/lifecycle.spec.ts` | Rebrand temporary test-directory prefix; browser recovery identifiers remain compatible. |

## C. Branding audit

Case-insensitive searches covered source, configuration, scripts, documentation, tests and tracked filenames. Replacements were targeted. Generic “engagement” terminology and user content were not renamed.

Remaining ENGAGE identifiers are intentional:

- Data, lock, backup/staging filenames, asset ownership and desktop/state paths are compatibility contracts described below.
- `ENGAGE_API_PORT`, `ENGAGE_E2E_RELEASE`, `ENGAGE_SUPERVISOR_SECRET` and `X-ENGAGE-Supervisor` are compatibility aliases. Canonical settings take priority.
- Old GitHub URL text identifies the accepted previous remote in migration code/tests; actual local origin remains unchanged pending owner execution.
- The migration guide identifies the old **Stop ENGAGE** menu entry so the owner can stop the existing installed version.
- Synthetic migration tests intentionally store a note titled `ENGAGE saved note` to verify that user-authored titles are not rewritten.
- Historical milestone reports/verification records, ADR-004, and the older source-verification hash manifest remain dated evidence. They are not current application branding. README/changelog identify the current guides. Git history is untouched.

No unintended whole-word ENGAGE display text remains in current application source, desktop code, HTML entrypoint or shipped notices. The existing default icon artwork remains a placeholder; this task did not invent a new logo. Owner-configured icons remain selected on reinstall.

## D. Data preservation assessment

Rebranding does not require moving the live profile or changing SQLite schema 4/native document format 1. The default profile remains `$XDG_DATA_HOME/engage/` when XDG_DATA_HOME is absolute, otherwise `~/.local/share/engage/`. It contains `engage.sqlite3`, `assets/` and `.engage.lock`. Notes, hierarchy and custom templates remain in SQLite; template image snapshots remain database BLOBs, and uploaded note images remain owned local files. No user titles/documents are rewritten.

Existing `engage-application` installation configuration/program releases and `engage-launcher` state/log directories remain stable. The migration helper respects the saved installation `data_home`; a custom profile can be supplied explicitly with `--data-dir`. Review its printed path before proceeding.

Browser identifiers remain `engage.note-id.v1`, `engage.navigation-collapsed.v1`, `engage.appearance.v1` and `engage.recovery.v1:`. Preferences/drafts depend on retaining the same browser profile and origin, including port. They are not contained in an SQLite backup. The desktop installer retains existing `org.engage.*.desktop` IDs and updates their displayed names instead of adding duplicates.

The migration script holds the existing profile lock and uses the application's existing integrity, foreign-key, document, image and backup-manifest checks. Source is archived with `.git` and ignored configuration before renaming; only rebuildable active environments/output are excluded. Backups are private but unencrypted. The original profile is neither moved, modified nor deleted. WAL headers/sidecars cause a refusal: current app profiles use rollback journals, and an unexpected WAL profile requires separate reviewed recovery/checkpointing, not an unsafe copy.

## E. Migration script design

The complete executable is [migrate_to_cyrnava.sh](migrate_to_cyrnava.sh). The final chat handoff also includes it verbatim. It does not download anything or contact GitHub.

Preflight checks expected repository owner/project and local runtime, branch/HEAD, clean Git status, supported origin transport, in-progress Git operations, destination conflicts, active repository working directories, safe separate profile/backup paths and available space. The shell validates the origin before executing repository-local Python. Source archives are compared with the original and checksummed. Existing profile backups use the established manifest. Renaming uses non-replacement semantics. Postchecks verify unchanged HEAD/branch, expected origin and clean status. A completion record permits reviewed manual rollback.

The helper uses the existing Python environment because reliable JSON, path, process, SQLite-profile and manifest validation already exist there. This avoids new dependencies and an independent backup format. The Bash entrypoint remains directly executable on Ubuntu. Unsupported worktrees, submodules, custom SSH host aliases, URL rewriting, explicit push URLs and symlink paths stop for manual review.

## F. Ubuntu instructions

See [the step-by-step migration guide](docs/migrate-to-cyrnava.md). First review/commit this source yourself, wait for Saved/uploads, stop all app/development processes and close tools in the checkout. Copy the script outside it and invoke it from your home directory. Review `--dry-run` output, especially the profile. After approving it, run with the same arguments without `--dry-run`. The script accepts any repository path; the example uses the current task's path. There is no automatic commit, fetch, push, installation or GitHub rename.

After migration, preserve/rebuild the nonportable Python venv at the new location, install pinned dependencies, test/build, and reinstall the existing desktop program copy with the same XDG environment and port. Dependency installation may require internet; normal application operation and the migration script require no external services.

## G. VS Code

No repository-owned `.vscode/settings.json`, `.vscode/launch.json`, `.vscode/tasks.json` or `.code-workspace` files were found. No global configuration was modified. Reopen the new root with `code "$NEW_REPO"`, recreate terminals, and select its `backend/.venv/bin/python` using **Python: Select Interpreter**. External workspace/debug/task/shortcut paths created by the owner may need manual updates from the old absolute root. Relative `${workspaceFolder}` paths remain valid. The guide provides exact environment rebuild commands.

## H. Actual testing results

All tests below ran against temporary/synthetic profiles, not real application data.

| Executed check | Result |
|---|---|
| Backend `python -m pytest -q` | **227 passed**, one existing Starlette/httpx deprecation warning. |
| Migration cases within backend suite | **15 passed**: read-only dry run; HTTPS/scp SSH/URI SSH; private verified backups; preserved HEAD/branch/profile bytes/note image/custom template; rerun; specific dirty/untracked/conflict/foreign-remote/pushurl/WAL/corrupt/busy/boundary refusals. |
| Frontend `npm test` | **207 passed** across 19 test files. |
| Frontend ESLint and TypeScript | Passed. |
| Production Vite build | Passed; existing large-chunk warning remains. |
| Full Chromium static-release journeys | **8 passed**; includes managed lifecycle, editing/restarts, conflicts, formatting/clipboard/images, templates/navigation and appearance. |
| Additional Chromium development-server appearance journey | **1 passed**, exercising canonical API-port proxy configuration and CyrNava title/header. |
| Firefox static-release appearance and navigation/template journeys | **2 passed**, including preferences, autosave and screenshots. |
| Ruff lint/format | Passed. |
| Bash syntax and Git whitespace checks | Passed. |
| Updated documentation screenshots | All four regenerated from synthetic release journeys and visually inspected for current branding/layout. |

An initial migration-test path check was too broad: tool-created Git metadata surrounded temporary directories and blocked legitimate separate profiles. It was aligned with the existing app backup boundary (separate from the supplied application checkout, with symlinks refused), and tests now assert each refusal's specific reason. No bypass option was added. A writable dedicated temporary directory was required by this session's sandbox. The final full suite passed after these corrections.

Actual desktop installation, GNOME icon trust, the owner's real notes/browser preferences, real checkout rename and real origin update were not executed. Verify those manually after review. Firefox was tested with the two relevant workspace journeys; the full eight-journey suite ran in Chromium, not Firefox. Existing warnings were not hidden and no test dependency upgrades were mixed into this task.

## I. Rollback and remaining risks

The guide covers manual non-overwriting folder/remote reversal using `migration.json`, checksum-verified archive recovery into a new empty directory, and data restoration into a new profile only if actually required. Moving the source folder back does not require replacing user data. The source archive contains reviewed rebranded source before the move; it is not a pre-rebranding Git revision.

M1-style data reliability remains governed by existing autosave/draft/conflict safeguards: wait for Saved/uploads before closing. Close all noncooperating database/file writers too; advisory locks cannot prevent unrelated external tools or sudden hardware failure. Backups contain private configuration and application content and require trusted storage. Keep custom XDG settings and browser port unchanged. Python virtual environments require rebuilding after a move. The installer has retained earlier program releases, but switching one is a separate reviewed operation.

No new product features, data schemas, dependency upgrades or license selection were introduced. The project-license decision remains pending as previously requested.

## J. Final status

Application rebranding and migration preparation are complete for review. The actual checkout is still `outputs/cyber-workspace` on `main`, and its origin is still `https://github.com/74Cerillion/PEngage_Pentest-Engagement-Manager-`. No actual migration/installation or Git publication occurred. Owner actions: review, commit if approved, stop the installed app, dry-run the script, approve/execute migration, rebuild environments, reinstall and verify the existing profile.

Suggested commit: `chore: rebrand ENGAGE as CyrNava and add safe local migration`.
