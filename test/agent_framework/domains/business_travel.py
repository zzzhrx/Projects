from __future__ import annotations

import re
from dataclasses import dataclass, fields, replace
from typing import Any


@dataclass(frozen=True)
class TravelIntakeField:
    key: str
    label: str
    why_it_matters: str


@dataclass(frozen=True)
class TravelBrief:
    origin: str | None = None
    destination: str | None = None
    departure_date: str | None = None
    return_date: str | None = None
    arrival_deadline: str | None = None
    business_constraints: str | None = None
    business_location: str | None = None
    budget_policy: str | None = None
    hotel_area: str | None = None
    transport_preference: str | None = None
    traveler_count: str | None = None
    risk_tolerance: str | None = None
    reimbursement_requirements: str | None = None
    notes: tuple[str, ...] = ()

    @classmethod
    def from_context(cls, context: dict[str, Any] | None) -> "TravelBrief":
        if not context:
            return cls()

        source = context.get("travel_brief", context)
        if isinstance(source, TravelBrief):
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

    def with_updates(self, updates: dict[str, Any]) -> "TravelBrief":
        cleaned_updates: dict[str, Any] = {}
        valid_fields = {field_info.name for field_info in fields(self)}
        for key, value in updates.items():
            if key not in valid_fields:
                continue
            if key == "notes":
                cleaned_updates[key] = _merge_notes(self.notes, tuple(value or ()))
            else:
                cleaned_updates[key] = _clean_text(value)
        return replace(self, **cleaned_updates)

    def to_dict(self) -> dict[str, Any]:
        return {
            field_info.name: getattr(self, field_info.name)
            for field_info in fields(self)
            if getattr(self, field_info.name) not in (None, "", ())
        }

    def known_items(self) -> tuple[tuple[str, str], ...]:
        labels = {
            "origin": "出发地",
            "destination": "目的地",
            "departure_date": "出行日期",
            "return_date": "返程时间",
            "arrival_deadline": "到达时限",
            "business_constraints": "业务约束",
            "business_location": "业务地点",
            "budget_policy": "预算/差标",
            "hotel_area": "酒店区域",
            "transport_preference": "交通偏好",
            "traveler_count": "出行人数",
            "risk_tolerance": "风险偏好",
            "reimbursement_requirements": "报销要求",
        }
        items: list[tuple[str, str]] = []
        for key, label in labels.items():
            value = getattr(self, key)
            if value:
                items.append((label, value))
        return tuple(items)


@dataclass(frozen=True)
class TravelBriefAssessment:
    brief: TravelBrief
    missing_keys: tuple[str, ...]
    suggested_questions: tuple[str, ...]
    readiness: str

    def prompt_block(self) -> str:
        known_lines = (
            "\n".join(f"- {label}: {value}" for label, value in self.brief.known_items())
            if self.brief.known_items()
            else "- none"
        )
        missing_lines = (
            "\n".join(f"- {key}" for key in self.missing_keys)
            if self.missing_keys
            else "- none"
        )
        question_lines = (
            "\n".join(f"- {question}" for question in self.suggested_questions)
            if self.suggested_questions
            else "- none"
        )
        return f"""
当前 TravelBrief:
{known_lines}

缺失字段:
{missing_lines}

建议追问:
{question_lines}

推荐就绪度:
- {self.readiness}
""".strip()


@dataclass(frozen=True)
class RecommendationBrief:
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

    def prompt_block(self) -> str:
        def _format_section(title: str, value: Any) -> str:
            if isinstance(value, tuple):
                if not value:
                    return f"- {title}: none"
                return "\n".join(f"- {title}: {item}" for item in value)
            return f"- {title}: {value}"

        sections = [
            _format_section("objective", self.objective),
            _format_section("status", self.status),
            _format_section("confidence", f"{self.confidence:.2f}"),
            _format_section("best_option", self.best_option),
            _format_section("transport_plan", self.transport_plan),
            _format_section("hotel_strategy", self.hotel_strategy),
            _format_section("schedule_timeline", self.schedule_timeline),
            _format_section("risks", self.risks),
            _format_section("assumptions", self.assumptions),
            _format_section("pending_realtime_checks", self.pending_realtime_checks),
            _format_section("next_actions", self.next_actions),
            _format_section("alternatives", self.alternatives),
        ]
        return "\n".join(sections)


