"""Derived, local note search. Canonical BlockNote JSON is never rewritten."""

import json
import re
import sqlite3

MAX_QUERY_LENGTH = 200
MAX_QUERY_TERMS = 16
MAX_RESULTS = 50
SEARCH_OBJECTS = {
    "note_search_documents": "table",
    "note_search": "table",
    "note_search_insert": "trigger",
    "note_search_update": "trigger",
    "note_search_delete": "trigger",
}
TEXT_BLOCKS = {
    "paragraph",
    "heading",
    "bulletListItem",
    "numberedListItem",
    "checkListItem",
    "quote",
    "codeBlock",
}


class InvalidSearchQuery(ValueError):
    pass


class SearchIndexError(RuntimeError):
    pass


def _take(text, budget):
    value = text[: budget["text"]]
    budget["text"] -= len(value)
    return value


def _push(pending, items, depth, budget):
    # Bound queued work too, including unexpected/cyclic legacy structures.
    available = max(0, budget["nodes"] - len(pending))
    pending.extend((item, depth) for item in reversed(items[:available]))


def _inline(content, budget):
    if isinstance(content, str):
        return _take(content, budget)
    pending = []
    if isinstance(content, list):
        _push(pending, content, 0, budget)
    parts = []
    while pending and budget["nodes"] and budget["text"]:
        item, depth = pending.pop()
        budget["nodes"] -= 1
        if not isinstance(item, dict) or depth > 128:
            continue
        if item.get("type") == "text" and isinstance(item.get("text"), str):
            parts.append(_take(item["text"], budget))
        elif item.get("type") == "link" and isinstance(item.get("content"), list):
            _push(pending, item["content"], depth + 1, budget)
    # A word may span differently styled runs: do not insert spaces between them.
    return "".join(parts)


def extract_text(document):
    """Return (headings, body), ignoring metadata and malformed structures.

    Bounds also make this safe to use on legacy JSON outside API validation.
    Traversal is iterative and never mutates source blocks or inline runs.
    """
    if not isinstance(document, list):
        return "", ""
    budget = {"nodes": 100_000, "text": 1_048_576}
    headings, body = [], []
    pending = [(block, 0) for block in reversed(document[:5000])]
    while pending and budget["nodes"] and budget["text"]:
        block, depth = pending.pop()
        budget["nodes"] -= 1
        if not isinstance(block, dict) or depth > 32:
            continue
        kind = block.get("type")
        if isinstance(kind, str) and kind in TEXT_BLOCKS:
            text = _inline(block.get("content"), budget)
            (headings if kind == "heading" else body).append(text)
        elif kind == "image" and isinstance(block.get("props"), dict):
            for field in ("caption", "name"):
                text = block["props"].get(field)
                if isinstance(text, str):
                    body.append(_take(text, budget))
        children = block.get("children")
        if isinstance(children, list):
            _push(pending, children[:5000], depth + 1, budget)
    return "\n".join(headings), "\n".join(body)


def index_note(connection, row):
    headings, body = extract_text(json.loads(row["document_json"]))
    connection.execute(
        """INSERT INTO note_search_documents
           (note_id, title, headings, body, indexed_revision) VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(note_id) DO UPDATE SET title=excluded.title,
               headings=excluded.headings, body=excluded.body,
               indexed_revision=excluded.indexed_revision""",
        (row["id"], row["title"], headings, body, row["revision"]),
    )


def create_index(connection):
    """Called inside the caller's migration/rebuild transaction; never commits."""
    connection.execute("""CREATE TABLE note_search_documents (
        id INTEGER PRIMARY KEY,
        note_id TEXT NOT NULL UNIQUE REFERENCES notes(id) ON DELETE CASCADE,
        title TEXT NOT NULL, headings TEXT NOT NULL, body TEXT NOT NULL,
        indexed_revision INTEGER NOT NULL CHECK (indexed_revision >= 1)
    )""")
    try:
        connection.execute("""CREATE VIRTUAL TABLE note_search USING fts5(
            title, headings, body, content='note_search_documents',
            content_rowid='id', tokenize='unicode61 remove_diacritics 2',
            prefix='2 3 4'
        )""")
    except sqlite3.OperationalError as error:
        if "no such module: fts5" in str(error):
            raise SearchIndexError(
                "This Python SQLite runtime requires FTS5 support."
            ) from None
        raise
    # Individual execute calls preserve the enclosing transaction (no executescript).
    connection.execute("""CREATE TRIGGER note_search_insert
        AFTER INSERT ON note_search_documents BEGIN
        INSERT INTO note_search(rowid,title,headings,body)
        VALUES(new.id,new.title,new.headings,new.body); END""")
    connection.execute("""CREATE TRIGGER note_search_delete
        AFTER DELETE ON note_search_documents BEGIN
        INSERT INTO note_search(note_search,rowid,title,headings,body)
        VALUES('delete',old.id,old.title,old.headings,old.body); END""")
    connection.execute("""CREATE TRIGGER note_search_update
        AFTER UPDATE ON note_search_documents BEGIN
        INSERT INTO note_search(note_search,rowid,title,headings,body)
        VALUES('delete',old.id,old.title,old.headings,old.body);
        INSERT INTO note_search(rowid,title,headings,body)
        VALUES(new.id,new.title,new.headings,new.body); END""")
    for row in connection.execute("SELECT * FROM notes ORDER BY id"):
        index_note(connection, row)
    verify_index(connection)


