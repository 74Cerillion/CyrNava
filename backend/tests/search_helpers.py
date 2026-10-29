"""Synthetic historical schemas and canonical snapshots; never real profile data."""


def remove_search_schema(connection):
    for name in ("note_search_insert", "note_search_update", "note_search_delete"):
        connection.execute(f"DROP TRIGGER IF EXISTS {name}")
    connection.execute("DROP TABLE IF EXISTS note_search")
    connection.execute("DROP TABLE IF EXISTS note_search_documents")


def canonical_snapshot(connection):
    return {
        name: connection.execute(f"SELECT * FROM {name} ORDER BY 1,2").fetchall()
        for name in ("notes", "folders", "assets", "templates", "template_images")
    }
