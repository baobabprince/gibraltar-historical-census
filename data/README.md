# Data Directory

Extracted census datasets in JSON and CSV formats.

## Current structure

```
data/
  1704/   # 41 / 41 (complete)
  1777/   # 3,130 / 3,130 (complete)
  1791/   # 2,992 / 2,992 (complete)
  1814/   # 1,853 / 1,853 (complete)
  1816/   # 6,679 / 6,679 (complete)
  1834/   # 14,569 / 14,569 (complete)
  1868/   # 10,000 / 15,405 (in progress)
  1871/   # 22,725 / 22,725 (complete)
  1911/   # 14,951 / 14,951 (complete)
```

Not yet started: 1878, 1881, 1891, 1901, 1914.

Each year folder contains:
- `records.json` – full structured records
- `records.csv` – same data for easy download
- `meta.json` – extracted count, source totals, resume point

## Source attribution

All data is transcribed / extracted from the Gibraltar National Archives website:
https://www.nationalarchives.gi/Inhabitants.aspx

Please cite the original source when using the data.
