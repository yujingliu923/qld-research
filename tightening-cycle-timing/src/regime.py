"""Current market-regime snapshot for the easing cycle that began with
the first rate cut after the 2022-23 hikes (first cut effective
2024-09-19, announced 2024-09-18).

Extends the index/yield history past the main study's mirrors by
splicing commit-pinned recent mirrors (cross-checked on overlapping
dates), extracts every cut from the fed funds target series, computes
regime metrics since the first cut, and compares the episode with the
start of every prior easing cycle in the study.

Outputs: output/REGIME.md, output/regime_current.png,
         output/regime_metrics.csv, output/first_cut_analogs.csv
"""

from __future__ import annotations

import io
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from data import CACHE_DIR, _get, _parse_two_col, load_all
from analysis import fed_rate_events, months_between, OUT
from events import CYCLES

_RAW = "https://raw.githubusercontent.com"

# Commit-pinned recent mirrors used to extend the main study's series
RECENT_MIRRORS = {
    # FRED SP500 daily closes 2016-02-12 .. 2026-02-11
    "SPX_FRED": f"{_RAW}/datasets/s-and-p-500/main/archive/fred_sp500.csv",
    # Yahoo ^IXIC daily 2020-01-02 .. 2026-01-09
    "IXIC_2020": f"{_RAW}/mahathirumalathi97-web/Cross-Market-Analysis/522191a337d35d25f7c3906869081b5e6fc2fbe9/IXIC.csv",
    # Yahoo ^GSPC / ^IXIC daily, rolling window 2025-06-11 .. 2026-06-09
    "GSPC_1Y": f"{_RAW}/timhun/daily-podcast-stk/ea21616cff02d89e325a2e7ec4586f2cf6ed2144/data/market/daily_GSPC.csv",
    "IXIC_1Y": f"{_RAW}/timhun/daily-podcast-stk/ea21616cff02d89e325a2e7ec4586f2cf6ed2144/data/market/daily_IXIC.csv",
    # FRED DGS2 mirror extending to 2026-03-17
    "DGS2_2026": f"{_RAW}/FeanorKingofNoldor/prometheus/04e6a017529e506b21bbd2d3eaefdef3541bc7e8/data/fred/dgs2.csv",
}


def _read_close(url: str, date_col: str, close_col: str) -> pd.Series:
    df = pd.read_csv(io.StringIO(_get(url)))
    df[date_col] = pd.to_datetime(df[date_col]).dt.tz_localize(None).dt.normalize()
    s = pd.to_numeric(df.set_index(date_col)[close_col], errors="coerce")
    return s.sort_index().dropna()


def _splice(parts: list[pd.Series], name: str, tol: float = 0.005) -> pd.Series:
    """Concatenate, later sources overriding earlier on overlap; verify
    overlapping observations agree within `tol` (guards against a mirror
    actually containing a different index)."""
    out = parts[0]
    for nxt in parts[1:]:
        overlap = out.index.intersection(nxt.index)
        if len(overlap):
            rel = (out.loc[overlap] - nxt.loc[overlap]).abs() / nxt.loc[overlap]
            bad = int((rel > tol).sum())
            # tolerate isolated bad ticks, reject systematic disagreement
            if bad > max(2, 0.005 * len(overlap)):
                raise ValueError(
                    f"{name}: splice mismatch on {bad}/{len(overlap)} "
                    f"overlap dates (worst {float(rel.max()):.2%})")
            if bad:
                print(f"[regime] {name}: {bad} isolated overlap outlier(s) "
                      f"ignored (worst {float(rel.max()):.2%})")
        out = pd.concat([out[~out.index.isin(nxt.index)], nxt]).sort_index()
    out.name = name
    return out


