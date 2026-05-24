"""
Long-hold strategies on QQQ / QLD / TQQQ.

Two strategies:
  - Buy & Hold:   invest $10,000 on day 0, hold to end.
  - Monthly DCA:  $1,000 on the first trading day of each calendar month.
    Lump-sum baseline (same total invested on day 0) is overlaid for context.

Two evaluation windows:
  - Period A — Simulation era: 1999-03-10 → today  (stitched sim+real)
  - Period B — Real era:        2010-02-11 → today (100% real ETF data)

For each (strategy × product × period) we report:
  Final NAV, total return, CAGR, annualised volatility, Sharpe (rf=0),
  Max drawdown, Max DD duration (days), dot-com peak/trough/recovery
  (Period A only), total contributed (DCA), IRR (DCA only).

Outputs:
  bah_nav_periodA.png, bah_nav_periodB.png
  dca_nav_periodA.png, dca_nav_periodB.png
  bah_metrics_periodA.png, bah_metrics_periodB.png
  dca_metrics_periodA.png, dca_metrics_periodB.png
"""

import matplotlib
matplotlib.use("Agg")
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
from scipy.optimize import brentq

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIG = ROOT / "figures"
TQQQ_CACHE = DATA / "tqqq_simulated.csv"
DATA.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

QQQ_COLOR  = "#1f77b4"
QLD_COLOR  = "#ff7f0e"
TQQQ_COLOR = "#2ca02c"
COLORS = {"QQQ": QQQ_COLOR, "QLD": QLD_COLOR, "TQQQ": TQQQ_COLOR}

QLD_INCEPTION  = pd.Timestamp("2006-06-19")
TQQQ_INCEPTION = pd.Timestamp("2010-02-11")
PERIOD_A_START = pd.Timestamp("1999-03-10")
PERIOD_B_START = pd.Timestamp("2010-02-11")

# ── 1. Load price data (Period A = stitched, Period B = real) ──────────────

qld_df = pd.read_csv(DATA / "qld_simulated.csv", index_col=0, parse_dates=True)
tqqq_df = pd.read_csv(TQQQ_CACHE, index_col=0, parse_dates=True)

# Pull fresh real TQQQ from yfinance (cached CSV may be stale).
print("Downloading latest TQQQ for the real-history portion...")
tqqq_live = yf.download("TQQQ", start="2010-02-11", auto_adjust=True)["Close"].squeeze().dropna()

qqq = qld_df["QQQ"].dropna()
qld_real = qld_df["QLD_actual"].dropna()
qld_stitch = qld_df["QLD_actual"].combine_first(qld_df["QLD_simulated"]).dropna()
tqqq_real = tqqq_live
# Real TQQQ for 2010+, cached simulated TQQQ only for pre-inception 1999-2010.
tqqq_stitch = tqqq_live.combine_first(tqqq_df["TQQQ_simulated"]).dropna()

prices_A = pd.DataFrame({"QQQ": qqq, "QLD": qld_stitch, "TQQQ": tqqq_stitch}).dropna()
prices_A = prices_A.loc[PERIOD_A_START:]

prices_B = pd.DataFrame({"QQQ": qqq, "QLD": qld_real, "TQQQ": tqqq_real}).dropna()
prices_B = prices_B.loc[PERIOD_B_START:]

# ── 2. Strategy engines ────────────────────────────────────────────────────

def buy_and_hold(price: pd.Series, initial: float = 10_000.0) -> pd.Series:
    return initial * price / price.iloc[0]

def monthly_dca(price: pd.Series, contribution: float = 1_000.0):
    """Returns (portfolio_value_series, contributions_series_with_dates)."""
    # First trading day of each month
    monthly_first = price.groupby([price.index.year, price.index.month]).head(1)
    contrib_dates = monthly_first.index
    units = 0.0
    total_contrib = 0.0
    pv = pd.Series(0.0, index=price.index)
    contribs = pd.Series(0.0, index=contrib_dates)
    next_contrib_idx = 0
    contrib_dates_set = set(contrib_dates)
    for dt in price.index:
        if dt in contrib_dates_set:
            units += contribution / price.loc[dt]
            total_contrib += contribution
            contribs.loc[dt] = contribution
        pv.loc[dt] = units * price.loc[dt]
    return pv, contribs

