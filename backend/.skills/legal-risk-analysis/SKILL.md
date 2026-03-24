---
name: legal-risk-analysis
description: Analyze contract clauses for legal risk and categorize by impact. Use this skill to assess which clauses are harmful, beneficial, or neutral for the company.
license: MIT
compatibility: Works with legal statute references and clause text
metadata:
  author: contract-system
  version: "1.0"
  domain: Legal Risk Assessment
allowed-tools: []
---

# Legal Risk Analysis Skill

## Overview

This skill provides structured frameworks for analyzing contract clauses to determine legal risk, identify harmful provisions, and categorize clauses by their impact on the company. The goal is to move beyond surface-level analysis to deep legal reasoning grounded in Indian law.

## Core Principles

1. **No Hallucination**: All risk assessments must reference verified legal sources
2. **Comprehensive**: Consider all dimensions of risk - legal, financial, operational
3. **Precise Scoring**: Use quantifiable criteria for risk assessment
4. **Balanced Analysis**: Acknowledge both protective and exposing aspects of each clause
5. **Actionable**: Risk assessment should guide negotiation strategy

## Clause Risk Categorization Framework

### Risk Score Scale (0-100)

- **0-20: Green - Beneficial for Company**
  - Protective language heavily favors company
  - Clauses that shift liability/risk away from company
  - Standard market terms that protect company interests
  - Examples: Limitation of liability, broad indemnification FOR company

- **20-40: Light Green - Favorable Terms**
  - Balanced language with some company protections
  - Standard market terms with minor issues
  - Negotiable provisions that can be improved
  - Examples: Balanced warranties, mutual indemnification

- **40-60: Yellow - Neutral Risk**
  - Balanced between parties
  - Industry standard terms
  - No significant concerns
  - Examples: Payment terms, delivery schedules, basic warranties

- **60-80: Orange - Unfavorable Terms**
  - Language tilts toward counterparty
  - Creates company obligations without reciprocal protection
  - Higher financial or legal exposure
  - Examples: Broad liability, loose warranties, strict compliance

- **80-100: Red - Critical Risk**
  - Highly unfavorable to company
  - Creates significant legal/financial exposure
  - May contain illegal or unenforceable provisions
  - Examples: Unlimited liability, broad indemnity obligations, personal guarantees

## Risk Assessment Dimensions

### 1. Legal Compliance Risk

**Assessment Questions**:

- Does the clause violate mandatory Indian law provisions?
- Is the clause unenforceable under Indian law?
- Does it conflict with statutory requirements?
- Are there implicit statutory provisions it excludes?

**Statute Reference Process**:

- Identify applicable Indian statute
- Retrieve text from indiacode.nic.in
- Compare clause against statutory requirements
- Assess compliance score

**Risk Scoring**:

- Violates statute: +35 risk points
- Conflicts with statute intent: +20 risk points
- Excludes statutory protections: +15 risk points
- Fully compliant: 0 risk points

### 2. Financial Exposure Risk

**Assessment Questions**:

- What is the maximum financial liability?
- Is the liability capped or uncapped?
- Are indirect/consequential damages included?
- Can liability exceed contract value?
- What is the financial impact if triggered?

**Risk Scoring Factors**:

- Uncapped liability: +25 risk points
- Liability > contract value: +20 risk points
- Includes consequential damages: +15 risk points
- No cap on damages: +20 risk points
- Each $1M exposure: +2 risk points (adjust for contract size)

### 3. Operational Risk

**Assessment Questions**:

- Does the clause impose difficult compliance burdens?
- Are performance standards achievable?
- What are the consequences of non-compliance?
- Are there ongoing obligations?
- Can costs spiral uncontrollably?

**Risk Scoring Factors**:

- Unreasonable performance standards: +15 risk points
- Ongoing compliance burdens: +10 risk points
- Difficult audit/verification requirements: +10 risk points
- Escalating obligations: +10 risk points
- Resource-intensive compliance: +5 risk points

### 4. Dispute Resolution Risk

**Assessment Questions**:

- Is dispute resolution favorable/unfavorable to company?
- Is arbitration or litigation required?
- Are there mandatory costs (attorney fees)?
- What jurisdiction governs?
- What happens if disputes arise?

**Risk Scoring Factors**:

- Litigation in unfavorable jurisdiction: +15 risk points
- Loser pays attorney fees: +10 risk points
- Complex multi-step dispute resolution: +5 risk points
- Exclusive jurisdiction far from company: +10 risk points
- Mandatory arbitration with cost-sharing: +5 risk points

### 5. Relationship/Partnership Risk

**Assessment Questions**:

- Does this clause indicate distrust?
- Are there asymmetric obligations?
- What does this say about power dynamics?
- Will this harm the business relationship?
- Are there hidden implications?

**Risk Scoring Factors**:

