---
name: india-code-research
description: Research Indian laws from indiacode.nic.in to support contract analysis with authentic legal references. Use this skill when analyzing contracts containing Indian law references or when identifying applicable Indian statutes and regulations.
license: MIT
compatibility: Requires internet access and search tools
metadata:
  author: contract-system
  version: "1.0"
  domain: Legal Research
  focus: Indian Contract Law
allowed-tools: [web_search, fetch_url]
---

# India Code Legal Research Skill

## Overview

This skill provides structured guidance for researching Indian laws from the authoritative India Code website (indiacode.nic.in) to support contract analysis. The skill ensures that legal references are based on verified government sources and current statute text.

## Why India Code Website

- **Official Source**: Hosted by National Informatics Centre (NIC), Ministry of Law and Justice
- **Authoritative**: Contains current, consolidated versions of all Indian laws
- **Verified Content**: Official government repository with no misinformation
- **No Hallucination Risk**: Direct statute text prevents AI interpretation errors
- **Citation Accuracy**: Proper section and chapter references for legal compliance

## Legal Research Process

### 1. Identify Applicable Laws

When analyzing a contract clause, determine which Indian laws apply:

**Common Law Categories**:

- **Contract Law**: Indian Contract Act, 1872 (primary legislation)
- **Commercial**: Sale of Goods Act, 1930; Negotiable Instruments Act, 1881
- **Employment**: Industrial Disputes Act, 1947; Payment of Gratuity Act, 1972
- **IP Rights**: Copyright Act, 1957; Patents Act, 1970; Trade Marks Act, 1999
- **Data Protection**: Digital Personal Data Protection Act, 2023
- **Consumer Protection**: Consumer Protection Act, 2019
- **Competition**: Competition Act, 2002
- **Dispute Resolution**: Arbitration and Conciliation Act, 1996
- **Insolvency**: Insolvency and Bankruptcy Code, 2016

### 2. Search for Statute on India Code Website

**Search Strategy**:

```
Query format: "site:indiacode.nic.in [Act Name] [Year]"
Example: "site:indiacode.nic.in Indian Contract Act 1872"
```

**Search Steps**:

1. Use web search with site restriction to indiacode.nic.in
2. Target specific acts, year, and section numbers
3. Retrieve the official statute page from nic.in domain

**Important**: Only accept results from indiacode.nic.in domain. Reject results from other legal databases.

### 3. Retrieve Full Statute Text

Once you identify the relevant statute on indiacode.nic.in:

1. **Fetch the statute page** using the URL from search results
2. **Extract section numbers** relevant to the clause being analyzed
3. **Copy exact statutory text** - do not paraphrase or interpret
4. **Note section headings** for precise citation format
5. **Record verbatim provisions** that apply to the contract clause

**Citation Format**:

```
[Act Name], [Year], Section [Number]
Example: Indian Contract Act, 1872, Section 65
```

### 4. Match Clause to Statute

Compare the contract clause against the statute provisions:

**Question Framework**:

- Does the clause comply with mandatory statutory provisions?
- Are there statutory restrictions the clause violates?
- Does the clause align with statutory default rules?
- Are there qualifying conditions in the statute not met in the clause?
- Does the statute permit excluding or modifying this clause?

### 5. Generate Legal Analysis

Based on statute retrieval, produce analysis containing:

- **Statute Citation**: Full name, year, section number
- **Statutory Text**: Exact quote from indiacode.nic.in
- **Clause Alignment**: How clause relates to statute
- **Compliance Status**: Yes/No/Partial with explanation
- **Risk Assessment**: This feeds into risk scoring

## High-Frequency Indian Laws for Contracts

### Indian Contract Act, 1872 (Primary)

- **Section 10-23**: Offer and Acceptance
- **Section 24-27**: Consideration
- **Section 28-35**: Capacity and Legality
- **Section 42-47**: Performance of Contracts
- **Section 55-75**: Breach and Remedies
- **Section 221-230**: Indemnity and Guarantee

### Sale of Goods Act, 1930

- **Chapter VIII**: Conditions and Warranties
- **Chapter X**: Transfer of Property
- **Section 39-46**: Risk and Property

### Negotiable Instruments Act, 1881

- **Section 73-76**: Indemnity and Guarantee
- **Chapter XVII**: Bills of Exchange and Promissory Notes

### Arbitration and Conciliation Act, 1996

- **Part I**: International Commercial Arbitration
- **Section 25-34**: Arbitral Proceedings
- **Section 48**: Grounds for Refusal of Arbitral Award

### Copyright Act, 1957

