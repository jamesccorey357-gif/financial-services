---
name: portfolio-risk
description: Risk report on a portfolio held in portfolio_state.json — concentration, sector exposure, unrealized P/L, volatility, beta, VaR, drawdown, correlated pairs, a market stress test, and whether each holding still passes the user's screens. Use when the user asks how risky their portfolio is, what they're exposed to, what happens in a selloff, or whether their holdings still pass the screener. Triggers on "portfolio risk", "how concentrated am I", "sector exposure", "what if the market drops 20%", "VaR", "drawdown", "beta of my portfolio", "do my holdings still pass".
---

# Portfolio Risk

Run the bundled script for every number. Do not compute weights, vol, beta or VaR by hand.

## Step 1: Find the portfolio

Look for `portfolio_state.json` in the working directory and its parents. The format is:

```json
{"cash": 33320.0, "positions": [{"symbol": "AAPL", "shares": 18, "avg_cost": 182.4, "last_price": 212.18}], "orders": []}
```

If the user runs the packaged Northstar Brokerage app, the live file is at `~/Library/Application Support/NorthstarBrokerage/portfolio_state.json` (or `$APP_SUPPORT_DIR`), not the project folder. If both exist, ask which one.

If the user has no state file, offer to build one from holdings they paste. Write it to a new file, never over an existing one.

## Step 2: Run the report

```bash
python3 <this skill's directory>/scripts/portfolio_risk.py --state <path> [--results-dir <folder with results_*.csv>] [--benchmark SPY] [--period 1y] [--json]
```

- Pass `--results-dir` when screener output exists. It adds which screens each holding passes and any red flags.
- Use `--json` when you need the numbers for further work; the text report is fine to summarize from.
- `--no-refresh` works offline but uses the `last_price` saved in the file. The brokerage app only updates that on a trade, so it can be months stale. Say so whenever you use it.
- Needs `yfinance` and `pandas` (the screener's `requirements.txt` covers both).

## Step 3: Interpret

Lead with what matters most for this portfolio, not a tour of every metric:

- **Concentration.** Flag any single name over 10% of equity, top 3 over 40%, or effective positions (1/HHI) under 5. A portfolio of three tech names is one bet, whatever the count says.
- **Sector.** Flag any sector over 30%. Note when every holding sits in one sector.
- **Cash.** A large cash weight dampens every portfolio-level number. When cash is over 20%, quote the "stocks only" vol and beta alongside the portfolio figures, or the risk will look smaller than it is.
- **Market risk.** Beta, annual vol, 1-day 95% VaR in dollars, and the stress lines. Translate at least one into plain terms ("a 20% market fall would cost roughly $X").
- **Correlation.** Pairs at 0.70 or above move together; holding both adds less diversification than it looks.
- **Screener status.** Holdings that no longer pass any screen, or carry a red flag, are worth a second look. That is a prompt to re-check the thesis, not a sell signal.
- **Unrealized gains.** Large gains matter for any trimming decision because selling realizes them.
- **Balance sheets.** If the `credit` plugin is installed, `credit-analysis` can check every holding's leverage and coverage in one run. Equity takes the first loss when a credit weakens.

## Caveats to state

- Vol, VaR, beta and drawdown apply today's weights to the past period. They show how the current mix would have behaved, not the account's actual history.
- VaR is historical: it says nothing about moves larger than the window contains.
- Data is Yahoo Finance. Sectors and betas can be missing or wrong.

## Output

A short summary: the 3–5 risks that matter, each with its number, then the full table if the user wants it. Do not recommend specific trades here. If the user wants to act on the findings, hand off to `position-sizing`.
