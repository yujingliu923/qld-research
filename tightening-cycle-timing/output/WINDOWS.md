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


## Cross-asset performance in the 12 months after each analog

Yield moves in bp; `UST10y_TR_approx` is carry minus duration x yield change (approximation, not an index). n/a = the series ends before the 12-month mark (DXY mirror ends 2024-05).

| window_end   |   SPX_% |   IXIC_% |   Gold_% |   WTI_% | DXY_%   |   d2y_bp |   d10y_bp |   UST10y_TR_approx_% |
|:-------------|--------:|---------:|---------:|--------:|:--------|---------:|----------:|---------------------:|
| 1997-01      |    24.7 |     17.4 |    -18.6 |   -28.7 | 8.3     |    -62   |    -100   |                 14.1 |
| 1999-01      |     9   |     57.2 |     -1   |   115.8 | 9.4     |    203   |     202   |                 -9.7 |
| 1999-12      |   -10.1 |    -39.3 |     -4.1 |     3.7 | 7.5     |   -113   |    -133   |                 16.7 |
| 2007-05      |    -8.5 |     -3.1 |     33.2 |    98.9 | -11.4   |   -226   |     -84   |                 11.7 |
| 2010-11      |     5.6 |      4.9 |     26.9 |    19.3 | -3.5    |    -20   |     -73   |                  9.3 |
| 2012-08      |    16.5 |     17   |    -17.1 |    11.9 | 1.0     |     17   |     121   |                 -8.9 |
| 2019-03      |    -8.8 |     -0.4 |     22.4 |   -65.9 | 1.8     |   -204   |    -171   |                 18.9 |
| 2020-12      |    26.9 |     21.4 |     -3.7 |    55.8 | 6.4     |     60   |      59   |                 -4.5 |
| 2024-02      |    16.8 |     17.1 |     43.1 |   -11.7 | n/a     |    -65   |      -1   |                  4.3 |
| 2025-01      |    14.9 |     19.5 |     75.4 |   -11.4 | n/a     |    -70   |     -32   |                  7.1 |
| median       |    12   |     17   |     10.7 |     7.8 | 4.1     |    -63.5 |     -52.5 |                  8.2 |


## Monthly S&P 500 returns after each analog (%)

| window_end   |   M+1 |   M+2 |   M+3 |   M+4 |   M+5 |   M+6 |   M+7 |   M+8 |   M+9 |   M+10 |   M+11 |   M+12 |   cum_12m |
|:-------------|------:|------:|------:|------:|------:|------:|------:|------:|------:|-------:|-------:|-------:|----------:|
| 1997-01      |  0.6  |  -4.3 |   5.8 |   5.9 |  4.3  |  7.8  | -5.7  |  5.3  | -3.4  |   4.5  |   1.6  |   1    |     24.7  |
| 1999-01      | -3.2  |   3.9 |   3.8 |  -2.5 |  5.4  | -3.2  | -0.6  | -2.9  |  6.3  |   1.9  |   5.8  |  -5.1  |      9    |
| 1999-12      | -5.1  |  -2   |   9.7 |  -3.1 | -2.2  |  2.4  | -1.6  |  6.1  | -5.3  |  -0.5  |  -8    |   0.4  |    -10.1  |
| 2007-05      | -1.8  |  -3.2 |   1.3 |   3.6 |  1.5  | -4.4  | -0.9  | -6.1  | -3.5  |  -0.6  |   4.8  |   1.1  |     -8.5  |
| 2010-11      |  6.5  |   2.3 |   3.2 |  -0.1 |  2.8  | -1.4  | -1.8  | -2.1  | -5.7  |  -7.2  |  10.8  |  -0.5  |      5.6  |
| 2012-08      |  2.4  |  -2   |   0.3 |   0.7 |  5.3  |  0.9  |  3.1  |  2    |  3.7  |  -2.5  |   4.8  |  -2.9  |     16.5  |
| 2019-03      |  3.9  |  -6.6 |   6.9 |   1.3 | -1.8  |  1.7  |  2    |  3.4  |  2.9  |  -0.2  |  -8.4  | -12.5  |     -8.8  |
| 2020-12      | -1.1  |   2.6 |   4.2 |   5.2 |  0.5  |  2.2  |  2.3  |  2.9  | -4.8  |   6.9  |  -0.8  |   4.4  |     26.9  |
| 2024-02      |  3.1  |  -4.2 |   4.8 |   3.5 |  1.1  |  2.3  |  2    | -1    |  5.7  |  -2.5  |   2.7  |  -1.4  |     16.8  |
| 2025-01      | -1.4  |  -5.8 |  -0.8 |   6.2 |  5    |  2.2  |  1.9  |  3.5  |  2.3  |   0.1  |  -0.1  |   1.4  |     14.9  |
| median       | -0.25 |  -2.6 |   4   |   2.4 |  2.15 |  1.95 |  0.65 |  2.45 | -0.55 |  -0.35 |   2.15 |  -0.05 |     11.95 |


