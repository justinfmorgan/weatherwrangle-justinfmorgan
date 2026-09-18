import os, numpy as np, pandas as pd, pycountry
from scipy.spatial import cKDTree
pd.set_option("display.width",220); pd.set_option("display.max_columns",30)
df=pd.read_pickle(os.environ.get("WW_SCRATCH",".")+"/daily.pkl")
c=df.drop_duplicates("line_no")[["line_no","city_id","city_name","country","lat","lon","n_days"]].reset_index(drop=True)

print("=== A. COUNTRY CODE VALIDITY vs ISO-3166 ===")
iso={x.alpha_2 for x in pycountry.countries}
codes=set(c.country); bad=sorted(codes-iso)
print("codes in file:",len(codes)," valid ISO:",len(codes&iso)," NOT in ISO list:",bad)
for b in bad: print("  ",b,":",c[c.country==b][["city_name","lat","lon"]].head(3).values.tolist())
# well-known ambiguous/legacy codes
for k in ["XK","AN","CS","YU","SU","UK","EU","ZR","TP","BU"]:
    if k in codes: print("  legacy/non-standard code present:",k,(c.country==k).sum())

print("\n=== B. EXACT / NEAR-DUPLICATE COORDINATES (independent of name) ===")
R=6371.0
def to_xyz(lat,lon):
    la,lo=np.radians(lat),np.radians(lon); return np.c_[np.cos(la)*np.cos(lo),np.cos(la)*np.sin(lo),np.sin(la)]*R
xyz=to_xyz(c.lat.values,c.lon.values); tree=cKDTree(xyz)
for km in [0.0,0.5,1.0,2.0,5.0]:
    pairs=tree.query_pairs(r=km+1e-9)
    same_ctry=sum(1 for i,j in pairs if c.country[i]==c.country[j]); same_name=sum(1 for i,j in pairs if c.city_name[i]==c.city_name[j])
    print(f"pairs within {km:>4} km: {len(pairs):>5}   same country: {same_ctry:>5}   same name: {same_name:>4}   cross-country: {len(pairs)-same_ctry}")
pairs=sorted(tree.query_pairs(r=2.0))
rows=[(c.city_id[i],c.city_name[i],c.country[i],c.city_id[j],c.city_name[j],c.country[j],round(float(np.linalg.norm(xyz[i]-xyz[j])),2)) for i,j in pairs]
near=pd.DataFrame(rows,columns=["id_a","name_a","ctry_a","id_b","name_b","ctry_b","km"]).sort_values("km")
print("\nall pairs within 2 km:"); print(near.to_string(index=False))
# are near-dup pairs' forecasts identical?
fc=df.groupby("city_id").apply(lambda g: hash(tuple(g.temp_day.round(2))), include_groups=False)
near["same_forecast"]=[fc[a]==fc[b] for a,b in zip(near.id_a,near.id_b)]
print("\nnear-dup pairs with byte-identical temp_day series:",near.same_forecast.sum(),"of",len(near))

print("\n=== C. SAME NAME, SAME COUNTRY — are they really distinct places? ===")
g=c.groupby(["city_name","country"])
dup=c[c.duplicated(["city_name","country"],keep=False)].copy()
def spread(gr):
    p=to_xyz(gr.lat.values,gr.lon.values); d=np.linalg.norm(p[:,None]-p[None],axis=2); return d[np.triu_indices(len(gr),1)].min()
mind=dup.groupby(["city_name","country"]).apply(spread, include_groups=False).rename("min_km_between_namesakes")
print("dup (name,country) groups:",len(mind))
print("min distance between namesakes — distribution (km):"); print(mind.describe(percentiles=[.05,.1,.25,.5]).round(1).to_string())
print("groups whose namesakes are < 5 km apart (suspicious — likely true duplicates):"); print(mind[mind<5].sort_values().to_string())
print("groups whose namesakes are 5-25 km apart (adjacent towns / suburbs?):", (mind.between(5,25)).sum())

print("\n=== D. SAME NAME, DIFFERENT COUNTRY ===")
xn=c.groupby("city_name").country.nunique(); xn=xn[xn>1]
print("names appearing in >1 country:",len(xn)," (e.g.)",xn.sort_values(ascending=False).head(8).to_dict())
# cross-country namesakes that are also geographically close (border towns / miscoded country?)
sub=c[c.city_name.isin(xn.index)]
close=[]
for name,gr in sub.groupby("city_name"):
    p=to_xyz(gr.lat.values,gr.lon.values); d=np.linalg.norm(p[:,None]-p[None],axis=2)
    for i in range(len(gr)):
        for j in range(i+1,len(gr)):
            if gr.country.iloc[i]!=gr.country.iloc[j] and d[i,j]<50: close.append((name,gr.country.iloc[i],gr.country.iloc[j],round(float(d[i,j]),1)))
print("cross-country namesakes within 50 km (possible country-code error or border town):",len(close)); print(close[:15])

print("\n=== E. IS EACH CITY GEOGRAPHICALLY PLAUSIBLE FOR ITS COUNTRY CODE? ===")
# distance from each city to the nearest OTHER city with the same country code; isolated outliers = suspect code
out=[]
for ctry,gr in c.groupby("country"):
    if len(gr)<3: continue
    p=to_xyz(gr.lat.values,gr.lon.values); t=cKDTree(p); d,_=t.query(p,k=2); nn=d[:,1]
    med=np.median(nn)
    for k,(idx,row) in enumerate(gr.iterrows()):
        if nn[k]>max(1500, 8*med): out.append((row.city_id,row.city_name,ctry,row.lat,row.lon,round(float(nn[k])),round(float(med))))
o=pd.DataFrame(out,columns=["city_id","city_name","country","lat","lon","km_to_nearest_same_country","country_median_nn_km"]).sort_values("km_to_nearest_same_country",ascending=False)
print("cities > max(1500 km, 8x country median) from any other city with the same code:",len(o)); print(o.head(25).to_string(index=False))
print("countries with <3 cities (can't test):",(c.country.value_counts()<3).sum())

print("\n=== F. IMPACT ON Q1-Q3 ===")
print("Q1 unique city_id:",c.city_id.nunique()," unique rounded (lat,lon) @3dp:",c[["lat","lon"]].round(3).drop_duplicates().shape[0]," @2dp:",c[["lat","lon"]].round(2).drop_duplicates().shape[0])
print("Q2 countries:",c.country.nunique()," of which ISO-valid:",len(codes&iso))
print("Q3 top10 unchanged if we drop all cities in <2km pairs? ->", c[~c.city_id.isin(set(near.id_a)|set(near.id_b))].country.value_counts().head(10).to_dict())
near.to_csv(os.environ.get("WW_OUT",".")+"/reexam_near_duplicate_cities.csv",index=False); o.to_csv(os.environ.get("WW_OUT",".")+"/reexam_geographic_outliers.csv",index=False)
