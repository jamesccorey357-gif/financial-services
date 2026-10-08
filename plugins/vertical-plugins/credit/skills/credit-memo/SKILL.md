---
name: credit-memo
description: Write a credit memo on a corporate issuer or a specific debt instrument — recommendation framing, business and financial risk, capital structure, covenants, downside case, relative value, and monitoring triggers — pulling from credit-analysis, capital-structure, and covenant-review. Use for credit committee papers, new-issue reviews, annual credit reviews, or bond and loan investment write-ups. Triggers on "credit memo", "credit committee", "write up this credit", "new issue review", "annual review", "should we lend to", "bond write-up".
---

# Credit Memo

## Step 1: Scope

Confirm with the user:
- **Purpose:** lending decision (bank or direct lending), investment in a bond or loan (asset manager), or annual review of an existing exposure
- **Instrument(s):** a specific tranche, or the issuer as a whole
- **Audience and length:** committee paper (5–10 pages) or a one-page summary
- **House template:** if the user's firm has one, follow it exactly. Otherwise use the structure below.

## Step 2: Do the analysis

Run the underlying skills rather than redoing their work:

1. `credit-analysis`: metrics, financial-risk band, business risk, and upgrade and downgrade triggers
2. `capital-structure`: debt stack, maturity wall, and recovery for the instrument in question
3. `covenant-review`: only if documents are provided. Otherwise note that the covenant package was not reviewed.

Add:

- **Downside case:** a stress scenario tied to something real, such as the issuer's own worst year, a peer's experience, or a named risk like losing a major customer. Show leverage, coverage, liquidity runway and covenant headroom at the trough, and whether the instrument is still covered on recovery.
- **Relative value** (investment memos only, and only with market data from a connector or from the user): yield or spread versus comparable issuers in the same band and sector, adjusted for seniority and tenor. For bond pricing and curve context, the LSEG `bond-relative-value` skill can supply the numbers if that partner plugin is installed.

## Step 3: Memo structure

1. **Summary and recommendation framing.** The request (amount, instrument, tenor, pricing), the 3–4 key credit strengths and risks, and the proposed decision **for the committee to make**. Phrase it as "the analysis supports…" or "key conditions would be…", never as a decision taken.
2. **Issuer overview:** business, scale, ownership, sponsor if any.
3. **Business risk:** industry, competitive position, cyclicality, management and financial policy.
4. **Financial risk:** the metrics table (3–5 years plus LTM), trend commentary, and the financial-risk band.
5. **Capital structure and liquidity:** the table, the maturity wall, and sources vs uses.
6. **Structure and documentation:** security, guarantees, covenant summary and headroom, and lender-protection gaps.
7. **Downside case and recovery.**
8. **Relative value** (if applicable).
9. **Key risks and mitigants:** a table pairing each risk with its mitigant and with what would show it is happening.
10. **Monitoring:** specific, measurable triggers for re-review (covenant headroom under X%, leverage over Y, a refinancing not done by a set date, a rating action).

## Writing standards

- Every number gets a source and period. Separate reported figures from adjusted ones, and list the adjustments.
- Lead every section with the conclusion, then the support.
- Give the risks as much space as the strengths. A memo that reads like a pitch fails its purpose.
- Don't state agency ratings or market prices that aren't from a cited source.
- Draft only. The memo supports a credit decision by authorized people. It does not approve credit or recommend a trade.

## Output

A Word document if the user wants a file, or markdown in chat for a quick review. Put the metrics and capital structure tables in an appendix workbook (`xlsx-author`) if they run long.
