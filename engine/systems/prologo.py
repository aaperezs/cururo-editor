import json
import os

import pygame
from engine.configs import *
from engine.project_paths import data_dir

RUTA_PROLOGO = data_dir("prologo.json")

pygame.font.init()

def _cargar_fuente(tam, negrita=False):
    for nombre in ["Georgia", "Palatino Linotype", "Book Antiqua", None]:
        try:
            if nombre:
                f = pygame.font.SysFont(nombre, tam, bold=negrita)
            else:
                f = pygame.font.Font(None, tam)
            if f and f.render("A", True, (0,0,0)).get_width() > 0:
                return f
        except:
            continue
    return pygame.font.Font(None, tam)

FUENTE_PROLOGO = _cargar_fuente(22)
FUENTE_PROLOGO_CHICA = _cargar_fuente(16)


class PrologoSystem:
    def __init__(self):
        self.lineas = []
        self.linea_actual = 0
        self.char_idx = 0
        self.activo = False
        self.terminado = False
        self._cargar()

    def _cargar(self):
        try:
            with open(RUTA_PROLOGO, "r", encoding="utf-8") as f:
                self.lineas = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error cargando prólogo: {e}")
            self.lineas = ["El bosque nórdico te llama..."]

    def iniciar(self):
        self.linea_actual = 0
        self.char_idx = 0
        self.activo = True
        self.terminado = False

    def actualizar(self):
        if not self.activo:
            return
        linea = self.lineas[self.linea_actual]
        if self.char_idx < len(linea):
            self.char_idx += 1

    def avanzar(self):
        if not self.activo:
            return
        linea = self.lineas[self.linea_actual]
        if self.char_idx < len(linea):
            self.char_idx = len(linea)
        elif self.linea_actual < len(self.lineas) - 1:
            self.linea_actual += 1
            self.char_idx = 0
        else:
            self.activo = False
            self.terminado = True

    def _dibujar_texto_centrado(self, pantalla, texto, fuente, color, y_inicial, max_ancho):
        palabras = texto.split(" ")
        lineas = []
        linea_actual = ""
        for palabra in palabras:
            if not palabra:
                continue
            prueba = linea_actual + (" " if linea_actual else "") + palabra
            if fuente.size(prueba)[0] <= max_ancho:
                linea_actual = prueba
            else:
                if linea_actual:
                    lineas.append(linea_actual)
                linea_actual = palabra
        if linea_actual:
            lineas.append(linea_actual)

        y = y_inicial - (len(lineas) - 1) * 34 // 2
        for linea in lineas:
            cx = ANCHO // 2 - fuente.size(linea)[0] // 2
            for dx, dy in [(1,1),(-1,-1),(0,1)]:
                pantalla.blit(fuente.render(linea, True, (80, 70, 50)), (cx + dx, y + dy))
            for dx, dy in [(1,0),(0,1)]:
                pantalla.blit(fuente.render(linea, True, (240, 230, 200)), (cx + dx, y + dy))
            pantalla.blit(fuente.render(linea, True, color), (cx, y))
            y += 34

    def dibujar(self, pantalla):
        if not self.activo:
            return

        pantalla.fill((5, 8, 15))

        texto = self.lineas[self.linea_actual][:self.char_idx]

        if self.linea_actual == len(self.lineas) - 1:
            self._dibujar_texto_centrado(pantalla, texto, FUENTE_PROLOGO_CHICA, (180, 160, 100), ALTO - 100, ANCHO - 120)
        else:
            self._dibujar_texto_centrado(pantalla, texto, FUENTE_PROLOGO, DORADO, ALTO // 2, ANCHO - 120)

        # Indicador de avance
        if self.char_idx >= len(self.lineas[self.linea_actual]):
            hint = FUENTE_PROLOGO_CHICA.render("[ESPACIO]", True, (100, 90, 60))
            hint_rect = hint.get_rect(center=(ANCHO // 2, ALTO - 30))
            pantalla.blit(hint, hint_rect)

        total = len(self.lineas)
        punto = self.linea_actual + 1
        for i in range(total):
            color = DORADO if i == self.linea_actual else (40, 35, 25)
            cx = ANCHO // 2 + (i - total // 2) * 20
            if total % 2 == 0:
                cx += 10
            pygame.draw.circle(pantalla, color, (cx, ALTO - 130), 3)

