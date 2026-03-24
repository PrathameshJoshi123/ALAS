"""
Clause-Specific Analysis Rules & Statute Mapping
Maps clause types to correct Indian Contract Act sections
Prevents hallucination of irrelevant statutes
"""

# CORRECT MAPPING: Clause Type → ICA 1872 Sections
CLAUSE_STATUTE_MAPPING = {
    # Contract Formation & Scope
    'Scope of Services': {
        'statute': 'Indian Contract Act 1872',
        'sections': ['Section 2(d)', 'Section 12'],  # Agreement definition, offer/acceptance
        'key_points': [
            'Scope must be clear and unambiguous',
            'Defines the enforceable obligations',
            'Unreasonably broad scope may be unenforceable'
        ],
        'risk_keywords': ['unlimited', 'all services', 'anything requested', 'at our discretion'],
        'example_risk': 'Scope says "provide all services company needs at any time" - TOO BROAD'
    },
    
    # Payment & Consideration
    'Payment Terms': {
        'statute': 'Indian Contract Act 1872',
        'sections': ['Section 2(d)', 'Section 35'],  # Consideration, payment terms execution
        'key_points': [
            'Consideration must be adequate but need not be adequate',
            'Payment terms must be clear (amount, timeline, conditions)',
            'Currency and payment method should be specified'
        ],
        'risk_keywords': ['undefined amount', 'at discretion', 'no payment', 'unlimited'],
        'example_risk': 'Payment says "amount to be mutually agreed" without timeline - ENFORCEABLE but risky'
    },
    
    # Term & Duration
    'Term & Termination': {
        'statute': 'Indian Contract Act 1872',
        'sections': ['Section 37-40', 'Section 41-45'],  # Agent duties, termination
        'key_points': [
            'Termination must follow specified notice period',
            'Unilateral termination at will is permissible but should be mutual',
            'Termination for cause requires clear definition of cause'
        ],
        'risk_keywords': ['immediately', 'at will', 'without notice', 'no cause'],
        'example_risk': 'Can terminate "immediately without notice" - CRITICAL risk if one-sided'
    },
    
    # Liability & Indemnity
    'Limitation of Liability': {
        'statute': 'Indian Contract Act 1872',
        'sections': ['Section 73', 'Section 55'],  # Breach damages, failure to perform
        'key_points': [
            'Section 73: Breach remedy is compensation for loss directly caused by breach',
            'Indirect damages are limit to foreseeable damages',
            'Parties can contractually limit liability - THIS IS PROTECTIVE'
        ],
        'risk_keywords': ['unlimited liability', 'all damages', 'third-party claims'],
        'example_risk': 'Indemnification for "all third-party claims without limit" - CRITICAL'
    },
    
    'Indemnification': {
        'statute': 'Indian Contract Act 1872',
        'sections': ['Section 124-125'],  # Indemnity definition and scope
        'key_points': [
            'Indemnity = promise to compensate for loss caused by indemnified party',
            'Scope must be defined: for whose actions? which claims?',
            'Broad indemnity covering party\'s own negligence is disfavored'
        ],
        'risk_keywords': ['all claims', 'any damages', 'our negligence', 'without limitation'],
        'example_risk': 'Indemnify all third-party claims for anything we do - CRITICAL (80+)'
    },
    
    # Confidentiality & IP
    'Confidentiality': {
        'statute': 'Indian Contract Act 1872 + Indian Penal Code',
        'sections': ['Section 2(n)', 'IPC Section 72'],  # Confidential communication
        'key_points': [
            'Must define what is "confidential"',
            'Duration of confidentiality obligation',
            'Permitted disclosures (legal requirement, court order, etc.)'
        ],
        'risk_keywords': ['perpetual', 'all information', 'customer lists', 'no exceptions'],
        'example_risk': 'All information treated as confidential forever - potentially unenforceable'
    },
    
    'Intellectual Property': {
        'statute': 'Indian Copyright Act 1957 + Patents Act 1970',
        'sections': [
            'Copyright Act Section 14, 17',  # Ownership, authorship
            'Patents Act Section 6'  # Right to patent
        ],
        'key_points': [
            'Must clearly assign IP ownership',
            'Distinguish: pre-existing IP vs work-for-hire',
            'Background IP should remain with originating party'
        ],
        'risk_keywords': ['all IP', 'our ideas', 'pre-existing', 'ambiguous ownership'],
        'example_risk': 'All work product including our pre-existing tools become customer property'
    },
    
    # Warranties & Representations
    'Warranties': {
        'statute': 'Indian Contract Act 1872',
        'sections': ['Section 14-15'],  # Warranties and representations
        'key_points': [
            'Warranty = assurance about fact, breach gives damages',
            'Representations = statements, breach may give recission',
            'Should define scope: as-is, fitness, merchantability?'
        ],
        'risk_keywords': ['unlimited', 'perpetual', 'all risks', 'guaranteed'],
        'example_risk': 'Warrant software works in ALL systems forever - unrealistic'
    },
    
    # Dispute Resolution
    'Governing Law': {
        'statute': 'Indian Contract Act 1872 + Indian Arbitration & Conciliation Act',
        'sections': ['Arbitration Act Section 20-25'],  # Arbitration scope
        'key_points': [
            'Governing law specifies which state\'s laws apply',
            'Jurisdiction clause specifies which court has authority',
            'Should match where contract will be performed/dispute arise'
        ],
        'risk_keywords': ['foreign law', 'conflicting jurisdictions', 'vague'],
        'example_risk': 'Governed by California law but disputes in Delhi courts - CONFLICT'
    },
    
    # Force Majeure
    'Force Majeure': {
        'statute': 'Indian Contract Act 1872',
        'sections': ['Section 32', 'Section 56'],  # Contingent contracts, impossibility
        'key_points': [
            'Section 32: Contract may be conditional on uncertain event',
            'Section 56: Contract void if performance becomes impossible',
            'Force majeure provides relief for unforeseeable events'
        ],
        'risk_keywords': [
            'no force majeure',
            'narrow definition',
            'excludes ordinary risks',
            'excessive liability'
        ],
        'example_risk': 'No force majeure clause despite external dependencies - RISK'
    }
}

