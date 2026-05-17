from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional

from app.database import init_db
from app.routers import prompt, lyric, score, midi
from app.services.llm_service import llm_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="AI音乐生成后端", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prompt.router)
app.include_router(lyric.router)
app.include_router(score.router)
app.include_router(midi.router)


class ApiKeyRequest(BaseModel):
    deepseek_api_key: Optional[str] = None
    qwen_api_key: Optional[str] = None


@app.post("/api/settings/keys")
async def update_api_keys(request: ApiKeyRequest):
    llm_service.update_keys(request.deepseek_api_key, request.qwen_api_key)
    return {"status": "ok"}


@app.get("/api/settings/keys/status")
async def check_api_keys_status():
    return {
        "deepseek_configured": bool(llm_service._deepseek_key),
        "qwen_configured": bool(llm_service._qwen_key),
    }


@app.get("/")
async def root():
    return {"message": "AI音乐生成后端服务"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
