"""
Clause-Specific Risk Recommendations
Generates actionable, non-generic recommendations based on identified risks
"""

from typing import List, Dict, Any

# SPECIFIC RECOMMENDATIONS BY CLAUSE TYPE & RISK LEVEL
SPECIFIC_RECOMMENDATIONS = {
    'Scope of Services': {
        'critical': [
            'Define scope with specific deliverables and exclusions (e.g., "does NOT include design, testing, deployment")',
            'Set boundaries on request frequency, response time, and availability',
            'Add clause: "Out-of-scope services require separate engagement and payment"'
        ],
        'high': [
            'Clarify ambiguous terms: define "consulting", "support", "services"',
            'Add change control process: scope changes must be documented and priced',
            'Specify limitations on concurrent projects or workload'
        ],
        'medium': [
            'Add examples of in-scope vs out-of-scope work',
            'Document assumptions (e.g., "Client provides access to systems")'
        ]
    },
    
    'Payment Terms': {
        'critical': [
            'Remove undefined payment amounts - specify exact price or clear formula',
            'If variable, set minimum and maximum: "Payment shall be X, ranging from Y to Z"',
            'Set specific payment schedule: "Due within 30 days of invoice"'
        ],
        'high': [
            'Add currency: "All payments in Indian Rupees"',
            'Specify payment method and conditions (e.g., "Net 30 from invoice date")',
            'Define late payment: "Late payments incur 2% monthly interest and stop work clause"'
        ],
        'medium': [
            'Clarify when invoices are issued (monthly, milestone, one-time)',
            'Add procedure for disputed invoices'
        ]
    },
    
    'Term & Termination': {
        'critical': [
            'If unilateral termination allowed: require 30-90 day notice period',
            'Add "For Convenience" termination fee: "Immediate termination costs 30 days fees"',
            'Define "Cause" termination clearly: material breach, payment default, etc.'
        ],
        'high': [
            'Make termination mutual and balanced: both parties need same notice period',
            'Add wind-down period: "On termination, provide X days transition assistance"',
            'Specify effect on obligations: "Surviving obligations include confidentiality, payment"'
        ],
        'medium': [
            'Clarify renewal terms if auto-renewal exists',
            'Document process for claiming fees owed at termination'
        ]
    },
    
    'Limitation of Liability': {
        'critical': [
            'DON\'T flag liability limits as HIGH RISK - they protect both parties',
            'Verify limits are mutual: "Each party\'s total liability capped at contract value"',
            'Exclude from cap: "Death, personal injury, confidentiality breach, willful misconduct"'
        ],
        'high': [
            'If cap is low relative to risk: "Liability limited to annual fees (₹50 lakhs)"',
            'Add carve-out language: "This limitation does not apply to gross negligence"'
        ],
        'medium': [
            'Clarify what damages are excluded: indirect, consequential, lost profits',
            'Verify consistency with indemnification clauses'
        ]
    },
    
    'Indemnification': {
        'critical': [
            'MOST CRITICAL: Carve out indemnity for counterparty\'s own negligence',
            'Change: "Indemnify for claims arising from OUR breach/negligence" (not theirs)',
            'Cap indemnity: "Ceiling is 2x annual contract value, not unlimited"',
            'Exclude: "We don\'t indemnify for their use of our product outside approved scope"'
        ],
        'high': [
            'Define covered claims: "Only third-party claims, not internal disputes"',
            'Add notice requirement: "Provide X days notice and cooperation opportunity"',
            'Limit control: "We control defense of claim but settle only with your consent"'
        ],
        'medium': [
            'Clarify timeline: "Indemnity applies for claims filed within 3 years"',
            'Specify documentation: "Provide evidence of loss and damage within 30 days"'
        ]
    },
    
    'Confidentiality': {
        'critical': [
            'Remove "perpetual" confidentiality - set term like "3 years post-termination"',
            'Carve-out: Information excluded from confidentiality: public domain, independently developed',
            'Specify permitted uses: "May disclose to advisors/vendors under NDA"'
        ],
        'high': [
            'Clarify what is "confidential": customer lists? pricing? technical data?',
            'Add legal necessity carve-out: "May disclose if required by law with notice"',
            'Distinguish types of info: customer data, IP, business info'
        ],
        'medium': [
            'Align with data protection requirements',
            'Document return/destruction obligations'
        ]
    },
    
    'Intellectual Property': {
        'critical': [
            'CRITICAL: Preserve pre-existing IP - carve out "Background IP or Foreground IP"',
            'Ownership: "You own deliverables. We retain all tools, frameworks, pre-existing IP"',
            'Licensing: "You get license to use deliverables. Work remains our IP, licensed to you"'
        ],
        'high': [
            'Define what transfers: "Only code written from scratch, not our libraries"',
            'Exclude our IP: "Our existing tools, SDKs, databases remain our property"',
            'Add limitation: "Customer cannot sublicense, resell, or commercialize our IP"'
        ],
        'medium': [
            'Specify source code escrow if needed',
            'Document what customer can modify'
        ]
    },
    
    'Warranties': {
        'critical': [
            'Remove unrealistic warranties: "We warrant software works in ALL systems forever"',
            'Qualify warranties: "Software provided AS-IS except for fitness for intended purpose"',
            'Time-limit warranties: "Warranties apply only during initial delivery period (90 days)"'
        ],
        'high': [
            'Specify warranty scope: "We warrant no viruses, functionality per spec, not stability"',
            'Add remedy limit: "Sole remedy for warranty breach is re-delivery or refund"',
            'Exclude: "Not liable for issues caused by modifications, misuse, or third-party code"'
        ],
        'medium': [
            'Clarify support period and SLAs separately from warranties',
            'Document testing responsibility'
        ]
    },
    
    'Governing Law': {
        'critical': [
            'ALIGN: Ensure governing law matches jurisdiction of contract performance',
            'If conflict: "Governed by Indian Contract Act 1872, disputes in [City] courts"',
            'For international: Add seat of arbitration: "Arbitration in Mumbai under LCIA rules"'
        ],
        'high': [
            'Specify exact jurisdiction: "High Court of Delhi has exclusive jurisdiction"',
            'For arbitration: "Single arbitrator for disputes <₹1 cr, three for larger"',
            'Add interim relief: "Either party can seek court injunction for breach pending arbitration"'
        ],
        'medium': [
            'Clarify notice address and communication method',
            'Specify time limits for bringing claims'
        ]
    },
    
    'Force Majeure': {
        'critical': [
            'If NO force majeure clause: Add one stating "Neither party liable for failure due to force majeure events"',
            'Define events: "earthquake, riot, war, pandemic, govt action, but NOT ordinary market changes"',
            'Add notice: "Affected party must notify within X days and mitigate impact"'
        ],
        'high': [
            'Exclude from relief: "Force majeure does not excuse payment obligations"',
            'Add termination: "If event exceeds Y days, either party can terminate"',
            'Clarify: "Does NOT cover pandemics (unless explicitly listed)"'
        ],
        'medium': [
            'Specify mitigation efforts required',
            'Document evidence needed to invoke force majeure'
        ]
    }
}

