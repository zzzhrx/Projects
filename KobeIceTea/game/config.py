from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import settings


@dataclass(frozen=True)
class GameConfig:
    root_dir: Path
    assets_dir: Path
    window_caption: str
    grid_size: int
    cell_size: int
    board_padding: int
    hud_height: int
    fps: int
    reward_spawn_interval: int
    background_color: tuple[int, int, int]
    panel_color: tuple[int, int, int]
    border_color: tuple[int, int, int]
    cell_light_color: tuple[int, int, int]
    cell_dark_color: tuple[int, int, int]
    text_color: tuple[int, int, int]
    accent_color: tuple[int, int, int]
    player_asset_name: str
    reward_asset_name: str
    player_sprite_scale: float
    reward_sprite_scale: float
    auto_train_rl: bool
    guide_mode_default: bool
    autoplay_default: bool
    autoplay_delay_ms: int
    rl_random_seed: int
    rl_episodes: int
    rl_max_actions_per_episode: int
    rl_evaluation_episodes: int
    rl_learning_rate: float
    rl_discount_factor: float
    rl_epsilon_start: float
    rl_epsilon_min: float
    rl_epsilon_decay: float
    rl_reward_count_bucket_cap: int
    rl_step_penalty: float
    rl_invalid_move_penalty: float
    rl_collect_reward_bonus: float
    rl_move_closer_bonus: float
    rl_move_away_penalty: float

    @property
    def board_pixel_size(self) -> int:
        return self.grid_size * self.cell_size

    @property
    def window_width(self) -> int:
        return (self.board_padding * 2) + self.board_pixel_size

    @property
    def window_height(self) -> int:
        return (self.board_padding * 2) + self.board_pixel_size + self.hud_height

    @property
    def start_position(self) -> tuple[int, int]:
        center = self.grid_size // 2
        return center, center


def load_config() -> GameConfig:
    return GameConfig(
        root_dir=settings.ROOT_DIR,
        assets_dir=settings.ASSETS_DIR,
        window_caption=settings.WINDOW_CAPTION,
        grid_size=settings.GRID_SIZE,
        cell_size=settings.CELL_SIZE,
        board_padding=settings.BOARD_PADDING,
        hud_height=settings.HUD_HEIGHT,
        fps=settings.FPS,
        reward_spawn_interval=settings.REWARD_SPAWN_INTERVAL,
        background_color=settings.BACKGROUND_COLOR,
        panel_color=settings.PANEL_COLOR,
        border_color=settings.BORDER_COLOR,
        cell_light_color=settings.CELL_LIGHT_COLOR,
        cell_dark_color=settings.CELL_DARK_COLOR,
        text_color=settings.TEXT_COLOR,
        accent_color=settings.ACCENT_COLOR,
        player_asset_name=settings.PLAYER_ASSET_NAME,
        reward_asset_name=settings.REWARD_ASSET_NAME,
        player_sprite_scale=settings.PLAYER_SPRITE_SCALE,
        reward_sprite_scale=settings.REWARD_SPRITE_SCALE,
        auto_train_rl=settings.AUTO_TRAIN_RL,
        guide_mode_default=settings.GUIDE_MODE_DEFAULT,
        autoplay_default=settings.AUTOPLAY_DEFAULT,
        autoplay_delay_ms=settings.AUTOPLAY_DELAY_MS,
        rl_random_seed=settings.RL_RANDOM_SEED,
        rl_episodes=settings.RL_EPISODES,
        rl_max_actions_per_episode=settings.RL_MAX_ACTIONS_PER_EPISODE,
        rl_evaluation_episodes=settings.RL_EVALUATION_EPISODES,
        rl_learning_rate=settings.RL_LEARNING_RATE,
        rl_discount_factor=settings.RL_DISCOUNT_FACTOR,
        rl_epsilon_start=settings.RL_EPSILON_START,
        rl_epsilon_min=settings.RL_EPSILON_MIN,
        rl_epsilon_decay=settings.RL_EPSILON_DECAY,
        rl_reward_count_bucket_cap=settings.RL_REWARD_COUNT_BUCKET_CAP,
        rl_step_penalty=settings.RL_STEP_PENALTY,
        rl_invalid_move_penalty=settings.RL_INVALID_MOVE_PENALTY,
        rl_collect_reward_bonus=settings.RL_COLLECT_REWARD_BONUS,
        rl_move_closer_bonus=settings.RL_MOVE_CLOSER_BONUS,
        rl_move_away_penalty=settings.RL_MOVE_AWAY_PENALTY,
    )
