import os
import pandas as pd, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
SP=os.environ.get("WW_SCRATCH", ".")
OUT="/Users/justinmorgan/Desktop/evidently-takehome/analysis"
df=pd.read_pickle(f"{SP}/daily.pkl")
BLUE,ORANGE,MUTED,GRID="#2a78d6","#eb6834","#52514e","#e4e3df"
plt.rcParams.update({"font.size":10,"axes.edgecolor":GRID,"axes.spines.top":False,"axes.spines.right":False,"axes.grid":True,"grid.color":GRID,
 "grid.linewidth":0.6,"axes.titleweight":"bold","axes.titlelocation":"left","figure.facecolor":"#fcfcfb","axes.facecolor":"#fcfcfb","axes.labelcolor":MUTED,"xtick.color":MUTED,"ytick.color":MUTED})
t=df[["temp_day","temp_min","temp_max","temp_night","temp_eve","temp_morn"]]; df["deg"]=t.nunique(axis=1)==1; df["c"]=df.temp_day-273.15
key=["city_id","city_name","country"]
lit=df.groupby(key).c.mean().sort_values(ascending=False); fil=df[~df.deg].groupby(key).c.mean().sort_values(ascending=False)
top=sorted(set(lit.head(10).index)|set(fil.head(10).index), key=lambda k:-fil[k])
fig,axes=plt.subplots(1,2,figsize=(14,5),gridspec_kw={"width_ratios":[1,1.15]}); fig.subplots_adjust(wspace=0.55)
ax=axes[0]; lab=[f"{n} ({c})" for _,n,c in top][::-1]; y=np.arange(len(top))
ax.barh(y+0.2,[lit[k] for k in top][::-1],height=0.38,color=MUTED,label="literal (all days)")
ax.barh(y-0.2,[fil[k] for k in top][::-1],height=0.38,color=ORANGE,label="filtered (stub day excluded)")
ax.set_yticks(y); ax.set_yticklabels(lab); ax.set_xlim(37.5,40.3); ax.set_xlabel("mean temp.day (°C)"); ax.legend(frameon=False,fontsize=9,loc="lower right")
ax.set_title("Q5 — union of both top-10s: literal vs filtered mean")
ax=axes[1]
# what the stub day does: per-city stub temp_day vs mean of the other days
stub=df[df.deg].set_index("city_id").c; rest=df[~df.deg].groupby("city_id").c.mean()
delta=(stub-rest.reindex(stub.index)).dropna()
ax.hist(delta,bins=80,color=BLUE,edgecolor="#fcfcfb",linewidth=0.3); ax.axvline(0,color=MUTED,lw=1)
ax.set_title("Why it matters: stub-day temp.day minus city's mean of real days"); ax.set_xlabel("°C"); ax.set_ylabel("cities")
ax.set_ylim(0,ax.get_ylim()[1]*1.35); ax.text(0.02,0.97,f"n={len(delta):,} cities with a stub day\nmedian {delta.median():.2f} °C, mean {delta.mean():.2f} °C\n{(delta<0).mean():.0%} of stubs are cooler than the city's real days",transform=ax.transAxes,ha="left",va="top",fontsize=9,color=MUTED)
fig.savefig(f"{OUT}/q5_literal_vs_filtered.png",dpi=130,bbox_inches="tight")
print("union size:",len(top)); print(pd.DataFrame({"literal":[lit[k] for k in top],"filtered":[fil[k] for k in top],"lit_rank":[list(lit.index).index(k)+1 for k in top],"fil_rank":[list(fil.index).index(k)+1 for k in top]},index=[f"{n} ({c})" for _,n,c in top]).round(2).to_string())
print("stub delta describe:"); print(delta.describe().round(2).to_string())
# --- humidity refinement check for ANSWERS.md
print("real-humidity days per city:", df.assign(h=df.humidity>0).groupby("line_no").h.sum().value_counts().to_dict())
