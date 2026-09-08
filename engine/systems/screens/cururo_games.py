import os

import pygame

from engine.project_paths import assets_dir
from .base import BaseScreen

RUTA = assets_dir("cururo_games.png")


class CururoGamesScreen(BaseScreen):
    def __init__(self, config=None):
        super().__init__(config)
        self._image = None
        self._cargar_imagen()

    def _cargar_imagen(self):
        if os.path.exists(RUTA):
            try:
                self._image = pygame.image.load(RUTA).convert_alpha()
            except pygame.error:
                pass

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
            return True
        return False

    def draw(self, surface):
        surface.fill((0, 0, 0))
        if self._image:
            rect = self._image.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2))
            surface.blit(self._image, rect)

