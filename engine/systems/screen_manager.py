import json
import os
import sys

import pygame

from engine.project_paths import data_dir
from engine.display import present as _display_present, get_buffer as _display_buffer
from .screens.cururo_games import CururoGamesScreen
from .screens.imagen import ImagenScreen
from .screens.text import TextScreen
from .screens.titulo import TituloScreen

SCREEN_REGISTRY = {
    "cururo_games": CururoGamesScreen,
}


def registrar_pantalla(screen_id, cls):
    SCREEN_REGISTRY[screen_id] = cls


class ScreenManager:
    def __init__(self, display_surf, screens_cfg):
        self.display = display_surf
        self.items = screens_cfg.get("items", ["cururo_games"])
        self.screen_configs = screens_cfg.get("config", {})
        self.enabled = screens_cfg.get("enabled", True)
        self._scenes_cache = None

    def _load_scenes_title(self):
        scenes_path = data_dir("scenes.json")
        if os.path.exists(scenes_path):
            try:
                with open(scenes_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("titulo", {})
            except Exception:
                pass
        return {}

    def run(self):
        if not self.enabled:
            return
        clock = pygame.time.Clock()
        for screen_id in self.items:
            cfg = self.screen_configs.get(screen_id, {})
            if not cfg.get("enabled", True):
                continue
            screen = self._crear(screen_id, cfg)
            if screen is None:
                continue
            self._ejecutar(screen, clock)

    def _crear(self, screen_id, cfg):
        cls = SCREEN_REGISTRY.get(screen_id)
        if cls:
            return cls(cfg)
        if screen_id == "title":
            title_data = self._load_scenes_title()
            if title_data.get("enabled"):
                return TituloScreen(cfg, title_data, self.display.get_size())
        try:
            texto = TextScreen(screen_id, cfg)
            if texto._lineas:
                return texto
        except Exception:
            pass
        try:
            return ImagenScreen(screen_id, cfg)
        except Exception:
            return None

    def _ejecutar(self, screen, clock):
        done = False
        while not done:
            dt = clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if screen.handle_event(event):
                    done = True
            if screen.update(dt):
                done = True
            screen.draw(_display_buffer())
            _display_present()

