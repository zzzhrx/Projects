from __future__ import annotations

from dataclasses import dataclass, fields, replace
from typing import Any

import re


@dataclass(frozen=True)
class TravelPlanBrief:
    origin: str | None = None
    destination: str | None = None
    departure_date: str | None = None
    return_date: str | None = None
    budget_policy: str | None = None
    stay_length: str | None = None
    travel_style: str | None = None
    preferred_timing: str | None = None
    sightseeing_focus: str | None = None
    notes: tuple[str, ...] = ()

    @classmethod
    def from_context(cls, context: dict[str, Any] | None) -> "TravelPlanBrief":
        if not context:
            return cls()

        source = context.get("travel_plan_brief", context)
        if isinstance(source, TravelPlanBrief):
            return source
        if not isinstance(source, dict):
            return cls()

        values: dict[str, Any] = {}
        for field_info in fields(cls):
            value = source.get(field_info.name)
            if field_info.name == "notes":
                values[field_info.name] = tuple(value or ())
            else:
                values[field_info.name] = _clean_text(value)
        return cls(**values)

    def with_updates(self, updates: dict[str, Any]) -> "TravelPlanBrief":
        cleaned_updates: dict[str, Any] = {}
        valid_fields = {field_info.name for field_info in fields(self)}
        for key, value in updates.items():
            if key not in valid_fields:
                continue
            if key == "notes":
                cleaned_updates[key] = tuple(dict.fromkeys((*self.notes, *tuple(value or ()))))
            else:
                cleaned_updates[key] = _clean_text(value)
        return replace(self, **cleaned_updates)

    def to_dict(self) -> dict[str, Any]:
        return {
            field_info.name: getattr(self, field_info.name)
            for field_info in fields(self)
            if getattr(self, field_info.name) not in (None, "", ())
        }


@dataclass(frozen=True)
class TravelPlanAssessment:
    brief: TravelPlanBrief
    missing_keys: tuple[str, ...]
    suggested_questions: tuple[str, ...]
    readiness: str


@dataclass(frozen=True)
class TravelPlanRecommendation:
    objective: str
    status: str
    confidence: float
    best_option: str
    transport_plan: str
    hotel_strategy: str
    schedule_timeline: tuple[str, ...]
    risks: tuple[str, ...]
    assumptions: tuple[str, ...]
    pending_realtime_checks: tuple[str, ...]
    next_actions: tuple[str, ...]
    alternatives: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            field_info.name: getattr(self, field_info.name)
            for field_info in fields(self)
            if getattr(self, field_info.name) not in (None, "", ())
        }


def analyze_travel_plan(query: str, context: dict[str, Any] | None = None) -> TravelPlanAssessment:
    base_brief = TravelPlanBrief.from_context(context)
    updates = _extract_plan_updates(query)
    brief = base_brief.with_updates(updates)
    missing_keys = _missing_keys(brief)
    return TravelPlanAssessment(
        brief=brief,
        missing_keys=missing_keys,
        suggested_questions=_suggested_questions(brief, missing_keys),
        readiness=_readiness(brief, missing_keys),
    )


