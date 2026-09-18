# daily_14.json — Running Answers (source of truth)

Data: 22,635 NDJSON lines, 368,909 flattened city-day rows. Snapshot 2017-03-14 ~04:30 UTC.
Known anomalies applied where noted: humidity == 0 is a missing-value artifact — every city has exactly
3 days of real humidity (days 0-2 for 16-day records, days 1-3 for 17-day records), all else is 0;
16,960 cities have one "stub" row (all six temp fields identical, last forecast day or day 0) whose
temp.day runs ~5.9 °C cooler than the city's real days;
UVI frozen from day_idx 7; Clouds category vanishes after day 3; 468 (name,country) pairs share
names across distinct city_ids — always key on city_id.

## Q1. How many city records are in the file?
**22,635.** One JSON object per line, each with a distinct city.id.
(22,005 if counted by name+country — wrong, name collisions.) Lat/lon cross-check (REEXAMINATION.md §1):
only 2 exact-coordinate pairs and ~10-30 plausible physical duplicates; the 468 namesake groups are real distinct places.

## Q2. How many unique countries?
**243** (ISO-3166 alpha-2, all well-formed). 242 are ISO-official; XK (Kosovo, 17 cities) is the standard
user-assigned code. No legacy codes. No city is geographically implausible for its code (REEXAMINATION.md §1).

## Q3. Top 10 countries by city count
| Rank | Country | Cities |
|---|---|---|
| 1 | US | 2,924 |
| 2 | IN | 2,393 |
| 3 | BR | 1,194 |
| 4 | DE | 985 |
| 5 | RU | 953 |
| 6 | CN | 788 |
| 7 | JP | 752 |
| 8 | GB | 672 |
| 9 | IT | 670 |
| 10 | FR | 610 |

Robust to near-duplicate dedup at 0.5/1/2 km (membership unchanged). GB vs IT (672 vs 670) is a near-tie.

## Q4. Exploded (city, country, date) row count
**368,909.** 15,886 cities x 16 days + 6,749 cities x 17 days. All rows unique on (city_id, country, date).
Not 316,890 (22,635 x 14) — the horizon is 16-17 days despite the filename.

## Q5. Top 10 hottest cities by mean temp.day (°C)

**Final (locked in):** stub rows excluded. The stub day (all six temps identical, at the forecast edge for
16,960 cities) is a daily-mean stand-in that runs ~5.9 °C cooler than the city's real days and biases
each city's mean by a city-specific amount, reshuffling ranks 2-10. See q5_literal_vs_filtered.png.

| Rank | City | Country | city_id | Mean temp.day °C |
|---|---|---|---|---|
| 1 | Dourbali | TD | 2433055 | 39.81 |
| 2 | Ayorou | NE | 2447416 | 39.41 |
| 3 | Damaturu | NG | 2345521 | 39.36 |
| 4 | Maiduguri | NG | 2331447 | 39.35 |
| 5 | Magumeri | NG | 2331528 | 39.35 |
| 6 | Niamey | NE | 2440485 | 39.25 |
| 7 | Massakory | TD | 2428228 | 39.25 |
| 8 | Geidam | NG | 2341294 | 39.22 |
| 9 | Potiskum | NG | 2324767 | 39.20 |
| 10 | Daura | NG | 2345096 | 39.20 |

Ties (Maiduguri/Magumeri, Potiskum/Daura) are exact — same model grid cell — within-tie order is arbitrary.
Sensitivity: temp.max gives 9/10 overlap; restricting to the first 4-7 days gives 0-2/10 — the ranking is a
16-day-mean ranking and the Sahel heat maximum moves during the window (REEXAMINATION.md §3-4).

Footnote — literal mean over all rows (reproduces the artifact): Dourbali 39.08, Maiduguri 38.75,
Magumeri 38.75, Damaturu 38.74, Massakory 38.69, Ayorou 38.68, Potiskum 38.62, Daura 38.62, Bogo (CM) 38.59,
Geidam 38.58. Independently reproduced by a blind agent (COMPARISON.md).

## Q6. San Francisco, CA tidy table
city_id 5391959 (37.77, -122.42). 16 days. Temps in °C; humidity nulled where source had 0 (missing-value artifact).
Date convention: UTC calendar date of `dt` (locked in). SF's dt values fall at 18:00-20:00 UTC so UTC date == local date.
See analysis/q6_san_francisco.csv.

| date | temp_min | temp_max | humidity | weather_description |
|---|---|---|---|---|
| 2017-03-13 | 9.8 | 19.0 | 67 | sky is clear |
| 2017-03-14 | 7.5 | 25.9 | 55 | sky is clear |
| 2017-03-15 | 8.6 | 22.8 | 56 | sky is clear |
| 2017-03-16 | 10.2 | 18.8 | null | light rain |
| 2017-03-17 | 6.5 | 18.6 | null | light rain |
| 2017-03-18 | 9.2 | 16.8 | null | light rain |
| 2017-03-19 | 10.5 | 18.1 | null | light rain |
| 2017-03-20 | 6.8 | 18.4 | null | light rain |
| 2017-03-21 | 4.6 | 16.7 | null | sky is clear |
| 2017-03-22 | 3.9 | 16.5 | null | light rain |
| 2017-03-23 | 5.2 | 12.2 | null | moderate rain |
| 2017-03-24 | 8.0 | 15.1 | null | moderate rain |
| 2017-03-25 | 5.5 | 13.6 | null | light rain |
| 2017-03-26 | 8.3 | 13.7 | null | moderate rain |
| 2017-03-27 | 5.6 | 15.8 | null | sky is clear |
| 2017-03-28 | 4.1 | 19.3 | null | sky is clear |
