---
name: credit-analysis
description: Fundamental credit analysis of a corporate issuer — leverage, interest coverage, cash-flow-to-debt, liquidity, and trend, benchmarked to S&P financial-risk bands, with a business-risk read and the factors that would move the credit up or down. Use when assessing an issuer's creditworthiness, checking a company's balance sheet strength, or screening equity holdings for credit risk. Triggers on "credit analysis", "how levered is", "can X service its debt", "credit profile", "leverage and coverage", "balance sheet risk", "is X investment grade".
---

# Credit Analysis

Answer one question: can this issuer meet its debt obligations through the cycle, and how much cushion does it have? Equity analysis asks how much upside there is. Credit analysis asks what has to go wrong for lenders to lose money.

## Step 1: Pull the numbers

For a public issuer, run the bundled script. It reads Yahoo Finance statements and prints LTM plus annual history:

```bash
python3 <this skill's directory>/scripts/credit_metrics.py <TICKER> [<TICKER> ...] [--years 4] [--json]
```

For private issuers, or when the user provides financials (CIM, lender model, compliance certificate), compute the same metrics from their numbers instead, and say which source you used. Prefer filings or provided financials over Yahoo whenever they disagree. Yahoo's EBITDA is unadjusted, and its "Total Debt" usually includes leases.

The script warns on two cases where the standard ratios mislead:
- **Financials** (banks, insurers). Leverage and coverage don't apply. Say so and stop, unless the user wants a capital, asset-quality and funding review instead.
- **Captive finance arms** (autos, heavy equipment). Consolidated debt includes loans that fund customer receivables. Deconsolidate the finance subsidiary using the segment note before judging leverage.

## Step 2: Core metrics

| Metric | What it tells you | Watch for |
|---|---|---|
| Debt / EBITDA, net debt / EBITDA | Years of earnings to repay debt | Trend over 3+ years; net vs gross gap (is the cash trapped offshore or needed for operations?) |
| EBITDA / interest, EBIT / interest | Cushion over interest cost | Floating-rate debt resetting higher; EBIT coverage under 2x |
| FFO / debt, FCF / debt | Cash generation against the debt load | FCF/debt much lower than FFO/debt means capex or dividends absorb the cash |
| Debt / capital | Balance-sheet leverage | Negative equity from buybacks makes this meaningless; say so |
| Liquidity | Cash + undrawn revolver vs. debt due in 12–24 months | Current ratio under 1 with large near-term maturities |

Map Debt/EBITDA and FFO/debt to the S&P financial-risk descriptors the script prints (minimal → highly leveraged). When the two disagree, report both and explain why (e.g. heavy working-capital swings, high interest burden).

**Adjustments to consider**, stated explicitly when made:
- Add operating leases if not already in debt; add unfunded pension deficits (after tax) for heavy-pension issuers.
- Strip one-offs from EBITDA only with a cited reason. Management's "adjusted EBITDA" add-backs are the most common way leverage gets understated.
- Count hybrid and preferred instruments per their terms. Don't treat them as equity by default.

## Step 3: Business risk

The financial ratios are half the picture. Assess, briefly and with evidence:
- **Cyclicality:** how far did EBITDA fall in the last downturn? Use peak-to-trough from history if available.
- **Competitive position:** scale, market share, pricing power, diversification by product, customer and geography.
- **Profitability and volatility:** margin level versus peers, and how stable it is.
- **Financial policy:** buybacks, dividends, M&A appetite, stated leverage target, and any ownership by a sponsor or controlling holder. A clean balance sheet with an aggressive policy will not stay clean.

A strong business tolerates more leverage at the same rating. Say where the business sits on that spectrum and why.

## Step 4: Debt service and liquidity

- **Maturity wall:** debt due each year for the next 5 years, against FCF plus cash. Use `capital-structure` for the full schedule.
- **Rate sensitivity:** share of debt that is floating, and what a 200bp move does to coverage.
- **Sources vs uses** over 12–24 months: cash, FCF and revolver availability against maturities, capex commitments and dividends.
- **Covenants:** headroom on maintenance tests if there are any. Use `covenant-review` for the documents.

## Step 5: Conclusion

- **Credit view:** one paragraph on the financial-risk band, the business-risk read, and the direction of travel (improving, stable, deteriorating), with the 2–3 numbers that matter most.
- **What would change it:** specific upgrade and downgrade triggers, e.g. "Debt/EBITDA above 5x for two quarters" or "refinancing the 2027 notes at more than 9%".
- **Peer table** if the user gives peers. Run the script on all of them in one call.

Never state or imply an agency rating unless it comes from a cited source (filing, rating-agency publication, or a connected data provider). The bands are a financial-risk indicator, not a rating.

## Tie-in for equity users

For holdings from `stock-screener` or `portfolio-risk`, a credit check is a quick sanity test of the balance sheet. Flag any holding in the "aggressive" or "highly leveraged" band, or with interest coverage under 3x. Equity is the first loss when credit weakens.
