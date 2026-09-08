import json
import os

import pygame
from engine.configs import *
from engine.project_paths import data_dir

RUTA = data_dir("text_screens.json")


class TextScreenPlayer:
    def __init__(self):
        self._datos = {}
        self._screen_id = ""
        self._titulo = ""
        self._lineas = []
        self._linea_actual = 0
        self._char_idx = 0
        self.activo = False
        self._cargar()

    def _cargar(self):
        try:
            with open(RUTA, "r", encoding="utf-8") as f:
                self._datos = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error cargando text_screens: {e}")
            self._datos = {}

    def recargar(self):
        self._cargar()

    def iniciar(self, screen_id):
        data = self._datos.get(screen_id)
        if not data:
            print(f"[TextScreen] ID '{screen_id}' no encontrada")
            self.activo = False
            return
        self._screen_id = screen_id
        self._titulo = data.get("titulo", "")
        self._lineas = data.get("lineas", [])
        self._linea_actual = 0
        self._char_idx = 0
        self.activo = True

    def actualizar(self):
        if not self.activo:
            return
        linea = self._lineas[self._linea_actual]
        if self._char_idx < len(linea):
            self._char_idx += 2

    def avanzar(self):
        if not self.activo:
            return
        linea = self._lineas[self._linea_actual]
        if self._char_idx < len(linea):
            self._char_idx = len(linea)
        elif self._linea_actual < len(self._lineas) - 1:
            self._linea_actual += 1
            self._char_idx = 0
        else:
            self.activo = False

    def _dibujar_texto_centrado(self, pantalla, texto, fuente, color, y_inicial, max_ancho):
        palabras = texto.split(" ")
        lineas_render = []
        linea_actual = ""
        for palabra in palabras:
            if not palabra:
                continue
            prueba = linea_actual + (" " if linea_actual else "") + palabra
            if fuente.size(prueba)[0] <= max_ancho:
                linea_actual = prueba
            else:
                if linea_actual:
                    lineas_render.append(linea_actual)
                linea_actual = palabra
        if linea_actual:
            lineas_render.append(linea_actual)

        y = y_inicial - (len(lineas_render) - 1) * 34 // 2
        for linea in lineas_render:
            cx = ANCHO // 2 - fuente.size(linea)[0] // 2
            for dx, dy in [(1, 1), (-1, -1), (0, 1)]:
                pantalla.blit(fuente.render(linea, True, (80, 70, 50)), (cx + dx, y + dy))
            pantalla.blit(fuente.render(linea, True, color), (cx, y))
            y += 34

    def dibujar(self, pantalla):
        if not self.activo:
            return

        pantalla.fill((5, 8, 15))

        if self._titulo:
            fuente_tit = pygame.font.SysFont("Arial", 28, bold=True)
            tit = fuente_tit.render(self._titulo, True, DORADO)
            cx = ANCHO // 2 - tit.get_width() // 2
            pantalla.blit(tit, (cx, 60))

        texto = self._lineas[self._linea_actual][:self._char_idx]
        self._dibujar_texto_centrado(pantalla, texto, pygame.font.SysFont("Arial", 22), DORADO, ALTO // 2, ANCHO - 120)

        if self._char_idx >= len(self._lineas[self._linea_actual]):
            hint = pygame.font.SysFont("Arial", 16).render("[ESPACIO]", True, (100, 90, 60))
            hint_rect = hint.get_rect(center=(ANCHO // 2, ALTO - 30))
            pantalla.blit(hint, hint_rect)

        total = len(self._lineas)
        for i in range(total):
            color = DORADO if i == self._linea_actual else (40, 35, 25)
            cx = ANCHO // 2 + (i - total // 2) * 20
            if total % 2 == 0:
                cx += 10
            pygame.draw.circle(pantalla, color, (cx, ALTO - 130), 3)

