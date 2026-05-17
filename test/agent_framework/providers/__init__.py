from __future__ import annotations

__all__ = ["AMapClient", "AgentGraphBuilder", "build_llm", "has_amap_api_key"]


def __getattr__(name: str):
    if name == "AMapClient":
        from agent_framework.providers.amap import AMapClient

        return AMapClient
    if name == "has_amap_api_key":
        from agent_framework.providers.amap import has_amap_api_key

        return has_amap_api_key
    if name == "AgentGraphBuilder":
        from agent_framework.providers.graph import AgentGraphBuilder

        return AgentGraphBuilder
    if name == "build_llm":
        from agent_framework.providers.llm import build_llm

        return build_llm
    raise AttributeError(name)
