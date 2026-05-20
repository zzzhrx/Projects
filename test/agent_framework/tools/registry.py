from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable

from agent_framework.core.settings import SearchSettings
from agent_framework.providers.amap import has_amap_api_key
from agent_framework.tools.amap import (
    build_amap_hotel_tool,
    build_amap_location_tool,
    build_amap_restaurant_tool,
    build_amap_route_tool,
    build_amap_weather_tool,
)
from agent_framework.tools.web_search import build_tavily_search_tool


@dataclass
class RegisteredTool:
    name: str
    description: str
    builder: Callable[[], Any]
    requires_authorization: bool = False
    has_side_effects: bool = False
    audit_log: bool = False
    supports_dry_run: bool = False
    _instance: Any | None = field(default=None, init=False, repr=False)

    def get_instance(self) -> Any:
        if self._instance is None:
            self._instance = self.builder()
        return self._instance

    @property
    def meta(self) -> dict[str, bool]:
        return {
            "requires_authorization": self.requires_authorization,
            "has_side_effects": self.has_side_effects,
            "audit_log": self.audit_log,
            "supports_dry_run": self.supports_dry_run,
        }


class ToolRegistry:
    def __init__(self, tools: list[RegisteredTool]) -> None:
        self._tools = tools

    @property
    def tools(self) -> tuple[RegisteredTool, ...]:
        return tuple(self._tools)

    def as_langchain_tools(self) -> list[Any]:
        return [tool.get_instance() for tool in self._tools]

    def prompt_block(self) -> str:
        if not self._tools:
            return "- none"

        return "\n".join(f"- {tool.name}: {tool.description}" for tool in self._tools)


def build_default_tool_registry(settings: SearchSettings) -> ToolRegistry:
    has_tavily_key = bool(
        os.getenv("TAVILY_API_KEY")
        or os.getenv("tavily_api_key")
        or os.getenv("TAVILY_KEY")
    )

    tools: list[RegisteredTool] = []
    if has_tavily_key:
        tools.append(
            RegisteredTool(
                name="tavily_search",
                description="Search the public web for fresh information and supporting references.",
                builder=lambda: build_tavily_search_tool(settings.max_results),
            )
        )

    if has_amap_api_key():
        tools.extend(build_amap_tool_specs())

    return ToolRegistry(tools=tools)


def build_amap_tool_specs() -> list[RegisteredTool]:
    return [
        RegisteredTool(
            name="amap_location_lookup",
            description="Resolve a city and address into structured location metadata using AMap.",
            builder=build_amap_location_tool,
        ),
        RegisteredTool(
            name="amap_route_summary",
            description="Summarize transit, driving, and walking routes between two locations using AMap.",
            builder=build_amap_route_tool,
        ),
        RegisteredTool(
            name="amap_hotel_search",
            description="Search hotels around a business location using AMap POI data.",
            builder=build_amap_hotel_tool,
        ),
        RegisteredTool(
            name="amap_restaurant_search",
            description="Search restaurants around a business location using AMap POI data.",
            builder=build_amap_restaurant_tool,
        ),
        RegisteredTool(
            name="amap_weather_forecast",
            description="Get a weather forecast for a city or business location using AMap.",
            builder=build_amap_weather_tool,
        ),
    ]
