#!/usr/bin/env python3
"""Gibraltar National Archives Inhabitants Register scraper.
Supports all years with FormView sequential navigation (1704–1914).
Automatically resumes from the last extracted record.
"""
from __future__ import annotations
import argparse, csv, json, re, time
from pathlib import Path
from typing import Any
import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Year configuration – all Complete FormView registers
# ---------------------------------------------------------------------------
YEAR_CONFIG: dict[int, dict[str, Any]] = {
    1704: {
        "url": "https://www.nationalarchives.gi/1704.aspx",
        "total": 41,
        "next_target": "ctl00$MainContent$FormView1$ctl01$NextButton",
    },
    1777: {
        "url": "https://www.nationalarchives.gi/1777.aspx",
        "total": 3130,
        "next_target": "ctl00$MainContent$FormView1$ctl01$NextButton",
    },
    1791: {
        "url": "https://www.nationalarchives.gi/1791.aspx",
        "total": 2992,
        "next_target": "ctl00$MainContent$FormView1$ctl01$NextButton",
    },
    1814: {
        "url": "https://www.nationalarchives.gi/1814.aspx",
        "total": 1853,
        "next_target": "ctl00$MainContent$FormView1$ctl01$NextButton",
    },
    1816: {
        "url": "https://www.nationalarchives.gi/1816.aspx",
        "total": 6679,
        "next_target": "ctl00$MainContent$FormView1$ctl01$NextButton",
    },
    1834: {
        "url": "https://www.nationalarchives.gi/1834.aspx",
        "total": 14569,
        "next_target": "ctl00$MainContent$FormView1$ctl01$NextButton",
    },
    1868: {
        "url": "https://www.nationalarchives.gi/1868.aspx",
        "total": 15405,
        "next_target": "ctl00$MainContent$FormView1$ctl01$NextButton",
    },
    1871: {
        "url": "https://www.nationalarchives.gi/1871.aspx",
        "total": 22725,
        "next_target": "ctl00$MainContent$FormView1$ctl01$NextButton",
    },
    1878: {
        "url": "https://www.nationalarchives.gi/1878.aspx",
        "total": 17982,
        "next_target": "ctl00$MainContent$FormView1$ctl01$NextButton",
    },
    1881: {
        "url": "https://www.nationalarchives.gi/1881.aspx",
        "total": 18616,
        "next_target": "ctl00$MainContent$FormView1$ctl01$NextButton",
    },
    1891: {
        "url": "https://www.nationalarchives.gi/1891.aspx",
        "total": 19057,
        "next_target": "ctl00$MainContent$FormView1$ctl01$NextButton",
    },
    1901: {
        "url": "https://www.nationalarchives.gi/1901.aspx",
        "total": 19342,
        "next_target": "ctl00$MainContent$FormView1$ctl01$NextButton",
    },
    1911: {
        "url": "https://www.nationalarchives.gi/1911.aspx",
        "total": 14951,
        "next_target": "ctl00$MainContent$FormView1$ctl01$NextButton",
    },
    1914: {
        "url": "https://www.nationalarchives.gi/1914.aspx",
        "total": 16535,
        "next_target": "ctl00$MainContent$FormView1$ctl01$NextButton",
    },
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; GibraltarCensusBot/1.1; "
        "+https://github.com/baobabprince/gibraltar-historical-census)"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}

# Map variant field names that appear across different years to a canonical key.
# Order matters only for the first match; we keep the original key as well.
FIELD_ALIASES: dict[str, str] = {
    # id variants
    "id": "id",
    "listid": "id",
    # name variants
    "surname": "surname",
    "surename": "surname",
    "forename": "forename",
    "forename": "forename",
    "name": "name",
    # address / street
    "street": "street",
    "address": "street",
    "streetname": "street",
    "hseno": "houseNo",
    "houseno": "houseNo",
    # relationship
    "familyrelationship": "familyRelationship",
    "relationship": "familyRelationship",
    "relationtohead": "familyRelationship",
    # occupation
    "occupation": "occupation",
    "trade_profession_occupation": "occupation",
    "tradeprofessionoccupation": "occupation",
    # nationality / religion
    "nat_reg": "nationalityReligion",
    "nationality": "nationality",
    "religion": "religion",
    # residence
    "yearsofresidence": "yearsOfResidence",
    "howlongresident": "yearsOfResidence",
    "tenantresdncy lgth": "yearsOfResidence",
    # other common
    "sex": "sex",
    "age": "age",
    "birthplace": "birthplace",
    "division": "division",
    "district": "district",
    "maritalstatus": "maritalStatus",
    "noofpersons": "noOfPersons",
    "noofrooms": "noOfRooms",
    "listname": "listname",
    "remarks": "remarks",
    "notes": "notes",
    "notes1": "notes1",
    "notes2": "notes2",
    "status": "status",
    "disabilities": "disabilities",
    "education": "education",
    "employmentposition": "employmentPosition",
    "pageno": "pageNo",
    "permitno": "permitNo",
    "permitclass": "permitClass",
}


