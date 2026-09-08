import os
import pygame

from engine.project_paths import assets_dir
from .base import BaseScreen


class TituloScreen(BaseScreen):
    def __init__(self, config=None, title_data=None, display_size=None):
        super().__init__(config)
        self.title_data = title_data or {}
        self.display_size = display_size or (800, 600)
        self._bg = None
        self._load_bg()
        self._seleccion = 0
        self._opciones = ["nueva_partida", "cargar_partida"]
        self._tiene_saves = self._verificar_saves()

    def _load_bg(self):
        bg_id = self.title_data.get("fondo", "")
        if bg_id:
            for ext in (".png", ".jpg", ".jpeg"):
                path = assets_dir(f"{bg_id}{ext}")
                if os.path.exists(path):
                    img = pygame.image.load(path).convert()
                    self._bg = pygame.transform.scale(img, self.display_size)
                    return
        self._bg = None

    def _verificar_saves(self):
        try:
            from engine.repositories.repositorio_saves import RepositorioSaves
            saves = RepositorioSaves()
            return len(saves.listar_slots()) > 0
        except Exception:
            return False

    def draw(self, surface):
        dw, dh = self.display_size
        if self._bg:
            surface.blit(self._bg, (0, 0))
        else:
            surface.fill((10, 12, 16))
        titulo = self.title_data.get("titulo", "")
        subtitulo = self.title_data.get("subtitulo", "")
        if titulo:
            font_l = pygame.font.SysFont("Georgia", 48, bold=True)
            ts = font_l.render(titulo, True, (220, 200, 160))
            surface.blit(ts, ((dw - ts.get_width()) // 2, dh // 3 - 20))
        if subtitulo:
            font_s = pygame.font.SysFont("Georgia", 22)
            ss = font_s.render(subtitulo, True, (180, 180, 190))
            surface.blit(ss, ((dw - ss.get_width()) // 2, dh // 2 + 10))

        # Opciones de menú
        font_menu = pygame.font.SysFont("Georgia", 22)
        opciones_texto = {
            "nueva_partida": "Nueva Partida",
            "cargar_partida": "Cargar Partida",
        }
        y_start = dh // 2 + 60
        for i, op_id in enumerate(self._opciones):
            if op_id == "cargar_partida" and not self._tiene_saves:
                continue
            texto = opciones_texto.get(op_id, op_id)
            es_sel = (i == self._seleccion)
            color = (220, 200, 160) if es_sel else (120, 130, 140)
            prefijo = "▶ " if es_sel else "  "
            ts = font_menu.render(f"{prefijo}{texto}", True, color)
            surface.blit(ts, ((dw - ts.get_width()) // 2, y_start))
            y_start += 40

        hint = pygame.font.SysFont("Arial", 16).render(
            "[↑↓] seleccionar   [ENTER] aceptar", True, (100, 110, 120)
        )
        surface.blit(hint, ((dw - hint.get_width()) // 2, dh - 40))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self._seleccion = max(0, self._seleccion - 1)
                return False
            if event.key == pygame.K_DOWN:
                self._seleccion = min(len(self._opciones) - 1, self._seleccion + 1)
                return False
            if event.key == pygame.K_RETURN:
                op = self._opciones[self._seleccion]
                if op == "cargar_partida" and not self._tiene_saves:
                    return False
                return True
            if event.key in (pygame.K_r, pygame.K_o):
                self._abrir_ajustes()
        return False

    def get_seleccion(self):
        return self._opciones[self._seleccion]

    def _abrir_ajustes(self):
        from .settings import SettingsScreen
        SettingsScreen(self.config, self.display_size).run()

