"""
Three-way return comparison: QQQ vs QLD vs TQQQ.

Generates two plots:
 1) yearly_returns_bar.png  — grouped bar chart of calendar-year returns 1999-2026,
    with bars hatched where the product is being simulated.
 2) monthly_best_heatmap.png — month-by-year grid; each cell coloured by the
    product that won that month, with the winning return printed inside.
    Cells whose winner is based on simulated data get a dashed border.

Reuses cached price series:
 - ../data/qld_simulated.csv  (Date, QQQ, QLD_actual, QLD_simulated)
 - ../data/tqqq_simulated.csv (Date, QQQ, TQQQ_actual, TQQQ_simulated, TQQQ_volume)
   — only the pre-2010 TQQQ_simulated column is consumed; real TQQQ for 2010+
   is re-fetched live from yfinance below.
"""

import matplotlib
matplotlib.use("Agg")
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
from matplotlib.lines import Line2D
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIG = ROOT / "figures"
TQQQ_CACHE = DATA / "tqqq_simulated.csv"
FIG.mkdir(parents=True, exist_ok=True)

QQQ_COLOR  = "#1f77b4"
QLD_COLOR  = "#ff7f0e"
TQQQ_COLOR = "#2ca02c"

QLD_INCEPTION  = pd.Timestamp("2006-06-19")
TQQQ_INCEPTION = pd.Timestamp("2010-02-11")

# ── 1. Load + stitch series ────────────────────────────────────────────────

qld_df = pd.read_csv(DATA / "qld_simulated.csv", index_col=0, parse_dates=True)
tqqq_df = pd.read_csv(TQQQ_CACHE, index_col=0, parse_dates=True)

# Pull fresh real TQQQ from yfinance (cached CSV may be stale)
print("Downloading latest TQQQ for the real-history portion...")
tqqq_live = yf.download("TQQQ", start="2010-02-11", auto_adjust=True)["Close"].squeeze().dropna()

qqq = qld_df["QQQ"].dropna()
qld_stitched  = qld_df["QLD_actual"].combine_first(qld_df["QLD_simulated"]).dropna()
# Real TQQQ wherever available (incl. recent yfinance dates beyond cached CSV);
# fall back to cached simulated TQQQ only for pre-inception 1999-2010 window.
tqqq_stitched = tqqq_live.combine_first(tqqq_df["TQQQ_simulated"]).dropna()

# Align all three on QQQ's calendar
idx = qqq.index
qld_s = qld_stitched.reindex(idx)
tqqq_s = tqqq_stitched.reindex(idx)

# Per-day is_simulated flags
qld_is_sim = qld_df["QLD_actual"].reindex(idx).isna()
tqqq_is_sim = tqqq_live.reindex(idx).isna()
qqq_is_sim = pd.Series(False, index=idx)

prices = pd.DataFrame({"QQQ": qqq, "QLD": qld_s, "TQQQ": tqqq_s})
sim_flags = pd.DataFrame({"QQQ": qqq_is_sim, "QLD": qld_is_sim, "TQQQ": tqqq_is_sim})

# ── 2. Yearly returns ─────────────────────────────────────────────────────

def yearly_returns(price: pd.Series) -> pd.Series:
    grouped = price.groupby(price.index.year)
    return grouped.last() / grouped.first() - 1.0

yr_qqq  = yearly_returns(prices["QQQ"])
yr_qld  = yearly_returns(prices["QLD"])
yr_tqqq = yearly_returns(prices["TQQQ"])

# Is the year-bar based on simulated data? (any simulated day in that year)
def yearly_is_sim(flag_series: pd.Series) -> pd.Series:
    return flag_series.groupby(flag_series.index.year).any()

sim_qqq  = yearly_is_sim(sim_flags["QQQ"])
sim_qld  = yearly_is_sim(sim_flags["QLD"])
sim_tqqq = yearly_is_sim(sim_flags["TQQQ"])

years = sorted(set(yr_qqq.index) | set(yr_qld.index) | set(yr_tqqq.index))

fig, ax = plt.subplots(figsize=(20, 9))
x = np.arange(len(years))
w = 0.28

def draw_bars(ax, x_pos, values_series, sim_series, color, label):
    for i, yr in enumerate(years):
        v = values_series.get(yr, np.nan)
        if np.isnan(v):
            continue
        is_sim = bool(sim_series.get(yr, False))
        ax.bar(x_pos[i], v, w,
               color=color,
               alpha=0.55 if is_sim else 1.0,
               hatch="//" if is_sim else None,
               edgecolor="black" if is_sim else color,
               linewidth=0.6,
               label=label if i == 0 else None)

