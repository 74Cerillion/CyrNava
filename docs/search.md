# F-09 — local full-text search

M2 provides the search API and persistence machinery; M3 adds the navigation-pane
interface and safe result navigation. M4 engineering validation covers integration,
migration/rebuild, offline checks and a reproducible synthetic benchmark. See the
[M4 report](../F09_M4_REPORT.md), [benchmark results](search-benchmark.md) and
[release checklist](search-release-checklist.md). No new dependencies are installed.
Owner commit/publication and existing license gates remain pending.

## Using global search

Type in **Search all notes...** near the top of the navigation pane. After 300 ms
without another query edit, the app searches all saved notes, regardless of folder
selection. Result cards show the note title, current folder path (or Workspace
root) and a short preview. Matching word prefixes are highlighted with React text
nodes; snippets are never interpreted as HTML. Highlighting is approximate and
does not duplicate FTS Unicode/diacritic normalization. The first 20 ranked
matches are shown; if there are more, refine the query. Scores are not displayed.

With focus in the search field, ↑/↓ select a result and Enter opens it. Enter also
opens the first ready result when no explicit result is selected. Escape anywhere
in the search controls or **Clear search** clears the field/results and focuses
the field, leaving the current note open. Mouse/touch activation works too. There
is no global shortcut to intercept BlockNote typing. Existing tree keys remain
scoped to the tree. A successful transition selects/reveals the note in the tree,
whose existing focus behavior focuses that row. The query remains available for
further searches. Collapsing navigation preserves the mounted search and editor.

Opening a different result first drains pending uploads and serialized saves
through the same guard as tree navigation. Failed saves, conflicts or pending
draft recovery leave the original draft open. The destination comes from the
canonical note API, not a snippet. Its current folder metadata is refreshed before
selection; deleted results/read failures preserve the current editor and report
an error. Selecting the already-open result never remounts the editor. Direct
navigation to a matching block is not implemented.

Search states distinguish waiting, searching, no matches and failures. **Retry
search** retains the query. Input changes/clear immediately abort and invalidate
previous requests; late replies cannot restore older results or errors, even when
a query is repeated. Successful saves and library refreshes rerun the current
query after the debounce; pending typing is not searchable until committed.
Changes made only in another tab need **Refresh library** or another query.
Search queries/results are page memory only, not browser storage or database
preferences; reloading clears them. The API still uses a GET URL, so the request
logging/privacy considerations below apply.

## Contract

`GET /api/search?q=nmap&limit=20`

```json
{
  "query": "nmap",
  "total": 1,
  "results": [{
    "note_id": "a-note-uuid",
    "title": "Nmap Enumeration",
    "folder_path": ["Cybersecurity", "Pentesting"],
    "snippet": "Common nmap enumeration techniques...",
    "score": -0.000002
  }]
}
```

- `q` defaults to empty; at most 200 Unicode characters and 16 word tokens.
  Leading/trailing whitespace is trimmed in the response. Empty, emoji-only or
  punctuation-only input returns no results. Unsupported controls are rejected.
- Words are Unicode letters/numbers separated by punctuation/underscores. Each
  becomes a literal **word prefix** joined with AND. `enum` matches `enumeration`;
  `umeration` does not. `nmap -sV` searches the prefixes `nmap` AND `sV`.
  Quotes/operators are not a user query language: `nmap OR enum` also requires
  the literal prefix `OR`. SQL parameters and FTS syntax escaping are separate.
- Matching is ASCII case-insensitive, with FTS5 `unicode61 remove_diacritics 2`.
  Unicode segmentation/case handling follows that tokenizer; linguistic stemming,
  fuzzy matching and general substring search are not provided.
- `limit` defaults to 20; range 1–50. `total` counts all matches before the limit.
  There is no pagination endpoint in M2.
- Exact full-title matches (ASCII `NOCASE`, after trimming the query) come first.
  Other results use FTS5 BM25 weights **title 10 / headings 4 / body 1**;
  note ID breaks ties. Scores are raw negative BM25 values: **lower is better**,
  not a percentage/probability. Weighting is a relevance preference, not rigid
  buckets that always place any title match above any body match.
- `folder_path` is an array of current folder names, from root to immediate parent;
  a root note has `[]`. Names containing `/` remain unambiguous. Breadcrumbs are
  resolved from the same read snapshot, so folder renames/moves need no reindex.
- Snippets are plain, untrusted text, at most 282 characters including ellipses.
  FTS5 chooses the matching column/window (which may be the title). No HTML
  highlighting is generated. The React consumer renders text safely.
- Successful and validation/error search responses use `Cache-Control: no-store`.
  Invalid input returns 422, unavailable/broken search returns 503 with a rebuild
  hint. Errors do not echo the query or database diagnostics.

The release and desktop entrypoints disable access logging. When running Uvicorn
directly, pass `--no-access-log` to avoid logging search terms in request URLs.
GET queries still appear wherever a client deliberately records URLs (for example
shell history, browser developer tools or custom proxies); no telemetry is added.

## How indexing works

Canonical notes still use native BlockNote `document_json`, format version 1.
`app/search.py::extract_text` reads supported paragraph/list/quote/code blocks,
H1–H6 and nested children, inline text and link display text, image caption/name.
Styled runs concatenate without inserted spaces so formatting cannot split a
word. IDs, styles, link targets and image URLs are ignored. Iterative traversal
caps depth, nodes, queued work and extracted text; malformed legacy structures
are skipped without changing the input. API document validation remains strict.

