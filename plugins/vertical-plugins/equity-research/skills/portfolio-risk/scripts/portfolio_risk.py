#!/usr/bin/env python3
"""
Risk report for a portfolio_state.json ({"cash": float, "positions": [{symbol, shares, avg_cost, last_price}]}).

  python3 portfolio_risk.py --state portfolio_state.json
  python3 portfolio_risk.py --state portfolio_state.json --results-dir .. --json
  python3 portfolio_risk.py --state portfolio_state.json --no-refresh      # offline: last_price only

Prints concentration, sector exposure, unrealized P/L, volatility, beta, VaR, drawdown,
correlated pairs, a beta stress test, and (with --results-dir) each holding's screener status.

History-based metrics apply TODAY's weights to the past period's returns. They describe how the
current mix would have behaved, not how the account actually performed.
"""
import argparse
import glob
import json
import math
import os
import sys

STRESS_MOVES = (-0.10, -0.20, -0.30)
HIGH_CORR = 0.70


def load_state(path):
    with open(path) as f:
        data = json.load(f)
    if not isinstance(data, dict) or "positions" not in data:
        sys.exit(f"{path}: expected an object with 'cash' and 'positions'")
    positions = [p for p in data["positions"] if float(p.get("shares", 0)) > 0]
    return float(data.get("cash", 0)), positions


def load_screens(results_dir):
    """{ticker: {template: row}} from results_<template>.csv files."""
    import pandas as pd
    out = {}
    for path in sorted(glob.glob(os.path.join(results_dir, "results_*.csv"))):
        tpl = os.path.basename(path)[len("results_"):-len(".csv")]
        for _, r in pd.read_csv(path).iterrows():
            out.setdefault(str(r["ticker"]).upper(), {})[tpl] = r
    return out


def fetch_history(symbols, benchmark, period):
    import yfinance as yf
    tickers = list(dict.fromkeys(symbols + [benchmark]))
    df = yf.download(tickers, period=period, auto_adjust=True, progress=False)["Close"]
    if hasattr(df, "to_frame") and not hasattr(df, "columns"):
        df = df.to_frame(tickers[0])
    return df.dropna(how="all")


def fetch_info(symbols):
    import yfinance as yf
    info = {}
    for s in symbols:
        try:
            i = yf.Ticker(s).info
            info[s] = {"sector": i.get("sector"), "beta": i.get("beta")}
        except Exception:
            info[s] = {"sector": None, "beta": None}
    return info


def pct(x):
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x * 100:.1f}%"


