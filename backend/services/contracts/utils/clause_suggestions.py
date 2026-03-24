"""
Clause Suggestion Engine

Generates beneficial clause recommendations based on:
1. Identified gaps in contract protection
2. Industry best practices
3. Indian law requirements
4. Risk assessment findings
"""

import logging
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class SuggestionTier(str, Enum):
    """Tier 1: Critical | Tier 2: Important | Tier 3: Recommended"""
    TIER_1_CRITICAL = "tier_1_critical"
    TIER_2_IMPORTANT = "tier_2_important"
    TIER_3_RECOMMENDED = "tier_3_recommended"


@dataclass
class ClauseSuggestion:
    """Structured clause suggestion"""
    clause_type: str
    tier: SuggestionTier
    title: str
    purpose: str
    recommended_language: str
    rationale: str
    statutory_basis: Optional[str]
    negotiation_hints: List[str]
    priority_level: str  # critical, high, medium, low
    estimated_difficulty: int  # 1-5 scale


class ClauseSuggestionEngine:
    """
    Generates beneficial clause recommendations based on analysis results.
    """
    
    def __init__(self):
        """Initialize suggestion engine"""
        self.logger = logging.getLogger(__name__)
    
    def analyze_contract_gaps(
        self,
        clause_scores: List[Dict[str, Any]],
        existing_clause_types: List[str],
        contract_type: Optional[str] = None
    ) -> List[ClauseSuggestion]:
        """
        Identify gaps in contract protection and suggest beneficial clauses.
        
        Args:
            clause_scores: List of analyzed clauses with risk assessments
            existing_clause_types: List of clause types already present
            contract_type: Type of contract (e.g., "MSA", "NDA", "SLA")
        
        Returns:
            List of suggested clauses ranked by priority
        """
        suggestions = []
        
        # Tier 1: Critical clauses to suggest if missing
        tier_1_critical = self._get_tier_1_suggestions(
            existing_clause_types,
            contract_type
        )
        suggestions.extend(tier_1_critical)
        
        # Tier 2: Important clauses based on contract analysis
        tier_2_important = self._get_tier_2_suggestions(
            clause_scores,
            existing_clause_types,
            contract_type
        )
        suggestions.extend(tier_2_important)
        
        # Tier 3: Recommended improvements
        tier_3_recommended = self._get_tier_3_suggestions(
            clause_scores,
            existing_clause_types
        )
        suggestions.extend(tier_3_recommended)
        
        # Sort by priority
        return sorted(suggestions, key=lambda x: (
            self._tier_priority(x.tier),
            x.priority_level
        ))
    
    def _get_tier_1_suggestions(
        self,
        existing_clause_types: List[str],
        contract_type: Optional[str] = None
    ) -> List[ClauseSuggestion]:
        """Get Tier 1 (Critical) clause suggestions"""
        suggestions = []
        
        # CRITICAL 1: Liability Limitation
        if 'liability_limitation' not in existing_clause_types:
            suggestions.append(ClauseSuggestion(
                clause_type='liability_limitation',
                tier=SuggestionTier.TIER_1_CRITICAL,
                title='Limitation of Liability Clause',
                purpose='Cap company liability exposure to manageable levels',
                recommended_language="""LIMITATION OF LIABILITY

(a) Notwithstanding any other provision in this Agreement, and except for 
indemnification obligations, breaches of confidentiality, or infringement of 
intellectual property rights, neither party's total aggregate liability under 
this Agreement shall exceed the annual fees paid or payable by [Client] for 
the Services in the 12-month period preceding the claim, or $[X], whichever 
is greater.

(b) Except as expressly stated above, in no event shall either party be liable 
for indirect, incidental, special, or consequential damages (including lost 
profits, loss of revenue, loss of data, or business interruption), even if 
advised of the possibility of such damages.

(c) This limitation applies to all causes of action, whether in contract, 
tort (including negligence), strict liability, or otherwise.""",
                rationale=(
                    'Protects company from unlimited financial exposure. '
                    'Essential in all B2B contracts. Capped liability is standard market term. '
                    'Without this, single incident could bankrupt company.'
                ),
                statutory_basis='Indian Contract Act, 1872, Section 73',
                negotiation_hints=[
                    'Universal in B2B contracts',
                    'Counterparty expects reciprocal cap',
                    'Exceptions: IP indemnity and confidentiality breaches',
                    'Typical range: 12 months fees or contract value'
                ],
                priority_level='critical',
                estimated_difficulty=2
            ))
        
        # CRITICAL 2: IP Indemnity (if vendor/vendor-like)
        if 'ip_indemnity' not in existing_clause_types:
            suggestions.append(ClauseSuggestion(
                clause_type='ip_indemnity',
                tier=SuggestionTier.TIER_1_CRITICAL,
                title='Intellectual Property Indemnity Clause',
                purpose='Shift liability for IP infringement claims to vendor',
                recommended_language="""INTELLECTUAL PROPERTY INDEMNITY

(a) [Vendor] shall indemnify, defend, and hold harmless [Company] from any 
third-party claims that the [Deliverables/Services] infringe any patent, 
copyright, trade secret, or other intellectual property right.

(b) [Vendor] shall:
    (i) Defend using counsel approved by [Company] (not to be unreasonably withheld)
    (ii) Pay all costs, including reasonable attorney fees and court costs
    (iii) Have sole control of defense, provided [Company] may participate
    (iv) Obtain settlement approval from [Company] (not to be unreasonably withheld)

(c) If [Deliverables] become infringing, [Vendor] may, at its option and 
expense, either:
    (i) Obtain the right for [Company] to continue using them;
    (ii) Replace or modify to make non-infringing; or
    (iii) If (i) and (ii) are not commercially feasible, terminate and refund fees

(d) [Vendor] has no obligation for claims arising from:
    (i) [Company]'s modification of [Deliverables]
    (ii) Use with other products not specified by [Vendor]
    (iii) Use violating [Vendor]'s instructions/documentation""",
                rationale=(
                    'Protects company from patent/copyright claims on deliverables. '
                    'Vendor controls the code/content and bears IP risk. '
                    'Standard in software, consulting, and product services.'
                ),
                statutory_basis='Indian Contract Act, 1872, Sections 124-130',
                negotiation_hints=[
                    'Essential for IP-bearing products/deliverables',
                    'Vendors typically agree to this in B2B contracts',
                    'Define scope clearly (IP only, not all claims)',
                    'Make reciprocal if company also creates IP'
                ],
                priority_level='critical',
                estimated_difficulty=3
            ))
        
        # CRITICAL 3: Confidentiality
        if 'confidentiality' not in existing_clause_types:
            suggestions.append(self._get_confidentiality_suggestion())
        
        return suggestions
    
    def _get_confidentiality_suggestion(self) -> ClauseSuggestion:
        """Get confidentiality clause suggestion"""
        return ClauseSuggestion(
            clause_type='confidentiality',
            tier=SuggestionTier.TIER_1_CRITICAL,
            title='Confidentiality and Data Protection Clause',
            purpose='Protect company information and trade secrets',
            recommended_language="""CONFIDENTIALITY AND DATA PROTECTION

(a) Definition: "Confidential Information" means all non-public information 
disclosed by one party to the other, including business plans, trade secrets, 
financial information, customer lists, and technical data, marked as 
confidential or reasonably understood to be confidential.

(b) Protection Obligations: Receiving party shall:
    (i) Maintain Confidential Information in strict confidence
    (ii) Limit access to employees on need-to-know basis
    (iii) Implement reasonable security measures per industry standards
    (iv) Not disclose without written consent, except as required by law
    (v) Use only for performing obligations under this Agreement

(c) Duration: Confidentiality obligations survive termination for [5] years 
(or indefinitely for trade secrets).

(d) Data Protection: For services involving personal data:
    (i) Comply with Digital Personal Data Protection Act, 2023
    (ii) Implement data minimization, purpose limitation, security controls
    (iii) Notify of breaches within 72 hours
    (iv) Delete data upon termination unless legally required to retain

(e) Return: Upon termination, return or destroy all Confidential Information 
per written instructions.""",
            rationale=(
                'Protects company information and competitive advantage. '
                'Data protection increasingly required post-2023 Act. '
                'Non-controversial if made mutual and balanced.'
            ),
            statutory_basis='Indian Contract Act, 1872; Digital Personal Data Protection Act, 2023',
            negotiation_hints=[
                'Must be mutual to avoid objections',
                'Longer duration for truly sensitive data (trade secrets)',
                'Data protection provisions increasingly expected',
                'Make carve-outs clear (publicly known, independently developed)',
                'Include data breach notification requirements'
            ],
            priority_level='critical',
            estimated_difficulty=2
        )
    
    def _get_tier_2_suggestions(
        self,
        clause_scores: List[Dict[str, Any]],
        existing_clause_types: List[str],
        contract_type: Optional[str] = None
    ) -> List[ClauseSuggestion]:
        """Get Tier 2 (Important) clause suggestions based on analysis"""
        suggestions = []
        
        # Warranty suggestion
        if 'warranty' not in existing_clause_types:
            suggestions.append(self._get_warranty_suggestion())
        
        # Audit rights suggestion (if dealing with vendor/vendor-like)
        if 'audit_rights' not in existing_clause_types:
            high_risk_clauses = [
                c for c in clause_scores 
                if c.get('risk_category') in ['unfavorable', 'critical']
            ]
            
            if high_risk_clauses:
                suggestions.append(self._get_audit_rights_suggestion())
        
        # Termination for convenience (if not present)
        if 'termination_for_convenience' not in existing_clause_types:
            suggestions.append(self._get_termination_suggestion())
        
        # SLA suggestion (if service-based contract)
        if contract_type in ['MSA', 'SLA', 'service'] and 'sla' not in existing_clause_types:
            suggestions.append(self._get_sla_suggestion())
        
        return suggestions
    
    def _get_warranty_suggestion(self) -> ClauseSuggestion:
        """Get warranty clause suggestion"""
        return ClauseSuggestion(
            clause_type='warranty',
            tier=SuggestionTier.TIER_2_IMPORTANT,
            title='Warranty Clause',
            purpose='Establish counterparty promises about quality and fit',
            recommended_language="""WARRANTIES

[Vendor] warrants that:

(a) Authority: It has full authority to enter into and perform this Agreement

(b) No Conflicts: This Agreement does not violate any law, regulation, court 
order, or other contractual obligation

(c) Performance: All [Services/Deliverables] shall be:
    (i) Performed in a professional and workmanlike manner
    (ii) Compliant with applicable laws and regulations
    (iii) Free from defects in workmanship and materials
    (iv) Fit for the purpose described in this Agreement

(d) IP Rights: [Vendor] warrants that [Deliverables]:
    (i) Are owned by [Vendor] or [Vendor] has valid rights
    (ii) Do not infringe third-party IP rights
    (iii) Require no third-party consents

(e) Regulatory: [Vendor] warrants compliance with:
    (i) Applicable data protection laws
    (ii) Industry standards and certifications
    (iii) Anti-corruption laws
    (iv) Competition laws

(f) Disclaimer: EXCEPT AS EXPRESSLY STATED, [VENDOR] DISCLAIMS ALL OTHER 
WARRANTIES, INCLUDING IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS.""",
            rationale=(
                'Creates clear baseline expectations about quality/functionality. '
                'Provides recourse if counterparty fails to perform. '
                'Standard in B2B; counterparty expects reciprocal warranties.'
            ),
            statutory_basis='Indian Contract Act, 1872, Section 15; Sale of Goods Act, 1930',
            negotiation_hints=[
                'Make mutual with reciprocal warranties',
                'Fitness for particular purpose is negotiable',
                'Common remedy: warranty replacement or refund',
                'Time-limited warranties (12-24 months typical)'
            ],
            priority_level='high',
            estimated_difficulty=2
        )
    
    def _get_audit_rights_suggestion(self) -> ClauseSuggestion:
        """Get audit rights clause suggestion"""
        return ClauseSuggestion(
            clause_type='audit_rights',
            tier=SuggestionTier.TIER_2_IMPORTANT,
            title='Audit and Compliance Rights',
            purpose='Give company visibility into vendor compliance',
            recommended_language="""AUDIT RIGHTS

(a) Compliance Audit: [Company] may audit [Vendor]'s compliance no more than 
[annually] with [30] days' notice. Audits may be:
    (i) In person at [Vendor]'s facilities during business hours
    (ii) Remotely via logs/systems access
    (iii) By independent third-party auditor (at [Company]'s expense)

(b) Security Audit: For services involving Company data:
    (i) [Company] may conduct or commission security assessments
    (ii) [Company] may request security certifications (SOC 2, ISO 27001)
    (iii) [Company] may audit data protection compliance

(c) Audit Costs: [Company] bears costs unless audit reveals material 
non-compliance (>5% SLA deviation), then [Vendor] reimburses audit costs.

(d) Remediation: [Vendor] develops remediation plan within [14] days of 
audit findings. [Company] monitors remediation progress.

(e) Confidentiality: [Company] maintains [Vendor]'s audit results in confidence.

(f) Cooperation: [Vendor] provides requested documentation within [5] business days.""",
            rationale=(
                'Provides visibility into vendor performance and compliance. '
                'Identifies hidden non-compliance before it becomes a problem. '
                'Mandatory for vendors processing personal data.'
            ),
            statutory_basis='Digital Personal Data Protection Act, 2023',
            negotiation_hints=[
                'Vendors may resist on-site audits; offer remote alternatives',
                'Frequency (annual, bi-annual) is negotiable',
                'Cap audit costs reasonable to both parties',
                'Make confidentiality mutual',
                'Especially important for data-handling vendors'
            ],
            priority_level='high',
            estimated_difficulty=3
        )
    
    def _get_termination_suggestion(self) -> ClauseSuggestion:
        """Get termination for convenience clause suggestion"""
        return ClauseSuggestion(
            clause_type='termination_for_convenience',
            tier=SuggestionTier.TIER_2_IMPORTANT,
            title='Termination for Convenience',
            purpose='Allow company to exit without cause',
            recommended_language="""TERMINATION FOR CONVENIENCE

(a) Right: [Company] may terminate without cause with [60] days' notice. 
[Vendor] may terminate without cause with [180] days' notice.

(b) Effect: Upon termination:
    (i) [Vendor] ceases performance and transitions work
    (ii) All Confidential Information returned or destroyed
    (iii) [Vendor] provides cooperation for [30] days at [hourly rate]

(c) Termination Fees:
    (i) Before [Year 1]: [Vendor] receives [20%] of remaining value, max [12 months]
    (ii) After [Year 1]: No termination fee
    (iii) If due to [Vendor] breach: No termination fee

(d) Accrued Obligations: [Company] pays for services through notice period.

(e) Survival: Confidentiality, indemnity, and liability limits survive termination.

(f) Return: Equipment and data returned within [10] days of termination.""",
            rationale=(
                'Allows company flexibility to exit underperforming relationships. '
                'Protects against technology obsolescence. '
                'Termination fees compensate vendor for investment.'
            ),
            statutory_basis='Indian Contract Act, 1872, Section 48',
            negotiation_hints=[
                'Notice period: 30-90 days typical (longer for strategic)',
                'Termination fees: 10-30% of remaining value',
                'Asymmetric notice periods reasonable (Company shorter)',
                'Transition services: free for 30 days typical',
                'Software/SaaS vendors often resist; offset with fees'
            ],
            priority_level='high',
            estimated_difficulty=2
        )
    
    def _get_sla_suggestion(self) -> ClauseSuggestion:
        """Get SLA clause suggestion"""
        return ClauseSuggestion(
            clause_type='sla',
            tier=SuggestionTier.TIER_2_IMPORTANT,
            title='Service Level Agreement (SLA)',
            purpose='Define quantifiable performance standards',
            recommended_language="""SERVICE LEVEL AGREEMENT

(a) Availability: [Vendor] shall maintain service availability of [99.5%] 
during Business Hours, measured monthly on trailing 30-day basis.

(b) Measurement: Availability = (Total Minutes - Downtime)/Total Minutes × 100%
    Downtime excludes: (i) maintenance with 72-hour notice, 
    (ii) force majeure, (iii) customer-caused issues

(c) Performance Targets:
    - Mean Time To Respond: Critical < 1 hour, High < 4 hours
    - Mean Time To Resolution: Critical < 8 hours, High < 24 hours
    - Ticket Response: 95% within SLA

(d) Support Escalation:
    - Level 1: Initial support (< 1 hour)
    - Level 2: Senior engineer (< 4 hours)
    - Level 3: Executive escalation (< 24 hours)

(e) Credits: Performance failures trigger service credits per Section [X].

(f) Out of Scope: SLA excludes:
    (i) Customer misconfiguration
    (ii) Unauthorized modifications
    (iii) Third-party products/services
    (iv) Force majeure events""",
            rationale=(
                'Converts subjective "best efforts" to objective measurement. '
                'Provides recourse for poor performance through credits. '
                'Aligns vendor incentives with company needs.'
            ),
            statutory_basis='Indian Contract Act, 1872, Sections 55-75',
            negotiation_hints=[
                'SLA percentages: 99.5-99.99% typical',
                'Credits: 5-25% per SLA breach typical',
                'Response times: 1-4 hour range typical',
                'Monthly measurement period standard',
                'Exclude maintenance windows and force majeure'
            ],
            priority_level='high',
            estimated_difficulty=3
        )
    
    def _get_tier_3_suggestions(
        self,
        clause_scores: List[Dict[str, Any]],
        existing_clause_types: List[str]
    ) -> List[ClauseSuggestion]:
        """Get Tier 3 (Recommended) clause suggestions"""
        suggestions = []
        
        # Limitation of remedies if high-risk contract
        if 'limitation_of_remedies' not in existing_clause_types:
            suggestions.append(self._get_limitation_of_remedies_suggestion())
        
        return suggestions
    
    def _get_limitation_of_remedies_suggestion(self) -> ClauseSuggestion:
        """Get limitation of remedies clause"""
        return ClauseSuggestion(
            clause_type='limitation_of_remedies',
            tier=SuggestionTier.TIER_3_RECOMMENDED,
            title='Limitation of Remedies',
            purpose='Define exclusive remedies and avoid litigation',
            recommended_language="""REMEDIES

(a) Exclusive: Remedies provided in this Agreement (SLA credits, refund 
rights, termination rights) are exclusive remedies for breach, whether in 
contract, tort, or otherwise.

(b) SLA Credits: When [Vendor] fails to meet SLA targets:
    - Availability < 99.5% but >= 99.0%: 5% service credit
    - Availability < 99.0% but >= 98.0%: 10% service credit
    - Availability < 98.0%: 25% service credit

(c) Credit Redemption: Credits applied against next month's invoice. 
Unused credits expire [12] months after accrual.

(d) Limitations: 
    (i) Credits are sole remedy for availability failures
    (ii) Total monthly credits capped at 100% of that month's fees
    (iii) Credits do not relieve [Vendor] of performance obligations

(e) No Consequential: Except for indemnity obligations, neither party 
liable for lost profits, lost revenue, or business interruption.""",
            rationale=(
                'Provides predictable remedy (credits) reducing litigation risk. '
                'Aligns incentives without extreme penalties. '
                'Reduces legal costs and disputes.'
            ),
            statutory_basis='Indian Contract Act, 1872, Sections 73-74',
            negotiation_hints=[
                'Vendors prefer predictable remedies over litigation',
                'Credit percentages: 5-25% typical',
                'Monthly cap: 100% of fees typical',
                'Can be combined with other remedies (termination, refund)'
            ],
            priority_level='medium',
            estimated_difficulty=2
        )
    
    def _tier_priority(self, tier: SuggestionTier) -> int:
        """Convert tier to numeric priority"""
        tier_map = {
            SuggestionTier.TIER_1_CRITICAL: 1,
            SuggestionTier.TIER_2_IMPORTANT: 2,
            SuggestionTier.TIER_3_RECOMMENDED: 3,
        }
        return tier_map.get(tier, 4)