def generate_specific_recommendations(
    clause_type: str,
    risk_score: int,
    risk_description: str,
    raw_text: str
) -> List[str]:
    """
    Generate clause-specific, actionable recommendations.
    NOT generic "review with legal team" - actual negotiation points.
    """
    
    recommendations = []
    
    # Determine risk level from score
    if risk_score >= 80:
        risk_level = 'critical'
    elif risk_score >= 60:
        risk_level = 'high'
    elif risk_score >= 40:
        risk_level = 'medium'
    else:
        # No recommendations for low/favorable scores
        return []
    
    # Get clause type recommendations
    normalized_type = clause_type.strip().title()
    
    # Try exact match first
    clause_recs = SPECIFIC_RECOMMENDATIONS.get(normalized_type)
    
    # Try partial match
    if not clause_recs:
        for key in SPECIFIC_RECOMMENDATIONS.keys():
            if key.lower() in normalized_type.lower() or normalized_type.lower() in key.lower():
                clause_recs = SPECIFIC_RECOMMENDATIONS[key]
                break
    
    # If still no match, return empty (no generic recommendations)
    if not clause_recs:
        return []
    
    # Get recommendations for this risk level
    recs_for_level = clause_recs.get(risk_level, [])
    
    # Take top 3 recommendations and add to list
    if recs_for_level:
        recommendations.extend(recs_for_level[:3])
    
    return recommendations


def generate_analysis_context(clause_type: str) -> str:
    """
    Generate context instructions for LLM to improve analysis quality.
    Based on specific clause type and common risks.
    """
    from services.contracts.agents.clause_statute_mapping import get_statute_for_clause
    
    statute_info = get_statute_for_clause(clause_type)
    
    context = f"""
### {clause_type.upper()} CLAUSE ANALYSIS

**Governing Law**: {statute_info['statute']}
**Key Sections**: {', '.join(statute_info['sections'])}

**Key Points**:
{chr(10).join(f"• {point}" for point in statute_info['key_points'])}

**Risk Indicators** (flag if present):
{chr(10).join(f"• {keyword}" for keyword in statute_info['risk_keywords']) if statute_info['risk_keywords'] else "• No specific risk keywords"}

**Example of CRITICAL Risk**:
{statute_info['example_risk']}

**Instructions**:
1. Compare this clause against the statutory defaults above
2. Identify deviations from market standard practices
3. Focus on ACTUAL risks, not textbook concerns
4. Don't flag routine clauses as high-risk
5. Provide SPECIFIC legal basis for risk assessment
"""
    
    return context
