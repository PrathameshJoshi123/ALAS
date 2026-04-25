from celery import shared_task
from workers.contract_generation.celery_config import celery_app
from workers.contract_generation.agent import agent, stream_agent_with_logging, logger, setup_logging
import time
import sys
from pathlib import Path


# Setup comprehensive logging for tasks
task_logger = setup_logging(
    log_file=str(Path(__file__).parent / "agent_execution.log")
)


# Add backend directory to path for imports
backend_path = str(Path(__file__).parent.parent)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)


# Define directories
TEMPLATES_DIR = Path(__file__).parent / "contract_templates"
MEMORIES_DIR = Path(__file__).parent / "memories"

TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
MEMORIES_DIR.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# TASK EXECUTION
# ==============================================================================

def invoke_agent(company_name: str, md_filename: str, contract_prompt: str, task_self=None):
    """Invoke the generation agent to draft a contract."""

    result_key = company_name.lower().replace(" ", "_")

    user_message = f"""You are drafting a contract for '{company_name}'.

USER REQUIREMENTS:
{contract_prompt}

CONTRACT TEMPLATE FILE:
/contract_templates/{md_filename}

---

MANDATORY WORKFLOW - YOU MUST COMPLETE ALL 5 STEPS:

**STEP 1: READ THE TEMPLATE IN CHUNKS**
- Read /contract_templates/{md_filename} in 300-line chunks only (offset = 0, 300, 600, etc.)
- After EACH chunk, immediately write findings to /memories/temp_analysis.md
- Document clause structure, obligations, payments, terms, gaps
- Continue until the entire template is read

**STEP 2: CONSOLIDATE TEMPLATE ANALYSIS**
- Re-read /memories/temp_analysis.md
- Add a "CONSOLIDATED SUMMARY" section with overall structure, missing clauses, and legal gaps
- Save to /memories/temp_analysis.md

**STEP 3: READ INDIAN CONTRACT ACT REFERENCE AND MAP IT**
- READ /contracts/indian_contract_law.md completely
- Identify at least 5 relevant sections for this contract
- Write an "INDIAN CONTRACT ACT MAPPING" section in /memories/temp_analysis.md
- Include: Section number, why it applies, how template aligns/conflicts, legal implications
- This step is MANDATORY and you will be checked for it

**STEP 4: DRAFT THE CONTRACT IN SECTIONS TO /memories/{result_key}_generated_contract.md**
CRITICAL: You MUST create this file and save it incrementally, not all at once.

Draft and save these sections separately:
  A) Title, Parties, Recitals → Draft → Save
  B) Definitions and Scope → Draft → Save
  C) Obligations of Each Party → Draft → Save
  D) Commercial Terms → Draft → Save
  E) Legal Clauses (Warranties, Liability, IP, Confidentiality with Act citations) → Draft → Save
  F) Dispute Resolution and Governing Law → Draft → Save

Use write_file or edit_file to save AFTER EACH section.

**STEP 5: FINAL REVIEW**
- Read the entire /memories/{result_key}_generated_contract.md
- Check consistency with template and user prompt
- Check all major clauses cite relevant Indian Contract Act sections
- Improve and save final version

---

VERIFICATION CHECKLIST - YOU MUST COMPLETE ALL:
✓ Read entire template in 300-line chunks
✓ Wrote chunk findings to /memories/temp_analysis.md
✓ Re-read temp_analysis and added CONSOLIDATED SUMMARY
✓ Read /contracts/indian_contract_law.md
✓ Added INDIAN CONTRACT ACT MAPPING to /memories/temp_analysis.md with 5+ section citations
✓ Created /memories/{result_key}_generated_contract.md
✓ Drafted and saved Section A (Title and Recitals)
✓ Drafted and saved Section B (Definitions)
✓ Drafted and saved Section C (Obligations)
✓ Drafted and saved Section D (Commercial Terms)
✓ Drafted and saved Section E (Legal Clauses with Act citations)
✓ Drafted and saved Section F (Dispute Resolution)
✓ Final review completed
✓ Final polished version saved

---

DO NOT STOP until all steps are complete.
DO NOT skip the Indian Contract Act reading.
DO NOT write the entire contract at once - save each section as you draft it.
DO NOT complete the task without creating /memories/{result_key}_generated_contract.md.

BEGIN NOW. Follow every step in order."""

    task_logger.info(f"Starting contract generation for: {company_name}")

    streaming_result = stream_agent_with_logging(
        user_message=user_message,
        stream_mode=["updates", "messages"]
    )

    return streaming_result


# ==============================================================================
# CELERY TASKS
# ==============================================================================

@celery_app.task(bind=True, name="process_contract_generation")
def trigger_contract_generation_pipeline(self, company_name: str, md_filename: str, contract_prompt: str):
    """Background task to generate a contract from a parsed template and prompt."""

    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        result_key = company_name.lower().replace(" ", "_")

        self.update_state(
            state="PROCESSING",
            meta={
                "company_name": company_name,
                "status": "Starting contract generation...",
                "timestamp": timestamp
            }
        )

        task_logger.info(f"\n{'#'*60}")
        task_logger.info(f"# GENERATING CONTRACT FOR: {company_name}")
        task_logger.info(f"# TEMPLATE: /contract_templates/{md_filename}")
        task_logger.info(f"# OUTPUT: /memories/{result_key}_generated_contract.md")
        task_logger.info(f"{'#'*60}\n")

        invoke_agent(company_name, md_filename, contract_prompt, task_self=self)

        self.update_state(
            state="SUCCESS",
            meta={
                "status": "completed",
                "company_name": company_name,
                "timestamp": timestamp
            }
        )

        task_logger.info(f"\nGeneration completed for {company_name}")

        return {
            "status": "completed",
            "company_name": company_name,
            "output_file": f"/memories/{result_key}_generated_contract.md",
            "timestamp": timestamp
        }

    except Exception as e:
        error_msg = f"Contract generation failed: {str(e)}"
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