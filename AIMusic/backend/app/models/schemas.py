from pydantic import BaseModel
from typing import Optional


class PromptOptimizeRequest(BaseModel):
    prompt: str
    step: str
    model: Optional[str] = "deepseek_pro"
    session_id: Optional[str] = None


class PromptOptimizeResponse(BaseModel):
    optimized_prompt: str
    model: str
    session_id: Optional[str] = None


class LyricGenerateRequest(BaseModel):
    prompt: str
    style: Optional[str] = "古风"
    paragraph_count: Optional[int] = 2
    rhyme_preference: Optional[str] = "auto"
    model: Optional[str] = "deepseek_pro"
    session_id: Optional[str] = None


class LyricGenerateResponse(BaseModel):
    lyrics: str
    lrc_content: Optional[str] = None
    model: str
    session_id: Optional[str] = None


class ScoreGenerateRequest(BaseModel):
    lyrics: str
    score_prompt: Optional[str] = None
    instrument: Optional[str] = "钢琴"
    model: Optional[str] = "qwen"
    session_id: Optional[str] = None


class ScoreGenerateResponse(BaseModel):
    vocal_abc: str = ""
    instrument_abc: str = ""
    abc_notation: str
    model: str
    session_id: Optional[str] = None


class MidiGenerateRequest(BaseModel):
    abc_notation: str
    session_id: Optional[str] = None


class MidiGenerateResponse(BaseModel):
    midi_file: str
    midi_url: str
    session_id: Optional[str] = None


class PromptVersion(BaseModel):
    id: Optional[int] = None
    step: str
    type: str
    content: str
    timestamp: Optional[str] = None
    parent_version_id: Optional[int] = None
    note: Optional[str] = None
    session_id: str