PHASE_ONE_INTAKE_FIELDS: tuple[TravelIntakeField, ...] = (
    TravelIntakeField(
        key="origin_destination",
        label="出发地和目的地",
        why_it_matters="决定交通方式、机场/车站选择和路线可行性。",
    ),
    TravelIntakeField(
        key="travel_dates",
        label="出行日期和时间窗口",
        why_it_matters="决定实时价格、余票、酒店可订性和是否需要备选方案。",
    ),
    TravelIntakeField(
        key="business_constraints",
        label="会议、到达、返程等硬约束",
        why_it_matters="商旅推荐应优先保证准点和业务目标，而不是只追求低价。",
    ),
    TravelIntakeField(
        key="budget_policy",
        label="预算、差标和报销要求",
        why_it_matters="避免推荐不可报销或超标准的方案。",
    ),
    TravelIntakeField(
        key="traveler_preferences",
        label="交通、酒店和舒适度偏好",
        why_it_matters="在满足业务约束后优化体验和效率。",
    ),
    TravelIntakeField(
        key="risk_tolerance",
        label="风险容忍度",
        why_it_matters="决定是否优先直达、早到、可退改和留出冗余时间。",
    ),
)


KNOWN_CITIES: tuple[str, ...] = (
    "北京",
    "上海",
    "广州",
    "深圳",
    "杭州",
    "南京",
    "成都",
    "重庆",
    "武汉",
    "西安",
    "苏州",
    "天津",
    "郑州",
    "长沙",
    "青岛",
    "厦门",
    "宁波",
    "合肥",
    "济南",
    "福州",
    "昆明",
    "沈阳",
    "大连",
    "哈尔滨",
    "长春",
    "南昌",
    "贵阳",
    "南宁",
    "海口",
    "三亚",
    "香港",
    "澳门",
    "台北",
)

BUSINESS_LOCATION_KEYWORDS: tuple[str, ...] = (
    "大厦",
    "园区",
    "广场",
    "写字楼",
    "会议室",
    "办公室",
    "陆家嘴",
    "张江",
    "徐家汇",
    "静安寺",
    "外滩",
    "世纪大道",
)

BUSINESS_LOCATION_SUFFIXES = "写字楼|会议室|办公室|大厦|园区|广场|中心"

DATE_PATTERNS: tuple[str, ...] = (
    r"今天",
    r"明天",
    r"后天",
    r"大后天",
    r"下周[一二三四五六日天]?",
    r"本周[一二三四五六日天]?",
    r"周[一二三四五六日天]",
    r"星期[一二三四五六日天]",
    r"\d{1,2}月\d{1,2}[日号]?",
    r"\d{4}-\d{1,2}-\d{1,2}",
)


def analyze_travel_brief(query: str, context: dict[str, Any] | None = None) -> TravelBriefAssessment:
    base_brief = TravelBrief.from_context(context)
    updates = _extract_brief_updates(query)
    brief = base_brief.with_updates(updates)
    missing_keys = _missing_keys(brief)
    return TravelBriefAssessment(
        brief=brief,
        missing_keys=missing_keys,
        suggested_questions=_suggested_questions(brief, missing_keys),
        readiness=_readiness(brief, missing_keys),
    )


