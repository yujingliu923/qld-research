# Who hikes first? Ordering and intervals of global rate cycles

**The hypothesis under test.** When global liquidity is abundant and the world economy overheats, inflation appears in emerging markets (EM) first because their currencies are volatile. Japan and the euro area then raise rates *before* the US to attract capital fleeing EM risk, and the US raises last — both to fight inflation and to keep the dollar stable. The question: is this sequence borne out by history, and how long are the intervals among the US, EU and Japan?

**Verdict in one line.** Half right. The *EM-first* leg is real (clearest in 2021, weaker in 2004). But the ordering of the majors is the **reverse** of the hypothesis: in every clean demand-driven cycle the **Fed hiked before the ECB and well before the Bank of Japan**, not after them. Japan is the structural laggard, not a leader. And the capital-flow mechanism runs the other way — because the dollar is the reserve/safe-haven currency, US tightening *pulls* capital toward the dollar, which is precisely why EM central banks hike pre-emptively to defend their currencies.


## The data

First-hike dates for each central bank in each modern global tightening cycle, hand-curated from primary sources (central-bank press releases; US dates cross-checked against the FRED DFEDTAR/DFEDTARU target series cached in the sibling `tightening-cycle-timing` project). `months_vs_Fed` is the gap between that bank's first hike and the Fed's, in months (negative = before the Fed, positive = after).

| cycle           | bank   | region   | first_hike   |   months_vs_Fed |
|:----------------|:-------|:---------|:-------------|----------------:|
| 1999 dot-com    | Fed    | US       | 1999-06-30   |             0   |
| 1999 dot-com    | ECB    | EU       | 1999-11-04   |             4.2 |
| 1999 dot-com    | BoJ    | Japan    | 2000-08-11   |            13.4 |
| 2004 housing    | Fed    | US       | 2004-06-30   |             0   |
| 2004 housing    | Brazil | EM       | 2004-09-15   |             2.5 |
| 2004 housing    | ECB    | EU       | 2005-12-01   |            17   |
| 2004 housing    | BoJ    | Japan    | 2006-07-14   |            24.4 |
| 2021 post-COVID | Brazil | EM       | 2021-03-17   |           -12   |
| 2021 post-COVID | Russia | EM       | 2021-03-19   |           -11.9 |
| 2021 post-COVID | Mexico | EM       | 2021-06-24   |            -8.7 |
| 2021 post-COVID | Fed    | US       | 2022-03-17   |             0   |
| 2021 post-COVID | ECB    | EU       | 2022-07-21   |             4.1 |
| 2021 post-COVID | BoJ    | Japan    | 2024-03-19   |            24.1 |

## Reading the three cycles

**1999 (dot-com).** Fed first (Jun 1999). ECB followed ~4 months later (Nov 1999); the BoJ only ended its zero-rate policy ~13 months after the Fed (Aug 2000) — and reversed within months as the tech bust hit.

**2004 (housing boom).** The cleanest demand cycle among the majors, and the most Fed-led. Fed first (Jun 2004). The ECB did not move until Dec 2005 — **~17 months after** the Fed. The BoJ ended ZIRP in Jul 2006, **~24 months after** the Fed. EM was *not* clearly ahead here: Brazil resumed hiking in Sep 2004, essentially alongside the Fed (+2.5 months). So the EM-first leg is a weak-to-mixed signal in 2004 and only becomes pronounced in 2021.

**2021 (post-COVID inflation).** The textbook case for the EM-first leg: Brazil hiked in Mar 2021, Russia days later, Mexico by Jun 2021 — roughly **a year before** the Fed (Mar 2022). The ECB again followed the Fed by ~4 months (Jul 2022), and the BoJ only exited negative rates in Mar 2024 — **~24 months after** the Fed.

## The intervals (the answer to 'how long?')

Measuring each major against the Fed, across the cycles where all three moved in the same direction:

| bank   |   min_months_after_Fed |   max_months_after_Fed |   avg_months_after_Fed |
|:-------|-----------------------:|-----------------------:|-----------------------:|
| BoJ    |                   13.4 |                   24.4 |                   20.6 |
| ECB    |                    4.1 |                   17   |                    8.4 |

- **EU (ECB) lags the US by roughly 4 to 17 months** (about a quarter in the fast 1999/2021 cycles, well over a year in 2004).
- **Japan (BoJ) lags the US by roughly 13 to 24 months**, when it participates at all.
- **EM leads the US by up to ~12 months** (Brazil was ~12 months ahead of the Fed in the 2021 cycle).

## Why the majors order this way (and the dollar mechanism)

- **Japan is a deflation story, not a liquidity-attraction story.** The BoJ held zero or negative rates almost continuously from 1999 to 2024 because its problem was *too little* inflation. It is structurally last to hike, often by years, and sometimes skips a global cycle entirely (it went *negative* in 2016 while the Fed was hiking). It does not pre-empt the Fed to attract capital.
- **The ECB follows, and when it has led it has regretted it.** The one modern case of the ECB hiking before the Fed was **April 2011** (to 1.50%), while the Fed stayed at zero until Dec 2015. That hike is now a textbook policy error: the euro debt crisis forced the ECB to *reverse* it within months. So the lone EU-before-US episode actually undercuts the hypothesis — it was a mistake driven by a domestic inflation scare, not a capital-attraction strategy, and it failed.
- **The dollar mechanism is backwards in the hypothesis.** Capital does not need to be lured to the dollar by a pre-emptive ECB/BoJ hike; the dollar is the world's reserve and safe-haven currency, so when the Fed tightens (or risk rises), money flows *into* the dollar on its own (1994 'tequila', 2013 taper tantrum, 2015, 2018, 2022 dollar surges). That outflow pressure on EM currencies is exactly *why EM central banks hike early and aggressively* — defensively, to protect their currencies and curb imported inflation, often ahead of the Fed. So the true causal chain is closer to: global inflation impulse -> EM hikes defensively (anticipating Fed tightening + dollar strength) -> Fed hikes -> ECB follows -> BoJ last.

## What the hypothesis gets right vs. wrong

| Claim | Verdict |
|---|---|
| EM notices/acts on inflation first | **Mostly correct** — strong in 2021 (Brazil ~12 months ahead of the Fed); mixed in 2004 (Brazil moved alongside the Fed). EM as a *group* tends to lead, but not in every cycle. |
| Japan and EU hike *before* the US | **Incorrect** — the Fed led the ECB by 4-17 months and the BoJ by 13-24 months in every clean cycle. |
| US hikes last among the majors | **Incorrect** — the US is typically the *first* of the three majors; Japan is last. |
| Pre-emptive EU/JP hikes pull capital from EM toward them | **Not supported** — capital flows to the *dollar* on Fed tightening; EM hikes are defensive responses to that, not the EU/JP magnet. |

## Caveats

- n = 3 clean cycles (plus the 2011 anomaly). This is case-study evidence, not a statistical law — treat the intervals as typical magnitudes, not precise constants.
- 'First hike' dates a cycle's start but ignores pace and terminal level; two banks can start close together yet diverge sharply (e.g. ECB 2011 reversed almost immediately).
- The EM leg is represented by a few large EMs (Brazil, Russia, Mexico); the broader EM universe is heterogeneous, but the lead-the-Fed pattern is well documented across the 2021 cycle.
- Dates are first-hike *decision/effective* dates from primary sources; small differences (announcement vs. settlement) do not change the ordering or the multi-month intervals.