def require_index(connection):
    objects = dict(
        connection.execute(
            "SELECT name,type FROM sqlite_master WHERE name LIKE 'note_search%'"
        ).fetchall()
    )
    if any(objects.get(name) != kind for name, kind in SEARCH_OBJECTS.items()):
        raise SearchIndexError("Search index is missing. Stop CyrNava and rebuild it.")


def verify_index(connection):
    require_index(connection)
    missing = connection.execute("""SELECT 1 FROM notes n
        LEFT JOIN note_search_documents d ON d.note_id=n.id
        WHERE d.id IS NULL OR d.indexed_revision!=n.revision OR d.title!=n.title
        LIMIT 1""").fetchone()
    if missing or connection.execute("PRAGMA foreign_key_check").fetchone():
        raise SearchIndexError("Search index does not match the saved notes.")
    # This FTS5 command checks its inverted index against the external content.
    # It belongs in writable migration/rebuild transactions, not read-only backups.
    connection.execute(
        "INSERT INTO note_search(note_search, rank) VALUES('integrity-check', 1)"
    )


def rebuild_index(connection):
    """Replace derived objects only. Caller owns locking, validation and commit."""
    for name in ("note_search_insert", "note_search_update", "note_search_delete"):
        connection.execute(f"DROP TRIGGER IF EXISTS {name}")
    connection.execute("DROP TABLE IF EXISTS note_search")
    connection.execute("DROP TABLE IF EXISTS note_search_documents")
    create_index(connection)


def prepare_query(query):
    if len(query) > MAX_QUERY_LENGTH:
        raise InvalidSearchQuery("Search query must be at most 200 characters.")
    if any((ord(c) < 32 and not c.isspace()) or ord(c) == 127 for c in query):
        raise InvalidSearchQuery(
            "Search query contains unsupported control characters."
        )
    try:
        query.encode("utf-8")
    except UnicodeError:
        raise InvalidSearchQuery(
            "Search query must contain valid Unicode text."
        ) from None
    terms = re.findall(r"[^\W_]+", query, re.UNICODE)
    if len(terms) > MAX_QUERY_TERMS:
        raise InvalidSearchQuery("Search query must contain at most 16 terms.")
    terms = list(dict.fromkeys(terms))
    # FTS grammar is separate from SQL binding. No raw query syntax reaches MATCH.
    expression = " AND ".join('"' + term.replace('"', '""') + '"*' for term in terms)
    return query.strip(), terms, expression


def _snippet(text, terms):
    if len(text) <= 280:
        return text
    match = re.search("|".join(re.escape(term) for term in terms), text, re.IGNORECASE)
    start = max(0, match.start() - 60) if match else 0
    end = start + 280
    return ("…" if start else "") + text[start:end] + ("…" if end < len(text) else "")


def search_notes(connection, query, limit=20):
    if type(limit) is not int or not 1 <= limit <= MAX_RESULTS:
        raise InvalidSearchQuery("Search limit must be between 1 and 50.")
    query, terms, expression = prepare_query(query)
    if not terms:
        return {"query": query, "total": 0, "results": []}
    require_index(connection)
    total = connection.execute(
        "SELECT COUNT(*) FROM note_search WHERE note_search MATCH ?", (expression,)
    ).fetchone()[0]
    rows = connection.execute(
        """SELECT n.id AS note_id, n.title, n.folder_id,
        snippet(note_search,-1,'','',' … ',24) AS snippet,
        bm25(note_search,10,4,1) AS score
        FROM note_search JOIN note_search_documents d ON d.id=note_search.rowid
        JOIN notes n ON n.id=d.note_id WHERE note_search MATCH ?
        ORDER BY CASE WHEN n.title = ? COLLATE NOCASE THEN 0 ELSE 1 END,
                 bm25(note_search,10,4,1), n.id LIMIT ?""",
        (expression, query, limit),
    ).fetchall()
    parents = {
        row["id"]: (row["parent_id"], row["name"])
        for row in connection.execute("SELECT id,parent_id,name FROM folders")
    }
    results = []
    for row in rows:
        path, seen, current = [], set(), row["folder_id"]
        while current is not None:
            if current in seen or current not in parents:
                raise SearchIndexError("Saved folder hierarchy is invalid.")
            seen.add(current)
            current, name = parents[current]
            path.append(name)
        results.append(
            {
                "note_id": row["note_id"],
                "title": row["title"],
                "folder_path": list(reversed(path)),
                "snippet": _snippet(row["snippet"], terms),
                "score": row["score"],
            }
        )
    return {"query": query, "total": total, "results": results}
