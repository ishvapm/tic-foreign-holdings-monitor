"""Monthly analysis of Treasury TIC SLT Table 1."""
from __future__ import annotations
import csv, html, math, re, sqlite3, statistics
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; RAW=ROOT/"data"/"slt_table1_official.txt"; OUT=ROOT/"artifacts"
FIELDS=["country","country_code","date","total_pos","total_flow","total_val","treasury_pos","treasury_flow","treasury_val","agency_pos","agency_flow","agency_val","corp_bond_pos","corp_bond_flow","corp_bond_val","equity_pos","equity_flow","equity_val"]
NUM=FIELDS[3:]; ASSETS={"Treasuries":("treasury_pos","treasury_flow","treasury_val"),"Agency bonds":("agency_pos","agency_flow","agency_val"),"Corporate bonds":("corp_bond_pos","corp_bond_flow","corp_bond_val"),"Equities":("equity_pos","equity_flow","equity_val")}
AGG=("All Countries","Of Which:","Total ","Memo:","International Organizations","Grand Total")
def number(x):
    x=x.strip().replace(",",""); return None if x.lower() in {"","na","n.a."} else float(x)
def parse(path=RAW):
    lines=path.read_text(encoding="utf-8-sig").splitlines(); start=next(i for i,x in enumerate(lines) if x.startswith("country\tcountry_code\tdate\t")); rows=[]
    for v in csv.reader(lines[start+1:],delimiter="\t"):
        if len(v)>=18 and re.fullmatch(r"\d{4}-\d{2}",v[2].strip()):
            r=dict(zip(FIELDS,v[:18])); r["country_code"]=r["country_code"].strip()
            for f in NUM:r[f]=number(r[f])
            rows.append(r)
    return rows
def is_country(r): return r["country_code"]!="99996" and not r["country"].startswith(AGG)
def robust_z(x,history):
    history=[v for v in history if v is not None]
    if len(history)<12:return None
    med=statistics.median(history); mad=statistics.median(abs(v-med) for v in history)
    return 0.0 if mad==0 and x==med else (math.copysign(99,x-med) if mad==0 else .6745*(x-med)/mad)
def anomalies(rows):
    series=defaultdict(list)
    for r in rows:
        if is_country(r): series[r["country_code"]].append(r)
    found=[]
    for values in series.values():
        values.sort(key=lambda r:r["date"])
        for idx in range(1,len(values)):
            cur,prev=values[idx],values[idx-1]
            for asset,(pos,flow,val) in ASSETS.items():
                if cur[pos] is None or prev[pos] is None:continue
                change=cur[pos]-prev[pos]
                hist=[]
                for j in range(max(1,idx-24),idx):
                    if values[j][pos] is not None and values[j-1][pos] is not None:hist.append(values[j][pos]-values[j-1][pos])
                z=robust_z(change,hist)
                residual=None if cur[flow] is None or cur[val] is None else change-cur[flow]-cur[val]
                residual_pct=None if residual is None or not prev[pos] else 100*residual/prev[pos]
                score=abs(z or 0)
                # Apply the dollar threshold after calculating the historical score.
                if z is not None and score>=4 and abs(change)>=500:
                    severity="HIGH" if score>=7 else "MEDIUM"
                    found.append({"date":cur["date"],"country":cur["country"],"country_code":cur["country_code"],"asset":asset,"signal":"UNUSUAL_POSITION_CHANGE","severity":severity,"position_usd_mm":cur[pos],"change_usd_mm":change,"flow_usd_mm":cur[flow],"valuation_usd_mm":cur[val],"residual_usd_mm":residual,"residual_pct":residual_pct,"robust_z":z,"review_note":"Check transactions, valuation, reclassification, and revisions."})
                if residual_pct is not None and abs(residual_pct)>=5 and abs(residual)>=500:
                    found.append({"date":cur["date"],"country":cur["country"],"country_code":cur["country_code"],"asset":asset,"signal":"LARGE_UNEXPLAINED_RESIDUAL","severity":"HIGH" if abs(residual_pct)>=10 else "MEDIUM","position_usd_mm":cur[pos],"change_usd_mm":change,"flow_usd_mm":cur[flow],"valuation_usd_mm":cur[val],"residual_usd_mm":residual,"residual_pct":residual_pct,"robust_z":z,"review_note":"Check source data, revisions, and other adjustments."})
    return sorted(found,key=lambda x:(x["date"],x["severity"],abs(x["robust_z"] or 0)),reverse=True)