def generate_contract_improvement_report(
    clause_scores: List[Dict[str, Any]],
    existing_clause_types: List[str],
    contract_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate comprehensive contract improvement report with suggestions.
    
    Args:
        clause_scores: List of analyzed clauses with risk assessments
        existing_clause_types: List of clause types in the contract
        contract_type: Type of contract (MSA, NDA, SLA, etc.)
    
    Returns:
        Report containing suggestions, gaps, and improvement roadmap
    """
    engine = ClauseSuggestionEngine()
    
    # Get all suggestions
    suggestions = engine.analyze_contract_gaps(
        clause_scores,
        existing_clause_types,
        contract_type
    )
    
    # Categorize by tier
    tier_1 = [s for s in suggestions if s.tier == SuggestionTier.TIER_1_CRITICAL]
    tier_2 = [s for s in suggestions if s.tier == SuggestionTier.TIER_2_IMPORTANT]
    tier_3 = [s for s in suggestions if s.tier == SuggestionTier.TIER_3_RECOMMENDED]
    
    return {
        'total_suggestions': len(suggestions),
        'gaps_identified': len(existing_clause_types),
        'improvement_potential': round((len(tier_1) + len(tier_2)) / (len(suggestions) + 1) * 100),
        'tier_1_critical': [
            {
                'clause_type': s.clause_type,
                'title': s.title,
                'purpose': s.purpose,
                'difficulty': s.estimated_difficulty,
                'priority': s.priority_level,
            }
            for s in tier_1
        ],
        'tier_2_important': [
            {
                'clause_type': s.clause_type,
                'title': s.title,
                'purpose': s.purpose,
                'difficulty': s.estimated_difficulty,
                'priority': s.priority_level,
            }
            for s in tier_2
        ],
        'tier_3_recommended': [
            {
                'clause_type': s.clause_type,
                'title': s.title,
                'purpose': s.purpose,
                'difficulty': s.estimated_difficulty,
                'priority': s.priority_level,
            }
            for s in tier_3
        ],
        'recommendations': [
            {
                'clause_type': s.clause_type,
                'title': s.title,
                'rationale': s.rationale,
                'negotiation_hints': s.negotiation_hints,
                'difficulty_level': s.estimated_difficulty
            }
            for s in suggestions[:10]  # Top 10 prioritized suggestions
        ]
    }
