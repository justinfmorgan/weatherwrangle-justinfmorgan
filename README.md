# Weather Wrangle — daily_14.json

Take-home analysis of an OpenWeatherMap-style bulk daily-forecast file (22,635 cities, 16–17 day horizon,
snapshot 2017-03-14). The source file (103 MB) exceeds GitHub's per-file limit and is not committed;
place `daily_14.json` in the repo root to reproduce.

## Answers

**[`analysis/ANSWERS.md`](analysis/ANSWERS.md)** — the six questions with final answers, and the data
filters applied to each.

**[`analysis/COMPARISON.md`](analysis/COMPARISON.md)** — cross-check against an independent blind pass
(a fresh agent given only the file and the questions), with a plausibility note per question.

## Method

1. **Format check** — confirmed strict NDJSON (LF-only, one object per line, no array wrapper); all lines parse.
2. **Schema inference** — walked every record/nested key; recorded types, presence, list lengths (`schema.py`).
3. **Anomaly pass** — before answering anything (`anomalies.py`, `anomalies2.py`). Key findings:
   - `humidity` is real for exactly 3 days per city; 0 elsewhere (missing-value sentinel, 82% of rows).
   - 16,960 cities have a "stub" day (all six temps identical, ~5.9 °C cooler than real days) at the forecast edge.
   - `uvi` frozen from day 7 onward; `Clouds` category vanishes after day 3; `dt` hour shifts at day 4 — a model switch.
   - 468 (name, country) pairs collide across distinct `city.id`s — always key on id.
   - Horizon is 16–17 days despite the filename.
4. **Answers with plausibility plots** — each question gets a plot of the relevant distribution so the
   answer can be judged in context (`answers.py`, `q*.png`).
5. **Independent verification** — blind agent + a separate temperature-histogram pass
   (`viz_temperature_histograms.py`). All six answers matched.

## Files

| Path | What |
|---|---|
| `analysis/ANSWERS.md` | Final answers |
| `analysis/COMPARISON.md` | Blind-agent cross-check and plausibility notes |
| `analysis/q6_san_francisco.csv` | Q6 tidy table (humidity nulled where the source had the 0 sentinel) |
| `analysis/q1_city_records.png` … `q6_san_francisco.png` | Per-question plausibility plots |
| `analysis/q5_literal_vs_filtered.png` | Why the stub day changes the Q5 ranking |
| `analysis/viz_horizon_artifacts.png` | Regime change at forecast day 4 (humidity, stubs, UVI, weather mix) |
| `analysis/viz_distributions.png` | Field distributions |
| `analysis/viz_temperature_histograms.png` | Six-panel temperature histogram set |
| `analysis/viz_city_map.png` | Coordinate sanity check |
| `analysis/*.py` | Reproducible scripts |

## Reproduce

```bash
uv venv .venv && uv pip install --python .venv/bin/python pandas matplotlib
# scripts expect daily.pkl; regenerate it first:
export WW_SCRATCH=.   # where daily.pkl lives
.venv/bin/python analysis/flatten.py
.venv/bin/python analysis/answers.py
```