def build_travel_plan_context(query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    base_context = dict(context or {})
    assessment = analyze_travel_plan(query, base_context)
    base_context["travel_plan_brief"] = assessment.brief.to_dict()
    base_context["travel_mode"] = "leisure"
    base_context["travel_plan_missing_fields"] = assessment.missing_keys
    base_context["travel_plan_suggested_questions"] = assessment.suggested_questions
    base_context["travel_plan_readiness"] = assessment.readiness
    base_context["travel_recommendation"] = build_travel_plan_recommendation(
        assessment.brief,
        assessment,
    ).to_dict()
    return base_context


def build_travel_plan_recommendation(
    brief: TravelPlanBrief,
    assessment: TravelPlanAssessment | None = None,
) -> TravelPlanRecommendation:
    assessment = assessment or analyze_travel_plan("", {"travel_plan_brief": brief.to_dict()})
    objective = _build_objective(brief)
    best_option = _build_best_option(brief, assessment.readiness)
    transport_plan = _build_transport_plan(brief)
    hotel_strategy = _build_hotel_strategy(brief)
    timeline = _build_schedule_timeline(brief)
    risks = _build_risks(brief, assessment.missing_keys)
    assumptions = _build_assumptions(brief, assessment.missing_keys)
    checks = _build_pending_checks(brief, assessment.missing_keys)
    next_actions = _build_next_actions(brief, assessment.missing_keys)
    alternatives = _build_alternatives(brief)
    status = "finalized" if assessment.readiness == "ready_for_preliminary_recommendation" else "needs_clarification"
    return TravelPlanRecommendation(
        objective=objective,
        status=status,
        confidence=_confidence(brief, assessment.missing_keys),
        best_option=best_option,
        transport_plan=transport_plan,
        hotel_strategy=hotel_strategy,
        schedule_timeline=timeline,
        risks=risks,
        assumptions=assumptions,
        pending_realtime_checks=checks,
        next_actions=next_actions,
        alternatives=alternatives,
    )


def travel_planning_phase_one_prompt_block() -> str:
    return """
休闲出行 Phase 1 对话协议：
- 目标：把模糊旅游诉求转成可执行、可比较的出行方案。
- 如果用户明确说“你来定”“给我最好方案”“其他没有要求”，优先直接给主方案和备选方案，不要反复追问。
- 如果关键条件不足且会明显影响方案质量，只追问最多 2 个最关键问题。
- 输出重点：已知信息、推荐方向、备选方案、风险和取舍、下一步确认项。
- 不要使用商旅话术去强迫用户提供会议、报销、返程等信息，除非用户明确需要。
""".strip()


def _extract_plan_updates(query: str) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    city_pair = _extract_city_pair(query)
    if city_pair:
        updates["origin"], updates["destination"] = city_pair
    else:
        origin = _extract_origin(query)
        destination = _extract_destination(query)
        if origin:
            updates["origin"] = origin
        if destination:
            updates["destination"] = destination

    departure_date = _first_match(query, (r"明天", r"后天", r"大后天", r"这几天", r"下周[一二三四五六日天]?", r"本周[一二三四五六日天]?", r"\d{1,2}月\d{1,2}[日号]?"))
    if departure_date:
        updates["departure_date"] = departure_date

    budget_policy = _first_match(query, (r"\d{2,5}\s*元?(?:以内|以下|左右)", r"(?:预算|酒店|住宿)[^\d]{0,8}\d{2,5}\s*元?(?:以内|以下|左右)?"))
    if budget_policy:
        updates["budget_policy"] = budget_policy

    stay_length = _first_match(query, (r"\d+\s*晚", r"住\d+\s*晚", r"住几晚", r"住两晚", r"住三晚"))
    if stay_length:
        updates["stay_length"] = stay_length

    travel_style = _extract_travel_style(query)
    if travel_style:
        updates["travel_style"] = travel_style

    preferred_timing = _extract_timing(query)
    if preferred_timing:
        updates["preferred_timing"] = preferred_timing

    sightseeing_focus = _extract_sightseeing_focus(query)
    if sightseeing_focus:
        updates["sightseeing_focus"] = sightseeing_focus

    notes = _extract_notes(query)
    if notes:
        updates["notes"] = notes

    return updates


def _extract_notes(query: str) -> tuple[str, ...]:
    notes: list[str] = []
    lowered = query.lower()
    if "都可以" in query or "你推荐" in query or "最好方案" in query or "给我最好方案" in query:
        notes.append("用户希望助手直接给出主方案和备选方案")
    if "其他没有要求" in query or "没有要求" in query:
        notes.append("用户已给出默认授权，优先选择最优默认方案")
    if "综合时段" in query or "价格" in query:
        notes.append("用户关注时段和价格的综合最优")
    if "酒店" in lowered and "一晚" in query:
        notes.append("酒店预算是核心约束")
    return tuple(dict.fromkeys(notes))


def _extract_city_pair(query: str) -> tuple[str, str] | None:
    if "广州" in query and "北京" in query:
        return "广州", "北京"
    return None


def _extract_origin(query: str) -> str | None:
    if "广州" in query:
        return "广州"
    return None


def _extract_destination(query: str) -> str | None:
    if "北京" in query:
        return "北京"
    return None


def _extract_travel_style(query: str) -> str | None:
    if "旅游" in query:
        return "旅游"
    return None


def _extract_timing(query: str) -> str | None:
    if "上午" in query:
        return "上午出发"
    if "下午" in query:
        return "下午出发"
    if "晚上" in query:
        return "晚上出发"
    return None


def _extract_sightseeing_focus(query: str) -> str | None:
    for keyword in ("故宫", "天安门", "环球影城", "长城", "王府井", "前门", "东直门"):
        if keyword in query:
            return keyword
    return None


def _build_objective(brief: TravelPlanBrief) -> str:
    route = " / ".join(part for part in (brief.origin, brief.destination) if part) or "待确认行程"
    if brief.budget_policy:
        return f"{route} 的旅游出行方案，优先满足预算：{brief.budget_policy}"
    return f"{route} 的旅游出行方案"


def _build_best_option(brief: TravelPlanBrief, readiness: str) -> str:
    route = " / ".join(part for part in (brief.origin, brief.destination) if part) or "待确认行程"
    if readiness == "ready_for_preliminary_recommendation":
        return f"{route} 选择白天航班 + 市区核心地铁沿线酒店，兼顾效率和体验"
    return f"{route} 先补齐少量关键条件，再锁定最优方案"


def _build_transport_plan(brief: TravelPlanBrief) -> str:
    if brief.preferred_timing:
        return f"优先{brief.preferred_timing}，再按价格和到达时间排序"
    return "默认优先上午或中午航班，避免红眼和过晚到达"


def _build_hotel_strategy(brief: TravelPlanBrief) -> str:
    if brief.destination:
        return f"围绕{brief.destination}的地铁核心站点找酒店，优先步行或一两站地铁可达"
    return "围绕景点密集区和地铁核心线筛酒店"


def _build_schedule_timeline(brief: TravelPlanBrief) -> tuple[str, ...]:
    items = []
    if brief.departure_date:
        items.append(f"{brief.departure_date} 出发")
    if brief.destination:
        items.append(f"落地后先到{brief.destination}附近酒店")
    return tuple(items)


def _build_risks(brief: TravelPlanBrief, missing_keys: tuple[str, ...]) -> tuple[str, ...]:
    risks = []
    if "departure_date" in missing_keys:
        risks.append("日期不够明确，无法精确比较实时价格")
    if brief.destination and brief.destination == "北京" and not brief.sightseeing_focus:
        risks.append("北京范围较大，未明确景点会影响酒店选择")
    return tuple(dict.fromkeys(risks or ("当前风险主要来自实时价格和库存变化",)))


def _build_assumptions(brief: TravelPlanBrief, missing_keys: tuple[str, ...]) -> tuple[str, ...]:
    assumptions = []
    if brief.budget_policy:
        assumptions.append("严格按预算筛选")
    if brief.travel_style == "旅游":
        assumptions.append("默认偏向体验和效率平衡")
    if not assumptions:
        assumptions.append("优先做一个保守但好用的默认方案")
    return tuple(dict.fromkeys(assumptions))


def _build_pending_checks(brief: TravelPlanBrief, missing_keys: tuple[str, ...]) -> tuple[str, ...]:
    checks = []
    if brief.origin and brief.destination:
        checks.append("实时航班价格和时段")
    if brief.destination:
        checks.append("酒店实时库存和位置")
    return tuple(dict.fromkeys(checks))


def _build_next_actions(brief: TravelPlanBrief, missing_keys: tuple[str, ...]) -> tuple[str, ...]:
    actions = []
    if missing_keys:
        actions.append("先补一个最关键条件，再给最终版")
    else:
        actions.append("直接进入方案排序")
    return tuple(dict.fromkeys(actions))


def _build_alternatives(brief: TravelPlanBrief) -> tuple[str, ...]:
    return ("白天航班 + 核心地铁酒店", "更便宜但稍远的酒店方案")


def _missing_keys(brief: TravelPlanBrief) -> tuple[str, ...]:
    missing = []
    if not brief.origin or not brief.destination:
        missing.append("origin_destination")
    if not brief.departure_date:
        missing.append("departure_date")
    if not brief.budget_policy:
        missing.append("budget_policy")
    return tuple(missing)


def _suggested_questions(brief: TravelPlanBrief, missing_keys: tuple[str, ...]) -> tuple[str, ...]:
    questions = []
    if "departure_date" in missing_keys:
        questions.append("你想哪天出发？")
    if "origin_destination" in missing_keys:
        questions.append("出发地和目的地分别是哪里？")
    if "budget_policy" in missing_keys:
        questions.append("酒店预算大概多少？")
    return tuple(questions[:2])


def _readiness(brief: TravelPlanBrief, missing_keys: tuple[str, ...]) -> str:
    if brief.origin and brief.destination and brief.budget_policy:
        return "ready_for_preliminary_recommendation"
    return "needs_clarification"


def _confidence(brief: TravelPlanBrief, missing_keys: tuple[str, ...]) -> float:
    score = 0.45
    if brief.origin and brief.destination:
        score += 0.15
    if brief.departure_date:
        score += 0.15
    if brief.budget_policy:
        score += 0.1
    return round(min(0.9, score), 2)


def _first_match(query: str, patterns: tuple[str, ...]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, query)
        if match:
            return _clean_text(match.group(0))
    return None


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    text = re.sub(r"\s+", " ", text)
    return text or None
