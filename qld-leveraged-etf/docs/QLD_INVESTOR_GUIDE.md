# QLD (ProShares Ultra QQQ): A Comprehensive Investor's Guide

## TL;DR
- **QLD is a 2× daily-reset leveraged ETF on the Nasdaq-100, launched June 19, 2006 by ProShares**, with ~$13.35 billion in AUM, a 0.95% net (0.98% gross) expense ratio, and exposure delivered through a mix of physical Nasdaq-100 stocks, E-mini Nasdaq-100 futures (NQM6), and roughly twelve total-return swaps written by major banks (Goldman, Morgan Stanley, JPMorgan, UBS, Barclays, BNP, Citi, Bank of America, Nomura, Société Générale).
- **It is engineered for one trading day at a time**, so over longer holds, performance depends heavily on the *path* of returns: in trending bull markets it has compounded faster than 2× QQQ (since-inception NAV CAGR of 25.06% through 4/30/2026 vs. roughly 10.8% for QQQ since QQQ's 1999 inception per TotalRealReturns.com), but in volatile or sideways markets it suffers "volatility decay." Its peak-to-trough drawdown reached **−83.13% on March 9, 2009**, with single-year losses of −72.89% (2008) and −60.52% (2022).
- **For most investors the right way to use QLD is tactically or as a *moderately* leveraged sleeve** (Reddit r/LETFs and a popular OptimizedPortfolio analysis identify ~2–2.5× as historically optimal leverage on the Nasdaq-100); long-only buy-and-hold of QLD has won handily over the last decade only because the Nasdaq-100's trend and low realized volatility favored leverage — a regime that is *not* guaranteed to repeat. Replication using QQQ on margin, deep ITM LEAPS, or NQ futures is cheaper but operationally harder.

---

## Key Findings
1. QLD is a synthetically-leveraged product. Roughly half of its 2× exposure is physical Nasdaq-100 stock, the rest is built with ~14% NQ futures and ~110%+ of NAV in total-return swaps across **twelve named bank counterparties**.
2. Daily resetting creates path dependency: QLD can *exceed* 2× the index over long uptrends with low realized variance (positive "leverage alpha" — empirically +10.14% annualized alpha vs. the S&P 500 since inception per PortfoliosLab), but lags 2× in choppy or bear regimes and can suffer −60 to −80% drawdowns.
3. Over the past decade, QLD compounded at ~31.9%/yr vs. ~38.7% for TQQQ and ~18% for QQQ (PortfoliosLab) — a regime-dependent outcome, not a guarantee.
4. The cheapest way to *replicate* QLD's exposure is generally NQ futures (CME finds a 2×-leveraged investor saves ~34 bps/yr vs. margined QQQ), followed by deep ITM QQQ LEAPS, then QQQ on margin, then QLD itself.
5. The most-cited rules-based strategy for holding leveraged Nasdaq exposure is the **Gayed & Bilello 200-day moving average "Leveraged Rotation Strategy"** (Dow Award 2016), which historically delivered higher returns *and* lower drawdowns than buy-and-hold S&P 500.

---

## 1. Product Design and Leverage Implementation

**Issuer and basic facts.** QLD — full name **ProShares Ultra QQQ** — is a non-diversified ETF in the ProShares Trust managed by ProShare Advisors LLC (CUSIP 74347R206). It seeks daily investment results, before fees and expenses, equal to **2× (200%) the daily performance of the Nasdaq-100 Index®**. As of 5/15/2026, ProShares reports net assets of **$13,354,750,339**, a **gross expense ratio of 0.98% and a net (after contractual fee waiver through 9/30/2026) expense ratio of 0.95%**, NAV calculated at 4:00 p.m. ET, and a 30-day median bid-ask spread of 0.01%.

**Underlying index.** The Nasdaq-100 is a modified market-capitalization-weighted index of the 100 largest non-financial companies listed on the Nasdaq Stock Market (currently 101 constituents per ProShares' 3/31/2026 disclosure). Sector weights are heavily tilted to information technology, communication services and consumer discretionary; **the top 10 holdings in the Nasdaq-100 currently account for about 47% of the index** (per BigGo Finance and StockAnalysis: NVDA 9.08%, AAPL 7.31%, MSFT 5.19%, AMZN 4.70%, GOOGL 3.83%, plus AVGO, META, GOOG, TSLA and COST). The index is reconstituted every December with rebalances in March, June and September.

**How the 2× exposure is built.** Unlike a plain index ETF that physically holds shares, QLD layers cash equity holdings on top of derivative contracts to manufacture ~200% notional exposure. The 5/15/2026 holdings file shows, in order of exposure weight:

- A substantially complete physical sleeve of Nasdaq-100 stocks (NVDA, AAPL, MSFT, AMZN, GOOGL/GOOG, AVGO, TSLA, META, etc.) totaling roughly the fund's own net assets.
- **Nasdaq-100 E-mini futures** (NQM6 — June 2026 contract): 13.63% exposure weight ($1.81 billion notional, 3,095 contracts).
- **Total return swaps on QQQ or the Nasdaq-100** with twelve counterparties, totaling roughly an additional 100% of NAV. Notable swap lines: Goldman Sachs International (22.84% QQQ swap + 8.82% NDX swap), Morgan Stanley & Co. International (14.91% + 4.26%), JPMorgan Chase NA (9.62%), Nomura Capital (9.07%), Société Générale (9.05%), Barclays Capital (8.86%), UBS AG (8.73%), BNP Paribas (8.37%), Citibank NA (8.20%), Bank of America NA (7.97%).
- Cash collateral parked in the ProShares Genius Money Market ETF (IQMM, ~$1.28 billion) and several U.S. Treasury bills maturing 2026.

In a swap, the bank pays QLD the daily total return of the Nasdaq-100 (or QQQ) and QLD pays the bank a financing rate — typically the short-term funding rate plus a spread that varies by counterparty. This embedded financing cost (separate from the 0.95% expense ratio) is the largest hidden cost of holding QLD.

**Daily rebalancing.** Each day at the close, QLD must adjust its notional swap/futures exposure so that the next day's exposure is again exactly 2× the *new* NAV. This means it **buys exposure after up days and sells exposure after down days** — i.e., it is a momentum-following, "trend-amplifying" instrument by construction. ProShares states explicitly: "*This ProShares ETF seeks daily investment results that correspond, before fees and expenses, to 2× the daily performance of its underlying benchmark (the 'Daily Target'). … For any holding period other than a day, your return may be higher or lower than the Daily Target. These differences may be significant.*"

**Volatility decay / beta slippage.** Because daily resets compound geometrically, an index that whipsaws back to flat leaves a leveraged ETF below par. The canonical illustration: if QQQ rises 10% one day and falls 9.09% the next, it ends roughly flat; QLD rises ~20% then falls ~18.18% and ends down ~1.8%. Avellaneda and Zhang (2009, *SIAM Journal on Financial Mathematics*, SSRN 1404708) derive an exact formula linking an LETF's return to the multiple of the underlying's return *minus* a term proportional to the underlying's realized variance — meaning **the higher the realized variance during your holding period, the further QLD will lag 2× QQQ**, and conversely, *low realized variance with positive drift can let QLD exceed 2× QQQ over long periods*.

The flip side, which is often understated by critics: in **strong uptrends with low volatility**, daily resetting actually generates positive "leverage alpha" by repeatedly *buying more exposure* after winning days. PortfoliosLab calculates QLD's annualized alpha at **+10.14% with a beta of 2.07 and R² of 0.86 versus the S&P 500** since June 2006 — i.e., it has actually captured **309.45% of S&P 500 gains and 172.44% of losses**, more than the static 2× math would predict.

## 2. Inception and Historical Context

QLD launched on **June 19, 2006** — one of ProShares' very first geared ETFs. ProFund Advisors (the same shop) had pioneered leveraged ETFs only weeks earlier in summer 2006 in 2×, −1× and −2× flavors on several major indexes; 3× products (UPRO, TQQQ, SQQQ) didn't appear until 2009–2010 once the SEC, FINRA and the marketplace became more comfortable with the wrapper. QLD launched into the final stages of the 2003–2007 bull market and was tested almost immediately by the Global Financial Crisis — an inauspicious start that gave the LETF category its first major drawdown lesson.

## 3. Market Regime Performance

**Where QLD wins.** Sustained low-volatility uptrends in the Nasdaq-100. Examples (calendar-year total returns from Yahoo/PortfoliosLab):

| Year | QLD total return |
|---|---|
| 2009 | **+121.20%** |
| 2013 | +82.11% |
| 2017 | +70.34% |
| 2019 | +81.69% |
| 2020 | +88.90% |
| 2023 | **+117.13%** |
| 2024 | +42.81% |

In several of these years, QLD captured *more than 2×* the index — the "trend bonus" of daily re-leveraging.

**Where QLD loses.** High-volatility, choppy, or sustained bear-market regimes:

- **2008 GFC**: QLD returned **−72.89%** (vs. roughly −42% for QQQ, i.e., worse than a static 2× by ~12 percentage points). Maximum peak-to-trough drawdown reached **−83.13% on March 9, 2009** (PortfoliosLab). Worst single month: **October 2008, −33.1%**.
- **2018**: −8.32% in a sideways/choppy year vs. about −1% for QQQ.
- **2020 COVID crash**: QLD's **worst single day ever was March 16, 2020 at −24.3%**, with the index dropping ~12.3% that day. Yet by year-end the V-shaped recovery and unprecedented Fed liquidity drove QLD to a **+88.90% calendar-year gain** with the **best single month on record being April 2020 at +30.6%** (and best single day October 13, 2008 at +24.6%, the GFC short-squeeze).
- **2022 bear market**: QLD lost **−60.52%** for the calendar year as the Nasdaq-100 fell about 33% on rising rates and tech multiple compression — almost twice the index loss, with no "trend bonus" because volatility was elevated and the drift was negative.
- **2023–2024 recovery**: QLD compounded **+117.13% (2023) and +42.81% (2024)** as AI-driven leadership and falling realized volatility produced the ideal regime for daily re-leveraging.

**Cumulative scoreboard (through 4/30/2026, ProShares).** Since-inception NAV total return CAGR is **25.06%**, with 1-year +82.96%, 3-year +48.59% annualized, 5-year +20.12%. Over the past 10 years, PortfoliosLab calculates **QLD at +31.88% annualized vs. TQQQ at +38.70% and QQQ at roughly +18%** — i.e., 2× the index hasn't quite been delivered over 10 years even in the best LETF environment in history, and 3× delivered well under 3×.

## 4. Buy-and-Hold and DCA Pros and Cons

**Pros of long-term buy-and-hold:**
- Convex upside in trending bull markets. PortfoliosLab notes that since inception the average daily return is +0.13%, average monthly is +2.45%, and "an investment would double in approximately 2.4 years" at that pace, with **63% of months positive** historically.
- Operationally simple: a single ticker in any brokerage account, no rolling, no margin call risk, no K-1 (QLD is structured as a RIC — investors get a Form 1099-DIV, not a K-1, unlike commodity/volatility ProShares).
- Built-in "stop loss" embedded in the structure: because of daily resetting, the fund mathematically cannot go to zero from a single day's move unless the Nasdaq-100 falls ≥50% intraday — and exchange circuit breakers halt trading well before that.

**Cons of long-term buy-and-hold:**
- **Drawdowns are brutal and prolonged.** The −83.13% GFC drawdown took years to recover; Logical Invest measures the maximum days under water at >629 days in some 5-year windows.
- **Volatility decay** is real in chop/bear regimes — 2008, 2018, 2022 all delivered worse-than-2× outcomes.
- **0.95% expense ratio + implied swap financing** (a roughly 5–6% all-in annual carry today, depending on short-term rates) is a structural headwind that compounds against you in flat markets.
- **Concentration risk:** the Nasdaq-100 is heavily tech/AI-tilted (top 10 holdings ~47% of the index), so a sector rotation away from mega-cap growth would amplify drawdowns.
- **Counterparty risk:** if the index has a dramatic intraday move, the prospectus warns that swap counterparties may close out positions, leaving the fund unable to replace exposure and exposing investors to additional decay (ProShares Form 497 supplement, 2019).

**Dollar-cost averaging (DCA).** DCA structurally helps a buy-and-hold QLD allocation because it forces buying *more* shares at lower prices — exactly what volatility decay rewards on the recovery. Jason Kelly's "9Sig" strategy formalizes this idea on TQQQ; the same logic applies to QLD with less violence. The downside is opportunity cost: in a sustained bull market like 2009–2020, lump-sum almost always beats DCA, and that effect is magnified at 2× leverage. **Tax-advantaged accounts (Roth IRA, 401(k))** are strongly preferred for any DCA/rebalancing program in QLD because the high turnover and frequent rebalancing trades in taxable accounts can generate short-term capital gains and wash-sale headaches.

**Tax implications.** QLD is a 1940-Act fund, so shareholders receive Form 1099-DIV for distributions and Form 1099-B for sales — *no Schedule K-1*, unlike volatility/commodity ProShares limited partnerships such as UVXY's old structure. Sales follow standard short-/long-term capital-gains rules. However, QLD has historically distributed short-term capital gains in some years; a Schwab/Direxion educational note explains the mechanic by which leveraged ETF distributions are typically treated as ordinary-income short-term gains, which then reduce NAV by the distribution amount. Investors who churn QLD short-term will pay ordinary-income tax on gains; long-term holders in taxable accounts get long-term capital-gains rates but suffer the friction of any forced distributions.

## 5. Comparison with QQQ, TQQQ, and Other Geared Products

### The QQQ complex (all tied to the Nasdaq-100)

| Ticker | Issuer | Leverage | Exp. ratio | AUM (approx.) | Inception |
|---|---|---|---|---|---|
| **QQQ** | Invesco | 1× | 0.20% | **~$468B** (PortfoliosLab, May 19, 2026) | Mar 10, 1999 |
| **QQQM** | Invesco | 1× (cheaper share class) | 0.15% | large | Oct 2020 |
| **QLD** | ProShares | 2× | 0.95% | $13.35B | Jun 19, 2006 |
| **TQQQ** | ProShares | 3× | 0.84–0.95% | $27B+ | Feb 9, 2010 |
| **PSQ** | ProShares | −1× | 0.95% | ~$500M | Jun 19, 2006 |
| **QID** | ProShares | −2× | 0.95% | ~$240M | Jul 11, 2006 |
| **SQQQ** | ProShares | −3× | 0.95% | ~$3.2B | Feb 9, 2010 |

### S&P 500 and Dow analogs

- **SSO** — ProShares Ultra S&P 500 (2×), launched June 21, 2006, 0.90% ER. Lower-volatility cousin of QLD; max drawdown −84.67%.
- **UPRO** — ProShares UltraPro S&P 500 (3×), launched 2009, 0.91–0.92% ER.
- **DDM** — ProShares Ultra Dow30 (2×), launched 2006.
- **SH/SDS/SPXU** — −1×/−2×/−3× S&P 500 (ProShares).
- **SPXL/SPXS** — Direxion's 3×/−3× S&P 500 equivalents.

### Performance comparison

- **10-year (PortfoliosLab):** TQQQ ~+38.7%/yr, QLD ~+31.9%/yr, QQQ ~+18%/yr. Correlation between QLD and TQQQ is 1.00; their daily moves are essentially in lockstep but with different magnitudes.
- **Max drawdowns:** TQQQ −81.66%, QLD −83.13%, SSO −84.67%. (QLD's deeper drawdown vs. TQQQ reflects that QLD lived through 2008 while TQQQ didn't launch until Feb 2010.)
- **Sharpe and volatility (PortfoliosLab, trailing 12-mo):** TQQQ Sharpe 3.05, QLD Sharpe 2.80, SSO Sharpe 1.97; QLD's rolling 1-month volatility ~13.6% vs. TQQQ ~20.4%.

### International equivalents

In Europe, there are no UCITS 2× Nasdaq-100 ETFs available to retail under standard UCITS leverage limits; **WisdomTree Nasdaq 100 3× Daily Leveraged ETP (LQQ on Euronext Paris / 3LNQ on LSE / QQQ3 LN)** is the closest exposure outside the U.S., though it is a 3× ETP rather than 2×. There is no widely traded 2× Nasdaq-100 product in Canada, Japan or Hong Kong with materially comparable AUM and liquidity to QLD.

## 6. How to Replicate QLD with QQQ

### Option A — QQQ on margin
Reg-T retail margin allows up to **2:1 initial leverage** (50% maintenance), which exactly matches QLD's 2× target. **Interactive Brokers' own website states (as of May 7, 2026): "Margin loans start at USD 4.14%,"** with a tiered structure that runs higher for smaller balances. That financing cost is roughly comparable to (often slightly cheaper than) QLD's implied swap-funding cost plus 0.95% expense ratio combined. Pros: full long-term capital-gains tax treatment, no decay, no counterparty risk, dividends pass through. Cons: explicit margin-call risk, daily mark-to-market by the broker, the position is *constant-exposure* (does not auto-rebalance — leverage drifts toward 1× as the position rises and toward higher leverage as it falls, requiring manual rebalancing if you want to maintain 2×).

### Option B — Deep-in-the-money LEAPS calls on QQQ
A deep-ITM LEAPS call with strike at ~50% of spot and 12–24 months to expiry has a delta near 1.0 and minimal extrinsic value. Buying one DITM LEAPS to control 100 shares of QQQ for ~50% of the cash outlay effectively gives ~2× delta-equivalent exposure. Cash freed up can sit in T-bills earning a meaningful yield in current rate regimes. Pros: implied financing is often the cheapest of any retail-accessible leverage method; explicit long-term capital-gains treatment when held >12 months; no daily rebalancing decay. Cons: requires options approval; need to *roll* before expiry (a tax event and a friction); during sharp drops with volatility expansion, gamma/vega effects can create temporary mispricing; not 2× per se — delta drifts as the underlying moves.

### Option C — E-mini Nasdaq-100 futures (NQ) or Micro NQ (MNQ)
A single NQ contract is $20 × the Nasdaq-100 index (so notional ≈ $400,000+ at current index levels) and requires initial margin of about $33,534 overnight per QuantVPS — i.e., embedded leverage of ~12:1 if fully utilized, but the trader can choose any effective leverage by sizing the contract count to portfolio size. CME's own cost analysis ("A Cost Comparison of NASDAQ-100 Futures & ETFs") finds that a **2×-leveraged investor saves about 34 basis points per annum** using NQ futures instead of margined QQQ over a 12-month holding period. NQ futures receive **Section 1256 / 60/40 tax treatment** (60% long-term, 40% short-term regardless of holding period — usually advantageous for an active trader). Cons: contracts roll quarterly (Mar/Jun/Sep/Dec) with execution friction; requires futures account; daily mark-to-market.

### Cost comparison summary (typical retail; today's rates)

| Method | Explicit cost | Implied financing | Tax | Operational complexity |
|---|---|---|---|---|
| QLD | 0.95% ER | ~5% (embedded in swap) | LTCG/STCG via 1099 | Lowest |
| Margined QQQ | 0.20% ER + IBKR's 4.14% (and up) | Explicit | Standard LTCG | Medium |
| QQQ DITM LEAPS | Bid-ask + premium | ~5% (priced via put-call parity) | LTCG if >1yr | Medium-high |
| NQ futures | Commissions + small roll cost | Implicit; 3mL + ~19 bps per CME analysis | Section 1256 60/40 | High |

## 7. Quant Strategies on Reddit and Bogleheads

### HFEA (Hedgefundie's Excellent Adventure) and QLD variants
The original HFEA, posted to Bogleheads in February 2019 by user "Hedgefundie," called for **40% UPRO / 60% TMF** rebalanced quarterly (later updated August 2019 to **55% UPRO / 45% TMF**). It exploits risk parity between 3× S&P 500 (UPRO) and 3× long-Treasuries (TMF), targeting an "S&P-like risk profile with higher returns." Many variants substitute or supplement QLD/TQQQ for tech tilt — e.g., "**34% UPRO / 20% TQQQ / 20% BRK.B / 20% GDE / 6% TMF**" or QLD-flavored versions that reduce drawdowns relative to pure 3× sleeves. Critically, the strategy depends on negative stock-bond correlation: **2022 was a stress test** in which TMF lost so heavily it forced a 1-for-10 reverse split, with max drawdown −92.04% since inception, and the strategy underperformed badly. As a QLD application: replacing UPRO with QLD (i.e., 55% QLD / 45% TMF) reduces stock-sleeve leverage from 3× to 2×, materially lowering both expected return and drawdown — a popular "HFEA-lite" choice in Bogleheads discussions.

### 200-day moving average — Gayed & Bilello, "Leverage for the Long Run"
**Michael A. Gayed, CFA and Charles V. Bilello (Pension Partners, LLC), "Leverage for the Long Run — A Systematic Approach to Managing Risk and Magnifying Returns in Stocks"** (March 3, 2016; SSRN 2741701; **winner of the 2016 Charles H. Dow Award** from the CMT Association) is the foundational paper. Its core finding: a "Leveraged Rotation Strategy" that holds 3× equity when the S&P 500 closes above its 200-day moving average and T-bills otherwise *dramatically* outperforms unleveraged buy-and-hold *and* a constant-leveraged buy-and-hold, while exhibiting **lower max drawdowns at every leverage multiple (1.25×, 2×, 3×) than the unleveraged S&P 500.**

From the paper's abstract (verbatim): "*Using leverage to magnify performance is an idea that has enticed investors and traders throughout history. The critical question of when to employ leverage and when to reduce risk, though, is not often addressed. We establish that volatility is the enemy of leverage and that streaks in performance tend to be beneficial to using margin. The conditions under which higher returns would be achieved from using leverage, then, are low volatility environments that are more likely to experience consecutive positive returns.*"

And from the body: "*High volatility and seesawing action are the enemies of leverage while low volatility and streaks in performance are its friends.*"

Terminal values (Oct 1928–Oct 2015, 1% leverage cost assumption; from the paper): $10,000 buy-and-hold S&P → $19M; **1.25× LRS → $270M; 2× LRS → $39B; 3× LRS → $9T** ("*Chart 8 displays the growth of $10,000 from October 1928 through October 2015. A buy and hold of the S&P 500 grows to over $19 million while the 1.25x, 2x and 3x LRS grow to over $270 million, $39 billion and $9 trillion respectively.*"). The paper also explicitly cautions that constant-leverage 3× without the rotation rule produces "*multiple 50+% drawdowns*" and "*did not reach new highs after both the 2000-02 and 2007-09 Bear Markets.*" r/LETFs implementations typically pair this rule with QLD (2×) or TQQQ (3×), often using the 200-day SMA on the Nasdaq-100 itself rather than the S&P 500.

### 9Sig (Jason Kelly)
Jason Kelly's "9% Signal" strategy (from *The Kelly Letter*) uses **TQQQ alongside a bond fund**, with a quarterly rebalance to a 9% growth target — selling above target, buying below. Kelly explicitly addresses volatility decay: "*TQQQ can do very well when simply bought and held over long time frames. But my 9Sig plan does even better with it by harnessing the high volatility.*" Adapted to QLD (a "6Sig-style" variant), the strategy's signal target would be approximately 4–6% per quarter to reflect 2× rather than 3× leverage. The mechanism is equivalent to value-averaging into a leveraged vehicle.

### Other Reddit/quant ideas
- **Volatility targeting**: dynamically allocate between QLD and cash so that ex-ante portfolio vol stays at a target (e.g., 15–20% annualized). Backtests on r/LETFs show this dramatically improves Sharpe over static QLD by ducking 2022-style episodes.
- **Risk parity (multi-asset)**: combine QLD with managed futures (KMLM/DBMF), gold (GLD/GDE), or long Treasuries (TMF/TLT/ZROZ) in inverse-volatility weights.
- **r/LETFs "moderate leverage" consensus**: community simulations including the 2000–2002 dot-com bust have consistently found **2×–2.5× to be near-optimal historical leverage** for the Nasdaq-100 (3× often produces an unrecoverable −98% drawdown in 2000–2002 sims). A widely cited blog post by John Williamson (OptimizedPortfolio, frequently referenced from r/LETFs) concludes (verbatim): "*The sweet spot in my testing was 2.5x leverage. You can achieve this with a blend of 50% TQQQ and 50% QLD, the 2x LETF. That's what I have as my long-term buy-and-hold core holdings and I'm pleased with it.*" — making QLD a structural component of the most common "long-term leveraged" portfolios in the LETF community.

## 8. Additional Considerations

**Daily rebalancing tracking error.** Academic work (Avellaneda & Zhang 2009; Cheng & Madhavan 2009; Guedj, Li & McCann 2010; Lu, Wang & Zhang 2012; Charupat & Miu 2011) consistently confirms: for holding periods up to about one month, a 2× LETF delivers approximately 2× the underlying; beyond that, performance is a function of realized variance and the drift of the underlying. Trainor & Carroll (2013) and DeVault et al. (2021) argue that the decay narrative is overstated and that LETFs can serve legitimate roles in sophisticated portfolios. Recent work (Forsyth et al., arXiv 2412.05431, "Smart leverage? Rethinking the role of Leveraged Exchange Traded Funds in constructing portfolios to beat a benchmark") finds that LETF-based strategies can achieve partial stochastic dominance over the benchmark in information-ratio-optimal setups.

**Path dependency.** The same 2-day flat-index example given earlier generalizes: an LETF's return over N days is a function of *both* the path's compound return and its realized variance. ProShares offers a "Rebalancing Calculator" for investors who want to maintain a constant 2× target through time rather than letting daily resets do it.

**Why ProShares recommends QLD only for daily trading.** The official prospectus language is unambiguous: it is a "Daily Target" product, and ProShares emphasizes that holding longer than one day requires monitoring. The SEC has issued investor alerts; **FINRA Regulatory Notice 09-53 (published August 31, 2009; effective December 1, 2009)** increased maintenance margin for 2× LETFs from 25% to 50% of market value, with the notice stating "*these maintenance margin requirements will increase by a percentage commensurate with the leverage of the ETF.*"

**Notable QLD drawdowns:**
- 2008–2009 GFC: **−83.13%** peak-to-trough (PortfoliosLab; trough 3/9/2009).
- 2018 Q4: roughly −36%.
- 2020 COVID: peak-to-trough about −56% in roughly five weeks (best single day +24.6% on 10/13/2008; worst single day −24.3% on 3/16/2020).
- 2022 bear: **−63.78% 5-year max** (YCharts); −60.52% calendar-year.

**Counterparty considerations.** The 5/15/2026 holdings show twelve named swap counterparties across the major U.S., European and Japanese banks, which materially reduces single-counterparty concentration relative to LETFs that use one or two banks.

---

## Recommendations

1. **Default rule for long-term investors**: do *not* hold 100% QLD as a core position. The 2008 and 2022 drawdowns demonstrate that even a "moderate" 2× ETF can lose 60–80% in a single year, and that level of drawdown ends most retirement plans. Trigger to reconsider: a sustained move of QQQ above its 200-day SMA *combined with* a 30-day realized volatility below 15% and a positive 12-month momentum reading is the regime QLD is built for.
2. **If you want leveraged Nasdaq exposure as a tactical sleeve**, size QLD at **10–25% of liquid net worth** and pair with cash, Treasuries, gold, or managed futures as ballast. The "HFEA-lite" (50–60% QLD / 40–50% TMF or ZROZ, quarterly rebalanced) is a reasonable starting framework but is *not* tested across regimes like 1965–1981 stagflation.
3. **If you want a rules-based long-term QLD program**, implement either the **Gayed-Bilello 200-day moving average rule** (own QLD only when QQQ closes above its 200-day SMA; otherwise own cash/T-bills) or **Jason Kelly's signal investing approach** — both empirically reduce drawdowns by ducking sustained bear markets.
4. **Prefer NQ futures or DITM LEAPS over QLD** if you (a) have an account >$100k, (b) understand rolls/Section 1256/options, and (c) want lower all-in carry costs and better tax treatment. For smaller accounts and operational simplicity, QLD wins.
5. **Hold in tax-advantaged accounts when possible.** Frequent rebalancing and any short-term gains distributions are taxed at ordinary-income rates outside a Roth IRA or 401(k).
6. **Thresholds that would change these recommendations**: a sustained move of QQQ below its 200-day SMA, a rise in realized 30-day vol above ~30%, or a renewed positive stock-bond correlation regime should each prompt reducing or hedging the QLD position.

## Caveats

- Performance figures cited above (QLD since-inception NAV CAGR of 25.06%) reflect an exceptionally favorable regime for U.S. mega-cap tech (2009–2024 ZIRP-driven QE rally plus 2023–2024 AI mania) and **almost certainly will not be repeated** at that magnitude. The Nasdaq-100's own since-1999 annualized total return is about 10.8% (TotalRealReturns.com) — a much more reasonable long-term base case for projecting QLD's compounded returns going forward.
- The "Leverage for the Long Run" terminal-wealth claims ($10k → $9T with 3× LRS) are based on backtests that assume frictionless execution at the close, ignore taxes, and use only 1% per year for the cost of leverage — likely understating real-world LETF financing costs.
- HFEA backtests rely on synthetic LETF data prior to 2009 and on negative stock-bond correlations that held 1982–2020; 2022 demonstrated these can break down.
- Counterparty risk in QLD is mitigated by diversification across twelve banks, but in a true 2008-style banking crisis, multiple counterparties can stress simultaneously. The prospectus warns that intraday dislocations can lock the fund out of its target exposure.
- ProShares' own statements on QLD's "daily target" should be taken seriously; the SEC and FINRA have repeatedly emphasized that LETFs are unsuitable for buy-and-hold for most retail investors.
- Reddit-sourced "optimal leverage" findings are sensitive to start dates and assumed financing costs. Backtests starting in 2000 (including dot-com) consistently support 1.5×–2× as optimal for Nasdaq, while backtests starting in 2010 favor 3×.
- Some figures cited (QQQ top-10 concentration, IBKR upper-tier margin rate, Nasdaq-100 long-term CAGR through QLD's inception period) are approximations consistent with multiple sources but should be re-verified against the most recent fund disclosures or rate tables before any allocation decision.