from __future__ import annotations

from agent_framework.core.settings import ModelSettings


def build_llm(settings: ModelSettings):
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing dependency `langchain-google-genai`. Install the packages in requirements.txt first."
        ) from exc

    if not settings.api_key:
        raise RuntimeError(
            "Missing Gemini API key. Set GEMINI_API_KEY, GOOGLE_API_KEY, OPENAI_API_KEY, or apikey in your environment."
        )

    llm_kwargs = {
        "model": settings.model,
        "google_api_key": settings.api_key,
        "temperature": settings.temperature,
    }
    if settings.api_base:
        llm_kwargs["client_options"] = {"api_endpoint": settings.api_base}

    return ChatGoogleGenerativeAI(
        **llm_kwargs,
    )
