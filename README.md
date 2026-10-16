# Gibraltar Historical Census

Modern, searchable web interface for the historical **Inhabitants of Gibraltar** registers from the [Gibraltar National Archives](https://www.nationalarchives.gi/).

Converts the outdated ASP.NET interface into a clean, filterable dataset hosted on GitHub Pages.

## Live site

**https://baobabprince.github.io/gibraltar-historical-census/**

## Data status

| Year | Total in source | Extracted | Status |
|------|-----------------|----------:|--------|
| 1704 | 41 | **41** | complete |
| 1777 | 3,130 | **3,130** | complete |
| 1791 | 2,992 | **2,992** | complete |
| 1814 | 1,853 | **1,853** | complete |
| 1816 | 6,679 | **6,679** | complete |
| 1834 | 14,569 | **14,569** | complete |
| 1868 | 15,405 | **10,000** | in progress |
| 1871 | 22,725 | **22,725** | complete |
| 1878 | 17,982 | — | not started |
| 1881 | 18,616 | — | not started |
| 1891 | 19,057 | — | not started |
| 1901 | 19,342 | — | not started |
| 1911 | 14,951 | **14,951** | complete |
| 1914 | 16,535 | — | not started |

**Total extracted so far: ~77,000 records** across 9 years.

Files per year: `data/{year}/records.json`, `records.csv`, `meta.json`

## Scraper

Supports years: **1704, 1777, 1791, 1814, 1816, 1834, 1868, 1871, 1878, 1881, 1891, 1901, 1911, 1914**

```bash
pip install -r requirements.txt
python scripts/scrape_census.py --year 1868 --max 500 --delay 0.4 --skip-delay 0.05
```

Auto-resumes from the last extracted record. Use `--skip-delay` for faster advancement when resuming large runs.

## GitHub Action

**Actions → Scrape Gibraltar Census → Run workflow**

Inputs: `year`, `max_records`, `delay`, `skip_delay`, `commit_results`

## Source

- https://www.nationalarchives.gi/Inhabitants.aspx
