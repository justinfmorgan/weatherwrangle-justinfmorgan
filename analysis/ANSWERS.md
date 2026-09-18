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
(22,005 if counted by name+country — wrong, name collisions.)

## Q2. How many unique countries?
**243** (ISO-3166 alpha-2, all well-formed).

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

## Q4. Exploded (city, country, date) row count
**368,909.** 15,886 cities x 16 days + 6,749 cities x 17 days. All rows unique on (city_id, country, date).
Not 316,890 (22,635 x 14) — the horizon is 16-17 days despite the filename.

## Q5. Top 10 hottest cities by mean temp.day (°C)

Two versions. **Recommended: filtered** (stub rows excluded) — the stub day is a daily-mean stand-in that
biases every city's mean down by a city-specific amount and reshuffles the ranking. Literal version kept
for reproducibility. See analysis/q5_literal_vs_filtered.png and COMPARISON.md. Awaiting owner sign-off.

| Rank | Filtered (recommended) | Mean °C | Literal (all rows) | Mean °C |
|---|---|---|---|---|
| 1 | Dourbali, TD | 39.81 | Dourbali, TD | 39.08 |
| 2 | Ayorou, NE | 39.41 | Maiduguri, NG | 38.75 |
| 3 | Damaturu, NG | 39.36 | Magumeri, NG | 38.75 |
| 4 | Maiduguri, NG | 39.35 | Damaturu, NG | 38.74 |
| 5 | Magumeri, NG | 39.35 | Massakory, TD | 38.69 |
| 6 | Niamey, NE | 39.25 | Ayorou, NE | 38.68 |
| 7 | Massakory, TD | 39.25 | Potiskum, NG | 38.62 |
| 8 | Geidam, NG | 39.22 | Daura, NG | 38.62 |
| 9 | Potiskum, NG | 39.20 | Bogo, CM | 38.59 |
| 10 | Daura, NG | 39.20 | Geidam, NG | 38.58 |

Ties (Maiduguri/Magumeri, Potiskum/Daura) are exact — same model grid cell — so within-tie order is arbitrary.

## Q6. San Francisco, CA tidy table
city_id 5391959 (37.77, -122.42). 16 days. Temps in °C; humidity nulled where source had 0 (missing-value artifact).
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
