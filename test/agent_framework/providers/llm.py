from __future__ import annotations

from agent_framework.core.settings import ModelSettings


def build_llm(settings: ModelSettings):
    if not settings.api_key:
        raise RuntimeError(
            "Missing API key. Set GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY, or apikey in your environment."
        )

    provider = settings.provider.lower()

    if provider == "gemini":
        return _build_gemini(settings)
    elif provider == "openai":
        return _build_openai(settings)
    elif provider == "anthropic":
        return _build_anthropic(settings)
    elif provider == "deepseek":
        return _build_deepseek(settings)
    else:
        raise RuntimeError(
            f"Unsupported LLM provider: {provider!r}. Supported: gemini, openai, anthropic, deepseek."
        )


def _build_gemini(settings: ModelSettings):
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing dependency `langchain-google-genai`. Install the packages in requirements.txt first."
        ) from exc

    llm_kwargs = {
        "model": settings.model,
        "google_api_key": settings.api_key,
        "temperature": settings.temperature,
    }
    if settings.api_base:
        llm_kwargs["client_options"] = {"api_endpoint": settings.api_base}

    return ChatGoogleGenerativeAI(**llm_kwargs)


def _build_openai(settings: ModelSettings):
    try:
        from langchain_openai import ChatOpenAI
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing dependency `langchain-openai`. Install it with: pip install langchain-openai"
        ) from exc

    llm_kwargs = {
        "model": settings.model,
        "openai_api_key": settings.api_key,
        "temperature": settings.temperature,
    }
    if settings.api_base:
        llm_kwargs["openai_api_base"] = settings.api_base

    return ChatOpenAI(**llm_kwargs)


def _build_anthropic(settings: ModelSettings):
    try:
        from langchain_anthropic import ChatAnthropic
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing dependency `langchain-anthropic`. Install it with: pip install langchain-anthropic"
        ) from exc

    llm_kwargs = {
        "model": settings.model,
        "anthropic_api_key": settings.api_key,
        "temperature": settings.temperature,
    }
    if settings.api_base:
        llm_kwargs["anthropic_api_url"] = settings.api_base

    return ChatAnthropic(**llm_kwargs)


def _build_deepseek(settings: ModelSettings):
    try:
        from langchain_openai import ChatOpenAI
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing dependency `langchain-openai`. Install it with: pip install langchain-openai"
        ) from exc

    llm_kwargs = {
        "model": settings.model,
        "openai_api_key": settings.api_key,
        "temperature": settings.temperature,
    }
    base = settings.api_base or "https://api.deepseek.com"
    llm_kwargs["openai_api_base"] = base

    return ChatOpenAI(**llm_kwargs)
