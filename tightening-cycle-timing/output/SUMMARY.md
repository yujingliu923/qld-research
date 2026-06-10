# Tightening-cycle timing: milestones vs. equity peaks

_Generated 2026-06-10. n = 7 cycles, 2 indices (S&P 500, Nasdaq Composite). All intervals in calendar months (days / 30.4375); **negative = peak preceded the milestone**._


## Data sources and integrity

FRED series CPIAUCSL, CPILFESL, FEDFUNDS, DGS2 (1976-), DGS1, WALCL (2002-), DFF; daily closes for ^GSPC (1945-) and ^IXIC (1971-). FRED/Yahoo are queried directly when reachable; otherwise each series falls back to a commit-pinned GitHub mirror of the official download (see `src/data.py:MIRRORS`). Integrity spot-checks against published benchmark values (e.g. S&P 1527.46 on 2000-03-24, Nasdaq 5048.62 on 2000-03-10): **all passed**.


## Detection rules (as run)

- **M1 (inflation inflection)**: month whose headline-CPI YoY is the minimum of a centered 13-month window and at least 4 of the next 6 months show a rising YoY; each cycle takes the nearest trough preceding M4. (Core-CPI variant in `master_timeline.csv`.)
- **M2 (rate-expectation shift)**: day whose 2y Treasury yield (1y before 1976-06) is the low of a centered 6-month window, followed by a rise of >= 75 bp within 6 months; nearest such trough preceding M4.
- **P (market peak)**: closing high not exceeded for >= 12 months and followed by a drawdown >= 15% before recovery; first qualifying peak after M1; 'no burst' if none within 48 months of M4.
- **M3/M4/QT**: hard-coded event table (`src/events.py`), verified against FEDFUNDS/WALCL, never modified.


### Event-table verification flags (reported, not corrected)

- 1972-74: funds rate already +1.39pp in the 6m before M4 (1973-01-01) — M4 may be late
- 1977-80: funds rate already +1.22pp in the 6m before M4 (1977-08-01) — M4 may be late
- 2015-18: funds rate only +0.30pp in the 12m after M4 (2015-12-16) — check M4 date

### Detection caveats surfaced by the rules

- **1994**: nearest preceding CPI-YoY trough is 45 months before M4 — no nearby month satisfied the 13-month-window + 4-of-6-rising rule (for 1994 the next trough lands 3 months *after* M4; for 1999 the 1996-98 disinflation never met the 4-of-6 rule).
- **1999**: nearest preceding CPI-YoY trough is 62 months before M4 — no nearby month satisfied the 13-month-window + 4-of-6-rising rule (for 1994 the next trough lands 3 months *after* M4; for 1999 the 1996-98 disinflation never met the 4-of-6 rule).
- **2015-18**: M2 trough sits 84 months before M4 — the >=75bp-in-6m rule finds no trough in the ZIRP/forward-guidance era, so this M2 is degenerate.
- **2021-22**: M2 trough sits 54 months before M4 — the >=75bp-in-6m rule finds no trough in the ZIRP/forward-guidance era, so this M2 is degenerate.
- **1977-80**: a qualifying S&P peak (1976-09-21, -19.4%) precedes the detected M1 (1976-12) and is therefore skipped by the 'first peak after M1' rule; the assigned peak is 1980-11-28.
- **2015-18**: the S&P's Sep-2018 high (-19.8% into Dec-2018) is *not* a qualifying peak because it was exceeded again within 12 months; the cycle is 'no burst' for the S&P under the stated rule.
- **2004**: the qualifying peak is Oct-2007 — 39 months after M4 (within the 48-month window, but a long gap).


## (a) Master timeline table

Rows are cycle x index; cycles with two M3 candidates appear twice (variants a/b), as requested.

