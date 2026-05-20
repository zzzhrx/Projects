from __future__ import annotations

from typing import Any

from agent_framework.routing.base import BaseSkillRouter, RouteDecision
from agent_framework.routing.default import KeywordSkillRouter
from agent_framework.skills.base import SkillRegistry, SkillSpec


class LLMFallbackRouter(BaseSkillRouter):
    """Hybrid router: tries keyword routing first, falls back to LLM intent classification.

    Keyword routing is fast and deterministic. When confidence is below the
    threshold, a lightweight LLM call classifies the query into one of the
    known skills and returns a RouteDecision with explicit reasoning.
    """

    def __init__(
        self,
        keyword_router: KeywordSkillRouter | None = None,
        threshold: float = 0.55,
        cache_size: int = 128,
    ) -> None:
        self._keyword = keyword_router or KeywordSkillRouter()
        self._threshold = threshold
        self._cache: dict[tuple[str, str], RouteDecision] = {}
        self._cache_max = cache_size

    def route(
        self,
        query: str,
        skill_registry: SkillRegistry,
        context: dict[str, Any] | None = None,
    ) -> RouteDecision:
        normalized = query.strip()
        cache_key = self._cache_key(normalized, context)
        if cache_key in self._cache:
            return self._cache[cache_key]

        keyword_decision = self._keyword.route(normalized, skill_registry, context)
        if keyword_decision.confidence >= self._threshold:
            self._cache_put(cache_key, keyword_decision)
            return keyword_decision

        try:
            llm_decision = self._llm_classify(normalized, skill_registry, keyword_decision)
        except Exception:
            llm_decision = keyword_decision

        self._cache_put(cache_key, llm_decision)
        return llm_decision

    def _cache_put(self, cache_key: tuple[str, str], decision: RouteDecision) -> None:
        if len(self._cache) >= self._cache_max:
            self._cache.pop(next(iter(self._cache)))
        self._cache[cache_key] = decision

    def _cache_key(self, query: str, context: dict[str, Any] | None) -> tuple[str, str]:
        if not context:
            return query, "no_context"

        travel_brief = context.get("travel_brief")
        if isinstance(travel_brief, dict):
            context_marker = "|".join(
                str(travel_brief.get(key) or "")
                for key in ("origin", "destination", "departure_date", "business_location")
            )
            return query, f"business:{context_marker}"

        travel_plan_brief = context.get("travel_plan_brief")
        if isinstance(travel_plan_brief, dict):
            context_marker = "|".join(
                str(travel_plan_brief.get(key) or "")
                for key in ("origin", "destination", "departure_date")
            )
            return query, f"leisure:{context_marker}"

        return query, str(context.get("travel_mode") or "generic")

    def _llm_classify(
        self, query: str, skill_registry: SkillRegistry, fallback: RouteDecision
    ) -> RouteDecision:
        skills_list = "\n".join(
            f"- {s.name}: {s.description}" for s in skill_registry.all()
        )
        prompt = (
            "Classify the user query into exactly one skill from the list below. "
            "Return a JSON object with keys: skill (one of the listed names), "
            "confidence (0.0-1.0), reason (one short sentence in Chinese), "
            "and required_capabilities (list of strings).\n\n"
            f"Skills:\n{skills_list}\n\n"
            f"Query: {query}\n\n"
            "Respond with only the JSON object, no markdown, no explanation."
        )

        from agent_framework.core.settings import ModelSettings, load_settings
        from agent_framework.providers.llm import build_llm

        base_model_settings = load_settings().model
        route_settings = ModelSettings(
            provider=base_model_settings.provider,
            model=base_model_settings.model,
            api_base=base_model_settings.api_base,
            api_key=base_model_settings.api_key,
            temperature=0,
        )
        llm = build_llm(route_settings)
        response = llm.invoke(prompt)
        raw = self._message_content_as_text(response.content if hasattr(response, "content") else response)

        import json
        import re

        json_match = re.search(r"\{[^{}]*\}", raw)
        if not json_match:
            return fallback

        data = json.loads(json_match.group(0))
        skill_name = data.get("skill", fallback.skill.name)
        confidence = float(data.get("confidence", fallback.confidence))
        reason = data.get("reason", fallback.reason)
        capabilities = tuple(data.get("required_capabilities", fallback.required_capabilities))

        if not skill_registry.has(skill_name):
            return fallback

        return RouteDecision(
            skill=skill_registry.get(skill_name),
            confidence=min(max(confidence, 0.0), 1.0),
            reason=reason,
            required_capabilities=capabilities,
            matched_signals=("llm_fallback",),
            clarification_focus=fallback.clarification_focus,
        )

    def _message_content_as_text(self, content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
                else:
                    parts.append(str(item))
            return "\n".join(part for part in parts if part)
        return str(content)
