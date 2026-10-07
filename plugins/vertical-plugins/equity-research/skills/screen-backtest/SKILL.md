---
name: screen-backtest
description: Track how the user's screener picks performed after each run — archive every screener.py run, then measure forward returns of passers vs a benchmark and vs the stocks that failed, by screen and horizon. Use when the user asks whether a screen works, how past picks did, or which screen performs best, and after every screener run to archive it. Triggers on "backtest the screen", "did the value screen work", "how did my picks do", "screen performance", "which screen is best", "track the screener".
---

# Screen Backtest

Forward tracking only. This skill measures what happened **after** each real screener run. It does not re-apply a screen to past data. Explain why if the user asks for a classic backtest:

> `screener.py` reads Yahoo Finance fundamentals as they are today. Many inputs (P/E, PEG, short interest, insider ownership, latest ROE) have no history there, so re-running a screen "as of" an old date would use information that wasn't available then. Its results would mostly pick names that are known, today, to have done well. A real backtest needs point-in-time fundamentals from a paid source (Compustat, FactSet, S&P Capital IQ). If the user has one of those connectors, offer to design one; otherwise forward tracking is the honest option.

## Archive every run

`screener.py` overwrites `results_<template>.csv` each time, so an un-archived run is lost. After any screener run, and whenever this skill is used, archive first:

```bash
python3 <this skill's directory>/scripts/screen_history.py snapshot --results-dir <screener folder> --history-dir <screener folder>/screen_history
```

The run date comes from the files' modification time, so a late snapshot is still filed correctly. Running it twice for the same date does nothing.

## Evaluate

```bash
python3 <this skill's directory>/scripts/screen_history.py evaluate --history-dir <screener folder>/screen_history [--template value] [--benchmark SPY] [--json]
```

For each archived run and screen, it reports equal-weight total returns (dividends included) from the run date's close for:

| Column | Meaning |
|---|---|
| Passers | Stocks that passed the screen |
| BuyZone | Passers whose DCF margin of safety was 25% or more |
| NonPass | The rest of that run's universe, which is the fairest comparison |
| Excess | Passers minus benchmark |
| Spread | Passers minus non-passers. This is the screen's actual edge |
| Hit | % of passers that beat the benchmark |

Periods: `since_run` (to the latest close), plus 1m / 3m / 6m / 12m once that much time has passed.

## Interpret honestly

- **Sample size first.** A screen with 3 passers on 2 runs has proven nothing. Under about 10 runs spanning 6+ months, describe results as early observations, not evidence. The script prints a warning when history is thin.
- **Spread beats excess.** A screen can beat SPY just because its universe did (e.g. all large-cap tech). Spread vs non-passers isolates what the screen itself added.
- **Overlapping runs aren't independent.** Weekly runs with the same five passers are close to one observation, not five.
- **One stock can be the whole result** at these sizes. Check `by_ticker` in `--json` output before drawing a conclusion.
- **Universe bias.** If `tickers.txt` was picked by hand (or the 30-name default list was used), results say as much about that list as about the screen.
- **Not a prediction.** Past screen performance doesn't say what the next run's picks will do.

## Output

A short read per screen (what the spread and hit rate say, and how much history backs them), then the table. If a screen is consistently negative over a meaningful sample, suggest looking at which check is letting losers through (compare `failed_checks` and metrics of the worst passers in the archived CSVs). Don't change `screener.py` thresholds without the user asking.
