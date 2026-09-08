import os

import pygame

from engine.project_paths import assets_dir
from .base import BaseScreen


class ImagenScreen(BaseScreen):
    """Pantalla genérica que muestra una imagen desde assets/<screen_id>.png"""

    def __init__(self, screen_id, config=None):
        super().__init__(config)
        self._screen_id = screen_id
        self._image = None
        self._cargar_imagen()

    def _cargar_imagen(self):
        ruta = assets_dir(f"{self._screen_id}.png")
        if os.path.exists(ruta):
            try:
                self._image = pygame.image.load(ruta).convert_alpha()
            except pygame.error:
                pass

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
            return True
        return False

    def draw(self, surface):
        surface.fill((0, 0, 0))
        if self._image:
            rect = self._image.get_rect(
                center=(surface.get_width() // 2, surface.get_height() // 2)
            )
            surface.blit(self._image, rect)

