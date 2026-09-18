# Blind-Agent Cross-Check

Two independent passes over `daily_14.json`:

- **Initial (this session)** — pandas, after a schema/anomaly pass. Scripts in `analysis/`.
- **Blind agent** — a fresh subagent given only the file path and the six questions. No access to this
  session's findings, scripts, or the `analysis/` folder. Used Python stdlib only (`json`, `Counter`,
  `statistics`), independently detected NDJSON format.

A third subagent produced `viz_temperature_histograms.png` (temperature-only visual pass) and its
observations are folded into the plausibility column.

| # | Question | Initial answer | Blind agent | Match | Plausibility / what makes most sense |
|---|---|---|---|---|---|
| 1 | City records | **22,635** (22,005 by name+country) | **22,635** (22,005 by name+country) | Yes | Both counted lines and both independently flagged the 468 name collisions. Unambiguous. |
| 2 | Unique countries | **243** | **243** | Yes | All ISO alpha-2, well-formed. 249 codes exist, so 243 is credible for a global city list. |
| 3 | Top 10 countries | US 2,924 · IN 2,393 · BR 1,194 · DE 985 · RU 953 · CN 788 · JP 752 · GB 672 · IT 670 · FR 610 | Identical, same order, same counts | Yes | Population-weighted city list; no ties near the cutoff (FR 610 vs #11), so the boundary is stable. |
| 4 | Exploded rows | **368,909** (15,886×16 + 6,749×17); 358,817 if keyed on name | **368,909**; 358,817 if keyed on name | Yes | Both independently found the 16/17-day split and rejected the filename's "14". Both agree `(city_id, date)` is the true key. |
| 5 | Top 10 hottest (literal) | Dourbali 39.08 · Maiduguri 38.75 · Magumeri 38.75 · Damaturu 38.74 · Massakory 38.69 · Ayorou 38.68 · Potiskum 38.62 · Daura 38.62 · Bogo 38.59 · Geidam 38.58 | Identical, same order, same values (also reported Kelvin and exact ties) | Yes | Blind agent computed the literal mean only. Initial pass also computed the **filtered** mean (stub day excluded): Dourbali 39.81 · Ayorou 39.41 · Damaturu 39.36 · Maiduguri 39.35 · Magumeri 39.35 · Niamey 39.25 · Massakory 39.25 · Geidam 39.22 · Potiskum 39.20 · Daura 39.20. Niamey enters, Bogo drops. See below. |
| 6 | San Francisco table | 16 rows, city_id 5391959, temps to 1 dp, humidity **nulled** where source had 0 | 16 rows, city_id 5391959, temps to 2 dp, humidity **kept as 0** | Yes (values) | Same city, same dates, same temps (rounding only), same descriptions. Blind agent independently concluded the 0s "should be treated as null" but reported the raw values. Initial pass nulled them in the CSV. |

## Q5: literal vs filtered — which makes more sense

Both agents agree on the literal answer. The question is whether the literal answer is *right*.

Evidence (`q5_literal_vs_filtered.png`):

- 16,960 cities (75%) have exactly one "stub" row where all six temp fields are identical — always the
  last forecast day (day 15 or 16), or day 0 for 1,239 cities. The histogram agent found the same
  16,960 zero-range rows independently.
- The stub's `temp.day` is on average **5.86 °C cooler** than the same city's mean over its real days
  (median −5.04 °C; 92% of stubs are cooler). It behaves like a daily mean, not a daytime temperature.
- Because the bias differs per city, it does not cancel in a ranking: literal ranks 2–10 all shift,
  Niamey (NE) moves from #13 to #6, Bogo (CM) from #9 to #13.

Decision (locked in): the **filtered** ranking is the final answer to "hottest cities", with the literal
ranking kept as a footnote for reproducibility. The filtered version is what the question is trying to
measure; the literal version reproduces a known artifact. See ANSWERS.md.

## Findings the blind agent added

- Humidity is real for **exactly 3 days per city, for all 22,635 cities**. 17-day records have a stale
  leading day (day 0 zeroed, days 1–3 real); 16-day records have days 0–2 real. Verified. This
  sharpens the initial "days 4+ are zero" description.
- Kathmandu pressure jumps ~709 → ~788 hPa mid-forecast: another sign of the model switch at day 4.
- Exact ties in Q5 (Maiduguri/Magumeri; Potiskum/Daura) — neighbouring cities on the same model grid
  cell have identical forecasts, so within-tie order is arbitrary.

## Findings the histogram agent added

- `temp.day == temp.max` in 64% of rows (63% even excluding stubs) — `day` is often just the max, not
  an independent reading.
- Bimodal `temp.day` (modes ~7 °C and ~26 °C) is geographic — the per-city means show the same two
  humps — not day-to-day noise. Southern hemisphere (13% of rows) is unimodal around 26 °C.
- Last forecast day is narrower than day 0 (sd 9.1 vs 11.0 °C): long-horizon regression to climatology.
- Extremes are plausible: 43.6 °C Diffa (NE), −29.1 °C Longyearbyen (SJ); 20 rows with >25 °C
  daily range in continental/dry climates.
