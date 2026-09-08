import pygame
import os

_sprite_cache = {}
_assets_dir = "assets"


def set_assets_dir(path):
    global _assets_dir
    _assets_dir = path


def _get_sprite_path(sprite_id):
    base = _assets_dir if os.path.isabs(_assets_dir) else os.path.join(os.getcwd(), _assets_dir)
    return os.path.join(base, f"{sprite_id}.png")


def load_sprite(sprite_id):
    if sprite_id in _sprite_cache:
        return _sprite_cache[sprite_id]

    path = _get_sprite_path(sprite_id)
    if os.path.exists(path):
        surf = pygame.image.load(path).convert_alpha()
        _sprite_cache[sprite_id] = surf
        return surf
    return None


def sprite_size(sprite_id):
    sprite = load_sprite(sprite_id)
    if sprite:
        return (sprite.get_width(), sprite.get_height())
    return (0, 0)


def draw_sprite(surface, sprite_id, x, y):
    sprite = load_sprite(sprite_id)
    if sprite:
        surface.blit(sprite, (x, y))


def draw_sprite_scaled(surface, sprite_id, x, y, w, h):
    sprite = load_sprite(sprite_id)
    if sprite:
        scaled = pygame.transform.scale(sprite, (w, h))
        surface.blit(scaled, (x, y))


def draw_rect(surface, color, rect, width=0):
    pygame.draw.rect(surface, color, rect, width)


def draw_rect_filled(surface, color, rect):
    pygame.draw.rect(surface, color, rect)


def draw_circle(surface, color, center, radius, width=0):
    pygame.draw.circle(surface, color, center, radius, width)


def draw_line(surface, color, start, end, width=1):
    pygame.draw.line(surface, color, start, end, width)


def draw_text(surface, text, x, y, color=(255, 255, 255), size=16, font_name=None):
    font = pygame.font.SysFont(font_name or "Arial", size)
    rendered = font.render(text, True, color)
    surface.blit(rendered, (x, y))


def draw_text_centered(surface, text, cx, cy, color=(255, 255, 255), size=16, font_name=None):
    font = pygame.font.SysFont(font_name or "Arial", size)
    rendered = font.render(text, True, color)
    rect = rendered.get_rect(center=(cx, cy))
    surface.blit(rendered, rect)


def text_width(text, size=16, font_name=None):
    font = pygame.font.SysFont(font_name or "Arial", size)
    return font.size(text)[0]


def text_height(size=16, font_name=None):
    font = pygame.font.SysFont(font_name or "Arial", size)
    return font.get_height()


def clear_sprite_cache():
    _sprite_cache.clear()
