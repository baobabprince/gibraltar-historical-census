#!/usr/bin/env python3
"""Build slim JSON files for the GitHub Pages frontend.

Keeps only fields needed for search/display so the site stays small and
Pages deploys stay under the 10-minute limit.
"""
from __future__ import annotations

import json
from pathlib import Path

SLIM_KEYS = [
    "year",
    "id",
    "surname",
    "forename",
    "sex",
    "age",
    "birthplace",
    "occupation",
    "street",
    "houseNo",
    "familyRelationship",
    "religion",
    "maritalStatus",
]

STREET_ALIASES = ("street", "address", "streetName", "streetname")


def slim_record(r: dict) -> dict:
    row = {}
    for k in SLIM_KEYS:
        v = r.get(k)
        if v is not None and v != "":
            row[k] = v
    if "street" not in row:
        for alt in STREET_ALIASES:
            if r.get(alt):
                row["street"] = r[alt]
                break
    return row


def main() -> None:
    data_root = Path("data")
    index_years = []

    for year_dir in sorted(data_root.iterdir()):
        if not year_dir.is_dir():
            continue
        if not year_dir.name.isdigit():
            continue
        year = int(year_dir.name)
        src = year_dir / "records.json"
        if not src.exists():
            continue

        records = json.loads(src.read_text(encoding="utf-8"))
        slim = [slim_record(r) for r in records]
        out = year_dir / "records.slim.json"
        out.write_text(
            json.dumps(slim, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )

        meta_path = year_dir / "meta.json"
        complete = False
        total = None
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            total = meta.get("total_in_source")
            extracted = meta.get("extracted", len(slim))
            complete = bool(total and extracted >= total)

        index_years.append(
            {
                "year": year,
                "file": f"data/{year}/records.slim.json",
                "count": len(slim),
                "complete": complete,
                "total_in_source": total,
            }
        )
        print(f"  {year}: {len(slim)} records -> {out} ({out.stat().st_size:,} bytes)")

    index_path = data_root / "index.json"
    index_path.write_text(
        json.dumps({"years": index_years}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {index_path} with {len(index_years)} years")


if __name__ == "__main__":
    main()
