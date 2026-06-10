"""Algorithmic detection of M1 (inflation inflection), M2 (rate-expectation
shift) and P (equity market peak).

Detection rules (also restated in output/SUMMARY.md):

M1 — on YoY headline CPI (and separately core CPI): a local trough is a
     month whose YoY value is the minimum of a centered 13-month window
     (t-6 .. t+6) AND at least 4 of the next 6 months show a
     month-over-month *rise* in the YoY rate.  Each cycle is assigned
     the nearest trough preceding (<=) its M4 date.

M2 — on the 2-year Treasury yield (DGS2; DGS1 before 1976-06): a trough
     is a day whose yield is the low of a centered 6-month window
     (t-3mo .. t+3mo) AND the yield rises >= 75 bp at some point within
     the following 6 months.  Each cycle is assigned the nearest
     qualifying trough preceding its M4 date.

P  — on daily index closes: a qualifying peak is a closing high that
     (a) is not exceeded by any close in the following 12 months, and
     (b) is followed by a drawdown of at least `dd_threshold` (default
     15 %) before the close first exceeds the peak again (or to the end
     of the sample).  Each cycle gets the *first* qualifying peak after
     its M1 date; if none occurs within 48 months of M4 the cycle is
     recorded as "no burst".
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# M1: inflation inflection
# ---------------------------------------------------------------------------

def yoy(monthly_index: pd.Series) -> pd.Series:
    return (monthly_index / monthly_index.shift(12) - 1.0) * 100.0


def find_inflation_troughs(cpi_level: pd.Series) -> pd.DataFrame:
    """All local YoY troughs per the 13-month-window + 4-of-6-rising rule."""
    y = yoy(cpi_level).dropna()
    vals = y.values
    out = []
    for i in range(6, len(vals) - 6):
        window = vals[i - 6:i + 7]
        if vals[i] > window.min() + 1e-12:
            continue
        # tie-break: only the first month of a flat minimum qualifies
        if np.argmin(window) != 6:
            continue
        nxt = vals[i + 1:i + 7]
        prev = vals[i:i + 6]
        rises = int((nxt > prev).sum())
        if rises >= 4:
            out.append({"date": y.index[i], "yoy": vals[i], "rises_next6": rises})
    return pd.DataFrame(out)


def assign_m1(troughs: pd.DataFrame, m4: pd.Timestamp) -> pd.Timestamp | None:
    prior = troughs[troughs["date"] <= m4]
    if prior.empty:
        return None
    return prior["date"].iloc[-1]


# ---------------------------------------------------------------------------
# M2: bond-market expectation shift
# ---------------------------------------------------------------------------

def splice_short_rate(dgs2: pd.Series, dgs1: pd.Series) -> pd.Series:
    """DGS2 from its 1976-06 start, DGS1 before that."""
    start2 = dgs2.index.min()
    return pd.concat([dgs1[dgs1.index < start2], dgs2]).sort_index()


def find_rate_troughs(rate: pd.Series, rise_bp: float = 75.0) -> pd.DataFrame:
    """Troughs = low of centered 6-month window, then >= rise_bp within 6m."""
    r = rate.dropna()
    idx = r.index
    vals = r.values
    out = []
    half = pd.DateOffset(months=3)
    fwd = pd.DateOffset(months=6)
    # restrict to local minima of a 21-obs window first for speed
    cand = np.where(vals == pd.Series(vals).rolling(21, center=True, min_periods=1).min().values)[0]
    for i in cand:
        t = idx[i]
        window = r[(idx >= t - half) & (idx <= t + half)]
        if vals[i] > window.min() + 1e-12:
            continue
        if window.idxmin() != t:  # first day of a flat low wins
            continue
        future = r[(idx > t) & (idx <= t + fwd)]
        if len(future) and (future.max() - vals[i]) * 100.0 >= rise_bp:
            out.append({"date": t, "yield": vals[i],
                        "rise_6m_bp": (future.max() - vals[i]) * 100.0})
    return pd.DataFrame(out)


def assign_m2(troughs: pd.DataFrame, m4: pd.Timestamp) -> pd.Timestamp | None:
    prior = troughs[troughs["date"] <= m4]
    if prior.empty:
        return None
    return prior["date"].iloc[-1]


# ---------------------------------------------------------------------------
# P: equity market peak
# ---------------------------------------------------------------------------

def find_qualifying_peaks(close: pd.Series, dd_threshold: float = 0.15) -> pd.DataFrame:
    """All closing highs not exceeded for >= 12 months and followed by a
    drawdown of >= dd_threshold before recovery (or sample end)."""
    c = close.dropna()
    idx = c.index
    vals = c.values
    n = len(vals)
    out = []
    i = 0
    while i < n:
        t = idx[i]
        horizon = t + pd.DateOffset(months=12)
        j = np.searchsorted(idx, horizon, side="right")
        if j > i + 1 and vals[i + 1:j].size and vals[i + 1:j].max() > vals[i]:
            i += 1
            continue
        # not exceeded within 12 months; find first recovery above the peak
        later = vals[i + 1:]
        rec_rel = np.where(later > vals[i])[0]
        end = i + 1 + rec_rel[0] if rec_rel.size else n
        if end <= i + 1:
            i += 1
            continue
        seg = vals[i + 1:end + 1] if end < n else vals[i + 1:]
        if seg.size == 0:
            i += 1
            continue
        trough_rel = int(np.argmin(seg))
        dd = 1.0 - seg[trough_rel] / vals[i]
        if dd >= dd_threshold:
            out.append({
                "date": t,
                "close": vals[i],
                "trough_date": idx[i + 1 + trough_rel],
                "trough_close": seg[trough_rel],
                "drawdown": dd,
            })
            # skip past the trough: lower closes inside the same decline
            # would otherwise also qualify
            i = i + 1 + trough_rel
        i += 1
    return pd.DataFrame(out)


def assign_peak(peaks: pd.DataFrame, m1: pd.Timestamp | None, m4: pd.Timestamp,
                window_months: int = 48):
    """First qualifying peak after M1 (fallback: after M4 - 24m if M1 is
    missing); 'no burst' if it is not within `window_months` of M4."""
    start = m1 if m1 is not None else m4 - pd.DateOffset(months=24)
    cand = peaks[peaks["date"] >= start]
    if cand.empty:
        return None, "no burst"
    row = cand.iloc[0]
    limit = m4 + pd.DateOffset(months=window_months)
    if row["date"] > limit:
        return None, "no burst"
    return row, "ok"


if __name__ == "__main__":
    from data import load_all
    from events import CYCLES

    s = load_all()
    cpi_troughs = find_inflation_troughs(s["CPIAUCSL"])
    core_troughs = find_inflation_troughs(s["CPILFESL"])
    rate = splice_short_rate(s["DGS2"], s["DGS1"])
    rate_troughs = find_rate_troughs(rate)
    spx_peaks = find_qualifying_peaks(s["SPX"])
    ixic_peaks = find_qualifying_peaks(s["IXIC"])

    print("\nHeadline CPI YoY troughs:")
    print(cpi_troughs.to_string(index=False))
    print("\n2y (1y pre-1976) yield troughs:")
    print(rate_troughs.to_string(index=False))
    print("\nSPX qualifying peaks (15% dd):")
    print(spx_peaks.to_string(index=False))
    print("\nIXIC qualifying peaks (15% dd):")
    print(ixic_peaks.to_string(index=False))

    print("\nPer-cycle assignment:")
    for c in CYCLES:
        m1 = assign_m1(cpi_troughs, c.m4)
        m2 = assign_m2(rate_troughs, c.m4)
        p_spx, st1 = assign_peak(spx_peaks, m1, c.m4)
        p_ix, st2 = assign_peak(ixic_peaks, m1, c.m4)
        ps = p_spx["date"].date() if p_spx is not None else st1
        pi = p_ix["date"].date() if p_ix is not None else st2
        print(f"{c.key:8s} M1={m1.date() if m1 is not None else 'none'} "
              f"M2={m2.date() if m2 is not None else 'none'} "
              f"P(SPX)={ps}  P(IXIC)={pi}")
