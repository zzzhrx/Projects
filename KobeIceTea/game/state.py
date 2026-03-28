from __future__ import annotations

from dataclasses import dataclass, field


GridPosition = tuple[int, int]


@dataclass
class GameState:
    player_position: GridPosition
    rewards: set[GridPosition] = field(default_factory=set)
    steps_taken: int = 0
    score: int = 0
