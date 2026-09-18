import os, numpy as np, pandas as pd
pd.set_option("display.width",220); pd.set_option("display.max_columns",30)
df=pd.read_pickle(os.environ.get("WW_SCRATCH",".")+"/daily.pkl")
t=df[["temp_day","temp_min","temp_max","temp_night","temp_eve","temp_morn"]]; df["stub"]=t.nunique(axis=1)==1
for k in ["temp_day","temp_max","temp_min"]: df[k+"_c"]=df[k]-273.15
key=["city_id","city_name","country"]

print("=== 1. RAIN KEY vs WEATHER LABEL ===")
ct=pd.crosstab(df.weather_main,df.has_rain_key,margins=True); print(ct.to_string())
print("\nRain-label rows WITHOUT rain key, by day_idx:"); print(df[(df.weather_main=="Rain")&(~df.has_rain_key)].day_idx.value_counts().sort_index().to_dict())
print("Clear-label rows WITH rain key, by day_idx:"); print(df[(df.weather_main=="Clear")&(df.has_rain_key)].day_idx.value_counts().sort_index().to_dict())
print("Clear-with-rain: rain amount dist:"); print(df[(df.weather_main=="Clear")&(df.has_rain_key)].rain.describe(percentiles=[.5,.9,.99]).round(2).to_string())
print("Rain-without-key: which descriptions?", df[(df.weather_main=="Rain")&(~df.has_rain_key)].weather_desc.value_counts().to_dict())
print("Rain-without-key: is it the stub row?", df[(df.weather_main=="Rain")&(~df.has_rain_key)].stub.mean().round(3))
print("Snow-label rows without snow key:", ((df.weather_main=="Snow")&(~df.has_snow_key)).sum(), " snow-key rows labelled Clear:", ((df.has_snow_key)&(df.weather_main=="Clear")).sum())
# does weather.id correspond to rain amount thresholds?
r=df[df.has_rain_key]; print("\nrain amount by weather_id (median, p90):"); print(r.groupby(["weather_id","weather_desc"]).rain.agg(n="size",median="median",p90=lambda s:s.quantile(.9)).round(2).to_string())
lab=(df.weather_main=="Rain").groupby(df.city_id).sum(); keyc=df.has_rain_key.groupby(df.city_id).sum()
print("\nPer-city 'rainy days': label-based vs key-based — cities where they differ:", (lab!=keyc).sum(), "of", lab.size, "; mean abs diff:", (lab-keyc).abs().mean().round(2))

print("\n=== 2. EXACT-TIE CITIES (identical forecasts = same grid cell) ===")
sig=df.sort_values(["city_id","dt"]).groupby("city_id").apply(lambda g: hash((tuple(g.temp_day),tuple(g.temp_min),tuple(g.pressure),tuple(g.dt))), include_groups=False)
c=df.drop_duplicates("city_id").set_index("city_id")[["city_name","country","lat","lon"]]; c["sig"]=sig
grp=c.groupby("sig"); sizes=grp.size()
print("cities sharing a byte-identical full forecast with >=1 other city:", (sizes[sizes>1]).sum(), " in", (sizes>1).sum(), "groups; largest group:", sizes.max())
print("group size dist:", sizes.value_counts().sort_index().to_dict())
print("cross-country identical groups:", (grp.country.nunique()>1).sum())
fil=df[~df.stub].groupby(key).temp_day_c.mean().sort_values(ascending=False)
top10=fil.head(10); ids=[k[0] for k in top10.index]
print("\nQ5 top-10 tie groups:"); 
for cid in ids:
    s=c.loc[cid,"sig"]; members=c[c.sig==s]
    if len(members)>1: print(f"  {c.loc[cid,'city_name']} ({c.loc[cid,'country']}) shares forecast with: {[(n,k) for n,k in zip(members.city_name,members.country) if n!=c.loc[cid,'city_name']]}")
# collapsed ranking: one entry per signature
fil_df=fil.reset_index(); fil_df["sig"]=fil_df.city_id.map(c.sig); collapsed=fil_df.drop_duplicates("sig").head(10)
print("Collapsed top-10 (one per grid cell):"); print(collapsed[["city_name","country","temp_day_c"]].round(2).to_string(index=False))

print("\n=== 3. Q5 SENSITIVITY: temp.max / horizon cap ===")
v={}
v["filtered temp_day (final)"]=fil.head(10)
v["temp_max, stub excl"]=df[~df.stub].groupby(key).temp_max_c.mean().sort_values(ascending=False).head(10)
v["temp_day, days 0-6 only"]=df[(~df.stub)&(df.day_idx<=6)].groupby(key).temp_day_c.mean().sort_values(ascending=False).head(10)
v["temp_day, days 0-3 (pre-switch)"]=df[(~df.stub)&(df.day_idx<=3)].groupby(key).temp_day_c.mean().sort_values(ascending=False).head(10)
base=set(v["filtered temp_day (final)"].index)
for name,s in v.items():
    print(f"\n{name}:  overlap with final = {len(base&set(s.index))}/10")
    print("   "+" | ".join(f"{n} {val:.1f}" for (_,n,_),val in s.items()))

print("\n=== 4. MODEL SWITCH AT DAY 4 — full characterisation ===")
d=df.sort_values(["line_no","day_idx"]).copy()
for col in ["pressure","speed","clouds","uvi","temp_day"]:
    d[col+"_jump"]=d.groupby("line_no")[col].diff().abs()
g=d.groupby("day_idx")
summary=pd.DataFrame({
 "humidity_zero":g.humidity.apply(lambda s:(s==0).mean()),
 "clouds_label":g.weather_main.apply(lambda s:(s=="Clouds").mean()),
 "night_icon":g.weather_icon.apply(lambda s:s.str.endswith("n").mean()),
 "rain_key":g.has_rain_key.mean(),
 "uvi_frozen":g.apply(lambda x:(x.uvi==x.uvi.shift()).mean() if x.name>0 else np.nan, include_groups=False),
 "stub":g.stub.mean(),
 "pressure_jump_med":g.pressure_jump.median(),
 "pressure_jump_p99":g.pressure_jump.quantile(.99),
 "speed_jump_med":g.speed_jump.median(),
 "dt_hour_shift":d.assign(h=d.dt_utc.dt.hour).groupby("day_idx").apply(lambda x:(x.h!=x.h.shift()).mean() if x.name>0 else np.nan, include_groups=False),
 "clouds_pct_mean":g.clouds.mean(),
}).round(3)
print(summary.to_string())
# pressure jump at day 3->4 vs elsewhere
pj=d[d.day_idx.between(1,15)].groupby("day_idx").pressure_jump.quantile(.9).round(2); print("\np90 |Δpressure| by day_idx:",pj.to_dict())
print("cities with |Δpressure| > 20 hPa at day 4:", (d[(d.day_idx==4)&(d.pressure_jump>20)].line_no.nunique()), " at any other day:", d[(d.day_idx!=4)&(d.pressure_jump>20)].line_no.nunique())
