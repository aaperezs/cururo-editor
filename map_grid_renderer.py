"""Map grid renderer — sprite cache, tile rendering, selection overlay, ghosts.

Extracted from MapEditorPanel._draw_grid to separate rendering from the main panel.
"""

from __future__ import annotations

import pygame

from editor.elements import is_multi_tile_element, get_element
from editor.sprite_registry import get_sprite_registry
from editor.common.sprite_loader import obtener as obtener_sprite
from editor.tileset import Tileset
from editor.project import get_current_project


class GridRenderer:
    """Manages sprite/tileset caches and renders the map grid."""

    def __init__(self) -> None:
        self.sprite_cache: dict[str, pygame.Surface | tuple | None] = {}
        self.sprite_cache_zoom: float = -1.0
        self.tileset_cache: dict[int, pygame.Surface | None] = {}
        self.tileset_cache_zoom: float = -1.0

    def draw(
        self,
        surface: pygame.Surface,
        tab,
        tile_size: int,
        vp_x: int,
        vp_y: int,
        vp_w: int,
        vp_h: int,
        scroll_x: int,
        scroll_y: int,
        show_grid: bool,
        selected_sprite_id: str | None,
        selected_pos: tuple[int, int] | None,
        drag_source: tuple | None,
        zoom: float,
    ) -> None:
        """Draw the entire map grid onto the surface."""
        if not tab:
            return

        ts = tile_size
        gr = pygame.Rect(vp_x, vp_y, vp_w, vp_h)

        if self.sprite_cache_zoom != zoom:
            self.sprite_cache = {}
            self.sprite_cache_zoom = zoom
        if self.tileset_cache_zoom != zoom:
            self.tileset_cache = {}
            self.tileset_cache_zoom = zoom

        tileset = None
        p = get_current_project()
        if p and p.tileset:
            tileset = Tileset.load_from_project(p)

        for z in tab.layer_order:
            ls = tab.layers.get(z)
            if not ls or not ls.visible or ls.opacity <= 0:
                continue

            alpha = max(1, int(ls.opacity * 2.55))

            for (gx, gy), sprite_id in ls.grid.items():
                sx = vp_x + gx * ts - scroll_x
                sy = vp_y + gy * ts - scroll_y
                if sx + ts < gr.x or sx > gr.x + gr.w or sy + ts < gr.y or sy > gr.y + gr.h:
                    continue

                if sprite_id.startswith("tileset:") and tileset:
                    try:
                        tile_index = int(sprite_id.split(":", 1)[1])
                        if tile_index not in self.tileset_cache:
                            tile_surf = tileset.get_tile(tile_index)
                            if tile_surf:
                                scaled = pygame.transform.scale(tile_surf, (ts, ts))
                                if alpha < 255:
                                    scaled.set_alpha(alpha)
                                self.tileset_cache[tile_index] = scaled
                            else:
                                self.tileset_cache[tile_index] = None
                        cached = self.tileset_cache.get(tile_index)
                        if isinstance(cached, pygame.Surface):
                            surface.blit(cached, (sx, sy))
                        continue
                    except (ValueError, IndexError):
                        pass

                if sprite_id not in self.sprite_cache:
                    actual_sprite_id = sprite_id
                    from editor.elements import _ELEMENTOS_DATA
                    el = _ELEMENTOS_DATA.get(sprite_id)
                    if el:
                        esp_id = el.get("sprite_id")
                        if esp_id:
                            actual_sprite_id = esp_id
                    info = get_sprite_registry().get(actual_sprite_id)
                    if not info:
                        info = get_sprite_registry().get(sprite_id)
                    sprite_file = info["file"] if info else None
                    sprite = obtener_sprite(sprite_file) if sprite_file else None
                    if sprite:
                        scaled = pygame.transform.scale(sprite, (ts, ts))
                        if alpha < 255:
                            scaled.set_alpha(alpha)
                        self.sprite_cache[sprite_id] = scaled
                    else:
                        col = (80, 80, 90) if info else (50, 55, 60)
                        self.sprite_cache[sprite_id] = col

                cached = self.sprite_cache.get(sprite_id)
                if isinstance(cached, pygame.Surface):
                    surface.blit(cached, (sx, sy))
                elif cached is not None:
                    if alpha < 255:
                        s = pygame.Surface((ts, ts), pygame.SRCALPHA)
                        s.fill((*cached, alpha))
                        surface.blit(s, (sx, sy))
                    else:
                        pygame.draw.rect(surface, cached, (sx, sy, ts, ts))

                if show_grid and ts >= 8:
                    pygame.draw.rect(surface, (45, 48, 52), (sx, sy, ts, ts), 1)

        # Selection overlay
        if selected_pos:
            sx = vp_x + selected_pos[0] * ts - scroll_x
            sy = vp_y + selected_pos[1] * ts - scroll_y
            pygame.draw.rect(surface, (255, 200, 50), (sx, sy, ts, ts), 3)

        # Multi-tile ghost preview
        if selected_sprite_id and is_multi_tile_element(selected_sprite_id):
            mx, my = pygame.mouse.get_pos()
            if gr.collidepoint(mx, my):
                el = get_element(selected_sprite_id)
                props = el.get("properties", {}) if el else {}
                rows = props.get("tile_rows", 1)
                cols = props.get("tile_cols", 1)
                ghost_gx = (mx - vp_x + scroll_x) // ts
                ghost_gy = (my - vp_y + scroll_y) // ts
                for r in range(rows):
                    for c in range(cols):
                        gsx = vp_x + (ghost_gx + c) * ts - scroll_x
                        gsy = vp_y + (ghost_gy + r) * ts - scroll_y
                        pygame.draw.rect(surface, (100, 200, 255, 80), (gsx, gsy, ts, ts), 2)

        # Drag ghost
        if drag_source is not None:
            mx, my = pygame.mouse.get_pos()
            if gr.collidepoint(mx, my):
                ghost_gx = (mx - vp_x + scroll_x) // ts
                ghost_gy = (my - vp_y + scroll_y) // ts
                gsx = vp_x + ghost_gx * ts - scroll_x
                gsy = vp_y + ghost_gy * ts - scroll_y
                ghost_sid = drag_source[2]
                ghost_surf = None
                if ghost_sid.startswith("tileset:") and tileset:
                    try:
                        tile_index = int(ghost_sid.split(":", 1)[1])
                        if tile_index in self.tileset_cache:
                            ghost_surf = self.tileset_cache[tile_index]
                        else:
                            tile_surf = tileset.get_tile(tile_index)
                            if tile_surf:
                                ghost_surf = pygame.transform.scale(tile_surf, (ts, ts))
                                self.tileset_cache[tile_index] = ghost_surf
                    except (ValueError, IndexError):
                        pass
                elif ghost_sid in self.sprite_cache:
                    ghost_surf = self.sprite_cache[ghost_sid]
                if isinstance(ghost_surf, pygame.Surface):
                    ghost_surf.set_alpha(100)
                    surface.blit(ghost_surf, (gsx, gsy))
                    ghost_surf.set_alpha(255)
                pygame.draw.rect(surface, (100, 200, 255), (gsx, gsy, ts, ts), 2)
