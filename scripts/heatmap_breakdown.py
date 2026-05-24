"""Detailed breakdown of monthly winners for the heatmap analysis.

Re-produces the numbers cited in `docs/QLD_STRATEGY_REPORT.md` §7.A.
"""
import numpy as np
import pandas as pd
import yfinance as yf
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TQQQ_CACHE = DATA / "tqqq_simulated.csv"

qld_df  = pd.read_csv(DATA / "qld_simulated.csv", index_col=0, parse_dates=True)
tqqq_df = pd.read_csv(TQQQ_CACHE,                 index_col=0, parse_dates=True)
tqqq_live = yf.download("TQQQ", start="2010-02-11", auto_adjust=True,
                        progress=False)["Close"].squeeze().dropna()

qqq = qld_df["QQQ"].dropna()
qld_s  = qld_df["QLD_actual"].combine_first(qld_df["QLD_simulated"]).dropna()
tqqq_s = tqqq_live.combine_first(tqqq_df["TQQQ_simulated"]).dropna()

idx = qqq.index
prices = pd.DataFrame({"QQQ": qqq, "QLD": qld_s.reindex(idx), "TQQQ": tqqq_s.reindex(idx)})

qld_sim_flag  = qld_df["QLD_actual"].reindex(idx).isna()
tqqq_sim_flag = tqqq_live.reindex(idx).isna()

def monthly(price):
    g = price.groupby([price.index.year, price.index.month])
    r = g.last() / g.first() - 1.0
    r.index = pd.MultiIndex.from_tuples(r.index, names=["year", "month"])
    return r

def monthly_any_sim(flag):
    g = flag.groupby([flag.index.year, flag.index.month]).any()
    g.index = pd.MultiIndex.from_tuples(g.index, names=["year", "month"])
    return g

m_qqq  = monthly(prices["QQQ"])
m_qld  = monthly(prices["QLD"])
m_tqqq = monthly(prices["TQQQ"])

s_qld  = monthly_any_sim(qld_sim_flag).reindex(m_qld.index, fill_value=False)
s_tqqq = monthly_any_sim(tqqq_sim_flag).reindex(m_tqqq.index, fill_value=False)

rows = []
for key in m_qqq.index.union(m_qld.index).union(m_tqqq.index):
    yr, mo = key
    rets = {"QQQ": m_qqq.get(key, np.nan),
            "QLD": m_qld.get(key, np.nan),
            "TQQQ": m_tqqq.get(key, np.nan)}
    if all(np.isnan(v) for v in rets.values()):
        continue
    winner = max(rets, key=lambda p: -np.inf if np.isnan(rets[p]) else rets[p])
    sim_q = bool(s_qld.get(key, False))
    sim_t = bool(s_tqqq.get(key, False))
    rows.append({
        "year": yr, "month": mo,
        "QQQ": rets["QQQ"], "QLD": rets["QLD"], "TQQQ": rets["TQQQ"],
        "winner": winner,
        "qld_uses_sim": sim_q,
        "tqqq_uses_sim": sim_t,
        "month_sign": "positive" if rets["QQQ"] > 0 else "negative",
    })

df = pd.DataFrame(rows)
print(f"Total months: {len(df)}\n")

print("── Wins by product ────────────────────────────────")
counts = df["winner"].value_counts()
for p in ["QQQ", "QLD", "TQQQ"]:
    n = int(counts.get(p, 0))
    print(f"  {p:5s}: {n:3d} months  ({n/len(df)*100:5.1f}%)")

print("\n── Wins by month-sign × product ───────────────────")
ct = pd.crosstab(df["month_sign"], df["winner"])
print(ct.to_string())

print("\n── Wins by data-source slice × product ────────────")
def slice_name(r):
    yr, mo = r["year"], r["month"]
    d = pd.Timestamp(year=yr, month=mo, day=15)
    if d < pd.Timestamp("2006-06-19"):
        return "1999–2006-Jun  (QLD sim, TQQQ sim)"
    if d < pd.Timestamp("2010-02-11"):
        return "2006-Jun–2010-Feb (QLD real, TQQQ sim)"
    return "2010-Feb–today (QLD real, TQQQ real)"
df["slice"] = df.apply(slice_name, axis=1)
ct2 = pd.crosstab(df["slice"], df["winner"])
print(ct2.to_string())

print("\n── The (rare) QLD-winning months in detail ────────")
qld_wins = df[df["winner"] == "QLD"].copy()
for _, r in qld_wins.iterrows():
    tag = []
    if r["qld_uses_sim"]:  tag.append("QLDsim")
    if r["tqqq_uses_sim"]: tag.append("TQQQsim")
    tag = "  [" + ",".join(tag) + "]" if tag else ""
    print(f"  {int(r['year'])}-{int(r['month']):02d}:  "
          f"QQQ {r['QQQ']*100:+.2f}%  QLD {r['QLD']*100:+.2f}%  TQQQ {r['TQQQ']*100:+.2f}%{tag}")
