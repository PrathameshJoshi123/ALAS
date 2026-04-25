---
name: supply-agreement-analysis
description: Use this skill to analyze supply agreements, supplier contracts, purchase and supply terms, and related commercial contracts. Extract key deal terms, identify favorable and unfavorable clauses, flag legal and commercial risks, and summarize the agreement the way an experienced contract lawyer would. IMPORTANT - This skill REQUIRES reading the Indian Contract Act before making red/green flag assessments.
license: MIT
compatibility: Requires text contract input. Works best with full agreement text, including exhibits, schedules, and appendices.
metadata:
  author: OpenAI
  version: "2.0"
  requires: indian_contract_law.md
allowed-tools: [read_file, write_file, edit_file, glob, grep, ls]
---

# supply-agreement-analysis

## Overview

This skill helps the agent read and analyze supply agreements like an expert commercial lawyer.

It should:

- extract all key commercial and legal information
- identify favorable clauses and unfavorable clauses
- flag missing provisions and hidden risks
- compare the agreement against standard market protections (including Indian Contract Act, 1872)
- explain issues in plain English with legal citations
- highlight negotiation points and fallback positions

The skill is for informational contract analysis, not legal advice.

## CRITICAL REQUIREMENT: Indian Contract Act Analysis

**BEFORE** making any red flag or green flag assessment, you MUST:

1. Quickly identify the contract type and what types of issues it raises
2. Determine which Indian Contract Act sections are RELEVANT to this contract:
   - Formation/validity issues? → Sections 10-22
   - Void/unlawful terms? → Sections 23-30
   - Contingent/conditional terms? → Sections 31-36
   - Performance obligations? → Sections 37-67
   - Breach/compensation? → Section 73
   - Indemnity/guarantee/surety? → Sections 124-147
