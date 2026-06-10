"""Hard-coded Fed tightening-cycle event table.

Dates below are taken as given (documented policy history); they are
*verified* against the data in :func:`verify_events` and flagged when
inconsistent, but never invented or modified programmatically.

Milestone codes:
  M3 = policy signal / hawkish announcement (may have multiple candidates)
  M4 = first actual rate hike
  QT = balance-sheet runoff start (where applicable)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

T = pd.Timestamp


@dataclass
class Cycle:
    key: str
    label: str
    m4: pd.Timestamp
    # list of (date, short description); empty = no formal signal (pre-
    # announcement era)
    m3_candidates: list = field(default_factory=list)
    qt_start: pd.Timestamp | None = None
    notes: str = ""


CYCLES = [
    Cycle(
        key="1972-74",
        label="1972-74 (Burns)",
        m4=T("1973-01-01"),
        m3_candidates=[],  # no formal announcements in this era: M3 = N/A
        notes="M4 = month the funds rate's sustained rise begins (1973-01); "
              "FOMC did not announce decisions in this era, so M3 is N/A.",
    ),
    Cycle(
        key="1977-80",
        label="1977-80 (Volcker shock)",
        m4=T("1977-08-01"),
        m3_candidates=[(T("1979-10-06"), "Volcker Saturday announcement")],
        notes="M4 = 1977-08 funds-rate rise begins; the only formal hawkish "
              "communication is Volcker's 1979-10-06 Saturday announcement, "
              "which postdates M4 by ~26 months.",
    ),
    Cycle(
        key="1994",
        label="1994 (surprise hike)",
        m4=T("1994-02-04"),
        m3_candidates=[(T("1994-02-04"), "surprise hike (M3 ≈ M4)")],
        notes="The hike itself was the signal: M3 ≈ M4.",
    ),
    Cycle(
        key="1999",
        label="1999-2000",
        m4=T("1999-06-30"),
        m3_candidates=[(T("1999-05-18"), "FOMC adopts tightening bias (announced)")],
    ),
    Cycle(
        key="2004",
        label="2004-06",
        m4=T("2004-06-30"),
        m3_candidates=[(T("2004-01-28"), '"patient" language shift')],
    ),
    Cycle(
        key="2015-18",
        label="2015-18 (hikes + QT)",
        m4=T("2015-12-16"),
        m3_candidates=[
            (T("2013-05-22"), "Bernanke taper testimony"),
            (T("2013-12-18"), "taper announced"),
        ],
        qt_start=T("2017-10-01"),
    ),
    Cycle(
        key="2021-22",
        label="2021-22 (hikes + QT)",
        m4=T("2022-03-16"),
        m3_candidates=[
            (T("2021-11-03"), "taper announced"),
            (T("2021-11-30"), 'Powell retires "transitory"'),
        ],
        qt_start=T("2022-06-01"),
    ),
]


def _monthly_ff(series: dict) -> pd.Series:
    return series["FEDFUNDS"]


def verify_events(series: dict) -> list[str]:
    """Cross-check the hard-coded table against FEDFUNDS / WALCL.

    Checks (failures are reported, never auto-corrected):
      * M4: the average funds rate 12 months after M4 should exceed the
        rate in the M4 month by >= 50 bp (a hike cycle actually started).
      * M4: the funds rate should not already have risen > 75 bp over the
        6 months *before* M4 (else M4 is late / mis-dated).
      * QT: WALCL 6 months after QT start should be below its level at
        QT start.
    """
    ff = _monthly_ff(series).copy()
    ff.index = ff.index.to_period("M")
    walcl = series["WALCL"]
    flags = []
    for c in CYCLES:
        m = pd.Period(c.m4, "M")
        try:
            now, later = ff.loc[m], ff.loc[m + 12]
            if later - now < 0.50:
                flags.append(f"{c.key}: funds rate only {later - now:+.2f}pp in the "
                             f"12m after M4 ({c.m4.date()}) — check M4 date")
            before = ff.loc[m - 6]
            if now - before > 0.75:
                flags.append(f"{c.key}: funds rate already +{now - before:.2f}pp in the "
                             f"6m before M4 ({c.m4.date()}) — M4 may be late")
        except KeyError:
            flags.append(f"{c.key}: FEDFUNDS data missing around M4 {c.m4.date()}")
        if c.qt_start is not None:
            w = walcl[walcl.index >= c.qt_start]
            if len(w) == 0:
                flags.append(f"{c.key}: no WALCL data after QT start")
            else:
                start = w.iloc[0]
                six_mo = walcl[walcl.index >= c.qt_start + pd.DateOffset(months=6)]
                if len(six_mo) and six_mo.iloc[0] >= start:
                    flags.append(f"{c.key}: WALCL not lower 6m after QT start "
                                 f"({c.qt_start.date()}) — check QT date")
    return flags


if __name__ == "__main__":
    from data import load_all

    s = load_all()
    for c in CYCLES:
        m3 = "; ".join(f"{d.date()} ({lbl})" for d, lbl in c.m3_candidates) or "N/A"
        qt = c.qt_start.date() if c.qt_start is not None else "-"
        print(f"{c.key:8s} M4={c.m4.date()}  QT={qt}  M3={m3}")
    flags = verify_events(s)
    print("\nVerification:", "OK — no inconsistencies" if not flags else "")
    for f in flags:
        print("  FLAG:", f)
