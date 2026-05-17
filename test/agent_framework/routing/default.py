from __future__ import annotations

from typing import Any

from agent_framework.routing.base import BaseSkillRouter, RouteDecision
from agent_framework.skills.base import SkillRegistry


class KeywordSkillRouter(BaseSkillRouter):
    research_keywords = {
        "最新",
        "今天",
        "实时",
        "新闻",
        "价格",
        "股价",
        "汇率",
        "政策",
        "搜索",
        "查一下",
        "look up",
        "latest",
    }
    business_travel_keywords = {
        "商旅",
        "出差",
        "差旅",
        "高铁",
        "火车",
        "机场",
        "车站",
        "退改",
        "报销",
        "预算",
        "travel",
        "flight",
        "hotel",
        "trip",
    }
    framework_intent_keywords = {
        "架构",
        "框架",
        "设计",
        "重构",
        "模块",
        "目录",
        "结构",
        "系统",
        "开发",
        "实现",
        "优化",
        "agent",
        "workflow",
    }
    architecture_keywords = {
        "架构",
        "框架",
        "设计",
        "重构",
        "模块",
        "目录",
        "结构",
        "agent",
        "workflow",
    }
    travel_continuation_keywords = {
        "都可以",
        "你推荐",
        "最好的",
        "按你说的",
        "可以",
        "行",
        "确认",
        "就这个",
        "没问题",
        "附近",
        "周边",
        "大厦",
        "中心",
        "机场",
        "车站",
        "酒店",
        "住",
        "预算",
        "返程",
        "回程",
        "几晚",
        "一晚",
        "两晚",
        "三晚",
    }
    leisure_travel_keywords = {
        "旅游",
        "旅行",
        "游玩",
        "景点",
        "度假",
        "打卡",
        "自由行",
        "亲子",
        "出游",
        "游览",
        "逛",
    }
    leisure_goal_keywords = {
        "最好",
        "最好的",
        "挑个好时间",
        "挑个好酒店",
        "好时间",
        "好酒店",
        "给我最好方案",
        "你来定",
        "其他没有要求",
    }

    def route(
        self,
        query: str,
        skill_registry: SkillRegistry,
        context: dict[str, Any] | None = None,
    ) -> RouteDecision:
        lowered_query = query.lower()
        travel_signals = self._matched(lowered_query, self.business_travel_keywords)
        architecture_signals = self._matched(lowered_query, self.architecture_keywords)
        research_signals = self._matched(lowered_query, self.research_keywords)
        continuation_signals = self._matched(lowered_query, self.travel_continuation_keywords)
        leisure_signals = self._matched(lowered_query, self.leisure_travel_keywords)
        leisure_goal_signals = self._matched(lowered_query, self.leisure_goal_keywords)
        has_travel_context = self._has_travel_context(context)

        if (
            architecture_signals
            and self._contains_any(lowered_query, self.framework_intent_keywords)
            and skill_registry.has("solution_architect")
        ):
            return RouteDecision(
                skill=skill_registry.get("solution_architect"),
                confidence=self._confidence(architecture_signals),
                reason="The request is about framework or product architecture, even though it may mention the travel domain.",
                matched_signals=architecture_signals,
                required_capabilities=("dialogue", "advisor", "planner"),
                clarification_focus=("target_state", "current_constraints", "tradeoffs"),
            )

        if (
            has_travel_context
            and skill_registry.has("business_travel_advisor")
            and (continuation_signals or self._looks_like_short_follow_up(query))
        ):
            return RouteDecision(
                skill=skill_registry.get("business_travel_advisor"),
                confidence=0.82,
                reason="Continuing the existing business travel thread from TravelBrief context.",
                matched_signals=continuation_signals or ("short_follow_up",),
                required_capabilities=("dialogue", "advisor", "planner"),
                clarification_focus=(
                    "update_travel_brief",
                    "confirm_constraints",
                    "recommendation_readiness",
                ),
            )

        if travel_signals and skill_registry.has("business_travel_advisor"):
            return RouteDecision(
                skill=skill_registry.get("business_travel_advisor"),
                confidence=self._confidence(travel_signals),
                reason="The request contains business travel planning signals.",
                matched_signals=travel_signals,
                required_capabilities=("dialogue", "advisor", "planner"),
                clarification_focus=(
                    "origin_destination",
                    "travel_dates",
                    "schedule_constraints",
                    "budget_policy",
                    "traveler_preferences",
                ),
            )

        if self._should_route_to_leisure_trip(query, context) and skill_registry.has("general_assistant"):
            return RouteDecision(
                skill=skill_registry.get("general_assistant"),
                confidence=self._confidence(leisure_signals or leisure_goal_signals or ("leisure_trip",)),
                reason="The request looks like leisure travel or general trip planning rather than business travel.",
                matched_signals=leisure_signals or leisure_goal_signals or ("leisure_trip",),
                required_capabilities=("dialogue", "advisor", "planner", "leisure_travel"),
                clarification_focus=("origin_destination", "travel_dates", "budget_policy"),
            )

        if architecture_signals and skill_registry.has("solution_architect"):
            return RouteDecision(
                skill=skill_registry.get("solution_architect"),
                confidence=self._confidence(architecture_signals),
                reason="The request asks about architecture, framework design, or module evolution.",
                matched_signals=architecture_signals,
                required_capabilities=("dialogue", "advisor", "planner"),
                clarification_focus=("target_state", "current_constraints", "tradeoffs"),
            )

        if research_signals and skill_registry.has("research_assistant"):
            return RouteDecision(
                skill=skill_registry.get("research_assistant"),
                confidence=self._confidence(research_signals),
                reason="The request appears to depend on fresh facts or verification.",
                matched_signals=research_signals,
                required_capabilities=("dialogue", "web_search"),
                clarification_focus=("freshness_requirement", "source_quality", "decision_context"),
            )

        return RouteDecision(
            skill=skill_registry.default(),
            confidence=0.45,
            reason="No specialized route matched; using the default conversation skill.",
            required_capabilities=("dialogue",),
            clarification_focus=("user_goal", "missing_context"),
        )

    def _matched(self, query: str, keywords: set[str]) -> tuple[str, ...]:
        return tuple(sorted(keyword for keyword in keywords if keyword in query))

    def _contains_any(self, query: str, keywords: set[str]) -> bool:
        return any(keyword in query for keyword in keywords)

    def _confidence(self, signals: tuple[str, ...]) -> float:
        return min(0.95, 0.55 + 0.1 * len(signals))

    def _has_travel_context(self, context: dict[str, Any] | None) -> bool:
        if not context:
            return False

        travel_brief = context.get("travel_brief")
        if not isinstance(travel_brief, dict):
            return False

        return bool(travel_brief.get("origin") or travel_brief.get("destination"))

    def _should_route_to_leisure_trip(self, query: str, context: dict[str, Any] | None) -> bool:
        if self._has_leisure_travel_context(context):
            return True

        lowered_query = query.lower()
        leisure_markers = self._matched(lowered_query, self.leisure_travel_keywords)
        if leisure_markers:
            return True

        return False

    def _has_leisure_travel_context(self, context: dict[str, Any] | None) -> bool:
        if not context:
            return False
        travel_mode = context.get("travel_mode")
        if travel_mode == "leisure":
            return True
        travel_plan_brief = context.get("travel_plan_brief")
        return isinstance(travel_plan_brief, dict) and bool(
            travel_plan_brief.get("origin") or travel_plan_brief.get("destination")
        )

    def _looks_like_short_follow_up(self, query: str) -> bool:
        stripped_query = query.strip()
        if not stripped_query:
            return False

        return len(stripped_query) <= 30
