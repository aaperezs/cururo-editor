import json
import os
import pygame

LOCALES_DIR = os.path.join(os.path.dirname(__file__), "locales")


class I18n:
    _instancia = None

    def __init__(self, lang="es"):
        self.lang = lang
        self._data = {}
        self._fuentes = {}
        self._cargar()
        I18n._instancia = self

    def _cargar(self):
        ruta = os.path.join(LOCALES_DIR, f"{self.lang}.json")
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        except FileNotFoundError:
            self._data = {}

    def t(self, key):
        return self._data.get(key, key)

    def set_lang(self, lang):
        self.lang = lang
        self._cargar()

    def fuente(self, tam, bold=False):
        clave = (tam, bold)
        if clave not in self._fuentes:
            for nombre in ["Segoe UI", "Arial", None]:
                try:
                    f = pygame.font.SysFont(nombre, tam, bold=bold)
                    if f and f.render("A", True, (0, 0, 0)).get_width() > 0:
                        self._fuentes[clave] = f
                        break
                except Exception:
                    continue
            else:
                self._fuentes[clave] = pygame.font.Font(None, tam)
        return self._fuentes[clave]

    @classmethod
    def instancia(cls):
        return cls._instancia
