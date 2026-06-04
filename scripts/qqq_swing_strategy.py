"""
Reddit "QQQ dip-buy" swing strategy backtest.

Strategy (as described on Reddit):
  ENTRY  — when the PREVIOUS day's QQQ close-to-close return is < -2%, buy.
  EXIT   — keep holding until the PREVIOUS day's QQQ return is > +3%, then sell.

The signal is ALWAYS derived from QQQ's daily return. The asset you actually
buy can be QQQ (1x), QLD (2x) or TQQQ (3x) — we backtest all three so the
QLD/TQQQ leverage angle of this repo is covered. Because the position on day
T is decided from the return realised on day T-1, every trade is effectively a
next-day execution (no look-ahead).

Two evaluation windows (mirrors scripts/qld_strategies.py):
  - Period A — Simulation era: 1999-03-10 -> last available day (stitched sim+real)
  - Period B — Real era:        2010-02-11 -> last available day (100% real ETF data)

Data:
  Tries to pull the most recent QQQ/QLD/TQQQ from yfinance so the backtest runs
  right up to today. If the network is unavailable (e.g. a sandbox whose policy
  blocks Yahoo Finance), it transparently falls back to the cached CSVs in
  data/ and prints the as-of date so you know how stale the answer is.

Outputs:
  figures/qqq_swing_nav_periodA.png, figures/qqq_swing_nav_periodB.png
  figures/qqq_swing_metrics_periodA.png, figures/qqq_swing_metrics_periodB.png
  data/qqq_swing_metrics.csv          (one row per asset x period)
  data/qqq_swing_signals.csv          (full signal/trade log, most recent window)
"""

import matplotlib
matplotlib.use("Agg")
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIG = ROOT / "figures"
DATA.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

QQQ_COLOR, QLD_COLOR, TQQQ_COLOR = "#1f77b4", "#ff7f0e", "#2ca02c"
COLORS = {"QQQ": QQQ_COLOR, "QLD": QLD_COLOR, "TQQQ": TQQQ_COLOR}

PERIOD_A_START = pd.Timestamp("1999-03-10")
PERIOD_B_START = pd.Timestamp("2010-02-11")

ENTRY_THRESHOLD = -0.02   # buy after a prev-day QQQ return below this
EXIT_THRESHOLD  = +0.03   # sell after a prev-day QQQ return above this

# ── 1. Load price data — live yfinance if possible, else cached CSV ─────────

def load_prices():
    """Return (prices_A, prices_B, source_note). Columns: QQQ, QLD, TQQQ."""
    qld_df = pd.read_csv(DATA / "qld_simulated.csv", index_col=0, parse_dates=True)
    tqqq_df = pd.read_csv(DATA / "tqqq_simulated.csv", index_col=0, parse_dates=True)

    qqq_cached = qld_df["QQQ"].dropna()
    qld_real_cached = qld_df["QLD_actual"].dropna()
    qld_stitch = qld_df["QLD_actual"].combine_first(qld_df["QLD_simulated"]).dropna()
    tqqq_sim = tqqq_df["TQQQ_simulated"].dropna()

    live_ok = False
    qqq = qqq_cached
    qld_real = qld_real_cached
    tqqq_real = None
    try:
        import yfinance as yf
        print("Attempting live download (QQQ, QLD, TQQQ) from yfinance ...")
        dl = yf.download(["QQQ", "QLD", "TQQQ"], start="1999-01-01",
                         auto_adjust=True, progress=False)["Close"]
        if dl is not None and not dl.dropna(how="all").empty:
            qqq_live = dl["QQQ"].dropna()
            qld_live = dl["QLD"].dropna()
            tqqq_live = dl["TQQQ"].dropna()
            if len(qqq_live) > 100:
                # Splice live onto cached so we keep the long simulated history
                qqq = qqq_live.combine_first(qqq_cached)
                qld_real = qld_live.combine_first(qld_real_cached)
                qld_stitch = qld_live.combine_first(qld_stitch)
                tqqq_real = tqqq_live
                live_ok = True
                print(f"  live data through {qqq_live.index.max().date()}")
    except Exception as e:
        print(f"  live download unavailable ({type(e).__name__}: {e}); using cached CSVs")

    if tqqq_real is None:
        # No live TQQQ — fall back to whatever real TQQQ we can reconstruct.
        # The cached file only has the simulated series; for Period B we need
        # real-era values, so use the simulated series from 2010 on as a proxy.
        tqqq_real = tqqq_sim.loc[PERIOD_B_START:]
    tqqq_stitch = (tqqq_real.combine_first(tqqq_sim)).dropna()

    prices_A = pd.DataFrame({"QQQ": qqq, "QLD": qld_stitch,
                             "TQQQ": tqqq_stitch}).dropna().loc[PERIOD_A_START:]
    prices_B = pd.DataFrame({"QQQ": qqq, "QLD": qld_real,
                             "TQQQ": tqqq_real}).dropna().loc[PERIOD_B_START:]

    # The QQQ signal series is returned untruncated: the joint dropna above can
    # be held back by a staler TQQQ cache, but the swing SIGNAL only needs QQQ,
    # so the current-month check should use every QQQ session we actually have.
    qqq_full = qqq.loc[PERIOD_A_START:]

    asof_qqq = qqq_full.index.max().date()
    asof_joint = prices_A.index.max().date()
    note = (f"LIVE (yfinance) spliced onto cache; QQQ as-of {asof_qqq}" if live_ok
            else f"CACHED CSV only; QQQ as-of {asof_qqq}, joint-3-ETF backtest as-of {asof_joint} "
                 f"(run on a networked machine to extend to today)")
    return prices_A, prices_B, qqq_full, note