# VALIDATION: Catch Irrelevant Statute Citations
IRRELEVANT_CITATION_PATTERNS = {
    'Indian Christian Marriage Act': 'This is for marriage contracts, not commercial contracts',
    'Hindu Marriage Act': 'Family law, not commercial',
    'Indian Succession Act': 'For wills/inheritance, not commercial contracts',
    'Land Acquisition Act': 'For land/property, not service/licensing contracts',
    'Uttar Pradesh': 'State-specific amendment (use if explicitly UP jurisdiction)',
    'Indian Penal Code': 'Criminal law, not contract analysis (only cite for torts)',
    'Motor Vehicles Act': 'For automotive, only relevant for transport contracts',
}

def get_statute_for_clause(clause_type: str) -> dict:
    """Return correct statute mapping for clause type"""
    # Normalize clause type
    normalized = clause_type.strip().title()
    
    # Try exact match
    if normalized in CLAUSE_STATUTE_MAPPING:
        return CLAUSE_STATUTE_MAPPING[normalized]
    
    # Try partial match
    for mapped_type, statute_info in CLAUSE_STATUTE_MAPPING.items():
        if mapped_type.lower() in normalized.lower() or normalized.lower() in mapped_type.lower():
            return statute_info
    
    # Default: General contract provisions
    return {
        'statute': 'Indian Contract Act 1872',
        'sections': ['Section 2', 'Section 23'],  # General definitions, validity
        'key_points': ['Contract must be valid under ICA 1872', 'Cannot be against public policy'],
        'risk_keywords': [],
        'example_risk': 'Unknown clause type - use general contract rules'
    }

def identify_irrelevant_citation(statute: str, section: str) -> str:
    """Check if statute citation is irrelevant - return warning if so"""
    statute_lower = statute.lower()
    
    for irrelevant_pattern, reason in IRRELEVANT_CITATION_PATTERNS.items():
        if irrelevant_pattern.lower() in statute_lower:
            return f"⚠️  IRRELEVANT CITATION: {statute} - {reason}"
    
    return ""

def validate_statute_relevance(clause_type: str, statute: str, section: str) -> bool:
    """Check if cited statute is relevant to clause type"""
    statute_info = get_statute_for_clause(clause_type)
    
    # Check irrelevant patterns
    if identify_irrelevant_citation(statute, section):
        return False
    
    # Check if statute matches expected
    expected_statute = statute_info['statute']
    if expected_statute.lower() not in statute.lower():
        return False
    
    return True
