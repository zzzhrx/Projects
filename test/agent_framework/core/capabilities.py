from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CapabilityStatus(str, Enum):
    READY = "ready"
    RESERVED = "reserved"


@dataclass(frozen=True)
class CapabilitySpec:
    name: str
    description: str
    status: CapabilityStatus
    design_goal: str


class CapabilityRegistry:
    def __init__(self, specs: list[CapabilitySpec]) -> None:
        self._specs = specs

    @property
    def specs(self) -> tuple[CapabilitySpec, ...]:
        return tuple(self._specs)

    def ready_names(self) -> tuple[str, ...]:
        return tuple(spec.name for spec in self._specs if spec.status == CapabilityStatus.READY)

    def prompt_block(self) -> str:
        return "\n".join(
            f"- {spec.name} [{spec.status.value}]: {spec.description} Goal: {spec.design_goal}"
            for spec in self._specs
        )


def build_default_capability_registry() -> CapabilityRegistry:
    return CapabilityRegistry(
        specs=[
            CapabilitySpec(
                name="dialogue",
                description="Handle multi-turn user conversations and retain thread memory.",
                status=CapabilityStatus.READY,
                design_goal="Serve as the front door for user intent understanding.",
            ),
            CapabilitySpec(
                name="web_search",
                description="Fetch live information from the web when freshness matters.",
                status=CapabilityStatus.READY,
                design_goal="Ground answers in current information instead of guessing.",
            ),
            CapabilitySpec(
                name="realtime_map",
                description="Resolve addresses, routes, hotels, and local POI data through AMap.",
                status=CapabilityStatus.READY,
                design_goal="Provide real-world travel grounding from map and POI data.",
            ),
            CapabilitySpec(
                name="advisor",
                description="Turn travel context, constraints, and research into grounded recommendations.",
                status=CapabilityStatus.READY,
                design_goal="Separate recommendation quality from raw retrieval and casual conversation.",
            ),
            CapabilitySpec(
                name="leisure_travel",
                description="Plan tourist and leisure trips with destination, dates, budget, and hotel preferences.",
                status=CapabilityStatus.READY,
                design_goal="Keep vacation planning distinct from business travel planning.",
            ),
            CapabilitySpec(
                name="planner",
                description="Convert a chosen direction into a structured, execution-ready plan.",
                status=CapabilityStatus.READY,
                design_goal="Prepare future booking and execution APIs with clear inputs, assumptions, and approvals.",
            ),
            CapabilitySpec(
                name="executor",
                description="Use tools and workflows to implement approved actions.",
                status=CapabilityStatus.RESERVED,
                design_goal="Eventually deliver autonomous task completion.",
            ),
        ]
    )