def build_travel_context(query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    base_context = dict(context or {})
    assessment = analyze_travel_brief(query, base_context)
    base_context["travel_brief"] = assessment.brief.to_dict()
    base_context["travel_mode"] = "business"
    base_context["travel_missing_fields"] = assessment.missing_keys
    base_context["travel_suggested_questions"] = assessment.suggested_questions
    base_context["travel_readiness"] = assessment.readiness
    base_context["travel_brief_prompt"] = assessment.prompt_block()
    base_context["travel_recommendation"] = build_travel_recommendation(
        assessment.brief,
        assessment,
    ).to_dict()
    return base_context


def build_travel_recommendation(
    brief: TravelBrief,
    assessment: TravelBriefAssessment | None = None,
) -> RecommendationBrief:
    assessment = assessment or analyze_travel_brief("", {"travel_brief": brief.to_dict()})
    route = _build_route_summary(brief)
    confidence = _recommendation_confidence(brief, assessment.missing_keys)
    objective = _build_objective(brief)
    best_option = _build_best_option(brief, assessment.readiness)
    transport_plan = _build_transport_plan(brief)
    hotel_strategy = _build_hotel_strategy(brief)
    timeline = _build_schedule_timeline(brief, route)
    risks = _build_risks(brief, assessment.missing_keys)
    assumptions = _build_assumptions(brief, assessment.missing_keys)
    checks = _build_pending_checks(brief, assessment.missing_keys)
    next_actions = _build_next_actions(brief, assessment.missing_keys)
    alternatives = _build_alternatives(brief)

    status = "finalized" if assessment.readiness == "ready_for_preliminary_recommendation" else "needs_clarification"
    return RecommendationBrief(
        objective=objective,
        status=status,
        confidence=confidence,
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


def _build_route_summary(brief: TravelBrief) -> str:
    parts: list[str] = []
    if brief.origin:
        parts.append(brief.origin)
    if brief.destination:
        parts.append(brief.destination)
    if brief.departure_date:
        parts.append(brief.departure_date)
    if not parts:
        return "待确认行程路线"
    return " / ".join(parts)


def _build_objective(brief: TravelBrief) -> str:
    route = _build_route_summary(brief)
    if brief.arrival_deadline:
        return f"{route}，确保{brief.arrival_deadline}前抵达"
    if brief.business_constraints:
        return f"{route}，满足业务约束：{brief.business_constraints}"
    return f"{route}，生成可执行商旅推荐"


def _recommendation_confidence(brief: TravelBrief, missing_keys: tuple[str, ...]) -> float:
    total_fields = 6.0
    known_score = 0.0
    for field_name in ("origin", "destination", "departure_date", "arrival_deadline", "budget_policy", "risk_tolerance"):
        if getattr(brief, field_name):
            known_score += 1.0
    if brief.business_location:
        known_score += 0.5
    penalty = min(0.4, 0.08 * len(missing_keys))
    return round(max(0.35, min(0.95, known_score / total_fields + 0.25 - penalty)), 2)


def _build_best_option(brief: TravelBrief, readiness: str) -> str:
    route = _build_route_summary(brief)
    if readiness == "ready_for_preliminary_recommendation":
        departure = brief.departure_date or "出行日"
        if brief.risk_tolerance and "低风险" in brief.risk_tolerance:
            return f"{route} 选择周二晚提前抵达，周三白天留足缓冲，优先保证{departure}的准点到达"
        return f"{route} 选择周三早班机优先，兼顾效率与预算"
    if brief.departure_date:
        return f"{route} 先补齐业务地点后，优先给出当天早班机或前一晚抵达的双方案"
    return f"{route} 先补齐关键约束，再生成推荐"


def _build_transport_plan(brief: TravelBrief) -> str:
    pieces: list[str] = []
    if brief.transport_preference:
        pieces.append(f"优先满足交通偏好：{brief.transport_preference}")
    else:
        pieces.append("默认优先早班直达、少中转、减少迟到风险")
    if brief.arrival_deadline:
        pieces.append(f"围绕{brief.arrival_deadline}倒推出发时间")
    if brief.risk_tolerance:
        pieces.append(f"风险偏好：{brief.risk_tolerance}")
    return "；".join(pieces)


def _build_hotel_strategy(brief: TravelBrief) -> str:
    if brief.business_location:
        return f"围绕{brief.business_location} 选择步行或短途打车可达的商务酒店"
    if brief.hotel_area:
        return f"优先选择{brief.hotel_area}附近的商务酒店"
    if brief.destination:
        return f"围绕{brief.destination}核心商务区，优先选地铁或短打车可达的酒店"
    return "先依据业务地点和预算筛选商务连锁酒店"


def _build_schedule_timeline(brief: TravelBrief, route: str) -> tuple[str, ...]:
    timeline: list[str] = []
    if brief.departure_date:
        timeline.append(f"{brief.departure_date}：完成出发前准备并确认实时票价/余位")
    if brief.arrival_deadline:
        timeline.append(f"出发当天：按{brief.arrival_deadline}倒推，留出至少1.5至2小时缓冲")
    if brief.business_location:
        timeline.append(f"抵达后：先到{brief.business_location}附近酒店或会场周边完成落地")
    timeline.append(f"路线锚点：{route}")
    return tuple(timeline)


def _build_risks(brief: TravelBrief, missing_keys: tuple[str, ...]) -> tuple[str, ...]:
    risks: list[str] = []
    if "travel_dates" in missing_keys:
        risks.append("日期或时间窗口未完全明确，实时查询前无法锁定最优班次")
    if "business_constraints" in missing_keys:
        risks.append("业务硬约束未完全确认，可能影响是否需要提前一晚抵达")
    if brief.destination and brief.destination == "上海" and not brief.business_location:
        risks.append("上海通勤差异较大，未确认具体楼宇前酒店和机场策略仍有偏差")
    if brief.risk_tolerance and "低风险" in brief.risk_tolerance:
        risks.append("低风险偏好意味着需要更高的时间缓冲与更保守的航班选择")
    if not risks:
        risks.append("当前风险主要来自实时票价、余位和天气变化")
    return tuple(dict.fromkeys(risks))


def _build_assumptions(brief: TravelBrief, missing_keys: tuple[str, ...]) -> tuple[str, ...]:
    assumptions: list[str] = []
    if brief.origin and brief.destination:
        assumptions.append("默认采用最短时间、低中转的商旅路径")
    if brief.arrival_deadline:
        assumptions.append("默认将到达时限视为必须满足的硬约束")
    if brief.budget_policy or brief.reimbursement_requirements:
        assumptions.append("默认优先满足差标和报销要求")
    if "business_constraints" in missing_keys:
        assumptions.append("若未说明会议时间，暂按最保守的提前抵达策略处理")
    if not assumptions:
        assumptions.append("当前信息不足，先生成保守推荐假设")
    return tuple(dict.fromkeys(assumptions))


def _build_pending_checks(brief: TravelBrief, missing_keys: tuple[str, ...]) -> tuple[str, ...]:
    checks: list[str] = []
    if brief.origin and brief.destination:
        checks.append("实时航班余位与价格")
    if brief.destination:
        checks.append("目的地酒店可订性与实时价格")
    if brief.business_location:
        checks.append("从酒店到业务地点的通勤时间")
    if "travel_dates" in missing_keys:
        checks.append("出行日期和可接受时间窗口")
    if "budget_policy" in missing_keys:
        checks.append("差标与报销政策")
    return tuple(dict.fromkeys(checks))


def _build_next_actions(brief: TravelBrief, missing_keys: tuple[str, ...]) -> tuple[str, ...]:
    actions: list[str] = []
    if missing_keys:
        actions.extend(_question_from_key(key, brief) for key in missing_keys[:3])
    else:
        actions.append("进入实时核验阶段，确认航班和酒店")
    if brief.business_location:
        actions.append("按业务地点筛选酒店和通勤方式")
    return tuple(dict.fromkeys(action for action in actions if action))


def _build_alternatives(brief: TravelBrief) -> tuple[str, ...]:
    alternatives: list[str] = []
    route = _build_route_summary(brief)
    if brief.risk_tolerance and "低风险" in brief.risk_tolerance:
        alternatives.append(f"{route} 的提前一晚抵达方案")
    alternatives.append(f"{route} 的当天早班机方案")
    if brief.transport_preference and "高铁" in brief.transport_preference:
        alternatives.append(f"{route} 的高铁/动卧备选方案")
    return tuple(dict.fromkeys(alternatives))


def _question_from_key(key: str, brief: TravelBrief) -> str | None:
    if key == "origin_destination":
        if not brief.origin and not brief.destination:
            return "请补充出发地和目的地"
        if not brief.origin:
            return "请补充出发地"
        return "请补充目的地"
    if key == "travel_dates":
        return "请补充出行日期和时间窗口"
    if key == "business_constraints":
        return "请补充会议时间或到达硬约束"
    if key == "budget_policy":
        return "请补充预算、差标或报销要求"
    if key == "traveler_preferences":
        return "请补充交通或酒店偏好"
    if key == "risk_tolerance":
        return "请补充风险偏好"
    return None


def business_travel_phase_one_prompt_block() -> str:
    intake_lines = "\n".join(
        f"- {field.key} ({field.label}): {field.why_it_matters}"
        for field in PHASE_ONE_INTAKE_FIELDS
    )
    return f"""
商旅 Phase 1 对话协议：
- 目标：把模糊出行诉求转成准确、可比较、可执行的推荐简报。
- 交流策略：先识别硬约束，再收集偏好；缺少关键信息时，一次最多问 3 个最关键问题。
- 推荐策略：商务约束优先，其次是可靠性、总成本、时间效率和舒适度。
- 实时性：涉及价格、余票、班次、酒店库存、政策变化时，应先说明需要实时查询；如果工具可用则查询，如果不可用则明确标注为待核验。
- 边界：当前不能自动购票、预订、支付、取消或改签；只能整理待确认信息、推荐方向和后续执行步骤。

必须优先收集的信息：
{intake_lines}

推荐输出格式：
1. 已知信息
2. 仍需确认
3. 推荐方向
4. 备选方案
5. 风险和取舍
6. 下一步确认项
""".strip()


def _extract_brief_updates(query: str) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    city_pair = _extract_city_pair(query)
    if city_pair:
        updates["origin"], updates["destination"] = city_pair
    else:
        destination = _extract_destination(query)
        origin = _extract_origin(query)
        if origin:
            updates["origin"] = origin
        if destination:
            updates["destination"] = destination

    departure_date = _first_match(query, DATE_PATTERNS)
    if departure_date:
        updates["departure_date"] = departure_date

    return_date = _extract_return_date(query)
    if return_date:
        updates["return_date"] = return_date

    arrival_deadline = _extract_arrival_deadline(query)
    if arrival_deadline:
        updates["arrival_deadline"] = arrival_deadline

    business_constraints = _extract_business_constraints(query, arrival_deadline)
    if business_constraints:
        updates["business_constraints"] = business_constraints

    business_location = _extract_business_location(query)
    if business_location:
        updates["business_location"] = business_location

    budget_policy = _extract_budget_policy(query)
    if budget_policy:
        updates["budget_policy"] = budget_policy

    hotel_area = _extract_hotel_area(query)
    if hotel_area:
        updates["hotel_area"] = hotel_area

    transport_preference = _extract_transport_preference(query)
    if transport_preference:
        updates["transport_preference"] = transport_preference

    traveler_count = _extract_traveler_count(query)
    if traveler_count:
        updates["traveler_count"] = traveler_count

    risk_tolerance = _extract_risk_tolerance(query)
    if risk_tolerance:
        updates["risk_tolerance"] = risk_tolerance

    reimbursement_requirements = _extract_reimbursement_requirements(query)
    if reimbursement_requirements:
        updates["reimbursement_requirements"] = reimbursement_requirements

    notes = _extract_notes(query)
    if notes:
        updates["notes"] = notes

    return updates


def _extract_city_pair(query: str) -> tuple[str, str] | None:
    for origin in KNOWN_CITIES:
        for destination in KNOWN_CITIES:
            if origin == destination:
                continue
            patterns = (
                f"从{origin}到{destination}",
                f"从{origin}去{destination}",
                f"{origin}到{destination}",
                f"{origin}去{destination}",
            )
            if any(pattern in query for pattern in patterns):
                return origin, destination
    return None


def _extract_origin(query: str) -> str | None:
    for city in KNOWN_CITIES:
        if f"从{city}" in query or f"{city}出发" in query:
            return city
    return None


def _extract_destination(query: str) -> str | None:
    for city in KNOWN_CITIES:
        destination_patterns = (
            f"去{city}",
            f"到{city}",
            f"{city}出差",
            f"{city}开会",
            f"前往{city}",
        )
        if any(pattern in query for pattern in destination_patterns):
            return city
    return None


def _extract_return_date(query: str) -> str | None:
    match = re.search(r"(?:返程|回程|返回|回来)(?:时间)?(?:是|在|安排在)?([\u4e00-\u9fa5\d\-月日号周星期一二三四五六天上午下午晚上点:：]+)", query)
    if not match:
        return None
    return _clean_text(match.group(1))


def _extract_arrival_deadline(query: str) -> str | None:
    patterns = (
        r"(?:上午|中午|下午|晚上)?\s*\d{1,2}\s*(?:点|:|：)\s*\d{0,2}\s*前(?:到|抵达)?",
        r"(?:上午|中午|下午|晚上)?\s*\d{1,2}\s*点半?\s*前(?:到|抵达)?",
        r"\d{1,2}:\d{2}\s*前(?:到|抵达)?",
    )
    return _first_match(query, patterns)


def _extract_business_constraints(query: str, arrival_deadline: str | None) -> str | None:
    constraints: list[str] = []
    if arrival_deadline:
        constraints.append(f"需要{arrival_deadline}")
    for keyword in ("会议", "开会", "拜访客户", "客户拜访", "培训", "面试", "签约"):
        if keyword in query:
            constraints.append(keyword)
    if not constraints:
        return None
    return "；".join(dict.fromkeys(constraints))


def _extract_business_location(query: str) -> str | None:
    query = query.strip(" ，。,.")
    for clause in _location_clauses(query):
        short_location = re.sub(r"^(?:在|到|去|前往)", "", clause)
        short_location = re.sub(r"(?:附近|周边)$", "", short_location)
        if any(keyword in short_location for keyword in BUSINESS_LOCATION_KEYWORDS):
            cleaned = _clean_location_text(short_location)
            if cleaned:
                return cleaned

    if len(short_location) <= 30 and any(keyword in short_location for keyword in BUSINESS_LOCATION_KEYWORDS):
        return _clean_location_text(short_location)

    explicit_match = re.search(
        rf"(?:在|到|去|前往)([^，。,.；;]{{2,30}}?(?:{BUSINESS_LOCATION_SUFFIXES}))",
        query,
    )
    if explicit_match:
        return _clean_location_text(explicit_match.group(1))

    for keyword in BUSINESS_LOCATION_KEYWORDS:
        if keyword in query and len(query) <= 30:
            return _clean_location_text(query)

    return None


def _extract_budget_policy(query: str) -> str | None:
    patterns = (
        r"(?:预算|差标|标准|每晚|酒店|住宿)[^\d]{0,8}\d{2,5}\s*元?(?:以内|以下|左右)?",
        r"\d{2,5}\s*元?(?:以内|以下|左右)",
    )
    return _first_match(query, patterns)


def _extract_hotel_area(query: str) -> str | None:
    for clause in _location_clauses(query):
        if "酒店" in clause and re.search(r"\d{2,5}", clause):
            continue
        match = re.search(r"(?:住|酒店|住宿)(?:在|安排在)?([^，。,.；;]{2,20}?)(?:附近|周边)", clause)
        if match:
            return _clean_hotel_area(match.group(1))
        match = re.search(r"([^，。,.；;]{2,20}?)(?:附近|周边)(?:的)?(?:酒店|住宿)?", clause)
        if match and any(keyword in match.group(1) for keyword in BUSINESS_LOCATION_KEYWORDS):
            return _clean_hotel_area(match.group(1))

    patterns = (
        r"(?:住|酒店|住宿)(?:在|安排在)?([^，。,.；;]{2,20}?)(?:附近|周边)",
        r"([^，。,.；;]{2,20}?)(?:附近|周边)(?:的)?(?:酒店|住宿)",
    )
    match = _first_match(query, patterns)
    return _clean_hotel_area(match)


def _location_clauses(query: str) -> tuple[str, ...]:
    clauses = re.split(r"[，。,.；;\n]+", query)
    return tuple(_clean_text(clause) or "" for clause in clauses if _clean_text(clause))


def _clean_location_text(value: str | None) -> str | None:
    text = _clean_text(value)
    if not text:
        return None
    text = re.sub(r"^(?:在|到|去|前往)", "", text)
    text = re.sub(r"(?:附近|周边)$", "", text)
    text = _strip_travel_noise(text)
    if not text or re.search(r"\d{2,5}\s*元?", text):
        return None
    return text


def _clean_hotel_area(value: str | None) -> str | None:
    text = _clean_location_text(value)
    if not text:
        return None
    return f"{text}附近"


def _strip_travel_noise(text: str) -> str:
    text = re.sub(r"^(?:酒店|住宿|住)(?:在|安排在)?", "", text)
    text = re.sub(r"(?:早班机|航班|机票|高铁|火车|返程|回程|不用规划).*$", "", text)
    text = re.sub(r"(?:下午|上午|晚上|中午)?\d{1,2}(?:点|:|：)\d{0,2}.*$", "", text)
    text = re.sub(r"(?:预算|差标|酒店|住宿)?\d{2,5}\s*元?(?:以内|以下|左右)?.*$", "", text)
    return text.strip(" ，。,.；;")


def _extract_transport_preference(query: str) -> str | None:
    preferences: list[str] = []
    mapping = {
        "高铁": "高铁优先",
        "火车": "火车/高铁",
        "航班": "航班优先",
        "飞机": "航班优先",
        "机票": "航班优先",
        "经济舱": "经济舱",
        "直达": "直达优先",
    }
    for keyword, label in mapping.items():
        if keyword in query:
            preferences.append(label)
    if "越早到越好" in query or "越早越好" in query:
        preferences.append("尽早到达")
    if not preferences:
        return None
    return "；".join(dict.fromkeys(preferences))


def _extract_traveler_count(query: str) -> str | None:
    match = re.search(r"([一二两三四五六七八九十\d]+)\s*(?:个)?人", query)
    if not match:
        return None
    return f"{match.group(1)}人"


def _extract_risk_tolerance(query: str) -> str | None:
    preferences: list[str] = []
    if "低风险" in query or "稳" in query or "稳妥" in query:
        preferences.append("低风险/稳妥优先")
    if "准点" in query or "别迟到" in query or "不能迟到" in query:
        preferences.append("准点优先")
    if "可退改" in query or "退改" in query:
        preferences.append("可退改优先")
    if not preferences:
        return None
    return "；".join(dict.fromkeys(preferences))


def _extract_reimbursement_requirements(query: str) -> str | None:
    requirements: list[str] = []
    for keyword in ("报销", "发票", "抬头", "差标", "经济舱"):
        if keyword in query:
            requirements.append(keyword)
    if not requirements:
        return None
    return "；".join(dict.fromkeys(requirements))


def _extract_notes(query: str) -> tuple[str, ...]:
    notes: list[str] = []
    if "都可以" in query or "你推荐" in query or "最好的" in query:
        notes.append("用户授权助手在已知硬约束下选择推荐方案")
    if "硬性要求" in query:
        notes.append("用户表示硬性要求已提供，后续应基于现有约束给出推荐")
    return tuple(notes)


def _missing_keys(brief: TravelBrief) -> tuple[str, ...]:
    missing: list[str] = []
    if not brief.origin or not brief.destination:
        missing.append("origin_destination")
    if not brief.departure_date:
        missing.append("travel_dates")
    if not brief.business_constraints and not brief.arrival_deadline:
        missing.append("business_constraints")
    if not brief.budget_policy and not brief.reimbursement_requirements:
        missing.append("budget_policy")
    if not brief.transport_preference and not brief.hotel_area:
        missing.append("traveler_preferences")
    if not brief.risk_tolerance:
        missing.append("risk_tolerance")
    return tuple(missing)


def _suggested_questions(brief: TravelBrief, missing_keys: tuple[str, ...]) -> tuple[str, ...]:
    questions: list[str] = []
    for key in missing_keys:
        if key == "origin_destination":
            if not brief.origin and not brief.destination:
                questions.append("你从哪个城市出发，目的地是哪里？")
            elif not brief.origin:
                questions.append("你的出发城市是哪里？")
            else:
                questions.append("这次出差的目的地是哪里？")
        elif key == "travel_dates":
            questions.append("出行日期和可接受的出发/到达时间窗口是什么？")
        elif key == "business_constraints":
            questions.append("有没有必须到达的时间、会议地点或返程硬约束？")
        elif key == "budget_policy":
            questions.append("公司差标、预算或报销要求是什么？")
        elif key == "traveler_preferences":
            questions.append("交通方式和酒店位置有什么偏好吗？")
        elif key == "risk_tolerance":
            questions.append("这次更看重低价、效率，还是低风险和可退改？")
        if len(questions) == 3:
            break
    return tuple(questions)


def _readiness(brief: TravelBrief, missing_keys: tuple[str, ...]) -> str:
    has_core_route = bool(brief.origin and brief.destination)
    has_core_time = bool(brief.departure_date)
    has_business_anchor = bool(brief.arrival_deadline or brief.business_constraints)
    if has_core_route and has_core_time and has_business_anchor and len(missing_keys) <= 2:
        return "ready_for_preliminary_recommendation"
    if has_core_route and has_core_time:
        return "needs_business_constraints_before_recommendation"
    return "needs_clarification"


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


def _merge_notes(existing_notes: tuple[str, ...], new_notes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys((*existing_notes, *new_notes)))
