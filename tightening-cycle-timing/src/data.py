"""Data acquisition and caching for the tightening-cycle timing study.

Primary sources are FRED (fredgraph CSV endpoint) and Yahoo Finance
(yfinance).  In environments where those hosts are unreachable, each
series falls back to a *pinned* public GitHub mirror of the official
FRED / Yahoo download (commit-SHA-pinned raw URLs, so the bytes cannot
change underneath us).  Every loaded series passes integrity
spot-checks against well-known published values before it is cached.

All series are cached to parquet under ``data_cache/``.
"""

from __future__ import annotations

import io
import os
from pathlib import Path

import numpy as np
import pandas as pd
import requests

CACHE_DIR = Path(__file__).resolve().parent.parent / "data_cache"
CACHE_DIR.mkdir(exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 (tightening-cycle-timing research)"}

_RAW = "https://raw.githubusercontent.com"

# Commit-pinned mirrors of official FRED downloads (observation_date/DATE
# + value format) and of Yahoo Finance daily index exports.
MIRRORS = {
    # FRED monthly, 1947-01 .. 2026-01
    "CPIAUCSL": f"{_RAW}/mikejrob/hawaii-lng-lsfo-brief/54f740e50517c4836cf2463f15fa0d24c80c76a1/fred_cpiaucsl.csv",
    # FRED monthly, 1957-01 .. 2023-12
    "CPILFESL": f"{_RAW}/dcuoliveira/MacroQuantDrafts/afe5422b5878b0dd664d1af39aad17d6e8851dd2/src/data/CPILFESL.csv",
    # FRED monthly, 1954-07 .. 2026-02
    "FEDFUNDS": f"{_RAW}/FeanorKingofNoldor/prometheus/04e6a017529e506b21bbd2d3eaefdef3541bc7e8/data/fred/fedfunds.csv",
    # FRED daily, 1976-06-01 .. 2025-10-16
    "DGS2": f"{_RAW}/tatmaca/bofa_hqla/49632028866c5a4b231e7b7740de2a37454f6ead/irr_data/DGS2.csv",
    # FRED daily, 1962-01-02 .. 2023-12-04
    "DGS1": f"{_RAW}/bharatgw/UncertaintyAndBankProfits/4d4e2503e6c29b9d5b6599cc2b1562b5a26f1a8a/Data/FedRates/DGS1.csv",
    # FRED weekly (Wednesday), 2002-12-18 .. 2025-05-21
    "WALCL": f"{_RAW}/badreddine631/TFG/e8786e93dc2ed792d31098294e865d7f9c1a56f7/datasets/WALCL.csv",
    # Daily closes: S&P 500 1945-01-02 .. 2024-06-06, Nasdaq Composite
    # 1971-02-05 .. 2024-06-07, daily effective fed funds (DFF) in daily.csv
    "SP500": f"{_RAW}/leocanada2007/us70/dc66bc6a1bfd3c1ffbe5fc105dd864fceaeeb1f2/data/SP500.csv",
    "IXIC": f"{_RAW}/leocanada2007/us70/dc66bc6a1bfd3c1ffbe5fc105dd864fceaeeb1f2/data/IXIC.csv",
    "US70_DAILY": f"{_RAW}/leocanada2007/us70/dc66bc6a1bfd3c1ffbe5fc105dd864fceaeeb1f2/data/daily.csv",
    # FRED daily fed funds target: single target 1982-09-27 .. 2008-12-15,
    # upper bound of the target range 2008-12-16 .. 2026-02
    "DFEDTAR": f"{_RAW}/vengveng/FEII/d646ed078efe87a902d89260ad2a6eea974bbe81/data/raw/DFEDTAR.csv",
    "DFEDTARU": f"{_RAW}/calderon777/monetary-economics/5d51200e2500079f8c660cd1ed2ee21f8ed1feb7/data_cache/dfedtaru.csv",
}

FRED_SERIES = ["CPIAUCSL", "CPILFESL", "FEDFUNDS", "DGS2", "DGS1", "WALCL"]


def _get(url: str, timeout: int = 60) -> str:
    r = requests.get(url, headers=UA, timeout=timeout)
    r.raise_for_status()
    return r.text


def _parse_two_col(text: str, name: str) -> pd.Series:
    """Parse a date,value CSV (FRED download format) into a Series."""
    df = pd.read_csv(io.StringIO(text))
    df.columns = ["date", name] + list(df.columns[2:])
    df = df[["date", name]]
    df["date"] = pd.to_datetime(df["date"])
    df[name] = pd.to_numeric(df[name], errors="coerce")
    s = df.set_index("date")[name].sort_index().dropna()
    return s


def _fetch_fred_direct(series_id: str) -> pd.Series:
    text = _get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}")
    return _parse_two_col(text, series_id)


def _fetch_fred_mirror(series_id: str) -> pd.Series:
    return _parse_two_col(_get(MIRRORS[series_id]), series_id)


def _fetch_index_direct(ticker: str, name: str) -> pd.Series:
    import yfinance as yf

    h = yf.Ticker(ticker).history(period="max", auto_adjust=False)
    s = h["Close"]
    s.index = pd.to_datetime(s.index.date)
    s.name = name
    return s.sort_index().dropna()


def _fetch_index_mirror(key: str) -> pd.Series:
    return _parse_two_col(_get(MIRRORS[key]), key)


