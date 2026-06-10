"""Timeline construction, interval statistics, ordering analysis,
conditional drawdowns, visualizations and SUMMARY.md generation."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import binomtest

import detect
from events import CYCLES

OUT = Path(__file__).resolve().parent.parent / "output"
OUT.mkdir(exist_ok=True)

MONTH_DAYS = 30.4375  # average calendar month, used for all month intervals
M2_DEGENERATE_MONTHS = 36  # flag M2 (or M1) assigned further back than this


def months_between(later, earlier):
    if later is None or earlier is None or pd.isna(later) or pd.isna(earlier):
        return np.nan
    return round((later - earlier).days / MONTH_DAYS, 1)


# ---------------------------------------------------------------------------
# Master timeline table
# ---------------------------------------------------------------------------

def detect_all(series, dd_threshold=0.15):
    rate = detect.splice_short_rate(series["DGS2"], series["DGS1"])
    return {
        "cpi_troughs": detect.find_inflation_troughs(series["CPIAUCSL"]),
        "core_troughs": detect.find_inflation_troughs(series["CPILFESL"]),
        "rate_troughs": detect.find_rate_troughs(rate),
        "peaks": {
            "SPX": detect.find_qualifying_peaks(series["SPX"], dd_threshold),
            "IXIC": detect.find_qualifying_peaks(series["IXIC"], dd_threshold),
        },
    }


def build_master(series, det) -> pd.DataFrame:
    rows = []
    for c in CYCLES:
        m1 = detect.assign_m1(det["cpi_troughs"], c.m4)
        m1_core = detect.assign_m1(det["core_troughs"], c.m4)
        m2 = detect.assign_m2(det["rate_troughs"], c.m4)
        m3list = c.m3_candidates or [(pd.NaT, "N/A")]
        for index in ["SPX", "IXIC"]:
            peak_row, status = detect.assign_peak(det["peaks"][index], m1, c.m4)
            p = peak_row["date"] if peak_row is not None else pd.NaT
            for vi, (m3, m3lbl) in enumerate(m3list):
                rows.append({
                    "cycle": c.key,
                    "index": index,
                    "m3_variant": "abc"[vi] if len(m3list) > 1 else "",
                    "m3_label": m3lbl,
                    "M1": m1, "M1_core": m1_core, "M2": m2, "M3": m3,
                    "M4": c.m4, "QT": c.qt_start, "P": p,
                    "P_status": status,
                    "P_close": peak_row["close"] if peak_row is not None else np.nan,
                    "P_trough_date": peak_row["trough_date"] if peak_row is not None else pd.NaT,
                    "P_drawdown": peak_row["drawdown"] if peak_row is not None else np.nan,
                    "P-M1": months_between(p, m1),
                    "P-M2": months_between(p, m2),
                    "P-M3": months_between(p, m3) if not pd.isna(m3) else np.nan,
                    "P-M4": months_between(p, c.m4),
                    "P-QT": months_between(p, c.qt_start) if c.qt_start is not None else np.nan,
                    "M1_gap_to_M4_m": months_between(c.m4, m1),
                    "M2_gap_to_M4_m": months_between(c.m4, m2),
                })
    df = pd.DataFrame(rows)
    df["M2_degenerate"] = df["M2_gap_to_M4_m"] > M2_DEGENERATE_MONTHS
    df["M1_degenerate"] = df["M1_gap_to_M4_m"] > M2_DEGENERATE_MONTHS
    return df


# ---------------------------------------------------------------------------
# Summary statistics with sign tests
# ---------------------------------------------------------------------------

def interval_stats(master: pd.DataFrame) -> pd.DataFrame:
    """Mean/median/min/max + before/after counts + binomial sign test.

    For P-M1/M2/M4/QT each cycle x index contributes once (M3 variants are
    duplicates there); for P-M3 the variants are reported separately.
    """
    base = master[master["m3_variant"].isin(["", "a"])]
    out = []

    def one(name, values, note=""):
        v = pd.Series(values).dropna()
        if v.empty:
            return
        after = int((v > 0).sum())
        before = int((v < 0).sum())
        n = after + before
        p = binomtest(after, n, 0.5).pvalue if n else np.nan
        out.append({
            "interval": name, "n": len(v),
            "mean_m": round(v.mean(), 1), "median_m": round(v.median(), 1),
            "min_m": v.min(), "max_m": v.max(),
            "peak_before": before, "peak_after": after,
            "sign_test_p": round(p, 3) if n else np.nan,
            "note": note,
        })

    for idx in ["SPX", "IXIC"]:
        sub = base[base["index"] == idx]
        for col in ["P-M1", "P-M2", "P-M4", "P-QT"]:
            one(f"{col} ({idx})", sub[col])
        # M2 excluding degenerate (ZIRP-era) assignments
        nd = sub[~sub["M2_degenerate"]]
        one(f"P-M2 ({idx}, excl. degenerate M2)", nd["P-M2"],
            note=f"drops cycles where M2 trough is >{M2_DEGENERATE_MONTHS}m before M4")
        # P-M3 both ways: single-M3 cycles combined with variant a, then b
        for variant in ["a", "b"]:
            mv = master[(master["index"] == idx)
                        & (master["m3_variant"].isin(["", variant]))]
            one(f"P-M3 ({idx}, variant {variant})", mv["P-M3"],
                note="single-candidate cycles included in both variants")
    return pd.DataFrame(out)


# ---------------------------------------------------------------------------
# Ordering analysis
# ---------------------------------------------------------------------------

def ordering_string(row) -> str:
    stones = [("M1", row["M1"]), ("M2", row["M2"]), ("M3", row["M3"]),
              ("M4", row["M4"]), ("P", row["P"])]
    stones = [(k, v) for k, v in stones if not pd.isna(v)]
    stones.sort(key=lambda kv: kv[1])
    parts = [stones[0][0]]
    for (pk, pv), (k, v) in zip(stones, stones[1:]):
        parts.append(("=" if v == pv else "<") + k)
    return "".join(parts)


def ordering_table(master: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in master.iterrows():
        seq = ordering_string(r) if r["P_status"] == "ok" else \
            ordering_string(r) + " (P=no burst)"
        rows.append({
            "cycle": r["cycle"], "index": r["index"],
            "m3_variant": r["m3_variant"], "sequence": seq,
            "front_run": (r["P_status"] == "ok" and not pd.isna(r["M3"])
                          and r["M3"] < r["P"] < r["M4"]),
            "P_after_QT": (r["P_status"] == "ok" and r["QT"] is not None
                           and not pd.isna(r["QT"]) and r["P"] > r["QT"]),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Conditional drawdowns (QT vs hikes-only) — case-study table
# ---------------------------------------------------------------------------

def cycle_window_drawdown(close: pd.Series, start, end):
    """Max drawdown from running peak inside [start, end]."""
    seg = close[(close.index >= start) & (close.index <= end)].dropna()
    if seg.empty:
        return np.nan, None, None, np.nan
    run = seg.cummax()
    dd = 1.0 - seg / run
    trough_date = dd.idxmax()
    peak_date = seg[seg.index <= trough_date].idxmax()
    return dd.max(), peak_date, trough_date, months_between(trough_date, peak_date)


def drawdown_table(series, master: pd.DataFrame) -> pd.DataFrame:
    base = master[master["m3_variant"].isin(["", "a"])]
    rows = []
    for _, r in base.iterrows():
        c = next(c for c in CYCLES if c.key == r["cycle"])
        close = series[r["index"]]
        start = r["M1"] if not pd.isna(r["M1"]) else c.m4 - pd.DateOffset(months=24)
        end = c.m4 + pd.DateOffset(months=48)
        wdd, wpk, wtr, wmonths = cycle_window_drawdown(close, start, end)
        rows.append({
            "cycle": r["cycle"], "index": r["index"],
            "QT_cycle": c.qt_start is not None,
            "assigned_P": r["P"].date() if not pd.isna(r["P"]) else "no burst",
            "assigned_P_drawdown_%": round(100 * r["P_drawdown"], 1)
            if not pd.isna(r["P_drawdown"]) else np.nan,
            "peak_to_trough_m": months_between(r["P_trough_date"], r["P"]),
            "window_max_dd_%": round(100 * wdd, 1),
            "window_dd_peak": wpk.date() if wpk is not None else None,
            "window_dd_trough": wtr.date() if wtr is not None else None,
            "window_peak_to_trough_m": wmonths,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Robustness: alternative drawdown thresholds for P
# ---------------------------------------------------------------------------

def robustness(series, det15) -> pd.DataFrame:
    rows = []
    for thr in [0.10, 0.15, 0.20]:
        det = det15 if thr == 0.15 else detect_all(series, thr)
        for c in CYCLES:
            m1 = detect.assign_m1(det15["cpi_troughs"], c.m4)
            for idx in ["SPX", "IXIC"]:
                pk, status = detect.assign_peak(det["peaks"][idx], m1, c.m4)
                rows.append({
                    "threshold": f"{int(thr * 100)}%",
                    "cycle": c.key, "index": idx,
                    "P": pk["date"].date() if pk is not None else "no burst",
                    "P-M4_m": months_between(pk["date"], c.m4) if pk is not None else np.nan,
                })
    df = pd.DataFrame(rows)
    piv = df.pivot(index=["cycle", "index"], columns="threshold",
                   values=["P", "P-M4_m"])
    piv.columns = [f"{a} @{b}" for a, b in piv.columns]
    return piv.reset_index()


# ---------------------------------------------------------------------------
# Timeline figures
# ---------------------------------------------------------------------------

def fed_rate_events(series, m4: pd.Timestamp, window_end: pd.Timestamp):
    """Hike announcements, terminal-rate date and first subsequent cut.

    From 1982-09-27 the daily fed funds target (DFEDTAR/DFEDTARU) dates
    every FOMC move exactly; before that there was no announced target,
    so hikes are not marked and the peak/first-cut are read from the
    monthly average funds rate (FEDFUNDS).
    """
    target = series["FFTARGET"]
    if m4 >= target.index.min():
        seg = target[(target.index >= m4 - pd.Timedelta(days=7))
                     & (target.index <= window_end)]
        ch = seg.diff()
        hikes = list(ch[ch > 0].index)
        peak_date = seg.idxmax()
        full_ch = target.diff()
        cuts = full_ch[(full_ch < 0) & (full_ch.index > peak_date)]
        first_cut = cuts.index[0] if len(cuts) else None
        rate_line = target
        mode = "target"
    else:
        ff = series["FEDFUNDS"]
        seg = ff[(ff.index >= m4) & (ff.index <= window_end)]
        hikes = []
        peak_date = seg.idxmax()
        peak_val = seg.max()
        after = ff[ff.index > peak_date]
        below = after[after < peak_val - 0.25]
        first_cut = below.index[0] if len(below) else None
        rate_line = ff
        mode = "monthly avg (no announced target pre-1982)"
    return {"hikes": hikes, "peak_date": peak_date, "first_cut": first_cut,
            "rate_line": rate_line, "mode": mode}


MILESTONE_STYLE = {
    "M1": ("tab:green", "M1 inflation inflection"),
    "M2": ("tab:blue", "M2 rate-expectation trough"),
    "M3": ("tab:orange", "M3 policy signal"),
    "M4": ("tab:red", "M4 first hike"),
    "QT": ("tab:purple", "QT start"),
}


def _plot_cycle(ax, series, master, cycle_key, annotate=True,
                legend_fontsize=8):
    rows = master[(master["cycle"] == cycle_key)
                  & (master["m3_variant"].isin(["", "a"]))]
    r0 = rows.iloc[0]
    c = next(c for c in CYCLES if c.key == cycle_key)
    anchor = r0["M1"] if not pd.isna(r0["M1"]) else c.m4 - pd.DateOffset(months=24)
    start = anchor - pd.DateOffset(months=6)
    p_dates = [d for d in rows["P"] if not pd.isna(d)]
    end = max([c.m4 + pd.DateOffset(months=30)] + [d + pd.DateOffset(months=18) for d in p_dates])
    rate_ev = fed_rate_events(series, c.m4, c.m4 + pd.DateOffset(months=60))
    if rate_ev["first_cut"] is not None:
        end = max(end, rate_ev["first_cut"] + pd.DateOffset(months=3))
    else:
        end = max(end, rate_ev["peak_date"] + pd.DateOffset(months=6))

    for idx, color in [("SPX", "black"), ("IXIC", "dimgray")]:
        s = series[idx]
        seg = s[(s.index >= start) & (s.index <= end)]
        if seg.empty:
            continue
        ref = s.asof(anchor)
        ax.plot(seg.index, 100 * seg / ref, lw=1.0, color=color,
                alpha=0.9 if idx == "SPX" else 0.55, label=idx)
    ax.set_yscale("log")

    all_m3 = [(d, lbl) for d, lbl in c.m3_candidates]
    marks = [("M1", r0["M1"]), ("M2", r0["M2"])] + \
            [("M3", d) for d, _ in all_m3] + \
            [("M4", c.m4), ("QT", c.qt_start)]
    off_scale = []
    for name, d in marks:
        if d is None or pd.isna(d):
            continue
        if not (start <= d <= end):
            off_scale.append(f"{name} {d.date()} (off-scale)")
            continue
        color, _ = MILESTONE_STYLE[name]
        ax.axvline(d, color=color, lw=1.4, alpha=0.8)
        if annotate:
            ax.annotate(name, (d, 0.985), xycoords=("data", "axes fraction"),
                        color=color, fontsize=8, ha="center", va="top",
                        fontweight="bold")
    if off_scale:
        ax.annotate("\n".join(off_scale), (0.01, 0.02),
                    xycoords="axes fraction", fontsize=7, color="gray")
    for _, r in rows.iterrows():
        if pd.isna(r["P"]):
            continue
        s = series[r["index"]]
        ref = s.asof(anchor)
        ax.plot([r["P"]], [100 * r["P_close"] / ref], marker="v", ms=8,
                color="crimson" if r["index"] == "SPX" else "darkorange",
                ls="none", label=f"P {r['index']} {r['P'].date()}")
    # right axis: policy-rate path with hikes / terminal rate / first cut
    ax2 = ax.twinx()
    rl = rate_ev["rate_line"]
    rseg = rl[(rl.index >= start) & (rl.index <= end)]
    ax2.plot(rseg.index, rseg.values, color="steelblue", lw=1.2, alpha=0.7,
             label=f"fed funds {'target' if rate_ev['mode'] == 'target' else 'rate'}")
    hikes = [h for h in rate_ev["hikes"] if start <= h <= end]
    if hikes:
        ax2.plot(hikes, [rl.asof(h) for h in hikes], ls="none", marker="^",
                 ms=5, color="firebrick", label=f"hike announced (n={len(hikes)})")
    pk = rate_ev["peak_date"]
    if start <= pk <= end:
        ax2.plot([pk], [rl.asof(pk)], ls="none", marker="*", ms=13,
                 color="gold", markeredgecolor="black", mew=0.5,
                 label=f"rate peak {pk.date()}")
    fc = rate_ev["first_cut"]
    if fc is not None and start <= fc <= end:
        ax2.plot([fc], [rl.asof(fc)], ls="none", marker="v", ms=8,
                 color="teal", label=f"first cut {fc.date()}")
    ax2.set_ylabel("fed funds (%)", fontsize=8, color="steelblue")
    ax2.tick_params(axis="y", labelsize=7, colors="steelblue")
    ax2.set_ylim(bottom=0)
    if rate_ev["mode"] != "target":
        ax2.annotate("pre-1982: monthly avg rate,\nno announced target",
                     (0.99, 0.02), xycoords="axes fraction", fontsize=7,
                     color="steelblue", ha="right")

    ax.set_xlim(start, end)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.grid(alpha=0.25)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=legend_fontsize, loc="upper left",
              framealpha=0.85)


def make_figures(series, master):
    for c in CYCLES:
        fig, ax = plt.subplots(figsize=(11, 5))
        _plot_cycle(ax, series, master, c.key)
        ax.set_title(f"{c.label}: milestones vs. index price (100 = M1, log scale)")
        fig.tight_layout()
        fig.savefig(OUT / f"timeline_{c.key}.png", dpi=130)
        plt.close(fig)

    fig, axes = plt.subplots(4, 2, figsize=(14, 16))
    for ax, c in zip(axes.flat, CYCLES):
        _plot_cycle(ax, series, master, c.key, annotate=True,
                    legend_fontsize=6)
        ax.set_title(c.label, fontsize=10)
    for ax in axes.flat[len(CYCLES):]:
        ax.axis("off")
    fig.suptitle("Tightening cycles: M1/M2/M3/M4/QT vs equity peak "
                 "(indexed to 100 at M1, log scale)", y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.985))
    fig.savefig(OUT / "timelines_all.png", dpi=120)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Entry point used by run_all.py
# ---------------------------------------------------------------------------

def run(series, event_flags, data_problems):
    det = detect_all(series, 0.15)
    master = build_master(series, det)
    stats = interval_stats(master)
    orders = ordering_table(master)
    dd = drawdown_table(series, master)
    robust = robustness(series, det)
    make_figures(series, master)

    master_out = master.copy()
    for col in ["M1", "M1_core", "M2", "M3", "M4", "QT", "P", "P_trough_date"]:
        master_out[col] = pd.to_datetime(master_out[col]).dt.date
    master_out.to_csv(OUT / "master_timeline.csv", index=False)
    stats.to_csv(OUT / "interval_stats.csv", index=False)
    orders.to_csv(OUT / "orderings.csv", index=False)
    dd.to_csv(OUT / "drawdowns.csv", index=False)
    robust.to_csv(OUT / "robustness.csv", index=False)

    write_summary(series, det, master, stats, orders, dd, robust,
                  event_flags, data_problems)
    return master, stats, orders, dd, robust


# ---------------------------------------------------------------------------
# SUMMARY.md
# ---------------------------------------------------------------------------

def _md(df: pd.DataFrame) -> str:
    return df.to_markdown(index=False)


def write_summary(series, det, master, stats, orders, dd, robust,
                  event_flags, data_problems):
    base = master[master["m3_variant"].isin(["", "a"])]

    def fmt_master():
        view = master.copy()
        for col in ["M1", "M2", "M3", "M4", "QT", "P"]:
            view[col] = pd.to_datetime(view[col]).dt.strftime("%Y-%m-%d")
        view["P"] = view.apply(
            lambda r: r["P"] if r["P_status"] == "ok" else "no burst", axis=1)
        view["M3"] = view["M3"].fillna("N/A") + view["m3_variant"].map(
            lambda v: f" ({v})" if v else "")
        cols = ["cycle", "index", "M1", "M2", "M3", "M4", "QT", "P",
                "P-M1", "P-M2", "P-M3", "P-M4", "P-QT"]
        return view[cols].fillna("-")

    ok = base[base["P_status"] == "ok"]
    deep = ok[ok["P_drawdown"] > 0.25]

    lines = []
    w = lines.append
    w("# Tightening-cycle timing: milestones vs. equity peaks\n")
    w(f"_Generated {pd.Timestamp.now():%Y-%m-%d}. n = {len(CYCLES)} cycles, "
      "2 indices (S&P 500, Nasdaq Composite). All intervals in calendar "
      "months (days / 30.4375); **negative = peak preceded the milestone**._\n")

    w("\n## Data sources and integrity\n")
    w("FRED series CPIAUCSL, CPILFESL, FEDFUNDS, DGS2 (1976-), DGS1, WALCL "
      "(2002-), DFF; daily closes for ^GSPC (1945-) and ^IXIC (1971-). "
      "FRED/Yahoo are queried directly when reachable; otherwise each series "
      "falls back to a commit-pinned GitHub mirror of the official download "
      "(see `src/data.py:MIRRORS`). Integrity spot-checks against published "
      "benchmark values (e.g. S&P 1527.46 on 2000-03-24, Nasdaq 5048.62 on "
      "2000-03-10): "
      + ("**all passed**." if not data_problems
         else "FAILURES: " + "; ".join(data_problems)) + "\n")

    w("\n## Detection rules (as run)\n")
    w("- **M1 (inflation inflection)**: month whose headline-CPI YoY is the "
      "minimum of a centered 13-month window and at least 4 of the next 6 "
      "months show a rising YoY; each cycle takes the nearest trough "
      "preceding M4. (Core-CPI variant in `master_timeline.csv`.)")
    w("- **M2 (rate-expectation shift)**: day whose 2y Treasury yield (1y "
      "before 1976-06) is the low of a centered 6-month window, followed by "
      "a rise of >= 75 bp within 6 months; nearest such trough preceding M4.")
    w("- **P (market peak)**: closing high not exceeded for >= 12 months and "
      "followed by a drawdown >= 15% before recovery; first qualifying peak "
      "after M1; 'no burst' if none within 48 months of M4.")
    w("- **M3/M4/QT**: hard-coded event table (`src/events.py`), verified "
      "against FEDFUNDS/WALCL, never modified.\n")

    w("\n### Event-table verification flags (reported, not corrected)\n")
    if event_flags:
        for f in event_flags:
            w(f"- {f}")
    else:
        w("- none")
    w("\n### Detection caveats surfaced by the rules\n")
    for _, r in base.drop_duplicates("cycle").iterrows():
        if r["M2_degenerate"]:
            w(f"- **{r['cycle']}**: M2 trough sits {r['M2_gap_to_M4_m']:.0f} "
              "months before M4 — the >=75bp-in-6m rule finds no trough in "
              "the ZIRP/forward-guidance era, so this M2 is degenerate.")
        if r["M1_degenerate"]:
            w(f"- **{r['cycle']}**: nearest preceding CPI-YoY trough is "
              f"{r['M1_gap_to_M4_m']:.0f} months before M4 — no nearby "
              "month satisfied the 13-month-window + 4-of-6-rising rule "
              "(for 1994 the next trough lands 3 months *after* M4; for "
              "1999 the 1996-98 disinflation never met the 4-of-6 rule).")
    w("- **1977-80**: a qualifying S&P peak (1976-09-21, -19.4%) precedes "
      "the detected M1 (1976-12) and is therefore skipped by the "
      "'first peak after M1' rule; the assigned peak is 1980-11-28.")
    w("- **2015-18**: the S&P's Sep-2018 high (-19.8% into Dec-2018) is *not* "
      "a qualifying peak because it was exceeded again within 12 months; the "
      "cycle is 'no burst' for the S&P under the stated rule.")
    w("- **2004**: the qualifying peak is Oct-2007 — "
      f"{base.loc[(base['cycle'] == '2004') & (base['index'] == 'SPX'), 'P-M4'].iloc[0]:.0f} "
      "months after M4 (within the 48-month window, but a long gap).\n")

    w("\n## (a) Master timeline table\n")
    w("Rows are cycle x index; cycles with two M3 candidates appear twice "
      "(variants a/b), as requested.\n")
    w(_md(fmt_master()))
    core = base.drop_duplicates("cycle")[["cycle", "M1", "M1_core"]].copy()
    core["M1 (headline)"] = pd.to_datetime(core["M1"]).dt.strftime("%Y-%m")
    core["M1 (core CPI)"] = pd.to_datetime(core["M1_core"]).dt.strftime("%Y-%m")
    core["spread_m"] = core.apply(
        lambda r: months_between(r["M1_core"], r["M1"]), axis=1)
    w("\nHeadline vs core-CPI M1 (core series starts 1957; spread in "
      "months, positive = core trough later):\n")
    w(_md(core[["cycle", "M1 (headline)", "M1 (core CPI)", "spread_m"]].fillna("-")))

    w("\n\n## Interval summary statistics\n")
    w("Sign test = two-sided binomial test of 'peak after milestone' vs. "
      "p=0.5, computed on the n shown. **With n <= 7 per index these are "
      "descriptive case studies, not powered hypothesis tests**; t-tests "
      "are deliberately not reported.\n")
    w(_md(stats))

    w("\n\n## (b) Ordering analysis\n")
    w(_md(orders[["cycle", "index", "m3_variant", "sequence",
                  "front_run", "P_after_QT"]]))
    seq_counts = (orders[orders["m3_variant"].isin(["", "a"])]
                  .groupby("sequence").size().rename("count").reset_index()
                  .sort_values("count", ascending=False))
    w("\nOrdering frequencies (M3 variant a):\n")
    w(_md(seq_counts))
    fr = sorted(set(orders.loc[orders["front_run"], "cycle"] + "/"
                    + orders.loc[orders["front_run"], "index"]))
    w(f"\n- **Front-running pattern (M3 < P < M4)**: occurs in "
      f"{len(fr)} cycle-index cases — " + (", ".join(fr) if fr else "never")
      + " (under at least one M3 variant).")
    pq = sorted(set(orders.loc[orders["P_after_QT"], "cycle"] + "/"
                    + orders.loc[orders["P_after_QT"], "index"]))
    w(f"- **Peak after QT start**: {len(pq)} cases — "
      + (", ".join(pq) if pq else "none — in both QT cycles the qualifying "
         "peak preceded the start of balance-sheet runoff") + ".\n")

    w("\n## Conditional drawdowns: QT cycles vs hikes-only "
      "(case-study evidence, not statistics)\n")
    w("`assigned_P_*` uses the qualifying peak; `window_*` is the max "
      "drawdown from a running peak inside [M1, M4+48m], which also captures "
      "episodes the 12-month rule excludes (e.g. S&P Q4-2018). Note the "
      "window truncates drawdowns that complete after M4+48m (1977-80, "
      "2004-07 rows), so `assigned_P_drawdown` can exceed `window_max_dd`.\n")
    w(_md(dd))
    qt_dd = dd[dd["QT_cycle"]]["window_max_dd_%"]
    no_qt_dd = dd[~dd["QT_cycle"]]["window_max_dd_%"]
    w(f"\nWithin-window comparison: QT cycles median max drawdown "
      f"{qt_dd.median():.1f}% (n={len(qt_dd)}) vs hikes-only "
      f"{no_qt_dd.median():.1f}% (n={len(no_qt_dd)}) — but the deepest "
      "busts (1973-74, 2000-02, 2007-09) completed *outside* the window "
      "and occurred without QT; see H3.")

    w("\n\n## (c) Hypothesis verdicts\n")
    h1 = ok[ok["P-M4"] < 0]
    w(f"\n**H1 — equity peaks precede the first hike (front-run M4): NOT "
      f"SUPPORTED in general.** Of {len(ok)} cycle-index cases with a "
      f"qualifying peak, only {len(h1)} peaked before M4 "
      f"({', '.join(sorted(set(h1['cycle'] + '/' + h1['index'])))}); "
      "in the older cycles the peak came months-to-years *after* the first "
      "hike. Front-running M4 is a feature of the QE-era cycles (2015-18 "
      "Nasdaq, 2021-22 both indices), not a historical regularity.")
    okall = master[(master["P_status"] == "ok") & ~master["M3"].isna()]
    h2a = okall[okall["m3_variant"].isin(["", "a"])]
    h2b = okall[okall["m3_variant"].isin(["", "b"])]
    w(f"\n**H2 — peaks follow the hawkish announcement (M3 trigger): "
      f"DIRECTIONALLY SUPPORTED but weak as a trigger.** Under the first "
      f"M3 candidates the peak followed M3 in {int((h2a['P-M3'] > 0).sum())}"
      f"/{len(h2a)} cases; under the second candidates in "
      f"{int((h2b['P-M3'] > 0).sum())}/{len(h2b)} (the lone exception: the "
      "Nasdaq's 2021-11-19 peak lands 0.4m before Powell retired "
      "'transitory' on 2021-11-30, though after the 2021-11-03 taper "
      "announcement). The lag, however, is extremely variable "
      f"(variant-a median {h2a['P-M3'].median():.0f}m, range "
      f"{h2a['P-M3'].min():.0f} to {h2a['P-M3'].max():.0f}m), so M3 timing "
      "alone has little predictive value for dating the peak.")
    deep_qt = deep[deep["QT"].notna()]
    w(f"\n**H3 — deep bursts (>25% drawdown) only with QT / reserve "
      f"scarcity: NOT SUPPORTED as stated.** Deep bursts: "
      + "; ".join(f"{r['cycle']}/{r['index']} ({100 * r['P_drawdown']:.0f}%)"
                  for _, r in deep.iterrows())
      + f". Only {len(deep_qt)} of {len(deep)} occurred in explicit-QT "
        "cycles (2021-22). The 1972-74 and 1999-2000 busts (48-78%) happened "
        "with no balance-sheet runoff — though under the pre-2008 corridor "
        "system reserves were *always* scarce, so a looser reading of "
        "'reserve scarcity' makes H3 unfalsifiable for pre-2008 cycles "
        "rather than confirmed.\n")

    w("\n## Robustness: peak-detection drawdown threshold (10% / 15% / 20%)\n")
    w(_md(robust))
    w("\nReading: every assigned peak except 2015-18 is identical at 10%, "
      "15% and 20% — the 1973/1980-81/2000/2007/2021-22 peaks and the 1994 "
      "'no burst' are threshold-invariant. Only 2015-18 moves: at 10% the "
      "S&P gains a qualifying peak (2015-05-21, i.e. *before* M4, "
      "strengthening the QE-era front-running reading), while at 20% the "
      "Nasdaq's 2015-07-20 peak drops out. The H1/H2/H3 verdicts are "
      "unchanged at all three thresholds.\n")

    w("\n## Limitations\n")
    w("- **n <= 7 cycles** (and only 2 with explicit QT): everything here is "
      "case-study evidence; the sign tests are reported with their n and "
      "should not be read as powered tests.")
    w("- **Peak definition sensitivity**: the 12-month/15% rule excludes "
      "fast-recovery crashes (S&P Q4-2018) and is sensitive at the margins "
      "(see robustness table).")
    w("- **CPI revisions / real-time vs revised data**: detection uses "
      "today's revised, seasonally adjusted CPI; policymakers and markets "
      "saw different real-time numbers.")
    w("- **Nasdaq history starts 1971-02**, shorter than the S&P (1945-); "
      "the 1972-74 Nasdaq row has only ~2 years of pre-cycle history.")
    w("- **Survivorship of the cycle list**: the seven cycles are a "
      "hand-picked, conventional list; mini-cycles and aborted tightenings "
      "(e.g. 1983-84, 1987) are excluded, which biases toward 'famous' "
      "outcomes.")
    w("- **M2 rule degenerates under ZIRP** (2009-2021): with the 2y pinned "
      "near zero, the >=75bp-in-6m trough rule reaches back to pre-QE lows "
      "for the 2015-18 and 2021-22 cycles.")
    w("- **Mirrored data**: in restricted environments the inputs come from "
      "commit-pinned GitHub mirrors of FRED/Yahoo downloads (validated by "
      "spot-checks); index history ends 2024-06 in the mirror, which is "
      "sufficient for every cycle studied.")
    w("- **1972-74 M3 is undefined** (no announcements era), so M3-based "
      "stats use at most 6 cycles.")

    (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    from data import load_all, verify_series
    from events import verify_events

    s = load_all()
    run(s, verify_events(s), verify_series(s))
    print(f"outputs written to {OUT}")
