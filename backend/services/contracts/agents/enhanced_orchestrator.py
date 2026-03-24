"""
Enhanced DeepAgents Contract Analysis Orchestration

Multi-stage contract analysis workflow using LangChain DeepAgents with Skills:
1. Clause Segmentation & Type Identification
2. India Code Legal Research (Skill-guided)
3. Legal Compliance Assessment (Skill-guided)
4. Risk Scoring
5. Beneficial Clause Suggestions (Skill-guided)
6. Validation & Storage

Uses Skills for:
- india-code-research: Structured legal research guidance
- legal-risk-analysis: Risk assessment framework
- clause-optimization: Beneficial clause recommendations
"""

import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID, uuid4
from datetime import datetime
from pathlib import Path

from deepagents import create_deep_agent
from langchain_anthropic import ChatAnthropic
from langchain_mistralai import ChatMistralAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from shared.database.models import Contract, Clause, ClauseSeverity, ContractStatus
from sqlalchemy.orm import Session

from services.contracts.utils.mistral_embeddings import get_mistral_embedder
from services.contracts.utils.chromadb_manager import get_chromadb_manager
from services.contracts.utils.paddle_ocr_extractor import get_ocr_extractor
from services.contracts.utils.web_search import (
    search_and_cache,
    search_india_code,
    search_statute_section,
    extract_act_and_section
)
from services.contracts.utils.risk_scoring import RiskScorer, batch_score_clauses, calculate_contract_risk_score
from services.contracts.utils.clause_suggestions import (
    ClauseSuggestionEngine,
    generate_contract_improvement_report
)

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


