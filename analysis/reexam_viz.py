import os, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
df=pd.read_pickle(os.environ.get("WW_SCRATCH",".")+"/daily.pkl"); OUT=os.environ.get("WW_OUT",".")
BLUE,ORANGE,AQUA,YELLOW,MUTED,GRID="#2a78d6","#eb6834","#1baf7a","#eda100","#52514e","#e4e3df"
plt.rcParams.update({"font.size":10,"axes.edgecolor":GRID,"axes.spines.top":False,"axes.spines.right":False,"axes.grid":True,"grid.color":GRID,
 "grid.linewidth":0.6,"axes.titleweight":"bold","axes.titlelocation":"left","figure.facecolor":"#fcfcfb","axes.facecolor":"#fcfcfb","axes.labelcolor":MUTED,"xtick.color":MUTED,"ytick.color":MUTED})
t=df[["temp_day","temp_min","temp_max","temp_night","temp_eve","temp_morn"]]; df["stub"]=t.nunique(axis=1)==1; df["c"]=df.temp_day-273.15
# relative day: align 17-day records so the stale leading day is idx -1
df["rel"]=np.where(df.n_days==17, df.day_idx-1, df.day_idx)
fig,axes=plt.subplots(2,2,figsize=(14,9)); fig.subplots_adjust(hspace=0.45,wspace=0.3)
# (a) model switch, aligned
ax=axes[0,0]; g=df[df.rel>=0].groupby("rel")
ax.plot(g.humidity.apply(lambda s:(s>0).mean())*100,color=BLUE,lw=2,marker="o",ms=4,label="humidity present")
ax.plot(g.weather_main.apply(lambda s:(s=="Clouds").mean())*100,color=ORANGE,lw=2,marker="o",ms=4,label="'Clouds' label share")
ax.plot(g.weather_icon.apply(lambda s:s.str.endswith("n").mean())*100,color=AQUA,lw=2,marker="o",ms=4,label="night icon share")
ax.plot(g.stub.mean()*100,color=YELLOW,lw=2,marker="o",ms=4,label="stub row share")
ax.axvspan(-0.5,2.5,color=BLUE,alpha=0.06); ax.text(0,92,"short-range window\n(3 real days)",fontsize=9,color=MUTED)
ax.set_title("Model switch after 3 real days (17-day records aligned)"); ax.set_xlabel("forecast day (aligned)"); ax.set_ylabel("% of rows"); ax.legend(frameon=False,fontsize=8,loc="center right"); ax.set_xticks(range(16))
# (b) rain key vs label
ax=axes[0,1]; ct=pd.crosstab(df.weather_main,df.has_rain_key).loc[["Clear","Clouds","Rain","Snow"]]
y=np.arange(4); ax.barh(y+0.2,ct[True],height=0.38,color=BLUE,label="rain key present"); ax.barh(y-0.2,ct[False],height=0.38,color=MUTED,label="rain key absent")
ax.set_yticks(y); ax.set_yticklabels(ct.index); ax.set_xlabel("rows"); ax.legend(frameon=False,fontsize=9); ax.invert_yaxis()
ax.set_title("Rain key vs weather label")
ax.text(ct[True]["Clear"]+3000,0.2,"6,158 — median 1.5 mm",va="center",fontsize=8,color=MUTED); ax.text(ct[False]["Rain"]+3000,1.8,"26,352 — all 'light rain' (amount < 0.2 mm floor)",va="center",fontsize=8,color=MUTED)
# (c) tie group sizes
ax=axes[1,0]
sig=df.sort_values(["city_id","dt"]).groupby("city_id").apply(lambda g: hash((tuple(g.temp_day),tuple(g.pressure))), include_groups=False)
sizes=sig.value_counts(); ax.hist(sizes.values,bins=np.arange(1,60,1),color=AQUA,edgecolor="#fcfcfb",linewidth=0.3)
ax.set_title(f"Forecast grid cells: {len(sizes):,} distinct forecasts for 22,635 cities"); ax.set_xlabel("cities sharing one identical forecast"); ax.set_ylabel("groups")
ax.text(0.98,0.95,f"{(sizes==1).sum():,} cities have a unique forecast\n{(sizes[sizes>1]).sum():,} (90%) share one with ≥1 other city\nlargest group: {sizes.max()} cities",transform=ax.transAxes,ha="right",va="top",fontsize=9,color=MUTED)
# (d) Q5 sensitivity overlap
ax=axes[1,1]; key=["city_id","city_name","country"]; nd=df[~df.stub]
final=set(nd.groupby(key).c.mean().nlargest(10).index)
variants={"temp_max":nd.groupby(key).temp_max.mean().nlargest(10),"literal (stubs in)":df.groupby(key).c.mean().nlargest(10),
          "days 0-9":nd[nd.day_idx<=9].groupby(key).c.mean().nlargest(10),"days 0-6":nd[nd.day_idx<=6].groupby(key).c.mean().nlargest(10),"days 0-3":nd[nd.day_idx<=3].groupby(key).c.mean().nlargest(10)}
ov={k:len(final&set(v.index)) for k,v in variants.items()}
ax.barh(list(ov),list(ov.values()),color=[BLUE if v>=8 else ORANGE for v in ov.values()],height=0.55); ax.set_xlim(0,10.5); ax.invert_yaxis()
for i,v in enumerate(ov.values()): ax.text(v+0.15,i,f"{v}/10",va="center",fontsize=9)
ax.set_title("Q5 robustness: top-10 overlap with the final (filtered, full-horizon) answer"); ax.set_xlabel("cities in common")
fig.suptitle("Reexamination — model switch, rain-key conflict, grid-cell ties, Q5 sensitivity",x=0.01,ha="left",fontsize=13,fontweight="bold")
fig.savefig(f"{OUT}/reexam_summary.png",dpi=130,bbox_inches="tight"); print("saved; overlaps:",ov)
