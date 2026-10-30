"""Synthetic-only P3 measurements; never accepts an existing workspace."""

import argparse
import hashlib
import io
import json
import resource
import tempfile
import threading
import time
from pathlib import Path

from PIL import Image

from app.assets import AssetStore
from app.database import Database
from app.migration import migrate, pack, unpack


def dataset(root, count):
    db = Database(root / "engage.sqlite3")
    db.initialize()
    store = AssetStore(db)
    parent = db.create_folder("Synthetic migration", None)
    child = parent
    for index in range(count):
        child = (
            db.create_folder(f"Folder {index}", parent["id"])
            if index % 20 == 0
            else child
        )
        note = db.create(
            f"Synthetic {index}",
            [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "Measured synthetic content. " * 20,
                            "styles": {"bold": True},
                        }
                    ],
                }
            ],
            1,
            child["id"],
        )
        data = io.BytesIO()
        # Deterministic noise: representative nontrivially sized screenshot bytes.
        pixels = hashlib.shake_256(str(index).encode()).digest(128 * 128 * 3)
        Image.frombytes("RGB", (128, 128), pixels).save(data, format="PNG")
        asset = store.upload(note["id"], data.getvalue(), "image/png")
        document = [
            *note["document_json"],
            {"type": "image", "props": {"url": asset["url"]}},
        ]
        db.update(note["id"], 1, {"document_json": document})
    return db


def measure(count):
    with tempfile.TemporaryDirectory(prefix="cyrnava-p3-benchmark-") as tmp:
        root = Path(tmp)
        source = root / "source"
        dataset(source, count)
        baseline = sum(p.stat().st_size for p in root.rglob("*") if p.is_file())
        peaks = [baseline]
        stop = threading.Event()

        def monitor():
            while not stop.wait(0.01):
                total = 0
                for p in root.rglob("*"):
                    try:
                        if p.is_file():
                            total += p.stat().st_size
                    except FileNotFoundError:
                        pass
                peaks.append(total)

        thread = threading.Thread(target=monitor)
        thread.start()
        try:
            start = time.perf_counter()
            backup = root / "verified.cyrnava"
            pack(source, backup)
            backup_seconds = time.perf_counter() - start
            stage = root / "verification"
            stage.mkdir()
            start = time.perf_counter()
            unpack(backup, stage)
            verify_seconds = time.perf_counter() - start
            import shutil

            shutil.rmtree(stage)
            start = time.perf_counter()
            result = migrate(backup, root / "restored")
            restore_seconds = time.perf_counter() - start
        finally:
            stop.set()
            thread.join()
        return {
            "status": "PASS",
            "notes": count,
            "images": count,
            "source_bytes": baseline,
            "archive_bytes": backup.stat().st_size,
            "backup_seconds": round(backup_seconds, 3),
            "verify_seconds": round(verify_seconds, 3),
            "restore_seconds": round(restore_seconds, 3),
            "migration_status": result["status"],
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "sampled_peak_disk_bytes": max(peaks),
            "sampled_additional_disk_bytes": max(peaks) - baseline,
            "disk_sample_interval_ms": 10,
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notes", type=int, choices=[10, 250, 1500], required=True)
    args = parser.parse_args()
    print(json.dumps(measure(args.notes), indent=2))


if __name__ == "__main__":
    main()
