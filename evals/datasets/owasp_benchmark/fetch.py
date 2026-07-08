"""Fetch OWASP Benchmark data into ignored local directories.

This script intentionally keeps raw data out of git. It downloads the upstream
archive, records its SHA-256 in `evals/registry.yaml`, extracts it under
`evals/datasets/owasp_benchmark/raw/`, and records the number of rows in
`expectedresults-1.2.csv`.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

import yaml

ARCHIVE_URL = (
    "https://github.com/OWASP-Benchmark/BenchmarkJava/archive/refs/heads/master.zip"
)
DATASET_ID = "owasp_benchmark"
EXPECTED_RESULTS = "expectedresults-1.2.csv"
SCRIPT_DIR = Path(__file__).resolve().parent
EVALS_DIR = SCRIPT_DIR.parents[1]
REGISTRY_PATH = EVALS_DIR / "registry.yaml"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=ARCHIVE_URL)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    downloads_dir = SCRIPT_DIR / "downloads"
    raw_dir = SCRIPT_DIR / "raw"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    archive_path = downloads_dir / "BenchmarkJava-master.zip"

    if archive_path.exists() and not args.force:
        print(f"Using existing archive: {archive_path}")
    else:
        print(f"Downloading {args.url}")
        urlretrieve(args.url, archive_path)

    checksum = _sha256(archive_path)
    extract_dir = raw_dir / "BenchmarkJava-master"
    if extract_dir.exists() and args.force:
        shutil.rmtree(extract_dir)
    if not extract_dir.exists():
        with zipfile.ZipFile(archive_path) as zf:
            zf.extractall(raw_dir)

    expected_results = _find_expected_results(extract_dir)
    n_cases = _count_cases(expected_results)
    _update_registry(checksum=checksum, n_cases=n_cases)
    print(f"sha256={checksum}")
    print(f"n_cases={n_cases}")
    print(f"raw_dir={extract_dir}")
    return 0


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _find_expected_results(raw_dir: Path) -> Path:
    matches = sorted(raw_dir.glob(f"**/{EXPECTED_RESULTS}"))
    if not matches:
        raise FileNotFoundError(f"{EXPECTED_RESULTS} not found under {raw_dir}")
    return matches[0]


def _count_cases(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def _update_registry(*, checksum: str, n_cases: int) -> None:
    registry = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8")) or {}
    datasets = registry.setdefault("datasets", {})
    dataset = datasets.setdefault(DATASET_ID, {})
    dataset["checksum_algorithm"] = "sha256"
    dataset["checksum"] = checksum
    dataset["checksum_target"] = "source_archive"
    dataset["n_cases"] = n_cases
    REGISTRY_PATH.write_text(
        yaml.safe_dump(registry, sort_keys=False),
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())