Schema 5 adds an ordinary `note_search_documents` projection, with integer ID,
unique cascading `note_id`, title, headings, body and `indexed_revision`. The
external-content FTS5 table `note_search` indexes its text using word-prefix
indexes of lengths 2, 3 and 4. Three projection triggers synchronize FTS inserts,
updates and deletes. There is one projection row per note; the FTS shadow tables
are owned by SQLite.

`Database.create`, `Database.update` and `TemplateStore.instantiate` call
`index_note` on their already-open write connection. Revision validation happens
before indexing. Canonical write, projection upsert and FTS trigger changes commit
together; an index failure rolls everything back and the API does not acknowledge
Saved. Deleting a note cascades to the projection and then FTS, including recursive
folder deletion. A failed deletion rolls back all three. Template definitions are
not searched; their instantiated notes are. Out-of-band SQL writers bypassing
these application functions are unsupported and can require rebuilding.

`Database.search` opens one read transaction for count, ranking and breadcrumbs.
The frontend never needs to load all documents to search. No note content is
executed, uploaded or requested from an external service.

## Upgrade safely

1. Wait for **Saved**, close the app and stop every desktop/development backend.
2. Make and retain a verified backup following [backup/restore](../BACKUP_RESTORE.md).
   The updated backup tool supports schemas 3, 4 and 5 before any migration.
3. Start the reviewed updated backend normally. Startup adds the projection,
   FTS table/triggers and existing-note backfill in **one transaction**, then sets
   `PRAGMA user_version=5`. Foreign-key and FTS external-content integrity checks
   must succeed before commit. Canonical note rows are never rewritten by this step.
4. If an old cooperating backend is still running, migration refuses rather than
   allowing that backend to keep saving without the new indexing code. Stop it
   normally and retry. Never remove the lock file to bypass the refusal.
5. Repeat startup leaves one index row per note. A schema-5 profile missing search
   objects fails startup with a repair hint; it is not silently reset. Use rebuild.

The migration holds an exclusive profile lock through commit. Current-schema
startup/serving uses shared locks. Linux `fcntl` locks protect cooperating backends
and tools; external SQLite tools do not participate and must also be stopped.
If the Python SQLite build lacks FTS5, startup fails clearly and rolls migration
back; select a Python/SQLite build with FTS5 rather than installing a new service.

Older application code refuses schema 5. There is **no in-place downgrade**. Use
the retained pre-upgrade backup in a separate profile if returning to old code;
edits made after that backup will not be in the older copy. Existing data paths
remain `$XDG_DATA_HOME/engage/` (absolute XDG value), otherwise
`~/.local/share/engage/`. The search index is private data in the same SQLite file.

## Offline rebuild

Stop all backends. From the checkout's `backend/` directory:

```bash
# Uses the same XDG/default profile as normal startup:
.venv/bin/python -m app.search_index rebuild

# Or identify the complete existing profile directory explicitly:
.venv/bin/python -m app.search_index rebuild \
  --data-dir "/absolute/private/profile/engage"
```

The full directory contains `engage.sqlite3` and `assets/`; it is not the XDG parent.
Do not run both commands unless you intend to rebuild both selected profiles.
The tool rejects running backends, missing profiles, symlinks, repository paths
and non-schema-5 databases. A restored schema-3/4 runtime profile must first be
started with this code to upgrade. It never creates a new profile for a typo.

Rebuild takes an exclusive lock, validates canonical notes/relationships/images
read-only using the existing backup validator, then replaces **only** search
objects inside one transaction. It backfills current saved notes and checks FTS
integrity and indexed revisions before committing. Failure rolls back derived
DDL/data changes; notes, IDs, revisions, timestamps, templates and assets remain
untouched. Success prints `Search index rebuilt and verified` and exits 0; errors
exit 1. Keep backups separate and unchanged.

This repairs missing/stale/logically inconsistent derived search data when the
canonical profile remains healthy. It is not recovery from arbitrary physical
SQLite corruption, missing evidence images, or damaged canonical documents.
Retain the original and consult a verified backup in those cases. Backup validation
does not write FTS integrity commands or promise semantic index consistency.

## Isolated manual API check

After review, use a temporary profile to avoid upgrading your everyday data.
In a terminal, from `backend/`:

```bash
SEARCH_CHECK_HOME="$(mktemp -d /tmp/cyrnava-search-check.XXXXXX)"
XDG_DATA_HOME="$SEARCH_CHECK_HOME" .venv/bin/python -m uvicorn app.main:app \
  --host 127.0.0.1 --port 8011 --no-access-log
```

In another terminal:

```bash
curl --fail-with-body -sS http://127.0.0.1:8011/api/notes \
  -H 'Content-Type: application/json' \
  -d '{"title":"Nmap Lab","document_json":[{"type":"paragraph","content":[{"type":"text","text":"Enumeration with nmap","styles":{}}]}]}'
curl --fail-with-body -sS 'http://127.0.0.1:8011/api/search?q=enum&limit=20'
```

Expect one result with the new note's ID and `folder_path: []`. Stop with Ctrl+C,
restart using the **same** `SEARCH_CHECK_HOME`, and repeat the search. Confirm
native formatting using the UI and repeat the query in its search control if
running a built frontend or the Vite development workflow. For rebuilding, stop that test backend and pass
`--data-dir "$SEARCH_CHECK_HOME/engage"` in the first terminal, then restart it.
Choose another free port if 8011 is occupied. The temporary profile is synthetic;
do not copy private notes into the checkout for tests.
