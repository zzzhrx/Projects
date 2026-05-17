from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from agent_framework.skills.base import SkillRegistry, SkillSpec


@dataclass(frozen=True)
class RouteDecision:
    skill: SkillSpec
    confidence: float
    reason: str
    matched_signals: tuple[str, ...] = ()
    required_capabilities: tuple[str, ...] = ()
    clarification_focus: tuple[str, ...] = ()


class BaseSkillRouter(ABC):
    @abstractmethod
    def route(
        self,
        query: str,
        skill_registry: SkillRegistry,
        context: dict[str, Any] | None = None,
    ) -> RouteDecision:
        raise NotImplementedError
