"""
Risk Scoring System for Contract Clauses

Implements multi-dimensional risk assessment based on:
1. Legal compliance with Indian law
2. Financial exposure
3. Operational complexity
4. Dispute resolution fairness
5. Relationship impact

Each clause receives a 0-100 risk score and categorical rating.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import json
from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session
from shared.database.models import Clause, ClauseSeverity

logger = logging.getLogger(__name__)


class RiskCategory(str, Enum):
    """Risk severity categories"""
    BENEFICIAL = "beneficial"        # 0-20: Green - protective for company
    FAVORABLE = "favorable"          # 20-40: Light green - favorable terms
    NEUTRAL = "neutral"              # 40-60: Yellow - balanced
    UNFAVORABLE = "unfavorable"      # 60-80: Orange - unfavorable
    CRITICAL = "critical"            # 80-100: Red - highly unfavorable


class RiskScorer:
    """
    Multi-dimensional risk scoring engine for contract clauses.
    
    Scoring dimensions:
    - Legal Compliance Risk: 0-35 points
    - Financial Exposure Risk: 0-25 points
    - Operational Risk: 0-15 points
    - Dispute Resolution Risk: 0-15 points
    - Relationship/Power Dynamic Risk: 0-10 points
    
    Total: 0-100 points
    """
    
    # Dimension weights and scoring ranges
    LEGAL_COMPLIANCE_MAX = 35
    FINANCIAL_EXPOSURE_MAX = 25
    OPERATIONAL_MAX = 15
    DISPUTE_RESOLUTION_MAX = 15
    RELATIONSHIP_MAX = 10
    
    # Keywords that trigger high-risk patterns
    HIGH_RISK_KEYWORDS = {
        'unlimited': 20,
        'any damages': 20,
        'all claims': 15,
        'perpetual': 15,
        'forever': 15,
        'indemnif': 15,  # indemnify, indemnification
        'strict liability': 20,
        'regardless of fault': 15,
        'sole discretion': 10,
        'sole remedy': 5,
        'no warranty': -10,  # Actually favorable (removes liability)
        'as-is': -5,  # Favorable (limits liability)
        'liability limited': -15,  # Favorable
        'cap': -10,  # Cap on liability - favorable
        'exclude': -10,  # Exclusion of damages - favorable
    }
    
    # Keywords indicating protective/favorable clauses
    PROTECTIVE_KEYWORDS = {
        'limitation of liability': -15,
        'excluded from liability': -15,
        'not liable for': -15,
        'not responsible for': -10,
        'indemnify [Company]': -15,
        'indemnify the Company': -15,
        '[Company] is indemnified': -15,
        'no obligation': -5,
        'best efforts': -5,
        'commercially reasonable': -5,
        'non-exclusive': -5,
        'royalty-free': -5,
    }
    
    def __init__(self, db: Session):
        """
        Initialize risk scorer
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def score_clause(
        self,
        clause_text: str,
        clause_type: Optional[str] = None,
        statutory_references: Optional[List[Dict[str, str]]] = None,
        contract_value: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive risk scoring on a clause.
        
        Args:
            clause_text: Full text of the clause
            clause_type: Type of clause (e.g., "Liability", "Indemnity")
            statutory_references: List of applicable statutes with status
            contract_value: Contract value for normalizing financial exposure
        
        Returns:
            Dict containing:
            - total_risk_score: 0-100
            - risk_category: RiskCategory enum
            - dimension_scores: Individual dimension scores
            - detected_patterns: List of risk patterns detected
            - recommendations: Suggested improvements
            - confidence_score: 0-100 confidence in assessment
        """
        
        # Initialize scores
        dimension_scores = {
            'legal_compliance': self._score_legal_compliance(clause_text, statutory_references),
            'financial_exposure': self._score_financial_exposure(clause_text, contract_value),
            'operational': self._score_operational_risk(clause_text),
            'dispute_resolution': self._score_dispute_resolution(clause_text),
            'relationship': self._score_relationship_risk(clause_text)
        }
        
        # Calculate total risk
        total_risk = sum(dimension_scores.values())
        
        # Detect patterns
        detected_patterns = self._detect_risk_patterns(clause_text)
        protective_patterns = self._detect_protective_patterns(clause_text)
        
        # Determine category
        risk_category = self._categorize_risk(total_risk)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            clause_text,
            clause_type,
            detected_patterns,
            total_risk
        )
        
        # Confidence based on keyword matches
        confidence_score = self._calculate_confidence(clause_text, detected_patterns)
        
        return {
            'total_risk_score': min(100, total_risk),  # Cap at 100
            'risk_category': risk_category.value,
            'dimension_scores': dimension_scores,
            'detected_patterns': detected_patterns,
            'protective_patterns': protective_patterns,
            'recommendations': recommendations,
            'confidence_score': confidence_score,
            'clause_type': clause_type,
            'analysis_timestamp': datetime.utcnow().isoformat()
        }
    
    def _score_legal_compliance(
        self,
        clause_text: str,
        statutory_references: Optional[List[Dict[str, str]]] = None
    ) -> int:
        """Score legal compliance dimension (0-35 points)"""
        score = 0
        
        # Check against Indian Contract Act, 1872 restrictions
        # Section 23-27: Agreements opposed to public policy are void
        public_policy_violators = [
            'against public policy',
            'void',
            'illegal',
            'unlawful',
            'unenforceable',
        ]
        
        for violator in public_policy_violators:
            if violator.lower() in clause_text.lower():
                score += 10
        
        # If statutory references provided, check compliance
        if statutory_references:
            non_compliant_count = sum(
                1 for ref in statutory_references 
                if ref.get('compliance_status') == 'non_compliant'
            )
            score += non_compliant_count * 15
        
        # Unconscionable terms (Section 13 - agreement without consent)
        unconscionable_indicators = [
            'unilateral discretion',
            'sole discretion',
            'at my discretion',
            'change at any time',
            'modify unilaterally',
        ]
        
        for indicator in unconscionable_indicators:
            if indicator.lower() in clause_text.lower():
                score += 8
        
        return min(score, self.LEGAL_COMPLIANCE_MAX)
    
    def _score_financial_exposure(
        self,
        clause_text: str,
        contract_value: Optional[float] = None
    ) -> int:
        """Score financial exposure dimension (0-25 points)"""
        score = 0
        text_lower = clause_text.lower()
        
        # Uncapped liability
        if 'unlimited' in text_lower or ('liability' in text_lower and 'cap' not in text_lower):
            score += 15
        
        # Includes consequential damages
        if 'consequential' in text_lower or 'indirect' in text_lower:
            score += 10
        
        # Perpetual liability
        if 'perpetual' in text_lower or 'forever' in text_lower:
            score += 5
        
        # Indemnity obligations (high financial impact)
        if 'indemnify' in text_lower or 'indemnification' in text_lower:
            # Check if it's FOR the company (favorable) or BY the company (unfavorable)
            if 'indemnify the company' in text_lower or 'indemnified by' in text_lower:
                score -= 5  # Favorable
            else:
                score += 8  # Unfavorable
        
        # Liquidated damages
        if 'liquidated damages' in text_lower:
            score += 5
        
        # Try to extract monetary amounts
        import re
        amounts = re.findall(r'\$\s*([\d,]+(?:\.\d{2})?)', clause_text)
        if amounts and contract_value:
            total_exposure = sum(float(a.replace(',', '')) for a in amounts)
            # If exposure > contract value, higher risk
            if total_exposure > contract_value * 2:
                score += 8
            elif total_exposure > contract_value:
                score += 5
        
        return min(score, self.FINANCIAL_EXPOSURE_MAX)
    
    def _score_operational_risk(self, clause_text: str) -> int:
        """Score operational complexity dimension (0-15 points)"""
        score = 0
        text_lower = clause_text.lower()
        
        # Unachievable standards
        unachievable_indicators = [
            '99.99%',
            'guaranteed',
            'always',
            'at all times',
            'without exception',
        ]
        
        for indicator in unachievable_indicators:
            if indicator in text_lower:
                score += 3
        
        # RTO/RPO or SLA requirements (ongoing compliance burden)
        if 'rto' in text_lower or 'rpo' in text_lower or 'sla' in text_lower:
            score += 3
        
        # Audit/inspection rights (operational burden)
        if 'audit' in text_lower or 'inspect' in text_lower or 'monitor' in text_lower:
            score += 2
        
        # Reporting requirements
        if 'report' in text_lower or 'notification' in text_lower:
            score += 1
        
        # Resource-intensive requirements
        resource_indicators = [
            'dedicated',
            'full-time',
            ' 24/7',
            'on-site',
            'round the clock',
        ]
        
        for indicator in resource_indicators:
            if indicator in text_lower:
                score += 2
        
        return min(score, self.OPERATIONAL_MAX)
    
    def _score_dispute_resolution(self, clause_text: str) -> int:
        """Score dispute resolution fairness (0-15 points)"""
        score = 0
        text_lower = clause_text.lower()
        
        # Unfavorable jurisdiction
        unfavorable_locations = [
            'exclusive jurisdiction',
            'sole jurisdiction',
            'only in',
            'shall be brought in',
        ]
        
        for location in unfavorable_locations:
            if location in text_lower:
                score += 5
        
        # Loser pays
        if 'loser pays' in text_lower or 'prevailing party' in text_lower:
            score += 5
        
        # Forced arbitration
        if 'mandatory arbitration' in text_lower or 'must arbitrate' in text_lower:
            score += 3  # Some see as neutral, some unfavorable
        
        # No right to jury trial
        if 'waive' in text_lower and 'jury' in text_lower:
            score += 2
        
        # Confession of judgment (very unfavorable)
        if 'confession of judgment' in text_lower or 'cognovit' in text_lower:
            score += 12
        
        # Limitation period (statute of limitations)
        if 'claim must be made within' in text_lower:
            # This is actually favorable (limits exposure period)
            score -= 3
        
        return max(0, min(score, self.DISPUTE_RESOLUTION_MAX))
    
    def _score_relationship_risk(self, clause_text: str) -> int:
        """Score relationship/power dynamic risk (0-10 points)"""
        score = 0
        text_lower = clause_text.lower()
        
        # Asymmetric obligations (one-way only)
        if ('company shall' in text_lower and 'vendor shall' not in text_lower) or \
           ('vendor shall' in text_lower and 'company shall' not in text_lower):
            score += 5
        
        # Termination rights heavily favor one party
        if ('terminate' in text_lower and 'without cause' in text_lower) and \
           'company may terminate' in text_lower and 'vendor may' not in text_lower:
            score -= 3  # Favorable to company
        elif ('terminate' in text_lower and 'without cause' in text_lower) and \
             'vendor may terminate' in text_lower and 'company may' not in text_lower:
            score += 5  # Unfavorable (vendor can exit)
        
        # Exclusivity requirements
        if 'exclusive' in text_lower and 'non-exclusive' not in text_lower:
            score += 2
        
        # Confidentiality overreach (one-sided)
        if 'confidential' in text_lower:
            if 'mutual' in text_lower or 'both parties' in text_lower:
                score -= 2  # Favorable (mutual)
            else:
                score += 2  # Unfavorable (one-sided)
        
        return max(0, min(score, self.RELATIONSHIP_MAX))
    
    def _detect_risk_patterns(self, clause_text: str) -> List[str]:
        """Detect high-risk patterns in clause"""
        patterns = []
        text_lower = clause_text.lower()
        
        # Pattern detection
        risk_patterns = {
            'unlimited_liability': ['unlimited', 'any damages', 'all claims'],
            'broad_indemnity': ['indemnify', 'indemnification'],
            'strict_liability': ['strict liability', 'regardless of fault'],
            'unilateral_termination': ['terminate', 'without cause', 'immediately'],
            'unachievable_sla': ['99.99%', '99.999%'],
            'unrestricted_ip': ['all work', 'sole property', 'exclusive ownership'],
            'perpetual_obligations': ['perpetual', 'forever', 'in perpetuity'],
            'exclusive_venue': ['exclusive jurisdiction', 'sole jurisdiction'],
            'broad_confidentiality': ['confidential', 'secret', 'proprietary'],
        }
        
        for pattern_name, keywords in risk_patterns.items():
            for keyword in keywords:
                if keyword in text_lower:
                    patterns.append(pattern_name)
                    break
        
        return patterns
    
    def _detect_protective_patterns(self, clause_text: str) -> List[str]:
        """Detect protective patterns favorable to company"""
        patterns = []
        text_lower = clause_text.lower()
        
        protective_patterns = {
            'liability_cap': ['limit', 'cap', 'maximum liability'],
            'damages_exclusion': ['no liability for', 'not liable for'],
            'consequential_exclusion': ['exclude', 'consequential', 'indirect', 'punitive'],
            'company_indemnity': ['indemnify the company', 'indemnify [company]'],
            'strong_warranty': ['warrant', 'guarantee', 'assure'],
            'ip_retention': ['retain', 'pre-existing', 'company owns'],
            'unilateral_termination_company': ['company may terminate', 'company can terminate'],
        }
        
        for pattern_name, keywords in protective_patterns.items():
            for keyword in keywords:
                if keyword in text_lower:
                    patterns.append(pattern_name)
                    break
        
        return patterns
    
    def _categorize_risk(self, score: int) -> RiskCategory:
        """Categorize risk based on score"""
        if score <= 20:
            return RiskCategory.BENEFICIAL
        elif score <= 40:
            return RiskCategory.FAVORABLE
        elif score <= 60:
            return RiskCategory.NEUTRAL
        elif score <= 80:
            return RiskCategory.UNFAVORABLE
        else:
            return RiskCategory.CRITICAL
    
    def _generate_recommendations(
        self,
        clause_text: str,
        clause_type: Optional[str],
        patterns: List[str],
        risk_score: int
    ) -> List[Dict[str, str]]:
        """Generate improvement recommendations"""
        recommendations = []
        
        if risk_score > 70:
            recommendations.append({
                'priority': 'critical',
                'suggestion': 'This clause creates significant risk. Prioritize for renegotiation.',
                'action': 'Schedule negotiation meeting with counterparty'
            })
        
        if 'unlimited_liability' in patterns:
            recommendations.append({
                'priority': 'high',
                'suggestion': 'Add explicit cap on liability (e.g., annual fees or contract value)',
                'action': 'Propose: "Liability capped at 12 months of fees or $XXX"'
            })
        
        if 'broad_indemnity' in patterns:
            recommendations.append({
                'priority': 'high',
                'suggestion': 'Narrow indemnity scope and add exclusions for company negligence',
                'action': 'Add: "...except to the extent caused by Company\'s gross negligence"'
            })
        
        if 'unilateral_termination' in patterns and 'company may terminate' not in clause_text.lower():
            recommendations.append({
                'priority': 'medium',
                'suggestion': 'Add mutual termination rights or notice period',
                'action': 'Propose reciprocal termination for convenience rights'
            })
        
        if 'perpetual_obligations' in patterns:
            recommendations.append({
                'priority': 'medium',
                'suggestion': 'Limit duration of obligations to reasonable period',
                'action': 'Change "perpetual" to "for 3 years after termination"'
            })
        
        return recommendations
    
    def _calculate_confidence(self, clause_text: str, detected_patterns: List[str]) -> int:
        """Calculate confidence score based on pattern detection"""
        # Confidence based on number of keywords matched
        text_length = len(clause_text.split())
        pattern_count = len(detected_patterns)
        
        # More patterns = higher confidence
        confidence = min(100, 40 + (pattern_count * 10) + min(30, text_length // 10))
        
        return confidence


def batch_score_clauses(
    db: Session,
    clauses: List[Dict[str, Any]],
    contract_value: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Score multiple clauses efficiently in batch.
    
    Args:
        db: Database session
        clauses: List of clause dicts with 'text', 'type', and optional 'statutes'
        contract_value: Total contract value for normalization
    
    Returns:
        List of scored clause results
    """
    scorer = RiskScorer(db)
    results = []
    
    for clause in clauses:
        scored = scorer.score_clause(
            clause_text=clause.get('text', ''),
            clause_type=clause.get('type'),
            statutory_references=clause.get('statutes'),
            contract_value=contract_value
        )
        results.append({
            **clause,
            **scored
        })
    
    return results


def calculate_contract_risk_score(clause_scores: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate overall contract risk from individual clause scores.
    
    Aggregation method:
    - Average of clause scores (normalized)
    - Weighted by clause importance
    - Critical clauses weighted 2x
    
    Args:
        clause_scores: List of individual clause risk assessments
    
    Returns:
        Dict with overall_risk_score, risk_category, top_concerns
    """
    if not clause_scores:
        return {
            'overall_risk_score': 0,
            'risk_category': 'no_clauses',
            'top_concerns': [],
            'average_clause_score': 0
        }
    
    # Calculate weighted average
    total_score = 0
    total_weight = 0
    critical_clauses = []
    
    for clause in clause_scores:
        score = clause.get('total_risk_score', 0)
        category = clause.get('risk_category', 'neutral')
        
        # Weight critical clauses 2x
        weight = 2 if category == 'critical' else 1
        
        total_score += score * weight
        total_weight += weight
        
        if category == 'critical':
            critical_clauses.append({
                'clause_type': clause.get('clause_type'),
                'risk_score': score,
                'patterns': clause.get('detected_patterns', [])
            })
    
    overall_score = round(total_score / total_weight) if total_weight > 0 else 0
    overall_category = RiskScorer(None)._categorize_risk(overall_score)
    
    # Top 5 concerns
    top_concerns = sorted(
        clause_scores,
        key=lambda x: x.get('total_risk_score', 0),
        reverse=True
    )[:5]
    
    return {
        'overall_risk_score': overall_score,
        'risk_category': overall_category.value,
        'top_concerns': [
            {
                'clause_type': c.get('clause_type'),
                'risk_score': c.get('total_risk_score'),
                'recommendation': c.get('recommendations', [{}])[0].get('suggestion')
            }
            for c in top_concerns
        ],
        'critical_clauses_count': len(critical_clauses),
        'total_clauses_analyzed': len(clause_scores),
        'average_clause_score': round(sum(c.get('total_risk_score', 0) for c in clause_scores) / len(clause_scores))
    }