| cycle   | index   | M1         | M2         | M3             | M4         | QT         | P          | P-M1   | P-M2   | P-M3   | P-M4   | P-QT   |
|:--------|:--------|:-----------|:-----------|:---------------|:-----------|:-----------|:-----------|:-------|:-------|:-------|:-------|:-------|
| 1972-74 | SPX     | 1972-08-01 | 1972-01-14 | N/A            | 1973-01-01 | -          | 1973-01-11 | 5.4    | 11.9   | -      | 0.3    | -      |
| 1972-74 | IXIC    | 1972-08-01 | 1972-01-14 | N/A            | 1973-01-01 | -          | 1973-01-11 | 5.4    | 11.9   | -      | 0.3    | -      |
| 1977-80 | SPX     | 1976-12-01 | 1977-04-14 | 1979-10-06     | 1977-08-01 | -          | 1980-11-28 | 47.9   | 43.5   | 13.8   | 39.9   | -      |
| 1977-80 | IXIC    | 1976-12-01 | 1977-04-14 | 1979-10-06     | 1977-08-01 | -          | 1981-05-29 | 53.9   | 49.5   | 19.7   | 45.9   | -      |
| 1994    | SPX     | 1990-05-01 | 1993-09-07 | 1994-02-04     | 1994-02-04 | -          | no burst   | -      | -      | -      | -      | -      |
| 1994    | IXIC    | 1990-05-01 | 1993-09-07 | 1994-02-04     | 1994-02-04 | -          | no burst   | -      | -      | -      | -      | -      |
| 1999    | SPX     | 1994-05-01 | 1998-10-16 | 1999-05-18     | 1999-06-30 | -          | 2000-03-24 | 70.8   | 17.2   | 10.2   | 8.8    | -      |
| 1999    | IXIC    | 1994-05-01 | 1998-10-16 | 1999-05-18     | 1999-06-30 | -          | 2000-03-10 | 70.3   | 16.8   | 9.8    | 8.3    | -      |
| 2004    | SPX     | 2004-02-01 | 2004-03-24 | 2004-01-28     | 2004-06-30 | -          | 2007-10-09 | 44.2   | 42.5   | 44.4   | 39.3   | -      |
| 2004    | IXIC    | 2004-02-01 | 2004-03-24 | 2004-01-28     | 2004-06-30 | -          | 2007-10-31 | 44.9   | 43.2   | 45.1   | 40.0   | -      |
| 2015-18 | SPX     | 2015-01-01 | 2008-12-16 | 2013-05-22 (a) | 2015-12-16 | 2017-10-01 | no burst   | -      | -      | -      | -      | -      |
| 2015-18 | SPX     | 2015-01-01 | 2008-12-16 | 2013-12-18 (b) | 2015-12-16 | 2017-10-01 | no burst   | -      | -      | -      | -      | -      |
| 2015-18 | IXIC    | 2015-01-01 | 2008-12-16 | 2013-05-22 (a) | 2015-12-16 | 2017-10-01 | 2015-07-20 | 6.6    | 79.1   | 25.9   | -4.9   | -26.4  |
| 2015-18 | IXIC    | 2015-01-01 | 2008-12-16 | 2013-12-18 (b) | 2015-12-16 | 2017-10-01 | 2015-07-20 | 6.6    | 79.1   | 19.0   | -4.9   | -26.4  |
| 2021-22 | SPX     | 2020-05-01 | 2017-09-07 | 2021-11-03 (a) | 2022-03-16 | 2022-06-01 | 2022-01-03 | 20.1   | 51.9   | 2.0    | -2.4   | -4.9   |
| 2021-22 | SPX     | 2020-05-01 | 2017-09-07 | 2021-11-30 (b) | 2022-03-16 | 2022-06-01 | 2022-01-03 | 20.1   | 51.9   | 1.1    | -2.4   | -4.9   |
| 2021-22 | IXIC    | 2020-05-01 | 2017-09-07 | 2021-11-03 (a) | 2022-03-16 | 2022-06-01 | 2021-11-19 | 18.6   | 50.4   | 0.5    | -3.8   | -6.4   |
| 2021-22 | IXIC    | 2020-05-01 | 2017-09-07 | 2021-11-30 (b) | 2022-03-16 | 2022-06-01 | 2021-11-19 | 18.6   | 50.4   | -0.4   | -3.8   | -6.4   |

