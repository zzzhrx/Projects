from __future__ import annotations

from agent_framework.skills.base import SkillRegistry, SkillSpec


def build_default_skill_registry() -> SkillRegistry:
    return SkillRegistry(
        skills=[
            SkillSpec(
                name="general_assistant",
                description="Default conversation skill for general requests and leisure travel planning.",
                instruction_block=(
                    "Clarify the user’s real objective, answer directly, and keep the path forward practical. "
                    "For leisure travel, do not force business-travel style questioning. "
                    "If the user asks for the best plan and key constraints are already present, provide a ranked recommendation with one主方案 and one备选方案."
                ),
                target_outcome="Provide helpful dialogue and grounded next steps for both general questions and leisure travel.",
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
                    "tavily_search",
                ),
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
