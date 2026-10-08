---
description: Archive the latest screener run and show how past picks performed
argument-hint: "[screen, e.g. 'value'] [benchmark, e.g. 'QQQ']"
---

Load the `screen-backtest` skill. First snapshot the current `results_*.csv` into `screen_history/`, then evaluate forward returns of every archived run.

If a screen or benchmark is provided, use it. Otherwise evaluate all screens against SPY.
