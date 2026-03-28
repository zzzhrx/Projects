from __future__ import annotations

from dataclasses import dataclass
import random

from .state import GameState, GridPosition


ACTION_UP = "UP"
ACTION_DOWN = "DOWN"
ACTION_LEFT = "LEFT"
ACTION_RIGHT = "RIGHT"
ACTION_SPACE = (ACTION_UP, ACTION_DOWN, ACTION_LEFT, ACTION_RIGHT)

ACTION_TO_DELTA: dict[str, tuple[int, int]] = {
    ACTION_UP: (0, -1),
    ACTION_DOWN: (0, 1),
    ACTION_LEFT: (-1, 0),
    ACTION_RIGHT: (1, 0),
}

ACTION_TO_LABEL: dict[str, str] = {
    ACTION_UP: "Up",
    ACTION_DOWN: "Down",
    ACTION_LEFT: "Left",
    ACTION_RIGHT: "Right",
}

ACTION_TO_ARROW: dict[str, str] = {
    ACTION_UP: "↑",
    ACTION_DOWN: "↓",
    ACTION_LEFT: "←",
    ACTION_RIGHT: "→",
}


@dataclass(frozen=True)
class MoveResult:
    moved: bool
    invalid_move: bool
    collected_reward: bool
    spawned_reward: bool
    previous_distance: int | None
    new_distance: int | None


def is_inside_grid(position: GridPosition, grid_size: int) -> bool:
    x, y = position
    return 0 <= x < grid_size and 0 <= y < grid_size


def valid_actions_for_position(
    player_position: GridPosition,
    grid_size: int,
) -> tuple[str, ...]:
    valid_actions: list[str] = []
    for action, (delta_x, delta_y) in ACTION_TO_DELTA.items():
        next_position = (player_position[0] + delta_x, player_position[1] + delta_y)
        if is_inside_grid(next_position, grid_size):
            valid_actions.append(action)
    return tuple(valid_actions)


def manhattan_distance(a: GridPosition, b: GridPosition) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def available_reward_positions(
    state: GameState,
    grid_size: int,
) -> list[GridPosition]:
    positions: list[GridPosition] = []
    for y in range(grid_size):
        for x in range(grid_size):
            position = (x, y)
            if position == state.player_position:
                continue
            if position in state.rewards:
                continue
            positions.append(position)
    return positions


def nearest_reward_position(
    player_position: GridPosition,
    rewards: set[GridPosition],
) -> GridPosition | None:
    if not rewards:
        return None

    return min(
        rewards,
        key=lambda reward_position: (
            manhattan_distance(player_position, reward_position),
            reward_position[1],
            reward_position[0],
        ),
    )


def nearest_reward_distance(
    player_position: GridPosition,
    rewards: set[GridPosition],
) -> int | None:
    nearest = nearest_reward_position(player_position, rewards)
    if nearest is None:
        return None
    return manhattan_distance(player_position, nearest)


def spawn_reward(state: GameState, grid_size: int, rng: random.Random) -> bool:
    choices = available_reward_positions(state, grid_size)
    if not choices:
        return False

    state.rewards.add(rng.choice(choices))
    return True


def steps_until_next_spawn(steps_taken: int, reward_spawn_interval: int) -> int:
    if reward_spawn_interval <= 0:
        return 0

    remainder = steps_taken % reward_spawn_interval
    if remainder == 0:
        return reward_spawn_interval
    return reward_spawn_interval - remainder


def apply_action(
    state: GameState,
    action: str,
    grid_size: int,
    reward_spawn_interval: int,
    rng: random.Random,
) -> MoveResult:
    if action not in ACTION_TO_DELTA:
        raise ValueError(f"Unknown action: {action}")

    previous_distance = nearest_reward_distance(state.player_position, state.rewards)
    delta_x, delta_y = ACTION_TO_DELTA[action]
    current_x, current_y = state.player_position
    new_position = (current_x + delta_x, current_y + delta_y)

    if not is_inside_grid(new_position, grid_size):
        return MoveResult(
            moved=False,
            invalid_move=True,
            collected_reward=False,
            spawned_reward=False,
            previous_distance=previous_distance,
            new_distance=previous_distance,
        )

    state.player_position = new_position
    state.steps_taken += 1

    collected_reward = False
    if new_position in state.rewards:
        state.rewards.remove(new_position)
        state.score += 1
        collected_reward = True

    spawned_reward = False
    if (
        reward_spawn_interval > 0
        and state.steps_taken % reward_spawn_interval == 0
    ):
        spawned_reward = spawn_reward(state, grid_size, rng)

    new_distance = nearest_reward_distance(state.player_position, state.rewards)
    return MoveResult(
        moved=True,
        invalid_move=False,
        collected_reward=collected_reward,
        spawned_reward=spawned_reward,
        previous_distance=previous_distance,
        new_distance=new_distance,
    )
