---
name: stock-screener
description: Run the local fundamental screener (screener.py — quality, GARP, value, dividend, speculative screens on Yahoo Finance data), read its results_<template>.csv output, and turn the passing names into a ranked, research-ready shortlist. Use when the user wants to run their screener, review screener results or watchlists, or asks why a ticker passed or failed a screen. Triggers on "run my screener", "screener.py", "screener results", "what passed the value screen", "quality / GARP / dividend / speculative screen", "watchlist_", or "why did X fail".
---

# Stock Screener

Drives the user's own `screener.py` rather than inventing screens. For open-ended idea sourcing with no screener in the workspace, use `idea-generation` instead.

## Step 1: Locate the screener

Look for `screener.py` in the working directory, then its parent directories. Confirm it is the right file by checking for `TEMPLATES = ["quality", "garp", "value", "dividend", "speculative"]`. If it can't be found, ask the user for the path — do not write a replacement.

Note whether recent `results_<template>.csv` files already exist next to it and their modification times.

## Step 2: Decide whether to run it

- **Fresh results exist (today) and the user only wants to review** → skip to Step 3.
- **Otherwise run it** from the screener's directory:

```bash
python3 screener.py --template <quality|garp|value|dividend|speculative|all> [--tickers <file>] [--out <dir>]
```

- Default ticker file is `tickers.txt`; if it's missing the script falls back to ~30 built-in large caps. Tell the user which universe was used — results on the default list say little.
- It pauses 0.4s per ticker, so ~100 tickers takes about a minute. Run large universes in the background.
- If `yfinance` / `pandas` are missing, point the user to `pip install -r requirements.txt` rather than installing silently.
- Report any tickers the script printed as "skipped".

## Step 3: Read the results

Each `results_<template>.csv` has one row per ticker, passers first. Key columns:

| Column | Meaning |
|---|---|
| `passed` | No check failed and at most one check had missing data |
| `score` | % of known checks passed (screen + basic filters + red flags) |
| `failed_checks` / `missing_checks` | `;`-separated check names |
| `intrinsic_value`, `margin_of_safety` | 5-year FCF DCF: growth = revenue CAGR capped at 15%, 9% discount, 3% terminal |
| `buy_zone` | Margin of safety ≥ 25% |

What each screen checks (the script is the source of truth if these differ):

- **quality** — ROE > 15% every year, ROIC > 12%, FCF positive 3+ years, D/E < 0.5, revenue growth > 8%/yr
- **garp** — EPS growth > 15%/yr, 0 < PEG < 1.5, FCF positive, price above 200-day average
- **value** — P/E and EV/EBITDA below sector-peer median (peers = other tickers in the run), FCF yield > 6%, D/E < 1, ROE > 10%
- **dividend** — yield 2–4%, raised 10+ years running, payout < 60%, 5y dividend growth > 6%/yr
- **speculative** — market cap $300M–$2B, revenue growth > 25%/yr, 2+ years cash runway, insiders > 10% (skips basic filters)

All screens except speculative also apply basic filters (market cap > $2B, volume > 500K, price > $5, common stock, NYSE/NASDAQ). All apply red flags (FCF negative while profitable, dilution > 5%, receivables outgrowing revenue by > 15 pts, short interest > 15%, payout > 90% outside REITs/utilities).

## Step 4: Build the shortlist

For each screen run, present:

1. **Header** — screen, universe size, number passed, run date.
2. **Passers table** — ticker, name, sector, score, price, intrinsic value, margin of safety, buy zone, and any `missing_checks`. Sort buy-zone names first, then by margin of safety.
3. **Near misses** — non-passers with score ≥ 80 and exactly one failed check, with the check that failed. These are often worth a look.
4. **Names in multiple screens** — tickers passing two or more templates (e.g. quality + value) are usually the strongest candidates; call them out.
5. **Caveats** worth flagging per name:
   - A passer with a missing check passed on incomplete data.
   - Value-screen sector medians come only from tickers in this run; a small or single-sector universe makes them unreliable.
   - The DCF is mechanical — a high margin of safety on a cyclical, a turnaround, or a company with lumpy FCF needs checking, not trusting.
   - Data is Yahoo Finance and can be stale or wrong; spot-check anything that looks extreme.

Keep it to what the CSV says. Do not add price targets or buy/sell calls.

## Step 5: Hand off to research

Offer next steps on the shortlist using the existing skills:

- `comps-analysis` — check the cheapness against a proper peer set, not just the run's sector median
- `earnings-preview` / `earnings-analysis` — for names reporting soon or just reported
- `catalyst-calendar` — upcoming events across the shortlist
- `thesis-tracker` — start a thesis for names the user wants to track
- `dcf-model` — a full DCF to replace the screener's mechanical one

## Answering "why did X pass/fail?"

Find the ticker's row in the relevant CSV and quote `failed_checks` and `missing_checks`, along with the underlying metric values (e.g. `roe_by_year`, `debt_to_equity`, `peg`, `fcf_yield`). Say how far each failing metric is from its threshold.

## Output

Markdown in chat by default. If the user wants a file, write `screener-shortlist-<YYYY-MM-DD>.md` next to the results (or an Excel workbook via `xlsx-author` if they ask for one).
