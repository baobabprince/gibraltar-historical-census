#!/usr/bin/env python3
"""Gibraltar National Archives Inhabitants Register scraper."""
from __future__ import annotations
import argparse, csv, json, re, time
from pathlib import Path
import requests
from bs4 import BeautifulSoup

YEAR_CONFIG = {
    1911: {
        "url": "https://www.nationalarchives.gi/1911.aspx",
        "total": 14951,
        "next_target": "ctl00$MainContent$FormView1$ctl01$NextButton",
    },
}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; GibraltarCensusBot/1.0; +https://github.com/baobabprince/gibraltar-historical-census)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}
FIELD_PATTERNS = {
    "id": r"ID:\s*(.+)", "surname": r"Surname:\s*(.+)", "forename": r"Forename:\s*(.+)",
    "sex": r"Sex:\s*(.+)", "age": r"Age:\s*(.+)", "disabilities": r"Disabilities:\s*(.+)",
    "birthplace": r"Birthplace:\s*(.+)", "religion": r"Religion:\s*(.+)",
    "education": r"Education:\s*(.+)", "occupation": r"Occupation:\s*(.+)",
    "division": r"Division:\s*(.+)", "district": r"District:\s*(.+)",
    "street": r"Street:\s*(.+)", "houseNo": r"HouseNo:\s*(.+)",
    "noOfRooms": r"NoOfRooms:\s*(.+)", "noOfPersons": r"NoOfPersons:\s*(.+)",
    "maritalStatus": r"MaritalStatus:\s*(.+)", "familyRelationship": r"FamilyRelationship:\s*(.+)",
    "employmentPosition": r"EmploymentPosition:\s*(.+)", "pageNo": r"PageNo:\s*(.+)",
    "listname": r"Listname:\s*(.+)", "remarks": r"Remarks:\s*(.+)",
    "notes": r"Notes:\s*(.+)", "notes1": r"Notes1:\s*(.+)", "notes2": r"Notes2:\s*(.+)",
}

def clean(val):
    if val is None: return None
    val = val.strip()
    if val.lower() in ("no data", "", "n/a", "-"): return None
    return val

def parse_record(html, year):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    fields = {"year": year}
    for key, pat in FIELD_PATTERNS.items():
        m = re.search(pat, text)
        fields[key] = clean(m.group(1)) if m else None
    m = re.search(r"Record\s+(\d+)\s+of\s+(\d+)", text)
    if m:
        fields["record_num"] = int(m.group(1))
        fields["total_records"] = int(m.group(2))
    if not fields.get("id"): return None
    return fields

def get_hidden(soup):
    data = {}
    for inp in soup.select('input[type="hidden"]'):
        name = inp.get("name")
        if name: data[name] = inp.get("value", "")
    return data

def scrape(year=1911, max_records=100, delay=0.4, start_from=1, output_dir=None):
    if year not in YEAR_CONFIG:
        raise ValueError(f"Year {year} not configured")
    cfg = YEAR_CONFIG[year]
    url = cfg["url"]
    next_target = cfg["next_target"]
    session = requests.Session()
    session.headers.update(HEADERS)
    print(f"Fetching initial page for {year}...")
    r = session.get(url, timeout=45)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    hidden = get_hidden(soup)
    records = []
    seen_ids = set()
    rec = parse_record(r.text, year)
    if not rec: raise RuntimeError("Could not parse first record")
    current_num = rec.get("record_num", 1)
    if start_from <= 1:
        records.append(rec)
        seen_ids.add(rec["id"])
        print(f"[{rec.get('record_num')}] {rec.get('surname')} {rec.get('forename')} (ID {rec.get('id')})")
    while current_num < start_from:
        post = hidden.copy()
        post["__EVENTTARGET"] = next_target
        post["__EVENTARGUMENT"] = ""
        r = session.post(url, data=post, timeout=45)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        hidden = get_hidden(soup)
        rec = parse_record(r.text, year)
        if not rec: break
        current_num = rec.get("record_num", current_num + 1)
        time.sleep(delay * 0.5)
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
        if rec["id"] in seen_ids:
            print(f"Duplicate ID {rec['id']} – stopping")
            break
        records.append(rec)
        seen_ids.add(rec["id"])
        print(f"[{rec.get('record_num')}/{rec.get('total_records')}] {rec.get('surname')} {rec.get('forename')} (ID {rec.get('id')})")
        if rec.get("record_num") and rec.get("total_records") and rec["record_num"] >= rec["total_records"]:
            print("Reached last record")
            break
        time.sleep(delay)
    if output_dir is None:
        output_dir = Path("data") / str(year)
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "records.json"
    existing = []
    if json_path.exists():
        try: existing = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception: pass
    by_id = {r["id"]: r for r in existing}
    for r in records: by_id[r["id"]] = r
    merged = list(by_id.values())
    merged.sort(key=lambda x: x.get("record_num") or 0)
    json_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    csv_fields = ["year","id","record_num","surname","forename","sex","age","birthplace","religion","education","occupation","street","houseNo","maritalStatus","familyRelationship","employmentPosition","notes","division","district"]
    with (output_dir / "records.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=csv_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(merged)
    meta = {"year": year, "source_url": url, "total_in_source": cfg.get("total"), "extracted": len(merged), "last_run_new": len(records)}
    (output_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"\nSaved {len(merged)} total records to {json_path}")
    return merged

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--year", type=int, default=1911)
    p.add_argument("--max", type=int, default=50)
    p.add_argument("--delay", type=float, default=0.4)
    p.add_argument("--start-from", type=int, default=1)
    p.add_argument("--output", type=str, default=None)
    args = p.parse_args()
    scrape(year=args.year, max_records=args.max, delay=args.delay, start_from=args.start_from, output_dir=args.output)

if __name__ == "__main__":
    main()