draw_bars(ax, x - w, yr_qqq,  sim_qqq,  QQQ_COLOR,  "QQQ")
draw_bars(ax, x,     yr_qld,  sim_qld,  QLD_COLOR,  "QLD")
draw_bars(ax, x + w, yr_tqqq, sim_tqqq, TQQQ_COLOR, "TQQQ")

ax.axhline(0, color="black", lw=0.7)

# Inception vertical lines
for incept, name in [(QLD_INCEPTION, "QLD inception\n2006-06-19"),
                     (TQQQ_INCEPTION, "TQQQ inception\n2010-02-11")]:
    yr = incept.year
    if yr in years:
        xi = years.index(yr)
        # Position the vline at the right edge of that year group
        ax.axvline(xi + 1.5*w, color="gray", ls=":", lw=1.0, alpha=0.7)
        ax.text(xi + 1.5*w + 0.05, ax.get_ylim()[1]*0.92, name,
                fontsize=7.5, color="gray", va="top")

ax.set_xticks(x)
ax.set_xticklabels([str(y) for y in years], rotation=45, ha="right", fontsize=9)
ax.set_ylabel("Calendar-year total return")
ax.set_title("Calendar-year returns: QQQ (1×) vs QLD (2×) vs TQQQ (3×), 1999–2026\n"
             "Hatched / faded bars = simulated;  solid bars = real ETF data",
             fontsize=12, fontweight="bold")
ax.grid(True, axis="y", alpha=0.3)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v*100:.0f}%"))

legend_handles = [
    Patch(facecolor=QQQ_COLOR,  label="QQQ  (1× — always real)"),
    Patch(facecolor=QLD_COLOR,  label="QLD  (2×)"),
    Patch(facecolor=TQQQ_COLOR, label="TQQQ (3×)"),
    Patch(facecolor="white", edgecolor="black", hatch="//", alpha=0.55,
          label="Simulated (hatched/faded)"),
    Patch(facecolor="white", edgecolor="black",
          label="Real ETF history (solid)"),
]
ax.legend(handles=legend_handles, loc="upper left", fontsize=9, ncol=2)

plt.tight_layout()
out_yearly = str(FIG / "yearly_returns_bar.png")
plt.savefig(out_yearly, dpi=150, bbox_inches="tight")
print(f"Saved → {out_yearly}")

# ── 3. Monthly best-performer heatmap ──────────────────────────────────────

def monthly_returns(price: pd.Series) -> pd.DataFrame:
    """Return a (year × month) DataFrame of total returns."""
    grouper = [price.index.year, price.index.month]
    grp = price.groupby(grouper)
    mret = grp.last() / grp.first() - 1.0
    mret.index = pd.MultiIndex.from_tuples(mret.index, names=["year", "month"])
    return mret.unstack("month")

def monthly_any_sim(flag: pd.Series) -> pd.DataFrame:
    grouper = [flag.index.year, flag.index.month]
    g = flag.groupby(grouper).any()
    g.index = pd.MultiIndex.from_tuples(g.index, names=["year", "month"])
    return g.unstack("month")

m_qqq  = monthly_returns(prices["QQQ"])
m_qld  = monthly_returns(prices["QLD"])
m_tqqq = monthly_returns(prices["TQQQ"])

s_qqq  = monthly_any_sim(sim_flags["QQQ"])
s_qld  = monthly_any_sim(sim_flags["QLD"])
s_tqqq = monthly_any_sim(sim_flags["TQQQ"])

all_years = sorted(set(m_qqq.index) | set(m_qld.index) | set(m_tqqq.index))
for d in (m_qqq, m_qld, m_tqqq, s_qqq, s_qld, s_tqqq):
    d_ = d.reindex(index=all_years, columns=range(1, 13))

m_qqq  = m_qqq.reindex(index=all_years, columns=range(1, 13))
m_qld  = m_qld.reindex(index=all_years, columns=range(1, 13))
m_tqqq = m_tqqq.reindex(index=all_years, columns=range(1, 13))
s_qqq  = s_qqq.reindex(index=all_years, columns=range(1, 13)).fillna(False)
s_qld  = s_qld.reindex(index=all_years, columns=range(1, 13)).fillna(False)
s_tqqq = s_tqqq.reindex(index=all_years, columns=range(1, 13)).fillna(False)

