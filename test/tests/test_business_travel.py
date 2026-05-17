import unittest
from datetime import datetime

from agent_framework.agent.service import AdvancedAgentService
from agent_framework.core.capabilities import build_default_capability_registry
from agent_framework.core.models import AgentRequest
from agent_framework.domains.business_travel import (
    analyze_travel_brief,
    build_travel_context,
    build_travel_recommendation,
)
from agent_framework.prompts.system import build_system_prompt
from agent_framework.skills.defaults import build_default_skill_registry
from agent_framework.tools.registry import ToolRegistry


class BusinessTravelBriefTests(unittest.TestCase):
    def test_extracts_core_travel_brief_from_common_request(self):
        assessment = analyze_travel_brief("我下周三从深圳到上海出差，下午2点前到，酒店800以内")

        self.assertEqual(assessment.brief.origin, "深圳")
        self.assertEqual(assessment.brief.destination, "上海")
        self.assertEqual(assessment.brief.departure_date, "下周三")
        self.assertEqual(assessment.brief.arrival_deadline, "下午2点前到")
        self.assertEqual(assessment.brief.budget_policy, "酒店800以内")
        self.assertEqual(assessment.readiness, "ready_for_preliminary_recommendation")

    def test_builds_missing_field_questions_with_limit(self):
        assessment = analyze_travel_brief("我下周去上海出差，帮我安排一下")

        self.assertEqual(assessment.brief.destination, "上海")
        self.assertIn("origin_destination", assessment.missing_keys)
        self.assertIn("business_constraints", assessment.missing_keys)
        self.assertLessEqual(len(assessment.suggested_questions), 3)

    def test_merges_existing_context_with_new_user_message(self):
        context = build_travel_context("我下周三去上海出差", {})
        updated_context = build_travel_context(
            "我从深圳出发，下午2点前到，预算800以内，高铁优先，稳妥一点",
            context,
        )

        brief = updated_context["travel_brief"]
        self.assertEqual(brief["origin"], "深圳")
        self.assertEqual(brief["destination"], "上海")
        self.assertEqual(brief["departure_date"], "下周三")
        self.assertEqual(brief["transport_preference"], "高铁优先")
        self.assertEqual(brief["risk_tolerance"], "低风险/稳妥优先")

    def test_extracts_business_location_from_follow_up(self):
        context = build_travel_context("我下周三从深圳到上海出差，下午2点前到，酒店800以内", {})
        updated_context = build_travel_context("在陆家嘴上海中心大厦", context)

        brief = updated_context["travel_brief"]
        self.assertEqual(brief["business_location"], "陆家嘴上海中心大厦")

    def test_extracts_clean_business_location_from_combined_request(self):
        assessment = analyze_travel_brief(
            "我下周三从深圳到上海出差，下午2点前到，酒店800以内，去上海中心大厦附近，早班机，返程不用规划。给我你认为最好的方案"
        )

        self.assertEqual(assessment.brief.business_location, "上海中心大厦")
        self.assertEqual(assessment.brief.hotel_area, "上海中心大厦附近")

    def test_records_delegation_note_without_losing_existing_brief(self):
        context = build_travel_context("我下周三从深圳到上海出差，下午2点前到，酒店800以内", {})
        updated_context = build_travel_context("都可以，你推荐个最好的，硬性要求我都说了", context)

        brief = updated_context["travel_brief"]
        self.assertEqual(brief["origin"], "深圳")
        self.assertEqual(brief["destination"], "上海")
        self.assertIn("用户授权助手在已知硬约束下选择推荐方案", brief["notes"])
        self.assertIn("用户表示硬性要求已提供，后续应基于现有约束给出推荐", brief["notes"])

    def test_builds_recommendation_brief_from_travel_brief(self):
        assessment = analyze_travel_brief("我下周三从深圳到上海出差，下午2点前到，酒店800以内")
        recommendation = build_travel_recommendation(assessment.brief, assessment)

        self.assertIn("深圳", recommendation.best_option)
        self.assertTrue(recommendation.transport_plan)
        self.assertTrue(recommendation.hotel_strategy)
        self.assertTrue(recommendation.pending_realtime_checks)
        self.assertTrue(recommendation.next_actions)
        self.assertGreaterEqual(recommendation.confidence, 0.35)

    def test_service_persists_travel_context_by_thread(self):
        service = AdvancedAgentService()

        service._build_request_context(
            AgentRequest(query="我下周三去上海出差", thread_id="travel-thread"),
            "business_travel_advisor",
        )
        context = service._build_request_context(
            AgentRequest(query="我从深圳出发，下午2点前到，预算800以内", thread_id="travel-thread"),
            "business_travel_advisor",
        )

        brief = context["travel_brief"]
        self.assertEqual(brief["origin"], "深圳")
        self.assertEqual(brief["destination"], "上海")
        self.assertEqual(brief["departure_date"], "下周三")
        self.assertEqual(context["travel_readiness"], "ready_for_preliminary_recommendation")

    def test_service_routes_follow_ups_to_business_travel_when_thread_has_brief(self):
        service = AdvancedAgentService()

        first_context = service._build_request_context(
            AgentRequest(
                query="我下周三从深圳到上海出差，下午2点前到，酒店800以内",
                thread_id="travel-route-thread",
            ),
            "business_travel_advisor",
        )
        first_decision = service.skill_router.route(
            "我下周三从深圳到上海出差，下午2点前到，酒店800以内",
            service.skill_registry,
            first_context,
        )
        second_decision = service.skill_router.route(
            "在陆家嘴上海中心大厦",
            service.skill_registry,
            first_context,
        )
        second_context = service._build_request_context(
            AgentRequest(query="在陆家嘴上海中心大厦", thread_id="travel-route-thread"),
            second_decision.skill.name,
            first_context,
        )
        third_decision = service.skill_router.route(
            "都可以，你推荐个最好的",
            service.skill_registry,
            second_context,
        )

        self.assertEqual(first_decision.skill.name, "business_travel_advisor")
        self.assertEqual(second_decision.skill.name, "business_travel_advisor")
        self.assertEqual(third_decision.skill.name, "business_travel_advisor")
        self.assertEqual(second_context["travel_brief"]["business_location"], "陆家嘴上海中心大厦")

    def test_prompt_includes_recommendation_brief(self):
        assessment = analyze_travel_brief("我下周三从深圳到上海出差，下午2点前到，酒店800以内")
        context = build_travel_context("我下周三从深圳到上海出差，下午2点前到，酒店800以内", {})
        skill = build_default_skill_registry().get("business_travel_advisor")
        prompt = build_system_prompt(
            now=datetime(2026, 5, 9),
            capabilities=build_default_capability_registry(),
            tools=ToolRegistry([]),
            skill=skill,
            route_decision=None,
            request_context=context,
        )

        self.assertIn("推荐简报", prompt)
        self.assertIn("best_option", prompt)


if __name__ == "__main__":
    unittest.main()
