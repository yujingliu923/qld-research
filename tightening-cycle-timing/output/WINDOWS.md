# Rolling 3-month signal windows: which past periods look like now?

_Generated 2026-06-10. Windows step monthly; each covers the 3 months ending at the date shown. Sample: 1954-07 to 2026-06 (864 windows); the final window is partial, ending at the last available close (2026-06-09). Yield features join in 1962 (DGS1 start); distance is RMS over available z-scored features._


## The current window

Window ending **2026-06** — pattern: **`HOLD | infl-flat | eq-up | high-vol`**

| feature        |   value |
|:---------------|--------:|
| eq_ret_3m      |   13.14 |
| eq_vol_3m      |   15.02 |
| eq_dd_12m      |   -2.93 |
| eq_mom_12m     |   19.04 |
| ff_chg_3m      |    0    |
| real_ff        |    0.81 |
| cpi_yoy        |    2.83 |
| cpi_yoy_chg_3m |    0    |
| y2_minus_ff    |    0.04 |
| y2_chg_3m      |    0    |

Stale inputs carried forward into the current window (mirror freshness): ff last observed 2026-02-28; cpi_yoy last observed 2026-01-31; y2 last observed 2026-03-31.


## Most similar past windows (top 10 distinct episodes)

| window_end   |   distance | pattern                             |   eq_ret_3m |   ff_chg_3m |   cpi_yoy |   y2_minus_ff |   fwd_6m_% |   fwd_12m_% |
|:-------------|-----------:|:------------------------------------|------------:|------------:|----------:|--------------:|-----------:|------------:|
| 1997-01      |       0.41 | HOLD | infl-flat | eq-up | mid-vol  |       11.47 |        0.01 |      3.04 |          0.69 |      21.39 |       24.69 |
| 1999-01      |       0.48 | CUT | infl-up | eq-up | high-vol    |       16.47 |       -0.44 |      1.67 |         -0.05 |       3.84 |        8.97 |
| 1999-12      |       0.46 | HOLD | infl-flat | eq-up | high-vol |       14.54 |        0.08 |      2.68 |          0.94 |      -1    |      -10.14 |
| 2007-05      |       0.48 | HOLD | infl-up | eq-up | mid-vol    |        8.8  |       -0.01 |      2.71 |         -0.33 |      -3.23 |       -8.51 |
| 2010-11      |       0.41 | HOLD | infl-flat | eq-up | mid-vol  |       12.51 |        0    |      1.08 |          0.26 |      13.95 |        5.63 |
| 2012-08      |       0.46 | HOLD | infl-flat | eq-up | mid-vol  |        7.35 |       -0.03 |      1.69 |          0.09 |       7.78 |       16.52 |
| 2019-03      |       0.34 | HOLD | infl-dn | eq-up | mid-vol    |       13.07 |        0.14 |      1.88 |         -0.14 |       5.02 |       -8.81 |
| 2020-12      |       0.35 | HOLD | infl-flat | eq-up | high-vol |       11.69 |        0    |      1.32 |          0.04 |      14.41 |       26.89 |
| 2024-02      |       0.48 | HOLD | infl-flat | eq-up | mid-vol  |       11.57 |        0    |      3.16 |         -0.69 |      10.83 |       16.84 |
| 2025-01      |       0.42 | CUT | infl-up | eq-up | high-vol    |        5.87 |       -0.5  |      2.99 |         -0.11 |       4.95 |       14.87 |

Forward S&P 500 returns after these analogs: median +11.9% over 12 months (range -10.1% to +26.9%).


## Pattern-code view

The current pattern `HOLD | infl-flat | eq-up | high-vol` occurred in 5 historical windows (0.6% of the sample).
 After those windows the S&P 500 was higher 12 months later in 60% of cases (median +6.4%).


Most frequent patterns over the full sample:

| pattern                           |   n |   med_fwd_12m |
|:----------------------------------|----:|--------------:|
| HOLD | infl-up | eq-up | mid-vol  |  50 |           8.9 |
| HOLD | infl-dn | eq-up | mid-vol  |  36 |          14.4 |
| HOLD | infl-dn | eq-up | low-vol  |  32 |           6.5 |
| HIKE | infl-up | eq-up | low-vol  |  31 |           5.8 |
| CUT | infl-dn | eq-up | mid-vol   |  29 |           7.7 |
| HOLD | infl-up | eq-up | low-vol  |  29 |           6.5 |
| HIKE | infl-up | eq-up | mid-vol  |  29 |           6.8 |
| CUT | infl-dn | eq-up | high-vol  |  26 |          16.8 |
| HIKE | infl-dn | eq-up | low-vol  |  25 |           9.9 |
| HIKE | infl-up | eq-dn | mid-vol  |  24 |          10.6 |
| HOLD | infl-dn | eq-up | high-vol |  23 |          14.4 |
| HOLD | infl-up | eq-dn | high-vol |  20 |          18.8 |


## Reading and limitations

- Similarity is measured on contemporaneous signals only — it knows nothing about valuations, positioning, fiscal policy or the *cause* of each configuration.
- The current window inherits the mirror staleness listed above; CPI in particular is carried forward, so the inflation features of 'now' are softer than the rest.
- Forward-return statistics over ~10 analogs (or one pattern cell) are anecdotes, not expectancies — same n<=7 spirit as the main study.
- Pre-1962 windows lack the two 2y-yield features; their distances are computed over the remaining 8 signals.