import os
import pandas as pd, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
SP=os.environ.get("WW_SCRATCH", ".")
df = pd.read_pickle(f"{SP}/daily.pkl")
BLUE,ORANGE,AQUA,YELLOW="#2a78d6","#eb6834","#1baf7a","#eda100"
INK,MUTED,GRID="#0b0b0b","#52514e","#e4e3df"
plt.rcParams.update({"font.size":10,"axes.edgecolor":GRID,"axes.spines.top":False,"axes.spines.right":False,
    "axes.grid":True,"grid.color":GRID,"grid.linewidth":0.6,"axes.titleweight":"bold","axes.titlelocation":"left",
    "figure.facecolor":"#fcfcfb","axes.facecolor":"#fcfcfb","text.color":INK,"axes.labelcolor":MUTED,"xtick.color":MUTED,"ytick.color":MUTED})

t = df[["temp_day","temp_min","temp_max","temp_night","temp_eve","temp_morn"]]
df["degenerate"] = t.nunique(axis=1)==1
d = df.sort_values(["line_no","day_idx"])
uvi_prev = d.groupby("line_no").uvi.shift(); df.loc[d.index,"uvi_frozen"] = (d.uvi==uvi_prev)

fig, axes = plt.subplots(2,2, figsize=(13,8.5)); fig.subplots_adjust(hspace=0.45, wspace=0.28)
g = df.groupby("day_idx")
ax=axes[0,0]; s=g.humidity.apply(lambda x:(x==0).mean()*100)
ax.bar(s.index, s.values, color=BLUE, width=0.7); ax.set_title("Share of rows with humidity = 0, by forecast day index")
ax.set_ylabel("% of rows"); ax.set_xlabel("day_idx"); ax.set_xticks(range(17)); ax.set_ylim(0,118)
ax.text(3.5,108,"days 4+ : humidity is 0 in 100% of rows",color=MUTED,fontsize=9)

ax=axes[0,1]; s=g.degenerate.mean()*100
ax.bar(s.index, s.values, color=ORANGE, width=0.7); ax.set_title("Share of rows where all six temp fields are identical")
ax.set_ylabel("% of rows"); ax.set_xlabel("day_idx"); ax.set_xticks(range(17))

ax=axes[1,0]; s=g.uvi_frozen.mean()*100
ax.bar(s.index, s.values, color=AQUA, width=0.7); ax.set_title("Share of rows whose UVI equals the previous day's UVI")
ax.set_ylabel("% of rows"); ax.set_xlabel("day_idx"); ax.set_xticks(range(17))

ax=axes[1,1]
mix = pd.crosstab(df.day_idx, df.weather_main, normalize="index")*100
order=["Clear","Rain","Snow","Clouds"]; cols=[YELLOW,BLUE,AQUA,ORANGE]; bottom=np.zeros(len(mix))
for m,c in zip(order,cols):
    ax.bar(mix.index, mix[m], bottom=bottom, color=c, width=0.7, label=m, edgecolor="#fcfcfb", linewidth=1); bottom+=mix[m].values
ax.set_title("Weather condition mix by forecast day index"); ax.set_ylabel("% of rows"); ax.set_xlabel("day_idx"); ax.set_xticks(range(17))
ax.legend(loc="upper left", bbox_to_anchor=(1,1), frameon=False, fontsize=9)
fig.suptitle("daily_14.json — forecast-horizon artifacts (368,909 city-day rows)", x=0.01, ha="left", fontsize=13, fontweight="bold")
fig.savefig(f"{SP}/viz_horizon_artifacts.png", dpi=130, bbox_inches="tight")

# --- distributions ---
fig, axes = plt.subplots(2,3, figsize=(14,7.5)); fig.subplots_adjust(hspace=0.5, wspace=0.3)
def hist(ax, s, title, color=BLUE, bins=60, xlabel=""):
    ax.hist(s.dropna(), bins=bins, color=color, edgecolor="#fcfcfb", linewidth=0.3); ax.set_title(title); ax.set_xlabel(xlabel); ax.set_ylabel("rows")
hist(axes[0,0], df.temp_day-273.15, "temp_day (converted to °C)", xlabel="°C")
hist(axes[0,1], df.pressure, "pressure (hPa) — low tail = altitude", xlabel="hPa")
hist(axes[0,2], df[df.humidity>0].humidity, "humidity, non-zero rows only (18%)", xlabel="%", bins=40)
hist(axes[1,0], df.speed, "wind speed (m/s)", color=AQUA, xlabel="m/s")
hist(axes[1,1], df.rain, "rain (mm), key present — floor at 0.2", color=AQUA, xlabel="mm", bins=80)
hist(axes[1,2], df.uvi, "uvi", color=AQUA, xlabel="index", bins=50)
fig.suptitle("daily_14.json — field distributions", x=0.01, ha="left", fontsize=13, fontweight="bold")
fig.savefig(f"{SP}/viz_distributions.png", dpi=130, bbox_inches="tight")

# --- city map ---
c = df.drop_duplicates("line_no")
fig, ax = plt.subplots(figsize=(13,6.2)); ax.grid(False)
ax.scatter(c.lon, c.lat, s=2, color=BLUE, alpha=0.35, linewidths=0)
ax.set_xlim(-180,180); ax.set_ylim(-60,85); ax.set_xlabel("lon"); ax.set_ylabel("lat")
ax.set_title("22,635 cities — coordinate sanity check (no (0,0) points, no out-of-range coords)")
fig.savefig(f"{SP}/viz_city_map.png", dpi=130, bbox_inches="tight")
print("done")
