from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import random

from game.config import GameConfig
from game.rules import ACTION_SPACE, valid_actions_for_position
from game.state import GameState

from .environment import GridWorldEnv, StateKey, encode_state


QTable = dict[StateKey, dict[str, float]]


@dataclass(frozen=True)
class TrainingSummary:
    episodes: int
    average_training_reward: float
    average_training_score: float
    best_training_score: int
    evaluation_average_score: float
    evaluation_average_reward: float
    final_epsilon: float

    def compact_text(self) -> str:
        return (
            f"train={self.average_training_score:.2f}  "
            f"eval={self.evaluation_average_score:.2f}  "
            f"best={self.best_training_score}  "
            f"eps={self.final_epsilon:.3f}"
        )


@dataclass(frozen=True)
class TrainedAgent:
    config: GameConfig
    agent: "QLearningAgent"
    summary: TrainingSummary

    def suggest_action(self, state: GameState) -> str:
        encoded_state = encode_state(self.config, state).as_tuple()
        valid_actions = valid_actions_for_position(
            state.player_position,
            self.config.grid_size,
        )
        return self.agent.best_action(encoded_state, allowed_actions=valid_actions)

    def q_values_for_state(self, state: GameState) -> dict[str, float]:
        encoded_state = encode_state(self.config, state).as_tuple()
        return self.agent.q_values_for_state(encoded_state)

    def encoded_state(self, state: GameState):
        return encode_state(self.config, state)


class QLearningAgent:
    def __init__(self, config: GameConfig) -> None:
        self.config = config
        self.learning_rate = config.rl_learning_rate
        self.discount_factor = config.rl_discount_factor
        self.epsilon = config.rl_epsilon_start
        self.epsilon_min = config.rl_epsilon_min
        self.epsilon_decay = config.rl_epsilon_decay
        self.random = random.Random(config.rl_random_seed)
        self.q_table: defaultdict[StateKey, dict[str, float]] = defaultdict(
            self._new_action_map
        )

    def _new_action_map(self) -> dict[str, float]:
        return {action: 0.0 for action in ACTION_SPACE}

    def choose_action(self, state: StateKey) -> str:
        if self.random.random() < self.epsilon:
            return self.random.choice(ACTION_SPACE)
        return self.best_action(state, deterministic=False)

    def best_action(
        self,
        state: StateKey,
        deterministic: bool = True,
        allowed_actions: tuple[str, ...] | None = None,
    ) -> str:
        action_values = self.q_table[state]
        candidate_actions = allowed_actions or ACTION_SPACE
        best_value = max(action_values[action] for action in candidate_actions)
        best_actions = [
            action
            for action in candidate_actions
            if action_values[action] == best_value
        ]

        if deterministic:
            return best_actions[0]
        return self.random.choice(best_actions)

    def update(
        self,
        state: StateKey,
        action: str,
        reward: float,
        next_state: StateKey,
        done: bool,
    ) -> None:
        current_q = self.q_table[state][action]
        next_best_q = 0.0 if done else max(self.q_table[next_state].values())
        td_target = reward + (self.discount_factor * next_best_q)
        td_error = td_target - current_q
        self.q_table[state][action] = current_q + (self.learning_rate * td_error)

    def decay_epsilon(self) -> None:
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def q_values_for_state(self, state: StateKey) -> dict[str, float]:
        return dict(self.q_table[state])


def train_agent(config: GameConfig) -> TrainedAgent:
    env = GridWorldEnv(config, seed=config.rl_random_seed)
    agent = QLearningAgent(config)

    episode_rewards: list[float] = []
    episode_scores: list[int] = []
    best_score = 0

    for _episode_index in range(config.rl_episodes):
        state = env.reset()
        done = False
        total_reward = 0.0

        while not done:
            action = agent.choose_action(state)
            next_state, reward, done, info = env.step(action)
            agent.update(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward

        episode_rewards.append(total_reward)
        episode_scores.append(env.state.score)
        best_score = max(best_score, env.state.score)
        agent.decay_epsilon()

    evaluation_average_score, evaluation_average_reward = evaluate_agent(config, agent)
    summary = TrainingSummary(
        episodes=config.rl_episodes,
        average_training_reward=_average(episode_rewards),
        average_training_score=_average(episode_scores),
        best_training_score=best_score,
        evaluation_average_score=evaluation_average_score,
        evaluation_average_reward=evaluation_average_reward,
        final_epsilon=agent.epsilon,
    )
    return TrainedAgent(config=config, agent=agent, summary=summary)


def evaluate_agent(
    config: GameConfig,
    agent: QLearningAgent,
) -> tuple[float, float]:
    env = GridWorldEnv(config, seed=config.rl_random_seed + 1)
    scores: list[int] = []
    rewards: list[float] = []

    for _episode_index in range(config.rl_evaluation_episodes):
        state = env.reset()
        done = False
        total_reward = 0.0

        while not done:
            action = agent.best_action(state)
            next_state, reward, done, info = env.step(action)
            state = next_state
            total_reward += reward

        scores.append(env.state.score)
        rewards.append(total_reward)

    return _average(scores), _average(rewards)


def _average(values: list[float] | list[int]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)