def load_extended(series: dict) -> dict:
    """SPX/IXIC/DGS2 extended to the freshest mirrored observation."""
    ext = {}
    for name, parts in {
        "SPX": [series["SPX"],
                lambda: _read_close(RECENT_MIRRORS["SPX_FRED"], "observation_date", "SP500"),
                lambda: _read_close(RECENT_MIRRORS["GSPC_1Y"], "date", "close")],
        "IXIC": [series["IXIC"],
                 lambda: _read_close(RECENT_MIRRORS["IXIC_2020"], "Date", "Close"),
                 lambda: _read_close(RECENT_MIRRORS["IXIC_1Y"], "date", "close")],
        "DGS2": [series["DGS2"],
                 lambda: _parse_two_col(_get(RECENT_MIRRORS["DGS2_2026"]), "DGS2")],
    }.items():
        path = CACHE_DIR / f"{name}_EXT.parquet"
        if path.exists():
            ext[name] = pd.read_parquet(path)[name]
            continue
        loaded = [parts[0]] + [fn() for fn in parts[1:]]
        s = _splice(loaded, name)
        s.to_frame().to_parquet(path)
        print(f"[regime] {name} extended to {s.index.max().date()} "
              f"(splice overlap checks passed)")
        ext[name] = s
    return ext


# ---------------------------------------------------------------------------
# Easing-cycle extraction and regime metrics
# ---------------------------------------------------------------------------

def easing_cycle(series: dict) -> dict:
    """Terminal rate of the last hiking cycle and every cut since."""
    target = series["FFTARGET"]
    last_cycle = CYCLES[-1]
    ev = fed_rate_events(series, last_cycle.m4,
                         last_cycle.m4 + pd.DateOffset(months=60))
    peak_date = ev["peak_date"]
    ch = target.diff()
    cuts = ch[(ch < 0) & (ch.index > peak_date)]
    cut_rows = [{"effective": d.date(), "change_bp": int(round(100 * v)),
                 "target_after_%": float(target.loc[d])}
                for d, v in cuts.items()]
    return {"peak_date": peak_date, "peak_rate": float(target.loc[peak_date]),
            "first_cut": cuts.index[0], "cuts": pd.DataFrame(cut_rows),
            "latest_rate": float(target.iloc[-1]),
            "rate_asof": target.index[-1]}


def regime_metrics(close: pd.Series, start: pd.Timestamp) -> dict:
    s = close[close.index >= start - pd.Timedelta(days=400)]
    post = close[close.index >= start]
    ath = post.cummax()
    dd = post / ath - 1.0
    ma200 = s.rolling(200).mean().reindex(post.index)
    ma50 = s.rolling(50).mean().reindex(post.index)
    last = post.index[-1]
    days = (last - start).days
    ret = post.iloc[-1] / post.iloc[0] - 1.0
    cur_dd = float(dd.iloc[-1])
    state = ("bull (at/near highs)" if cur_dd > -0.05 else
             "pullback" if cur_dd > -0.10 else
             "correction" if cur_dd > -0.20 else "bear")
    daily = post.pct_change().dropna()
    return {
        "as_of": last.date(),
        "return_since_first_cut_%": round(100 * ret, 1),
        "annualized_%": round(100 * ((1 + ret) ** (365.25 / days) - 1), 1),
        "max_drawdown_%": round(100 * float(dd.min()), 1),
        "max_dd_trough": dd.idxmin().date(),
        "current_dd_from_post-cut_high_%": round(100 * cur_dd, 1),
        "vol_63d_ann_%": round(100 * float(daily.tail(63).std() * np.sqrt(252)), 1),
        "vol_full_ann_%": round(100 * float(daily.std() * np.sqrt(252)), 1),
        "above_200dma": bool(post.iloc[-1] > ma200.iloc[-1]),
        "above_50dma": bool(post.iloc[-1] > ma50.iloc[-1]),
        "trend_state": state,
    }


