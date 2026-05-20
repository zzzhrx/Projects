from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SkillSpec:
    name: str
    description: str
    instruction_block: str
    target_outcome: str
    suggested_tools: tuple[str, ...] = ()
    context_builder: Callable[[str, dict[str, Any]], dict[str, Any]] | None = field(
        default=None, repr=False
    )


class SkillRegistry:
    def __init__(self, skills: list[SkillSpec], default_skill: str) -> None:
        self._skills = {skill.name: skill for skill in skills}
        self._default_skill = default_skill

    def all(self) -> tuple[SkillSpec, ...]:
        return tuple(self._skills.values())

    def get(self, name: str) -> SkillSpec:
        return self._skills[name]

    def has(self, name: str) -> bool:
        return name in self._skills

    def default(self) -> SkillSpec:
        return self.get(self._default_skill)

    def prompt_block(self) -> str:
        return "\n".join(
            f"- {skill.name}: {skill.description} Goal: {skill.target_outcome}"
            for skill in self.all()
        )
