---
name: position-sizing
description: Turn a screener shortlist into whole-share target positions and a proposed order list for a portfolio in portfolio_state.json, respecting per-name, speculative, and sector caps and a cash reserve. Use when the user asks how much of each name to buy, how to deploy cash into screener passers, or how to size or rebalance their positions. Triggers on "position sizing", "how much should I buy", "size these positions", "build a portfolio from the screen", "deploy my cash", "target weights", "rebalance into the shortlist".
---

# Position Sizing

Run the bundled script for all arithmetic. Your job is choosing the inputs with the user and explaining the result.

The output is a **proposal**. Never edit `portfolio_state.json` and never place orders. The user enters any trades themselves (in the Northstar Brokerage app, which is a simulator, or with their broker).

## Step 1: Inputs

- **Portfolio**: `portfolio_state.json`, found the same way as in `portfolio-risk` (project folder, or `~/Library/Application Support/NorthstarBrokerage/` for the packaged app).
- **Candidates**: passers in the screener's `results_<template>.csv`. Run `stock-screener` first if there are none or they are stale. The user can restrict screens (`--screens quality,value`) or name tickers directly (`--tickers`).
- **Method**, which you should confirm with the user:
  - `equal`: same dollars per name (the default and the easiest to defend)
  - `score`: weight by screener score, boosted by margin of safety (capped at +50%)
  - `inverse-vol`: less money in more volatile names (needs a year of price history)
- **Limits** (defaults, which the user can change): 10% per name, 3% per speculative-only name, 30% per sector, 5% cash reserve, at most 15 names.

## Step 2: Run

```bash
python3 <this skill's directory>/scripts/position_sizing.py --state <path> --results-dir <folder> \
  [--method equal|score|inverse-vol] [--screens a,b] [--tickers X,Y] \
  [--max-position 0.10] [--spec-cap 0.03] [--max-sector 0.30] [--cash-reserve 0.05] [--max-names 15] \
  [--sell-unlisted] [--rebalance] [--json]
```

How existing holdings are treated:

- **Held, not a candidate**: kept as is, and counted against its sector's cap. `--sell-unlisted` proposes selling them instead. Only use it when the user asks.
- **Held and a candidate**: kept at its current size, trimmed only if it breaks the name cap or its sector is over the cap. `--rebalance` resizes it from scratch like a new name, which can mean large trims.

## Step 3: Present

1. **Orders**: a table of BUY/SELL/HOLD with shares, dollars, and the target weight. Put sells first; they fund the buys.
2. **Why each size**: point out names held back by a cap (the `note` column). When a sector cap is binding, say which names it is squeezing.
3. **Before and after**: cash and sector weights.
4. **Undeployed cash**: if cash after is well above the reserve, explain that the caps prevented deploying it. Options are more names, looser caps, or holding cash. Don't loosen caps without asking.
5. **Things to check before acting**:
   - Every SELL realizes a gain or loss. Show the unrealized P/L from `portfolio-risk` for anything being trimmed.
   - Prices are the latest close (or CSV/state prices with `--no-refresh`). Orders fill at whatever the market is when entered.
   - Sizing does not replace research. Names from `stock-screener` passed a mechanical screen. Point to `comps-analysis`, `earnings-preview` or `thesis-tracker` for the largest new positions.

Run `portfolio-risk` on the result if the user wants to see what the proposed portfolio would look like. To do that, write the proposed positions to a new scratch state file, never over the real one.

Don't present the output as a recommendation to buy or sell any security. It is arithmetic on the user's own screen and limits.
