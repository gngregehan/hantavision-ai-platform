from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_MANIFEST = ROOT / "hantavirus_datasets.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response, destination.open("wb") as handle:
        shutil.copyfileobj(response, handle)


def download_zenodo_record(source: dict[str, Any], out_dir: Path, dry_run: bool) -> list[dict[str, str]]:
    api_url = source.get("apiUrl")
    if not api_url:
        return []
    print(f"[source] {source['id']} -> {api_url}")
    record = read_remote_json(api_url)
    downloads: list[dict[str, str]] = []
    for file_info in record.get("files", []):
        name = file_info.get("key") or file_info.get("filename")
        link = (file_info.get("links") or {}).get("self") or (file_info.get("links") or {}).get("download")
        if not name or not link:
            continue
        target = out_dir / source["id"] / name
        downloads.append({"source": source["id"], "file": name, "url": link, "path": str(target)})
        if dry_run:
            print(f"[dry-run] would download {name} -> {target}")
        elif target.exists():
            print(f"[skip] {target} already exists")
        else:
            print(f"[download] {name}")
            download_file(link, target)
    return downloads


def read_remote_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode("utf-8"))


def download_kaggle_slug(slug: str, out_dir: Path, dry_run: bool) -> dict[str, str]:
    target = out_dir / "kaggle" / slug.replace("/", "__")
    command = ["kaggle", "datasets", "download", "-d", slug, "-p", str(target), "--unzip"]
    if dry_run:
        print(f"[dry-run] {' '.join(command)}")
        return {"source": "kaggle", "slug": slug, "path": str(target), "status": "dry-run"}
    target.mkdir(parents=True, exist_ok=True)
    print(f"[kaggle] {slug}")
    subprocess.run(command, check=True)
    return {"source": "kaggle", "slug": slug, "path": str(target), "status": "downloaded"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Download HantaVision data sources into data/raw.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--include-auxiliary", action="store_true", help="Also download auxiliary non-diagnostic sources.")
    parser.add_argument(
        "--kaggle-slug",
        action="append",
        default=[],
        help="Optional verified Kaggle dataset slug. Use only after checking labels/license.",
    )
    parser.add_argument("--execute", action="store_true", help="Actually download files. Default is dry-run.")
    args = parser.parse_args()

    manifest = read_json(args.manifest)
    dry_run = not args.execute
    args.out_dir.mkdir(parents=True, exist_ok=True)

    downloads: list[dict[str, str]] = []
    for source in manifest.get("primaryTrainingSources", []):
        downloads.extend(download_zenodo_record(source, args.out_dir, dry_run))

    if args.include_auxiliary:
        for source in manifest.get("auxiliaryDiscovery", []):
            if source.get("apiUrl"):
                downloads.extend(download_zenodo_record(source, args.out_dir, dry_run))

    for slug in args.kaggle_slug:
        downloads.append(download_kaggle_slug(slug, args.out_dir, dry_run))

    output = {
        "dryRun": dry_run,
        "downloads": downloads,
        "warning": (
            "Kaggle slugs are not trusted automatically. Only curate them into training data after "
            "manual verification that labels are hantavirus-specific and licensing permits use."
        ),
    }
    report_path = args.out_dir / "download_manifest.json"
    report_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
