import os
import shutil
import json
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from schemas.pdf_upload import PDFUploadSchema
from services.parser import parse_pdf
from services.qa_agent import answer_question, initialize_vector_store
from workers.contract.tasks import trigger_agent_pipeline
from workers.contract.celery_config import celery_app
from pydantic import BaseModel
from services.vectorstore import create_vector_store_from_markdown
import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("contracts_router")
logger.setLevel(logging.DEBUG)

# Initialize router
router = APIRouter(prefix="/api/contracts", tags=["contracts"])

# Define results directory path
RESULTS_DIR = Path(__file__).parent.parent / "workers" / "contract" / "contracts" / "results"
CONTRACTS_DIR = Path(__file__).parent.parent / "workers" / "contract" / "contracts"
MEMORIES_DIR = Path(__file__).parent.parent / "workers" / "contract" / "memories"

# ==============================================================================
# REQUEST/RESPONSE SCHEMAS
# ==============================================================================

class QARequest(BaseModel):
    """Schema for QA request."""
    question: str
    markdown_file: str = None  # Optional: specific markdown file to query
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What are the payment terms in this contract?",
                "markdown_file": "government_of_india_contract.md"
            }
        }


class QAResponse(BaseModel):
    """Schema for QA response."""
    success: bool
    question: str = None
    answer: str = None
    qa_id: str = None
    source_file: str = None
    error: str = None


# ==============================================================================
# UPLOAD ENDPOINTS
# ==============================================================================