- **Section 37**: Assignment of Copyright
- **Section 51**: Infringement of Copyright

### Patents Act, 1970

- **Section 47**: Assignment of Patent and Licensing

### Trade Marks Act, 1999

- **Section 37**: Assignment and licensing

### Digital Personal Data Protection Act, 2023

- **Part II**: Rights and Obligations
- **Schedule I**: Sensitive Personal Data (for contracts handling PII)

## Common Contract Clause Analysis Examples

### Example 1: Indemnity Clause

**Clause**: "X shall indemnify Y against all claims arising from breach"
**Research**: Indian Contract Act, 1872, Sections 124-130 (Indemnity provisions)
**Search**: "site:indiacode.nic.in Indian Contract Act 1872 section 124"
**Key Questions**:

- Does indemnity exceed statutory limits?
- Are conditions within statutory framework?
- Is notice requirement included (Section 128)?

### Example 2: IP Rights Assignment

**Clause**: "All work created shall be sole property of Client"
**Research**: Copyright Act, 1957, Section 37 (Assignment requirements)
**Search**: "site:indiacode.nic.in Copyright Act 1957 section 37"
**Key Questions**:

- Is assignment made in writing (mandatory)?
- Does it cover existing and future works?
- Are moral rights properly addressed?

### Example 3: Limitation of Liability

**Clause**: "Liability capped at contract value"
**Research**: Indian Contract Act, 1872, Section 73 (Remoteness of Damage)
**Search**: "site:indiacode.nic.in Indian Contract Act 1872 section 73"
**Key Questions**:

- Are damages within foreseeable scope?
- Does cap create unconscionable disparity?
- Is consequential damage exclusion valid under Section 74?

### Example 4: Termination Rights

**Clause**: "Either party may terminate immediately without cause"
**Research**: Sale of Goods Act, 1930, Sections 26-27 (Performance of warranty)
**Search**: "site:indiacode.nic.in Sale of Goods Act 1930"
**Key Questions**:

- Is termination right subject to notice?
- Do statutory implied warranties apply?
- Is early termination a breach remedy?

## Best Practices for Accuracy

1. **Always verify source**: Confirm URL is indiacode.nic.in, never other legal sites
2. **Use exact text**: Copy statute language directly, never paraphrase
3. **Include section numbers**: Full citation format [Act], [Year], Section [XX]
4. **Note amendment dates**: Statutes are amended frequently; record date retrieved
5. **Check current version**: indiacode.nic.in contains consolidated versions
6. **Cross-reference related sections**: Statutory sections often contain conditional provisions
7. **Record verbatim quotes**: Essential for legal accuracy and audit trail

## Research Workflow for Subagents

When passed to subagents for clause analysis:

1. **Clause Analyzer** receives clause text
2. Identifies applicable law category (e.g., "indemnity")
3. **India Code Researcher** searches for relevant statute
4. Fetches full statute text from indiacode.nic.in
5. Returns statute excerpt with section citations
6. **Risk Assessor** evaluates compliance against statute
7. Produces compliance score and reasoning
8. **Risk Scorer** incorporates statutory compliance into overall risk

## Tools Available

- **web_search**: Search indiacode.nic.in and relevant legal sources
- **fetch_url**: Retrieve full statute text from indiacode.nic.in pages

## Validation Checklist

Before using research results:

- [ ] Source is indiacode.nic.in (official NIC domain)
- [ ] Statute is named correctly with year (e.g., "Act, YYYY")
- [ ] Section number is explicitly stated (e.g., "Section XX")
- [ ] Statutory text is quoted verbatim, not paraphrased
- [ ] Research date is noted (statutes are amended)
- [ ] Relevant amendments are considered
- [ ] Cross-referenced sections are acknowledged

## Reference: Top 10 Indian Acts for Contract Analysis

1. **Indian Contract Act, 1872** - Foundation for all contracts
2. **Sale of Goods Act, 1930** - Commercial transactions
3. **Negotiable Instruments Act, 1881** - Financial instruments
4. **Arbitration and Conciliation Act, 1996** - Dispute resolution
5. **Copyright Act, 1957** - Intellectual property
6. **Patents Act, 1970** - Innovation IP
7. **Trade Marks Act, 1999** - Brand protection
8. **Consumer Protection Act, 2019** - Consumer rights
9. **Digital Personal Data Protection Act, 2023** - Privacy obligations
10. **Competition Act, 2002** - Anti-competitive practices

Each should be checked from indiacode.nic.in for current, authoritative provisions when relevant clauses are encountered.
