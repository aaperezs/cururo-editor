import os
import pygame
from editor.sprite_registry import (
    get_sprite_registry, get_multi_tile_info, get_multi_tile_tiles,
    is_multi_tile, compute_multi_dims, sprite_registry_reload
)


class SpriteService:
    """Application service for sprite operations."""

    @staticmethod
    def get_registry():
        return get_sprite_registry()

    @staticmethod
    def get_sprite(sprite_id):
        return get_sprite_registry().get(sprite_id)

    @staticmethod
    def get_multi_tile(sprite_id):
        return get_multi_tile_info(sprite_id)

    @staticmethod
    def get_multi_tiles(sprite_id):
        return get_multi_tile_tiles(sprite_id)

    @staticmethod
    def is_multi(sprite_id):
        return is_multi_tile(sprite_id)

    @staticmethod
    def get_dims(sprite_id):
        return compute_multi_dims(sprite_id)

    @staticmethod
    def load_surface(sprite_id):
        info = get_sprite_registry().get(sprite_id)
        if info and info.get("file"):
            from editor.common.sprite_loader import obtener as load_sprite
            return load_sprite(info["file"])
        return None

    @staticmethod
    def reload():
        sprite_registry_reload()

    @staticmethod
    def get_display_name(sprite_id):
        info = get_sprite_registry().get(sprite_id)
        return info.get("display", sprite_id) if info else sprite_id


sprite_service = SpriteService()