- Asymmetric obligations (one-way): +15 risk points
- Excessive monitoring/audit rights: +10 risk points
- Unrestricted access to company information: +10 risk points
- Termination rights heavily favor counterparty: +10 risk points
- Relationship strain potential: +5 risk points

## Harmful Clause Detection Framework

### Patterns That Signal Harmful Clauses

#### Pattern 1: Unlimited Liability

```
Risk Indicators:
- Words: "unlimited", "any damages", "all claims", "perpetual"
- No cap mentioned
- Includes consequential, indirect, or punitive damages
- Survives termination indefinitely

Risk Score: 70-95 (CRITICAL)
Response: Must negotiate cap or exclusion of certain damage types
```

#### Pattern 2: Broad Indemnity Obligations

```
Risk Indicators:
- Company indemnifies for large category of claims
- No reciprocal indemnity from counterparty
- Indemnity covers counterparty's own negligence/breach
- Applies to "any claim" without limitation

Risk Score: 65-85 (HIGH)
Response: Narrow scope, add reciprocal protection, exclude counterparty negligence
```

#### Pattern 3: Strict Liability Standards

```
Risk Indicators:
- "Strict liability" or "regardless of fault"
- No fault requirement
- No negligence threshold
- Company liable for anything that happens

Risk Score: 60-80 (HIGH)
Response: Add "gross negligence" or "willful misconduct" qualifier
```

#### Pattern 4: Unachievable Performance Standards

```
Risk Indicators:
- SLAs with 99.99%+ uptime
- Guaranteed outcomes
- "Best efforts" without definition
- Performance measured by counterparty

Risk Score: 50-70 (MEDIUM-HIGH)
Response: Define achievable standards, add force majeure, define measurement method
```

#### Pattern 5: Unilateral Termination Rights

```
Risk Indicators:
- One party can terminate without cause
- No notice period or minimal notice
- No termination fee
- Applies anytime during term

Risk Score: 50-75 (MEDIUM-HIGH)
Response: Add reciprocal termination right, require notice period, add termination fee
```

#### Pattern 6: Exclusive Jurisdiction/Venue

```
Risk Indicators:
- Litigation must occur in distant, inconvenient location
- Company unfamiliar with local legal system
- Cost to defend significantly higher
- Counterparty's home country

Risk Score: 40-60 (MEDIUM)
Response: Negotiate mutual jurisdiction or neutral third location
```

#### Pattern 7: Confidentiality Over-Reach

```
Risk Indicators:
- Indefinite confidentiality obligations
- Company's own information treated as confidential
- Prevents disclosure of material facts
- Creates disadvantageous info asymmetry

Risk Score: 45-65 (MEDIUM)
Response: Limit duration, add carve-outs for required disclosures
```

#### Pattern 8: IP Rights Overreach

```
Risk Indicators:
- All work-product owned by counterparty
- Includes pre-existing company IP
- Includes work done outside engagement
- Grants broad license to third parties

Risk Score: 55-85 (HIGH)
Response: Carve out company pre-existing IP, limit to deliverables created for engagement
```

## Beneficial Clause Detection Framework

### Patterns That Signal Protective Clauses

#### Pattern 1: Strict Limitation of Liability

```
Protection Indicators:
- Explicit cap on liability (e.g., "$X or 12 months fees")
- Exclusion of consequential damages
- Exclusion of indirect damages
- Exclusion of punitive damages

Risk Score: 0-25 (BENEFICIAL)
Benefit: Protects company from catastrophic exposure
```

#### Pattern 2: Broad Indemnification FOR Company

```
Protection Indicators:
- Counterparty indemnifies company
- Covers intellectual property infringement
- Covers third-party claims
- Includes defense cost coverage

Risk Score: 0-20 (VERY BENEFICIAL)
Benefit: Shifts liability to counterparty for certain classes of claims
```

#### Pattern 3: Strong Confidentiality Protection

```
Protection Indicators:
- Prevents disclosure of company information
- Includes non-compete and non-solicitation
- Protects company trade secrets
- Survives termination appropriately

Risk Score: 5-30 (BENEFICIAL)
Benefit: Protects company intellectual assets
```

#### Pattern 4: Favorable IP Ownership

```
Protection Indicators:
- Company retains pre-existing IP ownership
- Work-product clearly owned by company
- Counterparty grants narrow rights only
- No license grant to third parties

Risk Score: 0-20 (VERY BENEFICIAL)
Benefit: Preserves company IP and competitive advantage
```

#### Pattern 5: Robust Warranty Coverage

```
Protection Indicators:
- Counterparty provides strong warranties
- Warranties cover all significant aspects
- Warranties have meaningful term (1+ years)
- Covers both title and performance

Risk Score: 5-25 (BENEFICIAL)
Benefit: Provides recourse if counterparty fails to perform
```

