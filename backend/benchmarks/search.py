"""Synthetic, offline backend benchmark: python -m benchmarks.search.

No existing database/profile option is accepted. JSON metrics go to stdout;
progress goes to stderr. The private temporary fixture is removed on exit.
"""

import argparse
import hashlib
import json
import math
import os
import platform
import random
import sqlite3
import statistics
import sys
import tempfile
from pathlib import Path
from time import perf_counter_ns
from uuid import NAMESPACE_URL, uuid5

from app.database import Database
from app.documents import validate_document
from app.search import index_note, verify_index

SEED = 20261029
TOPICS = (
    "Network reconnaissance",
    "Linux privilege",
    "Windows identity",
    "Web application",
    "Incident triage",
    "Database review",
    "Cloud lab",
    "Endpoint analysis",
    "Wireless lab",
    "Protocol analysis",
)
SENTENCES = (
    "Record the observed service version and compare the result with the baseline.",
    "Keep an explicit scope and document each local observation before continuing.",
    "Review the synthetic response and retain reproducible steps for later study.",
    "Check permissions carefully and explain the result without running note text.",
    "Separate confirmed observations from assumptions and questions still pending.",
)
REPOSITORY = Path(__file__).resolve().parents[2]


def identifier(kind, index, seed):
    return str(uuid5(NAMESPACE_URL, f"cyrnava-search-benchmark/{seed}/{kind}/{index}"))


def block(kind, text, **extra):
    return {
        "type": kind,
        "content": [{"type": "text", "text": text, "styles": {}}],
        "children": [],
        **extra,
    }


def document(index, rng):
    paragraphs = [block("paragraph", "Evidence summary for this synthetic local lab.")]
    for _ in range(rng.randint(1, 12)):
        paragraphs.append(
            block("paragraph", " ".join(rng.choices(SENTENCES, k=rng.randint(1, 5))))
        )
    paragraphs.extend(
        [
            block(
                "heading",
                "Discovery" if index % 3 == 0 else "Findings",
                props={"level": index % 6 + 1},
            ),
            block(
                "bulletListItem",
                "Enumerate the authorized lab",
                children=[
                    block(
                        "numberedListItem",
                        "Inspect the response",
                        children=[
                            block(
                                "checkListItem",
                                "Retain a checklist",
                                props={"checked": True},
                            )
                        ],
                    )
                ],
            ),
            block(
                "codeBlock",
                "nmap -sV 127.0.0.1\n"
                if index % 10 == 0
                else "printf 'local lab only'\n",
                props={"language": "text"},
            ),
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Styled ", "styles": {"bold": True}},
                    {
                        "type": "link",
                        "href": "https://example.invalid/not-fetched",
                        "content": [
                            {"type": "text", "text": "reference", "styles": {}}
                        ],
                    },
                ],
                "children": [],
            },
            block(
                "quote",
                f"canary{index:08d} "
                + ("Café 日本語" if index % 20 == 0 else "Local quotation"),
            ),
        ]
    )
    tags = []
    for divisor, word in (
        (100, "triagesignal"),
        (10, "servicetrace"),
        (2, "commontrace"),
    ):
        if index % divisor == 0:
            tags.append(word)
    paragraphs.append(block("paragraph", " ".join(tags)))
    if index % 10 == 0:
        paragraphs.append(
            {
                "type": "image",
                "props": {
                    "url": "",
                    "name": "diagram.png",
                    "caption": "Synthetic diagram",
                },
                "children": [],
            }
        )
    # Opaque metadata is retained in JSON but must not enter the index.
    paragraphs[0]["benchmark_metadata"] = "metadataonlyneedle"
    return paragraphs