def concentration(rows):
    out=[]
    for date in sorted({r["date"] for r in rows}):
        vals=[r["total_pos"] for r in rows if r["date"]==date and is_country(r) and r["total_pos"] is not None and r["total_pos"]>0]; total=sum(vals); shares=[v/total for v in vals]; hhi=sum(s*s for s in shares)
        out.append({"date":date,"covered_total_usd_mm":total,"hhi":hhi,"effective_number":1/hhi,"top5_share":sum(sorted(shares,reverse=True)[:5])})
    return out
def kmeans_latest(rows,k=4):
    latest=max(r["date"] for r in rows); data=[]
    for r in rows:
        if r["date"]==latest and is_country(r) and r["total_pos"] and r["total_pos"]>=10000 and all(r[p] is not None for p,_,_ in ASSETS.values()):
            x=[r[p]/r["total_pos"] for p,_,_ in ASSETS.values()]; data.append((r,x))
    data.sort(key=lambda z:z[0]["total_pos"],reverse=True); centers=[data[0][1]]
    while len(centers)<k: centers.append(max(data,key=lambda z:min(sum((a-b)**2 for a,b in zip(z[1],c)) for c in centers))[1])
    labels=[0]*len(data)
    for _ in range(50):
        new=[min(range(k),key=lambda j:sum((a-b)**2 for a,b in zip(x,centers[j]))) for _,x in data]
        if new==labels:break
        labels=new
        for j in range(k):
            pts=[data[i][1] for i,l in enumerate(labels) if l==j]
            if pts:centers[j]=[sum(p[d] for p in pts)/len(pts) for d in range(4)]
    names=[]; asset_names=list(ASSETS)
    for c in centers:names.append(asset_names[max(range(4),key=lambda i:c[i])]+"-oriented")
    return [{"date":latest,"country":r["country"],"country_code":r["country_code"],"holdings_usd_mm":r["total_pos"],"cluster":names[l],**{a.lower().replace(" ","_")+"_share":x[i] for i,a in enumerate(asset_names)}} for (r,x),l in zip(data,labels)]
