# Native document format 1

BlockNote JSON remains canonical. Database schema 3 and document format 1 are unchanged; this repair changes validation, not storage. No migration is necessary. SQLite stores and retrieves JSON without conversion to HTML/Markdown or removal of properties.

The editor schema lives inside the adapter at `frontend/src/components/editorSchema.ts`. The backend's `app/document_format_v1.json` is a serializable snapshot of that installed schema. `app/documents.py` interprets its block content kinds, property scalar types/enums and styles. The frontend contract test compares the snapshot with the exact adapter schema, so a dependency/configuration change fails visibly rather than silently drifting.

After a reviewed editor update, from `frontend/` run:

~~~bash
npm run document:contract
npm test
npm run build
~~~

Review the contract diff and run the backend compatibility tests and browser journeys too. This command does not authorize new resource types or change the document format version. New blocks using existing inline/plain/none content and scalar properties generally need only a reviewed contract update. A new content representation (for example tables or custom inline objects) or a new resource type requires explicit validation/rendering/security support before enabling it. Never generate a contract from a client-supplied request.

Current boundary: eight configured block types; heading levels 1–6; optional toggle-heading flag; text/link inline content; seven installed inline styles. The adapter excludes table, divider, toggle-list, video, audio and generic file blocks. The slash menu exposes 17 commands; H4–H6 and toggle-heading commands use the same heading block, not separate block types. Emoji is ordinary Unicode text. The default picker now uses already-installed emoji-mart packages and bundled local data; no dependency versions changed.

Validation retains the 1 MiB serialized UTF-8 limit, 5,000-block limit, 32-level block nesting limit and unique nonempty supplied IDs. All JSON, including extension metadata, also has finite-number, 128-level nesting and 100,000-item bounds. Known properties/styles have strict scalar types and enum checks. Links reject executable/unsupported schemes. Images accept only local CyrNava asset URLs, and the existing database transaction checks asset ownership even for nested blocks.

Additional block metadata and unknown properties are retained unchanged by the API under the JSON limits. This does not promise that an unmodified BlockNote schema can render arbitrary custom properties: only properties emitted/supported by the installed adapter have an editor round-trip guarantee. Unsupported block/inline/style types and non-native content shapes are rejected. The API accepts partial blocks used for empty-note creation, but editor-generated full JSON is the canonical round-trip representation. BlockNote fills omitted defaults/IDs for partial input. Undefined JavaScript properties (including image content) are absent from serialized JSON. Toggle open/closed state is per-browser view state in BlockNote local storage, while toggle identity and all children are document data.

Validation errors return field paths, reasons and error types, excluding Pydantic's input/context fields. The HTTP client displays those details with the existing Save Error/Retry flow. Note text, URLs and IDs are not included by the document validator in error reasons. Autosave's 700 ms debounce, serial request queue, local edit generations, manual retry, navigation flush and database revision checks are unchanged.

See [repair report](../BLOCKNOTE_COMPATIBILITY_REPORT.md) for the matrix, actual test results, backup details and remaining checks.
