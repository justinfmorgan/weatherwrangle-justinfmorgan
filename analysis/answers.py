import os
import pandas as pd, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
pd.set_option("display.width",200); pd.set_option("display.max_columns",20)
SP=os.environ.get("WW_SCRATCH", ".")
OUT="/Users/justinmorgan/Desktop/evidently-takehome/analysis"
df = pd.read_pickle(f"{SP}/daily.pkl")
BLUE,ORANGE,AQUA,YELLOW="#2a78d6","#eb6834","#1baf7a","#eda100"; INK,MUTED,GRID="#0b0b0b","#52514e","#e4e3df"
plt.rcParams.update({"font.size":10,"axes.edgecolor":GRID,"axes.spines.top":False,"axes.spines.right":False,"axes.grid":True,"grid.color":GRID,
 "grid.linewidth":0.6,"axes.titleweight":"bold","axes.titlelocation":"left","figure.facecolor":"#fcfcfb","axes.facecolor":"#fcfcfb",
 "text.color":INK,"axes.labelcolor":MUTED,"xtick.color":MUTED,"ytick.color":MUTED})
cities = df.drop_duplicates("line_no")
t = df[["temp_day","temp_min","temp_max","temp_night","temp_eve","temp_morn"]]
df["degenerate"] = t.nunique(axis=1)==1

# ---------- Q1 ----------
n_lines = len(cities); n_ids = cities.city_id.nunique(); n_namecountry = cities[["city_name","country"]].drop_duplicates().shape[0]
print("Q1 lines:", n_lines, " unique ids:", n_ids, " unique (name,country):", n_namecountry)
fig,ax=plt.subplots(figsize=(8,3))
vals=[n_lines,n_ids,n_namecountry]; labs=["NDJSON lines","unique city.id","unique (name,country)"]
ax.barh(labs,vals,color=[BLUE,BLUE,ORANGE],height=0.55)
for i,v in enumerate(vals): ax.text(v+150,i,f"{v:,}",va="center",fontsize=10)
ax.set_xlim(0,26000); ax.set_title("Q1 — city record count: three ways of counting"); ax.invert_yaxis()
fig.savefig(f"{OUT}/q1_city_records.png",dpi=130,bbox_inches="tight")

# ---------- Q2 / Q3 ----------
cc = cities.country.value_counts()
print("Q2 unique countries:", cc.size)
print("Q3 top 10:"); print(cc.head(10).to_string())
fig,axes=plt.subplots(1,2,figsize=(13,4.2),gridspec_kw={"width_ratios":[1.2,1]}); fig.subplots_adjust(wspace=0.35)
ax=axes[0]; ax.hist(cc.values,bins=np.logspace(0,3.6,40),color=BLUE,edgecolor="#fcfcfb",linewidth=0.3); ax.set_xscale("log")
ax.set_title(f"Q2 — cities per country across {cc.size} countries (log x)"); ax.set_xlabel("cities in country"); ax.set_ylabel("countries")
ax.axvline(10,color=MUTED,ls="--",lw=1); ax.text(10.5,ax.get_ylim()[1]*0.9,f"{(cc>=10).sum()} countries have ≥10 cities\n{(cc==1).sum()} have exactly 1",fontsize=9,color=MUTED)
ax=axes[1]; top=cc.head(10)[::-1]; ax.barh(top.index,top.values,color=BLUE,height=0.6)
for i,v in enumerate(top.values): ax.text(v+30,i,f"{v:,}",va="center",fontsize=9)
ax.set_xlim(0,3400); ax.set_title("Q3 — top 10 countries by city count"); ax.set_xlabel("cities")
fig.savefig(f"{OUT}/q2_q3_countries.png",dpi=130,bbox_inches="tight")

# ---------- Q4 ----------
df["date"] = df.dt_utc.dt.date
n_rows=len(df); n_uniq=df.drop_duplicates(["city_id","country","date"]).shape[0]
per = cities.n_days.value_counts().sort_index()
print("Q4 exploded rows:", n_rows, " unique (city_id,country,date):", n_uniq, " unique (name,country,date):", df.drop_duplicates(['city_name','country','date']).shape[0])
print("   rows if 14-day horizon:", n_lines*14, " rows excluding degenerate last day:", (~df.degenerate).sum())
fig,axes=plt.subplots(1,2,figsize=(12,3.8)); fig.subplots_adjust(wspace=0.35)
ax=axes[0]; ax.bar(per.index.astype(str),per.values,color=BLUE,width=0.5)
for i,v in enumerate(per.values): ax.text(i,v+200,f"{v:,} cities",ha="center",fontsize=9)
ax.set_title("Q4 — forecast length per city (filename says 14)"); ax.set_xlabel("days in data[]"); ax.set_ylabel("cities"); ax.set_ylim(0,18500)
ax=axes[1]; scen={"if 14 days/city":n_lines*14,"if 16 days/city":n_lines*16,"actual rows":n_rows,"if 17 days/city":n_lines*17}
ax.barh(list(scen),list(scen.values()),color=[MUTED,MUTED,BLUE,MUTED],height=0.55); ax.invert_yaxis()
for i,v in enumerate(scen.values()): ax.text(v+3000,i,f"{v:,}",va="center",fontsize=9)
ax.set_xlim(0,440000); ax.set_title("Q4 — where the actual row count sits"); ax.set_xlabel("rows")
fig.savefig(f"{OUT}/q4_exploded_rows.png",dpi=130,bbox_inches="tight")

