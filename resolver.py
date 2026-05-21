#!/usr/bin/env python3
"""Resolve chemical names in CSV files to CAS Registry Numbers via PubChem."""

import argparse
import csv
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CAS_RE = re.compile(r'^\d{2,7}-\d{2}-\d$')
SYNONYMS_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{}/synonyms/JSON"
REQUEST_DELAY = 0.25   # stay within PubChem's 5 req/s guideline
MAX_RETRIES = 3


def resolve_cas(name: str) -> str:
    """Return the first CAS number found in PubChem synonyms, or 'N/A'."""
    url = SYNONYMS_URL.format(urllib.parse.quote(name, safe=""))
    req = urllib.request.Request(url, headers={"User-Agent": "cas-resolver/1.0 (chemical name lookup)"})
    for attempt in range(MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.load(resp)
            synonyms = data["InformationList"]["Information"][0]["Synonym"]
            for syn in synonyms:
                if CAS_RE.match(syn):
                    return syn
            return "N/A"
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return "N/A"
            if attempt < MAX_RETRIES:
                time.sleep(2 ** attempt)
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if attempt < MAX_RETRIES:
                time.sleep(2 ** attempt)
                continue
            raise
    return "N/A"  # unreachable, but satisfies type checkers


def process_file(input_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with input_path.open(newline="") as f_in, output_path.open("w", newline="") as f_out:
        reader = csv.DictReader(f_in)
        fieldnames = list(reader.fieldnames) + ["cas_number"]
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            name = row["Name"]
            cas = resolve_cas(name)
            print(f"  {name!r:40s} -> {cas}")
            row["cas_number"] = cas
            writer.writerow(row)
            time.sleep(REQUEST_DELAY)


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve chemical names to CAS numbers.")
    parser.add_argument("--input-dir", default="input", type=Path)
    parser.add_argument("--output-dir", default="output", type=Path)
    args = parser.parse_args()

    csv_files = sorted(args.input_dir.glob("*.csv"))
    if not csv_files:
        print(f"No CSV files found in {args.input_dir}")
        return

    for csv_file in csv_files:
        print(f"\n{csv_file.name}")
        process_file(csv_file, args.output_dir / csv_file.name)

    print("\nDone.")


if __name__ == "__main__":
    main()
