from __future__ import annotations

from dataclasses import dataclass
import random

from game.config import GameConfig
from game.rules import (
    ACTION_SPACE,
    apply_action,
    nearest_reward_position,
    spawn_reward,
    steps_until_next_spawn,
)
from game.state import GameState


StateKey = tuple[int, int, int, int, int, int]


@dataclass(frozen=True)
class EncodedState:
    player_x: int
    player_y: int
    target_dx: int
    target_dy: int
    steps_until_spawn: int
    reward_count_bucket: int

    def as_tuple(self) -> StateKey:
        return (
            self.player_x,
            self.player_y,
            self.target_dx,
            self.target_dy,
            self.steps_until_spawn,
            self.reward_count_bucket,
        )

    def describe(self) -> str:
        return (
            f"p=({self.player_x},{self.player_y})  "
            f"target=({self.target_dx},{self.target_dy})  "
            f"spawn={self.steps_until_spawn}  "
            f"bucket={self.reward_count_bucket}"
        )


class GridWorldEnv:
    def __init__(self, config: GameConfig, seed: int | None = None) -> None:
        self.config = config
        self.random = random.Random(
            config.rl_random_seed if seed is None else seed
        )
        self.state = GameState(player_position=config.start_position)
        self.decision_count = 0

    def reset(self) -> StateKey:
        self.state = GameState(player_position=self.config.start_position)
        self.decision_count = 0
        spawn_reward(self.state, self.config.grid_size, self.random)
        return self.observe()

    def observe(self) -> StateKey:
        return encode_state(self.config, self.state).as_tuple()

    def step(self, action: str) -> tuple[StateKey, float, bool, dict[str, int | bool]]:
        transition = apply_action(
            self.state,
            action,
            self.config.grid_size,
            self.config.reward_spawn_interval,
            self.random,
        )
        self.decision_count += 1
        reward = self._calculate_reward(transition)
        done = self.decision_count >= self.config.rl_max_actions_per_episode
        info = {
            "moved": transition.moved,
            "invalid_move": transition.invalid_move,
            "collected_reward": transition.collected_reward,
            "score": self.state.score,
            "steps_taken": self.state.steps_taken,
            "decision_count": self.decision_count,
        }
        return self.observe(), reward, done, info

    def _calculate_reward(self, transition) -> float:
        reward = 0.0

        if transition.invalid_move:
            reward += self.config.rl_invalid_move_penalty
        else:
            reward += self.config.rl_step_penalty

        if transition.collected_reward:
            reward += self.config.rl_collect_reward_bonus

        if (
            transition.previous_distance is not None
            and transition.new_distance is not None
        ):
            if transition.new_distance < transition.previous_distance:
                reward += self.config.rl_move_closer_bonus
            elif transition.new_distance > transition.previous_distance:
                reward += self.config.rl_move_away_penalty

        return reward


def encode_state(config: GameConfig, state: GameState) -> EncodedState:
    player_x, player_y = state.player_position
    nearest_reward = nearest_reward_position(state.player_position, state.rewards)

    target_dx = 0
    target_dy = 0
    if nearest_reward is not None:
        target_dx = nearest_reward[0] - player_x
        target_dy = nearest_reward[1] - player_y

    reward_count_bucket = min(
        len(state.rewards),
        config.rl_reward_count_bucket_cap,
    )

    return EncodedState(
        player_x=player_x,
        player_y=player_y,
        target_dx=target_dx,
        target_dy=target_dy,
        steps_until_spawn=steps_until_next_spawn(
            state.steps_taken,
            config.reward_spawn_interval,
        ),
        reward_count_bucket=reward_count_bucket,
    )


def action_values_to_text(action_values: dict[str, float]) -> str:
    short_names = {
        "UP": "U",
        "DOWN": "D",
        "LEFT": "L",
        "RIGHT": "R",
    }
    return "  ".join(
        f"{short_names[action]}:{action_values[action]:.2f}"
        for action in ACTION_SPACE
    )
