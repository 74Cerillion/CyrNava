# F-09 backend search benchmark

Measured on 2026-10-29 with the M4 candidate. [Raw aggregate metrics](search-benchmark-results.json)
include every query's match count, median, p95, maximum, sample count, corpus
fingerprint and runtime metadata. No private notes or database files are included.

## Reproduce

From the checkout's `backend/` directory, with its existing virtual environment:

```bash
.venv/bin/python -m benchmarks.search > /tmp/cyrnava-search-benchmark.json
```

Defaults: **100 / 1,000 / 10,000 notes**, seed `20261029`, five warm-up rounds and
30 measured rounds per query. Progress goes to stderr; stdout is JSON. To make a
short diagnostic run instead of the full reference workload:

```bash
.venv/bin/python -m benchmarks.search --sizes 100 --warmups 1 --rounds 5
```

The harness creates private temporary databases under `/tmp` and removes them on
exit. It exposes **no existing-profile/database/path input option**, ignores the
application's XDG profile setting and refuses temporary data inside this checkout.
It requires no internet, services or packages beyond the installed project. Do not
run the reference benchmark alongside builds/browser suites or other heavy work.
The retained result was measured before those test suites, without a concurrent
application writer. This is a development-machine observation, not an isolated
hardware laboratory or a performance guarantee.

## Measurement boundary

The timer wraps `Database.search(query, limit=20)`. Each request opens a **fresh
SQLite connection**, enables foreign keys, takes its read snapshot, prepares the
literal prefix query, counts all matches, ranks/selects/snippets up to 20 rows,
resolves current folder paths, builds Python results and closes the connection.

It **excludes** fixture generation, index construction, HTTP request/response JSON,
browser rendering and the UI's intentional 300 ms debounce. Filesystem caches are
warm from seeding/correctness/warm-up calls; a fresh connection is not cold-disk
I/O. No performance PRAGMAs, global SQLite settings, journal changes, FTS optimize
commands or runtime application tuning were introduced for the measurement.

Queries are deterministically shuffled each round. Reported p95 is nearest-rank
`ceil(0.95 * n)` on the 30 samples, not an average. Query totals are verified against
known synthetic counts before timing. No wall-clock threshold is asserted by the
ordinary automated tests; they check harness correctness/isolation instead.

## Corpus

- Valid native format-1 BlockNote JSON: paragraphs, H1–H6, nested bullet/numbered/
  check lists, styled inline text, link display text, code commands, technical IPs,
  Unicode, quotes and placeholder image captions/names. No images are downloaded
  or decoded by search; no note text is executed.
- Deterministic varied text, UUIDs and metadata: observed JSON sizes **1,363–6,100
  bytes**, mean about **3.20 KiB** at 10,000 notes. This does not model every near-
  1 MiB document or a private operational corpus.
- Ten rotating note-title topics; about 10% root notes, the rest spread across
  folders with up to three levels. Datasets have 10 / 100 / 1,000 folders.
- Body terms occur in approximately 1%, 10% and 50% of notes. There are exact and
  partial title matches, heading/code/technical/Unicode queries, a unique term,
  misses and a metadata-only term that must remain unsearchable.
- Nested prefix `enum` deliberately matches every note. Two separately labeled
  broad stress queries also match every note, including one-character `e`.
- Fixture insertion is one setup-only bulk transaction using the production
  `index_note` helper/triggers and native validation; it does not benchmark normal
  note-save throughput. The document/title/ID fingerprint identifies the generated
  text corpus; folder counts/configuration are recorded separately.

At 10,000 notes the SQLite file is **86,286,336 bytes** (about 82.3 MiB), containing
canonical documents plus the derived projection, FTS postings and SQLite overhead.
There are no real evidence image files/template BLOBs in this benchmark. Setup/
validation/indexing took approximately **4.20 seconds**, outside all query samples.

## Observed results

Runtime: Python **3.12.15**, SQLite **3.46.1**, Linux x86_64, eight logical CPUs;
DELETE journal mode, 4,096-byte pages. Full OS/runtime strings and the source
fingerprint are in the JSON. These numbers are backend milliseconds.

| Notes | Highest typical-query median | Highest typical-query p95 | Highest broad-stress p95 | Target comparison |
| ---: | ---: | ---: | ---: | --- |
| 100 | 0.94 | 1.51 | 2.29 | Small corpus returned within a few backend milliseconds |
| 1,000 | 3.33 | 4.51 | 6.51 | Below the 100 ms typical-query target on this machine |
| 10,000 | 25.44 | 26.50 | 37.47 | Below the 250 ms typical-query target on this machine |

Per-query p95 exposes selective versus broad work rather than hiding the expensive
cases inside one pooled mean:

| Query category | Matches at 10,000 | p95 at 100 | p95 at 1,000 | p95 at 10,000 |
| --- | ---: | ---: | ---: | ---: |
| Exact full title | 1 | 0.71 | 0.87 | 1.70 |
| Partial title `network` | 1,000 | 0.72 | 1.48 | 6.00 |
| Heading `discovery` | 3,334 | 1.01 | 2.51 | 13.10 |
| Rare body term | 100 | 0.62 | 1.04 | 3.00 |
| Medium body term | 1,000 | 0.77 | 1.72 | 5.83 |
| Common body term | 5,000 | 1.29 | 3.19 | 19.84 |
| Nested prefix `enum` | 10,000 | 1.51 | 4.51 | 26.50 |
| Code AND `nmap -sV` | 1,000 | 0.82 | 1.84 | 6.67 |
| Technical IP | 1,000 | 1.02 | 2.15 | 9.12 |
| Unicode/diacritics | 500 | 0.80 | 1.68 | 4.42 |
| Unique body term | 1 | 0.55 | 0.79 | 1.32 |
| Miss | 0 | 0.47 | 0.72 | 1.49 |
| Metadata-only miss | 0 | 0.46 | 0.67 | 1.51 |
| All-note `evidence` stress | 10,000 | 1.43 | 4.04 | 26.60 |
| One-character `e` stress | 10,000 | 2.29 | 6.51 | 37.47 |

The all-match cases reveal the cost of exact total counting and relevance sorting;
the per-request folder metadata read also grows with the corpus. The results do
not justify an extra cache, background indexer or custom ranking engine now.
Storage speed, CPU contention, cold caches, many more/deeper folders, larger
documents and concurrent saves can produce different timings. Measure before
changing the straightforward implementation.
