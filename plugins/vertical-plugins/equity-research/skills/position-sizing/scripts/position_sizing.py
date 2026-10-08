#!/usr/bin/env python3
"""
Size a screener shortlist into whole-share target positions for a portfolio_state.json.

  python3 position_sizing.py --state portfolio_state.json --results-dir .
  python3 position_sizing.py --state portfolio_state.json --results-dir . --screens quality,value --method score
  python3 position_sizing.py --state portfolio_state.json --tickers MSFT,ADBE,QCOM --method inverse-vol

Candidates are the passers in results_<template>.csv (or --tickers). Holdings that are not candidates
are left as they are unless --sell-unlisted. Targets respect a per-name cap, a tighter cap for names
that pass only the speculative screen, a sector cap (counting holdings you keep), and a cash reserve.
Money the caps won't let you deploy stays in cash.

Output is a PROPOSED order list. It never edits the state file or places orders.
"""
import argparse
import glob
import json
import math
import os
import sys


def load_state(path):
    with open(path) as f:
        data = json.load(f)
    if not isinstance(data, dict) or "positions" not in data:
        sys.exit(f"{path}: expected an object with 'cash' and 'positions'")
    held = {p["symbol"].upper(): p for p in data["positions"] if float(p.get("shares", 0)) > 0}
    return float(data.get("cash", 0)), held


def load_universe(results_dir):
    """{ticker: {sector, price}} for every row in any results_<template>.csv, passed or not."""
    import pandas as pd
    out = {}
    for path in sorted(glob.glob(os.path.join(results_dir, "results_*.csv"))):
        for _, r in pd.read_csv(path).iterrows():
            u = out.setdefault(str(r["ticker"]).upper(), {"sector": None, "price": None})
            if not pd.isna(r["sector"]):
                u["sector"] = str(r["sector"])
            if not pd.isna(r["price"]):
                u["price"] = float(r["price"])
    return out


def load_candidates(results_dir, screens):
    """{ticker: {screens, score, mos, buy_zone, sector, price}} for every passer in the chosen screens."""
    import pandas as pd
    out = {}
    for path in sorted(glob.glob(os.path.join(results_dir, "results_*.csv"))):
        tpl = os.path.basename(path)[len("results_"):-len(".csv")]
        if screens and tpl not in screens:
            continue
        df = pd.read_csv(path)
        for _, r in df[df["passed"] == True].iterrows():  # noqa: E712 -- pandas bool column
            t = str(r["ticker"]).upper()
            c = out.setdefault(t, {"screens": [], "score": 0, "mos": None, "buy_zone": False,
                                   "sector": None, "price": None})
            c["screens"].append(tpl)
            c["score"] = max(c["score"], float(r["score"]))
            if not pd.isna(r["margin_of_safety"]):
                c["mos"] = float(r["margin_of_safety"])
            c["buy_zone"] = c["buy_zone"] or r["buy_zone"] is True or str(r["buy_zone"]) == "True"
            if not pd.isna(r["sector"]):
                c["sector"] = str(r["sector"])
            if not pd.isna(r["price"]):
                c["price"] = float(r["price"])
    return out


def market_data(symbols, period="1y"):
    """(last close, annualized vol, sector) per symbol from yfinance."""
    import yfinance as yf
    df = yf.download(symbols, period=period, auto_adjust=True, progress=False)["Close"]
    if not hasattr(df, "columns"):
        df = df.to_frame(symbols[0])
    out = {}
    for s in symbols:
        sector = None
        try:
            sector = yf.Ticker(s).info.get("sector")
        except Exception:
            pass
        col = df[s].dropna() if s in df.columns else None
        if col is None or col.empty:
            out[s] = {"price": None, "vol": None, "sector": sector}
            continue
        r = col.pct_change().dropna()
        out[s] = {"price": float(col.iloc[-1]), "vol": float(r.std() * math.sqrt(252)) if len(r) > 20 else None,
                  "sector": sector}
    return out


def allocate(raw, caps, sector_of, sector_room, budget, start):
    """Water-fill `budget` on top of `start` in proportion to `raw`, never exceeding a name's cap or its sector's room."""
    alloc = {t: start.get(t, 0.0) for t in raw}
    free = {t for t in raw if raw[t] > 0 and alloc[t] < caps[t]}
    remaining = budget
    for _ in range(100):
        if remaining <= 0.01 or not free:
            break
        total = sum(raw[t] for t in free)
        add = {t: remaining * raw[t] / total for t in free}
        # name caps
        for t in list(free):
            if alloc[t] + add[t] >= caps[t]:
                add[t] = caps[t] - alloc[t]
                free.discard(t)
        # sector caps
        for sec in {sector_of[t] for t in add}:
            names = [t for t in add if sector_of[t] == sec]
            used = sum(alloc[t] for t in raw if sector_of[t] == sec)
            room = sector_room[sec] - used
            want = sum(add[t] for t in names)
            if want > room:
                scale = max(room, 0) / want if want else 0
                for t in names:
                    add[t] *= scale
                    free.discard(t)
        for t, v in add.items():
            alloc[t] += v
        remaining -= sum(add.values())
    return alloc


