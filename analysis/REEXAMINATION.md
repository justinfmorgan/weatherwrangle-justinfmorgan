# Reexamination

Follow-up checks requested after the blind cross-check. Figure: `reexam_summary.png`.
Scripts: `reexam_location.py`, `reexam_location2.py`, `reexam_forecast.py`, `reexam_viz.py`.
Data outputs: `reexam_near_duplicate_cities.csv`, `reexam_geographic_outliers.csv` (empty — see E).

## 1. City identity and country codes, cross-examined with lat/lon

**A. Country code validity.** 243 codes; 242 are ISO-3166 alpha-2. The one exception is `XK` (Kosovo,
17 cities) — the standard user-assigned code, used by OpenWeatherMap, GeoNames and the EU. Not an error.
No legacy codes (UK, CS, YU, AN …) present. **Q2 = 243 stands.**

**B. Near-duplicate coordinates, independent of name.**

| Radius | Pairs | Same country | Same name | Cross-country |
|---|---|---|---|---|
| 0 km (exact) | 2 | 2 | 0 | 0 |
| ≤ 0.5 km | 8 | 8 | 2 | 0 |
| ≤ 1 km | 31 | 29 | 4 | 2 |
| ≤ 2 km | 393 | 386 | 10 | 7 |
| ≤ 5 km | 4,296 | 4,246 | 17 | 50 |

- The 2 exact-coordinate pairs are true duplicates: Tōkyō-to / Tokyo (JP) and Arumuganeri /
  Kayalpattinam (IN, coordinate collision — they are distinct towns in reality).
- ≤ 1 km pairs are transliteration/alias duplicates (Svetlogorsk / Svyetlahorsk, Zhucheng / Zhu Cheng City,
  Ischia Porto / Ischia, Zürich Kreis sub-districts).
- ≤ 2 km and ≤ 5 km pairs are dominated by genuinely distinct adjacent municipalities: Paris banlieue
  communes (Les Lilas / Bagnolet, Clamart / Châtillon), London boroughs, US suburbs. These are not
  duplicates; the city list is simply dense in metro areas.
- 372 of the 393 ≤ 2 km pairs have byte-identical forecasts (same model grid cell) — redundant, not wrong.

**C. Same name, same country (468 groups).** Median distance between namesakes is 673 km; 90% are
> 109 km apart. Only 15 groups have namesakes < 5 km apart (Esposende PT 0.3 km, Baden AT 0.4 km,
Kansas City US 4.5 km, Texarkana US 2.1 km …) — those are the plausible true duplicates or
twin-city entries. The remaining 453 are distinct places that share a name (4 Albanys, 4 Alexandrias).
**Q1 = 22,635 by city.id stands**; if you insisted on deduplicating physical places, the defensible
reduction is ~10–30 cities (exact + ≤ 1 km + the 15 same-name < 5 km groups), not 630.

**D. Same name, different country (428 names).** Only 2 cross-country namesake pairs are within 50 km:
Astara AZ / Astara IR (3 km — a real twin border town) and Niagara Falls US / CA (1 km — likewise).
No evidence of mis-assigned country codes.

**E. Geographic plausibility of country code.** For every country with ≥ 3 cities, no city is more than
max(1,500 km, 8× that country's median nearest-neighbour distance) from another city with the same
code. Zero outliers. 67 countries have < 3 cities and cannot be tested this way, but their coordinates
were spot-checked on the map (`viz_city_map.png`) and nothing lands in the ocean or the wrong continent.

**F. Impact on Q3.** One-survivor-per-cluster dedup at 0.5 / 1 / 2 km leaves the top-10 membership
unchanged; GB (672) and IT (670) swap at 2 km — effectively a tie. Only at 5 km (which merges genuine
adjacent communes) does FR drop from #10 to #15 and MX enter. **Q3 stands; note GB/IT as a near-tie.**

## 2. Rain key vs weather label

| label | rain key present | absent |
|---|---|---|
| Clear | 6,158 | 91,514 |
| Clouds | 0 | 10,282 |
| Rain | 201,167 | 26,352 |
| Snow | 19,079 | 14,357 |

- All 26,352 "Rain without key" rows are `light rain` (id 500). Rain amounts in the file have a hard floor
  at 0.2 mm, so these are almost certainly rows where the modelled amount was < 0.2 mm and the key was
  dropped while the label remained. Only 15% of them are stub rows.
- The 6,158 "Clear with key" rows carry real amounts (median 1.5 mm, p99 23 mm), concentrated in the
  long-range days 4–12. Here the label is the less trustworthy field.
- Per-city "rainy day" counts differ between label-based and key-based definitions for 72% of cities
  (mean |diff| 1.8 days).
- Rain amount tracks the weather id cleanly (500: median 1.0 mm, 501: 5.6, 502: 16.5, 503: 51.9).

**Recommendation:** "did it rain" = label is Rain **or** rain key present; "how much" = the key.
State the definition explicitly in any rain-based answer.

## 3. Exact-tie cities in Q5

90% of cities (20,485) share a byte-identical full forecast with at least one other city — 3,181 groups,
largest 163 cities, 305 groups spanning a border. The data is grid-cell based; ties are structural.
In the final top 10, Maiduguri / Magumeri and Potiskum / Daura are tied pairs. Collapsing to one city
per grid cell: Yagoua (CM) 39.19 and Bogo (CM) 39.14 enter at #9–10, Magumeri and Daura drop.
The question asks for cities, so the per-city ranking is kept as final, with ties flagged.

## 4. Q5 sensitivity

| Variant | Top-10 overlap with final |
|---|---|
| temp.max instead of temp.day | 9/10 (Ati TD replaces Potiskum) |
| literal, stubs included | 9/10 (Bogo replaces Niamey) |
| first 10 days only | 3/10 |
| first 7 days only | 2/10 |
| first 4 days only (pre-switch) | 0/10 (Wau / Tonj / Rumbek SS, Burkina Faso cities) |

The choice of temperature field barely matters; the **window** matters a lot. The Sahel heat maximum
migrates during the forecast period — South Sudan / Burkina Faso in the first days, Chad / Niger /
Nigeria over the full horizon. The full-horizon answer is what the question asked for and is the one
locked in; anyone using this ranking should know it is a 16-day mean, not a "current" ranking.

## 5. Model switch — full characterisation

Aligning 17-day records by dropping their stale leading day, every city has exactly 3 short-range days
(aligned days 0–2), then a long-range model:

| Field | Short-range (aligned 0–2) | Long-range (aligned 3+) |
|---|---|---|
| humidity | real (4–100) | always 0 |
| weather.main | Clear / Clouds / Rain / Snow | Clear / Rain / Snow only (Clouds 801–804 gone) |
| icon | day and night variants | day only |
| rain key present | 33–38% of rows | 64–75% |
| clouds % mean | 31–32 | 33–39 |
| |Δpressure| at the boundary | p99 = 67 hPa (vs 15–38 elsewhere) | |
| uvi | varies | frozen from aligned day 6–7 onward |
| last day | | stub row (all temps equal) for 75% of cities |

**Trustworthy horizon:** aligned days 0–2 are the only days where every field is populated as
documented. Days 3–13 are usable for temperature, pressure, wind, precipitation and label, with humidity
nulled and Clouds absent. UVI beyond day 6 and the final stub day should be dropped.
