from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.services.music_service import music_service
import os
import uuid

router = APIRouter(prefix="/api/midi", tags=["midi"])


@router.post("/generate")
async def generate_midi(request: dict):
    abc_notation = request.get("abc_notation", "")
    session_id = request.get("session_id", str(uuid.uuid4()))
    instrument = request.get("instrument", "钢琴")
    vocal_abc = request.get("vocal_abc", "")

    try:
        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "output",
        )
        os.makedirs(output_dir, exist_ok=True)

        filename = f"{session_id}.mid"
        filepath = os.path.join(output_dir, filename)

        lyrics = music_service.extract_lyrics_from_abc(vocal_abc) if vocal_abc else None

        music_service.abc_to_midi_file(
            abc_notation, filepath, instrument=instrument, vocal_lyrics=lyrics
        )

        return {"midi_url": f"/api/midi/download/{filename}", "filename": filename}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/download/{filename}")
async def download_midi(filename: str):
    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "output",
    )
    filepath = os.path.join(output_dir, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filepath, media_type="audio/midi", filename=filename)
