import os
import pandas as pd, numpy as np
pd.set_option("display.width", 220); pd.set_option("display.max_columns", 40)
df = pd.read_pickle(os.environ.get("WW_SCRATCH", ".") + "/daily.pkl")
d = df.sort_values(["line_no","day_idx"]).copy()
d["hour"] = d.dt_utc.dt.hour
d["hour_shift"] = d.groupby("line_no").hour.diff().fillna(0).ne(0)
print("=== dt hour shifts within a record, by day_idx ===")
print(d[d.hour_shift].day_idx.value_counts().sort_index().to_dict())
print("records with >=1 hour shift:", d[d.hour_shift].line_no.nunique())

print("\n=== degenerate (all-temps-equal) rows: which other fields look default? ===")
t = df[["temp_day","temp_min","temp_max","temp_night","temp_eve","temp_morn"]]
deg = df[t.nunique(axis=1)==1]
print("day_idx dist:", deg.day_idx.value_counts().sort_index().to_dict())
print("share of last-day rows that are degenerate:", (deg.day_idx==deg.n_days-1).mean().round(3))
last = df[df.day_idx==df.n_days-1]
print("share of ALL last-day rows that are degenerate:", (last[["temp_day","temp_min","temp_max","temp_night","temp_eve","temp_morn"]].nunique(axis=1)==1).mean().round(3))
print("degenerate rows at day_idx 0 -> sample:"); print(deg[deg.day_idx==0][["city_name","country","dt_utc","temp_day","pressure","humidity","speed","weather_desc"]].head(5).to_string())
print("\n=== per-day_idx field means (looking for regime changes) ===")
print(df.groupby("day_idx").agg(humidity_zero=("humidity",lambda s:(s==0).mean()), temp_spread=("temp_max",lambda s:0)).assign(
    temp_spread=df.assign(sp=df.temp_max-df.temp_min).groupby("day_idx").sp.mean(),
    rain_key=df.groupby("day_idx").has_rain_key.mean(),
    clouds=df.groupby("day_idx").clouds.mean(),
    uvi=df.groupby("day_idx").uvi.mean(),
    n=df.groupby("day_idx").size()).round(3).to_string())

print("\n=== 30K spread row ===")
print(df[(df.temp_day-df.temp_night).abs()>30][["city_name","country","lat","dt_utc","temp_day","temp_night","temp_min","temp_max"]].to_string())
print("\n=== exact coord dupes ===")
c = df.drop_duplicates("line_no")
print(c[c.duplicated(["lat","lon"],keep=False)].sort_values(["lat","lon"])[["city_id","city_name","country","lat","lon"]].to_string())
print("\n=== non-ASCII names ===")
print(c[~c.city_name.str.match(r"^[\x00-\x7F]*$")].city_name.tolist())
print("\n=== rain-key vs weather cross-tab (row-level) ===")
print(pd.crosstab(df.weather_main, df.has_rain_key).to_string())
print("\n=== uvi by day_idx: is it constant within a record after some day? ===")
print("records where uvi identical for day_idx>=4:", (d[d.day_idx>=4].groupby("line_no").uvi.nunique()==1).mean().round(3))
print("records where pressure identical for day_idx>=4:", (d[d.day_idx>=4].groupby("line_no").pressure.nunique()==1).mean().round(3))
print("\n=== snapshot time vs first dt: 'time' before or after first dt? ===")
first = d[d.day_idx==0]
print("first dt < time (forecast day already started):", (first.dt < first.time).sum(), "of", len(first))
