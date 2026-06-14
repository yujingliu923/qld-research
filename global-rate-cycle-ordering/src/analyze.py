"""Ordering and intervals of policy-rate hike cycles across central banks.

Tests a specific hypothesis about the sequence of monetary tightening:

  "When global liquidity is abundant and the economy overheats, inflation
   shows up in emerging markets first (volatile currencies). Japan and the
   euro area then hike *before* the US to attract capital fleeing EM risk,
   and the US hikes last, both to fight inflation and to keep the dollar
   stable."

We line up the first hike of each central bank within each global
tightening cycle and measure the gap (in months) relative to the Federal
Reserve. Dates are hand-curated from primary sources (central-bank press
releases; Fed dates cross-checked against the DFEDTAR/DFEDTARU target
series cached in ../../tightening-cycle-timing). See data/cycle_starts.csv.

Outputs: output/REPORT.md, output/intervals.csv, output/cycle_timeline.png
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "cycle_starts.csv"
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)

# Display order and colors per bank
BANK_ORDER = ["Brazil", "Russia", "Mexico", "Fed", "ECB", "BoJ"]
BANK_COLOR = {
    "Brazil": "#2ca02c", "Russia": "#8c564b", "Mexico": "#bcbd22",
    "Fed": "#d62728", "ECB": "#1f77b4", "BoJ": "#9467bd",
}
CYCLE_ORDER = ["1999 dot-com", "2004 housing", "2021 post-COVID"]


def months_between(a: pd.Timestamp, b: pd.Timestamp) -> float:
    """Signed months from a to b (30.44-day months), one decimal."""
    return round((b - a).days / 30.44, 1)


def load() -> pd.DataFrame:
    df = pd.read_csv(DATA, parse_dates=["first_hike"])
    df["cycle"] = pd.Categorical(df["cycle"], CYCLE_ORDER, ordered=True)
    return df.sort_values(["cycle", "first_hike"])


def intervals(df: pd.DataFrame) -> pd.DataFrame:
    """Gap of each bank's first hike vs. the Fed, within its cycle."""
    rows = []
    for cycle, g in df.groupby("cycle", observed=True):
        fed = g.loc[g["bank"] == "Fed", "first_hike"]
        fed_date = fed.iloc[0] if len(fed) else pd.NaT
        for _, r in g.iterrows():
            rows.append({
                "cycle": cycle,
                "bank": r["bank"],
                "region": r["region"],
                "first_hike": r["first_hike"].date(),
                "months_vs_Fed": months_between(fed_date, r["first_hike"])
                if pd.notna(fed_date) else None,
            })
    out = pd.DataFrame(rows)
    return out


def make_timeline(df: pd.DataFrame, fname: str):
    fig, ax = plt.subplots(figsize=(12, 5.5))
    ylabels = CYCLE_ORDER
    ypos = {c: i for i, c in enumerate(ylabels)}

    # label offsets (points, y) cycled for points that fall close together
    label_levels = [14, 26, -20, -32]
    for cycle, g in df.groupby("cycle", observed=True):
        y = ypos[cycle]
        lo, hi = g["first_hike"].min(), g["first_hike"].max()
        ax.plot([lo, hi], [y, y], color="lightgray", lw=2, zorder=1)
        g = g.sort_values("first_hike").reset_index(drop=True)
        prev_date = None
        lvl = 0
        for _, r in g.iterrows():
            # if this point is within ~150 days of the previous one, push its
            # label to the next stagger level; otherwise reset to the baseline
            if prev_date is not None and (r["first_hike"] - prev_date).days < 150:
                lvl += 1
            else:
                lvl = 0
            prev_date = r["first_hike"]
            ax.scatter(r["first_hike"], y, s=130, zorder=3,
                       color=BANK_COLOR.get(r["bank"], "gray"),
                       edgecolor="black", linewidth=0.6)
            dy = label_levels[lvl % len(label_levels)]
            ax.annotate(r["bank"], (r["first_hike"], y),
                        xytext=(0, dy), textcoords="offset points",
                        ha="center", fontsize=8.5,
                        color=BANK_COLOR.get(r["bank"], "gray"),
                        arrowprops=dict(arrowstyle="-", lw=0.5,
                                        color=BANK_COLOR.get(r["bank"], "gray"))
                        if abs(dy) > 16 else None)

    ax.set_yticks(range(len(ylabels)), ylabels)
    ax.set_ylim(-0.6, len(ylabels) - 0.4)
    ax.invert_yaxis()
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(axis="x", alpha=0.25)
    ax.set_title("First rate hike of each cycle: the Fed leads the ECB and "
                 "BoJ; EM leads in 2021\n(EM = green/brown/olive, Fed = red, "
                 "ECB = blue, BoJ = purple)", fontsize=11)
    ax.set_xlabel("date of first hike")
    fig.tight_layout()
    fig.savefig(OUT / fname, dpi=140)
    plt.close(fig)


