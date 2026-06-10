# tightening-cycle-timing

For each Fed tightening cycle (1972-74, 1977-80, 1994, 1999, 2004,
2015-18, 2021-22), measures the time from four milestone types to the
subsequent equity market peak (S&P 500 and Nasdaq Composite):

- **M1** inflation inflection (YoY CPI turns from falling to rising) — detected
- **M2** bond-market rate-expectation shift (2y/1y yield trough) — detected
- **M3** hawkish policy signal/announcement — hard-coded, verified
- **M4** first rate hike (plus QT start where applicable) — hard-coded, verified
- **P** equity peak (12-month unexceeded closing high followed by a
  >= 15% drawdown) — detected

## Run

```bash
pip install -r requirements.txt
python run_all.py            # FORCE_REFRESH=1 to bypass the parquet cache
```

## Structure

| Path | Contents |
|---|---|
| `src/data.py` | FRED + index data; direct fetch with commit-pinned GitHub-mirror fallback; parquet cache; integrity spot-checks |
| `src/events.py` | Hard-coded cycle/M3/M4/QT table + verification against FEDFUNDS/WALCL |
| `src/detect.py` | M1/M2/P detection rules |
| `src/analysis.py` | Master timeline, interval stats (sign tests), orderings, conditional drawdowns, robustness, figures, SUMMARY.md |
| `run_all.py` | End-to-end driver |
| `output/` | `SUMMARY.md` (read this), CSV tables, timeline PNGs |

Each timeline figure also shows the fed funds path on the right axis
(daily target DFEDTAR/DFEDTARU from 1982-09, monthly average FEDFUNDS
before that, when no target was announced), with red triangles at each
hike, a star at the terminal/peak rate and a teal triangle at the first
subsequent cut. Marker dates are the *effective* dates of target
changes, which can lag the FOMC announcement by a day.

## Headline results (details + caveats in `output/SUMMARY.md`)

- Equity peaks historically came *after* the first hike — often years
  after (1977-80: +40-46 months; 2004: +39-40 months). Front-running of
  M4 (peak before the first hike) appears only in the QE-era cycles
  (2015-18 Nasdaq, 2021-22 both indices).
- The peak followed the hawkish announcement (M3) in essentially every
  measurable case, but with lags from ~0 to 45 months.
- Deep busts (>25%) are *not* QT-specific: 1973-74, 2000-02 and 2007-09
  all happened without balance-sheet runoff.
- n <= 7 cycles: treat everything as case-study evidence, not statistics.
