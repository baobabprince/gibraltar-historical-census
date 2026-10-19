#!/usr/bin/env python3
"""Build slim JSON files for the GitHub Pages frontend.

Normalizes field aliases across census years so search/filters work
consistently, and keeps only fields needed for search/display.
"""
from __future__ import annotations

import json
from pathlib import Path


def first(r: dict, *keys: str):
    for k in keys:
        v = r.get(k)
        if v is not None and v != "":
            return v
    return None


def slim_record(r: dict) -> dict:
    year = r.get("year")
    row = {}
    if year is not None:
        row["year"] = year

    rid = first(r, "id", "listid")
    if rid is not None:
        row["id"] = rid

    surname = first(
        r,
        "surname",
        "surName",
        "tenantsurname",
        "occupantsurname",
        "ownersurname",
        "propietorsurname",
        "name",
    )
    if surname is not None:
        row["surname"] = surname

    forename = first(
        r,
        "forename",
        "foreName",
        "tenantforename",
        "occupantforename",
        "ownerforename",
        "proprietorforename",
    )
    if forename is not None:
        row["forename"] = forename

    sex = first(r, "sex")
    if sex is not None:
        row["sex"] = sex

    age = first(r, "age")
    if age is not None:
        row["age"] = age

    birthplace = first(r, "birthplace", "birthPlace", "country")
    if birthplace is not None:
        row["birthplace"] = birthplace

    occupation = first(
        r,
        "occupation",
        "tradeprofessionoccupation",
        "trade_profession_occupation",
    )
    if occupation is not None:
        row["occupation"] = occupation

    street = first(
        r,
        "street",
        "address",
        "streetName",
        "streetname",
        "situation",
    )
    if street is not None:
        row["street"] = street

    house = first(r, "houseNo", "houseno", "hseNo", "hseno")
    if house is not None:
        row["houseNo"] = house

    rel = first(r, "familyRelationship", "familyrelationship", "relationship")
    if rel is not None:
        row["familyRelationship"] = rel

    religion = first(
        r,
        "religion",
        "nationalityReligion",
        "nationality",
        "nation",
        "nat_reg",
    )
    if religion is not None:
        row["religion"] = religion

    marital = first(r, "maritalStatus", "maritalstatus", "status")
    if marital is not None:
        row["maritalStatus"] = marital

    district = first(r, "district", "districtname")
    if district is not None:
        row["district"] = district

    yor = first(
        r,
        "yearsOfResidence",
        "yearsofresidence",
        "howlongresident",
        "tenantresdncylgth",
    )
    if yor is not None:
        row["yearsOfResidence"] = yor

    notes = first(r, "notes", "remarks", "comments", "notes1")
    if notes is not None:
        row["notes"] = notes

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
