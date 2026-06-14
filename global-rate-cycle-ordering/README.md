# global-rate-cycle-ordering

Tests a hypothesis about the *sequence* of monetary tightening across the
world: that inflation shows up in emerging markets first, that Japan and
the euro area then hike **before** the US to attract capital fleeing EM
currency risk, and that the US hikes last to fight inflation and steady
the dollar.

We line up the **first hike** of each central bank within each global
tightening cycle and measure the gap (in months) relative to the Federal
Reserve.

## Finding

- **EM-first: mostly true.** Emerging markets tend to hike first — clearest
  in the 2021 cycle, where Brazil moved ~12 months ahead of the Fed. Weaker
  in 2004.
- **"EU and Japan before the US": false.** In every clean demand-driven
  cycle the **Fed hiked first** among the majors — ahead of the ECB by
  4-17 months and ahead of the Bank of Japan by 13-24 months. Japan is the
  structural laggard (near-permanent zero/negative rates 1999-2024), not a
  leader.
- **The capital-flow mechanism is backwards.** The dollar is the reserve /
  safe-haven currency, so Fed tightening *pulls* capital toward the dollar
  on its own; EM central banks hike early and defensively *in response* to
  that pressure, rather than the ECB/BoJ acting as the magnet.

Read `output/REPORT.md` for the full write-up and the cycle-by-cycle table.

## Run

```bash
pip install pandas matplotlib tabulate
python src/analyze.py
```

## Structure

| Path | Contents |
|---|---|
| `data/cycle_starts.csv` | Hand-curated first-hike dates per bank per cycle, with primary-source notes |
| `src/analyze.py` | Computes intervals vs. the Fed, renders the timeline, writes the report |
| `output/REPORT.md` | Full write-up: hypothesis, data, intervals, mechanism, what's right/wrong |
| `output/intervals.csv` | First-hike date and months-vs-Fed for every bank/cycle |
| `output/cycle_timeline.png` | Timeline of first hikes, one row per cycle |

## Sources

First-hike dates are from central-bank press releases and contemporaneous
reporting; US dates are cross-checked against the FRED DFEDTAR/DFEDTARU
target series cached in the sibling `tightening-cycle-timing` project.
Key references: ECB key-rate history (ecb.europa.eu), Bank of Japan policy
decisions, Banco Central do Brasil (Copom), Banco de México, and the
Federal Reserve target series. n = 3 clean cycles plus the aborted ECB
2011 hike — treat as case-study evidence, not a statistical law.
