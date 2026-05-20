import unittest

from agent_framework.routing.default import KeywordSkillRouter
from agent_framework.routing.llm_router import LLMFallbackRouter
from agent_framework.skills.defaults import build_default_skill_registry


class RoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.router = KeywordSkillRouter()
        self.registry = build_default_skill_registry()

    def test_routes_business_travel_request_to_travel_advisor(self):
        decision = self.router.route("我下周去上海出差，帮我看机票和酒店怎么安排", self.registry)

        self.assertEqual(decision.skill.name, "business_travel_advisor")
        self.assertGreater(decision.confidence, 0.5)
        self.assertIn("planner", decision.required_capabilities)
        self.assertIn("travel_dates", decision.clarification_focus)

    def test_routes_leisure_travel_request_to_general_assistant(self):
        decision = self.router.route("我计划这几天从广州飞到北京，旅游，你挑个好时间好酒店，酒店一晚300以内，其他没有要求，给我最好方案即可", self.registry)

        self.assertEqual(decision.skill.name, "general_assistant")
        self.assertIn("leisure_travel", decision.required_capabilities)

    def test_routes_architecture_request_to_solution_architect(self):
        decision = self.router.route("我想继续优化我的 agent 框架架构", self.registry)

        self.assertEqual(decision.skill.name, "solution_architect")
        self.assertIn("advisor", decision.required_capabilities)

    def test_routes_travel_product_architecture_to_solution_architect(self):
        decision = self.router.route("我要优化商旅出行推荐智能体助手的基础 agent 框架", self.registry)

        self.assertEqual(decision.skill.name, "solution_architect")

    def test_routes_fresh_fact_request_to_research_assistant(self):
        decision = self.router.route("查一下今天美元汇率", self.registry)

        self.assertEqual(decision.skill.name, "research_assistant")
        self.assertIn("web_search", decision.required_capabilities)

    def test_continues_business_travel_thread_from_context(self):
        context = {
            "travel_brief": {
                "origin": "深圳",
                "destination": "上海",
                "departure_date": "下周三",
            }
        }

        decision = self.router.route("在陆家嘴上海中心大厦", self.registry, context)

        self.assertEqual(decision.skill.name, "business_travel_advisor")
        self.assertEqual(decision.reason, "Continuing the existing business travel thread from TravelBrief context.")

    def test_continues_business_travel_thread_for_user_delegation(self):
        context = {
            "travel_brief": {
                "origin": "深圳",
                "destination": "上海",
                "departure_date": "下周三",
            }
        }

        decision = self.router.route("都可以，你推荐个最好的", self.registry, context)

        self.assertEqual(decision.skill.name, "business_travel_advisor")

    def test_llm_fallback_cache_keeps_context_sensitive_followups_distinct(self):
        class NoLLMRouter(LLMFallbackRouter):
            def _llm_classify(self, query, skill_registry, fallback):
                return fallback

        router = NoLLMRouter(keyword_router=self.router)

        no_context_decision = router.route("好的", self.registry, {})
        travel_context_decision = router.route(
            "好的",
            self.registry,
            {
                "travel_brief": {
                    "origin": "深圳",
                    "destination": "上海",
                    "departure_date": "下周三",
                }
            },
        )

        self.assertEqual(no_context_decision.skill.name, "general_assistant")
        self.assertEqual(travel_context_decision.skill.name, "business_travel_advisor")

    def test_llm_fallback_parses_list_content(self):
        router = LLMFallbackRouter(keyword_router=self.router)
        content = [{"type": "text", "text": '{"skill": "general_assistant"}'}]

        self.assertEqual(router._message_content_as_text(content), '{"skill": "general_assistant"}')


if __name__ == "__main__":
    unittest.main()
