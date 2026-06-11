"""
QLD Replication from QQQ

QLD aims to deliver 2x the daily return of QQQ, minus a daily fee:
    r_qld(t) = 2 * r_qqq(t) - f

where f is a constant daily fee (expense ratio + financing cost, annualized / 252).

We calibrate f by minimizing the squared log-error between the simulated QLD
and actual QLD over the overlapping period (2006-06-19 to present), then extend
the simulation back to QQQ's inception (1999-03-10).

Mirrors the TQQQ replication methodology in ../../tqqq/tqqq_replication.py.
"""

import matplotlib
matplotlib.use("Agg")
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
from scipy.optimize import minimize_scalar

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIG = ROOT / "figures"
DATA.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

# ── 1. Download data ────────────────────────────────────────────────────────

print("Downloading QQQ and QLD...")
qqq = yf.download("QQQ", start="1999-03-10", auto_adjust=True)["Close"].squeeze()
qld = yf.download("QLD", start="2006-06-19", auto_adjust=True)["Close"].squeeze()

qqq = qqq.dropna()
qld = qld.dropna()

qqq_ret = qqq.pct_change().dropna()
qld_ret = qld.pct_change().dropna()

# ── 2. Calibrate fee rate ───────────────────────────────────────────────────

overlap_start = qld.index[0]
overlap_end = min(qqq.index[-1], qld.index[-1])

qqq_ov = qqq_ret.loc[overlap_start:overlap_end]
qld_ov = qld_ret.loc[overlap_start:overlap_end]

common = qqq_ov.index.intersection(qld_ov.index)
qqq_ov = qqq_ov.loc[common]
qld_ov = qld_ov.loc[common]

print(f"Calibration window: {common[0].date()} → {common[-1].date()}  ({len(common)} days)")


def simulate_qld(daily_fee: float, qqq_returns: pd.Series) -> pd.Series:
    """Simulate a 2x leveraged ETF with constant daily fee."""
    sim_ret = 2.0 * qqq_returns - daily_fee
    return (1 + sim_ret).cumprod()


def loss(daily_fee: float) -> float:
    """MSE of log price-ratio between simulated and actual QLD."""
    sim = simulate_qld(daily_fee, qqq_ov)
    actual_cum = (1 + qld_ov).cumprod()
    log_ratio = np.log(sim.values) - np.log(actual_cum.values)
    return np.mean(log_ratio ** 2)


result = minimize_scalar(loss, bounds=(-0.001, 0.002), method="bounded")
daily_fee_opt = result.x
annual_fee_opt = daily_fee_opt * 252

print(f"\nCalibrated daily fee : {daily_fee_opt*100:.5f}% per day")
print(f"Implied annual fee   : {annual_fee_opt*100:.3f}% per year")
print(f"  ≈ 0.95% expense ratio + {annual_fee_opt*100 - 0.95:.3f}% implied financing cost")

# ── 3. Simulate over the full QQQ history ───────────────────────────────────

first_qld_price = qld.loc[overlap_start]
sim_full_ret = 2.0 * qqq_ret - daily_fee_opt
sim_full_cum = (1 + sim_full_ret).cumprod()
sim_full_price = sim_full_cum * (first_qld_price / sim_full_cum.loc[overlap_start])

qld_aligned = qld.reindex(sim_full_price.index)

# ── 4. Calibration quality ──────────────────────────────────────────────────

cal_sim = sim_full_price.loc[overlap_start:overlap_end]
cal_act = qld_aligned.loc[overlap_start:overlap_end].dropna()
common_cal = cal_sim.index.intersection(cal_act.index)

sim_daily_ret = cal_sim.loc[common_cal].pct_change().dropna()
act_daily_ret = cal_act.loc[common_cal].pct_change().dropna()
ret_diff = np.log1p(sim_daily_ret) - np.log1p(act_daily_ret)
tracking_error_ann = ret_diff.std() * np.sqrt(252) * 100

log_price_ratio = np.log(cal_sim.loc[common_cal]) - np.log(cal_act.loc[common_cal])
total_log_drift = log_price_ratio.iloc[-1]

print(f"\nCalibration quality (in-sample):")
print(f"  Annualised tracking error : {tracking_error_ann:.3f}%")
print(f"  Cumulative log drift (end): {total_log_drift*100:.2f}%  "
      f"({'sim > actual' if total_log_drift > 0 else 'sim < actual'})")

# ── 5. Plot ─────────────────────────────────────────────────────────────────

fig, axes = plt.subplots(3, 1, figsize=(14, 14))
fig.suptitle(
    f"QLD Replication from QQQ\n"
    f"Calibrated fee: {annual_fee_opt*100:.3f}% / year  "
    f"({daily_fee_opt*100:.4f}% / day)",
    fontsize=14, fontweight="bold"
)

