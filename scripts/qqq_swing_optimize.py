"""
Upgraded swing strategy — threshold grid search + TP/SL overlay.

Starting point: the Reddit rule (buy after a prev-day QQQ return < -2%, sell
after a prev-day return > +3%). This script searches for BETTER entry/exit
thresholds and then bolts a take-profit / stop-loss overlay on top to cut risk.

Everything is evaluated on the LONG simulated TQQQ series (1999-03-11 ->
2026-05-08, 6,833 trading days) — that is the "longer period" and the asset we
actually buy, because the leverage is where the threshold choice matters most.

Signal source is parametric:
  - "QQQ"  : entry/exit thresholds compare the prev-day QQQ return  (default,
             keeps the original strategy's identity; thresholds ~ -2% / +3%)
  - "TQQQ" : thresholds compare the prev-day TQQQ return            (~3x scale)

No look-ahead: the position held on day T is decided purely from information
available through day T-1 (prev-day signal return AND trade P&L to the prior
close).

Outputs (NO report/README changes — those are intentionally left untouched):
  figures/swing_opt_heatmap_cagr.png
  figures/swing_opt_heatmap_sharpe.png
  figures/swing_opt_tpsl_heatmap.png
  data/swing_opt_grid.csv          (every (signal, entry, exit) combo)
  data/swing_opt_tpsl.csv          (TP/SL sweep on the selected configs)
"""

import matplotlib
matplotlib.use("Agg")
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIG = ROOT / "figures"
DATA.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

TRADING_DAYS = 252

# ── 1. Load the long Period-A series (QQQ + simulated TQQQ) ──────────────────

qld_df = pd.read_csv(DATA / "qld_simulated.csv", index_col=0, parse_dates=True)
tqqq_df = pd.read_csv(DATA / "tqqq_simulated.csv", index_col=0, parse_dates=True)

qqq = qld_df["QQQ"].dropna()
tqqq = tqqq_df["TQQQ_simulated"].dropna()          # 1999 -> 2026-05-08
prices = pd.DataFrame({"QQQ": qqq, "TQQQ": tqqq}).dropna()
prices = prices.loc["1999-03-11":]

qqq_ret = prices["QQQ"].pct_change().fillna(0.0).values
tqqq_ret = prices["TQQQ"].pct_change().fillna(0.0).values
tqqq_price = (1.0 + pd.Series(tqqq_ret)).cumprod().values   # relative price level
N = len(prices)
START, END = prices.index[0].date(), prices.index[-1].date()
print(f"Loaded {N} sessions: {START} -> {END}  (buy TQQQ, simulated long series)")

# ── 2. Core backtest (numpy state machine) ──────────────────────────────────

def run_swing(signal_ret, asset_ret, asset_price, entry_thr, exit_thr,
              tp=None, sl=None, cooldown=0, trend_mask=None):
    """Return (nav, pos, n_trades). All inputs are aligned numpy arrays.

    entry: prev-day signal_ret < entry_thr  (enter, hold from this day)
           AND (trend_mask[i-1] if a trend filter is supplied)
           AND not inside a post-stop cooldown window
    exit : prev-day signal_ret > exit_thr   OR  prev-day trade P&L >= tp
                                            OR  prev-day trade P&L <= -sl
    cooldown   : sessions to stay flat after a STOP-LOSS exit (blocks re-entry
                 into a still-falling market — the failure mode of plain TP/SL).
    trend_mask : optional bool array; entry only allowed where True (e.g.
                 price > 200-day SMA — only buy dips inside an uptrend).
    """
    n = len(asset_ret)
    pos = np.zeros(n)
    state = 0
    entry_px = None
    cd = 0
    for i in range(1, n):
        ps = signal_ret[i - 1]
        if state == 0:
            if cd > 0:
                cd -= 1
            ok = ps < entry_thr and cd == 0
            if trend_mask is not None:
                ok = ok and bool(trend_mask[i - 1])
            if ok:
                state = 1
                entry_px = asset_price[i - 1]      # bought at prior close
        else:
            exit_now = ps > exit_thr
            if entry_px is not None:
                tr = asset_price[i - 1] / entry_px - 1.0   # P&L to prior close
                if tp is not None and tr >= tp:
                    exit_now = True
                if sl is not None and tr <= -sl:
                    exit_now = True
                    cd = cooldown                          # arm cooldown on a stop
            if exit_now:
                state = 0
                entry_px = None
        pos[i] = state
    strat_ret = pos * asset_ret
    nav = np.cumprod(1.0 + strat_ret)
    n_trades = int(np.sum((np.diff(pos) == 1))) + (1 if pos[0] == 1 else 0)
    return nav, pos, n_trades


