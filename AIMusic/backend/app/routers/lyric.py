from fastapi import APIRouter
from fastapi import HTTPException
from fastapi.responses import Response
from app.models.schemas import LyricGenerateRequest, LyricGenerateResponse
from app.services.llm_service import llm_service
from app.utils.lrc_utils import generate_lrc
import uuid

router = APIRouter(prefix="/api/lyric", tags=["lyric"])


@router.post("/generate", response_model=LyricGenerateResponse)
async def generate_lyrics(request: LyricGenerateRequest):
    session_id = request.session_id or str(uuid.uuid4())
    try:
        lyrics = await llm_service.generate_lyrics(
            request.prompt,
            request.style or "古风",
            request.paragraph_count or 2,
            request.rhyme_preference or "auto",
        )
        lrc_content = generate_lrc(lyrics)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return LyricGenerateResponse(
        lyrics=lyrics,
        lrc_content=lrc_content,
        model="deepseek_pro",
        session_id=session_id
    )


@router.post("/export")
async def export_lrc(request: dict):
    lrc_content = request.get("lrc_content", "")
    filename = request.get("filename", "lyrics.lrc")
    return Response(
        content=lrc_content,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
