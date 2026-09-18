import os
import pandas as pd, numpy as np
pd.set_option("display.width", 220); pd.set_option("display.max_columns", 40)
df = pd.read_pickle(os.environ.get("WW_SCRATCH", ".") + "/daily.pkl")
cities = df.drop_duplicates("line_no")

print("=== 1. HUMIDITY == 0 ===")
print("rows with humidity==0:", (df.humidity==0).sum(), f"({(df.humidity==0).mean():.1%})")
print("humidity==0 rate by day_idx:"); print(df.groupby("day_idx").humidity.apply(lambda s:(s==0).mean()).round(3).to_string())
print("humidity nonzero dist:"); print(df[df.humidity>0].humidity.describe().to_string())
print("records where ALL days humidity==0:", (df.groupby("line_no").humidity.max()==0).sum())

print("\n=== 2. BLANK CITY NAMES ===")
print(cities[cities.city_name.str.strip()==""][["line_no","city_id","city_name","country","lat","lon"]].to_string())
print("names with leading/trailing whitespace:", (cities.city_name != cities.city_name.str.strip()).sum())
print("names containing non-ASCII:", (~cities.city_name.str.match(r"^[\x00-\x7F]*$")).sum())
print("names containing digits:", cities.city_name.str.contains(r"\d").sum())
print(cities[cities.city_name.str.contains(r"\d")].city_name.head(10).tolist())

print("\n=== 3. DUPLICATE (name,country) with different ids ===")
dupes = cities[cities.duplicated(["city_name","country"], keep=False)].sort_values(["city_name","country"])
print("dup pairs count:", dupes[["city_name","country"]].drop_duplicates().shape[0], " rows involved:", len(dupes))
print(dupes[["city_id","city_name","country","lat","lon"]].head(12).to_string())
# exact coord duplicates?
print("exact (lat,lon) duplicates across different ids:", cities.duplicated(["lat","lon"], keep=False).sum())

print("\n=== 4. FORECAST LENGTH & DT GAPS ===")
d = df.sort_values(["line_no","day_idx"]).copy()
d["gap"] = d.groupby("line_no").dt.diff()
odd = d[d.gap.isin([82800,126000])]
print("records with a 23h gap:", odd[odd.gap==82800].line_no.nunique(), " with 35h gap:", odd[odd.gap==126000].line_no.nunique())
print("23h gap: which day_idx & dt:"); print(odd[odd.gap==82800].groupby(["day_idx"]).size().to_string())
print(odd[odd.gap==82800].dt_utc.dt.date.value_counts().to_string())
print("23h-gap countries:", odd[odd.gap==82800].country.value_counts().head(8).to_dict())
print("35h gap rows:"); print(odd[odd.gap==126000][["line_no","city_name","country","day_idx","dt_utc"]].to_string())
d0 = d[d.day_idx==0][["line_no","dt_utc"]].rename(columns={"dt_utc":"d0"}); print("n_days by first-dt date:"); print(cities[["line_no","n_days"]].merge(d0, on="line_no").assign(d0=lambda x:x.d0.dt.date).groupby(["d0","n_days"]).size().to_string())

print("\n=== 5. TEMP CONSISTENCY ===")
t = df[["temp_day","temp_min","temp_max","temp_night","temp_eve","temp_morn"]]
print("min > max:", (df.temp_min > df.temp_max).sum())
print("any of day/eve/morn/night < min:", (t[["temp_day","temp_eve","temp_morn","temp_night"]].lt(df.temp_min, axis=0).any(axis=1)).sum())
print("any of day/eve/morn/night > max:", (t[["temp_day","temp_eve","temp_morn","temp_night"]].gt(df.temp_max, axis=0).any(axis=1)).sum())
alleq = (t.nunique(axis=1)==1)
print("all six temps identical:", alleq.sum(), " by day_idx:", df[alleq].day_idx.value_counts().sort_index().to_dict())
print("temps in Celsius range (<100)?", (t<100).any(axis=1).sum(), " temps <200K:", (t<200).any(axis=1).sum())
print("temp_day-temp_night spread > 30K:", ((df.temp_day-df.temp_night).abs()>30).sum())

print("\n=== 6. PRESSURE / OTHER RANGES ===")
print("pressure<700:"); print(df[df.pressure<700].drop_duplicates("line_no")[["city_name","country","lat","lon","pressure"]].head(8).to_string())
print("deg==0 rows:", (df.deg==0).sum(), " deg==360:", (df.deg==360).sum())
print("speed==0:", (df.speed==0).sum(), " speed>20:", (df.speed>20).sum())
print("uvi>15:", (df.uvi>15).sum(), " uvi max rows:"); print(df.nlargest(3,"uvi")[["city_name","country","lat","dt_utc","uvi"]].to_string())
print("rain present but ==0:", ((df.has_rain_key)&(df.rain==0)).sum(), " snow present but ==0:", ((df.has_snow_key)&(df.snow==0)).sum())
print("rain>50:"); print(df[df.rain>50][["city_name","country","dt_utc","rain","weather_desc"]].head(6).to_string())

print("\n=== 7. WEATHER CODE CONSISTENCY ===")
wc = df.groupby(["weather_id","weather_main","weather_desc"]).size().reset_index(name="n").sort_values("weather_id")
print(wc.to_string())
print("weather_id -> multiple mains:", wc.groupby("weather_id").weather_main.nunique().gt(1).sum())
print("icon suffix dist:", df.weather_icon.str[-1].value_counts().to_dict())
print("rain key absent but weather is Rain:", ((~df.has_rain_key)&(df.weather_main=="Rain")).sum())
print("rain key present but weather is Clear:", ((df.has_rain_key)&(df.weather_main=="Clear")).sum())
print("snow key present but temp_day > 288K(15C):", ((df.has_snow_key)&(df.snow>0)&(df.temp_day>288)).sum())