Headline vs core-CPI M1 (core series starts 1957; spread in months, positive = core trough later):

| cycle   | M1 (headline)   | M1 (core CPI)   |   spread_m |
|:--------|:----------------|:----------------|-----------:|
| 1972-74 | 1972-08         | 1969-11         |      -33   |
| 1977-80 | 1976-12         | 1969-11         |      -85   |
| 1994    | 1990-05         | 1989-09         |       -8   |
| 1999    | 1994-05         | 1989-09         |      -56   |
| 2004    | 2004-02         | 2003-12         |       -2   |
| 2015-18 | 2015-01         | 2014-12         |       -1   |
| 2021-22 | 2020-05         | 2021-02         |        9.1 |


## Interval summary statistics

Sign test = two-sided binomial test of 'peak after milestone' vs. p=0.5, computed on the n shown. **With n <= 7 per index these are descriptive case studies, not powered hypothesis tests**; t-tests are deliberately not reported.

| interval                         |   n |   mean_m |   median_m |   min_m |   max_m |   peak_before |   peak_after |   sign_test_p | note                                              |
|:---------------------------------|----:|---------:|-----------:|--------:|--------:|--------------:|-------------:|--------------:|:--------------------------------------------------|
| P-M1 (SPX)                       |   5 |     37.7 |       44.2 |     5.4 |    70.8 |             0 |            5 |         0.062 |                                                   |
| P-M2 (SPX)                       |   5 |     33.4 |       42.5 |    11.9 |    51.9 |             0 |            5 |         0.062 |                                                   |
| P-M4 (SPX)                       |   5 |     17.2 |        8.8 |    -2.4 |    39.9 |             1 |            4 |         0.375 |                                                   |
| P-QT (SPX)                       |   1 |     -4.9 |       -4.9 |    -4.9 |    -4.9 |             1 |            0 |         1     |                                                   |
| P-M2 (SPX, excl. degenerate M2)  |   4 |     28.8 |       29.8 |    11.9 |    43.5 |             0 |            4 |         0.125 | drops cycles where M2 trough is >36m before M4    |
| P-M3 (SPX, variant a)            |   4 |     17.6 |       12   |     2   |    44.4 |             0 |            4 |         0.125 | single-candidate cycles included in both variants |
| P-M3 (SPX, variant b)            |   4 |     17.4 |       12   |     1.1 |    44.4 |             0 |            4 |         0.125 | single-candidate cycles included in both variants |
| P-M1 (IXIC)                      |   6 |     33.3 |       31.8 |     5.4 |    70.3 |             0 |            6 |         0.031 |                                                   |
| P-M2 (IXIC)                      |   6 |     41.8 |       46.4 |    11.9 |    79.1 |             0 |            6 |         0.031 |                                                   |
| P-M4 (IXIC)                      |   6 |     14.3 |        4.3 |    -4.9 |    45.9 |             2 |            4 |         0.688 |                                                   |
| P-QT (IXIC)                      |   2 |    -16.4 |      -16.4 |   -26.4 |    -6.4 |             2 |            0 |         0.5   |                                                   |
| P-M2 (IXIC, excl. degenerate M2) |   4 |     30.4 |       30   |    11.9 |    49.5 |             0 |            4 |         0.125 | drops cycles where M2 trough is >36m before M4    |
| P-M3 (IXIC, variant a)           |   5 |     20.2 |       19.7 |     0.5 |    45.1 |             0 |            5 |         0.062 | single-candidate cycles included in both variants |
| P-M3 (IXIC, variant b)           |   5 |     18.6 |       19   |    -0.4 |    45.1 |             1 |            4 |         0.375 | single-candidate cycles included in both variants |


## (b) Ordering analysis