def money(x):
    return "n/a" if x is None else f"{'-' if x < 0 else ''}${abs(x):,.0f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state", required=True, help="path to portfolio_state.json")
    ap.add_argument("--results-dir", help="folder with screener results_<template>.csv files")
    ap.add_argument("--benchmark", default="SPY")
    ap.add_argument("--period", default="1y", help="history window for vol/VaR/drawdown (yfinance period, default 1y)")
    ap.add_argument("--no-refresh", action="store_true", help="skip network calls; use last_price from the state file")
    ap.add_argument("--json", action="store_true", help="print JSON instead of a text report")
    args = ap.parse_args()

    cash, positions = load_state(args.state)
    symbols = [p["symbol"].upper() for p in positions]
    screens = load_screens(args.results_dir) if args.results_dir else {}
    report = {"state": os.path.abspath(args.state), "benchmark": args.benchmark, "period": args.period,
              "prices": "last_price from state file" if args.no_refresh else "latest close (yfinance)",
              "warnings": []}

    hist, info = None, {}
    if not args.no_refresh and symbols:
        try:
            hist = fetch_history(symbols, args.benchmark, args.period)
            info = fetch_info(symbols)
        except Exception as e:
            report["warnings"].append(f"price download failed ({str(e)[:80]}); fell back to last_price")
            report["prices"] = "last_price from state file"

    # --- holdings
    rows = []
    for p in positions:
        s = p["symbol"].upper()
        price = float(p.get("last_price") or 0)
        if hist is not None and s in hist.columns and hist[s].notna().any():
            price = float(hist[s].dropna().iloc[-1])
        elif hist is not None:
            report["warnings"].append(f"{s}: no price history; used last_price {price}")
        shares, cost = float(p["shares"]), float(p.get("avg_cost") or 0)
        sector = info.get(s, {}).get("sector")
        if not sector and s in screens:
            sector = next((str(r["sector"]) for r in screens[s].values() if str(r.get("sector")) != "nan"), None)
        rows.append({"symbol": s, "shares": shares, "price": price, "value": shares * price,
                     "avg_cost": cost, "unrealized_pl": shares * (price - cost),
                     "unrealized_pl_pct": (price / cost - 1) if cost else None,
                     "sector": sector or "Unknown", "beta": info.get(s, {}).get("beta")})
    invested = sum(r["value"] for r in rows)
    equity = invested + cash
    for r in rows:
        r["weight"] = r["value"] / equity if equity else 0
        r["weight_of_invested"] = r["value"] / invested if invested else 0
    rows.sort(key=lambda r: -r["value"])

    report["totals"] = {"equity": equity, "invested": invested, "cash": cash,
                        "cash_pct": cash / equity if equity else 0,
                        "unrealized_pl": sum(r["unrealized_pl"] for r in rows), "positions": len(rows)}
    report["holdings"] = rows

    # --- concentration
    w = [r["weight_of_invested"] for r in rows]
    hhi = sum(x * x for x in w)
    report["concentration"] = {"top1": rows[0]["weight"] if rows else 0,
                               "top3": sum(r["weight"] for r in rows[:3]),
                               "hhi_invested": hhi, "effective_positions": (1 / hhi) if hhi else 0}
    sectors = {}
    for r in rows:
        sectors[r["sector"]] = sectors.get(r["sector"], 0) + r["weight"]
    report["sectors"] = dict(sorted(sectors.items(), key=lambda kv: -kv[1]))

    # --- history-based risk
    if hist is not None and len(hist) > 20:
        rets = hist.pct_change().dropna(how="all")
        held = [r["symbol"] for r in rows if r["symbol"] in rets.columns]
        weights = {r["symbol"]: r["weight"] for r in rows}
        port = sum(rets[s].fillna(0) * weights[s] for s in held)  # cash earns 0
        bench = rets[args.benchmark] if args.benchmark in rets.columns else None
        vol = float(port.std() * math.sqrt(252))
        beta = None
        if bench is not None and bench.var() > 0:
            beta = float(port.cov(bench) / bench.var())
        nav = (1 + port).cumprod()
        mdd = float((nav / nav.cummax() - 1).min())
        var95 = float(-port.quantile(0.05))
        corr = rets[held].corr() if len(held) > 1 else None
        pairs = []
        if corr is not None:
            for i, a in enumerate(held):
                for b in held[i + 1:]:
                    c = corr.loc[a, b]
                    if c >= HIGH_CORR:
                        pairs.append({"pair": f"{a}/{b}", "corr": float(c)})
        inv_frac = invested / equity if equity else 0
        report["risk"] = {"days": int(len(port)), "annual_vol": vol, "beta": beta,
                          "annual_vol_invested": vol / inv_frac if inv_frac else None,
                          "beta_invested": beta / inv_frac if beta is not None and inv_frac else None,
                          "var95_1d_pct": var95, "var95_1d_usd": var95 * equity,
                          "max_drawdown": mdd, "return_over_period": float(nav.iloc[-1] - 1),
                          "high_corr_pairs": sorted(pairs, key=lambda x: -x["corr"])}
        if beta is not None:
            report["stress"] = [{"benchmark_move": m, "est_pl_usd": m * beta * equity, "est_pl_pct": m * beta}
                                for m in STRESS_MOVES]
    elif not args.no_refresh:
        report["warnings"].append("not enough price history for vol/VaR/drawdown")

    # --- screener status
    if screens:
        status = {}
        for r in rows:
            s = r["symbol"]
            per = screens.get(s)
            if not per:
                status[s] = {"in_universe": False}
                continue
            flags = set()
            for row in per.values():
                for c in str(row.get("failed_checks") or "").split(";"):
                    if c.strip().startswith("flag:"):
                        flags.add(c.strip())
            status[s] = {"in_universe": True,
                         "passes": [t for t, row in per.items() if bool(row["passed"])],
                         "red_flags": sorted(flags),
                         "margin_of_safety": next((float(row["margin_of_safety"]) for row in per.values()
                                                   if str(row.get("margin_of_safety")) != "nan"), None)}
        report["screens"] = status

    if args.json:
        print(json.dumps(report, indent=2, default=str))
        return

    t = report["totals"]
    print(f"Portfolio {report['state']}  (prices: {report['prices']})")
    print(f"Equity {money(t['equity'])} = invested {money(t['invested'])} + cash {money(t['cash'])} ({pct(t['cash_pct'])})"
          f"   unrealized P/L {money(t['unrealized_pl'])}\n")
    print(f"{'Symbol':<8}{'Shares':>8}{'Price':>10}{'Value':>12}{'Weight':>8}{'P/L %':>8}  Sector")
    for r in rows:
        print(f"{r['symbol']:<8}{r['shares']:>8g}{r['price']:>10.2f}{money(r['value']):>12}{pct(r['weight']):>8}"
              f"{pct(r['unrealized_pl_pct']):>8}  {r['sector']}")
    c = report["concentration"]
    print(f"\nConcentration: top1 {pct(c['top1'])}, top3 {pct(c['top3'])}, effective positions {c['effective_positions']:.1f}")
    print("Sectors: " + ", ".join(f"{k} {pct(v)}" for k, v in report["sectors"].items()))
    if "risk" in report:
        k = report["risk"]
        print(f"\nCurrent weights over the last {k['days']} trading days vs {args.benchmark}:")
        beta_txt = "" if k["beta"] is None else f", beta {k['beta']:.2f} (stocks only {k['beta_invested']:.2f})"
        print(f"  annual vol {pct(k['annual_vol'])} (stocks only {pct(k['annual_vol_invested'])}){beta_txt}")
        print(f"  1-day 95% VaR {pct(k['var95_1d_pct'])} ({money(k['var95_1d_usd'])}), max drawdown {pct(k['max_drawdown'])}")
        if k["high_corr_pairs"]:
            print("  highly correlated: " + ", ".join(f"{p['pair']} {p['corr']:.2f}" for p in k["high_corr_pairs"]))
    for s in report.get("stress", []):
        print(f"  {args.benchmark} {pct(s['benchmark_move'])} -> est. {money(s['est_pl_usd'])} ({pct(s['est_pl_pct'])})")
    if screens:
        print("\nScreener status:")
        for sym, st in report["screens"].items():
            if not st["in_universe"]:
                print(f"  {sym:<7} not in the screener universe")
            else:
                print(f"  {sym:<7} passes: {', '.join(st['passes']) or 'none'}"
                      f"{'   flags: ' + '; '.join(st['red_flags']) if st['red_flags'] else ''}")
    for wmsg in report["warnings"]:
        print(f"WARNING: {wmsg}")


if __name__ == "__main__":
    main()
