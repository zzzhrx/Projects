from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class AgentRequest:
    query: str
    thread_id: str
    show_process: bool = False
    requested_at: datetime = field(default_factory=datetime.now)
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentTrace:
    selected_skill: str
    route_confidence: float
    route_reason: str
    matched_signals: tuple[str, ...] = ()
    required_capabilities: tuple[str, ...] = ()
    clarification_focus: tuple[str, ...] = ()


@dataclass(frozen=True)
class AgentResponse:
    final_answer: str
    thread_id: str
    selected_skill: str
    used_capabilities: tuple[str, ...]
    trace: AgentTrace | None = None
    trace_messages: tuple[str, ...] = ()
    context: dict[str, Any] = field(default_factory=dict)