| cycle   | index   | m3_variant   | sequence                 | front_run   | P_after_QT   |
|:--------|:--------|:-------------|:-------------------------|:------------|:-------------|
| 1972-74 | SPX     |              | M2<M1<M4<P               | False       | False        |
| 1972-74 | IXIC    |              | M2<M1<M4<P               | False       | False        |
| 1977-80 | SPX     |              | M1<M2<M4<M3<P            | False       | False        |
| 1977-80 | IXIC    |              | M1<M2<M4<M3<P            | False       | False        |
| 1994    | SPX     |              | M1<M2<M3=M4 (P=no burst) | False       | False        |
| 1994    | IXIC    |              | M1<M2<M3=M4 (P=no burst) | False       | False        |
| 1999    | SPX     |              | M1<M2<M3<M4<P            | False       | False        |
| 1999    | IXIC    |              | M1<M2<M3<M4<P            | False       | False        |
| 2004    | SPX     |              | M3<M1<M2<M4<P            | False       | False        |
| 2004    | IXIC    |              | M3<M1<M2<M4<P            | False       | False        |
| 2015-18 | SPX     | a            | M2<M3<M1<M4 (P=no burst) | False       | False        |
| 2015-18 | SPX     | b            | M2<M3<M1<M4 (P=no burst) | False       | False        |
| 2015-18 | IXIC    | a            | M2<M3<M1<P<M4            | True        | False        |
| 2015-18 | IXIC    | b            | M2<M3<M1<P<M4            | True        | False        |
| 2021-22 | SPX     | a            | M2<M1<M3<P<M4            | True        | False        |
| 2021-22 | SPX     | b            | M2<M1<M3<P<M4            | True        | False        |
| 2021-22 | IXIC    | a            | M2<M1<M3<P<M4            | True        | False        |
| 2021-22 | IXIC    | b            | M2<M1<P<M3<M4            | False       | False        |

Ordering frequencies (M3 variant a):

| sequence                 |   count |
|:-------------------------|--------:|
| M1<M2<M3<M4<P            |       2 |
| M1<M2<M3=M4 (P=no burst) |       2 |
| M1<M2<M4<M3<P            |       2 |
| M2<M1<M3<P<M4            |       2 |
| M2<M1<M4<P               |       2 |
| M3<M1<M2<M4<P            |       2 |
| M2<M3<M1<M4 (P=no burst) |       1 |
| M2<M3<M1<P<M4            |       1 |

- **Front-running pattern (M3 < P < M4)**: occurs in 3 cycle-index cases — 2015-18/IXIC, 2021-22/IXIC, 2021-22/SPX (under at least one M3 variant).
- **Peak after QT start**: 0 cases — none — in both QT cycles the qualifying peak preceded the start of balance-sheet runoff.


## Conditional drawdowns: QT cycles vs hikes-only (case-study evidence, not statistics)

`assigned_P_*` uses the qualifying peak; `window_*` is the max drawdown from a running peak inside [M1, M4+48m], which also captures episodes the 12-month rule excludes (e.g. S&P Q4-2018). Note the window truncates drawdowns that complete after M4+48m (1977-80, 2004-07 rows), so `assigned_P_drawdown` can exceed `window_max_dd`.

