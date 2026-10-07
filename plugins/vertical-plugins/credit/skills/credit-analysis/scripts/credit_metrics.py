#!/usr/bin/env python3
"""
Credit metrics for a public issuer from Yahoo Finance statements: annual history plus LTM.

  python3 credit_metrics.py CHTR
  python3 credit_metrics.py CHTR MSFT F --json

Per period: revenue, EBITDA, interest, total debt (incl. leases as reported), cash, net debt, CFO, FFO (proxy),
capex, FCF, and the ratios Debt/EBITDA, Net debt/EBITDA, EBITDA/interest, EBIT/interest, FFO/debt, FCF/debt,
debt/capital, current ratio. LTM = last four quarters of flows with the latest quarter's balance sheet.

The leverage band maps Debt/EBITDA and FFO/debt to the financial-risk descriptors in S&P's corporate
methodology (standard volatility table). It is ONE input to a rating, not a rating: business risk,
modifiers, and group/government support are not considered.

Banks, insurers, and most other financials are not analyzed this way; the script warns and the ratios
are not meaningful for them.
"""
import argparse
import json
import math
import sys

# (descriptor, Debt/EBITDA upper bound, FFO/debt lower bound) -- S&P corporate methodology, standard volatility.
BANDS = [
    ("minimal", 1.5, 0.60),
    ("modest", 2.0, 0.45),
    ("intermediate", 3.0, 0.30),
    ("significant", 4.0, 0.20),
    ("aggressive", 5.0, 0.12),
    ("highly leveraged", math.inf, -math.inf),
]
FINANCIAL_SECTORS = {"Financial Services"}
NON_FINANCIAL_EXCEPTIONS = ("Asset Management", "Capital Markets", "Financial Data", "Credit Services")
# Industries where issuers often consolidate a captive finance arm (Ford Credit, Cat Financial, John Deere Financial).
CAPTIVE_FINANCE_INDUSTRIES = {"Auto Manufacturers", "Farm & Heavy Construction Machinery", "Recreational Vehicles",
                              "Auto & Truck Dealerships"}


def num(x):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(x) or math.isinf(x) else x


def pick(df, col, *names):
    for n in names:
        if n in df.index:
            v = num(df.loc[n, col])
            if v is not None:
                return v
    return None


def flows(is_, cf, col):
    """Flow items for one statement column (a fiscal year or a quarter)."""
    rev = pick(is_, col, "Total Revenue", "Operating Revenue")
    ebit = pick(is_, col, "EBIT", "Operating Income")
    da = pick(is_, col, "Reconciled Depreciation", "Depreciation And Amortization In Income Statement")
    ebitda = pick(is_, col, "EBITDA", "Normalized EBITDA")
    if ebitda is None and ebit is not None and da is not None:
        ebitda = ebit + da
    interest = pick(is_, col, "Interest Expense", "Interest Expense Non Operating")
    cfo = pick(cf, col, "Operating Cash Flow", "Cash Flow From Continuing Operating Activities")
    wc = pick(cf, col, "Change In Working Capital")
    capex = pick(cf, col, "Capital Expenditure", "Capital Expenditure Reported")
    return {
        "revenue": rev, "ebitda": ebitda, "ebit": ebit,
        "interest": abs(interest) if interest is not None else None,
        "cfo": cfo, "ffo": (cfo - wc) if cfo is not None and wc is not None else None,
        "capex": abs(capex) if capex is not None else None,
        "fcf": (cfo - abs(capex)) if cfo is not None and capex is not None else None,
    }


