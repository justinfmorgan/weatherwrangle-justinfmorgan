import os, numpy as np, pandas as pd
from scipy.spatial import cKDTree
from scipy.sparse.csgraph import connected_components
from scipy.sparse import coo_matrix
pd.set_option("display.width",220)
df=pd.read_pickle(os.environ.get("WW_SCRATCH",".")+"/daily.pkl")
c=df.drop_duplicates("line_no")[["city_id","city_name","country","lat","lon"]].reset_index(drop=True)
la,lo=np.radians(c.lat.values),np.radians(c.lon.values); xyz=np.c_[np.cos(la)*np.cos(lo),np.cos(la)*np.sin(lo),np.sin(la)]*6371
tree=cKDTree(xyz); base=c.country.value_counts()
print("Q3 sensitivity: count one city per near-duplicate cluster (same country only)")
rows={}
for km in [0.5,1,2,5]:
    pairs=[(i,j) for i,j in tree.query_pairs(r=km) if c.country[i]==c.country[j]]
    if not pairs: rows[km]=base; continue
    i,j=zip(*pairs); m=coo_matrix((np.ones(len(i)),(i,j)),shape=(len(c),len(c)))
    n,lab=connected_components(m,directed=False); c[f"cl{km}"]=lab
    dedup=c.drop_duplicates(f"cl{km}"); rows[km]=dedup.country.value_counts()
    top_pairs=pd.Series([c.country[a] for a in i]).value_counts().head(6).to_dict()
    print(f"  {km:>3} km: {len(pairs):>5} same-country pairs -> {len(c)-len(dedup):>4} cities removed; most affected: {top_pairs}")
tab=pd.DataFrame({"raw":base,**{f"dedup@{k}km":v for k,v in rows.items()}}).fillna(0).astype(int)
tab["rank_raw"]=tab.raw.rank(ascending=False,method="min").astype(int)
for k in rows: tab[f"rank@{k}km"]=tab[f"dedup@{k}km"].rank(ascending=False,method="min").astype(int)
print("\nTop-12 by raw count, with deduped counts and ranks:"); print(tab.sort_values("raw",ascending=False).head(12).to_string())
print("\nTop-10 membership by threshold:")
for k in rows: print(f"  @{k}km:", list(rows[k].head(10).index))
print("\nFR near-pairs example (2 km):"); fr=c[c.country=="FR"]; 
pairs=[(i,j) for i,j in tree.query_pairs(r=2) if c.country[i]=="FR" and c.country[j]=="FR"]
print(pd.DataFrame([(c.city_name[i],c.city_name[j]) for i,j in pairs[:12]],columns=["a","b"]).to_string(index=False))
