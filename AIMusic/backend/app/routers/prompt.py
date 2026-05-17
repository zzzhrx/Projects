from fastapi import APIRouter
from app.models.schemas import PromptOptimizeRequest, PromptOptimizeResponse
from app.services.llm_service import llm_service
from app.database import save_prompt_version
import uuid

router = APIRouter(prefix="/api/prompt", tags=["prompt"])


@router.post("/optimize", response_model=PromptOptimizeResponse)
async def optimize_prompt(request: PromptOptimizeRequest):
    session_id = request.session_id or str(uuid.uuid4())

    await save_prompt_version(
        step=request.step,
        type="original",
        content=request.prompt,
        session_id=session_id
    )

    optimized = await llm_service.optimize_prompt(request.prompt, request.step)

    await save_prompt_version(
        step=request.step,
        type="ai_optimized",
        content=optimized,
        session_id=session_id
    )

    return PromptOptimizeResponse(
        optimized_prompt=optimized,
        model="deepseek_pro",
        session_id=session_id
    )


@router.post("/quick-suggest")
async def quick_suggest(request: dict):
    suggestion = await llm_service.quick_suggest(request.get("text", ""), request.get("context", ""))
    return {"suggestion": suggestion}


@router.get("/history/{session_id}")
async def get_prompt_history(session_id: str, step: str = None):
    from app.database import get_prompt_versions
    versions = await get_prompt_versions(session_id, step)
    return {"versions": versions}


@router.post("/history/save")
async def save_human_modified(request: dict):
    await save_prompt_version(
        step=request.get("step", "prompt"),
        type="human_modified",
        content=request.get("content", ""),
        session_id=request.get("session_id", ""),
        note=request.get("note", "")
    )
    return {"status": "ok"}