def lumpsum_baseline(price: pd.Series, total_invested: float) -> pd.Series:
    return total_invested * price / price.iloc[0]

# ── 3. Metrics ─────────────────────────────────────────────────────────────

def perf_metrics(nav: pd.Series, label: str) -> dict:
    nav = nav.dropna()
    nav = nav[nav > 0]
    r = nav.pct_change().dropna()
    ny = len(r) / 252.0
    tot = nav.iloc[-1] / nav.iloc[0] - 1
    cagr = (1 + tot) ** (1 / ny) - 1 if ny > 0 else np.nan
    vol = r.std() * np.sqrt(252)
    sharpe = (r.mean() / r.std() * np.sqrt(252)) if r.std() > 0 else np.nan
    rmax = nav.cummax()
    dd = (nav - rmax) / rmax
    mdd = dd.min()
    # Drawdown duration: longest stretch underwater (days)
    under = (nav < rmax).astype(int)
    streaks = []
    cur = 0
    for v in under.values:
        if v == 1:
            cur += 1
        else:
            if cur > 0:
                streaks.append(cur)
            cur = 0
    if cur > 0:
        streaks.append(cur)
    max_dd_days = max(streaks) if streaks else 0
    return {
        "Strategy": label,
        "Final NAV ($)": nav.iloc[-1],
        "Total return (%)": tot * 100,
        "CAGR (%)": cagr * 100,
        "Annual vol (%)": vol * 100,
        "Sharpe": sharpe,
        "Max DD (%)": mdd * 100,
        "Max DD duration (days)": max_dd_days,
    }

def dot_com_stats(nav: pd.Series) -> dict:
    """Peak before 2003, trough after, and recovery date."""
    nav = nav.dropna()
    pre = nav.loc[:"2002-12-31"]
    if pre.empty:
        return {"Dot-com peak": "n/a", "Trough": "n/a", "DD (%)": np.nan, "Recovery": "n/a"}
    peak_date = pre.idxmax()
    peak_val = pre.loc[peak_date]
    after = nav.loc[peak_date:]
    trough_date = after.loc[:"2003-12-31"].idxmin()
    trough_val = nav.loc[trough_date]
    dd_pct = (trough_val / peak_val - 1) * 100
    recovery_mask = (nav.loc[trough_date:] >= peak_val)
    recovery_date = recovery_mask.idxmax() if recovery_mask.any() else None
    return {
        "Dot-com peak": peak_date.strftime("%Y-%m-%d"),
        "Trough": trough_date.strftime("%Y-%m-%d"),
        "DD (%)": dd_pct,
        "Recovery": recovery_date.strftime("%Y-%m-%d") if recovery_date is not None else "not yet",
    }

def irr_monthly(contribs: pd.Series, final_value: float, final_date) -> float:
    """Annualised IRR given monthly contributions and a final portfolio value.
       Cash-flow convention: contributions are outflows (negative), terminal value inflow."""
    dates = list(contribs.index) + [final_date]
    cashflows = list(-contribs.values) + [final_value]
    t0 = dates[0]
    # Time in years
    t_years = np.array([(d - t0).days / 365.25 for d in dates])
    def npv(rate):
        return np.sum(np.array(cashflows) / (1 + rate) ** t_years)
    try:
        return brentq(npv, -0.99, 5.0) * 100
    except Exception:
        return np.nan

# ── 4. Plot helpers ────────────────────────────────────────────────────────

