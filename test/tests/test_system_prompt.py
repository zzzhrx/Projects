import unittest
from datetime import datetime

from agent_framework.core.capabilities import build_default_capability_registry
from agent_framework.prompts.system import build_system_prompt
from agent_framework.routing.default import KeywordSkillRouter
from agent_framework.skills.defaults import build_default_skill_registry
from agent_framework.tools.registry import ToolRegistry, build_amap_tool_specs


class SystemPromptTests(unittest.TestCase):
    def test_business_travel_prompt_contains_phase_one_boundaries(self):
        skill_registry = build_default_skill_registry()
        route_decision = KeywordSkillRouter().route("我要去北京出差，帮我安排行程", skill_registry)

        prompt = build_system_prompt(
            now=datetime(2026, 4, 27),
            capabilities=build_default_capability_registry(),
            tools=ToolRegistry([]),
            skill=route_decision.skill,
            route_decision=route_decision,
            request_context={"traveler": "default_user"},
        )

        self.assertIn("Phase 1", prompt)
        self.assertIn("不要声称已经完成购票、预订、支付、取消或改签", prompt)
        self.assertIn("business_travel_advisor", prompt)
        self.assertIn("traveler: default_user", prompt)

    def test_business_travel_prompt_exposes_realtime_map_tools_when_available(self):
        skill_registry = build_default_skill_registry()
        route_decision = KeywordSkillRouter().route("我下周去上海出差，住陆家嘴附近", skill_registry)

        prompt = build_system_prompt(
            now=datetime(2026, 5, 10),
            capabilities=build_default_capability_registry(),
            tools=ToolRegistry(build_amap_tool_specs()),
            skill=route_decision.skill,
            route_decision=route_decision,
            request_context={"travel_brief": {"destination": "上海", "business_location": "陆家嘴"}},
        )

        self.assertIn("如果可用实时地图工具存在", prompt)
        self.assertIn("amap_hotel_search", prompt)
        self.assertIn("amap_route_summary", prompt)


if __name__ == "__main__":
    unittest.main()
