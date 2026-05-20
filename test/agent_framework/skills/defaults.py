from __future__ import annotations

from typing import Any

from agent_framework.domains.business_travel import build_travel_context
from agent_framework.domains.travel_planning import build_travel_plan_context
from agent_framework.skills.base import SkillRegistry, SkillSpec


def _build_leisure_context_if_relevant(query: str, context: dict[str, Any]) -> dict[str, Any]:
    """Only build leisure context when the query or existing context indicates leisure travel."""
    if context.get("travel_mode") == "leisure":
        return build_travel_plan_context(query, context)
    if isinstance(context.get("travel_plan_brief"), dict) and (
        context["travel_plan_brief"].get("origin") or context["travel_plan_brief"].get("destination")
    ):
        return build_travel_plan_context(query, context)

    leisure_keywords = (
        "旅游", "旅行", "游玩", "景点", "度假", "打卡", "自由行", "亲子", "出游", "游览",
    )
    if any(kw in query for kw in leisure_keywords):
        return build_travel_plan_context(query, context)

    return context


def build_default_skill_registry() -> SkillRegistry:
    return SkillRegistry(
        skills=[
            SkillSpec(
                name="general_assistant",
                description="Default conversation skill for general requests and leisure travel planning.",
                instruction_block=(
                    "Clarify the user’s real objective, answer directly, and keep the path forward practical. "
                    "For leisure travel, do not force business-travel style questioning. "
                    "If the user asks for the best plan and key constraints are already present, provide a ranked recommendation with one main plan and one backup plan."
                ),
                target_outcome="Provide helpful dialogue and grounded next steps for both general questions and leisure travel.",
                context_builder=_build_leisure_context_if_relevant,
            ),
            SkillSpec(
                name="research_assistant",
                description="Skill for questions that depend on fresh facts, current events, or verification.",
                instruction_block="Prefer web search before concluding, separate facts from interpretation, and state uncertainty honestly.",
                target_outcome="Deliver timely answers backed by current information.",
                suggested_tools=("tavily_search",),
            ),
            SkillSpec(
                name="business_travel_advisor",
                description="Phase-1 business travel advisor for precise itinerary conversations before booking APIs exist.",
                instruction_block=(
                    "Collect the travel objective, origin, destination, dates, schedule constraints, budget or reimbursement policy, "
                    "traveler preferences, and risk tolerance. If key fields are missing, ask concise follow-up questions before giving a firm recommendation. "
                    "When enough context exists, compare realistic options and label assumptions, tradeoffs, and next actions. "
                    "Do not claim to book, reserve, pay, cancel, or modify tickets or hotels."
                ),
                target_outcome="Turn fuzzy business travel needs into clear, decision-ready recommendations and an execution-ready brief.",
                suggested_tools=(
                    "amap_location_lookup",
                    "amap_route_summary",
                    "amap_hotel_search",
                    "amap_restaurant_search",
                    "amap_weather_forecast",
                    "tavily_search",
                ),
                context_builder=build_travel_context,
            ),
            SkillSpec(
                name="solution_architect",
                description="Skill for framework design, module decomposition, and long-term system evolution.",
                instruction_block="Prioritize clean boundaries, scalable extension points, and honest tradeoffs over clever shortcuts.",
                target_outcome="Turn vague product goals into maintainable system structure.",
            ),
        ],
        default_skill="general_assistant",
    )