3. Read ONLY those relevant sections from indian_contract_law.md (don't read the entire act)
4. Compare contract clauses against the relevant Act sections
5. Include Act section citations in all risk assessments
6. Highlight any conflicts between contract terms and the Act
7. Document which sections support or contradict the contract terms

## WORKFLOW: CHUNKED ANALYSIS FOR CONTEXT RETENTION

This skill is designed to work with a chunked analysis approach:

1. **Contract is read in 200-line chunks** by the agent
2. **Each chunk is analyzed independently** and findings saved to `/memories/chunk_N_analysis.md`
3. **After all chunks are read**, this skill is invoked for the consolidation phase
4. **Use all chunk findings** to create the final comprehensive analysis
5. **Consolidate into single report** saved as `/memories/{contract_name}_final_analysis.md`

When consolidating, your job is to:

- Read all chunk analysis files from /memories/
- Identify patterns across chunks
- Consolidate duplicate findings
- Create hierarchical risk assessment
- Cross-reference Act sections
- Produce final production-ready report

## Core Objective

Read the agreement carefully and answer these questions:

1. What is the deal structure?
2. Who are the parties and what are they promising?
3. What are the key obligations, timelines, and payment terms?
4. What clauses protect each side, and which side benefits more?
5. What terms are risky, unusual, one-sided, or missing?
6. What would a sophisticated lawyer immediately notice or negotiate?

## Instructions

### 1. Identify the contract type and structure

Determine whether the document is:

- a supply agreement
- master supply agreement
- purchase agreement
- vendor agreement
- framework agreement
- manufacturing agreement
- distribution / sourcing agreement
- amendment, addendum, or side letter

Then identify:

- parties and their roles
- effective date
- term and renewal
- exhibits, schedules, annexures, statements of work, purchase orders, or incorporated policies

### 2. Extract the key deal terms

Pull out the main business terms in a clean structured way, including:

- product/service being supplied
- quantities or forecasting commitments
- exclusivity or non-exclusivity
- pricing, discounts, escalators, indexation, rebates
- order process and acceptance rules
- delivery terms, Incoterms, logistics, title, and risk of loss
- inspection, testing, and acceptance
- payment terms, invoicing, withholding rights, setoff rights
- minimum purchase commitments or take-or-pay obligations
- lead times, service levels, and supply continuity obligations
- territory, customer restrictions, and channel restrictions

### 3. Review the legal clauses like a lawyer

Analyze each major clause and explain:

- what it means in plain English
- who it favors
- whether it is market-standard, seller-friendly, or buyer-friendly
- whether it creates risk, ambiguity, or hidden leverage
- whether it is unusually broad, narrow, or missing entirely

Pay special attention to:

- definitions
- scope of supply
- ordering mechanics
- forecast and planning obligations
- quality standards and specifications
- compliance with laws
- audits and inspection rights
- warranties
- recalls and product defects
- indemnities
- limitation of liability
- termination rights
- suspension rights
- force majeure
- confidentiality
- data protection and cybersecurity
- intellectual property ownership and infringement risk
- insurance
- subcontracting
- assignment and change of control
- dispute resolution and governing law
- remedies and cure periods
- survival clauses
- order of precedence

### 4. Identify good clauses and bad clauses WITH LEGAL CITATIONS

Before classifying any clause, cross-reference the Indian Contract Act, 1872:

- Sections 10-22: Contract formation and validity
- Sections 23-30: Void agreements and unlawful consideration
- Sections 31-36: Contingent contracts
- Sections 37-67: Performance of contracts
- Section 73: Compensation for breach
- Section 124-147: Indemnity and guarantee

Classify clauses as:

**Good clauses**

- strongly protect the client or user
- create leverage, clarity, or remedies
- reduce operational risk
- improve enforceability or accountability
- **CITE**: Reference relevant Act sections (e.g., "aligns with Section 73 - Compensation for breach")

**Bad clauses**

- shift too much risk to one party
- are vague, one-sided, or overly broad
- create hidden liabilities or uncapped exposure
- weaken remedies, timelines, or termination rights
- rely on subjective standards that are hard to enforce
- **CITE**: Reference conflicting Act sections (e.g., "violates Section 23 - Unlawful consideration by imposing unilateral penalties")

For each notable clause, explain:

- why it is good or bad
- what practical effect it has
- whether it is negotiable
- a suggested improvement if needed
- **MANDATORY: Cite relevant Indian Contract Act sections and explain how clause aligns or conflicts with the Act**

### 5. Flag red flags and missing protections

Look for:

- unlimited or overly broad indemnities
- weak or missing liability caps
- one-way termination rights
- automatic renewal traps
- price increase rights without guardrails
- vague acceptance criteria
- broad discretion to reject or delay orders
- supplier can suspend supply too easily
- customer cannot offset or withhold payment
- weak warranty language
- no recall allocation
- no audit or reporting rights
- no cure period before termination
- excessive exclusivity
- restrictive non-compete or non-solicit language
- assignment rights that allow unwanted transfers
- hidden incorporation by reference of terms not shown in the agreement
- conflict between main agreement and schedules
- missing survival language for key rights

### 6. Compare against a lawyer’s market sense

Use practical contract-lawyer judgment to say whether terms are:

- normal and acceptable
- slightly aggressive
- materially risky
- highly unusual
- one-sided enough to merit negotiation

When useful, mention:

- “this is standard”
- “this is seller-friendly”
- “this is buyer-friendly”
- “this is a major negotiation point”
- “this could become a dispute trigger”

### 7. Spot internal inconsistencies

Check whether the agreement contradicts itself, for example:

- different pricing in different sections
- mismatched definitions
- conflicting warranty periods
- conflicting liability caps
- inconsistent delivery terms
- annexures overriding the base agreement
- PO terms conflicting with master terms
- survival language conflicting with termination language

If there are inconsistencies, identify which clause likely controls based on the order-of-precedence clause.

### 8. Produce a practical negotiation view

End with:

- top 5 negotiation points
- top 5 risks
- clauses to keep as-is
- clauses to revise
- missing clauses to add
- likely dispute areas

If helpful, suggest stronger alternative language in plain English.

## Output format

Use this structure in the response:

### 1. Deal snapshot

A short plain-English summary of what the agreement does.

### 2. Key extracted terms

A structured list or table of the most important business terms.

### 3. Clause-by-clause legal analysis

For each major clause:

- clause name
- plain-English meaning
- who it favors
- risk level
- comments

### 4. Good clauses

List the clauses that are favorable and why.

### 5. Bad clauses / red flags

List the risky or unfavorable clauses and why they matter.

### 6. Missing clauses

List important protections or standard terms that are absent.

### 7. Negotiation points

List the most important edits a lawyer would push for.

### 8. Overall assessment

Give a concise conclusion such as:

- low risk / moderate risk / high risk
- buyer-friendly / supplier-friendly / balanced
- biggest legal and commercial concerns

## Analysis style

Be precise, practical, and commercially aware. Use plain English, but think like a lawyer.

When possible:

- separate legal risk from business risk
- distinguish enforceability issues from negotiation issues
- note whether a clause is unusual for a supply agreement
- explain real-world consequences, not just legal theory

## Important reasoning rules

- Do not assume a clause is harmless just because it looks familiar.
- Do not ignore hidden obligations in definitions, schedules, or incorporated documents.
- Do not treat a clause as standard if it is unusually broad or one-sided.
- Do not stop at summary; identify concrete implications.
- Do not give vague feedback like “needs review” without saying why.
- When language is ambiguous, say what interpretations are possible and which side benefits from the ambiguity.
- If the agreement is missing a clause that would usually matter, say so explicitly.

## Red flag severity scale with Indian Contract Act citations

Use one of these labels where useful:

- Low (Minor deviation from Act, minimal business impact)
- Medium (Notable issue, violates Act principles, manageable risk)
- High (Significant violation of Act, major business risk)
- Critical (Threatens contract enforceability, severe Act violations)

For EACH red flag, you MUST:

1. State the severity level
2. Explain the reason for the severity rating
3. **Cite the specific Indian Contract Act section(s) involved**
4. Explain how the contract clause conflicts with or violates the Act
5. Describe the real-world legal consequence

Example format:

```
RED FLAG: Unilateral Termination Without Cause
Severity: HIGH
Act Citation: Section 56 (Contract to do act afterwards becoming impossible or unlawful), Section 62 (Effect of novation, rescission, and alteration)
Issue: Contract allows Utility to terminate at any time without compensation, which may violate Section 56 principles of fair allocation of risk and Section 73 (Compensation for breach).
Legal Consequence: Courts may interpret this as unconscionable and unenforceable.
```

## Optional enhanced checks

If the contract is detailed enough, also analyze:

- supply chain resilience
- force majeure and allocation of shortages
- forecast accuracy obligations
- production capacity commitments
- regulatory compliance for the goods
- product liability exposure
- recall mechanics
- audit rights over sub-suppliers
- business continuity obligations
- ESG / modern slavery / anti-corruption / sanctions commitments

## Final instruction - Production Grade Output Required

The goal is to act like a highly competent commercial lawyer reviewing a supply agreement for a client:

- Identify what matters, what is dangerous, what is favorable, and what should be negotiated
- **Always cite Indian Contract Act sections** as supporting evidence for your analysis
- Save the analysis in structured format to /memories/ for the output generator to consume
- Do NOT write logs - let the system logging handle that
- Focus on creating analysis content that will be rendered to frontend by the output generator

**Output Structure Expected in /memories/:**

- Contract analysis should be in: `/memories/{contract_name}_analysis.md`
- Format: Markdown with clear sections, Act citations, and frontend-ready structure
- Do not include execution logs or tool calls - only the substantive analysis

---
