import os
import json
import pandas as pd

rows = []
with open("daily_14.json") as f:
    for line_no, line in enumerate(f, 1):
        rec = json.loads(line)
        c = rec["city"]
        for idx, d in enumerate(rec["data"]):
            w = d["weather"][0]
            rows.append({
                "line_no": line_no,
                "city_id": c["id"], "city_name": c["name"], "country": c["country"],
                "lat": c["coord"]["lat"], "lon": c["coord"]["lon"],
                "time": rec["time"], "n_days": len(rec["data"]), "day_idx": idx,
                "dt": d["dt"],
                "temp_day": d["temp"]["day"], "temp_min": d["temp"]["min"], "temp_max": d["temp"]["max"],
                "temp_night": d["temp"]["night"], "temp_eve": d["temp"]["eve"], "temp_morn": d["temp"]["morn"],
                "pressure": d["pressure"], "humidity": d["humidity"],
                "weather_id": w["id"], "weather_main": w["main"], "weather_desc": w["description"], "weather_icon": w["icon"],
                "speed": d["speed"], "deg": d["deg"], "clouds": d["clouds"],
                "rain": d.get("rain"), "snow": d.get("snow"), "uvi": d["uvi"],
                "has_rain_key": "rain" in d, "has_snow_key": "snow" in d,
            })
df = pd.DataFrame(rows)
df["time_utc"] = pd.to_datetime(df["time"], unit="s", utc=True)
df["dt_utc"] = pd.to_datetime(df["dt"], unit="s", utc=True)
df.to_pickle(os.environ.get("WW_SCRATCH", ".") + "/daily.pkl")
print(df.shape)
print(df.dtypes)
