#!/usr/bin/env python3
"""
Archive screener runs and measure how each screen's picks did afterwards.

  python3 screen_history.py snapshot --results-dir .                 # archive results_*.csv under screen_history/<run date>/
  python3 screen_history.py evaluate --history-dir screen_history     # forward returns of every archived run
  python3 screen_history.py evaluate --history-dir screen_history --template value --json

screener.py overwrites results_<template>.csv on every run, so snapshot after each run. The run date is
taken from the files' modification time, so snapshotting a day late still files the run under the right date.

evaluate compares, per snapshot and screen, the equal-weight total return (dividend-adjusted closes) from
the run date's close to the latest close for:
  passers, buy-zone passers, and the rest of that run's universe (non-passers), against a benchmark.
Fixed horizons (1m/3m/6m/12m) are reported once enough time has passed.

This is forward tracking only. It never re-applies a screen to past data: the screener's inputs are
current-only on Yahoo Finance, so a retroactive backtest would be full of look-ahead bias.
"""
import argparse
import glob
import json
import os
import shutil
import sys
from datetime import date, timedelta

HORIZONS = {"1m": 30, "3m": 91, "6m": 182, "12m": 365}


def snapshot(args):
    files = sorted(glob.glob(os.path.join(args.results_dir, "results_*.csv")))
    if not files:
        sys.exit(f"no results_*.csv in {os.path.abspath(args.results_dir)}; run screener.py first")
    run_day = date.fromtimestamp(max(os.path.getmtime(f) for f in files)).isoformat()
    dest = os.path.join(args.history_dir, run_day)
    if os.path.isdir(dest) and not args.overwrite:
        print(f"{dest} already exists; nothing copied (use --overwrite to replace)")
        return
    os.makedirs(dest, exist_ok=True)
    for f in files:
        shutil.copy2(f, dest)
    print(f"archived {len(files)} file(s) from {os.path.abspath(args.results_dir)} -> {os.path.abspath(dest)}")


def load_history(history_dir, template):
    """[(run date, template, DataFrame)] for every archived results file."""
    import pandas as pd
    runs = []
    for d in sorted(glob.glob(os.path.join(history_dir, "*"))):
        try:
            day = date.fromisoformat(os.path.basename(d))
        except ValueError:
            continue
        for f in sorted(glob.glob(os.path.join(d, "results_*.csv"))):
            tpl = os.path.basename(f)[len("results_"):-len(".csv")]
            if template and tpl != template:
                continue
            runs.append((day, tpl, pd.read_csv(f)))
    return runs


def as_bool(v):
    return v is True or str(v).strip().lower() == "true"


