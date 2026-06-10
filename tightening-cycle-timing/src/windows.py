"""Rolling 3-month signal windows and similarity-to-now analysis.

Every calendar month t defines a window covering months (t-2 .. t).
Each window is summarized by a 10-feature "signal pattern":

  equities (S&P 500):  3m return, 3m realized vol (annualized),
                       drawdown from trailing 12m high, 12m momentum
  policy:              3m change in the funds rate, real funds rate
                       (funds rate - CPI YoY)
  inflation:           CPI YoY level, 3m change in CPI YoY
  bond market:         2y - funds-rate gap, 3m change in the 2y yield

Features are z-scored over the full sample; similarity to the current
window is the RMS distance over the features available in both rows
(windows missing >3 features are dropped, which effectively starts the
sample in 1955 — yield features join in 1962 when DGS1 begins).

Each window also gets a discrete pattern code
(policy HIKE/CUT/HOLD x inflation up/down/flat x equity up/down/flat x
vol high/mid/low) whose historical frequency and forward returns are
tabulated.

Outputs: output/WINDOWS.md, output/window_signals.csv,
         output/window_similarity.png, output/window_analog_paths.png
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import detect
from analysis import OUT
from data import load_all
from regime import load_extended

MAX_FFILL = 6          # months a macro series may be carried forward
MIN_FEATURES = 7       # windows with fewer available features are dropped
EXCLUDE_MONTHS = 12    # ignore windows this close to "now" when ranking
EPISODE_GAP = 9        # months separating distinct analog episodes
TOP_K = 10

FEATURES = ["eq_ret_3m", "eq_vol_3m", "eq_dd_12m", "eq_mom_12m",
            "ff_chg_3m", "real_ff", "cpi_yoy", "cpi_yoy_chg_3m",
            "y2_minus_ff", "y2_chg_3m"]


def build_features(series, ext) -> tuple[pd.DataFrame, dict]:
    spx_d = ext["SPX"]
    spx_me = spx_d.resample("ME").last()
    r = spx_d.pct_change()

    eq_ret_3m = spx_me.pct_change(3) * 100
    eq_mom_12m = spx_me.pct_change(12) * 100
    eq_vol_3m = (r.rolling("91D").std() * np.sqrt(252) * 100).resample("ME").last()
    eq_dd_12m = (spx_d / spx_d.rolling("365D").max() - 1).resample("ME").last() * 100

    def month_end(s):
        x = s.copy()
        x.index = x.index + pd.offsets.MonthEnd(0)
        return x[~x.index.duplicated(keep="last")]

    ff = month_end(series["FEDFUNDS"])
    cpi = month_end(series["CPIAUCSL"])
    cpi_yoy = (cpi / cpi.shift(12) - 1) * 100
    y2 = detect.splice_short_rate(ext["DGS2"], series["DGS1"]).resample("ME").last()

    idx = spx_me.index
    df = pd.DataFrame(index=idx)
    df["eq_ret_3m"] = eq_ret_3m
    df["eq_vol_3m"] = eq_vol_3m
    df["eq_dd_12m"] = eq_dd_12m
    df["eq_mom_12m"] = eq_mom_12m

    stale = {}
    for name, s in [("ff", ff), ("cpi_yoy", cpi_yoy), ("y2", y2)]:
        aligned = s.reindex(idx)
        filled = aligned.ffill(limit=MAX_FFILL)
        last_real = s.dropna().index.max()
        stale[name] = last_real
        df[f"_{name}"] = filled
    df["ff_chg_3m"] = df["_ff"] - df["_ff"].shift(3)
    df["real_ff"] = df["_ff"] - df["_cpi_yoy"]
    df["cpi_yoy"] = df["_cpi_yoy"]
    df["cpi_yoy_chg_3m"] = df["_cpi_yoy"] - df["_cpi_yoy"].shift(3)
    df["y2_minus_ff"] = df["_y2"] - df["_ff"]
    df["y2_chg_3m"] = df["_y2"] - df["_y2"].shift(3)
    df = df[FEATURES]

    df = df[df.notna().sum(axis=1) >= MIN_FEATURES]
    # forward returns for "what happened next"
    fwd = pd.DataFrame(index=spx_me.index)
    fwd["fwd_6m_%"] = (spx_me.shift(-6) / spx_me - 1) * 100
    fwd["fwd_12m_%"] = (spx_me.shift(-12) / spx_me - 1) * 100
    return df.join(fwd), stale


def pattern_code(row) -> str:
    pol = ("HIKE" if row["ff_chg_3m"] > 0.20 else
           "CUT" if row["ff_chg_3m"] < -0.20 else "HOLD")
    inf = ("infl-up" if row["cpi_yoy_chg_3m"] > 0.1 else
           "infl-dn" if row["cpi_yoy_chg_3m"] < -0.1 else "infl-flat")
    eq = ("eq-up" if row["eq_ret_3m"] > 2 else
          "eq-dn" if row["eq_ret_3m"] < -2 else "eq-flat")
    return f"{pol} | {inf} | {eq} | {row['_volband']}-vol"


def add_patterns(df: pd.DataFrame) -> pd.DataFrame:
    lo, hi = df["eq_vol_3m"].quantile([0.3, 0.7])
    df = df.copy()
    df["_volband"] = np.where(df["eq_vol_3m"] < lo, "low",
                              np.where(df["eq_vol_3m"] > hi, "high", "mid"))
    df["pattern"] = df.apply(pattern_code, axis=1)
    return df.drop(columns="_volband")


def similarity(df: pd.DataFrame) -> pd.DataFrame:
    z = (df[FEATURES] - df[FEATURES].mean()) / df[FEATURES].std()
    now = z.iloc[-1]
    diff2 = (z - now) ** 2
    avail = diff2.notna().sum(axis=1)
    dist = np.sqrt(diff2.sum(axis=1) / avail)
    out = df.copy()
    out["distance"] = dist
    out["n_features"] = avail
    return out


def pick_episodes(ranked: pd.DataFrame, now: pd.Timestamp) -> pd.DataFrame:
    cand = ranked[abs((ranked.index - now).days) > EXCLUDE_MONTHS * 30.4]
    picks = []
    for t, row in cand.sort_values("distance").iterrows():
        if all(abs((t - p).days) > EPISODE_GAP * 30.4 for p in picks):
            picks.append(t)
        if len(picks) == TOP_K:
            break
    return ranked.loc[sorted(picks)]


def make_figures(df, analogs, spx_d, now):
    spx_me = spx_d.resample("ME").last()
    fig, (ax, axd) = plt.subplots(2, 1, figsize=(13, 7.5), sharex=True,
                                  gridspec_kw={"height_ratios": [2, 1]})
    seg = spx_me[spx_me.index >= df.index.min()]
    ax.plot(seg.index, seg.values, color="black", lw=0.9, label="S&P 500 (monthly)")
    ax.set_yscale("log")
    for i, t in enumerate(analogs.index):
        ax.axvspan(t - pd.DateOffset(months=3), t, color="darkorange",
                   alpha=0.45, label="top-10 analog window" if i == 0 else None)
    ax.axvspan(now - pd.DateOffset(months=3), now, color="crimson", alpha=0.6,
               label=f"now ({now:%Y-%m})")
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.25)
    ax.set_title("Rolling 3-month signal windows: similarity to the current window")

    axd.plot(df.index, df["distance"], color="steelblue", lw=0.8)
    axd.scatter(analogs.index, analogs["distance"], color="darkorange",
                zorder=3, s=25)
    axd.set_ylabel("signal distance to now\n(lower = more similar)", fontsize=8)
    axd.grid(alpha=0.25)
    axd.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.tight_layout()
    fig.savefig(OUT / "window_similarity.png", dpi=130)
    plt.close(fig)

    # forward paths of the closest analogs vs. the path into "now"
    fig, ax = plt.subplots(figsize=(10, 6))
    months = range(-6, 25)
    paths = []
    for t in analogs.sort_values("distance").index[:5]:
        base = spx_me.asof(t)
        path = [spx_me.asof(t + pd.DateOffset(months=m)) / base * 100
                if t + pd.DateOffset(months=m) <= spx_me.index.max() else np.nan
                for m in months]
        paths.append(path)
        ax.plot(months, path, lw=1.0, alpha=0.6, label=f"{t:%Y-%m} (d={analogs.loc[t, 'distance']:.2f})")
    med = np.nanmedian(np.array(paths, dtype=float), axis=0)
    ax.plot(months, med, lw=2.2, color="black", label="median of top-5 analogs")
    base_now = spx_me.asof(now)
    now_path = [spx_me.asof(now + pd.DateOffset(months=m)) / base_now * 100
                for m in range(-6, 1)]
    ax.plot(range(-6, 1), now_path, lw=2.2, color="crimson", label="now (trailing 6m)")
    ax.axvline(0, color="gray", lw=0.8)
    ax.set_xlabel("months from window end")
    ax.set_ylabel("S&P 500 (100 = window end)")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)
    ax.set_title("S&P 500 around the five closest historical analogs")
    fig.tight_layout()
    fig.savefig(OUT / "window_analog_paths.png", dpi=130)
    plt.close(fig)


def write_report(df, analogs, stale, now, last_close):
    cur = df.loc[now]
    same = df[df["pattern"] == cur["pattern"]]
    same_hist = same[abs((same.index - now).days) > EXCLUDE_MONTHS * 30.4]

    L = []
    w = L.append
    w("# Rolling 3-month signal windows: which past periods look like now?\n")
    w(f"_Generated {pd.Timestamp.now():%Y-%m-%d}. Windows step monthly; each "
      f"covers the 3 months ending at the date shown. Sample: "
      f"{df.index.min():%Y-%m} to {df.index.max():%Y-%m} "
      f"({len(df)} windows); the final window is partial, ending at the "
      f"last available close ({last_close:%Y-%m-%d}). Yield features join "
      "in 1962 (DGS1 start); distance is RMS over available z-scored "
      "features._\n")

    w("\n## The current window\n")
    w(f"Window ending **{now:%Y-%m}** — pattern: **`{cur['pattern']}`**\n")
    feat_rows = pd.DataFrame({"feature": FEATURES,
                              "value": [round(cur[f], 2) for f in FEATURES]})
    w(feat_rows.to_markdown(index=False))
    w("\nStale inputs carried forward into the current window (mirror "
      "freshness): "
      + "; ".join(f"{k} last observed {v:%Y-%m-%d}" for k, v in stale.items())
      + ".\n")

    w("\n## Most similar past windows (top 10 distinct episodes)\n")
    view = analogs.reset_index().rename(columns={"index": "window_end"})
    view["window_end"] = pd.to_datetime(view["window_end"]).dt.strftime("%Y-%m")
    cols = ["window_end", "distance", "pattern", "eq_ret_3m", "ff_chg_3m",
            "cpi_yoy", "y2_minus_ff", "fwd_6m_%", "fwd_12m_%"]
    w(view[cols].round(2).to_markdown(index=False))
    w(f"\nForward S&P 500 returns after these analogs: median "
      f"{analogs['fwd_12m_%'].median():+.1f}% over 12 months "
      f"(range {analogs['fwd_12m_%'].min():+.1f}% to "
      f"{analogs['fwd_12m_%'].max():+.1f}%).\n")

    w("\n## Pattern-code view\n")
    w(f"The current pattern `{cur['pattern']}` occurred in "
      f"{len(same_hist)} historical windows "
      f"({100 * len(same_hist) / len(df):.1f}% of the sample).")
    if len(same_hist):
        w(f" After those windows the S&P 500 was higher 12 months later in "
          f"{(same_hist['fwd_12m_%'] > 0).mean() * 100:.0f}% of cases "
          f"(median {same_hist['fwd_12m_%'].median():+.1f}%).\n")
    w("\nMost frequent patterns over the full sample:\n")
    freq = (df.groupby("pattern")
              .agg(n=("pattern", "size"), med_fwd_12m=("fwd_12m_%", "median"))
              .sort_values("n", ascending=False).head(12).reset_index())
    w(freq.round(1).to_markdown(index=False))

    w("\n\n## Reading and limitations\n")
    w("- Similarity is measured on contemporaneous signals only — it knows "
      "nothing about valuations, positioning, fiscal policy or the *cause* "
      "of each configuration.")
    w("- The current window inherits the mirror staleness listed above; "
      "CPI in particular is carried forward, so the inflation features of "
      "'now' are softer than the rest.")
    w("- Forward-return statistics over ~10 analogs (or one pattern cell) "
      "are anecdotes, not expectancies — same n<=7 spirit as the main "
      "study.")
    w("- Pre-1962 windows lack the two 2y-yield features; their distances "
      "are computed over the remaining 8 signals.")

    (OUT / "WINDOWS.md").write_text("\n".join(L), encoding="utf-8")


def main():
    series = load_all()
    ext = load_extended(series)
    df, stale = build_features(series, ext)
    df = add_patterns(df)
    df = similarity(df)
    now = df.index[-1]
    analogs = pick_episodes(df, now)
    make_figures(df, analogs, ext["SPX"], now)
    write_report(df, analogs, stale, now, ext["SPX"].index.max())
    df.round(3).to_csv(OUT / "window_signals.csv")
    print(f"[windows] {len(df)} windows {df.index.min():%Y-%m}..{now:%Y-%m}; "
          f"current pattern: {df.loc[now, 'pattern']}")
    print("[windows] top analogs:",
          ", ".join(f"{t:%Y-%m}" for t in analogs.sort_values('distance').index))


if __name__ == "__main__":
    main()
