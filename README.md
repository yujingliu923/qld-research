# QLD Quantitative Research

Replication, comparative analysis, and long-hold strategy backtests for **QLD (ProShares Ultra QQQ, 2× daily-reset Nasdaq-100 ETF)** alongside its 1× (QQQ) and 3× (TQQQ) peers.

## What's here

| Path | Contents |
|---|---|
| [`docs/QLD_INVESTOR_GUIDE.md`](docs/QLD_INVESTOR_GUIDE.md) | Long-form investor's guide to QLD (product structure, history, strategies) |
| [`docs/QLD_CALIBRATION.md`](docs/QLD_CALIBRATION.md) | Fee calibration methodology + tracking-error report; shows how QLD is simulated back to 1999 |
| [`docs/QLD_RETURNS_COMPARISON.md`](docs/QLD_RETURNS_COMPARISON.md) | Yearly bars + monthly best-performer heatmap; QQQ vs QLD vs TQQQ |
| [`docs/QLD_STRATEGY_REPORT.md`](docs/QLD_STRATEGY_REPORT.md) | Buy & Hold and Monthly DCA backtests across two evaluation windows |
| [`docs/QQQ_SWING_STRATEGY_REPORT.md`](docs/QQQ_SWING_STRATEGY_REPORT.md) | Reddit "buy after −2%, sell after +3%" QQQ swing strategy backtest + live-state check |
| [`scripts/`](scripts/) | The 4 reproducible Python scripts |
| [`data/`](data/) | Cached price series + strategy metrics (CSV) |
| [`figures/`](figures/) | All generated plots (PNG) |

## Highlights

- **Calibrated daily fee:** 0.01090 %/day ≈ **2.747 %/yr** (≈ 0.95 % expense ratio + 1.80 % implied swap financing) — fit by minimising MSE of log price-ratio against real QLD over 2006-06-22 → today, 5,011 trading days.
- **Period-A (1999 → today, simulated) Buy & Hold**: QLD's 27-year CAGR is **10.93 %** — indistinguishable from QQQ's 10.90 % — because the simulated −98.78 % dot-com drawdown took **20 years** (2000-03-27 → 2020-08-26) to recover. TQQQ over the same window earned **5.07 %** CAGR and **has not** reclaimed its 2000 peak.
- **Period-B (2010-02 → today, real) Buy & Hold**: leverage paid off cleanly. QLD CAGR **33.80 %**, TQQQ **44.09 %**, vs. QQQ **19.84 %**. Max drawdowns scaled near-linearly with leverage (−35 % / −64 % / −82 %), and every product fully recovered within the window.
- **Monthly DCA inverts the dot-com pathology** — spreading 327 monthly contributions over 1999 → today gives QLD a money-weighted IRR of **23.0 %/yr** vs. QQQ's 15.3 %/yr (TQQQ: 28.2 %/yr).

## Reproducing the analysis

```bash
# Requires Python 3.12, an internet connection (for yfinance), and the deps in requirements.txt.
pip install -r requirements.txt

python scripts/qld_replication.py          # → data/qld_simulated.csv + figures/qld_replication.png
python scripts/qld_returns_comparison.py   # → figures/yearly_returns_bar.png + monthly_best_heatmap.png
python scripts/qld_strategies.py           # → 8 strategy plots + data/strategy_metrics.csv
python scripts/heatmap_breakdown.py        # prints monthly-winner counts (cited in QLD_STRATEGY_REPORT §7.A)
python scripts/qqq_swing_strategy.py       # → 4 swing plots + data/qqq_swing_metrics.csv + live-state check
```

All scripts use absolute paths derived from `Path(__file__)`, so they can be run from any cwd.

## Bundled TQQQ reference data

[`data/tqqq_simulated.csv`](data/tqqq_simulated.csv) is a snapshot of the simulated TQQQ series produced by the companion [TQQQ replication research](https://github.com/) (TQQQ inception is 2010-02-11; the simulated values back to 1999 use the same constant-daily-fee model described in [`docs/QLD_CALIBRATION.md`](docs/QLD_CALIBRATION.md), but calibrated against real TQQQ rather than real QLD). Only the **pre-2010** simulated TQQQ values are consumed by the analysis here; for **2010 onward** the scripts re-fetch real TQQQ from yfinance at runtime.

If you want to regenerate `data/tqqq_simulated.csv` yourself rather than trust the bundled snapshot, the calibration follows the same methodology as [`scripts/qld_replication.py`](scripts/qld_replication.py) — just substitute leverage 3× for 2× and use TQQQ instead of QLD as the calibration target.

## Caveats

Simulation-based pre-inception figures (QLD pre-2006-06-19, TQQQ pre-2010-02-11) assume a constant daily fee and a frictionless market that would have allowed the fund to continue trading through arbitrary drawdowns. In reality LETFs face exchange halts, counterparty defaults, and reverse splits that this model does not capture — e.g., the −99 %+ simulated dot-com drawdowns should be treated as an illustration of leverage pathology, not a literal counterfactual. See [`docs/QLD_CALIBRATION.md`](docs/QLD_CALIBRATION.md) §6 and [`docs/QLD_STRATEGY_REPORT.md`](docs/QLD_STRATEGY_REPORT.md) §6 for full caveats.

## License

MIT (see [LICENSE](../LICENSE) at the repository root, if present).