ax1 = axes[0]
ax1.semilogy(sim_full_price.index, sim_full_price.values, color="steelblue",
             lw=1.2, label="Simulated QLD (from QQQ)")
ax1.semilogy(qld_aligned.dropna().index, qld_aligned.dropna().values,
             color="darkorange", lw=1.2, alpha=0.85, label="Actual QLD")
ax1.axvline(pd.Timestamp(overlap_start), color="gray", ls="--", lw=0.8,
            label="QLD inception (calibration start)")
ax1.set_title("Full history: Simulated vs Actual QLD (log scale)")
ax1.set_ylabel("Price (USD, log scale)")
ax1.legend(fontsize=9)
ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax1.grid(True, which="both", alpha=0.3)

ax2 = axes[1]
ratio = (cal_sim.loc[common_cal] / cal_act.loc[common_cal]).dropna()
ax2.plot(ratio.index, ratio.values, color="purple", lw=0.9)
ax2.axhline(1.0, color="black", lw=0.8, ls="--")
ax2.axvline(pd.Timestamp("2022-03-16"), color="red", ls=":", lw=1.0, alpha=0.7)
ax2.text(pd.Timestamp("2022-05-01"), ratio.max() * 0.97,
         "Fed hikes begin\n(financing cost rises)", fontsize=7.5, color="red", va="top")
ax2.set_title("In-sample calibration: Simulated / Actual QLD\n"
              "(ratio > 1 → actual QLD underperforms sim, i.e. real fees higher than calibrated)")
ax2.set_ylabel("Ratio")
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax2.grid(True, alpha=0.3)

ax3 = axes[2]
pre_start = qqq_ret.index[0]
pre_end = overlap_start
sim_pre = sim_full_price.loc[pre_start:pre_end]
qqq_pre = qqq.loc[pre_start:pre_end]
qqq_pre_rebased = qqq_pre / qqq_pre.iloc[0] * sim_pre.iloc[0]

ax3.semilogy(sim_pre.index, sim_pre.values, color="steelblue", lw=1.3,
             label="Simulated QLD (pre-inception)")
ax3.semilogy(qqq_pre_rebased.index, qqq_pre_rebased.values, color="green",
             lw=1.1, alpha=0.75, label="QQQ (rebased to sim start)")
ax3.set_title("Pre-inception simulation: 1999–2006 (includes dot-com crash)")
ax3.set_ylabel("Price (USD, log scale)")
ax3.legend(fontsize=9)
ax3.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax3.grid(True, which="both", alpha=0.3)

plt.tight_layout()
out_path = str(FIG / "qld_replication.png")
plt.savefig(out_path, dpi=150, bbox_inches="tight")
print(f"\nPlot saved → {out_path}")

# ── 6. Save simulated series ────────────────────────────────────────────────

df_out = pd.DataFrame({
    "QQQ": qqq,
    "QLD_actual": qld_aligned,
    "QLD_simulated": sim_full_price,
})
csv_path = str(DATA / "qld_simulated.csv")
df_out.to_csv(csv_path)
print(f"Data saved → {csv_path}")

# ── 7. Key stats ────────────────────────────────────────────────────────────

periods = {
    "Dot-com crash (2000-03 to 2002-10)": ("2000-03-01", "2002-10-31"),
    "GFC (2007-10 to 2009-03)":           ("2007-10-01", "2009-03-31"),
    "COVID crash (2020-02 to 2020-03)":   ("2020-02-01", "2020-03-31"),
    "2022 bear market":                    ("2022-01-01", "2022-12-31"),
    "Full history":                        (str(sim_full_price.index[0].date()),
                                            str(sim_full_price.index[-1].date())),
}

print("\n── Simulated QLD drawdowns in key periods ──────────────────────────")
for label, (s, e) in periods.items():
    sub = sim_full_price.loc[s:e]
    if len(sub) < 2:
        continue
    total_ret = sub.iloc[-1] / sub.iloc[0] - 1
    max_dd = ((sub - sub.cummax()) / sub.cummax()).min()
    print(f"  {label}")
    print(f"    Total return : {total_ret*100:+.1f}%   Max drawdown: {max_dd*100:.1f}%")

# Calendar-year sanity check
print("\n── Calendar-year returns: simulated QLD ────────────────────────────")
years = sorted({d.year for d in sim_full_price.index})
for yr in years:
    sub = sim_full_price[sim_full_price.index.year == yr]
    if len(sub) < 2:
        continue
    ret = sub.iloc[-1] / sub.iloc[0] - 1
    print(f"  {yr}: {ret*100:+7.2f}%")