def write_report(df: pd.DataFrame, iv: pd.DataFrame):
    L = []
    w = L.append
    w("# Who hikes first? Ordering and intervals of global rate cycles\n")
    w("**The hypothesis under test.** When global liquidity is abundant and "
      "the world economy overheats, inflation appears in emerging markets "
      "(EM) first because their currencies are volatile. Japan and the euro "
      "area then raise rates *before* the US to attract capital fleeing EM "
      "risk, and the US raises last — both to fight inflation and to keep the "
      "dollar stable. The question: is this sequence borne out by history, "
      "and how long are the intervals among the US, EU and Japan?\n")
    w("**Verdict in one line.** Half right. The *EM-first* leg is real "
      "(clearest in 2021, weaker in 2004). But the ordering of the majors "
      "is the **reverse** of the "
      "hypothesis: in every clean demand-driven cycle the **Fed hiked before "
      "the ECB and well before the Bank of Japan**, not after them. Japan is "
      "the structural laggard, not a leader. And the capital-flow mechanism "
      "runs the other way — because the dollar is the reserve/safe-haven "
      "currency, US tightening *pulls* capital toward the dollar, which is "
      "precisely why EM central banks hike pre-emptively to defend their "
      "currencies.\n")

    w("\n## The data\n")
    w("First-hike dates for each central bank in each modern global "
      "tightening cycle, hand-curated from primary sources (central-bank "
      "press releases; US dates cross-checked against the FRED "
      "DFEDTAR/DFEDTARU target series cached in the sibling "
      "`tightening-cycle-timing` project). `months_vs_Fed` is the gap "
      "between that bank's first hike and the Fed's, in months "
      "(negative = before the Fed, positive = after).\n")
    show = iv.copy()
    show["months_vs_Fed"] = show["months_vs_Fed"].map(
        lambda x: "" if x is None or pd.isna(x) else f"{x:+.1f}")
    w(show.to_markdown(index=False))

    w("\n## Reading the three cycles\n")
    w("**1999 (dot-com).** Fed first (Jun 1999). ECB followed ~4 months "
      "later (Nov 1999); the BoJ only ended its zero-rate policy ~13 months "
      "after the Fed (Aug 2000) — and reversed within months as the tech "
      "bust hit.")
    w("\n**2004 (housing boom).** The cleanest demand cycle among the "
      "majors, and the most Fed-led. Fed first (Jun 2004). The ECB did not "
      "move until Dec 2005 — **~17 months after** the Fed. The BoJ ended "
      "ZIRP in Jul 2006, **~24 months after** the Fed. EM was *not* clearly "
      "ahead here: Brazil resumed hiking in Sep 2004, essentially alongside "
      "the Fed (+2.5 months). So the EM-first leg is a weak-to-mixed signal "
      "in 2004 and only becomes pronounced in 2021.")
    w("\n**2021 (post-COVID inflation).** The textbook case for the EM-first "
      "leg: Brazil hiked in Mar 2021, Russia days later, Mexico by Jun 2021 "
      "— roughly **a year before** the Fed (Mar 2022). The ECB again "
      "followed the Fed by ~4 months (Jul 2022), and the BoJ only exited "
      "negative rates in Mar 2024 — **~24 months after** the Fed.")

    w("\n## The intervals (the answer to 'how long?')\n")
    w("Measuring each major against the Fed, across the cycles where all "
      "three moved in the same direction:\n")
    maj = iv[iv["bank"].isin(["ECB", "BoJ"])].dropna(subset=["months_vs_Fed"])
    summ = (maj.groupby("bank")["months_vs_Fed"]
            .agg(["min", "max", "mean"]).round(1).reset_index())
    summ.columns = ["bank", "min_months_after_Fed", "max_months_after_Fed",
                    "avg_months_after_Fed"]
    w(summ.to_markdown(index=False))
    w("\n- **EU (ECB) lags the US by roughly 4 to 17 months** (about a "
      "quarter in the fast 1999/2021 cycles, well over a year in 2004).")
    w("- **Japan (BoJ) lags the US by roughly 13 to 24 months**, when it "
      "participates at all.")
    w("- **EM leads the US by up to ~12 months** (Brazil was ~12 months "
      "ahead of the Fed in the 2021 cycle).")

    w("\n## Why the majors order this way (and the dollar mechanism)\n")
    w("- **Japan is a deflation story, not a liquidity-attraction story.** "
      "The BoJ held zero or negative rates almost continuously from 1999 to "
      "2024 because its problem was *too little* inflation. It is "
      "structurally last to hike, often by years, and sometimes skips a "
      "global cycle entirely (it went *negative* in 2016 while the Fed was "
      "hiking). It does not pre-empt the Fed to attract capital.")
    w("- **The ECB follows, and when it has led it has regretted it.** The "
      "one modern case of the ECB hiking before the Fed was **April 2011** "
      "(to 1.50%), while the Fed stayed at zero until Dec 2015. That hike is "
      "now a textbook policy error: the euro debt crisis forced the ECB to "
      "*reverse* it within months. So the lone EU-before-US episode actually "
      "undercuts the hypothesis — it was a mistake driven by a domestic "
      "inflation scare, not a capital-attraction strategy, and it failed.")
    w("- **The dollar mechanism is backwards in the hypothesis.** Capital "
      "does not need to be lured to the dollar by a pre-emptive ECB/BoJ "
      "hike; the dollar is the world's reserve and safe-haven currency, so "
      "when the Fed tightens (or risk rises), money flows *into* the dollar "
      "on its own (1994 'tequila', 2013 taper tantrum, 2015, 2018, 2022 "
      "dollar surges). That outflow pressure on EM currencies is exactly "
      "*why EM central banks hike early and aggressively* — defensively, to "
      "protect their currencies and curb imported inflation, often ahead of "
      "the Fed. So the true causal chain is closer to: global inflation "
      "impulse -> EM hikes defensively (anticipating Fed tightening + dollar "
      "strength) -> Fed hikes -> ECB follows -> BoJ last.")

    w("\n## What the hypothesis gets right vs. wrong\n")
    w("| Claim | Verdict |")
    w("|---|---|")
    w("| EM notices/acts on inflation first | **Mostly correct** — strong in "
      "2021 (Brazil ~12 months ahead of the Fed); mixed in 2004 (Brazil "
      "moved alongside the Fed). EM as a *group* tends to lead, but not in "
      "every cycle. |")
    w("| Japan and EU hike *before* the US | **Incorrect** — the Fed led the "
      "ECB by 4-17 months and the BoJ by 13-24 months in every clean cycle. |")
    w("| US hikes last among the majors | **Incorrect** — the US is "
      "typically the *first* of the three majors; Japan is last. |")
    w("| Pre-emptive EU/JP hikes pull capital from EM toward them | **Not "
      "supported** — capital flows to the *dollar* on Fed tightening; EM "
      "hikes are defensive responses to that, not the EU/JP magnet. |")

    w("\n## Caveats\n")
    w("- n = 3 clean cycles (plus the 2011 anomaly). This is case-study "
      "evidence, not a statistical law — treat the intervals as typical "
      "magnitudes, not precise constants.")
    w("- 'First hike' dates a cycle's start but ignores pace and terminal "
      "level; two banks can start close together yet diverge sharply (e.g. "
      "ECB 2011 reversed almost immediately).")
    w("- The EM leg is represented by a few large EMs (Brazil, Russia, "
      "Mexico); the broader EM universe is heterogeneous, but the lead-the-"
      "Fed pattern is well documented across the 2021 cycle.")
    w("- Dates are first-hike *decision/effective* dates from primary "
      "sources; small differences (announcement vs. settlement) do not "
      "change the ordering or the multi-month intervals.")

    (OUT / "REPORT.md").write_text("\n".join(L), encoding="utf-8")


def main():
    df = load()
    iv = intervals(df)
    iv.to_csv(OUT / "intervals.csv", index=False)
    make_timeline(df, "cycle_timeline.png")
    write_report(df, iv)
    print("[ordering] cycles:", ", ".join(CYCLE_ORDER))
    print(iv.to_string(index=False))


if __name__ == "__main__":
    main()
