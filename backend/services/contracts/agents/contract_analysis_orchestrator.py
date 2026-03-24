"""
DeepAgents Contract Analysis Orchestration
Coordinates the multi-stage contract analysis workflow:
1. Clause Segmentation & Vectorization
2. Semantic Rule Retrieval
3. Legal Reasoning (Mistral LLM)
4. Validation & Storage
"""

import logging
import json
import re
from typing import Dict, List, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime

from deepagents import create_deep_agent
from langchain_anthropic import ChatAnthropic
from langchain_mistralai import ChatMistralAI
from langgraph.checkpoint.memory import MemorySaver

from shared.database.models import Contract, Clause, ClauseSeverity, ContractStatus
from sqlalchemy.orm import Session

from services.contracts.utils.mistral_embeddings import get_mistral_embedder
from services.contracts.utils.chromadb_manager import get_chromadb_manager
from services.contracts.utils.paddle_ocr_extractor import get_ocr_extractor
from services.contracts.utils.web_search import search_and_cache

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


class ContractAnalysisOrchestrator:
    """
    Orchestrates the entire contract analysis workflow using DeepAgents
    Manages coordination between specialized analysis subagents
    """
    
    def __init__(self, db: Session):
        """
        Initialize the orchestrator
        
        Args:
            db: SQLAlchemy database session for storing results
        """
        self.db = db
        self.embedder = get_mistral_embedder()
        self.chromadb = get_chromadb_manager()
        self.ocr = get_ocr_extractor()
        
        # Initialize checkpointer for agent memory
        self.checkpointer = MemorySaver()
        
        logger.info("Initialized Contract Analysis Orchestrator")
    
    def create_analysis_graph(self, web_search_context: Optional[str] = None) -> Any:
        """
        Create the main contract analysis orchestration graph with subagents
        
        Returns:
            Compiled DeepAgents graph for contract analysis
        """
        
        # Define specialized subagents
        clause_analysis_subagent = {
            "name": "clause-analyzer",
            "description": "Expert in segmenting contracts into atomic clauses and identifying clause types",
            "system_prompt": """You are an expert legal document analyst specializing in clause segmentation.
            
Your task is to:
1. Parse the extracted contract text into logical, atomic clauses
2. Identify clause types (Indemnity, IP Rights, Liability, Termination, Warranty, etc.)
3. Detect clause positions and boundaries
4. Tag each clause with appropriate metadata (section, type, severity potential)

Output must be valid JSON with structure:
{
    "clauses": [
        {
            "clause_number": int,
            "section_title": str,
            "clause_type": str,
            "raw_text": str,
            "is_standard": bool
        }
    ],
    "total_clauses": int,
    "document_structure": str
}""",
            "tools": []
        }
        
        legal_reasoning_subagent = {
            "name": "legal-reasoner",
            "description": "Expert in legal analysis using Mistral LLM for risk assessment",
            "system_prompt": """You are an expert legal counsel specializing in contract analysis and risk assessment.

For each clause provided, you will:
1. Analyze the clause against Indian statutory law (Indian Contract Act 1872, etc.)
2. Identify any non-standard or risky terms
3. Flag missing mandatory clauses
4. Detect jurisdiction mismatches
5. Provide detailed legal reasoning for findings
6. Assign risk severity (CRITICAL, HIGH, MEDIUM, LOW, INFO)

Output must be valid JSON for each clause with:
{
    "clause_number": int,
    "legal_reasoning": str,
    "severity": str,
    "risk_description": str,
    "applicable_statute": str,
    "statute_section": str,
    "confidence_score": int,
    "is_standard": bool,
    "is_missing_mandatory": bool,
    "is_jurisdiction_mismatch": bool
}

Additionally, if a mandatory protection is missing (for example IP ownership, indemnity,
liability cap, dispute resolution mechanism, force majeure, or acceptance criteria),
emit a synthetic finding with:
- clause_type starting with "Missing "
- severity set based on impact
- is_missing_mandatory = true
- risk_description and legal_reasoning explaining the business/legal impact.""",
            "tools": []
        }
        
        validator_subagent = {
            "name": "validator",
            "description": "Expert in validating AI findings and computing confidence scores",
            "system_prompt": """You are an expert validator ensuring quality of contract analysis results.

Your task is to:
1. Validate semantic accuracy of clause text extraction
2. Check consistency of legal reasoning
3. Cross-reference findings against precedents
4. Compute final confidence scores (0-100)
5. Flag any contradictions or anomalies
6. Generate overall contract risk score

Output must be valid JSON:
{
    "validation_status": "validated" | "requires_review",
    "overall_risk_score": int,
    "critical_issues": int,
    "high_issues": int,
    "quality_metrics": {
        "text_extraction_accuracy": int,
        "legal_reasoning_confidence": int,
        "precedent_match_score": int
    },
    "recommendations": [str]
}""",
            "tools": []
        }
        
        # Main orchestrator system prompt
        orchestrator_prompt = """You are the Contract Analysis Orchestrator managing a multi-stage legal document analysis workflow.

Your responsibilities:
1. Review the extracted contract text from OCR (with confidence metrics)
2. Break down the analysis into stages:
   a. Delegate clause segmentation to the clause-analyzer subagent
   b. Send identified clauses to the legal-reasoner subagent for analysis
   c. Validate results with the validator subagent
3. Aggregate all findings into a comprehensive risk analysis report
4. Store all clause embeddings in the vector database
5. Generate final recommendations

You have access to:
- PaddleOCR extraction results (raw text, confidence scores)
- Mistral embeddings for semantic analysis
- ChromaDB for storing and retrieving clause vectors
- Subagents for specialized analysis tasks

Maintain context throughout the workflow and ensure data consistency.

ExternalLegalContext:
{web_search_context}
"""
        
        # Format prompt with any external web context provided
        try:
            orchestrator_prompt = orchestrator_prompt.format(web_search_context=(web_search_context or "No external web context available."))
        except Exception:
            pass

        # Create main orchestrator agent with subagents
        agent = create_deep_agent(
            name="contract-analyzer",
            model="mistral-medium",  # Using Mistral Medium as specified
            system_prompt=orchestrator_prompt,
            tools=[],  # Built-in file system and planning tools available
            subagents=[
                clause_analysis_subagent,
                legal_reasoning_subagent,
                validator_subagent
            ],
            checkpointer=self.checkpointer  # Enable memory across invocations
        )
        
        return agent
    
    async def analyze_contract(
        self,
        contract: Contract,
        tenant_id: UUID,
        file_path: str
    ) -> Dict[str, Any]:
        """
        Execute the complete contract analysis workflow
        
        Args:
            contract: Contract model instance
            tenant_id: Tenant UUID
            file_path: Path to the contract PDF file
        
        Returns:
            Dict with analysis results including clauses and risk scores
        """
        try:
            logger.info(f"Starting contract analysis for contract {contract.id}")
            
            # Step 1: Extract text using PaddleOCR
            logger.info("Step 1: Extracting text with PaddleOCR")
            extraction_result = self.ocr.extract_from_pdf(file_path)
            
            if extraction_result['error']:
                logger.error(f"OCR extraction failed: {extraction_result['error']}")
                return {
                    'status': 'failed',
                    'error': extraction_result['error']
                }
            
            raw_text = extraction_result['raw_text']
            confidence = extraction_result['confidence_percentage']
            
            # Update contract with extraction results
            contract.raw_text = raw_text
            contract.text_extraction_confidence = confidence
            contract.status = ContractStatus.PROCESSING
            self.db.commit()
            
            # Step 2: Enrich with web-based legal context and create agent
            logger.info("Step 2: Performing web search for legal context (ddgs)")
            try:
                web_results = search_and_cache(self.db, tenant_id, "Indian contract law " + (contract.contract_type or ""), max_results=5)
            except Exception:
                web_results = []

            # Build a short textual summary of results to pass into the orchestrator
            web_context_snippets = []
            for r in (web_results or [])[:5]:
                title = r.get("title") or r.get("href") or ""
                body = r.get("body") or r.get("snippet") or ""
                web_context_snippets.append(f"- {title}: {body}")
            web_context = "\n".join(web_context_snippets) if web_context_snippets else "No external web context available."

            logger.info("Step 3: Creating analysis orchestrator agent")
            agent = self.create_analysis_graph(web_search_context=web_context)
            
            # Prepare input for agent
            analysis_prompt = f"""Analyze this contract text and provide comprehensive risk analysis.

CONTRACT TEXT:
{raw_text}

Please:
1. Segment the text into individual clauses
2. Analyze each clause for legal risks using Indian statutory law
3. Validate findings and compute confidence scores
4. Generate embeddings for semantic search
5. Return structured JSON with all findings"""
            
            logger.info("Step 3: Invoking analysis agent with streaming")
            try:
                result = self._stream_analyze_contract(
                    agent=agent,
                    contract_id=contract.id,
                    analysis_prompt=analysis_prompt
                )
            except Exception as api_error:
                error_str = str(api_error)
                if "401" in error_str or "Unauthorized" in error_str or "MISTRAL_API_KEY" in error_str:
                    logger.warning(f"Mistral API unavailable ({error_str}), using fallback analysis")
                    # Return fallback results instead of crashing
                    analysis_data = self._create_fallback_analysis(raw_text)
                    contract.status = ContractStatus.ANALYZED
                    contract.overall_risk_score = 0
                    contract.total_clauses_found = 0
                    contract.critical_issues = 0
                    contract.high_issues = 0
                    self.db.commit()
                    
                    return {
                        'status': 'completed',
                        'contract_id': str(contract.id),
                        'analysis': analysis_data,
                        'message': 'Contract analysis completed (text extraction only - Mistral API unavailable)',
                        'warning': 'Full AI analysis unavailable. Please provide valid MISTRAL_API_KEY in .env'
                    }
                else:
                    raise
            
            # Step 3: Process agent output and store results
            logger.info("Step 4: Processing analysis results")
            analysis_data = self._parse_agent_output(result)
            analysis_data = self._augment_with_missing_mandatory_clauses(
                raw_text=raw_text,
                analysis_data=analysis_data
            )
            logger.info(
                "Parse summary: captured_payloads=%s parsed_clauses=%s overall_risk_score=%s",
                len(result.get('captured_payloads', []) if isinstance(result, dict) else []),
                len(analysis_data.get('clauses', [])),
                analysis_data.get('risk_scores', {}).get('overall_risk_score', 0)
            )

            captured_payload_count = len(result.get('captured_payloads', []) if isinstance(result, dict) else [])
            parsed_clause_count = len(analysis_data.get('clauses', []))
            if parsed_clause_count == 0 and captured_payload_count > 0:
                raise ValueError(
                    "Agent produced payloads but no clauses were parsed. "
                    "Aborting update to avoid persisting empty analysis."
                )
            
            # Step 4: Generate embeddings and store in ChromaDB
            logger.info("Step 5: Generating embeddings and storing in vector DB")
            await self._store_clauses_with_embeddings(
                contract_id=contract.id,
                tenant_id=tenant_id,
                clauses=analysis_data.get('clauses', [])
            )
            
            # Step 5: Update contract with final results
            logger.info("Step 6: Updating contract with analysis results")
            self._update_contract_with_results(contract, analysis_data)
            
            logger.info(f"✓ Contract analysis completed successfully for {contract.id}")
            
            return {
                'status': 'completed',
                'contract_id': str(contract.id),
                'analysis': analysis_data,
                'message': 'Contract analysis completed successfully'
            }
            
        except Exception as e:
            logger.error(f"Contract analysis failed: {str(e)}", exc_info=True)
            try:
                contract.status = ContractStatus.ANALYSIS_FAILED
                self.db.commit()
            except Exception as status_error:
                # Some databases may not yet have the new enum value.
                self.db.rollback()
                logger.warning(
                    "Could not persist analysis_failed status (likely enum mismatch): %s",
                    str(status_error)
                )
                try:
                    contract.status = ContractStatus.PROCESSING
                    self.db.commit()
                except Exception:
                    self.db.rollback()
            
            return {
                'status': 'failed',
                'error': str(e),
                'contract_id': str(contract.id)
            }
    
    def _parse_agent_output(self, agent_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse the agent's output and extract structured analysis results
        
        Args:
            agent_result: Raw output from the DeepAgents orchestrator (streaming or invoke format)
        
        Returns:
            Dict with structured analysis data
        """
        try:
            analysis_data = {
                'clauses': [],
                'risk_scores': {},
                'recommendations': []
            }

            text_payloads = self._collect_text_payloads(agent_result)
            if not text_payloads:
                logger.warning("No textual payloads found in agent result")
                return {'clauses': [], 'error': 'No agent output', 'analysis_mode': 'fallback'}

            clause_index: Dict[int, Dict[str, Any]] = {}
            for payload in text_payloads:
                for candidate in self._extract_json_candidates(payload):
                    try:
                        parsed = json.loads(candidate)
                    except json.JSONDecodeError:
                        continue
                    self._merge_parsed_payload(parsed, analysis_data, clause_index)

            if clause_index:
                analysis_data['clauses'] = [
                    clause_index[k] for k in sorted(clause_index.keys())
                ]

            logger.info(f"Parsed {len(analysis_data['clauses'])} clauses from agent output")
            return analysis_data
            
        except Exception as e:
            logger.error(f"Failed to parse agent output: {str(e)}", exc_info=True)
            return {'clauses': [], 'error': str(e), 'analysis_mode': 'fallback'}

    def _collect_text_payloads(self, agent_result: Dict[str, Any]) -> List[str]:
        """Collect text payloads from multiple DeepAgents result formats."""
        payloads: List[str] = []

        # Streaming collector payloads (preferred when available)
        captured = agent_result.get('captured_payloads', [])
        if isinstance(captured, list):
            payloads.extend(str(p) for p in captured if p)

        # Direct messages at top level
        messages = agent_result.get('messages', [])
        if isinstance(messages, list):
            for msg in messages:
                content = msg.get('content') if isinstance(msg, dict) else getattr(msg, 'content', None)
                if content:
                    if isinstance(content, (dict, list)):
                        payloads.append(json.dumps(content, ensure_ascii=True))
                    else:
                        payloads.append(str(content))

        # Nested final_state / node states
        states_to_scan = []
        final_state = agent_result.get('final_state')
        if isinstance(final_state, dict):
            states_to_scan.append(final_state)
        if isinstance(agent_result, dict):
            states_to_scan.append(agent_result)

        for state in states_to_scan:
            for node_state in state.values() if isinstance(state, dict) else []:
                if not isinstance(node_state, dict):
                    continue
                node_messages = node_state.get('messages', [])
                if not isinstance(node_messages, list):
                    continue
                for msg in node_messages:
                    content = msg.get('content') if isinstance(msg, dict) else getattr(msg, 'content', None)
                    if content:
                        if isinstance(content, (dict, list)):
                            payloads.append(json.dumps(content, ensure_ascii=True))
                        else:
                            payloads.append(str(content))

        # Preserve order while deduplicating
        deduped = list(dict.fromkeys(payloads))
        return deduped

    def _extract_json_candidates(self, text: str) -> List[str]:
        """Extract likely JSON snippets from markdown/codefences/plain text."""
        candidates: List[str] = []

        if not text:
            return candidates

        # Prefer fenced JSON blocks when present
        fence_matches = re.findall(r"```(?:json)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
        for block in fence_matches:
            block = block.strip()
            if block:
                candidates.append(block)

        # Fallback: scan balanced JSON objects/arrays from raw text
        starts = [i for i, ch in enumerate(text) if ch in '{[']
        for start in starts:
            stack: List[str] = []
            for i in range(start, len(text)):
                ch = text[i]
                if ch in '{[':
                    stack.append(ch)
                elif ch in '}]':
                    if not stack:
                        break
                    opener = stack.pop()
                    if (opener == '{' and ch != '}') or (opener == '[' and ch != ']'):
                        break
                    if not stack:
                        snippet = text[start:i + 1].strip()
                        if snippet:
                            candidates.append(snippet)
                        break

        # Small dedupe to keep parser efficient
        return list(dict.fromkeys(candidates))

    def _merge_parsed_payload(
        self,
        payload: Any,
        analysis_data: Dict[str, Any],
        clause_index: Dict[int, Dict[str, Any]]
    ) -> None:
        """Merge parsed JSON payloads from subagents into unified analysis data."""

        def upsert_clause(clause_like: Dict[str, Any]) -> None:
            normalized = self._normalize_clause_payload(clause_like)
            number = normalized['clause_number']
            if number in clause_index:
                clause_index[number].update({k: v for k, v in normalized.items() if v not in (None, '', [])})
            else:
                clause_index[number] = normalized

        if isinstance(payload, dict):
            if isinstance(payload.get('clauses'), list):
                for c in payload['clauses']:
                    if isinstance(c, dict):
                        upsert_clause(c)

            if isinstance(payload.get('legal_analysis'), list):
                for item in payload['legal_analysis']:
                    if isinstance(item, dict):
                        upsert_clause(item)

            if isinstance(payload.get('risk_analysis'), list):
                for item in payload['risk_analysis']:
                    if isinstance(item, dict):
                        upsert_clause(item)

            if isinstance(payload.get('validation_results'), list):
                for item in payload['validation_results']:
                    if isinstance(item, dict):
                        upsert_clause(item)

            if isinstance(payload.get('recommendations'), list):
                analysis_data['recommendations'] = payload['recommendations']

            if 'overall_risk_score' in payload:
                analysis_data['risk_scores'].update({
                    'overall_risk_score': payload.get('overall_risk_score', 0),
                    'critical_issues': payload.get('critical_issues', 0),
                    'high_issues': payload.get('high_issues', 0)
                })

        elif isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict):
                    upsert_clause(item)

    def _normalize_clause_payload(self, clause_like: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize heterogeneous clause/risk JSON shapes into DB-ready clause schema."""
        clause_number = clause_like.get('clause_number') or clause_like.get('clause_id') or clause_like.get('id') or 0
        try:
            clause_number = int(clause_number)
        except Exception:
            # Handles IDs like "CLAUSE_1" or "Clause-12".
            number_match = re.search(r"(\d+)", str(clause_number))
            clause_number = int(number_match.group(1)) if number_match else 0

        risks = clause_like.get('risks') or []
        first_risk = risks[0] if isinstance(risks, list) and risks and isinstance(risks[0], dict) else {}

        severity = (
            clause_like.get('severity')
            or clause_like.get('risk_level')
            or first_risk.get('severity')
            or first_risk.get('risk_level')
            or 'info'
        )
        severity = str(severity).lower()
        if severity not in {'critical', 'high', 'medium', 'low', 'info'}:
            severity = 'info'

        confidence = clause_like.get('confidence_score') or clause_like.get('validation_confidence') or 0
        try:
            confidence = int(float(confidence))
        except Exception:
            confidence = 0

        return {
            'clause_number': clause_number,
            'section_title': clause_like.get('section_title') or clause_like.get('section') or clause_like.get('heading'),
            'clause_type': clause_like.get('clause_type') or clause_like.get('type'),
            'raw_text': (
                clause_like.get('raw_text')
                or clause_like.get('clause_text')
                or clause_like.get('text')
                or clause_like.get('clause')
                or clause_like.get('legal_reasoning')
                or clause_like.get('risk_description')
                or ''
            ),
            'severity': severity,
            'risk_description': clause_like.get('risk_description') or first_risk.get('risk_description') or first_risk.get('description'),
            'legal_reasoning': clause_like.get('legal_reasoning') or clause_like.get('validation_notes') or first_risk.get('legal_reasoning'),
            'confidence_score': confidence,
            'applicable_statute': clause_like.get('applicable_statute') or first_risk.get('applicable_statute'),
            'statute_section': clause_like.get('statute_section') or first_risk.get('statute_section'),
            'is_standard': bool(clause_like.get('is_standard', True)),
            'is_missing_mandatory': bool(clause_like.get('is_missing_mandatory', False)),
            'is_jurisdiction_mismatch': bool(clause_like.get('is_jurisdiction_mismatch', False)),
        }
    
    def _create_fallback_analysis(self, raw_text: str) -> Dict[str, Any]:
        """
        Create a basic analysis when Mistral API is unavailable
        Provides text extraction and basic clause detection without AI analysis
        
        Args:
            raw_text: Extracted contract text
        
        Returns:
            Dict with basic clause structure
        """
        try:
            # Split text into paragraphs as basic "clauses"
            paragraphs = [p.strip() for p in raw_text.split('\n\n') if p.strip()]
            
            clauses = []
            for i, para in enumerate(paragraphs[:10], 1):  # Limit to first 10 for fallback
                # Try to detect section headers
                section_title = None
                clause_type = None
                
                if para.isupper() or ':' in para:
                    section_title = para[:80]  # Use first 80 chars as title
                
                clauses.append({
                    'clause_number': i,
                    'section_title': section_title,
                    'clause_type': clause_type,
                    'raw_text': para,
                    'severity': 'info',
                    'risk_description': 'Text extracted - awaiting AI analysis',
                    'confidence_score': 0,
                    'is_standard': True,
                    'is_missing_mandatory': False,
                    'is_jurisdiction_mismatch': False
                })
            
            return {
                'clauses': clauses,
                'error': None,
                'analysis_mode': 'fallback_text_extraction_only'
            }
        except Exception as e:
            logger.error(f"Fallback analysis failed: {str(e)}")
            return {
                'clauses': [],
                'error': str(e),
                'analysis_mode': 'failed'
            }

    def _augment_with_missing_mandatory_clauses(
        self,
        raw_text: str,
        analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add synthetic risk findings for missing mandatory legal protections."""
        clauses = analysis_data.get('clauses', []) or []
        all_text = "\n".join(
            [raw_text] + [str(c.get('raw_text', '')) for c in clauses]
        ).lower()

        def has_any(patterns: List[str]) -> bool:
            return any(re.search(p, all_text, re.IGNORECASE) for p in patterns)

        # Core completeness checks for commercial software/service contracts.
        checks = [
            {
                "name": "Missing IP Ownership",
                "severity": "high",
                "patterns": [r"intellectual\s+property", r"\bip\b", r"ownership\s+of\s+(work|software|deliverables|source\s*code)"] ,
                "risk": "Ownership of created software/work product is not clearly defined.",
                "reasoning": "Absence of IP ownership terms can cause future disputes over reuse, licensing, and commercialization rights."
            },
            {
                "name": "Missing Indemnity",
                "severity": "high",
                "patterns": [r"indemnif(y|ication)", r"hold\s+harmless"],
                "risk": "No indemnity allocation for third-party claims or legal losses.",
                "reasoning": "Indemnity provisions are standard for allocating claim risk between parties."
            },
            {
                "name": "Missing Liability Cap",
                "severity": "medium",
                "patterns": [r"liability\s+shall\s+not\s+exceed", r"aggregate\s+liability", r"cap\s+on\s+liability", r"limited\s+to\s+(fees|contract\s+value|amount\s+paid)"],
                "risk": "No explicit maximum liability cap is defined.",
                "reasoning": "Exclusion of indirect damages alone is not a substitute for an aggregate liability limit."
            },
            {
                "name": "Missing Dispute Resolution",
                "severity": "medium",
                "patterns": [r"arbitration", r"jurisdiction", r"courts?\s+of", r"venue", r"dispute\s+resolution"],
                "risk": "No clear mechanism/forum for dispute resolution is defined.",
                "reasoning": "Governing law without venue/arbitration process leaves procedural ambiguity during disputes."
            },
            {
                "name": "Missing Force Majeure",
                "severity": "medium",
                "patterns": [r"force\s+majeure", r"act\s+of\s+god", r"beyond\s+(reasonable\s+)?control"],
                "risk": "No force majeure protection for unforeseen events.",
                "reasoning": "Contracts should define obligations and relief when events beyond control disrupt performance."
            },
            {
                "name": "Missing Deliverables Acceptance Criteria",
                "severity": "medium",
                "patterns": [r"acceptance\s+criteria", r"acceptance\s+test", r"milestone", r"delivery\s+schedule", r"timeline"],
                "risk": "Deliverable acceptance standards and timeline controls are not explicit.",
                "reasoning": "Undefined acceptance terms increase scope and payment disputes."
            },
        ]

        # Governing law alone does not satisfy dispute resolution quality.
        has_governing_law = has_any([r"governing\s+law", r"laws?\s+of\s+india"])

        max_clause_no = 0
        for c in clauses:
            try:
                max_clause_no = max(max_clause_no, int(c.get('clause_number', 0)))
            except Exception:
                continue

        for check in checks:
            present = has_any(check["patterns"])
            if check["name"] == "Missing Dispute Resolution" and has_governing_law and not present:
                pass

            if present:
                continue

            max_clause_no += 1
            clauses.append({
                'clause_number': max_clause_no,
                'section_title': 'Missing Mandatory Clause',
                'clause_type': check['name'],
                'raw_text': f"Mandatory clause missing: {check['name']}",
                'severity': check['severity'],
                'risk_description': check['risk'],
                'legal_reasoning': check['reasoning'],
                'confidence_score': 92,
                'applicable_statute': 'Indian Contract Act 1872',
                'statute_section': None,
                'is_standard': False,
                'is_missing_mandatory': True,
                'is_jurisdiction_mismatch': False,
            })

        analysis_data['clauses'] = clauses
        return analysis_data
    
    def _stream_analyze_contract(
        self,
        agent,
        contract_id: UUID,
        analysis_prompt: str
    ) -> Dict[str, Any]:
        """
        Stream agent execution to log thinking and model calls
        
        Args:
            agent: DeepAgents orchestrator
            contract_id: Contract UUID for tracking
            analysis_prompt: The analysis prompt to send
        
        Returns:
            Final agent result
        """
        api_call_count = 0
        subagent_states = {}
        final_state = None
        collected_messages = []
        captured_payloads: List[str] = []
        
        logger.info(f"🚀 Starting streamed analysis for contract {contract_id}")
        logger.info("=" * 80)
        
        try:
            for chunk in agent.stream(
                {
                    "messages": [{
                        "role": "user",
                        "content": analysis_prompt
                    }]
                },
                config={"configurable": {"thread_id": str(contract_id)}},
                stream_mode="updates",
                subgraphs=True,
                version="v2"
            ):
                chunk_type = None
                namespace = ()
                data = None

                if isinstance(chunk, dict) and "type" in chunk and "data" in chunk:
                    chunk_type = chunk.get("type")
                    namespace = chunk.get("ns", ())
                    data = chunk.get("data")
                elif isinstance(chunk, tuple) and len(chunk) == 2:
                    # LangGraph native stream format: (namespace, updates)
                    namespace, data = chunk
                    chunk_type = "updates"
                elif isinstance(chunk, dict):
                    # Some stream modes emit node updates directly
                    chunk_type = "updates"
                    data = chunk
                
                # Determine if this is from main agent or subagent
                is_subagent = any(s.startswith("tools:") for s in namespace)
                source = "subagent" if is_subagent else "MAIN"
                
                if is_subagent:
                    subagent_id = next(s for s in namespace if s.startswith("tools:"))
                else:
                    subagent_id = None
                
                # Handle update chunks (node execution)
                if chunk_type == "updates":
                    # Store the final state - updates mode gives us the latest state
                    final_state = data
                    
                    for node_name, node_data in data.items():
                        if node_name == "model_request" or "model" in str(node_name).lower():
                            api_call_count += 1
                            
                            # Log agent's thinking/reasoning
                            thinking = f"\n[{source}] 🧠 MODEL_CALL #{api_call_count}"
                            if subagent_id:
                                thinking += f" ({subagent_id})"
                            
                            # Try to extract messages from the state
                            try:
                                # node_data contains state dict with messages
                                if isinstance(node_data, dict):
                                    messages = node_data.get("messages", [])
                                    for msg in messages:
                                        collected_messages.append(msg)
                                        if hasattr(msg, 'type') and msg.type == 'ai' and hasattr(msg, 'content'):
                                            content_preview = str(msg.content)[:150]
                                            thinking += f"\n  └─ Reasoning: {content_preview}..."
                                            if getattr(msg, 'content', None):
                                                captured_payloads.append(str(msg.content))
                            except Exception as e:
                                logger.debug(f"Could not extract message details: {e}")
                            
                            logger.info(thinking)
                        
                        elif node_name == "tools":
                            # Tool calls/results from agents
                            if isinstance(node_data, dict):
                                messages = node_data.get("messages", [])
                                for msg in messages:
                                    collected_messages.append(msg)
                                    if hasattr(msg, 'type') and msg.type == "tool":
                                        tool_name = getattr(msg, 'name', 'unknown')
                                        tool_id = getattr(msg, 'tool_call_id', '')
                                        content = getattr(msg, 'content', '')
                                        
                                        # Log tool result with content preview
                                        if tool_name == "task":
                                            # Task tool returns subagent descriptions
                                            content_preview = str(content)[:200] if content else "N/A"
                                            logger.info(f"[{source}] 📋 TASK_SPAWNED: {content_preview[:100]}...")
                                            if content:
                                                if isinstance(content, (dict, list)):
                                                    captured_payloads.append(json.dumps(content, ensure_ascii=True))
                                                else:
                                                    captured_payloads.append(str(content))
                                        elif tool_name == "write_todos":
                                            # This is internal planning - show briefly
                                            logger.debug(f"[{source}] 📝 PLANNING_STEP")
                                        else:
                                            # Other tools
                                            logger.info(f"[{source}] 🔧 TOOL_RESULT: {tool_name}")
                                        
                                        subagent_states[tool_id] = "completed"
        
        except Exception as stream_error:
            logger.error(f"❌ Streaming error: {str(stream_error)}")
            logger.exception(stream_error)
            raise
        
        logger.info("=" * 80)
        logger.info(f"✅ Streaming complete. Total API calls: {api_call_count}")
        logger.info(f"Subagent states: {list(subagent_states.keys())}")
        
        # Log the architecture
        logger.info("\n📊 AGENT EXECUTION SUMMARY:")
        logger.info("-" * 80)
        logger.info("""
🏛️  ARCHITECTURE:
  └─ MAIN ORCHESTRATOR (mistral-medium)
      ├─ Clause Analyzer Subagent 📋
      ├─ Legal Reasoner Subagent ⚖️
      └─ Validator Subagent ✅

📍 WHAT HAPPENED:
1. Main agent called task tool → spawned clause-analyzer
2. Clause-analyzer used write_todos for planning (internal LangGraph step)
3. Clause-analyzer spawned sub-tasks for each clause
4. Main agent called task tool → spawned legal-reasoner
5. Legal-reasoner analyzed clauses for risks
6. Subagents used write_todos to break down complex analyses
7. Results collected and aggregated

⚠️  NOTES:
  • write_todos is an internal DeepAgents planning tool (not shown in output)
  • Each MODEL_CALL represents one LLM API call to Mistral
  • Subagents can run in parallel, reducing total time
  • Task tool spawning = subagent delegation
        """)
        logger.info("-" * 80)
        
        # Return the final state as the result
        return {
            "messages": collected_messages,
            "captured_payloads": captured_payloads,
            "final_state": final_state or {}
        }
    
    async def _store_clauses_with_embeddings(
        self,
        contract_id: UUID,
        tenant_id: UUID,
        clauses: List[Dict[str, Any]]
    ) -> None:
        """
        Generate embeddings for clauses and store in ChromaDB + PostgreSQL
        
        Args:
            contract_id: Contract UUID
            tenant_id: Tenant UUID
            clauses: List of clause dictionaries with analysis
        """
        try:
            # Keep only clauses with meaningful text to satisfy DB model constraints.
            cleaned_clauses = []
            for c in clauses:
                raw_text = str(c.get('raw_text', '')).strip()
                if not raw_text:
                    continue
                c['raw_text'] = raw_text
                cleaned_clauses.append(c)

            if not cleaned_clauses:
                logger.warning("No clause texts to embed")
                return

            # Clear previous clause rows only when we have valid replacements.
            self.db.query(Clause).filter(Clause.contract_id == contract_id).delete()
            self.db.flush()

            clause_texts = [c['raw_text'] for c in cleaned_clauses]
            logger.info("Prepared %s clauses for embedding and persistence", len(clause_texts))
            
            # Generate embeddings in batch (more efficient)
            logger.info(f"Generating embeddings for {len(clause_texts)} clauses")
            embeddings = self.embedder.embed_batch(clause_texts)
            
            # Prepare data for ChromaDB and PostgreSQL
            chromadb_additions = []
            postgres_clauses = []
            
            for i, (clause_data, embedding) in enumerate(zip(cleaned_clauses, embeddings)):
                clause_id = uuid4()
                
                # Prepare ChromaDB data
                chromadb_additions.append({
                    'clause_id': clause_id,
                    'clause_text': clause_data.get('raw_text', ''),
                    'embedding': embedding,
                    'metadata': {
                        'contract_id': str(contract_id),
                        'tenant_id': str(tenant_id),
                        'clause_type': clause_data.get('clause_type', ''),
                        'severity': clause_data.get('severity', 'info'),
                        'clause_number': clause_data.get('clause_number', i + 1),
                        'confidence_score': clause_data.get('confidence_score', 0),
                        'is_standard': clause_data.get('is_standard', True),
                    }
                })
                
                # Create PostgreSQL Clause object
                clause_obj = Clause(
                    contract_id=contract_id,
                    tenant_id=tenant_id,
                    clause_number=clause_data.get('clause_number', i + 1),
                    clause_type=clause_data.get('clause_type'),
                    section_title=clause_data.get('section_title'),
                    raw_text=clause_data.get('raw_text', ''),
                    severity=ClauseSeverity(str(clause_data.get('severity', 'info')).lower()),
                    risk_description=clause_data.get('risk_description'),
                    legal_reasoning=clause_data.get('legal_reasoning'),
                    confidence_score=clause_data.get('confidence_score', 0),
                    chromadb_id=str(clause_id),
                    applicable_statute=clause_data.get('applicable_statute'),
                    statute_section=clause_data.get('statute_section'),
                    is_standard=1 if clause_data.get('is_standard', True) else 0,
                    is_missing_mandatory=1 if clause_data.get('is_missing_mandatory', False) else 0,
                    is_jurisdiction_mismatch=1 if clause_data.get('is_jurisdiction_mismatch', False) else 0,
                )
                postgres_clauses.append(clause_obj)
            
            # Store in PostgreSQL
            if postgres_clauses:
                logger.info(f"Adding {len(postgres_clauses)} clauses to PostgreSQL")
                self.db.add_all(postgres_clauses)
                self.db.commit()

            # Store in ChromaDB (best effort). DB persistence is primary source of truth.
            if chromadb_additions:
                try:
                    logger.info(f"Adding {len(chromadb_additions)} clauses to ChromaDB")
                    self.chromadb.add_clauses_batch(chromadb_additions)
                except Exception as chroma_error:
                    logger.warning(
                        "ChromaDB insert failed, but PostgreSQL clauses were saved: %s",
                        str(chroma_error)
                    )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to store clauses with embeddings: {str(e)}")
            raise
    
    def _update_contract_with_results(
        self,
        contract: Contract,
        analysis_data: Dict[str, Any]
    ) -> None:
        """
        Update contract metadata with analysis results
        
        Args:
            contract: Contract model to update
            analysis_data: Analysis results dict
        """
        try:
            # Count clauses by severity
            clauses = analysis_data.get('clauses', [])
            contract.total_clauses_found = len(clauses)
            
            severity_count = {
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0,
                'info': 0
            }
            
            for clause in clauses:
                severity = clause.get('severity', 'info').lower()
                if severity in severity_count:
                    severity_count[severity] += 1
            
            contract.critical_issues = severity_count.get('critical', 0)
            contract.high_issues = severity_count.get('high', 0)
            
            # Calculate overall risk score
            risk_scores = analysis_data.get('risk_scores', {})
            model_risk_score = risk_scores.get('overall_risk_score', 0)
            computed_risk_score = min(
                100,
                severity_count['critical'] * 30
                + severity_count['high'] * 18
                + severity_count['medium'] * 10
                + severity_count['low'] * 4
            )
            contract.overall_risk_score = max(model_risk_score, computed_risk_score)
            
            contract.status = ContractStatus.ANALYZED
            contract.updated_at = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"Updated contract {contract.id} with analysis results")
            
        except Exception as e:
            logger.error(f"Failed to update contract: {str(e)}")
            raise


def get_contract_orchestrator(db: Session) -> ContractAnalysisOrchestrator:
    """
    Get contract analysis orchestrator instance
    
    Args:
        db: Database session
    
    Returns:
        ContractAnalysisOrchestrator: Initialized orchestrator
    """
    return ContractAnalysisOrchestrator(db)