# ---------- Q5 ----------
df["temp_day_c"]=df.temp_day-273.15
m_all = df.groupby(["city_id","city_name","country"]).temp_day_c.mean()
m_clean = df[~df.degenerate].groupby(["city_id","city_name","country"]).temp_day_c.mean()
top_all=m_all.sort_values(ascending=False).head(10); top_clean=m_clean.sort_values(ascending=False).head(10)
print("Q5 top 10 (all days):"); print(top_all.round(2).to_string())
print("Q5 top 10 (excluding degenerate last-day rows):"); print(top_clean.round(2).to_string())
print("   same set?", set(top_all.index)==set(top_clean.index), " rank change:", [a==b for a,b in zip(top_all.index,top_clean.index)])
print("   city-mean temp_day distribution (°C):"); print(m_all.describe(percentiles=[.5,.9,.99,.999]).round(2).to_string())
fig,axes=plt.subplots(1,2,figsize=(13,4.2),gridspec_kw={"width_ratios":[1.2,1]}); fig.subplots_adjust(wspace=0.4)
ax=axes[0]; ax.hist(m_all.values,bins=70,color=BLUE,edgecolor="#fcfcfb",linewidth=0.3)
ax.axvline(top_all.min(),color=ORANGE,lw=1.5); ax.text(top_all.min()-0.5,ax.get_ylim()[1]*0.85,f"top-10 cutoff\n{top_all.min():.1f} °C",ha="right",fontsize=9,color=ORANGE)
ax.set_title(f"Q5 — per-city mean temp.day, {len(m_all):,} cities"); ax.set_xlabel("mean temp.day (°C)"); ax.set_ylabel("cities")
ax=axes[1]; lab=[f"{n} ({c})" for _,n,c in top_all.index][::-1]; ax.barh(lab,top_all.values[::-1],color=ORANGE,height=0.6)
for i,v in enumerate(top_all.values[::-1]): ax.text(v+0.1,i,f"{v:.2f}",va="center",fontsize=9)
ax.set_xlim(30,40); ax.set_title("Q5 — top 10 hottest by mean temp.day (°C)"); ax.set_xlabel("°C")
fig.savefig(f"{OUT}/q5_hottest_cities.png",dpi=130,bbox_inches="tight")

# ---------- Q6 ----------
sf = df[df.city_id==5391959].sort_values("dt").copy()
tidy = pd.DataFrame({"date":sf.dt_utc.dt.strftime("%Y-%m-%d"),"temp_min":(sf.temp_min-273.15).round(1),"temp_max":(sf.temp_max-273.15).round(1),
                     "humidity":sf.humidity,"weather_description":sf.weather_desc,"day_idx":sf.day_idx,"degenerate":sf.degenerate}).reset_index(drop=True)
print("Q6 San Francisco (id 5391959):"); print(tidy.to_string(index=False))
tidy.drop(columns=["day_idx","degenerate"]).to_csv(f"{OUT}/q6_san_francisco.csv",index=False)
us = df[df.country=="US"]
fig,axes=plt.subplots(1,2,figsize=(13,4.2)); fig.subplots_adjust(wspace=0.3)
ax=axes[0]; ax.hist((us.temp_min-273.15),bins=60,color=AQUA,alpha=0.8,label="US temp_min",edgecolor="#fcfcfb",linewidth=0.3)
ax.hist((us.temp_max-273.15),bins=60,color=ORANGE,alpha=0.6,label="US temp_max",edgecolor="#fcfcfb",linewidth=0.3)
ax.axvspan(tidy.temp_min.min(),tidy.temp_max.max(),color=BLUE,alpha=0.12); ax.text(tidy.temp_min.min(),ax.get_ylim()[1]*0.9,"SF range",color=BLUE,fontsize=9)
ax.set_title("Q6 — SF temps vs all US city-day rows (°C)"); ax.set_xlabel("°C"); ax.set_ylabel("rows"); ax.legend(frameon=False,fontsize=9)
ax=axes[1]; x=np.arange(len(tidy))
ax.fill_between(x,tidy.temp_min,tidy.temp_max,color=BLUE,alpha=0.15); ax.plot(x,tidy.temp_max,color=ORANGE,lw=2,label="temp_max"); ax.plot(x,tidy.temp_min,color=AQUA,lw=2,label="temp_min")
ax.set_xticks(x); ax.set_xticklabels(tidy.date.str[5:],rotation=60,fontsize=8); ax.set_ylabel("°C"); ax.set_title("Q6 — San Francisco 16-day forecast")
h0=int((tidy.humidity==0).idxmax()); ax.axvspan(h0-0.5,len(tidy)-0.5,color=YELLOW,alpha=0.08); ax.text(h0,tidy.temp_max.max()+0.3,f"humidity = 0 from {tidy.date[h0]} onward",fontsize=8,color=MUTED)
ax.legend(frameon=False,fontsize=9,loc="lower left")
fig.savefig(f"{OUT}/q6_san_francisco.png",dpi=130,bbox_inches="tight")
print("done")
