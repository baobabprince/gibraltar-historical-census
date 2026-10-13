# Data Directory

This folder will hold the extracted census datasets in JSON and CSV formats.

## Planned structure

```
data/
  abstracts/          # Statistical summaries 1767–2001
  1777/
  1814/
  1816/
  1834/
  1868/
  1871/
  1878/
  1881/
  1901/
  1911/
  1921/
  ...
```

Each year folder will contain:
- `records.json` – full structured records
- `records.csv` – same data for easy download
- `meta.json` – field definitions, record count, source notes

## Source attribution

All data is transcribed / extracted from the Gibraltar National Archives website:
https://www.nationalarchives.gi/Inhabitants.aspx

Please cite the original source when using the data.