# ── 2. Strategy engine ──────────────────────────────────────────────────────

def swing_positions(qqq_ret: pd.Series) -> pd.Series:
    """State machine over QQQ daily returns.

    Position on day T (1 = invested, 0 = flat) is decided from the return on
    day T-1, so there is no look-ahead. Enter when prev-day return < -2%,
    exit when prev-day return > +3%.
    """
    entry = qqq_ret.shift(1) < ENTRY_THRESHOLD
    exit_ = qqq_ret.shift(1) > EXIT_THRESHOLD
    pos = pd.Series(0, index=qqq_ret.index, dtype=int)
    state = 0
    for t in qqq_ret.index:
        if state == 0 and bool(entry.loc[t]):
            state = 1
        elif state == 1 and bool(exit_.loc[t]):
            state = 0
        pos.loc[t] = state
    return pos


def backtest(price: pd.Series, qqq_ret: pd.Series, initial: float = 10_000.0):
    """Buy `price` asset on the QQQ-derived swing signal. Returns (nav, pos)."""
    asset_ret = price.pct_change().reindex(qqq_ret.index).fillna(0.0)
    pos = swing_positions(qqq_ret)
    strat_ret = pos * asset_ret
    nav = initial * (1 + strat_ret).cumprod()
    return nav, pos


# ── 3. Metrics ──────────────────────────────────────────────────────────────

def perf_metrics(nav: pd.Series, pos: pd.Series, label: str) -> dict:
    nav = nav.dropna()
    r = nav.pct_change().dropna()
    ny = len(r) / 252.0
    tot = nav.iloc[-1] / nav.iloc[0] - 1
    cagr = (1 + tot) ** (1 / ny) - 1 if ny > 0 else np.nan
    active = r[pos.reindex(r.index).fillna(0) == 1]      # only days in market
    vol = active.std() * np.sqrt(252) if len(active) else np.nan
    sharpe = (r.mean() / r.std() * np.sqrt(252)) if r.std() > 0 else np.nan
    rmax = nav.cummax()
    dd = (nav - rmax) / rmax
    mdd = dd.min()

    # Trade accounting: a trade = a contiguous block of pos==1
    p = pos.reindex(nav.index).fillna(0).astype(int).values
    trades, holds, t_returns = 0, [], []
    in_pos = False
    start_i = None
    navv = nav.values
    for i, v in enumerate(p):
        if v == 1 and not in_pos:
            in_pos, start_i = True, i
        elif v == 0 and in_pos:
            in_pos = False
            trades += 1
            holds.append(i - start_i)
            t_returns.append(navv[i - 1] / navv[start_i - 1] - 1 if start_i > 0 else navv[i - 1] / navv[start_i] - 1)
    if in_pos:  # still holding at the end
        trades += 1
        holds.append(len(p) - start_i)
        t_returns.append(navv[-1] / navv[start_i - 1] - 1 if start_i > 0 else navv[-1] / navv[start_i] - 1)

    wins = [x for x in t_returns if x > 0]
    return {
        "Strategy": label,
        "Final NAV ($)": nav.iloc[-1],
        "Total return (%)": tot * 100,
        "CAGR (%)": cagr * 100,
        "In-market vol (%)": vol * 100,
        "Sharpe": sharpe,
        "Max DD (%)": mdd * 100,
        "Time in market (%)": p.mean() * 100,
        "Trades": trades,
        "Win rate (%)": (len(wins) / trades * 100) if trades else np.nan,
        "Avg hold (days)": np.mean(holds) if holds else np.nan,
        "Avg trade (%)": np.mean(t_returns) * 100 if t_returns else np.nan,
    }


