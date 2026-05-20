from __future__ import annotations

from datetime import datetime

from agent_framework.core.capabilities import CapabilityRegistry
from agent_framework.domains.business_travel import business_travel_phase_one_prompt_block
from agent_framework.domains.travel_planning import travel_planning_phase_one_prompt_block
from agent_framework.routing.base import RouteDecision
from agent_framework.skills.base import SkillSpec
from agent_framework.tools.registry import ToolRegistry


def build_system_prompt(
    now: datetime,
    capabilities: CapabilityRegistry,
    tools: ToolRegistry,
    skill: SkillSpec,
    route_decision: RouteDecision | None = None,
    request_context: dict | None = None,
) -> str:
    current_date = now.strftime("%Y-%m-%d")
    route_block = _build_route_block(route_decision)
    context_block = _build_context_block(request_context or {})
    domain_block = _build_domain_block(skill, request_context or {}, route_decision)
    return f"""
你是一个面向真实世界任务的高级 Agent 框架原型。
当前日期是 {current_date}。

当前产品方向：
- 终极目标：商旅出行推荐智能体助手，未来支持自动买票、酒店预订和行程执行。
- 当前阶段：Phase 1，只做准确交流、需求澄清、实时建议和可执行方案整理。
- 当前限制：不要声称已经完成购票、预订、支付、取消或改签；涉及这些动作时，先给出待确认清单和后续执行建议。

你的工作原则：
1. 先理解用户真正目标，再回答表层问题。
2. 涉及实时信息、事实核验、日期、新闻、价格、政策或外部变化时，优先使用工具查询，不要猜。
3. 给建议时要真实、可执行、明确区分“事实”“判断”“不确定性”。
4. 如果当前能力还不能直接执行任务，要诚实说明，并给出下一步可落地方案。
5. 默认以中文回复，除非用户要求其他语言。
6. 当关键信息缺失时，先问最少数量的澄清问题；不要用一长串问题压过用户。
7. 对商旅需求，优先收集：出发地、目的地、日期/时间、会议或到达约束、预算/差标、交通偏好、酒店位置偏好、同行人、发票/报销要求。
8. 给商旅建议时，尽量输出：已知信息、缺失信息、推荐方向、备选方案、风险提醒、下一步确认项。
9. 如果上下文里已经存在推荐简报，请优先沿用其中的事实、风险、备选方案和下一步动作，不要重新编造具体票价、余位或酒店库存。
10. 如果可用实时地图工具存在，优先核验地址、通勤时间、酒店位置、周边 POI 和目的地天气，再给出最终推荐。

当前框架能力：
{capabilities.prompt_block()}

当前激活 skill：
- {skill.name}: {skill.description}
- Goal: {skill.target_outcome}
- Workflow: {skill.instruction_block}

路由判断：
{route_block}

请求上下文：
{context_block}

领域协议：
{domain_block}

推荐简报：
{_build_recommendation_block(request_context or {})}

当前可用工具：
{tools.prompt_block()}
""".strip()


def _build_route_block(route_decision: RouteDecision | None) -> str:
    if route_decision is None:
        return "- unavailable"

    lines = [
        f"- skill: {route_decision.skill.name}",
        f"- confidence: {route_decision.confidence:.2f}",
        f"- reason: {route_decision.reason}",
    ]
    if route_decision.matched_signals:
        lines.append(f"- matched_signals: {', '.join(route_decision.matched_signals)}")
    if route_decision.required_capabilities:
        lines.append(f"- required_capabilities: {', '.join(route_decision.required_capabilities)}")
    if route_decision.clarification_focus:
        lines.append(f"- clarification_focus: {', '.join(route_decision.clarification_focus)}")
    return "\n".join(lines)


def _build_context_block(context: dict) -> str:
    if not context:
        return "- none"

    lines: list[str] = []
    for key, value in context.items():
        if isinstance(value, dict):
            lines.append(f"- {key}:")
            for nested_key, nested_value in value.items():
                lines.append(f"  - {nested_key}: {nested_value}")
            continue

        if isinstance(value, (tuple, list)):
            joined_value = ", ".join(str(item) for item in value) if value else "none"
            lines.append(f"- {key}: {joined_value}")
            continue

        text = str(value)
        if "\n" in text:
            lines.append(f"- {key}:")
            lines.extend(f"  {line}" for line in text.splitlines())
        else:
            lines.append(f"- {key}: {text}")

    return "\n".join(lines)


def _build_domain_block(skill: SkillSpec, context: dict, route_decision: RouteDecision | None) -> str:
    if skill.name == "business_travel_advisor":
        return business_travel_phase_one_prompt_block()
    if skill.name == "general_assistant":
        if context.get("travel_mode") == "leisure" or isinstance(context.get("travel_plan_brief"), dict):
            return travel_planning_phase_one_prompt_block()
        return """
通用对话协议：
- 目标：优先把用户真实诉求讲清楚，再给直接可执行的回答。
- 如果问题不是旅行，直接按常规助手方式回答，不要引入商旅或旅游模板。
- 如果问题明显是休闲旅行，再用休闲出行协议。
""".strip()

    return "- none"


def _build_recommendation_block(context: dict) -> str:
    recommendation = context.get("travel_recommendation")
    if not isinstance(recommendation, dict):
        return "- none"

    lines: list[str] = []
    for key in (
        "objective",
        "status",
        "confidence",
        "best_option",
        "transport_plan",
        "hotel_strategy",
        "schedule_timeline",
        "risks",
        "assumptions",
        "pending_realtime_checks",
        "next_actions",
        "alternatives",
    ):
        value = recommendation.get(key)
        if value in (None, "", []):
            continue
        if isinstance(value, list):
            joined = ", ".join(str(item) for item in value)
            lines.append(f"- {key}: {joined}")
        else:
            lines.append(f"- {key}: {value}")

    return "\n".join(lines) if lines else "- none"