def evaluate(args):
    import pandas as pd
    import yfinance as yf
    runs = load_history(args.history_dir, args.template)
    if not runs:
        sys.exit(f"no snapshots in {os.path.abspath(args.history_dir)}; run `snapshot` after a screener run")
    tickers = sorted({str(t).upper() for _, _, df in runs for t in df["ticker"]} | {args.benchmark})
    start = min(day for day, _, _ in runs) - timedelta(days=7)
    px = yf.download(tickers, start=start.isoformat(), auto_adjust=True, progress=False)["Close"]
    if not hasattr(px, "columns"):
        px = px.to_frame(tickers[0])
    px = px.dropna(how="all")
    last_day = px.index[-1].date()

    def close_on_or_after(sym, day):
        if sym not in px.columns:
            return None, None
        s = px[sym].dropna()
        s = s[s.index.date >= day]
        return (float(s.iloc[0]), s.index[0].date()) if len(s) else (None, None)

    def close_on_or_before(sym, day):
        if sym not in px.columns:
            return None
        s = px[sym].dropna()
        s = s[s.index.date <= day]
        return float(s.iloc[-1]) if len(s) else None

    def ret(sym, d0, d1):
        p0, _ = close_on_or_after(sym, d0)
        p1 = close_on_or_before(sym, d1)
        return None if p0 is None or p1 is None or p0 <= 0 else p1 / p0 - 1

    def group_ret(syms, d0, d1):
        rs = [r for r in (ret(s, d0, d1) for s in syms) if r is not None]
        return (sum(rs) / len(rs) if rs else None), len(rs)

    results, warnings = [], []
    for day, tpl, df in runs:
        df = df.assign(ticker=df["ticker"].astype(str).str.upper())
        passed = df[df["passed"].map(as_bool)]["ticker"].tolist()
        buy_zone = df[df["passed"].map(as_bool) & df["buy_zone"].map(as_bool)]["ticker"].tolist()
        rest = df[~df["passed"].map(as_bool)]["ticker"].tolist()
        missing = [t for t in df["ticker"] if t not in px.columns or px[t].dropna().empty]
        if missing:
            warnings.append(f"{day} {tpl}: no prices for {', '.join(missing)} (delisted or renamed?)")
        periods = {"since_run": last_day}
        for name, days in HORIZONS.items():
            if day + timedelta(days=days) <= last_day:
                periods[name] = day + timedelta(days=days)
        out = {"run": day.isoformat(), "template": tpl, "universe": len(df), "passers": passed,
               "buy_zone": buy_zone, "periods": {}}
        for name, end in periods.items():
            bench = ret(args.benchmark, day, end)
            p, n_p = group_ret(passed, day, end)
            b, n_b = group_ret(buy_zone, day, end)
            r, n_r = group_ret(rest, day, end)
            beat = [s for s in passed if ret(s, day, end) is not None and bench is not None and ret(s, day, end) > bench]
            out["periods"][name] = {
                "end": end.isoformat(), "benchmark": bench,
                "passers": p, "passers_n": n_p, "passers_excess": None if p is None or bench is None else p - bench,
                "buy_zone": b, "buy_zone_n": n_b,
                "non_passers": r, "non_passers_n": n_r,
                "spread_vs_non_passers": None if p is None or r is None else p - r,
                "hit_rate": len(beat) / n_p if n_p else None,
                "by_ticker": {s: ret(s, day, end) for s in passed},
            }
        results.append(out)

    report = {"benchmark": args.benchmark, "prices_through": last_day.isoformat(), "runs": results, "warnings": warnings}
    if args.json:
        print(json.dumps(report, indent=2, default=str))
        return

    def pct(x):
        return "  n/a" if x is None else f"{x * 100:+.1f}%"

    print(f"Forward returns vs {args.benchmark}, prices through {last_day} (equal-weight, dividends included)\n")
    print(f"{'Run':<11}{'Screen':<12}{'Period':<10}{'Days':>5}{'Pass':>6}{'Passers':>9}{'Bench':>8}{'Excess':>8}"
          f"{'BuyZone':>9}{'NonPass':>9}{'Spread':>8}{'Hit':>6}")
    for r in results:
        run_day = date.fromisoformat(r["run"])
        for name, p in r["periods"].items():
            days = (date.fromisoformat(p["end"]) - run_day).days
            hit = "  n/a" if p["hit_rate"] is None else f"{p['hit_rate'] * 100:.0f}%"
            print(f"{r['run']:<11}{r['template']:<12}{name:<10}{days:>5}{p['passers_n']:>6}{pct(p['passers']):>9}"
                  f"{pct(p['benchmark']):>8}{pct(p['passers_excess']):>8}{pct(p['buy_zone']):>9}"
                  f"{pct(p['non_passers']):>9}{pct(p['spread_vs_non_passers']):>8}{hit:>6}")
    n_runs = len({r["run"] for r in results})
    if n_runs < 3 or all((last_day - date.fromisoformat(r["run"])).days < 91 for r in results):
        print(f"\nOnly {n_runs} run(s), all under 3 months old: too little history to judge any screen yet.")
    for w in warnings:
        print(f"WARNING: {w}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot", help="archive the current results_*.csv files")
    s.add_argument("--results-dir", default=".")
    s.add_argument("--history-dir", default="screen_history")
    s.add_argument("--overwrite", action="store_true", help="replace an existing snapshot for the same date")
    e = sub.add_parser("evaluate", help="forward returns of every archived run")
    e.add_argument("--history-dir", default="screen_history")
    e.add_argument("--template", help="only this screen")
    e.add_argument("--benchmark", default="SPY")
    e.add_argument("--json", action="store_true")
    args = ap.parse_args()
    snapshot(args) if args.cmd == "snapshot" else evaluate(args)


if __name__ == "__main__":
    main()