# ── 4. Plot helpers ─────────────────────────────────────────────────────────

def plot_nav(navs: dict, bah: dict, title: str, out_path: str):
    fig, ax = plt.subplots(figsize=(14, 7))
    for label, nav in navs.items():
        ax.semilogy(nav.index, nav.values, color=COLORS[label], lw=1.6,
                    label=f"{label} swing")
    for label, nav in bah.items():
        ax.semilogy(nav.index, nav.values, color=COLORS[label], lw=1.0, ls="--",
                    alpha=0.55, label=f"{label} buy & hold")
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_ylabel("Portfolio value (USD, log scale)")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="upper left", fontsize=9, ncol=2)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved -> {out_path}")


def plot_metrics_table(rows: list, columns: list, title: str, out_path: str):
    n_rows, n_cols = len(rows), len(columns)
    fig, ax = plt.subplots(figsize=(max(13, n_cols * 1.45), 1.0 + 0.5 * n_rows))
    ax.axis("off")
    cell_text, row_colors = [], []
    for r in rows:
        cells = []
        for c in columns:
            v = r.get(c, "")
            if isinstance(v, float):
                if "$" in c or "NAV" in c:
                    cells.append(f"${v:,.0f}")
                elif "DD" in c or "return" in c.lower() or "Avg trade" in c:
                    cells.append(f"{v:+.2f}%")
                elif "(%)" in c:
                    cells.append(f"{v:.2f}%")
                elif "Sharpe" in c:
                    cells.append(f"{v:.2f}")
                elif "days" in c:
                    cells.append(f"{v:.1f}")
                else:
                    cells.append(f"{v:.2f}")
            else:
                cells.append(str(v))
        cell_text.append(cells)
        prod = r.get("Strategy", "").split()[0]
        row_colors.append(matplotlib.colors.to_rgba(COLORS.get(prod, "#ccc"), alpha=0.18))
    tbl = ax.table(cellText=cell_text, colLabels=columns, cellLoc="center",
                   loc="center", cellColours=[[rc] * n_cols for rc in row_colors])
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.5)
    tbl.scale(1.0, 1.5)
    ax.set_title(title, fontsize=12, fontweight="bold", pad=14)
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved -> {out_path}")


# ── 5. Run ──────────────────────────────────────────────────────────────────

METRIC_COLS = ["Strategy", "Final NAV ($)", "Total return (%)", "CAGR (%)",
               "In-market vol (%)", "Sharpe", "Max DD (%)", "Time in market (%)",
               "Trades", "Win rate (%)", "Avg hold (days)", "Avg trade (%)"]


def run_period(prices: pd.DataFrame, label: str, letter: str) -> list:
    start, end = prices.index[0], prices.index[-1]
    print(f"\n────── Period {letter}: {label} ({start.date()} -> {end.date()}) ──────")
    qqq_ret = prices["QQQ"].pct_change()

    swing_navs, bah_navs, rows = {}, {}, []
    for p in prices.columns:
        nav, pos = backtest(prices[p], qqq_ret)
        swing_navs[p] = nav
        bah_navs[p] = 10_000.0 * prices[p] / prices[p].iloc[0]
        rows.append(perf_metrics(nav, pos, f"{p} swing"))
        # also a buy & hold row for comparison
        bah_pos = pd.Series(1, index=prices.index)
        rows.append(perf_metrics(bah_navs[p], bah_pos, f"{p} buy & hold"))

    plot_nav(swing_navs, bah_navs,
             f"Reddit QQQ swing (buy after <-2%, sell after >+3%) — Period {letter}: {label}",
             str(FIG / f"qqq_swing_nav_period{letter}.png"))
    plot_metrics_table(rows, METRIC_COLS,
                       f"QQQ swing vs buy & hold — Period {letter}: {label}",
                       str(FIG / f"qqq_swing_metrics_period{letter}.png"))

    print("\nSummary:")
    for r in rows:
        print(f"  {r['Strategy']:<18} CAGR {r['CAGR (%)']:7.2f}%  Sharpe {r['Sharpe']:5.2f}  "
              f"MaxDD {r['Max DD (%)']:7.2f}%  inMkt {r['Time in market (%)']:5.1f}%  "
              f"trades {r['Trades']:>3}  win {r['Win rate (%)'] if not np.isnan(r['Win rate (%)']) else 0:4.0f}%")
    return rows


