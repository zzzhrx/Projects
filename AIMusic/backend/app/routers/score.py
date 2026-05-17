from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.models.schemas import ScoreGenerateRequest, ScoreGenerateResponse
from app.services.llm_service import llm_service
from app.services.music_service import music_service
from app.services.audio_service import audio_service
from app.database import save_prompt_version, get_prompt_versions
import uuid

router = APIRouter(prefix="/api/score", tags=["score"])


@router.post("/optimize-prompt")
async def optimize_score_prompt(request: dict):
    session_id = request.get("session_id", str(uuid.uuid4()))

    await save_prompt_version(step="score", type="original", content=request.get("prompt", ""), session_id=session_id)

    optimized = await llm_service.optimize_score_prompt(request.get("prompt", ""))

    await save_prompt_version(step="score", type="ai_optimized", content=optimized, session_id=session_id)

    return {"optimized_prompt": optimized, "session_id": session_id}


@router.post("/generate", response_model=ScoreGenerateResponse)
async def generate_score(request: ScoreGenerateRequest):
    session_id = request.session_id or str(uuid.uuid4())
    instrument = request.instrument or "钢琴"

    try:
        raw_abc = await llm_service.generate_score(
            request.lyrics,
            request.score_prompt or "",
            instrument,
        )
        vocal_abc, llm_instrument = music_service.split_abc_tracks(raw_abc, instrument)
        if vocal_abc.strip():
            instrument_abc = music_service.generate_accompaniment_abc(
                vocal_abc, instrument, tempo=72
            )
        else:
            instrument_abc = llm_instrument
        combined_abc = music_service.combine_abc_tracks(vocal_abc, instrument_abc)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not combined_abc:
        raise HTTPException(status_code=502, detail="曲谱生成结果为空，请调整提示词后重试。")

    return ScoreGenerateResponse(
        vocal_abc=vocal_abc,
        instrument_abc=instrument_abc,
        abc_notation=combined_abc,
        model="qwen",
        session_id=session_id
    )


@router.post("/render-audio")
async def render_audio(request: dict):
    abc_notation = request.get("abc_notation", "")
    if not abc_notation.strip():
        raise HTTPException(status_code=400, detail="ABC 曲谱不能为空")

    try:
        audio_path = audio_service.abc_to_audio(abc_notation)
        return FileResponse(
            audio_path,
            media_type="audio/wav",
            filename="output.wav",
            headers={"Content-Disposition": "attachment; filename=output.wav"},
        )
    except RuntimeError as e:
        raise HTTPException(status_code=501, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"音频渲染失败: {e}") from e


@router.get("/prompt/history")
async def get_score_prompt_history(session_id: str):
    versions = await get_prompt_versions(session_id, "score")
    return {"versions": versions}