def clean(val: str | None) -> str | None:
    if val is None:
        return None
    val = val.strip()
    if val.lower() in ("no data", "", "n/a", "-", "?", "??"):
        return None
    return val


def normalize_key(raw: str) -> str:
    """Turn a display label into a safe dict key."""
    k = re.sub(r"[^\w]", "", raw.lower())
    return FIELD_ALIASES.get(k, k)


def parse_record(html: str, year: int) -> dict[str, Any] | None:
    """Extract every 'Label: value' pair generically + record number."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)

    fields: dict[str, Any] = {"year": year}

    # Generic capture of "Key: value" lines (handles multi-word keys)
    for m in re.finditer(r"^([A-Za-z][A-Za-z0-9_ ?()]*?):\s*(.*)$", text, re.MULTILINE):
        raw_key = m.group(1).strip()
        val = clean(m.group(2))
        key = normalize_key(raw_key)
        # Prefer the first non-None value if the same canonical key appears twice
        if key not in fields or fields[key] is None:
            fields[key] = val
        # Also keep the original raw key for full fidelity
        raw_safe = re.sub(r"[^\w]", "_", raw_key.lower()).strip("_")
        if raw_safe and raw_safe not in fields:
            fields[raw_safe] = val

    # Record number ("Record N of TOTAL")
    m = re.search(r"Record\s+(\d+)\s+of\s+(\d+)", text, re.IGNORECASE)
    if m:
        fields["record_num"] = int(m.group(1))
        fields["total_records"] = int(m.group(2))

    # Must have some kind of identifier
    if not any(fields.get(k) for k in ("id", "listid", "name", "surname", "surename")):
        return None
    return fields


def get_hidden(soup: BeautifulSoup) -> dict[str, str]:
    data = {}
    for inp in soup.select('input[type="hidden"]'):
        name = inp.get("name")
        if name:
            data[name] = inp.get("value", "")
    return data


def load_existing(output_dir: Path) -> list[dict]:
    json_path = output_dir / "records.json"
    if not json_path.exists():
        return []
    try:
        return json.loads(json_path.read_text(encoding="utf-8"))
    except Exception:
        return []


def get_resume_point(existing: list[dict]) -> int:
    if not existing:
        return 1
    nums = [r.get("record_num") for r in existing if r.get("record_num") is not None]
    if not nums:
        return 1
    return max(nums) + 1


def record_id(rec: dict) -> str | None:
    """Best available unique identifier for deduplication."""
    for k in ("id", "listid", "listID"):
        if rec.get(k):
            return str(rec[k])
    # Fallback composite
    parts = [str(rec.get(k) or "") for k in ("surname", "forename", "age", "street", "houseNo")]
    composite = "|".join(parts)
    return composite if composite.strip("|") else None


def scrape(
    year: int = 1911,
    max_records: int = 100,
    delay: float = 0.4,
    output_dir: str | Path | None = None,
    force_start: int | None = None,
    skip_delay: float = 0.05,
):
    if year not in YEAR_CONFIG:
        raise ValueError(
            f"Year {year} not configured. Available: {sorted(YEAR_CONFIG)}"
        )
    cfg = YEAR_CONFIG[year]
    url = cfg["url"]
    next_target = cfg["next_target"]

    if output_dir is None:
        output_dir = Path("data") / str(year)
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    existing = load_existing(output_dir)
    start_from = force_start if force_start is not None else get_resume_point(existing)

    print(f"Year: {year}")
    print(f"Already extracted: {len(existing)} records")
    print(f"Resuming from record_num: {start_from}")
    print(f"Will fetch up to {max_records} new records")
    print(f"Skip delay: {skip_delay}s | Collect delay: {delay}s")
    print("-" * 50)

    if start_from > cfg.get("total", 999999):
        print("All records already extracted. Nothing to do.")
        return existing

    session = requests.Session()
    session.headers.update(HEADERS)

    print("Fetching initial page...")
    r = session.get(url, timeout=45)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    hidden = get_hidden(soup)

    records: list[dict] = []
    seen_ids = {record_id(rec) for rec in existing if record_id(rec)}

    rec = parse_record(r.text, year)
    if not rec:
        raise RuntimeError("Could not parse first record")
    current_num = rec.get("record_num", 1)

    # ---------- Fast-forward to resume point ----------
    if start_from > 1:
        print(f"Advancing to record {start_from} (skip delay={skip_delay}s)...")
        while current_num < start_from:
            post = hidden.copy()
            post["__EVENTTARGET"] = next_target
            post["__EVENTARGUMENT"] = ""
            try:
                r = session.post(url, data=post, timeout=45)
                r.raise_for_status()
            except Exception as e:
                print(f"Network error while advancing: {e}")
                break
            soup = BeautifulSoup(r.text, "html.parser")
            hidden = get_hidden(soup)
            rec = parse_record(r.text, year)
            if not rec:
                print("Failed to advance – stopping")
                break
            current_num = rec.get("record_num", current_num + 1)
            if current_num % 100 == 0 or current_num == start_from:
                print(f"  ... now at record {current_num}")
            if skip_delay > 0:
                time.sleep(skip_delay)
        print(f"Reached record {current_num}")

    # Capture the record we landed on (if it is the desired start)
    rid = record_id(rec) if rec else None
    if (
        rec
        and rec.get("record_num") == start_from
        and rid
        and rid not in seen_ids
    ):
        records.append(rec)
        seen_ids.add(rid)
        label = (
            f"{rec.get('surname') or rec.get('name') or ''} "
            f"{rec.get('forename') or ''}"
        ).strip()
        print(
            f"[{rec.get('record_num')}/{rec.get('total_records')}] "
            f"{label} (ID {rid})"
        )

    # ---------- Collect new records ----------
    while len(records) < max_records:
        post = hidden.copy()
        post["__EVENTTARGET"] = next_target
        post["__EVENTARGUMENT"] = ""
        try:
            r = session.post(url, data=post, timeout=45)
            r.raise_for_status()
        except Exception as e:
            print(f"Network error: {e}")
            break

        soup = BeautifulSoup(r.text, "html.parser")
        hidden = get_hidden(soup)
        rec = parse_record(r.text, year)

        if not rec:
            print("Parse failed – stopping")
            break

        rid = record_id(rec)
        if rid and rid in seen_ids:
            print(f"Duplicate ID {rid} – stopping")
            break

        records.append(rec)
        if rid:
            seen_ids.add(rid)

        label = (
            f"{rec.get('surname') or rec.get('name') or ''} "
            f"{rec.get('forename') or ''}"
        ).strip()
        print(
            f"[{rec.get('record_num')}/{rec.get('total_records')}] "
            f"{label} (ID {rid})"
        )

        if (
            rec.get("record_num")
            and rec.get("total_records")
            and rec["record_num"] >= rec["total_records"]
        ):
            print("Reached last record in source")
            break

        time.sleep(delay)

    # ---------- Merge & save ----------
    by_id: dict[str, dict] = {}
    for r in existing:
        rid = record_id(r)
        if rid:
            by_id[rid] = r
    for r in records:
        rid = record_id(r)
        if rid:
            by_id[rid] = r

    merged = list(by_id.values())
    merged.sort(key=lambda x: x.get("record_num") or 0)

    json_path = output_dir / "records.json"
    json_path.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Dynamic CSV columns – union of all keys, prioritising common ones
    preferred = [
        "year", "id", "record_num", "surname", "forename", "name", "sex", "age",
        "birthplace", "religion", "nationality", "nationalityReligion",
        "education", "occupation", "street", "houseNo", "maritalStatus",
        "familyRelationship", "employmentPosition", "status",
        "yearsOfResidence", "division", "district", "noOfPersons", "noOfRooms",
        "permitNo", "permitClass", "pageNo", "listname", "remarks", "notes",
    ]
    all_keys: set[str] = set()
    for r in merged:
        all_keys.update(r.keys())
    csv_fields = [k for k in preferred if k in all_keys]
    csv_fields += sorted(k for k in all_keys if k not in csv_fields)

    with (output_dir / "records.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=csv_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(merged)

    meta = {
        "year": year,
        "source_url": url,
        "total_in_source": cfg.get("total"),
        "extracted": len(merged),
        "last_run_new": len(records),
        "next_record_num": (
            max((r.get("record_num") or 0) for r in merged) + 1 if merged else 1
        ),
    }
    (output_dir / "meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )

    print("-" * 50)
    print(f"New records this run : {len(records)}")
    print(f"Total records now    : {len(merged)}")
    print(f"Next resume point    : {meta['next_record_num']}")
    print(f"Saved → {json_path}")
    return merged


def main():
    p = argparse.ArgumentParser(
        description="Scrape Gibraltar census – auto-resumes from last record"
    )
    p.add_argument("--year", type=int, default=1911,
                   help=f"Census year. Available: {sorted(YEAR_CONFIG)}")
    p.add_argument("--max", type=int, default=50,
                   help="Max new records to fetch this run")
    p.add_argument("--delay", type=float, default=0.4,
                   help="Delay (seconds) between requests while collecting")
    p.add_argument("--skip-delay", type=float, default=0.05,
                   help="Delay (seconds) while advancing to resume point (default 0.05)")
    p.add_argument("--output", type=str, default=None)
    p.add_argument("--force-start", type=int, default=None,
                   help="Override auto-resume and start from this record_num")
    args = p.parse_args()
    scrape(
        year=args.year,
        max_records=args.max,
        delay=args.delay,
        output_dir=args.output,
        force_start=args.force_start,
        skip_delay=args.skip_delay,
    )


if __name__ == "__main__":
    main()
