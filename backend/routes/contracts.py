import json
import logging
from pathlib import Path
from typing import Any

from bson import ObjectId
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from models.database import get_db, now_utc
from services.parser import parse_pdf
from services.qa_agent import answer_question, initialize_vector_store
from shared.dependencies import get_current_user
from workers.contract.celery_config import celery_app
from workers.contract.tasks import trigger_agent_pipeline
from workers.contract_generation.tasks import trigger_contract_generation_pipeline

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("contracts_router")
logger.setLevel(logging.DEBUG)

router = APIRouter(prefix="/api/contracts", tags=["contracts"])

RESULTS_DIR = Path(__file__).parent.parent / "workers" / "contract" / "contracts" / "results"
CONTRACTS_DIR = Path(__file__).parent.parent / "workers" / "contract" / "contracts"
MEMORIES_DIR = Path(__file__).parent.parent / "workers" / "contract" / "memories"
GENERATION_MEMORIES_DIR = Path(__file__).parent.parent / "workers" / "contract_generation" / "memories"
VECTORSTORES_DIR = Path(__file__).parent.parent / "workers" / "contract" / "vectorstores"
CONTRACT_TEMPLATES_DIR = Path(__file__).parent.parent / "workers" / "contract_generation" / "contract_templates"


class QARequest(BaseModel):
    question: str = Field(min_length=2)
    contract_id: str | None = None
    markdown_file: str | None = None


class QAResponse(BaseModel):
    success: bool
    contract_id: str | None = None
    question: str | None = None
    answer: str | None = None
    qa_id: str | None = None
    source_file: str | None = None
    error: str | None = None


