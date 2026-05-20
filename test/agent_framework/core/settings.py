from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


@dataclass(frozen=True)
class ModelSettings:
    provider: str = field(default_factory=lambda: os.getenv("AGENT_PROVIDER", "gemini"))
    model: str = field(default_factory=lambda: os.getenv("AGENT_MODEL", "gemini-2.0-flash"))
    api_base: str | None = field(
        default_factory=lambda: os.getenv("GEMINI_API_BASE")
        or os.getenv("GEMINI_BASE_URL")
        or os.getenv("OPENAI_API_BASE")
        or os.getenv("ANTHROPIC_BASE_URL")
        or os.getenv("baseurl")
        or os.getenv("BASEURL")
    )
    api_key: str | None = field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("ANTHROPIC_API_KEY")
        or os.getenv("apikey")
    )
    temperature: float = field(default_factory=lambda: float(os.getenv("AGENT_TEMPERATURE", "0")))


@dataclass(frozen=True)
class SearchSettings:
    max_results: int = field(default_factory=lambda: int(os.getenv("SEARCH_MAX_RESULTS", "3")))


@dataclass(frozen=True)
class RuntimeSettings:
    default_thread_id: str = field(default_factory=lambda: os.getenv("DEFAULT_THREAD_ID", "user_001"))
    show_process_by_default: bool = field(
        default_factory=lambda: os.getenv("SHOW_PROCESS", "false").lower() == "true"
    )
    timezone: str = field(default_factory=lambda: os.getenv("AGENT_TIMEZONE", "Asia/Shanghai"))
    exit_commands: tuple[str, ...] = ("exit", "quit")
    banner_text: str = field(default_factory=lambda: "Advanced Agent 已启动 (输入 'exit' 退出)")


@dataclass(frozen=True)
class AgentSettings:
    agent_name: str = field(default_factory=lambda: os.getenv("AGENT_NAME", "advanced-agent"))
    model: ModelSettings = field(default_factory=ModelSettings)
    search: SearchSettings = field(default_factory=SearchSettings)
    runtime: RuntimeSettings = field(default_factory=RuntimeSettings)


def load_settings() -> AgentSettings:
    load_dotenv()
    return AgentSettings()
