from __future__ import annotations

from agent_framework.providers.llm import build_llm
from agent_framework.tools.registry import ToolRegistry


class AgentGraphBuilder:
    def __init__(self, model_settings, tool_registry: ToolRegistry) -> None:
        self.model_settings = model_settings
        self.tool_registry = tool_registry

    def build(self):
        try:
            from langgraph.checkpoint.memory import MemorySaver
            from langgraph.prebuilt import create_react_agent
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Missing dependency `langgraph`. Install the packages in requirements.txt first."
            ) from exc

        llm = build_llm(self.model_settings)
        memory = MemorySaver()
        return create_react_agent(
            llm,
            self.tool_registry.as_langchain_tools(),
            checkpointer=memory,
        )
