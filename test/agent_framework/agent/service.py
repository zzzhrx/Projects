from __future__ import annotations

from typing import Any

from agent_framework.core.capabilities import CapabilityRegistry, build_default_capability_registry
from agent_framework.core.models import AgentRequest, AgentResponse, AgentTrace
from agent_framework.core.settings import AgentSettings, load_settings
from agent_framework.domains.business_travel import build_travel_context
from agent_framework.domains.travel_planning import build_travel_plan_context
from agent_framework.prompts.system import build_system_prompt
from agent_framework.providers.graph import AgentGraphBuilder
from agent_framework.routing.base import BaseSkillRouter
from agent_framework.routing.default import KeywordSkillRouter
from agent_framework.skills.base import SkillRegistry
from agent_framework.skills.defaults import build_default_skill_registry
from agent_framework.tools.registry import ToolRegistry, build_default_tool_registry


class AdvancedAgentService:
    def __init__(
        self,
        settings: AgentSettings | None = None,
        capability_registry: CapabilityRegistry | None = None,
        tool_registry: ToolRegistry | None = None,
        skill_registry: SkillRegistry | None = None,
        skill_router: BaseSkillRouter | None = None,
    ) -> None:
        self.settings = settings or load_settings()
        self.capability_registry = capability_registry or build_default_capability_registry()
        self.tool_registry = tool_registry or build_default_tool_registry(self.settings.search)
        self.skill_registry = skill_registry or build_default_skill_registry()
        self.skill_router = skill_router or KeywordSkillRouter()
        self._agent_executor = None
        self._thread_contexts: dict[str, dict[str, Any]] = {}

    def run(self, request: AgentRequest) -> AgentResponse:
        base_context = self._merged_context(request)
        route_decision = self.skill_router.route(request.query, self.skill_registry, base_context)
        selected_skill = route_decision.skill
        request_context = self._build_request_context(
            request,
            selected_skill.name,
            base_context,
            route_decision,
        )
        config = {"configurable": {"thread_id": request.thread_id}}
        inputs = {
            "messages": [
                (
                    "system",
                    build_system_prompt(
                        now=request.requested_at,
                        capabilities=self.capability_registry,
                        tools=self.tool_registry,
                        skill=selected_skill,
                        route_decision=route_decision,
                        request_context=request_context,
                    ),
                ),
                ("user", request.query),
            ]
        }

        trace_messages: list[str] = []
        agent_executor = self._get_agent_executor()
        if request.show_process:
            final_answer = self._run_with_trace(
                agent_executor=agent_executor,
                inputs=inputs,
                config=config,
                trace_messages=trace_messages,
            )
        else:
            result = agent_executor.invoke(inputs, config)
            final_answer = self._extract_last_message(result["messages"])

        return AgentResponse(
            final_answer=final_answer,
            thread_id=request.thread_id,
            selected_skill=selected_skill.name,
            used_capabilities=self.capability_registry.ready_names(),
            trace=AgentTrace(
                selected_skill=selected_skill.name,
                route_confidence=route_decision.confidence,
                route_reason=route_decision.reason,
                matched_signals=route_decision.matched_signals,
                required_capabilities=route_decision.required_capabilities,
                clarification_focus=route_decision.clarification_focus,
            ),
            trace_messages=tuple(trace_messages),
            context=request_context,
        )

    def framework_overview(self) -> str:
        return "\n".join(
            [
                "Framework capabilities:",
                self.capability_registry.prompt_block(),
                "Registered skills:",
                self.skill_registry.prompt_block(),
                "Available tools:",
                self.tool_registry.prompt_block(),
            ]
        )

    def _get_agent_executor(self):
        if self._agent_executor is None:
            self._agent_executor = AgentGraphBuilder(
                model_settings=self.settings.model,
                tool_registry=self.tool_registry,
            ).build()
        return self._agent_executor

    def _merged_context(self, request: AgentRequest) -> dict[str, Any]:
        stored_context = self._thread_contexts.get(request.thread_id, {})
        return {**stored_context, **request.context}

    def _build_request_context(
        self,
        request: AgentRequest,
        selected_skill_name: str,
        base_context: dict[str, Any] | None = None,
        route_decision: Any | None = None,
    ) -> dict[str, Any]:
        request_context = dict(base_context or self._merged_context(request))

        if selected_skill_name == "business_travel_advisor":
            request_context = build_travel_context(request.query, request_context)
        elif selected_skill_name == "general_assistant" and self._should_build_leisure_context(
            request.query,
            request_context,
            route_decision,
        ):
            request_context = build_travel_plan_context(request.query, request_context)

        self._thread_contexts[request.thread_id] = request_context
        return request_context

    def _should_build_leisure_context(
        self,
        query: str,
        context: dict[str, Any],
        route_decision: Any | None = None,
    ) -> bool:
        if context.get("travel_mode") == "leisure":
            return True
        if isinstance(context.get("travel_plan_brief"), dict):
            return True
        if route_decision and getattr(route_decision.skill, "name", None) == "general_assistant":
            if "leisure_travel" in getattr(route_decision, "required_capabilities", ()):
                return True

        lowered_query = query.lower()
        leisure_keywords = (
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
        )
        return any(keyword in lowered_query for keyword in leisure_keywords)

    def _run_with_trace(
        self,
        agent_executor,
        inputs: dict[str, Any],
        config: dict[str, Any],
        trace_messages: list[str],
    ) -> str:
        final_answer = ""
        for event in agent_executor.stream(inputs, config, stream_mode="values"):
            message = event["messages"][-1]
            content = self._extract_message_content(getattr(message, "content", ""))
            if content:
                trace_messages.append(content)
                final_answer = content
        return final_answer

    def _extract_last_message(self, messages: list[Any]) -> str:
        if not messages:
            return ""
        return self._extract_message_content(getattr(messages[-1], "content", ""))

    def _extract_message_content(self, content: Any) -> str:
        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            collected: list[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text = str(item.get("text", "")).strip()
                else:
                    text = str(item).strip()
                if text:
                    collected.append(text)
            return "\n".join(collected).strip()

        return str(content).strip()
