import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from benchmarks.search import distribution, measure_size


def test_nearest_rank_percentiles_do_not_hide_slow_samples():
    result = distribution(list(range(1, 101)))
    assert result == {"samples": 100, "median_ms": 50.5, "p95_ms": 95, "max_ms": 100}


def test_corpus_is_deterministic_and_all_benchmark_counts_are_verified():
    first, second = measure_size(20, 42, 0, 1), measure_size(20, 42, 0, 1)
    assert first["corpus_sha256"] == second["corpus_sha256"]
    assert first["document_bytes"] == second["document_bytes"]
    assert len(first["queries"]) == 15
    assert all(row["samples"] == 1 for row in first["queries"])
    assert (
        next(row for row in first["queries"] if row["label"] == "all_notes")["matches"]
        == 20
    )
    assert first["sqlite"]["journal_mode"] == "delete"
    assert measure_size(20, 43, 0, 1)["corpus_sha256"] != first["corpus_sha256"]


def test_benchmark_ignores_real_data_environment_and_removes_temporary_profiles(
    tmp_path, monkeypatch
):
    import benchmarks.search as benchmark

    real = tmp_path / "personal/engage"
    real.mkdir(parents=True)
    sentinel = real / "engage.sqlite3"
    sentinel.write_bytes(b"Do not open a personal profile")
    before = hashlib.sha256(sentinel.read_bytes()).hexdigest()
    monkeypatch.setenv("XDG_DATA_HOME", str(real.parent))
    original = benchmark.tempfile.TemporaryDirectory
    locations = []

    def temporary(*args, **kwargs):
        value = original(*args, **kwargs)
        locations.append(Path(value.name))
        return value

    monkeypatch.setattr(benchmark.tempfile, "TemporaryDirectory", temporary)
    benchmark.measure_size(3, 42, 0, 1)
    assert locations and all(not path.exists() for path in locations)
    assert all(not path.is_relative_to(benchmark.REPOSITORY) for path in locations)
    assert hashlib.sha256(sentinel.read_bytes()).hexdigest() == before


@pytest.mark.parametrize(
    "arguments",
    [
        ["--sizes", "0"],
        ["--sizes", "10001"],
        ["--rounds", "0"],
        ["--warmups", "-1"],
        ["--data-dir", "/tmp/should-not-exist"],
    ],
)
def test_cli_rejects_invalid_sizes_and_existing_profile_options(arguments):
    result = subprocess.run(
        [sys.executable, "-m", "benchmarks.search", *arguments],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2


def test_cli_reports_only_synthetic_metrics():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "benchmarks.search",
            "--sizes",
            "2",
            "--rounds",
            "1",
            "--warmups",
            "0",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    report = json.loads(result.stdout)
    assert report["benchmark_format"] == 1 and len(report["source_sha256"]) == 64
    assert report["datasets"][0]["notes"] == 2
    assert "Measuring 2 synthetic notes" in result.stderr
    assert "/tmp/" not in result.stdout  # No private runtime paths in metrics.
