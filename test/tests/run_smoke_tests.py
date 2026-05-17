from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent_framework.core.capabilities import build_default_capability_registry
from agent_framework.domains.business_travel import analyze_travel_brief
from agent_framework.prompts.system import build_system_prompt
from agent_framework.routing.default import KeywordSkillRouter
from agent_framework.skills.defaults import build_default_skill_registry
from agent_framework.tools.registry import ToolRegistry


def main() -> None:
    skill_registry = build_default_skill_registry()
    router = KeywordSkillRouter()

    travel_decision = router.route("我下周去上海出差，帮我看机票和酒店怎么安排", skill_registry)
    assert travel_decision.skill.name == "business_travel_advisor"
    assert "planner" in travel_decision.required_capabilities

    architecture_decision = router.route("我想继续优化我的 agent 框架架构", skill_registry)
    assert architecture_decision.skill.name == "solution_architect"

    research_decision = router.route("查一下今天美元汇率", skill_registry)
    assert research_decision.skill.name == "research_assistant"

    travel_assessment = analyze_travel_brief("我下周三从深圳到上海出差，下午2点前到，酒店800以内")
    assert travel_assessment.brief.origin == "深圳"
    assert travel_assessment.brief.destination == "上海"
    assert travel_assessment.readiness == "ready_for_preliminary_recommendation"

    prompt = build_system_prompt(
        now=datetime(2026, 4, 27),
        capabilities=build_default_capability_registry(),
        tools=ToolRegistry([]),
        skill=travel_decision.skill,
        route_decision=travel_decision,
        request_context={"traveler": "default_user"},
    )
    assert "Phase 1" in prompt
    assert "不要声称已经完成购票、预订、支付、取消或改签" in prompt
    assert "business_travel_advisor" in prompt
    assert "traveler: default_user" in prompt

    print("smoke tests passed")


if __name__ == "__main__":
    main()
