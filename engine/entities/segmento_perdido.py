import math
import random

import pygame
from engine.configs import *


class SegmentoPerdido:
    def __init__(self, x, y, nivel_ancho=800, nivel_alto=600):
        self.origen_x = x
        self.origen_y = y
        self.x = x
        self.y = y
        self.tiempo_vida = 60
        self.vida_maxima = 60
        self.recogido = False
        self.parpadeo = 0

        angulo = random.uniform(0, math.pi * 2)
        dist = random.randint(3, 8) * TAMANO_CELDA
        self.dest_x = x + math.cos(angulo) * dist
        self.dest_y = y + math.sin(angulo) * dist
        self.dest_x = max(TAMANO_CELDA, min(nivel_ancho - TAMANO_CELDA, self.dest_x))
        self.dest_y = max(TAMANO_CELDA, min(nivel_alto - TAMANO_CELDA, self.dest_y))

        self.vel_x = (self.dest_x - x) / 10
        self.vel_y = (self.dest_y - y) / 10
        self.fase_vuelo = 0

    def actualizar(self):
        if not self.recogido:
            self.tiempo_vida -= 1
            self.parpadeo += 1
            if self.fase_vuelo < 10:
                self.x += self.vel_x
                self.y += self.vel_y
                self.fase_vuelo += 1

    def dibujar(self, pantalla, offset_x=0, offset_y=0):
        if self.recogido or self.tiempo_vida <= 0:
            return

        restante = self.tiempo_vida / self.vida_maxima
        parpadeo_vel = max(1, int(30 * restante))

        if self.tiempo_vida < 30 and self.parpadeo % parpadeo_vel < parpadeo_vel // 2:
            return

        cx = self.x + TAMANO_CELDA // 2
        cy = self.y + TAMANO_CELDA // 2
        ox = offset_x
        oy = offset_y

        brillo = int(255 * max(0, restante - 0.3) + 80)

        for g in range(4, 0, -1):
            alpha = 40 - g * 8
            radio = 14 + g * 3
            surf = pygame.Surface((radio * 2 + 4, radio * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 220, 80, alpha), (radio + 2, radio + 2), radio)
            pantalla.blit(surf, (cx + ox - radio - 2, cy + oy - radio - 2))

        puntos = [
            (cx, cy - 7),
            (cx + 6, cy - 2),
            (cx + 5, cy + 4),
            (cx, cy + 8),
            (cx - 5, cy + 4),
            (cx - 6, cy - 2),
        ]
        body = [(px + ox, py + oy) for px, py in puntos]
        pygame.draw.polygon(pantalla, (220, 180, 60), body)
        pygame.draw.polygon(pantalla, (180, 140, 30), body, 1)

        brillo_pts = [
            (cx - 2, cy - 5),
            (cx + 2, cy - 4),
            (cx + 1, cy - 1),
            (cx - 1, cy - 2),
        ]
        brillo_draw = [(px + ox, py + oy) for px, py in brillo_pts]
        pygame.draw.polygon(pantalla, (255, 240, 180), brillo_draw)

        brillo2 = [
            (cx + 3, cy + 2),
            (cx + 5, cy + 1),
            (cx + 4, cy + 3),
        ]
        b2 = [(px + ox, py + oy) for px, py in brillo2]
        pygame.draw.polygon(pantalla, (255, 255, 220), b2)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, TAMANO_CELDA, TAMANO_CELDA)

    def esta_vivo(self):
        return self.tiempo_vida > 0 and not self.recogido
