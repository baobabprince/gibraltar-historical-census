# Gibraltar Historical Census

Modern, searchable web interface for the historical **Inhabitants of Gibraltar** registers from the [Gibraltar National Archives](https://www.nationalarchives.gi/).

Converts the outdated ASP.NET interface into a clean, filterable dataset hosted on GitHub Pages.

## Live site

**https://baobabprince.github.io/gibraltar-historical-census/**

## Data status

| Year | Total in source | Extracted |
|------|-----------------|----------|
| 1911 | 14,951 | **14,951** (complete) |
| Other years (1704–1914) | — | Scraper ready, not yet extracted |

Files per year: `data/{year}/records.json`, `records.csv`, `meta.json`

## Scraper

Supports years: **1704, 1777, 1791, 1814, 1816, 1834, 1868, 1871, 1878, 1881, 1891, 1901, 1911, 1914**

```bash
pip install -r requirements.txt
python scripts/scrape_census.py --year 1901 --max 500 --delay 0.4 --skip-delay 0.05
```

Auto-resumes from the last extracted record. Use `--skip-delay` for faster advancement when resuming large runs.

## GitHub Action

**Actions → Scrape Gibraltar Census → Run workflow**

Inputs: `year`, `max_records`, `delay`, `skip_delay`, `commit_results`

## Source

- https://www.nationalarchives.gi/Inhabitants.aspx