def balances(bs, col):
    debt = pick(bs, col, "Total Debt")
    if debt is None:
        parts = [pick(bs, col, "Long Term Debt And Capital Lease Obligation", "Long Term Debt"),
                 pick(bs, col, "Current Debt And Capital Lease Obligation", "Current Debt")]
        debt = sum(p for p in parts if p is not None) if any(p is not None for p in parts) else None
    cash = pick(bs, col, "Cash Cash Equivalents And Short Term Investments", "Cash And Cash Equivalents")
    return {
        "debt": debt, "leases": pick(bs, col, "Capital Lease Obligations"), "cash": cash,
        "net_debt": (debt - cash) if debt is not None and cash is not None else None,
        "current_debt": pick(bs, col, "Current Debt And Capital Lease Obligation", "Current Debt"),
        "equity": pick(bs, col, "Stockholders Equity", "Total Equity Gross Minority Interest"),
        "current_assets": pick(bs, col, "Current Assets"),
        "current_liabilities": pick(bs, col, "Current Liabilities"),
    }


def ratios(p):
    def div(a, b):
        return None if a is None or b is None or b == 0 else a / b
    r = {
        "debt_to_ebitda": div(p["debt"], p["ebitda"]) if (p["ebitda"] or 0) > 0 else None,
        "net_debt_to_ebitda": div(p["net_debt"], p["ebitda"]) if (p["ebitda"] or 0) > 0 else None,
        "ebitda_to_interest": div(p["ebitda"], p["interest"]),
        "ebit_to_interest": div(p["ebit"], p["interest"]),
        "ffo_to_debt": div(p["ffo"], p["debt"]),
        "fcf_to_debt": div(p["fcf"], p["debt"]),
        "debt_to_capital": div(p["debt"], (p["debt"] or 0) + (p["equity"] or 0)) if p["debt"] is not None else None,
        "current_ratio": div(p["current_assets"], p["current_liabilities"]),
        "cash_to_current_debt": div(p["cash"], p["current_debt"]),
    }
    r["band_debt_ebitda"] = band_by_leverage(r["debt_to_ebitda"], p["ebitda"])
    r["band_ffo_debt"] = band_by_ffo(r["ffo_to_debt"], p["debt"])
    return r


def band_by_leverage(x, ebitda):
    if ebitda is not None and ebitda <= 0:
        return "highly leveraged"  # negative EBITDA: leverage is undefined and as bad as it gets
    if x is None:
        return None
    if x <= 0:
        return "minimal"
    return next(name for name, hi, _ in BANDS if x < hi)


def band_by_ffo(x, debt):
    if debt is not None and debt == 0:
        return "minimal"
    if x is None:
        return None
    return next(name for name, _, lo in BANDS if x > lo)


def analyze(symbol):
    import yfinance as yf
    t = yf.Ticker(symbol)
    info = {}
    try:
        info = t.info or {}
    except Exception:
        pass
    is_, bs, cf = t.income_stmt, t.balance_sheet, t.cashflow
    qis, qbs, qcf = t.quarterly_income_stmt, t.quarterly_balance_sheet, t.quarterly_cashflow
    out = {"symbol": symbol.upper(), "name": info.get("longName") or info.get("shortName"),
           "sector": info.get("sector"), "industry": info.get("industry"),
           "currency": info.get("financialCurrency"), "periods": [], "warnings": []}
    financial = (info.get("sector") in FINANCIAL_SECTORS
                 and not str(info.get("industry", "")).startswith(NON_FINANCIAL_EXCEPTIONS))
    if info.get("industry") in CAPTIVE_FINANCE_INDUSTRIES:
        out["warnings"].append("may consolidate a captive finance arm whose debt funds customer loans; "
                               "deconsolidate it (segment data in the 10-K) before judging leverage")
    if financial:
        out["warnings"].append(f"{info.get('industry')}: leverage/coverage ratios are not meaningful for this kind "
                               "of financial; use capital, asset-quality and funding metrics instead")
    if is_ is None or is_.empty or bs is None or bs.empty:
        out["warnings"].append("no annual statements from Yahoo Finance")
        return out

    # LTM: last four quarters of flows, latest quarter's balances
    if qis is not None and qcf is not None and qbs is not None and len(qis.columns) >= 4 and len(qcf.columns) >= 4 \
            and not qbs.empty:
        qs = [flows(qis, qcf, c) for c in list(qis.columns[:4])]
        ltm = {k: (sum(q[k] for q in qs) if all(q[k] is not None for q in qs) else None) for k in qs[0]}
        ltm.update(balances(qbs, qbs.columns[0]))
        ltm["period"] = f"LTM {qis.columns[0].date()}"
        out["periods"].append(ltm)
    else:
        out["warnings"].append("fewer than four quarters available; no LTM column")

    for col in [c for c in is_.columns if c in bs.columns and c in cf.columns]:
        if out["periods"] and out["periods"][0]["period"] == f"LTM {col.date()}":
            out["periods"][0]["period"] = f"FY {col.date()}"  # LTM ends on a fiscal year-end: same numbers
            continue
        p = flows(is_, cf, col)
        p.update(balances(bs, col))
        p["period"] = f"FY {col.date()}"
        out["periods"].append(p)
    for p in out["periods"]:
        p.update(ratios(p))
        if financial:
            p["band_debt_ebitda"] = p["band_ffo_debt"] = None
    if out["periods"] and not financial and out["periods"][0]["band_debt_ebitda"] != out["periods"][0]["band_ffo_debt"]:
        out["warnings"].append("Debt/EBITDA and FFO/debt point to different bands; S&P weighs the core ratios "
                               "together and supplements with others -- read both")
    return out


