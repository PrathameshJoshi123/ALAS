from celery import shared_task
from workers.contract.celery_config import celery_app
from workers.contract.agent import agent, stream_agent_with_logging, logger, setup_logging
import time
import sys
import logging
from pathlib import Path
from services.vectorstore import create_vector_store_from_markdown

# Setup comprehensive logging for tasks
task_logger = setup_logging(
    log_file=str(Path(__file__).parent / "agent_execution.log")
)

# Add backend directory to path for imports
backend_path = str(Path(__file__).parent.parent)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Define contracts directory
CONTRACTS_DIR = Path(__file__).parent / "contracts"

# Ensure contracts directory exists
CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# TASK EXECUTION
# ==============================================================================

def invoke_agent(company_name: str, md_filename: str, task_self=None):
    """
    Invoke agent to analyze contract.
    
    Args:
        company_name: Name of the company
        md_filename: Markdown filename
        task_self: Celery task self reference
        
    Returns:
        Agent streaming result
    """
    result_key = company_name.lower().replace(" ", "_")
    
    user_message = f"""Analyse the contract for '{company_name}'.

Contract file: /contracts/{md_filename}

1. Understand the contract type
2. Use act_extractor subagent to get Indian Contract Act requirements
3. Use file_analyzer subagent to analyze the contract
4. Generate final comprehensive report in /memories/{result_key}_final_analysis.md

Include: classification, parties, obligations, risks, red flags, green flags, missing clauses, and recommendations."""
    
    task_logger.info(f"Starting analysis for: {company_name}")
    
    # Stream agent execution
    streaming_result = stream_agent_with_logging(
        user_message=user_message,
        stream_mode=["updates", "messages"]
    )
    
    return streaming_result


# ==============================================================================
# CELERY TASKS
# ==============================================================================

@celery_app.task(bind=True, name="process_contract")
def trigger_agent_pipeline(self, company_name: str, md_filename: str):
    """
    Background task to analyze a contract.
    
    Invokes the agent to analyze the contract and generate a final 
    markdown report at /memories/{company_name}_final_analysis.md
    
    Args:
        company_name: Name of the company
        md_filename: Name of the markdown file containing the contract
    """
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        result_key = company_name.lower().replace(" ", "_")
        
        self.update_state(
            state="PROCESSING",
            meta={
                "company_name": company_name,
                "status": "Starting contract analysis...",
                "timestamp": timestamp
            }
        )
        
        task_logger.info(f"\n{'#'*60}")
        task_logger.info(f"# ANALYZING: {company_name}")
        task_logger.info(f"# CONTRACT: /contracts/{md_filename}")
        task_logger.info(f"{'#'*60}\n")
        
        # Invoke the agent
        invoke_agent(company_name, md_filename, task_self=self)
        
        # Update success state
        self.update_state(
            state="SUCCESS",
            meta={
                "status": "completed",
                "company_name": company_name,
                "timestamp": timestamp
            }
        )
        
        task_logger.info(f"\nAnalysis completed for {company_name}")
        
        return {
            "status": "completed",
            "company_name": company_name,
            "timestamp": timestamp
        }
        
    except Exception as e:
        error_msg = f"Contract analysis failed: {str(e)}"
        task_logger.error(error_msg, exc_info=True)
        
        self.update_state(
            state="FAILURE",
            meta={
                "error": error_msg,
                "company_name": company_name,
                "timestamp": time.strftime("%Y%m%d_%H%M%S")
            }
        )
        raise


@celery_app.task(bind=True, name="create_vector_store")
def create_vector_store_task(self, md_filename: str):
    """
    Background task to create a vector store for a markdown file.
    
    This task is triggered asynchronously after a contract is uploaded.
    The vector store is persisted to disk for later use in QA.
    
    Args:
        md_filename: Name of the markdown file to create vector store for
    """
    try:
        task_logger.info(f"Starting vector store creation for: {md_filename}")
        
        # Get full path to markdown file
        contracts_dir = Path(__file__).parent / "contracts"
        md_file_path = contracts_dir / md_filename
        
        if not md_file_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {md_file_path}")
        
        # Create and save vector store
        create_vector_store_from_markdown(str(md_file_path))
        
        task_logger.info(f"Vector store created successfully for: {md_filename}")
        
        return {
            "status": "completed",
            "filename": md_filename,
            "timestamp": time.strftime("%Y%m%d_%H%M%S")
        }
        
    except Exception as e:
        error_msg = f"Vector store creation failed: {str(e)}"
        task_logger.error(error_msg, exc_info=True)
        raise