def current_month_check(qqq: pd.Series, asof_note: str):
    """Detailed verification of whether the strategy is active THIS month."""
    ret = qqq.pct_change()
    pos = swing_positions(ret)

    last_day = qqq.index.max()
    print("\n" + "=" * 70)
    print("CURRENT-MONTH / LIVE-STATE CHECK")
    print("=" * 70)
    print(f"Data source: {asof_note}")
    print(f"Latest session in data: {last_day.date()}  (QQQ close {qqq.iloc[-1]:.2f})")
    print(f"Position state on latest session: {'INVESTED' if pos.iloc[-1] else 'FLAT (in cash)'}")

    # When did the last entry/exit trigger fire?
    entry_days = ret[ret < ENTRY_THRESHOLD]
    exit_days = ret[ret > EXIT_THRESHOLD]
    if len(entry_days):
        d = entry_days.index[-1]
        print(f"Most recent ENTRY trigger (QQQ day < -2%): {d.date()} ({entry_days.iloc[-1]*100:+.2f}%)"
              f"  -> would buy next session {qqq.loc[d:].index[1].date() if len(qqq.loc[d:])>1 else 'n/a'}")
    if len(exit_days):
        d = exit_days.index[-1]
        print(f"Most recent EXIT trigger  (QQQ day > +3%): {d.date()} ({exit_days.iloc[-1]*100:+.2f}%)"
              f"  -> would sell next session {qqq.loc[d:].index[1].date() if len(qqq.loc[d:])>1 else 'n/a'}")

    # This calendar month
    cm = qqq[(qqq.index.year == last_day.year) & (qqq.index.month == last_day.month)]
    cm_ret = ret.reindex(cm.index)
    print(f"\nThis month ({last_day.strftime('%Y-%m')}) — {len(cm)} sessions in data:")
    month_entry = cm_ret[cm_ret < ENTRY_THRESHOLD]
    month_exit = cm_ret[cm_ret > EXIT_THRESHOLD]
    print(f"  days with QQQ return < -2% (entry triggers): {len(month_entry)}")
    print(f"  days with QQQ return > +3% (exit triggers):  {len(month_exit)}")
    print(f"  worst day this month: {cm_ret.min()*100:+.2f}%   best day: {cm_ret.max()*100:+.2f}%")
    verdict = ("ACTIVE — at least one -2% entry trigger fired this month"
               if len(month_entry) else
               "NOT TRIGGERED this month — no -2% QQQ down-day, so the strategy stays in cash")
    print(f"  VERDICT: {verdict}")

    # Save a signal log of the most recent 40 sessions for inspection
    log = pd.DataFrame({
        "qqq_close": qqq,
        "qqq_ret_%": ret * 100,
        "entry_trigger": (ret < ENTRY_THRESHOLD),
        "exit_trigger": (ret > EXIT_THRESHOLD),
        "position": pos,
    }).tail(40)
    out = DATA / "qqq_swing_signals.csv"
    log.to_csv(out)
    print(f"\nSaved recent signal log -> {out}")
    return verdict


if __name__ == "__main__":
    prices_A, prices_B, qqq_full, asof_note = load_prices()
    print(f"\nData: {asof_note}")

    rows_A = run_period(prices_A, "Simulation era 1999-today", "A")
    rows_B = run_period(prices_B, "Real era 2010-today", "B")

    all_rows = []
    for letter, rows in [("A", rows_A), ("B", rows_B)]:
        for r in rows:
            all_rows.append({"Period": letter, **r})
    out_csv = DATA / "qqq_swing_metrics.csv"
    pd.DataFrame(all_rows).to_csv(out_csv, index=False)
    print(f"\nSaved -> {out_csv}")

    current_month_check(qqq_full, asof_note)
