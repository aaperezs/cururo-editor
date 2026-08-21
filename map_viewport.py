"""Viewport del editor de mapas — zoom, scroll, coordenadas screen↔grid."""

from __future__ import annotations

import pygame


class MapViewport:
    """Gestiona transformaciones de coordenadas y estado visual del mapa."""

    def __init__(self, base_tile_size: int = 20) -> None:
        self._base_tile_size: int = base_tile_size
        self.zoom: float = 1.0
        self.scroll_x: int = 0
        self.scroll_y: int = 0
        self.show_grid: bool = True

    @property
    def tile_size(self) -> int:
        """Tamaño de tile en píxeles (aplicando zoom)."""
        return max(4, int(self._base_tile_size * self.zoom))

    def set_base_tile_size(self, ts: int) -> None:
        self._base_tile_size = ts

    def zoom_in(self) -> None:
        self.zoom = min(4.0, self.zoom + 0.25)

    def zoom_out(self) -> None:
        self.zoom = max(0.25, self.zoom - 0.25)

    def zoom_label(self) -> str:
        return f"{int(self.zoom * 100)}%"

    def screen_to_grid(self, mx: int, my: int, viewport_rect: pygame.Rect) -> tuple[int, int]:
        """Convierte coordenadas de pantalla a coordenadas de grilla."""
        ts = self.tile_size
        gx = (mx - viewport_rect.x + self.scroll_x) // ts
        gy = (my - viewport_rect.y + self.scroll_y) // ts
        return (gx, gy)

    def grid_to_screen(self, gx: int, gy: int, viewport_rect: pygame.Rect) -> tuple[int, int]:
        """Convierte coordenadas de grilla a coordenadas de pantalla (esquina superior-izquierda)."""
        ts = self.tile_size
        sx = gx * ts - self.scroll_x + viewport_rect.x
        sy = gy * ts - self.scroll_y + viewport_rect.y
        return (sx, sy)

    def content_size(self, tab: object) -> tuple[int, int]:
        """Devuelve (ancho, alto) total del contenido del mapa en píxeles."""
        ts = self.tile_size
        ancho = max((ls.ancho for ls in tab.layers.values()), default=0)  # type: ignore[union-attr]
        alto = max((ls.alto for ls in tab.layers.values()), default=0)  # type: ignore[union-attr]
        return (ancho * ts, alto * ts)

    def update_content_size(self, tab: object, scroll_area: object) -> None:
        """Actualiza el tamaño del contenido en el ScrollableArea."""
        w, h = self.content_size(tab)
        scroll_area.set_content(w, h)  # type: ignore[union-attr]