## Monthly Nasdaq returns after each analog (%)

| window_end   |   M+1 |   M+2 |   M+3 |    M+4 |    M+5 |   M+6 |   M+7 |   M+8 |    M+9 |   M+10 |   M+11 |   M+12 |   cum_12m |
|:-------------|------:|------:|------:|-------:|-------:|------:|------:|------:|-------:|-------:|-------:|-------:|----------:|
| 1997-01      |  -5.1 |  -6.7 |   3.2 |  11.1  |   3    |  10.5 |  -0.4 |  6.2  |  -5.5  |   0.4  |  -1.9  |    3.1 |     17.4  |
| 1999-01      |  -8.7 |   7.6 |   3.3 |  -2.8  |   8.7  |  -1.8 |   3.8 |  0.2  |   8    |  12.5  |  22    |   -3.2 |     57.2  |
| 1999-12      |  -3.2 |  19.2 |  -2.6 | -15.6  | -11.9  |  16.6 |  -5   | 11.7  | -12.7  |  -8.3  | -22.9  |   -4.9 |    -39.3  |
| 2007-05      |  -0   |  -2.2 |   2   |   4    |   5.8  |  -6.9 |  -0.3 | -9.9  |  -5    |   0.3  |   5.9  |    4.6 |     -3.1  |
| 2010-11      |   6.2 |   1.8 |   3   |  -0    |   3.3  |  -1.3 |  -2.2 | -0.6  |  -6.4  |  -6.4  |  11.1  |   -2.4 |      4.9  |
| 2012-08      |   1.6 |  -4.5 |   1.1 |   0.3  |   4.1  |   0.6 |   3.4 |  1.9  |   3.8  |  -1.5  |   6.6  |   -1   |     17    |
| 2019-03      |   4.7 |  -7.9 |   7.4 |   2.1  |  -2.6  |   0.5 |   3.7 |  4.5  |   3.5  |   2    |  -6.4  |  -10.1 |     -0.4  |
| 2020-12      |   1.4 |   0.9 |   0.4 |   5.4  |  -1.5  |   5.5 |   1.2 |  4    |  -5.3  |   7.3  |   0.3  |    0.7 |     21.4  |
| 2024-02      |   1.8 |  -4.4 |   6.9 |   6    |  -0.8  |   0.6 |   2.7 | -0.5  |   6.2  |   0.5  |   1.6  |   -4   |     17.1  |
| 2025-01      |  -4   |  -8.2 |   0.9 |   9.6  |   6.6  |   3.7 |   1.6 |  5.6  |   4.7  |  -1.5  |  -0.5  |    0.9 |     19.5  |
| median       |   0.7 |  -3.3 |   2.5 |   3.05 |   3.15 |   0.6 |   1.4 |  2.95 |  -0.75 |   0.35 |   0.95 |   -1.7 |     17.05 |

Same data as a heatmap: `window_analog_monthly.png`.


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