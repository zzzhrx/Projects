from __future__ import annotations

import random

import pygame

from .assets import SpriteBundle, load_sprites
from .config import GameConfig, load_config
from .rules import (
    ACTION_DOWN,
    ACTION_LEFT,
    ACTION_RIGHT,
    ACTION_TO_ARROW,
    ACTION_TO_DELTA,
    ACTION_TO_LABEL,
    ACTION_UP,
    apply_action,
    is_inside_grid,
    spawn_reward,
)
from .state import GameState, GridPosition
from rl.environment import action_values_to_text
from rl.q_learning import TrainedAgent, train_agent


class GridGame:
    def __init__(self, config: GameConfig | None = None) -> None:
        pygame.init()
        self.config = config or load_config()
        self.screen = pygame.display.set_mode(
            (self.config.window_width, self.config.window_height)
        )
        pygame.display.set_caption(self.config.window_caption)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 34)
        self.small_font = pygame.font.Font(None, 26)
        self.tiny_font = pygame.font.Font(None, 22)
        self.micro_font = pygame.font.Font(None, 20)
        self.random = random.Random()
        self.board_rect = pygame.Rect(
            self.config.board_padding,
            self.config.board_padding,
            self.config.board_pixel_size,
            self.config.board_pixel_size,
        )
        self.hud_rect = pygame.Rect(
            self.config.board_padding,
            self.board_rect.bottom + 16,
            self.config.board_pixel_size,
            self.config.hud_height,
        )
        self.key_to_action = {
            pygame.K_UP: ACTION_UP,
            pygame.K_DOWN: ACTION_DOWN,
            pygame.K_LEFT: ACTION_LEFT,
            pygame.K_RIGHT: ACTION_RIGHT,
            pygame.K_w: ACTION_UP,
            pygame.K_s: ACTION_DOWN,
            pygame.K_a: ACTION_LEFT,
            pygame.K_d: ACTION_RIGHT,
        }
        self.guide_mode = self.config.guide_mode_default
        self.autoplay_enabled = self.config.autoplay_default
        self.last_autoplay_tick = 0
        self.trained_agent: TrainedAgent | None = None
        self.rl_status_text = "RL not trained yet."
        self.sprites: SpriteBundle = load_sprites(self.config)
        self.state = self._build_initial_state()

        if self.config.auto_train_rl:
            self._train_rl_agent()

    def _build_initial_state(self) -> GameState:
        state = GameState(player_position=self.config.start_position)
        spawn_reward(state, self.config.grid_size, self.random)
        return state

    def run(self) -> None:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    continue

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                        continue

                    if event.key == pygame.K_r:
                        self.state = self._build_initial_state()
                        continue

                    if event.key == pygame.K_g:
                        self.guide_mode = not self.guide_mode
                        continue

                    if event.key == pygame.K_p:
                        if self.trained_agent is None:
                            self._train_rl_agent()
                        self.autoplay_enabled = not self.autoplay_enabled
                        self.last_autoplay_tick = pygame.time.get_ticks()
                        continue

                    if event.key == pygame.K_t:
                        self._train_rl_agent()
                        continue

                    self._handle_move(event.key)

            self._update_autoplay()
            self._draw()
            self.clock.tick(self.config.fps)

        pygame.quit()

    def _train_rl_agent(self) -> None:
        self.rl_status_text = "Training RL agent..."
        self.trained_agent = train_agent(self.config)
        self.rl_status_text = self.trained_agent.summary.compact_text()
        self.last_autoplay_tick = pygame.time.get_ticks()

    def _update_autoplay(self) -> None:
        if not self.autoplay_enabled or self.trained_agent is None:
            return

        now = pygame.time.get_ticks()
        if now - self.last_autoplay_tick < self.config.autoplay_delay_ms:
            return

        action = self.trained_agent.suggest_action(self.state)
        self._handle_action(action)
        self.last_autoplay_tick = now

    def _handle_move(self, key: int) -> None:
        if key not in self.key_to_action:
            return

        self._handle_action(self.key_to_action[key])

    def _handle_action(self, action: str) -> None:
        apply_action(
            self.state,
            action,
            self.config.grid_size,
            self.config.reward_spawn_interval,
            self.random,
        )

    def _draw(self) -> None:
        self.screen.fill(self.config.background_color)
        self._draw_board()
        self._draw_rewards()
        self._draw_guide_overlay()
        self._draw_player()
        self._draw_hud()
        pygame.display.flip()

    def _draw_board(self) -> None:
        pygame.draw.rect(
            self.screen,
            self.config.panel_color,
            self.board_rect,
            border_radius=12,
        )

        for y in range(self.config.grid_size):
            for x in range(self.config.grid_size):
                cell_rect = self._cell_rect((x, y))
                cell_color = (
                    self.config.cell_light_color
                    if (x + y) % 2 == 0
                    else self.config.cell_dark_color
                )
                pygame.draw.rect(self.screen, cell_color, cell_rect, border_radius=10)
                pygame.draw.rect(
                    self.screen,
                    self.config.border_color,
                    cell_rect,
                    width=1,
                    border_radius=10,
                )

        pygame.draw.rect(
            self.screen,
            self.config.border_color,
            self.board_rect,
            width=3,
            border_radius=12,
        )

    def _draw_rewards(self) -> None:
        for reward_position in self.state.rewards:
            self._draw_sprite_at(self.sprites.reward, reward_position)

    def _draw_player(self) -> None:
        self._draw_sprite_at(self.sprites.player, self.state.player_position)

    def _draw_guide_overlay(self) -> None:
        if not self.guide_mode or self.trained_agent is None:
            return

        suggested_action = self.trained_agent.suggest_action(self.state)
        delta_x, delta_y = ACTION_TO_DELTA[suggested_action]
        player_x, player_y = self.state.player_position
        next_position = (player_x + delta_x, player_y + delta_y)
        if not is_inside_grid(next_position, self.config.grid_size):
            return

        cell_rect = self._cell_rect(next_position)
        pygame.draw.rect(
            self.screen,
            self.config.accent_color,
            cell_rect,
            width=4,
            border_radius=10,
        )

    def _draw_sprite_at(self, sprite: pygame.Surface, position: GridPosition) -> None:
        cell_rect = self._cell_rect(position)
        sprite_rect = sprite.get_rect(center=cell_rect.center)
        self.screen.blit(sprite, sprite_rect)

    def _draw_hud(self) -> None:
        pygame.draw.rect(
            self.screen,
            self.config.panel_color,
            self.hud_rect,
            border_radius=12,
        )
        pygame.draw.rect(
            self.screen,
            self.config.border_color,
            self.hud_rect,
            width=2,
            border_radius=12,
        )

        status_text = (
            f"Steps: {self.state.steps_taken}    "
            f"Score: {self.state.score}    "
            f"Rewards On Board: {len(self.state.rewards)}"
        )
        gameplay_text = (
            f"Move: Arrow Keys / WASD    "
            f"Spawn: every {self.config.reward_spawn_interval} valid steps"
        )
        control_text = (
            f"G guide={'ON' if self.guide_mode else 'OFF'}    "
            f"P autoplay={'ON' if self.autoplay_enabled else 'OFF'}    "
            f"T retrain    R restart    Esc quit"
        )
        asset_text = (
            f"Assets: {self.config.player_asset_name} / {self.config.reward_asset_name}"
        )

        self.screen.blit(
            self.font.render(status_text, True, self.config.text_color),
            (self.hud_rect.left + 18, self.hud_rect.top + 14),
        )
        self.screen.blit(
            self.small_font.render(gameplay_text, True, self.config.text_color),
            (self.hud_rect.left + 18, self.hud_rect.top + 48),
        )
        self.screen.blit(
            self.tiny_font.render(control_text, True, self.config.accent_color),
            (self.hud_rect.left + 18, self.hud_rect.top + 76),
        )
        self.screen.blit(
            self.tiny_font.render(asset_text, True, self.config.text_color),
            (self.hud_rect.left + 18, self.hud_rect.top + 98),
        )

        rl_lines = self._build_rl_lines()
        base_y = self.hud_rect.top + 128
        for line_index, line in enumerate(rl_lines):
            self.screen.blit(
                self.micro_font.render(line, True, self.config.text_color),
                (self.hud_rect.left + 18, base_y + (line_index * 22)),
            )

    def _build_rl_lines(self) -> list[str]:
        if self.trained_agent is None:
            return [
                "RL status: not trained.",
                "Press T to train an agent that suggests actions with Q-learning.",
            ]

        encoded_state = self.trained_agent.encoded_state(self.state)
        suggested_action = self.trained_agent.suggest_action(self.state)
        q_values = self.trained_agent.q_values_for_state(self.state)

        return [
            f"RL summary: {self.rl_status_text}",
            f"Encoded state: {encoded_state.describe()}",
            (
                "Suggested action: "
                f"{ACTION_TO_LABEL[suggested_action]} {ACTION_TO_ARROW[suggested_action]}"
            ),
            f"Q-values: {action_values_to_text(q_values)}",
        ]

    def _cell_rect(self, position: GridPosition) -> pygame.Rect:
        x, y = position
        return pygame.Rect(
            self.board_rect.left + (x * self.config.cell_size) + 4,
            self.board_rect.top + (y * self.config.cell_size) + 4,
            self.config.cell_size - 8,
            self.config.cell_size - 8,
        )


def main() -> None:
    GridGame().run()