def first_cut_analogs(spx: pd.Series, series: dict) -> pd.DataFrame:
    """SPX path after the first cut of each easing cycle in the study."""
    rows = []
    for c in CYCLES:
        ev = fed_rate_events(series, c.m4, c.m4 + pd.DateOffset(months=60))
        fc = ev["first_cut"]
        if fc is None:
            continue
        base = spx.asof(fc)
        path = spx[(spx.index >= fc)]

        def ret(months):
            t = fc + pd.DateOffset(months=months)
            return (round(100 * (spx.asof(t) / base - 1), 1)
                    if t <= spx.index.max() else np.nan)

        win = path[path.index <= fc + pd.DateOffset(months=12)]
        dd12 = (win / win.cummax() - 1).min() if len(win) else np.nan
        rows.append({
            "cycle": c.key, "first_cut": fc.date(),
            "SPX_+6m_%": ret(6), "SPX_+12m_%": ret(12),
            "max_dd_within_12m_%": round(100 * float(dd12), 1),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------

def make_figure(ext, series, cyc, metrics):
    fc = cyc["first_cut"]
    start = fc - pd.DateOffset(months=4)
    fig, (ax, axr) = plt.subplots(
        2, 1, figsize=(11, 7.5), sharex=True,
        gridspec_kw={"height_ratios": [2.2, 1]})
    for name, color in [("SPX", "black"), ("IXIC", "dimgray")]:
        s = ext[name]
        seg = s[s.index >= start]
        ax.plot(seg.index, 100 * seg / s.asof(fc), color=color, lw=1.1,
                alpha=0.9 if name == "SPX" else 0.55,
                label=f"{name} (last: {s.index.max().date()})")
    for d in cyc["cuts"]["effective"]:
        ax.axvline(pd.Timestamp(d), color="teal", lw=1.1, alpha=0.6)
    ax.axvline(fc, color="teal", lw=2.0)
    ax.annotate(f"first cut {fc.date()}", (fc, 0.97),
                xycoords=("data", "axes fraction"), color="teal",
                fontsize=8, ha="right", rotation=90, va="top")
    ax.set_yscale("log")
    ax.set_ylabel("price (100 = first cut)")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8, loc="upper left")
    ax.set_title("Easing cycle since the first cut: prices, cuts (teal), "
                 "policy rate, 2y and CPI")

    target = series["FFTARGET"]
    tseg = target[target.index >= start]
    axr.plot(tseg.index, tseg.values, color="steelblue", lw=1.4,
             label=f"fed funds target (to {target.index.max().date()})")
    d2 = ext["DGS2"]
    dseg = d2[d2.index >= start]
    axr.plot(dseg.index, dseg.values, color="darkorange", lw=1.0,
             label=f"2y Treasury (to {d2.index.max().date()})")
    cpi = series["CPIAUCSL"]
    yoy = (cpi / cpi.shift(12) - 1) * 100
    cseg = yoy[yoy.index >= start]
    axr.plot(cseg.index, cseg.values, color="seagreen", lw=1.2, marker=".",
             ms=3, label=f"CPI YoY (to {yoy.index.max().date()})")
    axr.set_ylabel("%")
    axr.grid(alpha=0.25)
    axr.legend(fontsize=8, loc="upper right")
    axr.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.tight_layout()
    fig.savefig(OUT / "regime_current.png", dpi=130)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def write_report(ext, series, cyc, met, analogs):
    fc = cyc["first_cut"]
    target = series["FFTARGET"]
    d2 = ext["DGS2"]
    cpi = series["CPIAUCSL"]
    yoy = ((cpi / cpi.shift(12) - 1) * 100).dropna()
    walcl = series["WALCL"]
    walcl_6m_ago = walcl.asof(walcl.index[-1] - pd.DateOffset(months=6))
    qt_running = walcl.iloc[-1] < walcl_6m_ago
    twoy_gap = float(d2.iloc[-1] - target.iloc[-1])

    spx_state = met["SPX"]["trend_state"]
    ixic_state = met["IXIC"]["trend_state"]
    uptrend = all(met[i]["above_200dma"] for i in ("SPX", "IXIC"))
    shallow = all(met[i]["current_dd_from_post-cut_high_%"] > -10
                  for i in ("SPX", "IXIC"))
    label = ("easing-cycle bull market"
             if "bull" in spx_state and "bull" in ixic_state
             else "easing-cycle bull market, currently in a pullback"
             if uptrend and shallow
             else "easing cycle with corrective/bear equities")

    L = []
    w = L.append
    w("# Current market regime since the first cut (easing cycle)\n")
    w(f"_Generated {pd.Timestamp.now():%Y-%m-%d}. Defined relative to the "
      f"2021-22 tightening cycle's terminal rate ({cyc['peak_rate']:.2f}% "
      f"reached {cyc['peak_date'].date()}); the easing cycle begins with "
      f"the first cut effective **{fc.date()}** (announced one day "
      "earlier). All metrics use the latest mirrored observation of each "
      "series — staleness varies and is stated per series._\n")

    w(f"\n## Verdict: {label}\n")
    el = months_between(ext['SPX'].index.max(), fc)
    w(f"- {el:.0f} months into the easing cycle, cumulative cuts of "
      f"{-cyc['cuts']['change_bp'].sum()} bp have brought the target from "
      f"{cyc['peak_rate']:.2f}% to {cyc['latest_rate']:.2f}% "
      f"(as of {cyc['rate_asof'].date()}).")
    w(f"- S&P 500: {met['SPX']['return_since_first_cut_%']}% since the first "
      f"cut ({met['SPX']['annualized_%']}% annualized), max drawdown "
      f"{met['SPX']['max_drawdown_%']}%, now {met['SPX']['current_dd_from_post-cut_high_%']}% "
      f"from its post-cut high — **{spx_state}**.")
    w(f"- Nasdaq: {met['IXIC']['return_since_first_cut_%']}% "
      f"({met['IXIC']['annualized_%']}% annualized), max drawdown "
      f"{met['IXIC']['max_drawdown_%']}%, now {met['IXIC']['current_dd_from_post-cut_high_%']}% "
      f"from its post-cut high — **{ixic_state}**.")
    w(f"- Rates: 2y Treasury {d2.iloc[-1]:.2f}% vs target "
      f"{target.iloc[-1]:.2f}% ({twoy_gap:+.2f} pp) — the bond market "
      + ("is still pricing further easing." if twoy_gap < -0.10 else
         "prices the Fed roughly on hold." if abs(twoy_gap) <= 0.10 else
         "is pricing tightening risk.")
      + f" (2y as of {d2.index.max().date()})")
    w(f"- Inflation: CPI YoY {yoy.iloc[-1]:.1f}% as of "
      f"{yoy.index[-1]:%Y-%m} vs {yoy.asof(fc):.1f}% at the first cut.")
    w(f"- Balance sheet: WALCL {'still shrinking' if qt_running else 'no longer shrinking'} "
      f"over the last 6 observed months (as of {walcl.index[-1].date()}).\n")

    w("\n## Cuts in this easing cycle (effective dates of target changes)\n")
    w(cyc["cuts"].to_markdown(index=False))

    w("\n\n## Regime metrics since the first cut\n")
    mdf = pd.DataFrame(met).T.reset_index().rename(columns={"index": "index_"})
    w(mdf.to_markdown(index=False))

    w("\n\n## Historical analogs: S&P 500 after the first cut of each "
      "easing cycle\n")
    w("The bifurcation is stark: first cuts that followed a burst bubble "
      "(2001, 2007) led to deep losses; 'mid-cycle'/soft-landing first cuts "
      "(1995, 2019, 2024) led to gains. Same caveat as the main study: "
      "n is tiny — case studies, not statistics.\n")
    w(analogs.to_markdown(index=False))

    w("\n\n## Data freshness / limitations\n")
    for name in ["SPX", "IXIC", "DGS2"]:
        w(f"- {name}: through {ext[name].index.max().date()} (spliced "
          "recent mirrors, overlap-checked; see `src/regime.py:RECENT_MIRRORS`).")
    w(f"- Fed funds target: through {target.index.max().date()}; "
      f"CPI: through {cpi.index.max():%Y-%m}; WALCL: through "
      f"{walcl.index[-1].date()} — any policy moves after these dates are "
      "not reflected.")
    w("- Regime labels use fixed drawdown bands (5/10/20%) and 50/200-day "
      "moving averages; they describe price action, not valuations or "
      "positioning.")
    w("- The SP500 daily series 2016-2026 is FRED's (close), spliced onto "
      "Yahoo history; sources agree on >2,000 overlapping dates, with "
      "isolated single-day bad ticks ignored (worst 0.79% on 2018-08-16).")

    (OUT / "REGIME.md").write_text("\n".join(L), encoding="utf-8")


def main():
    series = load_all()
    ext = load_extended(series)
    cyc = easing_cycle(series)
    met = {name: regime_metrics(ext[name], cyc["first_cut"])
           for name in ["SPX", "IXIC"]}
    analogs = first_cut_analogs(ext["SPX"], series)
    make_figure(ext, series, cyc, met)
    write_report(ext, series, cyc, met, analogs)
    pd.DataFrame(met).T.to_csv(OUT / "regime_metrics.csv")
    analogs.to_csv(OUT / "first_cut_analogs.csv", index=False)
    print(f"[regime] first cut {cyc['first_cut'].date()}, "
          f"{len(cyc['cuts'])} cuts to {cyc['latest_rate']:.2f}%")
    print(f"[regime] wrote {OUT / 'REGIME.md'}")


if __name__ == "__main__":
    main()
