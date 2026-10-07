---
description: Score a parsed KYC record against the rules grid
argument-hint: "[client or investor name]"
---

Load the `kyc-rules` skill to risk-rate the parsed record, list every rule outcome with the rule cited, and route anything missing or escalation-worthy.

Use the record from the latest `/kyc-parse` output if there is one. Otherwise ask the user for the parsed record or run `kyc-doc-parse` first. This scores and routes; it does not approve onboarding.