def write_csv(path,rows):
    if not rows:return
    with path.open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def build(rows):
    OUT.mkdir(exist_ok=True); signals=anomalies(rows); conc=concentration(rows); clusters=kmeans_latest(rows); latest=max(r["date"] for r in rows); totals={r["date"]:r for r in rows if r["country_code"]=="99996"}; t=totals[latest]; prior=totals[sorted(totals)[-2]]
    recent=[s for s in signals if s["date"]>=sorted(totals)[-13]]; high=[s for s in recent if s["severity"]=="HIGH"]; c=conc[-1]
    write_csv(OUT/"anomaly_cases.csv",signals);write_csv(OUT/"concentration_history.csv",conc);write_csv(OUT/"portfolio_clusters.csv",clusters)
    db=OUT/"tic_stress_monitor.db";db.unlink(missing_ok=True);con=sqlite3.connect(db)
    con.execute("CREATE TABLE anomaly_cases(date TEXT,country TEXT,country_code TEXT,asset TEXT,signal TEXT,severity TEXT,position_usd_mm REAL,change_usd_mm REAL,flow_usd_mm REAL,valuation_usd_mm REAL,residual_usd_mm REAL,residual_pct REAL,robust_z REAL,review_note TEXT)");con.executemany("INSERT INTO anomaly_cases VALUES("+",".join("?"*14)+")",[list(x.values()) for x in signals])
    con.execute("CREATE TABLE concentration(date TEXT,covered_total_usd_mm REAL,hhi REAL,effective_number REAL,top5_share REAL)");con.executemany("INSERT INTO concentration VALUES(?,?,?,?,?)",[list(x.values()) for x in conc]);con.commit();con.close()
    top=sorted([r for r in rows if r["date"]==latest and is_country(r) and r["total_pos"]],key=lambda r:r["total_pos"],reverse=True)[:5]
    report=f"# Monthly TIC Holdings Review\n\n**Data through {latest}**\n\n## Summary\n\nForeign residents held **${t['total_pos']/1e6:,.2f} trillion** of U.S. long-term securities. The position changed **${(t['total_pos']-prior['total_pos'])/1000:+,.1f} billion** in the latest month. Net transactions were **${t['total_flow']/1000:+,.1f} billion** and valuation changes were **${t['total_val']/1000:+,.1f} billion**.\n\nThe five largest country positions accounted for **{c['top5_share']:.1%}** of covered holdings. The effective number of equally sized country positions was **{c['effective_number']:.1f}**. There were **{len(recent)}** review items in the latest 12 months, including **{len(high)} high-priority items**.\n\n## Largest country positions\n\n|Country|Holdings ($bn)|\n|---|---:|\n"+"".join(f"|{r['country']}|{r['total_pos']/1000:,.1f}|\n" for r in top)+"\n## Recent high-priority items\n\n|Date|Country|Security type|Test|Robust z|Residual %|\n|---|---|---|---|---:|---:|\n"+"".join(f"|{s['date']}|{s['country']}|{s['asset']}|{s['signal']}|{(s['robust_z'] or 0):.1f}|{(s['residual_pct'] or 0):.1f}%|\n" for s in high[:12])+"\n## Notes\n\nTransaction and valuation fields begin in February 2023. Country attribution may reflect custodial centers. Residuals may include revisions, rounding, and adjustments not reported separately.\n"
    (OUT/"research_brief.md").write_text(report,encoding="utf-8")
    bars="".join(f'<tr><td>{html.escape(r["country"])}</td><td>${r["total_pos"]/1000:,.0f}B</td></tr>' for r in top); cases="".join(f'<tr><td>{s["date"]}</td><td>{html.escape(s["country"])}</td><td>{s["asset"]}</td><td>{s["signal"]}</td><td>{s["robust_z"] or 0:.1f}</td></tr>' for s in high[:15]); cluster_counts=defaultdict(int)
    for x in clusters:cluster_counts[x["cluster"]]+=1
    cards="".join(f'<div><small>{html.escape(k)}</small><strong>{v}</strong></div>' for k,v in cluster_counts.items())
    page=f'''<!doctype html><meta charset="utf-8"><title>TIC Holdings Monitor</title><style>body{{margin:0;background:#f3f6f8;font:15px Segoe UI;color:#17212b}}header{{background:#112f46;color:white;padding:30px 6%}}main{{max-width:1150px;margin:auto}}section{{background:white;margin:18px;padding:20px;border-radius:9px;box-shadow:0 2px 8px #0001}}.kpi{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;background:none;box-shadow:none}}.kpi div,.clusters div{{background:white;padding:18px;border-radius:8px}}strong{{display:block;font-size:29px}}.two{{display:grid;grid-template-columns:1fr 1.5fr;gap:0}}table{{width:100%;border-collapse:collapse}}td,th{{padding:9px;border-bottom:1px solid #ddd;text-align:left}}.clusters{{display:flex;gap:10px;flex-wrap:wrap;background:#eef3f6;padding:12px}}@media(max-width:800px){{.kpi,.two{{grid-template-columns:1fr}}}}</style><header><h1>TIC Foreign Holdings Monitor</h1><p>Form SLT, Table 1 • {latest}</p></header><main><section class="kpi"><div>Total holdings<strong>${t['total_pos']/1e6:,.2f}T</strong></div><div>Top-five share<strong>{c['top5_share']:.1%}</strong></div><div>12-month review items<strong>{len(recent)}</strong></div><div>High priority<strong>{len(high)}</strong></div></section><div class="two"><section><h2>Largest country positions</h2><table>{bars}</table></section><section><h2>Recent high-priority items</h2><table><tr><th>Date</th><th>Country</th><th>Security type</th><th>Test</th><th>z</th></tr>{cases}</table></section></div><section><h2>Portfolio groups</h2><div class="clusters">{cards}</div><p>Countries with at least $10 billion, grouped by security-type shares.</p></section><section><small>Transaction and valuation fields begin in February 2023. See METHODOLOGY.md for definitions and limitations.</small></section></main>''';(OUT/"dashboard.html").write_text(page,encoding="utf-8")
    print(f"{len(rows):,} rows | {len(signals):,} review items | {len(clusters)} country groups | latest {latest}")
def main():build(parse())
if __name__=="__main__":main()