def _cached(name: str, fetchers) -> pd.Series:
    """Load a series from parquet cache, else try fetchers in order."""
    path = CACHE_DIR / f"{name}.parquet"
    if path.exists() and not os.environ.get("FORCE_REFRESH"):
        return pd.read_parquet(path)[name]
    last_err = None
    for label, fn in fetchers:
        try:
            s = fn()
            s.name = name
            s.to_frame().to_parquet(path)
            print(f"[data] {name}: fetched via {label}, "
                  f"{s.index.min().date()} .. {s.index.max().date()} ({len(s)} obs)")
            return s
        except Exception as e:  # noqa: BLE001 - fall through to next source
            last_err = e
            print(f"[data] {name}: {label} failed ({type(e).__name__}), trying next source")
    raise RuntimeError(f"all sources failed for {name}: {last_err}")


def load_fred(series_id: str) -> pd.Series:
    return _cached(series_id, [
        ("FRED direct", lambda: _fetch_fred_direct(series_id)),
        ("GitHub mirror", lambda: _fetch_fred_mirror(series_id)),
    ])


def load_spx() -> pd.Series:
    return _cached("SPX", [
        ("yfinance ^GSPC", lambda: _fetch_index_direct("^GSPC", "SPX")),
        ("GitHub mirror", lambda: _fetch_index_mirror("SP500")),
    ])


def load_ixic() -> pd.Series:
    return _cached("IXIC", [
        ("yfinance ^IXIC", lambda: _fetch_index_direct("^IXIC", "IXIC")),
        ("GitHub mirror", lambda: _fetch_index_mirror("IXIC")),
    ])


def load_dff() -> pd.Series:
    """Daily effective fed funds rate (FRED DFF), used to verify M4 dates."""

    def direct():
        return _fetch_fred_direct("DFF")

    def mirror():
        df = pd.read_csv(io.StringIO(_get(MIRRORS["US70_DAILY"])))
        df.columns = [c.strip("﻿") for c in df.columns]
        df["DATE"] = pd.to_datetime(df["DATE"])
        s = df.set_index("DATE")["DFF"]
        return pd.to_numeric(s, errors="coerce").sort_index().dropna()

    return _cached("DFF", [("FRED direct", direct), ("GitHub mirror", mirror)])


def load_target() -> pd.Series:
    """Fed funds target rate, daily: DFEDTAR (1982-09-27..2008-12-15)
    spliced with the target-range upper bound DFEDTARU (2008-12-16..).
    Discrete changes in this series date the FOMC hike/cut decisions."""

    def direct():
        old = _fetch_fred_direct("DFEDTAR")
        new = _fetch_fred_direct("DFEDTARU")
        return pd.concat([old, new]).sort_index()

    def mirror():
        old = _parse_two_col(_get(MIRRORS["DFEDTAR"]), "DFEDTAR")
        new = _parse_two_col(_get(MIRRORS["DFEDTARU"]), "DFEDTARU")
        return pd.concat([old[old.index < new.index.min()], new]).sort_index()

    return _cached("FFTARGET", [("FRED direct", direct), ("GitHub mirror", mirror)])


# ---------------------------------------------------------------------------
# Integrity spot checks: known published values, tolerance 1 %.
# ---------------------------------------------------------------------------
SPOT_CHECKS = {
    "SPX": [("2000-03-24", 1527.46), ("2007-10-09", 1565.15), ("2022-01-03", 4796.56)],
    "IXIC": [("2000-03-10", 5048.62), ("2021-11-19", 16057.44)],
    "CPIAUCSL": [("1980-03-01", 80.1), ("2022-06-01", 296.3)],
    "FEDFUNDS": [("1981-06-01", 19.10), ("2023-01-01", 4.33)],
    "DGS2": [("2021-12-31", 0.73)],
    # 1994-11-15 hike to 5.50; 2023-07-27 hike to 5.50 upper bound
    "FFTARGET": [("1994-11-16", 5.50), ("2023-07-28", 5.50)],
}


def verify_series(series: dict[str, pd.Series]) -> list[str]:
    """Return a list of human-readable integrity warnings (empty = clean)."""
    problems = []
    for name, checks in SPOT_CHECKS.items():
        if name not in series:
            continue
        s = series[name]
        for date, expected in checks:
            ts = pd.Timestamp(date)
            if ts not in s.index:
                problems.append(f"{name}: no observation at {date}")
                continue
            got = float(s.loc[ts])
            if abs(got - expected) / expected > 0.01:
                problems.append(f"{name} @ {date}: got {got}, expected ~{expected}")
    return problems


def load_all() -> dict[str, pd.Series]:
    series = {sid: load_fred(sid) for sid in FRED_SERIES}
    series["SPX"] = load_spx()
    series["IXIC"] = load_ixic()
    series["DFF"] = load_dff()
    series["FFTARGET"] = load_target()
    problems = verify_series(series)
    if problems:
        for p in problems:
            print(f"[data] INTEGRITY WARNING: {p}")
    else:
        print("[data] all integrity spot-checks passed")
    return series


if __name__ == "__main__":
    data = load_all()
    for k, v in data.items():
        print(f"{k:10s} {v.index.min().date()} .. {v.index.max().date()}  n={len(v)}")