def plot_nav(navs: dict, title: str, out_path: str,
             period_start: pd.Timestamp, period_end: pd.Timestamp,
             baselines: dict | None = None,
             inception_lines: list | None = None):
    fig, ax = plt.subplots(figsize=(14, 7))
    for label, nav in navs.items():
        ax.semilogy(nav.index, nav.values, color=COLORS[label],
                    lw=1.5, label=f"{label}")
    if baselines:
        for label, baseline in baselines.items():
            ax.semilogy(baseline.index, baseline.values, color=COLORS[label],
                        lw=1.0, ls="--", alpha=0.6,
                        label=f"{label} lump-sum")
    if inception_lines:
        for dt, name in inception_lines:
            if period_start <= dt <= period_end:
                ax.axvline(dt, color="gray", ls=":", lw=0.9, alpha=0.8)
                ax.text(dt, ax.get_ylim()[1]*0.7, " " + name,
                        fontsize=8, color="gray", rotation=90, va="top")
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_ylabel("Portfolio value (USD, log scale)")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="upper left", fontsize=9, ncol=2)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved → {out_path}")

def plot_metrics_table(rows: list[dict], title: str, out_path: str,
                       columns: list[str]):
    n_rows = len(rows)
    n_cols = len(columns)
    fig, ax = plt.subplots(figsize=(max(11, n_cols * 1.5), 1.0 + 0.5 * n_rows))
    ax.axis("off")
    cell_text = []
    row_colors = []
    for r in rows:
        cells = []
        for c in columns:
            v = r.get(c, "")
            if isinstance(v, float):
                if "DD" in c or "(%)" in c or "vol" in c.lower() or "return" in c.lower() or "CAGR" in c.lower():
                    cells.append(f"{v:+.2f}%" if "DD" in c or "return" in c.lower() else f"{v:.2f}%")
                elif "Sharpe" in c:
                    cells.append(f"{v:.2f}")
                elif "NAV" in c or "$" in c or "Contributed" in c or "IRR" in c:
                    cells.append(f"${v:,.0f}" if "$" in c or "NAV" in c or "Contributed" in c else f"{v:.2f}%")
                else:
                    cells.append(f"{v:.2f}")
            else:
                cells.append(str(v))
        cell_text.append(cells)
        # color rows by product
        prod = r.get("Strategy", "").split()[0]
        rgba = matplotlib.colors.to_rgba(COLORS.get(prod, "#cccccc"), alpha=0.18)
        row_colors.append(rgba)

    tbl = ax.table(
        cellText=cell_text,
        colLabels=columns,
        cellLoc="center",
        loc="center",
        cellColours=[[rc] * n_cols for rc in row_colors],
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1.0, 1.5)
    ax.set_title(title, fontsize=12, fontweight="bold", pad=14)
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved → {out_path}")

# ── 5. Run BAH and DCA on both periods ─────────────────────────────────────

INITIAL_BAH = 10_000.0
DCA_AMT = 1_000.0

