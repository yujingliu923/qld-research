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
from data import CACHE_DIR, _get, _parse_two_col, load_all, MIRRORS
from regime import load_extended

ASSET_MIRRORS = {
    # London fixing, monthly, 1833 .. 2026-05
    "GOLD": "https://raw.githubusercontent.com/datasets/gold-prices/main/data/monthly.csv",
    # WTI spot, daily (EIA), 1986 .. 2026-06
    "WTI": "https://raw.githubusercontent.com/datasets/oil-prices/main/data/wti-daily.csv",
    # FRED DGS10 daily, 1962 .. 2026-03
    "DGS10": "https://raw.githubusercontent.com/FeanorKingofNoldor/prometheus/04e6a017529e506b21bbd2d3eaefdef3541bc7e8/data/fred/dgs10.csv",
}

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


def load_assets() -> dict:
    """Gold, WTI, 10y yield and the dollar index, parquet-cached."""
    import io

    out = {}

    def cached(name, fetch):
        path = CACHE_DIR / f"{name}.parquet"
        if path.exists():
            out[name] = pd.read_parquet(path)[name]
            return
        s = fetch()
        s.name = name
        s.to_frame().to_parquet(path)
        print(f"[windows] {name}: {s.index.min().date()} .. {s.index.max().date()}")
        out[name] = s

    def gold():
        df = pd.read_csv(io.StringIO(_get(ASSET_MIRRORS["GOLD"])))
        idx = pd.to_datetime(df["Date"]) + pd.offsets.MonthEnd(0)
        return pd.to_numeric(df.set_axis(idx)["Price"], errors="coerce").dropna()

    cached("GOLD", gold)
    cached("WTI", lambda: _parse_two_col(_get(ASSET_MIRRORS["WTI"]), "WTI"))
    cached("DGS10", lambda: _parse_two_col(_get(ASSET_MIRRORS["DGS10"]), "DGS10"))

    def dxy():
        df = pd.read_csv(io.StringIO(_get(MIRRORS["US70_DAILY"])))
        df.columns = [c.strip("﻿") for c in df.columns]
        df["DATE"] = pd.to_datetime(df["DATE"])
        s = pd.to_numeric(df.set_index("DATE")["US_Dollar_Index"], errors="coerce")
        return s.sort_index().dropna()

    cached("DXY", dxy)
    return out


def _me(t: pd.Timestamp, months: int) -> pd.Timestamp:
    """t shifted by `months` and rolled to that month's end (avoids
    asof() slipping to the prior month when e.g. Nov-30 + 1m = Dec-30)."""
    return (t + pd.DateOffset(months=months)) + pd.offsets.MonthEnd(0)


def _fwd_ret(s: pd.Series, t: pd.Timestamp, months: int):
    t2 = _me(t, months)
    if t2 > s.index.max() or t < s.index.min():
        return np.nan
    return float(s.asof(t2) / s.asof(t) - 1) * 100


def asset_table(analogs: pd.DataFrame, ext, assets) -> pd.DataFrame:
    """Cross-asset performance in the 12 months after each analog window."""
    rows = []
    for t in analogs.index:
        d10_0, d10_1 = assets["DGS10"].asof(t), np.nan
        t2 = _me(t, 12)
        if t2 <= assets["DGS10"].index.max():
            d10_1 = assets["DGS10"].asof(t2)
        # approximate 10y Treasury 12m total return: carry - duration x dY
        if not np.isnan(d10_1):
            y0, y1 = d10_0 / 100, d10_1 / 100
            dur = (1 - (1 + y1) ** -10) / y1
            tr10 = round(100 * (y0 - dur * (y1 - y0)), 1)
        else:
            tr10 = np.nan
        d2 = ext["DGS2"]
        rows.append({
            "window_end": f"{t:%Y-%m}",
            "SPX_%": round(_fwd_ret(ext["SPX"], t, 12), 1),
            "IXIC_%": round(_fwd_ret(ext["IXIC"], t, 12), 1),
            "Gold_%": round(_fwd_ret(assets["GOLD"], t, 12), 1),
            "WTI_%": round(_fwd_ret(assets["WTI"], t, 12), 1),
            "DXY_%": round(_fwd_ret(assets["DXY"], t, 12), 1),
            "d2y_bp": round(100 * (d2.asof(_me(t, 12)) - d2.asof(t)))
            if _me(t, 12) <= d2.index.max() else np.nan,
            "d10y_bp": round(100 * (d10_1 - d10_0)) if not np.isnan(d10_1) else np.nan,
            "UST10y_TR_approx_%": tr10,
        })
    df = pd.DataFrame(rows)
    med = df.drop(columns="window_end").median(numeric_only=True).round(1)
    df.loc[len(df)] = ["median"] + [med.get(c, np.nan) for c in df.columns[1:]]
    return df