@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(..., description="PDF file to upload"),
    company_name: str = Form(..., description="Company name"),
):
    """
    Upload a PDF file and company name.
    
    - Parses the PDF to markdown
    - Saves the markdown file to contracts folder
    - Triggers background agent pipeline
    """
    try:
        logger.info(f"\n{'='*70}")
        logger.info(f"[API /upload] Received PDF upload request")
        logger.info(f"[API /upload] File: {file.filename}, Company: {company_name}")
        
        # Validate file type
        if file.content_type != "application/pdf":
            logger.error(f"[API /upload] ✗ Invalid file type: {file.content_type}")
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Create contracts directory if it doesn't exist
        contracts_dir = Path(__file__).parent.parent / "workers" / "contract" / "contracts"
        contracts_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"[API /upload] Contracts directory ready: {contracts_dir}")
        
        # Save uploaded PDF temporarily
        temp_pdf_path = contracts_dir / f"temp_{file.filename}"
        logger.debug(f"[API /upload] Saving temp PDF to: {temp_pdf_path}")
        
        with open(temp_pdf_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"[API /upload] ✓ PDF saved: {len(content)} bytes")
        
        # Parse PDF to markdown and save automatically
        logger.info(f"[API /upload] Parsing PDF to markdown...")
        md_filename = parse_pdf(str(temp_pdf_path), company_name=company_name)
        logger.info(f"[API /upload] ✓ Markdown created: {md_filename}")
        
        # Clean up temporary PDF
        temp_pdf_path.unlink()
        logger.debug(f"[API /upload] Cleaned up temp PDF")
        
        # Trigger background agent pipeline
        logger.info(f"[API /upload] Triggering agent pipeline...")
        task = trigger_agent_pipeline.delay(company_name, md_filename)
        logger.info(f"[API /upload] ✓ Agent pipeline task queued: {task.id}")
        
        # Trigger vector store creation asynchronously (don't wait for completion)
        logger.info(f"[API /upload] Triggering vector store creation...")
        celery_app.send_task("create_vector_store", args=(md_filename,))
        logger.info(f"[API /upload] ✓ Vector store creation task queued")
        
        logger.info(f"[API /upload] ✓ Upload completed successfully")
        logger.info(f"{'='*70}\n")

        return JSONResponse(
            status_code=202,
            content={
                "message": "PDF uploaded and processing started",
                "company_name": company_name,
                "markdown_file": md_filename,
                "task_id": task.id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API /upload] ✗ Error: {str(e)}", exc_info=True)
        logger.info(f"{'='*70}\n")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


# ==============================================================================
# RESULT ENDPOINTS
# ==============================================================================

@router.get("/result/{company_name}")
async def get_agent_result(company_name: str):
    """
    Get the result of the agent analysis for a company.
    
    Reads the result from the stored JSON file.
    """
    logger.info(f"[API /result] Fetching result for company: {company_name}")
    
    result_key = company_name.lower().replace(" ", "_")
    result_file = RESULTS_DIR / f"{result_key}_result.json"
    
    logger.debug(f"[API /result] Looking for result file: {result_file}")
    
    if not result_file.exists():
        logger.warning(f"[API /result] ⚠ Result not found for: {company_name}")
        raise HTTPException(
            status_code=404,
            detail=f"No result found for company: {company_name}. Pipeline may still be processing or file not found."
        )
    
    try:
        with open(result_file, "r", encoding="utf-8") as f:
            result_data = json.load(f)
        
        logger.info(f"[API /result] ✓ Result retrieved for: {company_name}")
        
        return JSONResponse(
            status_code=200,
            content={
                "company_name": company_name,
                "result": result_data,
                "status": "completed"
            }
        )
    except json.JSONDecodeError:
        logger.error(f"[API /result] ✗ Result file corrupted: {result_file}")
        raise HTTPException(
            status_code=500,
            detail="Error reading result file. File may be corrupted."
        )
    except Exception as e:
        logger.error(f"[API /result] ✗ Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving result: {str(e)}"
        )


@router.get("/result-list")
async def list_available_results():
    """
    List all available agent results.
    """
    logger.debug(f"[API /result-list] Listing available results")
    
    if not RESULTS_DIR.exists():
        logger.debug(f"[API /result-list] Results directory doesn't exist yet")
        return JSONResponse(
            status_code=200,
            content={
                "available_results": [],
                "total": 0
            }
        )
    
    # Get all result files
    result_files = list(RESULTS_DIR.glob("*_result.json"))
    available_results = [f.stem.replace("_result", "") for f in result_files]
    
    logger.info(f"[API /result-list] Found {len(available_results)} results")
    
    return JSONResponse(
        status_code=200,
        content={
            "available_results": available_results,
            "total": len(available_results),
            "results_directory": str(RESULTS_DIR)
        }
    )


# ==============================================================================
# MARKDOWN CONTENT ENDPOINTS
# ==============================================================================

@router.get("/markdown/{filename}")
async def get_markdown_content(filename: str):
    """
    Get the content of a markdown file.
    
    Returns the full markdown content of a parsed contract.
    Used to display contract content in the frontend.
    """
    logger.debug(f"[API /markdown] Fetching markdown: {filename}")
    
    try:
        # Sanitize filename to prevent directory traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            logger.warning(f"[API /markdown] ⚠ Invalid filename attempt: {filename}")
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        md_file_path = MEMORIES_DIR / filename
        logger.debug(f"[API /markdown] File path: {md_file_path}")
        
        if not md_file_path.exists():
            logger.warning(f"[API /markdown] ⚠ File not found: {filename}")
            raise HTTPException(
                status_code=404,
                detail=f"Markdown file not found: {filename}"
            )
        
        # Read markdown content
        content = md_file_path.read_text(encoding="utf-8")
        logger.info(f"[API /markdown] ✓ Markdown retrieved: {filename} ({len(content)} bytes)")
        
        return JSONResponse(
            status_code=200,
            content={
                "filename": filename,
                "content": content,
                "size_bytes": len(content),
                "status": "success"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API /markdown] ✗ Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error reading markdown file: {str(e)}"
        )


@router.get("/markdown")
async def list_markdown_files():
    """
    List all available markdown files in the contracts directory.
    """
    logger.debug(f"[API /markdown-list] Listing markdown files")
    
    try:
        if not MEMORIES_DIR.exists():
            logger.debug(f"[API /markdown-list] Memories directory doesn't exist yet")
            return JSONResponse(
                status_code=200,
                content={
                    "files": [],
                    "total": 0
                }
            )
        
        md_files = [f.name for f in MEMORIES_DIR.glob("*.md")]
        logger.info(f"[API /markdown-list] Found {len(md_files)} markdown files")
        
        return JSONResponse(
            status_code=200,
            content={
                "files": sorted(md_files),
                "total": len(md_files),
                "directory": str(CONTRACTS_DIR)
            }
        )
        
    except Exception as e:
        logger.error(f"[API /markdown-list] ✗ Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error listing markdown files: {str(e)}"
        )


# ==============================================================================
# QA ENDPOINTS
# ==============================================================================

@router.post("/qa", response_model=QAResponse)
async def ask_question(request: QARequest):
    """
    Ask a question about a contract.
    
    Process:
    1. Load vector store for the markdown file (reuses cached instance if same file)
    2. Query vector store for relevant sections
    3. Return comprehensive answer
    4. Store Q&A in memory
    
    Args:
        question: The question to answer
        markdown_file: Optional specific markdown file to query
        
    Returns:
        Answer with metadata
    """
    try:
        logger.info(f"\n{'='*70}")
        logger.info(f"[API /qa] Received QA request")
        logger.info(f"[API /qa] Question: {request.question}")
        logger.info(f"[API /qa] Markdown file: {request.markdown_file}")
        
        md_file = request.markdown_file
        
        if not md_file:
            error_msg = "markdown_file is required"
            logger.error(f"[API /qa] ✗ {error_msg}")
            return QAResponse(
                success=False,
                error=error_msg
            )
        
        # Sanitize filename to prevent directory traversal
        if ".." in md_file or "/" in md_file or "\\" in md_file:
            error_msg = "Invalid filename"
            logger.error(f"[API /qa] ✗ {error_msg}")
            return QAResponse(
                success=False,
                error=error_msg
            )
        
        # Initialize vector store from disk (reuses cache if same file)
        logger.info(f"[API /qa] Initializing vector store for: {md_file}")
        try:
            initialize_vector_store(md_file)
            logger.info(f"[API /qa] ✓ Vector store initialized successfully")
        except Exception as e:
            error_msg = f"Failed to load vector store: {str(e)}"
            logger.error(f"[API /qa] ✗ {error_msg}", exc_info=True)
            return QAResponse(
                success=False,
                error=error_msg
            )
        
        # Get answer from QA agent
        logger.info(f"[API /qa] Calling answer_question()...")
        result = answer_question(request.question)
        
        logger.debug(f"[API /qa] Result: {result}")
        
        if not result.get("success"):
            logger.error(f"[API /qa] ✗ QA agent failed: {result.get('error')}")
            return QAResponse(
                success=False,
                error=result.get("error", "Unknown error")
            )
        
        logger.info(f"[API /qa] ✓ Question answered successfully")
        logger.info(f"[API /qa] Answer length: {len(result.get('answer', ''))} characters")
        logger.info(f"{'='*70}\n")
        
        return QAResponse(
            success=True,
            question=result.get("question"),
            answer=result.get("answer"),
            qa_id=result.get("qa_id"),
            source_file=result.get("source_file")
        )
        
    except Exception as e:
        logger.error(f"[API /qa] ✗ Unexpected error: {str(e)}", exc_info=True)
        logger.info(f"{'='*70}\n")
        return QAResponse(
            success=False,
            error=f"Error processing question: {str(e)}"
        )
