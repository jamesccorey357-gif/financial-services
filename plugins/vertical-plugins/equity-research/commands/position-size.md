---
description: Size a screener shortlist into a proposed order list
argument-hint: "[equal|score|inverse-vol] [screens or tickers]"
---

Load the `position-sizing` skill to turn screener passers into whole-share target positions within per-name, sector, and cash limits.

If a method, screens, or tickers are provided, use them. Otherwise default to equal weight across all passing screens and confirm the limits with the user before running. Propose orders only; never edit the portfolio file.
