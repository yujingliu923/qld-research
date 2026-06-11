# quant-research

Quantitative finance research monorepo. Each topic lives in its own
standalone folder with its own README, code, data and outputs.

| Topic | Contents |
|---|---|
| [`qld-leveraged-etf/`](qld-leveraged-etf/) | QLD (2× Nasdaq-100 ETF) replication back to 1999, fee calibration, QQQ/QLD/TQQQ comparison, buy-and-hold and DCA strategy backtests |
| [`tightening-cycle-timing/`](tightening-cycle-timing/) | Fed tightening cycles 1972-2022: timing between inflation inflection, rate-expectation shift, policy signal, first hike, QT and the equity market peak; current-regime and rolling-window similarity analyses |

## Conventions

- Each folder is self-contained: run its scripts from anywhere (paths are
  derived from the file location), install its own `requirements.txt`.
- Generated artifacts (reports, figures, cached data) are committed inside
  the topic folder so results are reviewable on GitHub without rerunning.
- New research topics get a new top-level folder.