| cycle   | index   | QT_cycle   | assigned_P   |   assigned_P_drawdown_% |   peak_to_trough_m |   window_max_dd_% | window_dd_peak   | window_dd_trough   |   window_peak_to_trough_m |
|:--------|:--------|:-----------|:-------------|------------------------:|-------------------:|------------------:|:-----------------|:-------------------|--------------------------:|
| 1972-74 | SPX     | False      | 1973-01-11   |                    48.2 |               20.7 |              48.2 | 1973-01-11       | 1974-10-03         |                      20.7 |
| 1972-74 | IXIC    | False      | 1973-01-11   |                    59.9 |               20.7 |              59.9 | 1973-01-11       | 1974-10-03         |                      20.7 |
| 1977-80 | SPX     | False      | 1980-11-28   |                    27.1 |               20.4 |              19.1 | 1976-12-31       | 1978-03-06         |                      14.1 |
| 1977-80 | IXIC    | False      | 1981-05-29   |                    28.8 |               14.5 |              24.9 | 1980-02-08       | 1980-03-27         |                       1.6 |
| 1994    | SPX     | False      | no burst     |                   nan   |              nan   |              19.9 | 1990-07-16       | 1990-10-11         |                       2.9 |
| 1994    | IXIC    | False      | no burst     |                   nan   |              nan   |              30.7 | 1990-07-16       | 1990-10-16         |                       3   |
| 1999    | SPX     | False      | 2000-03-24   |                    49.1 |               30.5 |              49.1 | 2000-03-24       | 2002-10-09         |                      30.5 |
| 1999    | IXIC    | False      | 2000-03-10   |                    77.9 |               31   |              77.9 | 2000-03-10       | 2002-10-09         |                      31   |
| 2004    | SPX     | False      | 2007-10-09   |                    56.8 |               17   |              18.6 | 2007-10-09       | 2008-03-10         |                       5   |
| 2004    | IXIC    | False      | 2007-10-31   |                    55.6 |               16.3 |              24.1 | 2007-10-31       | 2008-03-10         |                       4.3 |
| 2015-18 | SPX     | True       | no burst     |                   nan   |              nan   |              19.8 | 2018-09-20       | 2018-12-24         |                       3.1 |
| 2015-18 | IXIC    | True       | 2015-07-20   |                    18.2 |                6.8 |              23.6 | 2018-08-29       | 2018-12-24         |                       3.8 |
| 2021-22 | SPX     | True       | 2022-01-03   |                    25.4 |                9.3 |              25.4 | 2022-01-03       | 2022-10-12         |                       9.3 |
| 2021-22 | IXIC    | True       | 2021-11-19   |                    36.4 |               13.3 |              36.4 | 2021-11-19       | 2022-12-28         |                      13.3 |

Within-window comparison: QT cycles median max drawdown 24.5% (n=4) vs hikes-only 27.8% (n=10) — but the deepest busts (1973-74, 2000-02, 2007-09) completed *outside* the window and occurred without QT; see H3.


## (c) Hypothesis verdicts


**H1 — equity peaks precede the first hike (front-run M4): NOT SUPPORTED in general.** Of 11 cycle-index cases with a qualifying peak, only 3 peaked before M4 (2015-18/IXIC, 2021-22/IXIC, 2021-22/SPX); in the older cycles the peak came months-to-years *after* the first hike. Front-running M4 is a feature of the QE-era cycles (2015-18 Nasdaq, 2021-22 both indices), not a historical regularity.