def seed_corpus(database, count, seed):
    """Fixture-only bulk transaction; setup is never part of search timings."""
    rng = random.Random(seed)
    lengths, digest = [], hashlib.sha256()
    folder_ids = [
        identifier("folder", index, seed) for index in range(max(1, count // 10))
    ]
    now = "2026-10-29T00:00:00+00:00"
    with database.connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        for index, folder in enumerate(folder_ids):
            parent = None if index % 3 == 0 else folder_ids[index - 1]
            connection.execute(
                "INSERT INTO folders VALUES(?,?,?,0,?,?)",
                (folder, parent, f"Synthetic folder {index:04d}", now, now),
            )
        for index in range(count):
            value = document(index, rng)
            validate_document(value)
            encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
            lengths.append(len(encoded.encode()))
            title = f"{TOPICS[index % len(TOPICS)]} {index:05d}"
            note_id = identifier("note", index, seed)
            parent = None if index % 10 == 0 else folder_ids[index % len(folder_ids)]
            connection.execute(
                "INSERT INTO notes VALUES(?,?,?,?,1,1,?,?)",
                (note_id, parent, title, encoded, now, now),
            )
            index_note(
                connection,
                {
                    "id": note_id,
                    "title": title,
                    "document_json": encoded,
                    "revision": 1,
                },
            )
            digest.update((note_id + title + encoded).encode())
        verify_index(connection)
    return {
        "notes": count,
        "folders": len(folder_ids),
        "document_bytes": {
            "min": min(lengths),
            "mean": round(statistics.mean(lengths), 2),
            "max": max(lengths),
            "total": sum(lengths),
        },
        "corpus_sha256": digest.hexdigest(),
    }


def queries(count):
    unique = min(42, count - 1)

    def every(divisor):
        return (count - 1) // divisor + 1

    return [
        ("exact_title", f"{TOPICS[unique % len(TOPICS)]} {unique:05d}", 1, "typical"),
        ("partial_title", "network", every(10), "typical"),
        ("heading", "discovery", every(3), "typical"),
        ("body_rare", "triagesignal", every(100), "typical"),
        ("body_medium", "servicetrace", every(10), "typical"),
        ("body_common", "commontrace", every(2), "typical"),
        ("nested_prefix", "enum", count, "typical"),
        ("code_and", "nmap -sV", every(10), "typical"),
        ("technical_ip", "127.0.0.1", every(10), "typical"),
        ("unicode", "cafe 日本語", every(20), "typical"),
        ("unique_body", f"canary{unique:08d}", 1, "typical"),
        ("miss", "nomatchingtokenxyz", 0, "typical"),
        ("metadata_ignored", "metadataonlyneedle", 0, "typical"),
        ("all_notes", "evidence", count, "broad_stress"),
        ("one_character", "e", count, "broad_stress"),
    ]


def distribution(values):
    ordered = sorted(values)
    return {
        "samples": len(values),
        "median_ms": round(statistics.median(values), 4),
        "p95_ms": round(ordered[math.ceil(0.95 * len(values)) - 1], 4),
        "max_ms": round(max(values), 4),
    }


def measure_size(count, seed, warmups, rounds):
    with tempfile.TemporaryDirectory(
        prefix="cyrnava-search-benchmark-", dir="/tmp"
    ) as directory:
        profile = Path(directory).resolve()
        if profile.is_relative_to(REPOSITORY):
            raise RuntimeError("Benchmark data must be outside the repository")
        database = Database(profile / "engage.sqlite3")
        database.initialize()
        started = perf_counter_ns()
        corpus = seed_corpus(database, count, seed)
        corpus["fixture_setup_ms"] = round((perf_counter_ns() - started) / 1_000_000, 3)
        cases = queries(count)
        # Correctness is checked separately, before any measured samples.
        for _, query, expected, _ in cases:
            result = database.search(query)
            if result["total"] != expected or len(result["results"]) != min(
                20, expected
            ):
                raise RuntimeError("Synthetic benchmark result count is incorrect")
        with database.connect() as connection:
            corpus["sqlite"] = {
                "journal_mode": connection.execute("PRAGMA journal_mode").fetchone()[0],
                "page_size": connection.execute("PRAGMA page_size").fetchone()[0],
            }
        corpus["database_bytes"] = database.path.stat().st_size
        samples = {label: [] for label, *_ in cases}
        rng = random.Random(seed + count)
        for iteration in range(warmups + rounds):
            order = list(cases)
            rng.shuffle(order)
            for label, query, _, _ in order:
                started = perf_counter_ns()
                database.search(query, limit=20)
                elapsed = (perf_counter_ns() - started) / 1_000_000
                if iteration >= warmups:
                    samples[label].append(elapsed)
        corpus["queries"] = [
            {
                "label": label,
                "query": query,
                "category": category,
                "matches": expected,
                "returned": min(20, expected),
                **distribution(samples[label]),
            }
            for label, query, expected, category in cases
        ]
        return corpus


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", type=int, nargs="+", default=[100, 1000, 10000])
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--warmups", type=int, default=5)
    parser.add_argument("--rounds", type=int, default=30)
    args = parser.parse_args()
    if (
        any(not 1 <= size <= 10000 for size in args.sizes)
        or not 1 <= args.rounds <= 1000
        or not 0 <= args.warmups <= 100
    ):
        parser.error("Use sizes 1..10000, rounds 1..1000 and warmups 0..100.")
    source = hashlib.sha256()
    for name in (
        "app/database.py",
        "app/search.py",
        "app/documents.py",
        "benchmarks/search.py",
    ):
        source.update(name.encode())
        source.update((REPOSITORY / "backend" / name).read_bytes())
    result = {
        "benchmark_format": 1,
        "seed": args.seed,
        "warmup_rounds": args.warmups,
        "measured_rounds": args.rounds,
        "cache": "warm filesystem cache; fresh connection per search",
        "measurement": (
            "Database.search: connection, snapshot, validation, count, rank, "
            "snippets, folder paths, close; excludes HTTP/JSON/browser/debounce "
            "and fixture setup"
        ),
        "environment": {
            "python": platform.python_version(),
            "sqlite": sqlite3.sqlite_version,
            "os": platform.platform(),
            "logical_cpus": os.cpu_count(),
        },
        "source_sha256": source.hexdigest(),
        "datasets": [],
    }
    for count in args.sizes:
        print(f"Measuring {count} synthetic notes...", file=sys.stderr, flush=True)
        result["datasets"].append(
            measure_size(count, args.seed, args.warmups, args.rounds)
        )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