def monthly_grid(close: pd.Series, analogs: pd.DataFrame) -> pd.DataFrame:
    """Month-by-month % returns for the 12 months after each analog."""
    me = close.resample("ME").last()
    rows = {}
    for t in analogs.index:
        rets = []
        for m in range(1, 13):
            a = _me(t, m - 1)
            b = _me(t, m)
            rets.append(round(100 * (me.asof(b) / me.asof(a) - 1), 1)
                        if b <= me.index.max() and a >= me.index.min() else np.nan)
        rows[f"{t:%Y-%m}"] = rets + [round(_fwd_ret(close, t, 12), 1)]
    grid = pd.DataFrame(rows, index=[f"M+{m}" for m in range(1, 13)] + ["cum_12m"]).T
    grid.loc["median"] = grid.median()
    return grid.reset_index().rename(columns={"index": "window_end"})


def monthly_heatmap(grids: dict, fname: str):
    fig, axes = plt.subplots(len(grids), 1, figsize=(11, 4.2 * len(grids)))
    for ax, (label, grid) in zip(np.atleast_1d(axes), grids.items()):
        g = grid.set_index("window_end")[[f"M+{m}" for m in range(1, 13)]]
        data = g.values.astype(float)
        lim = np.nanmax(np.abs(data))
        im = ax.imshow(data, cmap="RdYlGn", vmin=-lim, vmax=lim, aspect="auto")
        ax.set_xticks(range(12), g.columns, fontsize=8)
        ax.set_yticks(range(len(g)), g.index, fontsize=8)
        for i in range(data.shape[0]):
            for j in range(12):
                if not np.isnan(data[i, j]):
                    ax.annotate(f"{data[i, j]:.1f}", (j, i), ha="center",
                                va="center", fontsize=7)
        ax.set_title(f"{label}: monthly % returns in the 12 months after "
                     "each analog window", fontsize=10)
        fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(OUT / fname, dpi=130)
    plt.close(fig)


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


def write_report(df, analogs, stale, now, last_close,
                 assets_df=None, grids=None, assets=None):
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

    if assets_df is not None:
        w("\n\n## Cross-asset performance in the 12 months after each analog\n")
        w("Yield moves in bp; `UST10y_TR_approx` is carry minus duration x "
          "yield change (approximation, not an index). n/a = the series "
          "ends before the 12-month mark"
          + (f" (DXY mirror ends {assets['DXY'].index.max():%Y-%m})."
             if assets is not None else "."))
        w("")
        w(assets_df.fillna("n/a").to_markdown(index=False))

    if grids is not None:
        for label, grid in grids.items():
            w(f"\n\n## Monthly {label} returns after each analog (%)\n")
            w(grid.fillna("n/a").to_markdown(index=False))
        w("\nSame data as a heatmap: `window_analog_monthly.png`.\n")

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
    assets = load_assets()
    assets_df = asset_table(analogs, ext, assets)
    grids = {"S&P 500": monthly_grid(ext["SPX"], analogs),
             "Nasdaq": monthly_grid(ext["IXIC"], analogs)}
    monthly_heatmap(grids, "window_analog_monthly.png")
    write_report(df, analogs, stale, now, ext["SPX"].index.max(),
                 assets_df, grids, assets)
    df.round(3).to_csv(OUT / "window_signals.csv")
    assets_df.to_csv(OUT / "window_analog_assets.csv", index=False)
    for label, grid in grids.items():
        grid.to_csv(OUT / f"window_analog_monthly_{label.replace('&', '').replace(' ', '').lower()}.csv",
                    index=False)
    print(f"[windows] {len(df)} windows {df.index.min():%Y-%m}..{now:%Y-%m}; "
          f"current pattern: {df.loc[now, 'pattern']}")
    print("[windows] top analogs:",
          ", ".join(f"{t:%Y-%m}" for t in analogs.sort_values('distance').index))


if __name__ == "__main__":
    main()