def metrics(nav, pos, strat_ret, n_trades):
    years = len(nav) / TRADING_DAYS
    cagr = nav[-1] ** (1.0 / years) - 1.0
    sd = strat_ret.std()
    sharpe = (strat_ret.mean() / sd * np.sqrt(TRADING_DAYS)) if sd > 0 else np.nan
    peak = np.maximum.accumulate(nav)
    mdd = (nav / peak - 1.0).min()
    return {
        "CAGR": cagr * 100,
        "Sharpe": sharpe,
        "MaxDD": mdd * 100,
        "Finalx": nav[-1],
        "TimeInMkt": pos.mean() * 100,
        "Trades": n_trades,
    }


# 200-day trend filter on QQQ (only buy dips while QQQ closes above its 200d SMA)
qqq_sma200 = prices["QQQ"].rolling(200).mean().values
trend_up = prices["QQQ"].values > qqq_sma200          # bool array, NaN -> False


def evaluate(signal_ret, entry_thr, exit_thr, tp=None, sl=None,
             cooldown=0, trend=False, lo=0, hi=None):
    hi = N if hi is None else hi
    tmask = trend_up[lo:hi] if trend else None
    nav, pos, nt = run_swing(signal_ret[lo:hi], tqqq_ret[lo:hi],
                             tqqq_price[lo:hi] / tqqq_price[lo], entry_thr,
                             exit_thr, tp, sl, cooldown=cooldown, trend_mask=tmask)
    strat_ret = pos * tqqq_ret[lo:hi]
    return metrics(nav, pos, strat_ret, nt)


# ── 3. Baseline (the original -2% / +3% rule on TQQQ) ───────────────────────

base = evaluate(qqq_ret, -0.02, 0.03)
bh_nav = tqqq_price / tqqq_price[0]
bh_years = N / TRADING_DAYS
bh = {
    "CAGR": (bh_nav[-1] ** (1 / bh_years) - 1) * 100,
    "Sharpe": tqqq_ret.std() and tqqq_ret[1:].mean() / tqqq_ret[1:].std() * np.sqrt(TRADING_DAYS),
    "MaxDD": (bh_nav / np.maximum.accumulate(bh_nav) - 1).min() * 100,
    "TimeInMkt": 100.0, "Trades": 1,
}
print(f"\nBaseline TQQQ buy & hold        : CAGR {bh['CAGR']:6.2f}%  Sharpe {bh['Sharpe']:.2f}  MaxDD {bh['MaxDD']:7.2f}%")
print(f"Baseline swing -2%/+3% (QQQ sig): CAGR {base['CAGR']:6.2f}%  Sharpe {base['Sharpe']:.2f}  MaxDD {base['MaxDD']:7.2f}%  trades {base['Trades']}")

# ── 4. Grid search over (entry, exit) for each signal source ────────────────

def grid_for_signal(signal_ret, entry_grid, exit_grid, tag):
    rows = []
    for e in entry_grid:
        for x in exit_grid:
            m = evaluate(signal_ret, e, x)
            rows.append({"signal": tag, "entry": e, "exit": x, **m})
    return pd.DataFrame(rows)

# QQQ-signal grid (thresholds on QQQ return, ~original scale)
q_entry = np.round(np.arange(-0.005, -0.0525, -0.0025), 4)   # -0.5% .. -5.0%
q_exit  = np.round(np.arange(0.005, 0.0825, 0.0025), 4)      # +0.5% .. +8.0%
print(f"\nGrid search (QQQ signal): {len(q_entry)} entry x {len(q_exit)} exit = {len(q_entry)*len(q_exit)} combos ...")
grid_q = grid_for_signal(qqq_ret, q_entry, q_exit, "QQQ")

# TQQQ-signal grid (~3x scaled thresholds)
t_entry = np.round(np.arange(-0.015, -0.1575, -0.0075), 4)   # -1.5% .. -15%
t_exit  = np.round(np.arange(0.015, 0.2475, 0.0075), 4)      # +1.5% .. +24%
print(f"Grid search (TQQQ signal): {len(t_entry)} entry x {len(t_exit)} exit = {len(t_entry)*len(t_exit)} combos ...")
grid_t = grid_for_signal(tqqq_ret, t_entry, t_exit, "TQQQ")