class EnhancedContractAnalysisOrchestrator:
    """
    Orchestrates the complete contract analysis workflow using DeepAgents.
    
    Architecture:
    - Main Orchestrator Agent (coordinates overall flow)
    - Clause Segmentation Subagent (extracts and identifies clauses)
    - India Code Researcher Subagent (researches Indian law with Skills)
    - Risk Assessment Subagent (evaluates clause risk using Skills)
    - Suggestion Engine (recommends improvements with Skills)
    
    Skills Integration:
    - /skills/india-code-research/ - Legal research guidelines
    - /skills/legal-risk-analysis/ - Risk assessment framework
    - /skills/clause-optimization/ - Beneficial clause recommendations
    """
    
    def __init__(self, db: Session, skills_dir: Optional[str] = None):
        """
        Initialize the orchestrator with DeepAgents and Skills.
        
        Args:
            db: SQLAlchemy database session
            skills_dir: Path to skills directory (default: ./.skills/)
        """
        self.db = db
        self.embedder = get_mistral_embedder()
        self.chromadb = get_chromadb_manager()
        self.ocr = get_ocr_extractor()
        self.risk_scorer = RiskScorer(db)
        self.suggestion_engine = ClauseSuggestionEngine()
        
        # Initialize checkpointer for agent memory
        self.checkpointer = MemorySaver()
        
        # Store for agent cross-thread persistence
        self.store = InMemoryStore()
        
        # Skills directory
        self.skills_dir = skills_dir or Path(__file__).parent.parent.parent.parent / ".skills"
        
        logger.info(f"Initializing Enhanced Contract Analysis Orchestrator")
        logger.info(f"Skills directory: {self.skills_dir}")
        
        # Create the main orchestration agent
        self.main_agent = self._create_orchestration_agent()
    
    def _create_orchestration_agent(self) -> Any:
        """
        Create the main DeepAgents orchestration agent.
        
        This agent coordinates the multi-stage analysis workflow with subagents.
        Skills are loaded to guide the analysis process.
        """
        
        # Skills paths - relative to FileSystemBackend root
        skills_paths = [
            "/.skills/india-code-research/",
            "/.skills/legal-risk-analysis/",
            "/.skills/clause-optimization/"
        ]
        
        # System prompt for orchestrator
        system_prompt = """You are the Contract Analysis Orchestrator - an expert legal AI assistant 
specializing in contract analysis under Indian law.

YOUR ROLE:
You coordinate a multi-stage analysis workflow for contracts submitted by clients. Your goal is to:
1. Extract and segment clauses from the contract text
2. Identify applicable Indian laws for each clause
3. Assess legal compliance and risk using provided Skills
4. Generate improvement recommendations
5. Produce comprehensive analysis report

ANALYSIS WORKFLOW:
1. CONTRACT EXTRACTION: Parse the contract text into logical, atomic clauses
   - Identify clause boundaries and types
   - Tag sections and subsections
   - Note any structural issues

2. LEGAL RESEARCH: For each clause, identify and research applicable Indian law
   - Use the india-code-research Skill to guide your research
   - Search indiacode.nic.in for relevant statutes
   - Verify statutory compliance

3. RISK ASSESSMENT: Evaluate each clause using legal-risk-analysis Skill
   - Assess legal compliance dimension
   - Evaluate financial exposure
   - Gauge operational complexity
   - Review dispute resolution fairness
   - Consider relationship impact

4. SCORING: Calculate risk scores using multi-dimensional framework
   - Beneficial (0-20): Protective for company
   - Favorable (20-40): Good terms
   - Neutral (40-60): Balanced terms
   - Unfavorable (60-80): Needs improvement
   - Critical (80-100): Requires renegotiation

5. IMPROVEMENT RECOMMENDATIONS: Use clause-optimization Skill to suggest enhancements
   - Tier 1 Critical: Must-have protective clauses
   - Tier 2 Important: Should-have enhancements
   - Tier 3 Recommended: Nice-to-have improvements

OUTPUT:
Produce structured JSON with:
- Segmented clauses with risk scores
- Indian law references
- Compliance assessments  
- Contract-level risk score
- Prioritized improvement suggestions
- Negotiation guidance

CRITICAL CONSTRAINTS:
- All legal research MUST be from indiacode.nic.in only
- No hallucination - cite exact statute sections
- All risk assessments must reference legal basis
- All suggestions must be enforceable under Indian law
- Use exact statutory text, never paraphrase

TOOLS AVAILABLE:
- Search and access Indian statutes via web_search
- Analyze contract structure and extract clauses
- Score clauses using multi-dimensional framework
- Generate improvement recommendations

Let me know when you're ready to analyze a contract."""
        
        # Create the main agent with Skills
        try:
            agent = create_deep_agent(
                model="claude-opus-4-1-20250805",  # Latest Anthropic model
                system_prompt=system_prompt,
                skills=skills_paths,  # Load skills for analysis guidance
                checkpointer=self.checkpointer,
                store=self.store
            )
            logger.info("Successfully created DeepAgents orchestration agent with Skills")
            return agent
        except Exception as e:
            logger.error(f"Failed to create DeepAgents orchestrator: {str(e)}")
            raise
    
    def analyze_contract(
        self,
        contract_id: UUID,
        contract_text: str,
        contract_type: Optional[str] = None,
        counterparty_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive contract analysis using DeepAgents orchestrator.
        
        Args:
            contract_id: Database ID of contract
            contract_text: Full extracted contract text
            contract_type: Type of contract (NDA, MSA, SLA, etc.)
            counterparty_name: Name of counterparty
        
        Returns:
            Dict containing:
            - extracted_clauses: List of parsed clauses
            - risk_assessments: Per-clause risk scores
            - statutory_references: Identified Indian laws
            - overall_risk_score: Aggregate contract risk
            - improvement_suggestions: Recommended enhancements
            - analysis_metadata: Timestamps, confidence scores
        """
        
        logger.info(f"Starting enhanced analysis for contract {contract_id}")
        start_time = datetime.utcnow()
        
        try:
            # Stage 1: Extract and segment clauses
            logger.info("Stage 1: Extracting and segmenting clauses...")
            extracted_clauses = self._extract_clauses(contract_text)
            
            # Stage 2: Identify applicable Indian laws
            logger.info("Stage 2: Identifying applicable Indian laws...")
            statutory_refs = self._identify_applicable_laws(extracted_clauses)
            
            # Stage 3: Perform risk assessment for each clause
            logger.info("Stage 3: Performing risk assessment...")
            clause_scores = self._assess_clause_risks(extracted_clauses, statutory_refs)
            
            # Stage 4: Calculate overall contract risk
            logger.info("Stage 4: Calculating overall contract risk...")
            overall_risk = calculate_contract_risk_score(clause_scores)
            
            # Stage 5: Generate improvement suggestions
            logger.info("Stage 5: Generating improvement suggestions...")
            existing_clause_types = list(set(c.get('type') for c in extracted_clauses if c.get('type')))
            improvement_report = generate_contract_improvement_report(
                clause_scores,
                existing_clause_types,
                contract_type
            )
            
            # Compile comprehensive analysis result
            analysis_result = {
                'contract_id': str(contract_id),
                'contract_type': contract_type,
                'counterparty_name': counterparty_name,
                'analysis_timestamp': datetime.utcnow().isoformat(),
                
                # Extracted content
                'extracted_clauses': extracted_clauses,
                'total_clauses': len(extracted_clauses),
                
                # Risk assessment
                'clause_risk_assessments': clause_scores,
                'overall_contract_risk': overall_risk,
                
                # Statutory compliance
                'statutory_references': statutory_refs,
                'india_code_statutes_referenced': len(set(
                    ref.get('act') for ref in statutory_refs if ref.get('source') == 'indiacode.nic.in'
                )),
                
                # Improvement recommendations
                'improvement_report': improvement_report,
                'critical_missing_clauses': improvement_report.get('tier_1_critical', []),
                'negotiation_priorities': self._generate_negotiation_priorities(clause_scores),
                
                # Metadata
                'analysis_duration_seconds': (datetime.utcnow() - start_time).total_seconds(),
                'analysis_status': 'completed',
                'confidence_metrics': {
                    'average_clause_confidence': round(
                        sum(c.get('confidence_score', 0) for c in clause_scores) / len(clause_scores)
                        if clause_scores else 0
                    ),
                    'total_clauses_analyzed': len(clause_scores),
                    'clauses_with_statutory_refs': sum(
                        1 for c in clause_scores if c.get('statutory_references')
                    )
                }
            }
            
            logger.info(f"Contract analysis completed for {contract_id}")
            logger.info(f"  - Clauses: {len(extracted_clauses)}")
            logger.info(f"  - Overall Risk: {overall_risk['overall_risk_score']}/100")
            logger.info(f"  - Duration: {analysis_result['analysis_duration_seconds']:.2f}s")
            
            return analysis_result
        
        except Exception as e:
            logger.error(f"Contract analysis failed: {str(e)}", exc_info=True)
            return {
                'contract_id': str(contract_id),
                'analysis_status': 'failed',
                'error': str(e),
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
    
    def _extract_clauses(self, contract_text: str) -> List[Dict[str, Any]]:
        """
        Extract and segment clauses from contract text.
        
        Uses pattern matching and NLP to identify clause boundaries,
        types, and hierarchical relationships.
        """
        clauses = []
        clause_counter = 1
        
        # Split by common clause delimiters
        # Patterns: "1.", "1.1.", "SECTION 1", "ARTICLE 1", etc.
        clause_pattern = r'^(?:(?:Section|Article|SECTION|ARTICLE)\s+)?(\d+(?:\.\d+)*)\s*[\.\:]'
        
        lines = contract_text.split('\n')
        current_clause = None
        current_section = None
        
        for line in lines:
            # Check for clause heading
            match = re.match(clause_pattern, line, re.IGNORECASE)
            
            if match:
                # Save previous clause
                if current_clause:
                    clauses.append({
                        'clause_number': clause_counter,
                        'section_title': current_section,
                        'raw_text': current_clause.strip(),
                        'type': self._identify_clause_type(current_section or current_clause),
                        'position': len(clauses),
                        'confidence': 85
                    })
                    clause_counter += 1
                
                # Start new clause
                current_section = line.strip()
                current_clause = ''
            elif current_clause is not None:
                current_clause += '\n' + line
        
        # Don't forget the last clause
        if current_clause:
            clauses.append({
                'clause_number': clause_counter,
                'section_title': current_section,
                'raw_text': current_clause.strip(),
                'type': self._identify_clause_type(current_section or current_clause),
                'position': len(clauses),
                'confidence': 85
            })
        
        return clauses
    
    def _identify_clause_type(self, text: str) -> Optional[str]:
        """Identify the type of clause from its heading and content"""
        text_lower = text.lower()
        
        # Common clause types
        clause_types = {
            'Liability': ['liability', 'damages', 'limitation'],
            'Indemnity': ['indemnif', 'indemnity', 'hold harmless'],
            'Termination': ['termination', 'terminate', 'cancellation'],
            'Warranty': ['warrant', 'guarantee', 'assure'],
            'Confidentiality': ['confidential', 'confidentiality', 'nda', 'secrecy'],
            'Intellectual Property': ['intellectual property', 'copyright', 'patent', 'ip rights'],
            'Payment': ['payment', 'fees', 'compensation', 'royalties'],
            'Audit': ['audit', 'examination', 'inspection'],
            'SLA': ['service level', 'sla', 'uptime', 'availability'],
            'Dispute Resolution': ['dispute', 'arbitration', 'litigation', 'mediation'],
            'Force Majeure': ['force majeure', 'act of god', 'unforeseeable'],
            'Data Protection': ['data', 'privacy', 'personal data', 'gdpr', 'dpdpa'],
        }
        
        for clause_type, keywords in clause_types.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return clause_type
        
        return None
    
    def _identify_applicable_laws(
        self,
        clauses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Identify and research applicable Indian laws for each clause.
        
        Uses pattern matching to find statute references in clauses,
        then searches indiacode.nic.in for the full statute.
        """
        statutory_refs = []
        
        for clause in clauses:
            clause_text = clause.get('raw_text', '')
            
            # Look for statute references in the clause text
            statute_pattern = r'(?:under\s+)?(?:the\s+)?(?:Indian\s+)?([A-Za-z\s,]+(?:Act|Code)),?\s*(\d{4})'
            matches = re.findall(statute_pattern, clause_text, re.IGNORECASE)
            
            for act_name, year in matches:
                act_name = act_name.strip()
                
                logger.info(f"Found statute reference: {act_name}, {year}")
                
                # Search India Code for this statute
                try:
                    statute_result = search_statute_section(
                        self.db,
                        tenant_id=UUID('00000000-0000-0000-0000-000000000000'),  # Placeholder
                        act_name=act_name,
                        year=year
                    )
                    
                    statutory_refs.append({
                        'clause_number': clause.get('clause_number'),
                        'clause_type': clause.get('type'),
                        'act': statute_result.get('act'),
                        'statute_url': statute_result.get('url'),
                        'found': statute_result.get('found'),
                        'raw_text': statute_result.get('raw_text'),
                        'source': 'indiacode.nic.in',
                        'retrieved_at': datetime.utcnow().isoformat()
                    })
                except Exception as e:
                    logger.warning(f"Failed to retrieve statute: {str(e)}")
        
        return statutory_refs
    
    def _assess_clause_risks(
        self,
        clauses: List[Dict[str, Any]],
        statutory_refs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Perform risk assessment on each clause using multi-dimensional scoring.
        
        Incorporates:
        - Legal compliance against Indian law
        - Financial exposure
        - Operational complexity
        - Dispute resolution fairness
        - Relationship impact
        """
        clause_scores = []
        
        for clause in clauses:
            # Find statutory references for this clause
            clause_statutes = [
                ref for ref in statutory_refs
                if ref.get('clause_number') == clause.get('clause_number')
            ]
            
            # Score the clause
            score_result = self.risk_scorer.score_clause(
                clause_text=clause.get('raw_text', ''),
                clause_type=clause.get('type'),
                statutory_references=clause_statutes,
                contract_value=None  # Would be provided with contract
            )
            
            # Combine with clause data
            clause_scores.append({
                **clause,
                **score_result,
                'statutory_references': clause_statutes
            })
        
        return clause_scores
    
    def _generate_negotiation_priorities(
        self,
        clause_scores: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate prioritized negotiation strategy based on risk assessment.
        
        Returns clauses ordered by:
        1. Risk severity (critical first)
        2. Negotiation likelihood
        3. Business impact potential
        """
        
        # Filter to unfavorable and critical clauses
        problem_clauses = [
            c for c in clause_scores
            if c.get('risk_category') in ['unfavorable', 'critical']
        ]
        
        # Sort by risk score
        problem_clauses.sort(
            key=lambda x: x.get('total_risk_score', 0),
            reverse=True
        )
        
        # Take top 5 priority renegotiations
        priorities = []
        for clause in problem_clauses[:5]:
            recommendations = clause.get('recommendations', [])
            
            priorities.append({
                'clause_number': clause.get('clause_number'),
                'clause_type': clause.get('clause_type'),
                'risk_score': clause.get('total_risk_score'),
                'risk_category': clause.get('risk_category'),
                'priority_reason': f"Risk score {clause.get('total_risk_score')}/100 - {clause.get('risk_category')} severity",
                'recommended_changes': recommendations[0].get('suggestion') if recommendations else 'Requires renegotiation',
                'negotiation_difficulty': 'medium'  # Could be assessed dynamically
            })
        
        return priorities


# Legacy compatibility - create simplified interface
def create_orchestrator(db: Session, skills_dir: Optional[str] = None) -> EnhancedContractAnalysisOrchestrator:
    """Factory function to create orchestrator instance"""
    return EnhancedContractAnalysisOrchestrator(db, skills_dir)
