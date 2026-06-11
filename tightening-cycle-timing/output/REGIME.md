# Current market regime since the first cut (easing cycle)

_Generated 2026-06-10. Defined relative to the 2021-22 tightening cycle's terminal rate (5.50% reached 2023-07-27); the easing cycle begins with the first cut effective **2024-09-19** (announced one day earlier). All metrics use the latest mirrored observation of each series — staleness varies and is stated per series._


## Verdict: easing-cycle bull market, currently in a pullback

- 21 months into the easing cycle, cumulative cuts of 175 bp have brought the target from 5.50% to 3.75% (as of 2026-02-18).
- S&P 500: 29.3% since the first cut (16.1% annualized), max drawdown -18.9%, now -2.9% from its post-cut high — **bull (at/near highs)**.
- Nasdaq: 42.5% (22.9% annualized), max drawdown -24.3%, now -5.2% from its post-cut high — **pullback**.
- Rates: 2y Treasury 3.68% vs target 3.75% (-0.07 pp) — the bond market prices the Fed roughly on hold. (2y as of 2026-03-17)
- Inflation: CPI YoY 2.8% as of 2026-01 vs 2.4% at the first cut.
- Balance sheet: WALCL still shrinking over the last 6 observed months (as of 2025-05-21).


## Cuts in this easing cycle (effective dates of target changes)

| effective   |   change_bp |   target_after_% |
|:------------|------------:|-----------------:|
| 2024-09-19  |         -50 |             5    |
| 2024-11-08  |         -25 |             4.75 |
| 2024-12-19  |         -25 |             4.5  |
| 2025-09-18  |         -25 |             4.25 |
| 2025-10-30  |         -25 |             4    |
| 2025-12-11  |         -25 |             3.75 |


## Regime metrics since the first cut

| index_   | as_of      |   return_since_first_cut_% |   annualized_% |   max_drawdown_% | max_dd_trough   |   current_dd_from_post-cut_high_% |   vol_63d_ann_% |   vol_full_ann_% | above_200dma   | above_50dma   | trend_state          |
|:---------|:-----------|---------------------------:|---------------:|-----------------:|:----------------|----------------------------------:|----------------:|-----------------:|:---------------|:--------------|:---------------------|
| SPX      | 2026-06-09 |                       29.3 |           16.1 |            -18.9 | 2025-04-08      |                              -2.9 |            15   |             16.6 | True           | True          | bull (at/near highs) |
| IXIC     | 2026-06-09 |                       42.5 |           22.9 |            -24.3 | 2025-04-08      |                              -5.2 |            20.8 |             21.9 | True           | True          | pullback             |


## Historical analogs: S&P 500 after the first cut of each easing cycle

The bifurcation is stark: first cuts that followed a burst bubble (2001, 2007) led to deep losses; 'mid-cycle'/soft-landing first cuts (1995, 2019, 2024) led to gains. Same caveat as the main study: n is tiny — case studies, not statistics.

| cycle   | first_cut   |   SPX_+6m_% |   SPX_+12m_% |   max_dd_within_12m_% |
|:--------|:------------|------------:|-------------:|----------------------:|
| 1972-74 | 1974-08-01  |        -2.2 |         11.7 |                 -24.6 |
| 1977-80 | 1981-08-01  |       -10   |        -18.2 |                 -20   |
| 1994    | 1995-07-06  |        11.3 |         18.7 |                  -4.6 |
| 1999    | 2001-01-03  |        -8.4 |        -13.5 |                 -29.7 |
| 2004    | 2007-09-18  |       -12.4 |        -20.6 |                 -26.1 |
| 2015-18 | 2019-08-01  |         9.2 |         10.8 |                 -33.9 |
| 2021-22 | 2024-09-19  |        -0.7 |         16.6 |                 -18.9 |


## Data freshness / limitations

- SPX: through 2026-06-09 (spliced recent mirrors, overlap-checked; see `src/regime.py:RECENT_MIRRORS`).
- IXIC: through 2026-06-09 (spliced recent mirrors, overlap-checked; see `src/regime.py:RECENT_MIRRORS`).
- DGS2: through 2026-03-17 (spliced recent mirrors, overlap-checked; see `src/regime.py:RECENT_MIRRORS`).
- Fed funds target: through 2026-02-18; CPI: through 2026-01; WALCL: through 2025-05-21 — any policy moves after these dates are not reflected.
- Regime labels use fixed drawdown bands (5/10/20%) and 50/200-day moving averages; they describe price action, not valuations or positioning.
- The SP500 daily series 2016-2026 is FRED's (close), spliced onto Yahoo history; sources agree on >2,000 overlapping dates, with isolated single-day bad ticks ignored (worst 0.79% on 2018-08-16).