grid = pd.concat([grid_q, grid_t], ignore_index=True)
grid.to_csv(DATA / "swing_opt_grid.csv", index=False)
print(f"Saved -> {DATA/'swing_opt_grid.csv'}")

# ── 5. Pick winners ─────────────────────────────────────────────────────────

def show(title, r):
    print(f"  {title:<32} entry {r['entry']*100:+5.2f}%  exit {r['exit']*100:+5.2f}%  "
          f"[{r['signal']:>4} sig]  CAGR {r['CAGR']:6.2f}%  Sharpe {r['Sharpe']:.2f}  "
          f"MaxDD {r['MaxDD']:7.2f}%  inMkt {r['TimeInMkt']:4.1f}%  trades {int(r['Trades'])}")

best_cagr = grid.loc[grid["CAGR"].idxmax()]
best_sharpe = grid.loc[grid["Sharpe"].idxmax()]
# also per-signal bests for QQQ signal (the headline, comparable to original)
best_cagr_q = grid_q.loc[grid_q["CAGR"].idxmax()]
best_sharpe_q = grid_q.loc[grid_q["Sharpe"].idxmax()]

print("\n── Winners ──────────────────────────────────────────────────────")
show("Highest CAGR (all signals)", best_cagr)
show("Highest Sharpe (all signals)", best_sharpe)
show("Highest CAGR (QQQ signal)", best_cagr_q)
show("Highest Sharpe (QQQ signal)", best_sharpe_q)

print("\nTop 5 by CAGR:")
for _, r in grid.sort_values("CAGR", ascending=False).head(5).iterrows():
    show("", r)
print("Top 5 by Sharpe:")
for _, r in grid.sort_values("Sharpe", ascending=False).head(5).iterrows():
    show("", r)

# ── 6. Heatmaps (QQQ-signal grid, comparable to the original thresholds) ────

def heatmap(grid_df, entry_grid, exit_grid, value, title, out, fmt="%.0f",
            star=None):
    piv = grid_df.pivot(index="entry", columns="exit", values=value)
    piv = piv.reindex(index=sorted(entry_grid), columns=sorted(exit_grid))
    fig, ax = plt.subplots(figsize=(13, 6))
    im = ax.imshow(piv.values, aspect="auto", origin="lower", cmap="viridis")
    ax.set_xticks(range(len(piv.columns)))
    ax.set_xticklabels([f"{c*100:.1f}" for c in piv.columns], rotation=90, fontsize=7)
    ax.set_yticks(range(len(piv.index)))
    ax.set_yticklabels([f"{r*100:.2f}" for r in piv.index], fontsize=7)
    ax.set_xlabel("Exit threshold: prev-day QQQ return > X%  (sell)")
    ax.set_ylabel("Entry threshold: prev-day QQQ return < Y%  (buy)")
    ax.set_title(title, fontsize=12, fontweight="bold")
    fig.colorbar(im, ax=ax, label=value)
    if star is not None:
        try:
            yi = list(piv.index).index(round(star["entry"], 4))
            xi = list(piv.columns).index(round(star["exit"], 4))
            ax.scatter([xi], [yi], marker="*", s=320, c="red", edgecolors="white", zorder=5)
        except ValueError:
            pass
    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved -> {out}")

heatmap(grid_q, q_entry, q_exit, "CAGR",
        f"TQQQ swing — CAGR (%) over QQQ-signal thresholds, {START}->{END}\n"
        f"red star = max CAGR; black dot in text = original -2%/+3%",
        str(FIG / "swing_opt_heatmap_cagr.png"), star=best_cagr_q)
heatmap(grid_q, q_entry, q_exit, "Sharpe",
        f"TQQQ swing — Sharpe over QQQ-signal thresholds, {START}->{END}\n"
        f"red star = max Sharpe",
        str(FIG / "swing_opt_heatmap_sharpe.png"), star=best_sharpe_q)

# ── 7. TP/SL overlay on the selected configs ────────────────────────────────
# Apply take-profit / stop-loss to BOTH the best-CAGR and best-Sharpe configs.

tp_grid = [None, 0.10, 0.20, 0.30, 0.50, 0.75, 1.00]      # take-profit on TQQQ trade
sl_grid = [None, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50]      # stop-loss on TQQQ trade

