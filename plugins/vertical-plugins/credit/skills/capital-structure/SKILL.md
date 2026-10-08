---
name: capital-structure
description: Build an issuer's capital structure table — every debt tranche by seniority and security with amount, coupon, maturity, and leverage through each tranche — plus the maturity wall and a recovery waterfall under a distressed enterprise value. Use when laying out a debt stack, assessing refinancing risk, or estimating recovery by tranche. Triggers on "cap table", "capital structure", "debt stack", "maturity wall", "maturity schedule", "recovery analysis", "waterfall", "where does this bond sit".
---

# Capital Structure

## Step 1: Gather the debt stack

Sources, in order of preference: the debt footnote in the latest 10-K/10-Q, the credit agreement and indentures, a lender presentation, or a connected data provider (S&P Capital IQ, LSEG). Yahoo Finance gives only totals, which is not enough here. Cite the source and as-of date for every line.

For each instrument capture:

- Name / CUSIP if available
- Type: revolver, term loan A/B, secured notes, unsecured notes, convertibles, preferred
- Seniority and security: 1st lien, 2nd lien, senior unsecured, subordinated; and which entity issued it (opco vs holdco)
- Amount outstanding, plus commitment and amount drawn for revolvers
- Coupon: fixed rate, or floating spread over SOFR with any floor
- Maturity, and any springing maturity
- Guarantors; call schedule if relevant

Also capture cash, operating leases if treated as debt, and market capitalization for public issuers.

## Step 2: Capital structure table

Order by priority of claim, top to bottom:

| Tranche | Security | Amount | Coupon | Maturity | x EBITDA (cumulative) | % of total debt |
|---|---|---|---|---|---|---|
| Revolver ($X committed) | 1L | drawn | S+xxx | | | |
| Term Loan B | 1L | | S+xxx | | | |
| Senior secured notes | 1L | | x.x% | | | |
| Senior unsecured notes | Unsecured | | x.x% | | | |
| **Total debt** | | | | | | |
| Less: cash | | | | | | |
| **Net debt** | | | | | | |
| Market cap / equity | | | | | | |
| **Enterprise value** | | | | | | |

Cumulative leverage "through" each tranche is the key column. It shows how much EBITDA coverage sits ahead of each lender.

Also show the weighted-average cost of debt, the floating share of total debt, and the weighted-average maturity.

## Step 3: Maturity wall

A year-by-year schedule for the next 5–7 years, including revolver expiry and scheduled amortization. Set it against:
- Cash on hand plus expected FCF per year (from `credit-analysis` or the user's model)
- Undrawn revolver availability, net of any springing covenant

Flag any year where maturities exceed cash plus FCF. Also flag a large maturity within 24 months when markets are tight or the issuer is in a weak leverage band. Note the refinancing math: what the new coupon would do to interest coverage.

## Step 4: Recovery waterfall (when asked, or when the credit is weak)

1. **Distressed EV:** apply a distressed multiple to a stressed EBITDA, and state both assumptions. Typical approach: EBITDA fall similar to the issuer's own worst downturn or a peer default, at a multiple at or below the sector's trough trading multiple. Show a range, not a point.
2. **Deductions ahead of funded debt:** administrative and priority claims (commonly a few percent of EV), and any debt at subsidiaries that sits structurally ahead of holdco debt.
3. **Waterfall:** allocate EV down the stack by priority. Assume the revolver is fully drawn at default, since it usually is. Pari passu tranches share pro rata.
4. **Output:** recovery % per tranche at low, mid and high EV.

| Tranche | Claim | Recovery (low) | Recovery (mid) | Recovery (high) |
|---|---|---|---|---|

Unsecured lenders recover only after secured debt is covered, so their recovery is the most sensitive to the EV assumption. Say so when the range is wide.

## Caveats

- Liens, guarantees and baskets in the documents decide actual priority. A table built from footnotes is a first pass. Use `covenant-review` on the documents for anything that matters.
- Recovery analysis is scenario arithmetic, not a forecast of default.
- Market prices of bonds and loans, if available from a connector, show what the market thinks recovery will be. Compare them to your waterfall and explain any gap.