#### Pattern 6: Strong Compliance/Security Requirements

```
Protection Indicators:
- Requires counterparty to maintain security standards
- Requires compliance certifications
- Includes audit rights
- Defines data protection obligations

Risk Score: 10-30 (BENEFICIAL)
Benefit: Ensures counterparty maintains required standards
```

## Risk Scoring Calculation Method

### Base Score Calculation

```
Total Risk Score = Σ (Dimension Scores)

Where:

Dimension Scores =
  Legal Compliance Risk (0-35) +
  Financial Exposure Risk (0-25) +
  Operational Risk (0-15) +
  Dispute Resolution Risk (0-15) +
  Relationship Risk (0-10)

Final Score = Total Risk Score capped at 0-100
```

### Example: Unlimited Indemnity Clause

**Clause**: "Company indemnifies Client for any and all claims, damages, or costs arising from the services, including indirect and consequential damages, perpetually."

**Dimension Scoring**:

- **Legal Compliance**: 25/35 (Enforceable but overly broad; assumes Client not negligent)
- **Financial Exposure**: 25/25 (Unlimited scope, includes all damage types, perpetual)
- **Operational**: 10/15 (Company must defend all claims regardless of merit)
- **Dispute Resolution**: 8/15 (Company likely pays defense costs)
- **Relationship**: 7/10 (Asymmetric burden harms relationship)

**Total Risk Score**: 75/100 (CRITICAL - RED - Requires renegotiation)

**Recommendation**:

- Cap liability at contract value
- Exclude consequential damages
- Add "gross negligence or willful misconduct" qualifier
- Limit duration to warranty period (e.g., 1-2 years)

## Clause Interrelationships

**Important**: Risk assessment must consider how clauses interact:

- **Limitation of Liability + Indemnity**: Indemnity may exceed liability cap
- **Warranty + Termination**: Short warranties + unilateral termination = no recourse
- **Confidentiality + Termination**: Must survive termination appropriately
- **IP Rights + License Grant**: License scope may grant more than intended
- **Compliance + Audit**: Audit rights may be mechanism to discover breach

## Output Format for Risk Analysis

Each clause analysis should include:

```json
{
  "clause_number": 1,
  "clause_type": "Liability Limitation",
  "raw_text": "[quoted text]",

  "risk_dimensions": {
    "legal_compliance": 0, // 0-35
    "financial_exposure": 20, // 0-25
    "operational": 5, // 0-15
    "dispute_resolution": 0, // 0-15
    "relationship": 0 // 0-10
  },

  "total_risk_score": 25,
  "risk_category": "BENEFICIAL", // RED/ORANGE/YELLOW/GREEN_LIGHT/GREEN

  "legal_reasoning": "Explicit cap on liability protects company from unlimited exposure...",

  "harmful_patterns_detected": [],
  "protective_patterns_detected": [
    "Explicit liability cap",
    "Exclusion of consequential damages"
  ],

  "key_concerns": [],
  "recommended_changes": [],

  "statutory_references": {
    "act": "Indian Contract Act",
    "year": 1872,
    "relevant_sections": [73, 74]
  },

  "confidence_score": 95 // 0-100 based on analysis depth
}
```

## Risk Assessment Checklist

Before finalizing risk score:

- [ ] All dimensions scored consistently
- [ ] Legal compliance verified against applicable Indian law
- [ ] Financial exposure quantified
- [ ] Interrelationships with other clauses considered
- [ ] Industry context considered (some industries have higher tolerance)
- [ ] Geographic jurisdiction considered
- [ ] Company size/capacity considered relative to obligations
- [ ] Market standards compared
- [ ] Negotiation leverage assessed
- [ ] Statutory references verified from indiacode.nic.in

## Benchmarking: Standard Industry Scores

**Typical Risk Profiles by Contract Type**:

| Contract Type            | Typical Score Range | Benchmark |
| ------------------------ | ------------------- | --------- |
| Master Service Agreement | 35-55               | 45        |
| NDA (Mutual)             | 20-40               | 30        |
| SLA (Vendor)             | 25-50               | 40        |
| License Agreement        | 30-60               | 45        |
| Joint Venture            | 40-70               | 55        |
| Employment               | 20-45               | 35        |
| Procurement              | 35-60               | 50        |
| Partnership              | 30-65               | 50        |

If individual clause score significantly exceeds benchmark, flag for renegotiation.

## Integration with India Code Research

This skill works in conjunction with **india-code-research** skill:

1. Clause Risk Analyzer identifies potential issues
2. India Code Research Skill retrieves applicable statute
3. Legal Compliance Risk dimension incorporates statutory analysis
4. Final risk score reflects both statutory compliance AND commercial fairness

This dual approach ensures both legal validity AND commercial protection.
