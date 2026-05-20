from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path


ALLOWED_LABELS = {"infected", "non_infected"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}


def stable_bucket(source_id: str, source_path: str) -> str:
    digest = hashlib.sha256(f"{source_id}:{source_path}".encode("utf-8")).hexdigest()
    value = int(digest[:8], 16) / 0xFFFFFFFF
    if value < 0.7:
        return "train"
    if value < 0.85:
        return "val"
    return "test"


def main() -> None:
    parser = argparse.ArgumentParser(description="Curate manually reviewed hantavirus labels into train/val/test folders.")
    parser.add_argument("--labels-csv", type=Path, required=True)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--out-dir", type=Path, default=Path("data/hantavirus"))
    parser.add_argument("--copy", action="store_true", help="Copy files instead of dry-run reporting.")
    args = parser.parse_args()

    rows: list[dict[str, str]] = []
    with args.labels_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"source_id", "relative_path", "label"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"labels CSV is missing columns: {', '.join(sorted(missing))}")
        rows = [row for row in reader]

    report: dict[str, object] = {"copied": 0, "skipped": [], "splits": {"train": 0, "val": 0, "test": 0}}
    for row in rows:
        label = row["label"].strip()
        if label not in ALLOWED_LABELS:
            report["skipped"].append({"row": row, "reason": f"unsupported label {label!r}"})
            continue
        source_path = args.raw_dir / row["source_id"] / row["relative_path"]
        if source_path.suffix.lower() not in IMAGE_EXTENSIONS:
            report["skipped"].append({"row": row, "reason": "not a supported image extension"})
            continue
        if not source_path.exists():
            report["skipped"].append({"row": row, "reason": f"missing file {source_path}"})
            continue
        split = row.get("split") or stable_bucket(row["source_id"], row["relative_path"])
        if split not in {"train", "val", "test"}:
            report["skipped"].append({"row": row, "reason": f"unsupported split {split!r}"})
            continue
        target = args.out_dir / split / label / f"{row['source_id']}__{source_path.name}"
        if args.copy:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target)
        report["copied"] = int(report["copied"]) + 1
        report["splits"][split] = int(report["splits"][split]) + 1

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "curation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