def fmt(v, kind):
    if v is None:
        return "n/a"
    if kind == "x":
        return f"{v:.1f}x"
    if kind == "%":
        return f"{v * 100:.0f}%"
    if kind == "$":
        return f"{v / 1e9:,.2f}B" if abs(v) >= 1e9 else f"{v / 1e6:,.0f}M"
    return str(v)


ROWS = [("Revenue", "revenue", "$"), ("EBITDA", "ebitda", "$"), ("Interest expense", "interest", "$"),
        ("Total debt", "debt", "$"), ("  of which leases", "leases", "$"), ("Cash + ST inv.", "cash", "$"),
        ("Net debt", "net_debt", "$"), ("CFO", "cfo", "$"), ("FFO (CFO - WC)", "ffo", "$"), ("Capex", "capex", "$"),
        ("FCF", "fcf", "$"), ("Debt / EBITDA", "debt_to_ebitda", "x"), ("Net debt / EBITDA", "net_debt_to_ebitda", "x"),
        ("EBITDA / interest", "ebitda_to_interest", "x"), ("EBIT / interest", "ebit_to_interest", "x"),
        ("FFO / debt", "ffo_to_debt", "%"), ("FCF / debt", "fcf_to_debt", "%"), ("Debt / capital", "debt_to_capital", "%"),
        ("Current ratio", "current_ratio", "x"), ("Cash / current debt", "cash_to_current_debt", "x"),
        ("Band (Debt/EBITDA)", "band_debt_ebitda", ""), ("Band (FFO/debt)", "band_ffo_debt", "")]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("symbols", nargs="+")
    ap.add_argument("--years", type=int, default=4, help="fiscal years to show after LTM (default 4)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    reports = []
    for s in args.symbols:
        try:
            r = analyze(s)
        except Exception as e:
            r = {"symbol": s.upper(), "periods": [], "warnings": [f"failed: {str(e)[:120]}"]}
        r["periods"] = r["periods"][: args.years + 1]
        reports.append(r)
    if args.json:
        print(json.dumps(reports, indent=2, default=str))
        return
    for r in reports:
        print(f"\n{r['symbol']}  {r.get('name') or ''}  ({r.get('sector') or '?'} / {r.get('industry') or '?'}, "
              f"{r.get('currency') or '?'})")
        if r["periods"]:
            print(f"{'':<22}" + "".join(f"{p['period']:>18}" for p in r["periods"]))
            for label, key, kind in ROWS:
                print(f"{label:<22}" + "".join(f"{fmt(p.get(key), kind):>18}" for p in r["periods"]))
        for w in r["warnings"]:
            print(f"WARNING: {w}")
    print("\nBands = S&P financial-risk descriptors (standard volatility) from core ratios only; not a credit rating.")


if __name__ == "__main__":
    main()