def tpsl_sweep(cfg, sig_arr, label):
    rows = []
    for tp in tp_grid:
        for sl in sl_grid:
            m = evaluate(sig_arr, cfg["entry"], cfg["exit"], tp=tp, sl=sl)
            rows.append({"config": label, "entry": cfg["entry"], "exit": cfg["exit"],
                         "tp": tp, "sl": sl, **m})
    return pd.DataFrame(rows)

sig_map = {"QQQ": qqq_ret, "TQQQ": tqqq_ret}
sweep_cagr = tpsl_sweep(best_cagr, sig_map[best_cagr["signal"]], "best-CAGR")
sweep_sharpe = tpsl_sweep(best_sharpe, sig_map[best_sharpe["signal"]], "best-Sharpe")
tpsl = pd.concat([sweep_cagr, sweep_sharpe], ignore_index=True)
tpsl.to_csv(DATA / "swing_opt_tpsl.csv", index=False)
print(f"\nSaved -> {DATA/'swing_opt_tpsl.csv'}")

def fmt_lvl(v):
    return "none" if v is None else f"{v*100:.0f}%"

print("\n── TP/SL overlay on the best-Sharpe config "
      f"(entry {best_sharpe['entry']*100:+.2f}%, exit {best_sharpe['exit']*100:+.2f}%, "
      f"{best_sharpe['signal']} sig) ──")
no_overlay = sweep_sharpe[(sweep_sharpe.tp.isna()) & (sweep_sharpe.sl.isna())].iloc[0]
print(f"  no TP/SL                : CAGR {no_overlay['CAGR']:6.2f}%  Sharpe {no_overlay['Sharpe']:.2f}  MaxDD {no_overlay['MaxDD']:7.2f}%")
# best risk-adjusted overlay (max Sharpe) and best drawdown-reduction that keeps CAGR within 25% of base
best_overlay = sweep_sharpe.loc[sweep_sharpe["Sharpe"].idxmax()]
print(f"  max-Sharpe overlay      : TP {fmt_lvl(best_overlay['tp'])} / SL {fmt_lvl(best_overlay['sl'])}  "
      f"-> CAGR {best_overlay['CAGR']:6.2f}%  Sharpe {best_overlay['Sharpe']:.2f}  MaxDD {best_overlay['MaxDD']:7.2f}%")
# shallowest drawdown that retains >= 70% of the no-overlay CAGR
keep = sweep_sharpe[sweep_sharpe["CAGR"] >= 0.70 * no_overlay["CAGR"]]
safest = keep.loc[keep["MaxDD"].idxmax()]   # MaxDD is negative; max() = shallowest
print(f"  shallowest-DD (>=70%CAGR): TP {fmt_lvl(safest['tp'])} / SL {fmt_lvl(safest['sl'])}  "
      f"-> CAGR {safest['CAGR']:6.2f}%  Sharpe {safest['Sharpe']:.2f}  MaxDD {safest['MaxDD']:7.2f}%")

# TP/SL heatmap (Sharpe) for the best-Sharpe config
piv = sweep_sharpe.copy()
piv["tp_l"] = piv["tp"].map(fmt_lvl)
piv["sl_l"] = piv["sl"].map(fmt_lvl)
pv = piv.pivot(index="tp_l", columns="sl_l", values="MaxDD")
order_tp = [fmt_lvl(v) for v in tp_grid]
order_sl = [fmt_lvl(v) for v in sl_grid]
pv = pv.reindex(index=order_tp, columns=order_sl)
fig, ax = plt.subplots(figsize=(9, 6))
im = ax.imshow(pv.values, aspect="auto", origin="upper", cmap="RdYlGn")
ax.set_xticks(range(len(pv.columns))); ax.set_xticklabels(pv.columns)
ax.set_yticks(range(len(pv.index))); ax.set_yticklabels(pv.index)
ax.set_xlabel("Stop-loss (TQQQ trade drawdown)")
ax.set_ylabel("Take-profit (TQQQ trade gain)")
ax.set_title(f"Max drawdown (%) under TP/SL — best-Sharpe config\n"
             f"entry {best_sharpe['entry']*100:+.2f}% / exit {best_sharpe['exit']*100:+.2f}% ({best_sharpe['signal']} sig)",
             fontsize=11, fontweight="bold")
for i in range(len(pv.index)):
    for j in range(len(pv.columns)):
        v = pv.values[i, j]
        if not np.isnan(v):
            ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=7)
