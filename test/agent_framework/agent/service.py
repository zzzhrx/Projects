from __future__ import annotations

import logging
import time
from typing import Any
from zoneinfo import ZoneInfo

from agent_framework.agent.state import LRUContextStore, ThreadContextStore
from agent_framework.core.capabilities import CapabilityRegistry, build_default_capability_registry
from agent_framework.core.models import AgentRequest, AgentResponse, AgentTrace, ToolCallTrace
from agent_framework.core.settings import AgentSettings, load_settings
from agent_framework.prompts.system import build_system_prompt
from agent_framework.providers.graph import AgentGraphBuilder
from agent_framework.routing.base import BaseSkillRouter
from agent_framework.routing.default import KeywordSkillRouter
from agent_framework.skills.base import SkillRegistry
from agent_framework.skills.defaults import build_default_skill_registry
from agent_framework.tools.registry import ToolRegistry, build_default_tool_registry

logger = logging.getLogger(__name__)


class AdvancedAgentService:
    def __init__(
        self,
        settings: AgentSettings | None = None,
        capability_registry: CapabilityRegistry | None = None,
        tool_registry: ToolRegistry | None = None,
        skill_registry: SkillRegistry | None = None,
        skill_router: BaseSkillRouter | None = None,
        context_store: ThreadContextStore | None = None,
    ) -> None:
        self.settings = settings or load_settings()
        self.capability_registry = capability_registry or build_default_capability_registry()
        self.tool_registry = tool_registry or build_default_tool_registry(self.settings.search)
        self.skill_registry = skill_registry or build_default_skill_registry()
        self.skill_router = skill_router or KeywordSkillRouter()
        self._context_store = context_store or LRUContextStore()
        self._agent_executor = None

    # -- public API --

    def run(self, request: AgentRequest) -> AgentResponse:
        return self._execute(request, stream=request.show_process)

    async def arun(self, request: AgentRequest) -> AgentResponse:
        return await self._aexecute(request, stream=request.show_process)

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

    def build_request_context(
        self,
        request: AgentRequest,
        selected_skill_name: str,
        base_context: dict[str, Any] | None = None,
        route_decision: Any | None = None,
    ) -> dict[str, Any]:
        skill = self.skill_registry.get(selected_skill_name)
        request_context = dict(base_context or self._merged_context(request))

        if skill.context_builder:
            request_context = skill.context_builder(request.query, request_context)

        self._context_store.put(request.thread_id, request_context)
        return request_context

    # -- internal execution --

    def _execute(
        self,
        request: AgentRequest,
        stream: bool,
        async_mode: bool = False,
    ) -> AgentResponse:
        if async_mode:
            raise RuntimeError("Use AdvancedAgentService.arun() for async execution.")

        route_decision, selected_skill, request_context, config, inputs = self._prepare_invocation(request)
        trace_messages: list[str] = []
        tool_calls: tuple[ToolCallTrace, ...] = ()
        agent_executor = self._get_agent_executor()

        if stream:
            final_answer, tool_calls = self._run_with_trace(
                agent_executor=agent_executor,
                inputs=inputs,
                config=config,
                trace_messages=trace_messages,
            )
        else:
            result = agent_executor.invoke(inputs, config)
            final_answer = self._extract_last_message(result["messages"])
            tool_calls = self._extract_tool_calls(result["messages"])

        return self._build_response(
            final_answer=final_answer,
            request=request,
            selected_skill_name=selected_skill.name,
            route_decision=route_decision,
            request_context=request_context,
            trace_messages=trace_messages,
            tool_calls=tool_calls,
        )

    async def _aexecute(
        self,
        request: AgentRequest,
        stream: bool,
    ) -> AgentResponse:
        route_decision, selected_skill, request_context, config, inputs = self._prepare_invocation(request)
        trace_messages: list[str] = []
        agent_executor = self._get_agent_executor()

        if stream:
            raise NotImplementedError("Async streaming is not implemented yet.")

        result = await agent_executor.ainvoke(inputs, config)
        final_answer = self._extract_last_message(result["messages"])
        tool_calls = self._extract_tool_calls(result["messages"])

        return self._build_response(
            final_answer=final_answer,
            request=request,
            selected_skill_name=selected_skill.name,
            route_decision=route_decision,
            request_context=request_context,
            trace_messages=trace_messages,
            tool_calls=tool_calls,
        )

    def _prepare_invocation(
        self,
        request: AgentRequest,
    ) -> tuple[Any, Any, dict[str, Any], dict[str, Any], dict[str, Any]]:
        localized_now = self._localized_request_time(request.requested_at)
        base_context = self._merged_context(request)
        base_context.setdefault("current_date", localized_now.date().isoformat())
        base_context.setdefault("current_timezone", self.settings.runtime.timezone)
        route_decision = self.skill_router.route(request.query, self.skill_registry, base_context)
        selected_skill = route_decision.skill

        request_context = self.build_request_context(
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
                        now=localized_now,
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
        return route_decision, selected_skill, request_context, config, inputs

    def _build_response(
        self,
        *,
        final_answer: str,
        request: AgentRequest,
        selected_skill_name: str,
        route_decision: Any,
        request_context: dict[str, Any],
        trace_messages: list[str],
        tool_calls: tuple[ToolCallTrace, ...],
    ) -> AgentResponse:
        logger.info(
            "agent run complete skill=%s confidence=%.2f tool_calls=%d",
            selected_skill_name,
            route_decision.confidence,
            len(tool_calls),
        )

        return AgentResponse(
            final_answer=final_answer,
            thread_id=request.thread_id,
            selected_skill=selected_skill_name,
            used_capabilities=self.capability_registry.ready_names(),
            trace=AgentTrace(
                selected_skill=selected_skill_name,
                route_confidence=route_decision.confidence,
                route_reason=route_decision.reason,
                matched_signals=route_decision.matched_signals,
                required_capabilities=route_decision.required_capabilities,
                clarification_focus=route_decision.clarification_focus,
                tool_calls=tool_calls,
            ),
            trace_messages=tuple(trace_messages),
            context=request_context,
        )

    def _localized_request_time(self, requested_at):
        try:
            timezone = ZoneInfo(self.settings.runtime.timezone)
        except Exception:
            return requested_at

        if requested_at.tzinfo is None:
            return requested_at.replace(tzinfo=timezone)
        return requested_at.astimezone(timezone)

    def _get_agent_executor(self):
        if self._agent_executor is None:
            self._agent_executor = AgentGraphBuilder(
                model_settings=self.settings.model,
                tool_registry=self.tool_registry,
            ).build()
        return self._agent_executor

    def _merged_context(self, request: AgentRequest) -> dict[str, Any]:
        stored_context = self._context_store.get(request.thread_id)
        return {**stored_context, **request.context}

    # -- stream & message helpers --

    def _run_with_trace(
        self,
        agent_executor,
        inputs: dict[str, Any],
        config: dict[str, Any],
        trace_messages: list[str],
    ) -> tuple[str, tuple[ToolCallTrace, ...]]:
        final_answer = ""
        tool_calls: list[ToolCallTrace] = []
        pending: dict[str, float] = {}
        tool_index_by_id: dict[str, int] = {}
        for event in agent_executor.stream(inputs, config, stream_mode="values"):
            message = event["messages"][-1]
            tool_calls_attr = getattr(message, "tool_calls", None)
            if tool_calls_attr:
                for tc in tool_calls_attr:
                    tc_name, tc_args, tc_id = self._tool_call_parts(tc)
                    pending[tc_id or tc_name] = time.monotonic()
                    if tc_id:
                        tool_index_by_id[tc_id] = len(tool_calls)
                    tool_calls.append(ToolCallTrace(
                        name=tc_name,
                        args=tc_args,
                        status="running",
                    ))
            tc_name = getattr(message, "name", None)
            tc_id = getattr(message, "tool_call_id", None)
            if tc_name and tc_id is not None:
                start = pending.pop(tc_id, None)
                latency = (time.monotonic() - start) * 1000 if start else None
                result = self._extract_message_content(getattr(message, "content", ""))
                index = tool_index_by_id.get(tc_id)
                if index is None:
                    index = self._last_matching_tool_index(tool_calls, tc_name)
                if index is not None:
                    existing = tool_calls[index]
                    tool_calls[index] = ToolCallTrace(
                        name=existing.name,
                        args=existing.args,
                        result=result,
                        latency_ms=latency,
                        status="success",
                    )
            content = self._extract_message_content(getattr(message, "content", ""))
            if content:
                trace_messages.append(content)
                final_answer = content
        for index, tc in enumerate(tool_calls):
            if tc.status == "running":
                tool_calls[index] = ToolCallTrace(
                    name=tc.name, args=tc.args, status="timeout"
                )
        return final_answer, tuple(tool_calls)

    def _extract_tool_calls(self, messages: list[Any]) -> tuple[ToolCallTrace, ...]:
        tool_calls: list[ToolCallTrace] = []
        tool_index_by_id: dict[str, int] = {}
        for msg in messages:
            tool_calls_attr = getattr(msg, "tool_calls", None)
            if tool_calls_attr:
                for tc in tool_calls_attr:
                    tc_name, tc_args, tc_id = self._tool_call_parts(tc)
                    if tc_id:
                        tool_index_by_id[tc_id] = len(tool_calls)
                    tool_calls.append(ToolCallTrace(name=tc_name, args=tc_args, status="invoked"))

            tc_name = getattr(msg, "name", None)
            tc_id = getattr(msg, "tool_call_id", None)
            if tc_name and tc_id is not None:
                index = tool_index_by_id.get(tc_id)
                if index is None:
                    index = self._last_matching_tool_index(tool_calls, tc_name)
                if index is not None:
                    existing = tool_calls[index]
                    tool_calls[index] = ToolCallTrace(
                        name=existing.name,
                        args=existing.args,
                        result=self._extract_message_content(getattr(msg, "content", "")),
                        status="success",
                    )
        return tuple(tool_calls)

    def _tool_call_parts(self, tool_call: Any) -> tuple[str, dict[str, Any], str]:
        if isinstance(tool_call, dict):
            name = tool_call.get("name", "unknown")
            args = tool_call.get("args", {})
            call_id = tool_call.get("id", "")
        else:
            name = getattr(tool_call, "name", "unknown")
            args = getattr(tool_call, "args", {})
            call_id = getattr(tool_call, "id", "")
        return str(name), args if isinstance(args, dict) else {}, str(call_id or "")

    def _last_matching_tool_index(self, tool_calls: list[ToolCallTrace], tool_name: str) -> int | None:
        for index in range(len(tool_calls) - 1, -1, -1):
            if tool_calls[index].name == tool_name:
                return index
        return None

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
