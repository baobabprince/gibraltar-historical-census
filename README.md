# Gibraltar Historical Census

Modern, searchable web interface for the historical **Inhabitants of Gibraltar** registers from the [Gibraltar National Archives](https://www.nationalarchives.gi/).

Converts the outdated ASP.NET interface into a clean, filterable dataset hosted on GitHub Pages.

## Live site

Once GitHub Pages is enabled (Settings → Pages → Deploy from branch `master` / `main`), the site will be at:

**https://baobabprince.github.io/gibraltar-historical-census/**

## Data status (1911)

| Metric | Value |
|--------|-------|
| Total in source | 14,951 |
| Extracted so far | 75 |
| Next resume | record 76 |

Files: `data/1911/records.json`, `records.csv`, `meta.json`

## Scraper

```bash
pip install -r requirements.txt
python scripts/scrape_census.py --year 1911 --max 100 --delay 0.5
```

Auto-resumes from the last extracted record.

## GitHub Action

**Actions → Scrape Gibraltar Census → Run workflow**

Inputs: `year`, `max_records`, `delay`, `commit_results`

## Source

- https://www.nationalarchives.gi/1911.aspx
- Other years can be added to `YEAR_CONFIG` in the scraper.
