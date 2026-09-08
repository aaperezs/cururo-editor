import json
import os
import pygame

from engine.project_paths import data_dir
from .recoleccion import RecoleccionMiniJuego
from .timing import TimingMiniJuego
from .puzzle import PuzzleMiniJuego

_RUTA = data_dir("minijuegos.json")


def load_minigames():
    if not os.path.exists(_RUTA):
        return {}
    with open(_RUTA, "r", encoding="utf-8") as f:
        return json.load(f)


class MiniJuegoManager:
    def __init__(self, estado):
        self.estado = estado
        self._minigames_data = load_minigames()
        self._activo = None
        self._resultado = {}

    def iniciar(self, minijuego_id):
        cfg = self._minigames_data.get(minijuego_id)
        if not cfg:
            return False
        tipo = cfg.get("tipo", "")
        if tipo == "recoleccion":
            self._activo = RecoleccionMiniJuego(cfg)
        elif tipo == "timing":
            self._activo = TimingMiniJuego(cfg)
        elif tipo == "puzzle":
            self._activo = PuzzleMiniJuego(cfg)
        else:
            return False
        self._resultado = {}
        self._activo.iniciar()
        return True

    @property
    def activo(self):
        return self._activo is not None

    def handle_event(self, event):
        if self._activo:
            return self._activo.handle_event(event)
        return False

    def actualizar(self, dt_ms):
        if not self._activo:
            return False
        terminado = self._activo.actualizar(dt_ms)
        if terminado:
            self._resultado = self._activo.get_resultado()
            self._activo = None
            return True
        return False

    def dibujar(self, surface):
        if self._activo:
            self._activo.dibujar(surface)

    def get_resultado(self):
        return self._resultado