def run_period(prices: pd.DataFrame, period_label: str, period_letter: str,
               include_dotcom: bool):
    period_start = prices.index[0]
    period_end = prices.index[-1]
    print(f"\n────── Period {period_letter}: {period_label} "
          f"({period_start.date()} → {period_end.date()}) ──────")

    # BAH
    bah_navs = {p: buy_and_hold(prices[p], INITIAL_BAH) for p in prices.columns}

    plot_nav(
        bah_navs,
        title=f"Buy & Hold $10,000 — Period {period_letter}: {period_label}",
        out_path=str(FIG / f"bah_nav_period{period_letter}.png"),
        period_start=period_start, period_end=period_end,
        inception_lines=[(QLD_INCEPTION, "QLD inception"),
                         (TQQQ_INCEPTION, "TQQQ inception")] if period_letter == "A" else None,
    )

    # BAH metrics
    bah_rows = []
    bah_cols = ["Strategy", "Final NAV ($)", "Total return (%)", "CAGR (%)",
                "Annual vol (%)", "Sharpe", "Max DD (%)", "Max DD duration (days)"]
    if include_dotcom:
        bah_cols += ["Dot-com peak", "Trough", "DD (%)", "Recovery"]
    for p in prices.columns:
        m = perf_metrics(bah_navs[p], f"{p} Buy & Hold")
        if include_dotcom:
            m.update(dot_com_stats(bah_navs[p]))
        bah_rows.append(m)
    plot_metrics_table(bah_rows,
                       title=f"Buy & Hold — Performance metrics — Period {period_letter}",
                       out_path=str(FIG / f"bah_metrics_period{period_letter}.png"),
                       columns=bah_cols)
    bah_metrics_export = bah_rows

    # DCA
    dca_navs = {}
    contribs_dict = {}
    for p in prices.columns:
        pv, contribs = monthly_dca(prices[p], DCA_AMT)
        dca_navs[p] = pv
        contribs_dict[p] = contribs

    # Lump-sum baselines: same total contributed, but invested all on day 0
    baselines = {}
    for p in prices.columns:
        total = contribs_dict[p].sum()
        baselines[p] = lumpsum_baseline(prices[p], total)

    plot_nav(
        dca_navs,
        title=f"Monthly DCA $1,000 — Period {period_letter}: {period_label}\n"
              f"(dashed = same total invested as lump-sum on day 0)",
        out_path=str(FIG / f"dca_nav_period{period_letter}.png"),
        period_start=period_start, period_end=period_end,
        baselines=baselines,
        inception_lines=[(QLD_INCEPTION, "QLD inception"),
                         (TQQQ_INCEPTION, "TQQQ inception")] if period_letter == "A" else None,
    )

    # DCA metrics
    dca_rows = []
    dca_cols = ["Strategy", "Final NAV ($)", "Total contributed ($)", "IRR (%/yr)",
                "Total return (%)", "CAGR (%)", "Annual vol (%)", "Sharpe",
                "Max DD (%)", "Max DD duration (days)"]
    for p in prices.columns:
        m = perf_metrics(dca_navs[p], f"{p} Monthly DCA")
        contributed = contribs_dict[p].sum()
        irr = irr_monthly(contribs_dict[p], dca_navs[p].iloc[-1], dca_navs[p].index[-1])
        m["Total contributed ($)"] = contributed
        m["IRR (%/yr)"] = irr
        # For DCA NAV, "Total return" against initial NAV is misleading; we compute
        # money-weighted return via IRR instead. Replace Total return with portfolio/contributed.
        m["Total return (%)"] = (dca_navs[p].iloc[-1] / contributed - 1) * 100  # MOIC - 1
        # CAGR via IRR (consistent)
        m["CAGR (%)"] = irr
        dca_rows.append(m)
    plot_metrics_table(dca_rows,
                       title=f"Monthly DCA $1,000 — Performance metrics — Period {period_letter}\n"
                             f"(Total return shown is portfolio-value / total-contributed − 1; CAGR shown is IRR)",
                       out_path=str(FIG / f"dca_metrics_period{period_letter}.png"),
                       columns=dca_cols)

    # Console summary
    print("\nBAH metrics:")
    for row in bah_rows:
        print(f"  {row['Strategy']:<25}  CAGR {row['CAGR (%)']:6.2f}%  "
              f"Sharpe {row['Sharpe']:.2f}  MaxDD {row['Max DD (%)']:.2f}%")
        if include_dotcom:
            print(f"     dot-com peak {row['Dot-com peak']}, trough {row['Trough']} "
                  f"({row['DD (%)']:+.1f}%), recovered {row['Recovery']}")
    print("\nDCA metrics:")
    for row in dca_rows:
        print(f"  {row['Strategy']:<25}  IRR {row['IRR (%/yr)']:6.2f}%  "
              f"Sharpe {row['Sharpe']:.2f}  MaxDD {row['Max DD (%)']:.2f}%  "
              f"contributed ${row['Total contributed ($)']:,.0f}, final ${row['Final NAV ($)']:,.0f}")

    return {"bah": bah_metrics_export, "dca": dca_rows}

results_A = run_period(prices_A, "Simulation era 1999–today",
                       period_letter="A", include_dotcom=True)
results_B = run_period(prices_B, "Real era 2010–today",
                       period_letter="B", include_dotcom=False)

# Export consolidated CSV for the report
all_rows = []
for label, res in [("A", results_A), ("B", results_B)]:
    for kind in ("bah", "dca"):
        for r in res[kind]:
            row = {"Period": label, "Strategy_kind": kind, **r}
            all_rows.append(row)
out_csv = str(DATA / "strategy_metrics.csv")
pd.DataFrame(all_rows).to_csv(out_csv, index=False)
print(f"\nSaved → {out_csv}")
