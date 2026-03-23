"""
Contract Management Service - Business Logic
Handles contract lifecycle, analysis orchestration, and risk management
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from shared.database.models import Contract, Clause, ContractStatus, ClauseSeverity, User
from shared.audit.audit_logger import get_audit_logger
from services.contracts.schemas.contract_schemas import (
    ContractUploadRequest,
    ContractResponse,
    RiskAnalysisResponse,
    ClauseResponse,
    ContractListResponse,
)
from services.contracts.utils import (
    get_file_manager,
    get_mistral_embedder,
    get_chromadb_manager,
    get_ocr_extractor
)
from services.contracts.agents import get_contract_orchestrator

logger = logging.getLogger(__name__)


class ContractService:
    """Service layer for contract management operations"""
    
    def __init__(self, db: Session):
        """
        Initialize contract service
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.file_manager = get_file_manager()
        self.audit = get_audit_logger()
        self.embedder = get_mistral_embedder()
        self.chromadb = get_chromadb_manager()
        self.ocr = get_ocr_extractor()
        self.orchestrator = get_contract_orchestrator(db)
        
        logger.info("Initialized Contract Service")
    
    def upload_contract(
        self,
        tenant_id: UUID,
        user_id: UUID,
        file_content: bytes,
        filename: str,
        request: ContractUploadRequest
    ) -> ContractResponse:
        """
        Handle contract upload and initiate analysis
        
        Args:
            tenant_id: Tenant UUID
            user_id: User UUID (uploader)
            file_content: PDF file bytes
            filename: Original filename
            request: ContractUploadRequest schema
        
        Returns:
            ContractResponse: Created contract metadata
            
        Raises:
            Exception: If file save or analysis initiation fails
        """
        try:
            from uuid import uuid4
            
            # Step 1: Generate contract ID upfront (before any DB operations)
            contract_id = uuid4()
            
            # Step 2: Save file to disk FIRST (before creating DB record)
            logger.info(f"Saving contract file: {filename}")
            file_path = self.file_manager.save_contract_file(
                tenant_id=tenant_id,
                contract_id=contract_id,
                file_content=file_content,
                original_filename=filename
            )
            
            if not file_path:
                raise ValueError("File save returned empty path")
            
            logger.info(f"File saved successfully: {file_path}")
            
            # Step 3: Now create contract record with file_path already set
            contract = Contract(
                id=contract_id,
                tenant_id=tenant_id,
                uploaded_by=user_id,
                filename=filename,
                counterparty_name=request.counterparty_name,
                contract_type=request.contract_type,
                file_path=file_path,  # Already has value - no NULL violation
                status=ContractStatus.UPLOADED,
            )
            
            self.db.add(contract)
            self.db.commit()
            
            logger.info(f"Contract {contract_id} created and file saved to {file_path}")
            
            # Step 4: Log upload event (use fresh session since previous one committed)
            self.audit.log_event(
                db=self.db,
                tenant_id=tenant_id,
                user_id=user_id,
                event_type="contract_upload",
                action="upload",
                status="success",
                description=f"Contract uploaded: {filename} → {file_path}"
            )
            
            return self._to_contract_response(contract)
            
        except Exception as e:
            logger.error(f"Failed to upload contract: {str(e)}")
            try:
                self.db.rollback()
                self.audit.log_event(
                    db=self.db,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    event_type="contract_upload",
                    action="upload",
                    status="failure",
                    description=f"Failed to upload contract: {str(e)}"
                )
            except Exception as audit_error:
                logger.error(f"Failed to log audit event: {str(audit_error)}")
            
            raise
    
    async def analyze_contract(
        self,
        contract_id: UUID,
        tenant_id: UUID
    ) -> RiskAnalysisResponse:
        """
        Initiate and perform contract analysis using DeepAgents orchestrator
        
        Args:
            contract_id: Contract UUID
            tenant_id: Tenant UUID
        
        Returns:
            RiskAnalysisResponse: Completed analysis with risk scores
            
        Raises:
            ValueError: If contract not found
            Exception: If analysis fails
        """
        try:
            # Get contract
            contract = self.db.query(Contract).filter(
                and_(Contract.id == contract_id, Contract.tenant_id == tenant_id)
            ).first()
            
            if not contract:
                raise ValueError(f"Contract {contract_id} not found")
            
            logger.info(f"Starting analysis for contract {contract_id}")
            
            # Get full file path
            file_path = self.file_manager.get_contract_file_path(contract.file_path)
            
            # Execute analysis via orchestrator
            result = await self.orchestrator.analyze_contract(
                contract=contract,
                tenant_id=tenant_id,
                file_path=str(file_path)
            )
            
            if result['status'] == 'failed':
                raise Exception(f"Analysis failed: {result.get('error')}")
            
            # Build response
            return self.get_risk_analysis(contract_id, tenant_id)
            
        except Exception as e:
            logger.error(f"Contract analysis failed: {str(e)}")
            raise
    
    def get_contract(
        self,
        contract_id: UUID,
        tenant_id: UUID
    ) -> ContractResponse:
        """
        Get contract metadata by ID
        
        Args:
            contract_id: Contract UUID
            tenant_id: Tenant UUID (for isolation)
        
        Returns:
            ContractResponse: Contract metadata
            
        Raises:
            ValueError: If contract not found
        """
        contract = self.db.query(Contract).filter(
            and_(Contract.id == contract_id, Contract.tenant_id == tenant_id)
        ).first()
        
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")
        
        return self._to_contract_response(contract)
    
    def list_contracts(
        self,
        tenant_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None
    ) -> ContractListResponse:
        """
        List contracts for a tenant with pagination
        
        Args:
            tenant_id: Tenant UUID
            page: Page number (1-indexed)
            page_size: Items per page
            status: Optional filter by status
        
        Returns:
            ContractListResponse: Paginated contract list
        """
        try:
            # Build query
            query = self.db.query(Contract).filter(Contract.tenant_id == tenant_id)
            
            if status:
                query = query.filter(Contract.status == status)
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            offset = (page - 1) * page_size
            contracts = query.order_by(desc(Contract.created_at)).offset(offset).limit(page_size).all()
            
            return ContractListResponse(
                total=total,
                page=page,
                page_size=page_size,
                contracts=[self._to_contract_response(c) for c in contracts]
            )
            
        except Exception as e:
            logger.error(f"Failed to list contracts: {str(e)}")
            raise
    
    def get_risk_analysis(
        self,
        contract_id: UUID,
        tenant_id: UUID
    ) -> RiskAnalysisResponse:
        """
        Get complete risk analysis for a contract
        
        Args:
            contract_id: Contract UUID
            tenant_id: Tenant UUID
        
        Returns:
            RiskAnalysisResponse: Risk analysis with all clauses and scores
            
        Raises:
            ValueError: If contract not found
        """
        try:
            # Get contract
            contract = self.db.query(Contract).filter(
                and_(Contract.id == contract_id, Contract.tenant_id == tenant_id)
            ).first()
            
            if not contract:
                raise ValueError(f"Contract {contract_id} not found")
            
            # Get all clauses
            clauses = self.db.query(Clause).filter(
                Clause.contract_id == contract_id
            ).order_by(Clause.clause_number).all()
            
            # Count clauses by severity
            medium_issues = len([c for c in clauses if c.severity == ClauseSeverity.MEDIUM])
            low_issues = len([c for c in clauses if c.severity == ClauseSeverity.LOW])
            
            # Build analysis summary
            analysis_summary = self._generate_analysis_summary(contract, clauses)
            recommendations = self._generate_recommendations(contract, clauses)
            
            return RiskAnalysisResponse(
                contract_id=contract_id,
                status=contract.status,
                overall_risk_score=contract.overall_risk_score,
                total_clauses_found=contract.total_clauses_found,
                critical_issues=contract.critical_issues,
                high_issues=contract.high_issues,
                medium_issues=medium_issues,
                low_issues=low_issues,
                clauses=[self._to_clause_response(c) for c in clauses],
                analysis_summary=analysis_summary,
                recommended_actions=recommendations,
                updated_at=contract.updated_at
            )
            
        except Exception as e:
            logger.error(f"Failed to get risk analysis: {str(e)}")
            raise
    
    def get_clause_detail(
        self,
        clause_id: UUID,
        tenant_id: UUID
    ) -> Dict[str, Any]:
        """
        Get detailed clause information with similar clauses and precedents
        
        Args:
            clause_id: Clause UUID
            tenant_id: Tenant UUID
        
        Returns:
            Dict with clause detail, contract, and similar clauses
            
        Raises:
            ValueError: If clause not found
        """
        try:
            # Get clause
            clause = self.db.query(Clause).filter(
                and_(Clause.id == clause_id, Clause.tenant_id == tenant_id)
            ).first()
            
            if not clause:
                raise ValueError(f"Clause {clause_id} not found")
            
            # Get parent contract
            contract = self.db.query(Contract).filter(
                Contract.id == clause.contract_id
            ).first()
            
            # Search for similar clauses in ChromaDB
            query_embedding = self.embedder.embed_text(clause.raw_text)
            similar = self.chromadb.search_similar_clauses(
                query_embedding=query_embedding,
                severity_filter=clause.severity.value,
                n_results=5
            )
            
            return {
                'clause': self._to_clause_response(clause),
                'contract': self._to_contract_response(contract),
                'similar_clauses': similar,
                'precedent_matches': []  # Would populate from playbook collection
            }
            
        except Exception as e:
            logger.error(f"Failed to get clause detail: {str(e)}")
            raise
    
    def delete_contract(
        self,
        contract_id: UUID,
        tenant_id: UUID,
        user_id: UUID
    ) -> None:
        """
        Delete a contract and related data
        
        Args:
            contract_id: Contract UUID
            tenant_id: Tenant UUID
            user_id: User UUID (for audit)
        """
        try:
            contract = self.db.query(Contract).filter(
                and_(Contract.id == contract_id, Contract.tenant_id == tenant_id)
            ).first()
            
            if not contract:
                raise ValueError(f"Contract {contract_id} not found")
            
            # Delete from ChromaDB
            self.chromadb.delete_clauses_for_contract(contract_id)
            
            # Delete file
            self.file_manager.delete_contract_files(tenant_id, contract_id)
            
            # Delete from PostgreSQL
            self.db.query(Clause).filter(Clause.contract_id == contract_id).delete()
            self.db.delete(contract)
            self.db.commit()
            
            # Audit log
            self.audit.log(
                tenant_id=tenant_id,
                user_id=user_id,
                event_type="contract_delete",
                action="delete",
                status="success",
                description=f"Contract deleted: {contract.filename}"
            )
            
            logger.info(f"Contract {contract_id} deleted successfully")
            
        except Exception as e:
            logger.error(f"Failed to delete contract: {str(e)}")
            self.audit.log(
                tenant_id=tenant_id,
                user_id=user_id,
                event_type="contract_delete",
                action="delete",
                status="failure",
                description=f"Failed to delete contract: {str(e)}"
            )
            raise
    
    def _to_contract_response(self, contract: Contract) -> ContractResponse:
        """Convert Contract model to response schema"""
        return ContractResponse(
            id=contract.id,
            filename=contract.filename,
            counterparty_name=contract.counterparty_name,
            contract_type=contract.contract_type,
            status=contract.status,
            overall_risk_score=contract.overall_risk_score,
            total_clauses_found=contract.total_clauses_found,
            critical_issues=contract.critical_issues,
            high_issues=contract.high_issues,
            uploaded_by=contract.uploaded_by,
            created_at=contract.created_at,
            updated_at=contract.updated_at
        )
    
    def _to_clause_response(self, clause: Clause) -> ClauseResponse:
        """Convert Clause model to response schema"""
        return ClauseResponse(
            id=clause.id,
            clause_number=clause.clause_number,
            clause_type=clause.clause_type,
            section_title=clause.section_title,
            raw_text=clause.raw_text,
            severity=clause.severity,
            risk_description=clause.risk_description,
            legal_reasoning=clause.legal_reasoning,
            confidence_score=clause.confidence_score,
            is_standard=bool(clause.is_standard),
            is_missing_mandatory=bool(clause.is_missing_mandatory),
            is_jurisdiction_mismatch=bool(clause.is_jurisdiction_mismatch),
            applicable_statute=clause.applicable_statute,
            statute_section=clause.statute_section,
            created_at=clause.created_at
        )
    
    def _generate_analysis_summary(self, contract: Contract, clauses: List[Clause]) -> str:
        """Generate human-readable analysis summary"""
        total = contract.total_clauses_found
        critical = contract.critical_issues
        high = contract.high_issues
        
        if critical > 0:
            return f"{critical} critical and {high} high-risk clauses requiring immediate legal review"
        elif high > 0:
            return f"{high} high-risk clauses identified requiring legal review"
        else:
            return f"Contract analyzed with {total} clauses. No critical issues identified."
    
    def _generate_recommendations(self, contract: Contract, clauses: List[Clause]) -> List[str]:
        """Generate actionable recommendations from analysis"""
        recommendations = []
        
        # Group clauses by type and severity
        critical_by_type = {}
        high_by_type = {}
        
        for clause in clauses:
            if clause.severity == ClauseSeverity.CRITICAL:
                critical_by_type.setdefault(clause.clause_type, []).append(clause)
            elif clause.severity == ClauseSeverity.HIGH:
                high_by_type.setdefault(clause.clause_type, []).append(clause)
        
        # Generate recommendations
        for clause_type, clause_list in critical_by_type.items():
            recommendations.append(f"URGENT: Review {clause_type} clause - {len(clause_list)} critical issue(s)")
        
        for clause_type, clause_list in high_by_type.items():
            if clause_type not in critical_by_type:
                recommendations.append(f"Review {clause_type} clause - {len(clause_list)} high-risk issue(s)")
        
        return recommendations[:5]  # Return top 5 recommendations


def get_contract_service(db: Session) -> ContractService:
    """
    Get contract service instance
    
    Args:
        db: Database session
    
    Returns:
        ContractService: Initialized service
    """
    return ContractService(db)
