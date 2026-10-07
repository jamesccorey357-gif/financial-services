---
name: covenant-review
description: Extract and summarize the covenants in a credit agreement or bond indenture — financial maintenance tests with current headroom, incurrence tests, negative covenants and their baskets, EBITDA definition add-backs, events of default, and lender-protection gaps. Use when reviewing loan or bond documents, checking covenant compliance or headroom, or assessing how much a borrower can lever up, move assets, or pay out. Triggers on "covenant review", "covenant headroom", "credit agreement", "indenture", "baskets", "is the borrower in compliance", "covenant-lite", "what can the borrower do".
---

# Covenant Review

Input: the credit agreement, indenture, amendments, and (for headroom) the latest compliance certificate or financials. Work only from the documents provided. Cite the section number for every term. If a document references another that isn't provided (e.g. an intercreditor agreement), say so rather than assuming its contents.

## Step 1: Document map

- Parties: borrower, guarantors, agent or trustee, and the restricted vs unrestricted subsidiary designation
- Facilities and amounts, maturity, pricing grid
- Amendments in effect, and what each changed

## Step 2: Defined terms that drive everything

Read these first. They decide how much every covenant actually restricts.

- **Consolidated EBITDA:** list every add-back. Flag uncapped add-backs: projected cost savings and synergies, "run-rate" adjustments, restructuring charges, and look-back or look-forward periods. Quantify the cap if one exists (e.g. "synergies capped at 25% of EBITDA").
- **Consolidated Total Debt / Indebtedness:** what is excluded (e.g. leases, letters of credit, earn-outs).
- **Net debt cash netting:** unlimited, or capped?
- **Restricted vs Unrestricted Subsidiaries:** the conditions for moving a subsidiary or asset out of the lender group.

## Step 3: Financial covenants

**Maintenance** covenants are tested every quarter regardless of activity. **Incurrence** covenants are tested only when the borrower takes an action (borrows, pays a dividend, makes an acquisition).

| Covenant | Type | Level (step-downs) | Test date / frequency | Current | Headroom |
|---|---|---|---|---|---|
| Max total net leverage | Maintenance | e.g. 4.50x → 4.00x | Quarterly | x.xx | |
| Min interest coverage | Maintenance | | | | |
| Springing revolver test | Springing at X% drawn | | | | |

Headroom has two parts. Show both:
- **Ratio headroom:** covenant level vs current.
- **EBITDA cushion:** how far EBITDA can fall before a breach, holding debt constant, = 1 − (current leverage ÷ covenant level). For coverage tests, apply the same logic to interest.

Note any equity cure rights: how many, how often, and whether a cure can be used to pay down debt. Note any covenant holidays.

**Covenant-lite:** if there is no maintenance test (common in term loan B and high-yield bonds), say so up front. Lenders then rely only on incurrence tests and events of default.

## Step 4: Negative covenants and baskets

For each, state the general prohibition, then every basket and its size. Fixed-dollar baskets, "greater of $X and Y% of EBITDA" growers, and builder or available-amount baskets all matter:

- **Debt incurrence:** ratio debt capacity, general basket, incremental/accordion (free-and-clear amount plus ratio-based)
- **Liens:** general basket, and any ability to prime existing lenders
- **Restricted payments:** dividends, buybacks, the builder basket and its starting amount
- **Investments**, including in unrestricted subsidiaries. Flag the "J.Crew" trapdoor risk where IP or other valuable assets can be moved out.
- **Asset sales:** reinvestment rights vs mandatory prepayment, sweep percentages
- **Affiliate transactions; changes in business**

Where possible, total how much **additional debt** and **restricted payments** the borrower could make today under all baskets combined.

## Step 5: Lender-protection checklist

Flag each of these as present, absent, or partial, with the section cited:

- Anti-layering / anti-subordination (blocks "uptier" or "non-pro-rata" exchanges, e.g. Serta-style)
- Sacred rights requiring every affected lender's consent: pro rata sharing, release of all or most collateral or guarantors, payment waterfall
- J.Crew blocker (no transfer of material IP to unrestricted subsidiaries)
- Chewy blocker (guarantor not released just because a subsidiary becomes non-wholly-owned)
- Change of control: the trigger definition and the put price
- MFN protection on incremental debt: the spread cushion and its sunset

## Step 6: Events of default

Payment default and grace periods, cross-default vs cross-acceleration and their thresholds, judgment default threshold, change of control, and going-concern qualification if included.

## Output

1. **Summary:** a 5–8 line read. How tight is the package, what is the current headroom, what is the biggest lender-protection gap?
2. The financial covenant table with headroom.
3. The baskets table, with total incremental debt and RP capacity.
4. The lender-protection checklist.
5. Open questions: missing documents and ambiguous drafting.

This is a document summary to support review by counsel, not a legal opinion. Say so when the user is making a decision that turns on interpretation of a provision.