def _serialize_datetime(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _serialize_contract(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(doc["_id"]),
        "tenant_id": doc.get("tenant_id"),
        "owner_user_id": doc.get("owner_user_id"),
        "company_name": doc.get("company_name"),
        "counterparty_name": doc.get("counterparty_name"),
        "contract_type": doc.get("contract_type"),
        "original_filename": doc.get("original_filename"),
        "markdown_file": doc.get("markdown_file"),
        "vector_store_key": doc.get("vector_store_key"),
        "status": doc.get("status"),
        "analysis_mode": doc.get("analysis_mode"),
        "analysis_task_id": doc.get("analysis_task_id"),
        "created_at": _serialize_datetime(doc.get("created_at")),
        "updated_at": _serialize_datetime(doc.get("updated_at")),
        "last_activity_at": _serialize_datetime(doc.get("last_activity_at")),
        "live": doc.get("live", {}),
    }


def _result_filename_for_company(company_name: str) -> str:
    return f"{company_name.lower().replace(' ', '_')}_result.json"


def _final_analysis_filename_for_company(company_name: str) -> str:
    return f"{company_name.lower().replace(' ', '_')}_final_analysis.md"


def _attach_live_status(contract: dict[str, Any]) -> dict[str, Any]:
    markdown_file = contract.get("markdown_file", "")
    company_name = contract.get("company_name", "")
    vector_store_key = contract.get("vector_store_key") or Path(markdown_file).stem

    analysis_mode = contract.get("analysis_mode", "analysis")

    markdown_ready = (CONTRACTS_DIR / markdown_file).exists() if markdown_file else False
    result_ready = (RESULTS_DIR / _result_filename_for_company(company_name)).exists() if company_name else False
    final_analysis_filename = _final_analysis_filename_for_company(company_name) if company_name else None
    final_analysis_ready = (MEMORIES_DIR / final_analysis_filename).exists() if final_analysis_filename else False
    vector_store_ready = (VECTORSTORES_DIR / vector_store_key).exists() if vector_store_key else False

    generated_contract_filename = f"{company_name.lower().replace(' ', '_')}_generated_contract.md" if company_name else None
    generated_contract_ready = (GENERATION_MEMORIES_DIR / generated_contract_filename).exists() if generated_contract_filename else False

    if analysis_mode == "generation":
        if generated_contract_ready:
            inferred_status = "completed"
        elif contract.get("status") == "failed":
            inferred_status = "failed"
        else:
            inferred_status = "processing"
    else:
        if final_analysis_ready or result_ready:
            inferred_status = "completed"
        elif contract.get("status") == "failed":
            inferred_status = "failed"
        else:
            inferred_status = "processing"

    contract["status"] = inferred_status
    contract["live"] = {
        "markdown_ready": markdown_ready,
        "result_ready": result_ready,
        "final_analysis_ready": final_analysis_ready,
        "vector_store_ready": vector_store_ready,
        "generated_contract_ready": generated_contract_ready,
        "final_analysis_filename": final_analysis_filename,
        "generated_contract_filename": generated_contract_filename,
        "updated_from_filesystem": True,
    }
    return contract


def _build_analysis_payload_from_markdown(markdown_content: str) -> dict[str, Any]:
    """Build a normalized analysis payload from final analysis markdown text."""
    lines = [ln.strip() for ln in markdown_content.splitlines()]
    non_empty = [ln for ln in lines if ln]

    summary = ""
    for ln in non_empty:
        if ln.startswith("#") or ln.startswith("-"):
            continue
        summary = ln
        break

    overall_risk_score = 0
    lowered = markdown_content.lower()
    if "overall risk: high" in lowered or "overall risk high" in lowered:
        overall_risk_score = 78
    elif "overall risk: medium" in lowered or "overall risk medium" in lowered:
        overall_risk_score = 52
    elif "overall risk: low" in lowered or "overall risk low" in lowered:
        overall_risk_score = 28

    recommended_actions: list[str] = []
    in_reco_section = False
    for ln in lines:
        l = ln.strip()
        lower = l.lower()
        if lower.startswith("##") and "recommendation" in lower:
            in_reco_section = True
            continue
        if in_reco_section and lower.startswith("##") and "recommendation" not in lower:
            break
        if in_reco_section and (l.startswith("-") or (l[:2].isdigit() and l[2:3] in [".", ")"])):
            cleaned = l.lstrip("- ").strip()
            if cleaned:
                recommended_actions.append(cleaned)

    clauses = []
    critical_issues = 0
    high_issues = 0
    medium_issues = 0
    low_issues = 0

    import re
    import json
    match = re.search(r"```json\s*(.*?)\s*```", markdown_content, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            if "overall_risk_score" in data:
                try:
                    overall_risk_score = int(data["overall_risk_score"])
                except ValueError:
                    pass
            if "clauses" in data and isinstance(data["clauses"], list):
                clauses = data["clauses"]
                for c in clauses:
                    sev = c.get("severity", "").lower()
                    if sev == "critical": critical_issues += 1
                    elif sev == "high": high_issues += 1
                    elif sev == "medium": medium_issues += 1
                    elif sev == "low": low_issues += 1
        except Exception:
            pass

    # Strip the JSON block from the markdown output so it doesn't display in UI
    if match:
        clean_markdown = markdown_content.replace(match.group(0), "").strip()
    else:
        clean_markdown = markdown_content

    return {
        "overall_risk_score": overall_risk_score,
        "critical_issues": critical_issues,
        "high_issues": high_issues,
        "medium_issues": medium_issues,
        "low_issues": low_issues,
        "analysis_summary": summary or "Final analysis generated.",
        "recommended_actions": recommended_actions,
        "clauses": clauses,
        "analysis_markdown": clean_markdown,
        "source": "memories_markdown",
    }


def _sync_analysis_from_memories(contract: dict[str, Any]) -> dict[str, Any] | None:
    """If final analysis markdown exists, persist it in Mongo and return payload."""
    company_name = contract.get("company_name")
    if not company_name:
        return contract.get("analysis_payload")

    if contract.get("analysis_mode") == "generation":
        gen_filename = f"{company_name.lower().replace(' ', '_')}_generated_contract.md"
        gen_path = GENERATION_MEMORIES_DIR / gen_filename
        if not gen_path.exists():
            return contract.get("analysis_payload")
        
        markdown_content = gen_path.read_text(encoding="utf-8")
        parsed_payload = {
            "overall_risk_score": 0,
            "critical_issues": 0,
            "high_issues": 0,
            "medium_issues": 0,
            "low_issues": 0,
            "analysis_summary": "Contract generation completed.",
            "recommended_actions": [],
            "clauses": [],
            "analysis_markdown": markdown_content,
            "source": "generation_markdown"
        }
        final_filename = gen_filename
    else:
        final_filename = _final_analysis_filename_for_company(company_name)
        final_path = MEMORIES_DIR / final_filename
        if not final_path.exists():
            return contract.get("analysis_payload")

        markdown_content = final_path.read_text(encoding="utf-8")
        parsed_payload = _build_analysis_payload_from_markdown(markdown_content)

    db = get_db()
    db.contracts.update_one(
        {"_id": contract["_id"]},
        {
            "$set": {
                "analysis_payload": parsed_payload,
                "analysis_markdown": markdown_content,
                "analysis_source_filename": final_filename,
                "analysis_updated_at": now_utc(),
                "status": "completed",
                "updated_at": now_utc(),
            }
        },
    )
    return parsed_payload


def _parse_object_id(value: str, detail: str = "Invalid id") -> ObjectId:
    try:
        return ObjectId(value)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=detail) from exc


def _sanitize_filename(filename: str) -> str:
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    return filename


def _resolve_contract_for_user(
    user: dict[str, Any],
    contract_id: str | None = None,
    markdown_file: str | None = None,
) -> dict[str, Any]:
    db = get_db()
    owner_user_id = user["id"]

    if contract_id:
        contract = db.contracts.find_one(
            {"_id": _parse_object_id(contract_id, "Invalid contract_id"), "owner_user_id": owner_user_id}
        )
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        return contract

    if markdown_file:
        safe_markdown = _sanitize_filename(markdown_file)
        contract = db.contracts.find_one(
            {"owner_user_id": owner_user_id, "markdown_file": safe_markdown},
            sort=[("created_at", -1)],
        )
        if contract:
            return contract

    active_contract_id = user.get("active_contract_id")
    if active_contract_id:
        try:
            active_contract_oid = ObjectId(active_contract_id)
            contract = db.contracts.find_one(
                {"_id": active_contract_oid, "owner_user_id": owner_user_id}
            )
            if contract:
                return contract
        except Exception:
            pass

    latest = db.contracts.find_one({"owner_user_id": owner_user_id}, sort=[("created_at", -1)])
    if latest:
        return latest

    raise HTTPException(status_code=404, detail="No contract found for user")


@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(..., description="PDF file to upload"),
    company_name: str | None = Form(default=None, description="Company name"),
    counterparty_name: str | None = Form(default=None, description="Counterparty name"),
    contract_type: str | None = Form(default=None, description="Contract type"),
    contract_prompt: str | None = Form(default=None, description="Optional prompt for contract generation"),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    try:
        logger.info("\n%s", "=" * 70)
        logger.info("[API /upload] Received PDF upload request")

        generation_prompt = contract_prompt.strip() if contract_prompt and contract_prompt.strip() else None
        is_generation_request = generation_prompt is not None

        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        display_company_name = (
            (company_name or "").strip()
            or (counterparty_name or "").strip()
            or Path(file.filename).stem
        )

        target_markdown_dir = CONTRACT_TEMPLATES_DIR if is_generation_request else CONTRACTS_DIR
        target_markdown_dir.mkdir(parents=True, exist_ok=True)

        temp_pdf_path = target_markdown_dir / f"temp_{file.filename}"
        with open(temp_pdf_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        md_filename = parse_pdf(
            str(temp_pdf_path),
            company_name=display_company_name,
            output_dir=str(target_markdown_dir),
        )

        temp_pdf_path.unlink(missing_ok=True)

        if is_generation_request:
            task = trigger_contract_generation_pipeline.delay(
                display_company_name,
                md_filename,
                generation_prompt,
            )
            mode = "generation"
            status = "processing"
        else:
            task = trigger_agent_pipeline.delay(display_company_name, md_filename)
            celery_app.send_task("create_vector_store", args=(md_filename,))
            mode = "analysis"
            status = "processing"

        db = get_db()
        now = now_utc()
        contract_doc = {
            "tenant_id": current_user["tenant_id"],
            "owner_user_id": current_user["id"],
            "company_name": display_company_name,
            "counterparty_name": (counterparty_name or "").strip() or display_company_name,
            "contract_type": (contract_type or "general").strip(),
            "original_filename": file.filename,
            "markdown_file": md_filename,
            "vector_store_key": Path(md_filename).stem,
            "analysis_mode": mode,
            "analysis_task_id": task.id,
            "status": status,
            "created_at": now,
            "updated_at": now,
            "last_activity_at": now,
        }

        inserted = db.contracts.insert_one(contract_doc)
        contract_id = str(inserted.inserted_id)

        db.users.update_one(
            {"_id": _parse_object_id(current_user["id"], "Invalid user id")},
            {
                "$set": {
                    "active_contract_id": contract_id,
                    "updated_at": now,
                }
            },
        )

        logger.info("[API /upload] Upload completed and contract saved: %s", contract_id)
        logger.info("%s\n", "=" * 70)

        return JSONResponse(
            status_code=202,
            content={
                "id": contract_id,
                "message": "PDF uploaded and processing started",
                "company_name": display_company_name,
                "markdown_file": md_filename,
                "mode": mode,
                "task_id": task.id,
            },
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[API /upload] Error: %s", str(exc), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(exc)}")


@router.get("")
def list_contracts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    db = get_db()
    skip = (page - 1) * page_size

    cursor = (
        db.contracts.find({"owner_user_id": current_user["id"]})
        .sort("created_at", -1)
        .skip(skip)
        .limit(page_size)
    )
    items = [_serialize_contract(_attach_live_status(c)) for c in cursor]
    total = db.contracts.count_documents({"owner_user_id": current_user["id"]})

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.get("/{contract_id}")
def get_contract_details(contract_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
    db = get_db()
    contract = db.contracts.find_one(
        {
            "_id": _parse_object_id(contract_id, "Invalid contract id"),
            "owner_user_id": current_user["id"],
        }
    )
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    contract = _attach_live_status(contract)
    db.contracts.update_one(
        {"_id": contract["_id"]},
        {
            "$set": {
                "status": contract["status"],
                "updated_at": now_utc(),
            }
        },
    )
    return _serialize_contract(contract)


@router.delete("/{contract_id}")
def delete_contract(contract_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
    db = get_db()
    result = db.contracts.delete_one(
        {
            "_id": _parse_object_id(contract_id, "Invalid contract id"),
            "owner_user_id": current_user["id"],
        }
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Contract not found")

    db.qa_history.delete_many({"contract_id": contract_id, "user_id": current_user["id"]})
    return {"success": True}


@router.post("/{contract_id}/analyze")
def analyze_contract(contract_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
    db = get_db()
    contract = db.contracts.find_one(
        {
            "_id": _parse_object_id(contract_id, "Invalid contract id"),
            "owner_user_id": current_user["id"],
        }
    )
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    task = trigger_agent_pipeline.delay(contract["company_name"], contract["markdown_file"])
    celery_app.send_task("create_vector_store", args=(contract["markdown_file"],))

    db.contracts.update_one(
        {"_id": contract["_id"]},
        {
            "$set": {
                "analysis_task_id": task.id,
                "status": "processing",
                "updated_at": now_utc(),
            }
        },
    )

    return {
        "success": True,
        "task_id": task.id,
        "contract_id": contract_id,
    }


@router.get("/{contract_id}/analysis")
def get_contract_analysis(contract_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
    """Mongo-first analysis endpoint; syncs final analysis markdown from memories when present."""
    db = get_db()
    contract = db.contracts.find_one(
        {
            "_id": _parse_object_id(contract_id, "Invalid contract id"),
            "owner_user_id": current_user["id"],
        }
    )
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    payload = _sync_analysis_from_memories(contract)

    refreshed = db.contracts.find_one({"_id": contract["_id"]})
    refreshed = _attach_live_status(refreshed)
    db.contracts.update_one(
        {"_id": refreshed["_id"]},
        {"$set": {"status": refreshed["status"], "updated_at": now_utc()}},
    )

    if not payload:
        return {
            "status": "processing",
            "analysis_summary": "Analysis is still running. Please keep polling.",
            "recommended_actions": [],
            "clauses": [],
            "analysis_markdown": "",
            "live": refreshed.get("live", {}),
        }

    return {
        **payload,
        "status": "completed",
        "live": refreshed.get("live", {}),
    }


@router.get("/result/{company_name}")
async def get_agent_result(company_name: str):
    logger.info("[API /result] Fetching result for company: %s", company_name)

    result_key = company_name.lower().replace(" ", "_")
    result_file = RESULTS_DIR / f"{result_key}_result.json"

    if not result_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No result found for company: {company_name}. Pipeline may still be processing or file not found.",
        )

    try:
        with open(result_file, "r", encoding="utf-8") as handle:
            result_data = json.load(handle)

        return JSONResponse(
            status_code=200,
            content={
                "company_name": company_name,
                "result": result_data,
                "status": "completed",
            },
        )
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Error reading result file. File may be corrupted.") from exc


@router.get("/result-list")
async def list_available_results():
    if not RESULTS_DIR.exists():
        return JSONResponse(status_code=200, content={"available_results": [], "total": 0})

    result_files = list(RESULTS_DIR.glob("*_result.json"))
    available_results = [f.stem.replace("_result", "") for f in result_files]

    return JSONResponse(
        status_code=200,
        content={
            "available_results": available_results,
            "total": len(available_results),
            "results_directory": str(RESULTS_DIR),
        },
    )


@router.get("/markdown/{filename}")
async def get_markdown_content(filename: str, current_user: dict[str, Any] = Depends(get_current_user)):
    safe_filename = _sanitize_filename(filename)
    db = get_db()

    contract = db.contracts.find_one({"owner_user_id": current_user["id"], "markdown_file": safe_filename})
    md_file_path = CONTRACTS_DIR / safe_filename

    # Support generated final analysis and generated contracts written under /memories.
    if not contract and (safe_filename.endswith("_final_analysis.md") or safe_filename.endswith("_generated_contract.md")):
        user_contracts = db.contracts.find({"owner_user_id": current_user["id"]}, {"company_name": 1})
        allowed = set()
        for c in user_contracts:
            cname = c.get("company_name")
            if cname:
                allowed.add(_final_analysis_filename_for_company(cname))
                allowed.add(f"{cname.lower().replace(' ', '_')}_generated_contract.md")
        
        if safe_filename in allowed:
            if safe_filename.endswith("_generated_contract.md"):
                md_file_path = GENERATION_MEMORIES_DIR / safe_filename
            else:
                md_file_path = MEMORIES_DIR / safe_filename
            contract = {"owner_user_id": current_user["id"]}

    if not contract:
        raise HTTPException(status_code=404, detail="Markdown file not mapped to this user")

    if not md_file_path.exists():
        raise HTTPException(status_code=404, detail=f"Markdown file not found: {safe_filename}")

    content = md_file_path.read_text(encoding="utf-8")
    return JSONResponse(
        status_code=200,
        content={
            "filename": safe_filename,
            "content": content,
            "size_bytes": len(content),
            "status": "success",
        },
    )


@router.get("/markdown")
async def list_markdown_files(current_user: dict[str, Any] = Depends(get_current_user)):
    db = get_db()
    contracts = list(
        db.contracts.find(
            {"owner_user_id": current_user["id"]},
            {"markdown_file": 1, "company_name": 1},
        )
    )
    files = {c.get("markdown_file") for c in contracts if c.get("markdown_file")}

    # Include final analysis and generated contract files when available in /memories.
    for c in contracts:
        company_name = c.get("company_name")
        if not company_name:
            continue
        final_name = _final_analysis_filename_for_company(company_name)
        if (MEMORIES_DIR / final_name).exists():
            files.add(final_name)
        gen_name = f"{company_name.lower().replace(' ', '_')}_generated_contract.md"
        if (GENERATION_MEMORIES_DIR / gen_name).exists():
            files.add(gen_name)

    files = sorted(files)

    return JSONResponse(
        status_code=200,
        content={
            "files": files,
            "total": len(files),
            "directory": str(CONTRACTS_DIR),
        },
    )


@router.post("/qa", response_model=QAResponse)
async def ask_question(
    request: QARequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    try:
        logger.info("\n%s", "=" * 70)
        logger.info("[API /qa] Received QA request")

        contract = _resolve_contract_for_user(
            current_user,
            contract_id=request.contract_id,
            markdown_file=request.markdown_file,
        )
        contract_id = str(contract["_id"])

        initialize_vector_store(contract["markdown_file"])
        result = answer_question(request.question)

        if not result.get("success"):
            return QAResponse(success=False, contract_id=contract_id, error=result.get("error", "Unknown error"))

        db = get_db()
        now = now_utc()
        db.qa_history.insert_one(
            {
                "tenant_id": current_user["tenant_id"],
                "user_id": current_user["id"],
                "contract_id": contract_id,
                "question": request.question,
                "answer": result.get("answer"),
                "qa_id": result.get("qa_id"),
                "source_file": contract["markdown_file"],
                "created_at": now,
            }
        )

        db.contracts.update_one(
            {"_id": contract["_id"]},
            {
                "$set": {
                    "last_activity_at": now,
                    "updated_at": now,
                }
            },
        )

        db.users.update_one(
            {"_id": _parse_object_id(current_user["id"], "Invalid user id")},
            {
                "$set": {
                    "active_contract_id": contract_id,
                    "updated_at": now,
                }
            },
        )

        logger.info("[API /qa] Question answered successfully for contract_id=%s", contract_id)
        logger.info("%s\n", "=" * 70)

        return QAResponse(
            success=True,
            contract_id=contract_id,
            question=result.get("question"),
            answer=result.get("answer"),
            qa_id=result.get("qa_id"),
            source_file=contract["markdown_file"],
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[API /qa] Unexpected error: %s", str(exc), exc_info=True)
        return QAResponse(success=False, error=f"Error processing question: {str(exc)}")


@router.post("/{contract_id}/qa", response_model=QAResponse)
async def ask_question_for_contract(
    contract_id: str,
    request: QARequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    merged = QARequest(
        question=request.question,
        contract_id=contract_id,
        markdown_file=request.markdown_file,
    )
    return await ask_question(merged, current_user)
