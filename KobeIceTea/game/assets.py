from __future__ import annotations

from dataclasses import dataclass

import pygame

from .config import GameConfig


@dataclass(frozen=True)
class SpriteBundle:
    player: pygame.Surface
    reward: pygame.Surface


def load_sprites(config: GameConfig) -> SpriteBundle:
    player_size = _sprite_size(config.cell_size, config.player_sprite_scale)
    reward_size = _sprite_size(config.cell_size, config.reward_sprite_scale)

    return SpriteBundle(
        player=_load_sprite(
            config.assets_dir / config.player_asset_name,
            player_size,
            _build_player_placeholder(player_size),
        ),
        reward=_load_sprite(
            config.assets_dir / config.reward_asset_name,
            reward_size,
            _build_reward_placeholder(reward_size),
        ),
    )


def _sprite_size(cell_size: int, scale: float) -> int:
    return max(1, int(cell_size * scale))


def _load_sprite(path, sprite_size: int, fallback: pygame.Surface) -> pygame.Surface:
    if not path.exists():
        return fallback

    try:
        image = pygame.image.load(path.as_posix()).convert_alpha()
    except pygame.error:
        return fallback

    return _scale_to_fit(image, sprite_size)


def _scale_to_fit(surface: pygame.Surface, sprite_size: int) -> pygame.Surface:
    width, height = surface.get_size()
    if width <= 0 or height <= 0:
        return pygame.transform.smoothscale(surface, (sprite_size, sprite_size))

    scale = min(sprite_size / width, sprite_size / height)
    scaled_size = (
        max(1, int(width * scale)),
        max(1, int(height * scale)),
    )
    return pygame.transform.smoothscale(surface, scaled_size)


def _build_player_placeholder(size: int) -> pygame.Surface:
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2
    radius = (size // 2) - 4

    pygame.draw.circle(surface, (49, 96, 126), (center, center), radius)
    pygame.draw.circle(surface, (232, 244, 248), (center, center), radius - 10, width=4)
    pygame.draw.polygon(
        surface,
        (255, 238, 197),
        [
            (center, 10),
            (center + 10, center + 5),
            (center, center - 2),
            (center - 10, center + 5),
        ],
    )
    return surface


def _build_reward_placeholder(size: int) -> pygame.Surface:
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2
    outer = 8

    pygame.draw.polygon(
        surface,
        (224, 163, 45),
        [
            (center, outer),
            (size - outer, center),
            (center, size - outer),
            (outer, center),
        ],
    )
    pygame.draw.polygon(
        surface,
        (255, 228, 152),
        [
            (center, outer + 10),
            (size - outer - 10, center),
            (center, size - outer - 10),
            (outer + 10, center),
        ],
        width=4,
    )
    return surface