**H2 — peaks follow the hawkish announcement (M3 trigger): DIRECTIONALLY SUPPORTED but weak as a trigger.** Under the first M3 candidates the peak followed M3 in 9/9 cases; under the second candidates in 8/9 (the lone exception: the Nasdaq's 2021-11-19 peak lands 0.4m before Powell retired 'transitory' on 2021-11-30, though after the 2021-11-03 taper announcement). The lag, however, is extremely variable (variant-a median 14m, range 0 to 45m), so M3 timing alone has little predictive value for dating the peak.

**H3 — deep bursts (>25% drawdown) only with QT / reserve scarcity: NOT SUPPORTED as stated.** Deep bursts: 1972-74/SPX (48%); 1972-74/IXIC (60%); 1977-80/SPX (27%); 1977-80/IXIC (29%); 1999/SPX (49%); 1999/IXIC (78%); 2004/SPX (57%); 2004/IXIC (56%); 2021-22/SPX (25%); 2021-22/IXIC (36%). Only 2 of 10 occurred in explicit-QT cycles (2021-22). The 1972-74 and 1999-2000 busts (48-78%) happened with no balance-sheet runoff — though under the pre-2008 corridor system reserves were *always* scarce, so a looser reading of 'reserve scarcity' makes H3 unfalsifiable for pre-2008 cycles rather than confirmed.


## Robustness: peak-detection drawdown threshold (10% / 15% / 20%)

| cycle   | index   | P @10%     | P @15%     | P @20%     |   P-M4_m @10% |   P-M4_m @15% |   P-M4_m @20% |
|:--------|:--------|:-----------|:-----------|:-----------|--------------:|--------------:|--------------:|
| 1972-74 | IXIC    | 1973-01-11 | 1973-01-11 | 1973-01-11 |           0.3 |           0.3 |           0.3 |
| 1972-74 | SPX     | 1973-01-11 | 1973-01-11 | 1973-01-11 |           0.3 |           0.3 |           0.3 |
| 1977-80 | IXIC    | 1981-05-29 | 1981-05-29 | 1981-05-29 |          45.9 |          45.9 |          45.9 |
| 1977-80 | SPX     | 1980-11-28 | 1980-11-28 | 1980-11-28 |          39.9 |          39.9 |          39.9 |
| 1994    | IXIC    | no burst   | no burst   | no burst   |         nan   |         nan   |         nan   |
| 1994    | SPX     | no burst   | no burst   | no burst   |         nan   |         nan   |         nan   |
| 1999    | IXIC    | 2000-03-10 | 2000-03-10 | 2000-03-10 |           8.3 |           8.3 |           8.3 |
| 1999    | SPX     | 2000-03-24 | 2000-03-24 | 2000-03-24 |           8.8 |           8.8 |           8.8 |
| 2004    | IXIC    | 2007-10-31 | 2007-10-31 | 2007-10-31 |          40   |          40   |          40   |
| 2004    | SPX     | 2007-10-09 | 2007-10-09 | 2007-10-09 |          39.3 |          39.3 |          39.3 |
| 2015-18 | IXIC    | 2015-07-20 | 2015-07-20 | no burst   |          -4.9 |          -4.9 |         nan   |
| 2015-18 | SPX     | 2015-05-21 | no burst   | no burst   |          -6.9 |         nan   |         nan   |
| 2021-22 | IXIC    | 2021-11-19 | 2021-11-19 | 2021-11-19 |          -3.8 |          -3.8 |          -3.8 |
| 2021-22 | SPX     | 2022-01-03 | 2022-01-03 | 2022-01-03 |          -2.4 |          -2.4 |          -2.4 |

Reading: every assigned peak except 2015-18 is identical at 10%, 15% and 20% — the 1973/1980-81/2000/2007/2021-22 peaks and the 1994 'no burst' are threshold-invariant. Only 2015-18 moves: at 10% the S&P gains a qualifying peak (2015-05-21, i.e. *before* M4, strengthening the QE-era front-running reading), while at 20% the Nasdaq's 2015-07-20 peak drops out. The H1/H2/H3 verdicts are unchanged at all three thresholds.


## Limitations

- **n <= 7 cycles** (and only 2 with explicit QT): everything here is case-study evidence; the sign tests are reported with their n and should not be read as powered tests.
- **Peak definition sensitivity**: the 12-month/15% rule excludes fast-recovery crashes (S&P Q4-2018) and is sensitive at the margins (see robustness table).
- **CPI revisions / real-time vs revised data**: detection uses today's revised, seasonally adjusted CPI; policymakers and markets saw different real-time numbers.
- **Nasdaq history starts 1971-02**, shorter than the S&P (1945-); the 1972-74 Nasdaq row has only ~2 years of pre-cycle history.
- **Survivorship of the cycle list**: the seven cycles are a hand-picked, conventional list; mini-cycles and aborted tightenings (e.g. 1983-84, 1987) are excluded, which biases toward 'famous' outcomes.
- **M2 rule degenerates under ZIRP** (2009-2021): with the 2y pinned near zero, the >=75bp-in-6m trough rule reaches back to pre-QE lows for the 2015-18 and 2021-22 cycles.
- **Mirrored data**: in restricted environments the inputs come from commit-pinned GitHub mirrors of FRED/Yahoo downloads (validated by spot-checks); index history ends 2024-06 in the mirror, which is sufficient for every cycle studied.
- **1972-74 M3 is undefined** (no announcements era), so M3-based stats use at most 6 cycles.