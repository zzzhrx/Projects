from __future__ import annotations

from agent_framework.agent.service import AdvancedAgentService
from agent_framework.core.capabilities import build_default_capability_registry
from agent_framework.core.settings import AgentSettings, load_settings
from agent_framework.routing.llm_router import LLMFallbackRouter
from agent_framework.runtime.cli import ChatCLI
from agent_framework.skills.defaults import build_default_skill_registry
from agent_framework.tools.registry import build_default_tool_registry


def build_agent_service(settings: AgentSettings | None = None) -> AdvancedAgentService:
    resolved_settings = settings or load_settings()
    return AdvancedAgentService(
        settings=resolved_settings,
        capability_registry=build_default_capability_registry(),
        tool_registry=build_default_tool_registry(resolved_settings.search),
        skill_registry=build_default_skill_registry(),
        skill_router=LLMFallbackRouter(),
    )


def build_cli(settings: AgentSettings | None = None) -> ChatCLI:
    resolved_settings = settings or load_settings()
    return ChatCLI(
        agent_service=build_agent_service(resolved_settings),
        runtime_settings=resolved_settings.runtime,
    )