fig.colorbar(im, ax=ax, label="Max drawdown (%)")
plt.tight_layout()
plt.savefig(FIG / "swing_opt_tpsl_heatmap.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved -> {FIG/'swing_opt_tpsl_heatmap.png'}")

# ── 7b. Risk overlays: plain TP/SL is not enough — add cooldown & trend ─────
# Plain stop-losses just whipsaw because the rule re-enters the same crash the
# next dip. Two structural fixes that actually cut tail risk:
#   (a) stop-loss + re-entry COOLDOWN  (stay flat N days after a stop)
#   (b) 200-day TREND filter           (only buy dips while QQQ > 200d SMA)

bs = best_sharpe
bs_sig = sig_map[bs["signal"]]
overlays = [
    ("no overlay (best-Sharpe)",        dict()),
    ("+ stop-loss 30%",                 dict(sl=0.30)),
    ("+ stop-loss 25% + cooldown 20d",  dict(sl=0.25, cooldown=20)),
    ("+ stop-loss 30% + cooldown 40d",  dict(sl=0.30, cooldown=40)),
    ("+ 200d trend filter",             dict(trend=True)),
    ("+ trend + stop-loss 30%+cd20",    dict(trend=True, sl=0.30, cooldown=20)),
]
overlay_rows = []
print("\n── Risk overlays on best-Sharpe config "
      f"(entry {bs['entry']*100:+.2f}% / exit {bs['exit']*100:+.2f}%, {bs['signal']} sig) ──")
print(f"  {'overlay':<34} {'CAGR':>7} {'Sharpe':>7} {'MaxDD':>8} {'inMkt':>6} {'trades':>7}")
for name, kw in overlays:
    m = evaluate(bs_sig, bs["entry"], bs["exit"], **kw)
    overlay_rows.append({"overlay": name, **kw, **m})
    print(f"  {name:<34} {m['CAGR']:6.2f}% {m['Sharpe']:6.2f} {m['MaxDD']:7.2f}% "
          f"{m['TimeInMkt']:5.1f}% {int(m['Trades']):6d}")
pd.DataFrame(overlay_rows).to_csv(DATA / "swing_opt_overlays.csv", index=False)
print(f"Saved -> {DATA/'swing_opt_overlays.csv'}")

# Comparison bar: CAGR vs |MaxDD| across overlays
fig, ax = plt.subplots(figsize=(12, 6))
names = [r["overlay"] for r in overlay_rows]
cagrs = [r["CAGR"] for r in overlay_rows]
dds = [abs(r["MaxDD"]) for r in overlay_rows]
x = np.arange(len(names))
ax.bar(x - 0.2, cagrs, 0.4, label="CAGR (%)", color="#2ca02c")
ax.bar(x + 0.2, dds, 0.4, label="|Max drawdown| (%)", color="#d62728")
ax.set_xticks(x); ax.set_xticklabels(names, rotation=25, ha="right", fontsize=8)
ax.set_ylabel("%")
ax.set_title("Risk overlays — return kept vs drawdown removed (long simulated TQQQ)",
             fontsize=12, fontweight="bold")
ax.legend(); ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(FIG / "swing_opt_overlays.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved -> {FIG/'swing_opt_overlays.png'}")

# ── 8. Robustness: in-sample / out-of-sample split ──────────────────────────

split = N // 2
print(f"\n── Robustness: train {START}..{prices.index[split].date()}  |  "
      f"test {prices.index[split].date()}..{END} ──")
def oos(cfg, sig_arr, name):
    tr = evaluate(sig_arr, cfg["entry"], cfg["exit"], lo=0, hi=split)
    te = evaluate(sig_arr, cfg["entry"], cfg["exit"], lo=split, hi=N)
    print(f"  {name:<26} train CAGR {tr['CAGR']:6.2f}% Sharpe {tr['Sharpe']:.2f} | "
          f"test CAGR {te['CAGR']:6.2f}% Sharpe {te['Sharpe']:.2f} MaxDD {te['MaxDD']:7.2f}%")
oos(best_cagr, sig_map[best_cagr["signal"]], "best-CAGR params")
oos(best_sharpe, sig_map[best_sharpe["signal"]], "best-Sharpe params")
oos({"entry": -0.02, "exit": 0.03}, qqq_ret, "original -2%/+3%")

print("\nDone. (report + README intentionally untouched)")