product_colors = {"QQQ": QQQ_COLOR, "QLD": QLD_COLOR, "TQQQ": TQQQ_COLOR}
product_returns = {"QQQ": m_qqq, "QLD": m_qld, "TQQQ": m_tqqq}
product_sim     = {"QQQ": s_qqq, "QLD": s_qld, "TQQQ": s_tqqq}

n_years = len(all_years)
fig, ax = plt.subplots(figsize=(15, max(8, n_years * 0.42)))

# precompute max abs return for color intensity scaling
all_vals = np.concatenate([
    m_qqq.values.flatten(), m_qld.values.flatten(), m_tqqq.values.flatten()
])
finite = all_vals[np.isfinite(all_vals)]
vmax = np.nanpercentile(np.abs(finite), 95)  # robust max

month_labels = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

for i, yr in enumerate(all_years):
    for j, m in enumerate(range(1, 13)):
        rets = {p: product_returns[p].loc[yr, m] for p in product_returns}
        if all(np.isnan(v) for v in rets.values()):
            ax.add_patch(Rectangle((j, n_years - 1 - i), 1, 1,
                                    facecolor="#eeeeee", edgecolor="white"))
            continue

        winner = max(rets.keys(), key=lambda p: -np.inf if np.isnan(rets[p]) else rets[p])
        win_val = rets[winner]
        win_color = product_colors[winner]
        is_sim = bool(product_sim[winner].loc[yr, m])

        # Color intensity: alpha scales with |return| / vmax
        alpha = min(1.0, max(0.20, abs(win_val) / vmax))
        # For negative wins (all three negative), keep distinct
        if win_val < 0:
            alpha = min(1.0, max(0.18, abs(win_val) / vmax * 0.85))

        ax.add_patch(Rectangle(
            (j, n_years - 1 - i), 1, 1,
            facecolor=win_color,
            alpha=alpha,
            edgecolor="black",
            linestyle=(0, (3, 2)) if is_sim else "solid",
            linewidth=1.0 if is_sim else 0.6,
        ))
        text_color = "white" if alpha > 0.55 else "black"
        ax.text(j + 0.5, n_years - 1 - i + 0.5,
                f"{win_val*100:+.1f}%",
                ha="center", va="center",
                fontsize=7.5, color=text_color, fontweight="bold")

ax.set_xlim(0, 12)
ax.set_ylim(0, n_years)
ax.set_xticks(np.arange(12) + 0.5)
ax.set_xticklabels(month_labels)
ax.set_yticks(np.arange(n_years) + 0.5)
ax.set_yticklabels(all_years[::-1])
ax.set_aspect("equal")
ax.tick_params(length=0)
for spine in ax.spines.values():
    spine.set_visible(False)

ax.set_title("Monthly best performer: QQQ vs QLD vs TQQQ  (1999–2026)\n"
             "Cell colour = winning product; value = winner's monthly return.  "
             "Dashed border = winner's month uses simulated data.",
             fontsize=12, fontweight="bold")

legend_handles = [
    Patch(facecolor=QQQ_COLOR,  label="QQQ wins"),
    Patch(facecolor=QLD_COLOR,  label="QLD wins"),
    Patch(facecolor=TQQQ_COLOR, label="TQQQ wins"),
    Line2D([0], [0], color="black", lw=1.2, label="Real data"),
    Line2D([0], [0], color="black", lw=1.2, ls=(0, (3, 2)), label="Simulated data"),
]
ax.legend(handles=legend_handles, loc="upper left",
          bbox_to_anchor=(1.01, 1.0), fontsize=9, frameon=False)

plt.tight_layout()
out_heatmap = str(FIG / "monthly_best_heatmap.png")
plt.savefig(out_heatmap, dpi=150, bbox_inches="tight")
print(f"Saved → {out_heatmap}")

# ── 4. Summary stats ───────────────────────────────────────────────────────

print("\nWinning months by product (1999-2026):")
total_cells = 0
wins = {"QQQ": 0, "QLD": 0, "TQQQ": 0}
for yr in all_years:
    for m in range(1, 13):
        rets = {"QQQ": m_qqq.loc[yr, m], "QLD": m_qld.loc[yr, m], "TQQQ": m_tqqq.loc[yr, m]}
        if all(np.isnan(v) for v in rets.values()):
            continue
        winner = max(rets, key=lambda p: -np.inf if np.isnan(rets[p]) else rets[p])
        wins[winner] += 1
        total_cells += 1
for p, c in wins.items():
    print(f"  {p:5s}: {c:3d} / {total_cells}  ({c/total_cells*100:.1f}%)")