def pct(x):
    return f"{x * 100:.1f}%"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state", required=True, help="path to portfolio_state.json")
    ap.add_argument("--results-dir", default=".", help="folder with screener results_<template>.csv files")
    ap.add_argument("--screens", help="comma list of screens to draw candidates from (default: all)")
    ap.add_argument("--tickers", help="comma list of candidates; overrides the screener passers")
    ap.add_argument("--method", choices=["equal", "score", "inverse-vol"], default="equal")
    ap.add_argument("--max-position", type=float, default=0.10, help="max weight per name (default 0.10)")
    ap.add_argument("--spec-cap", type=float, default=0.03, help="max weight for speculative-only names (default 0.03)")
    ap.add_argument("--max-sector", type=float, default=0.30, help="max weight per sector (default 0.30)")
    ap.add_argument("--cash-reserve", type=float, default=0.05, help="weight kept in cash (default 0.05)")
    ap.add_argument("--max-names", type=int, default=15, help="max number of candidates to size (default 15)")
    ap.add_argument("--sell-unlisted", action="store_true", help="target 0 for holdings that are not candidates")
    ap.add_argument("--rebalance", action="store_true",
                    help="resize held candidates from scratch (may trim them); default only trims above a cap")
    ap.add_argument("--no-refresh", action="store_true", help="skip network calls; use CSV / state prices")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if args.method == "inverse-vol" and args.no_refresh:
        sys.exit("--method inverse-vol needs price history; drop --no-refresh")

    cash, held = load_state(args.state)
    screens = [s.strip() for s in args.screens.split(",")] if args.screens else None
    cands = load_candidates(args.results_dir, screens) if not args.tickers else {}
    if args.tickers:
        known = load_candidates(args.results_dir, None) if glob.glob(os.path.join(args.results_dir, "results_*.csv")) else {}
        for t in [x.strip().upper() for x in args.tickers.split(",") if x.strip()]:
            cands[t] = known.get(t, {"screens": [], "score": 0, "mos": None, "buy_zone": False, "sector": None, "price": None})
    if not cands:
        sys.exit("no candidates: no passers in the chosen results files and no --tickers given")
    ranked = sorted(cands, key=lambda t: (not cands[t]["buy_zone"], -cands[t]["score"], -(cands[t]["mos"] or -9)))
    dropped = ranked[args.max_names:]
    cands = {t: cands[t] for t in ranked[:args.max_names]}

    warnings = []
    symbols = sorted(set(cands) | set(held))
    md = {}
    if not args.no_refresh:
        try:
            md = market_data(symbols)
        except Exception as e:
            warnings.append(f"market data download failed ({str(e)[:80]}); using CSV / state prices")

    universe = load_universe(args.results_dir)

    def price_of(t):
        p = (md.get(t, {}).get("price") or cands.get(t, {}).get("price") or universe.get(t, {}).get("price")
             or float(held.get(t, {}).get("last_price") or 0))
        return p or None

    def sector_of(t):
        return (md.get(t, {}).get("sector") or cands.get(t, {}).get("sector") or universe.get(t, {}).get("sector")
                or "Unknown")

    price = {t: price_of(t) for t in symbols}
    for t in [t for t in cands if not price[t]]:
        warnings.append(f"{t}: no price; skipped")
        del cands[t]
    held_value = {t: float(held[t]["shares"]) * (price[t] or 0) for t in held}
    equity = cash + sum(held_value.values())

    kept = {t for t in held if t not in cands and not args.sell_unlisted}
    investable = equity * (1 - args.cash_reserve) - sum(held_value[t] for t in kept)

    if args.method == "equal":
        raw = {t: 1.0 for t in cands}
    elif args.method == "score":
        raw = {t: max(c["score"], 1) / 100 * (1 + min(max(c["mos"] or 0, 0), 0.5)) for t, c in cands.items()}
    else:
        raw = {}
        for t in cands:
            v = md.get(t, {}).get("vol")
            if v:
                raw[t] = 1 / v
            else:
                warnings.append(f"{t}: no volatility history; skipped")
    spec_only = {t for t, c in cands.items() if c["screens"] == ["speculative"]}
    caps = {t: equity * (args.spec_cap if t in spec_only else args.max_position) for t in raw}
    sectors = {t: sector_of(t) for t in symbols}
    sector_room = {}
    for sec in set(sectors.values()):
        sector_room[sec] = equity * args.max_sector - sum(held_value[t] for t in kept if sectors[t] == sec)
    # Held candidates start at their current value (trimmed to the name cap) unless --rebalance.
    start = {} if args.rebalance else {t: min(held_value[t], caps[t]) for t in raw if t in held}
    for t in sorted(start, key=lambda t: -start[t]):  # a sector already over its cap trims its holdings pro rata
        sec = sectors[t]
        over = sum(start[x] for x in start if sectors[x] == sec) - sector_room[sec]
        if over > 0:
            names = [x for x in start if sectors[x] == sec]
            total = sum(start[x] for x in names)
            for x in names:
                start[x] -= over * start[x] / total
    budget = investable - sum(start.values())
    if budget <= 0:
        warnings.append("holdings already use the investable budget; nothing to buy")
        budget = 0
    alloc = allocate(raw, caps, sectors, sector_room, budget, start)

    rows = []
    for t in symbols:
        cur = int(float(held[t]["shares"])) if t in held else 0
        p = price[t]
        if t in kept:
            tgt, why = cur, "kept (not a candidate)"
        elif t in held and t not in cands:
            tgt, why = 0, "not a candidate (--sell-unlisted)"
        elif t not in raw:
            continue
        else:
            tgt = int(alloc[t] // p)
            notes = []
            if alloc[t] >= caps[t] - 0.01:
                notes.append("spec cap" if t in spec_only else "name cap")
            if sector_room.get(sectors[t], 0) - sum(alloc[x] for x in raw if sectors[x] == sectors[t]) <= 0.01:
                notes.append("sector cap")
            why = ", ".join(notes)
        delta = tgt - cur
        rows.append({"ticker": t, "screens": cands.get(t, {}).get("screens", []), "sector": sectors[t],
                     "price": p, "current_shares": cur, "current_weight": cur * p / equity if equity else 0,
                     "target_shares": tgt, "target_weight": tgt * p / equity if equity else 0,
                     "order": "BUY" if delta > 0 else "SELL" if delta < 0 else "HOLD", "order_shares": abs(delta),
                     "order_value": delta * p, "note": why})
    rows.sort(key=lambda r: -r["target_weight"])
    cash_after = cash - sum(r["order_value"] for r in rows)
    sector_after = {}
    for r in rows:
        sector_after[r["sector"]] = sector_after.get(r["sector"], 0) + r["target_weight"]

    report = {"equity": equity, "cash_before": cash, "cash_after": cash_after,
              "cash_after_pct": cash_after / equity if equity else 0, "method": args.method,
              "limits": {"max_position": args.max_position, "spec_cap": args.spec_cap,
                         "max_sector": args.max_sector, "cash_reserve": args.cash_reserve},
              "orders": rows, "sectors_after": dict(sorted(sector_after.items(), key=lambda kv: -kv[1])),
              "not_sized": dropped, "warnings": warnings}
    if args.json:
        print(json.dumps(report, indent=2, default=str))
        return

    print(f"Equity ${equity:,.0f}, method {args.method}, caps: name {pct(args.max_position)}, spec {pct(args.spec_cap)}, "
          f"sector {pct(args.max_sector)}, cash reserve {pct(args.cash_reserve)}\n")
    print(f"{'Ticker':<7}{'Price':>9}{'Now':>6}{'Wt':>7}{'Target':>8}{'Wt':>7}  {'Order':<12}{'Value':>11}  Sector / note")
    for r in rows:
        order = "HOLD" if r["order"] == "HOLD" else f"{r['order']} {r['order_shares']}"
        print(f"{r['ticker']:<7}{r['price']:>9.2f}{r['current_shares']:>6}{pct(r['current_weight']):>7}"
              f"{r['target_shares']:>8}{pct(r['target_weight']):>7}  {order:<12}{r['order_value']:>11,.0f}  "
              f"{r['sector']}{' / ' + r['note'] if r['note'] else ''}")
    print(f"\nCash ${cash:,.0f} -> ${cash_after:,.0f} ({pct(report['cash_after_pct'])})")
    print("Sectors after: " + ", ".join(f"{k} {pct(v)}" for k, v in report["sectors_after"].items()))
    if dropped:
        print(f"Not sized (beyond --max-names {args.max_names}): {', '.join(dropped)}")
    for w in warnings:
        print(f"WARNING: {w}")
    print("\nProposed orders only. Nothing was placed and the state file was not changed.")


if __name__ == "__main__":
    main()
