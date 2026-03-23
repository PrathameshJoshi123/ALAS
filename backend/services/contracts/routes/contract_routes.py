"""
Contract Management Service Routes - API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, File, UploadFile, Form
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from shared.database.db import get_db
from shared.jwt_handler.jwt_utils import verify_token
from shared.database.models import User
from services.contracts.schemas.contract_schemas import (
    ContractUploadRequest,
    ContractResponse,
    RiskAnalysisResponse,
    ContractListResponse,
    ErrorResponse,
    ContractAnalysisJobResponse,
)
from services.contracts.utils import get_contract_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/contracts", tags=["contracts"])


def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    Extract and validate current user from Authorization header
    
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid Authorization header"
            )
        
        token = auth_header.replace("Bearer ", "")
        
        # Verify token and get tenant/user info
        payload = verify_token(token)
        user_id = UUID(payload.get("user_id"))
        tenant_id = UUID(payload.get("tenant_id"))
        
        # Fetch user from database
        user = db.query(User).filter(
            User.id == user_id,
            User.tenant_id == tenant_id
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


@router.post(
    "/upload",
    response_model=ContractResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        413: {"model": ErrorResponse, "description": "File too large"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def upload_contract(
    request: Request,
    file: UploadFile = File(...),
    counterparty_name: Optional[str] = Form(None),
    contract_type: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ContractResponse:
    """
    Upload a third-party contract PDF for analysis
    
    **Sequence 1: Third-Party Contract Ingestion & Risk Analysis (The Intake Flow)**
    
    Step 1: Upload Initiation
    - User uploads a contract PDF via Next.js frontend
    - API Gateway validates JWT and resolves tenant
    - Contract stored in files/tenant_id/contract_id/ directory
    
    Args:
        request: FastAPI Request object
        file: PDF file upload
        counterparty_name: Name of third-party entity
        contract_type: Type of contract (NDA, SLA, etc.)
        db: Database session
        current_user: Authenticated user
    
    Returns:
        ContractResponse: Created contract metadata
    
    Raises:
        HTTPException: 400 if invalid, 401 if unauthorized, 413 if too large, 500 if error
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )
        
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported"
            )
        
        # Limit file size to 50MB
        max_size = 50 * 1024 * 1024
        file_content = await file.read()
        
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds {max_size / 1024 / 1024:.0f}MB limit"
            )
        
        # Create upload request
        upload_request = ContractUploadRequest(
            counterparty_name=counterparty_name,
            contract_type=contract_type
        )
        
        # Use contract service
        service = get_contract_service(db)
        contract = service.upload_contract(
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            file_content=file_content,
            filename=file.filename,
            request=upload_request
        )
        
        logger.info(f"Contract uploaded successfully: {contract.id}")
        
        return contract
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Contract upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload contract"
        )


@router.get(
    "/{contract_id}",
    response_model=ContractResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Contract not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
def get_contract(
    contract_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ContractResponse:
    """
    Get contract metadata by ID
    
    Args:
        contract_id: Contract UUID
        db: Database session
        current_user: Authenticated user
    
    Returns:
        ContractResponse: Contract details
    
    Raises:
        HTTPException: 401 if unauthorized, 404 if not found
    """
    try:
        service = get_contract_service(db)
        contract = service.get_contract(contract_id, current_user.tenant_id)
        return contract
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get contract: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve contract"
        )


@router.get(
    "",
    response_model=ContractListResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
def list_contracts(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ContractListResponse:
    """
    List contracts for the current tenant with pagination
    
    Args:
        page: Page number (default: 1)
        page_size: Items per page (default: 20, max: 100)
        status: Filter by contract status
        db: Database session
        current_user: Authenticated user
    
    Returns:
        ContractListResponse: Paginated list of contracts
    
    Raises:
        HTTPException: 401 if unauthorized, 500 if error
    """
    try:
        if page_size > 100:
            page_size = 100
        
        service = get_contract_service(db)
        return service.list_contracts(
            tenant_id=current_user.tenant_id,
            page=page,
            page_size=page_size,
            status=status
        )
        
    except Exception as e:
        logger.error(f"Failed to list contracts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve contracts"
        )


@router.get(
    "/{contract_id}/risk-analysis",
    response_model=RiskAnalysisResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Contract not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
def get_risk_analysis(
    contract_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> RiskAnalysisResponse:
    """
    Get complete risk analysis for a contract with all clauses
    
    **Step 8: Validation & Storage → UI Update**
    - Frontend queries GET /contracts/{id}/risk-analysis
    - Renders interactive risk profile with:
      - Risk heatmap (by severity)
      - Clause-level citations
      - Confidence scores
      - Recommended actions
    
    Args:
        contract_id: Contract UUID
        db: Database session
        current_user: Authenticated user
    
    Returns:
        RiskAnalysisResponse: Complete risk analysis with all clauses
    
    Raises:
        HTTPException: 401 if unauthorized, 404 if not found, 500 if error
    """
    try:
        service = get_contract_service(db)
        return service.get_risk_analysis(contract_id, current_user.tenant_id)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get risk analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve risk analysis"
        )


@router.delete(
    "/{contract_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Contract not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
def delete_contract(
    contract_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete a contract and all associated data
    
    Deletes:
    - Contract metadata from PostgreSQL
    - All clauses from PostgreSQL
    - All clause embeddings from ChromaDB
    - PDF file from disk
    
    Args:
        contract_id: Contract UUID
        db: Database session
        current_user: Authenticated user
    
    Raises:
        HTTPException: 401 if unauthorized, 404 if not found, 500 if error
    """
    try:
        service = get_contract_service(db)
        service.delete_contract(contract_id, current_user.tenant_id, current_user.id)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to delete contract: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete contract"
        )


@router.post(
    "/{contract_id}/analyze",
    response_model=ContractAnalysisJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Contract not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def analyze_contract(
    contract_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ContractAnalysisJobResponse:
    """
    Initiate contract analysis via DeepAgents orchestrator
    
    **Complete Sequence 1: Third-Party Contract Ingestion & Risk Analysis Flow**
    
    Step 2: API Gateway Routing
    Step 3: Ingestion & Extraction
    Step 4: Agentic Handoff
    Step 5: Clause Segmentation & Vectorization
    Step 6: Semantic Rule Retrieval
    Step 7: Legal Reasoning (Mistral LLM)
    Step 8: Validation & Storage
    
    Args:
        contract_id: Contract UUID
        db: Database session
        current_user: Authenticated user
    
    Returns:
        ContractAnalysisJobResponse: Analysis job status with tracking info
    
    Raises:
        HTTPException: 401 if unauthorized, 404 if not found, 500 if error
    """
    try:
        service = get_contract_service(db)
        
        # Start analysis (async)
        result = await service.analyze_contract(contract_id, current_user.tenant_id)
        
        logger.info(f"Contract analysis initiated: {contract_id}")
        
        return ContractAnalysisJobResponse(
            job_id=f"job_{contract_id}",
            contract_id=contract_id,
            status="processing",
            progress_percentage=0,
            message="Analysis in progress: Extracting text, segmenting clauses, and analyzing risks..."
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to analyze contract: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate contract analysis"
        )
