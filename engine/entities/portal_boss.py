# entities/portal_boss.py - PORTAL DE ENTRADA Y SALIDA (COMPLETO)
import pygame
from engine.configs import *


class PortalBoss:
    def __init__(self, x, y, arena, posicion_salida=None):
        self.x = x
        self.y = y
        self.ancho = TAMANO_CELDA
        self.alto = TAMANO_CELDA
        self.arena = arena

        # --- PORTAL DE ENTRADA (en el mundo principal) ---
        self.activo_entrada = arena.boss is not None

        # --- PORTAL DE SALIDA (dentro de la arena) ---
        self.x_salida = arena.x + arena.ancho // 2 - self.ancho // 2
        self.y_salida = arena.y + arena.alto // 2 + 30
        self.activo_salida = False

        self.animacion = 0

        # Posiciones
        self.punto_entrada = (arena.x + 50, arena.y + arena.alto - 50)
        if posicion_salida:
            self.posicion_salida = (
                (posicion_salida[0] // TAMANO_CELDA) * TAMANO_CELDA,
                (posicion_salida[1] // TAMANO_CELDA) * TAMANO_CELDA
            )
        else:
            self.posicion_salida = ((x // TAMANO_CELDA) * TAMANO_CELDA,
                                (y // TAMANO_CELDA) * TAMANO_CELDA)

        # Estado visual
        self.estado = "NORMAL"
        self.tiempo_espera = 0
        self.delay_salida = 18

    def actualizar(self, snake, estado):
        """Actualiza el portal - la entrada se maneja via eventos (cururo)"""
        # --- PORTAL DE SALIDA (dentro de la arena, se activa cuando el jefe muere) ---
        if not self.arena.boss or not self.arena.boss.vivo:
            if not self.activo_salida:
                self.activo_salida = True
                self.estado = "SALIDA"
                self.tiempo_espera = self.delay_salida
                print(f"¡Portal de SALIDA activado en ({self.x_salida}, {self.y_salida})!")

    def dibujar(self, pantalla, offset_x=0, offset_y=0):
        if self.activo_entrada:
            self._dibujar_portal(pantalla, self.x + offset_x, self.y + offset_y, "ENTRADA", offset_x, offset_y)

        if self.activo_salida:
            self._dibujar_portal(pantalla, self.x_salida + offset_x, self.y_salida + offset_y, "SALIDA", offset_x, offset_y)

    def _dibujar_portal(self, pantalla, x, y, tipo, offset_x=0, offset_y=0):
        self.animacion += 0.05

        pulsacion = abs(pygame.math.Vector2(1, 0).rotate_rad(self.animacion).x)
        radio_base = 20
        radio = radio_base + pulsacion * 8

        centro = (x + self.ancho // 2, y + self.alto // 2)

        if tipo == "SALIDA":
            colores = [(255, 215, 0, 220), (255, 200, 50, 170), (255, 180, 0, 120)]
            if self.tiempo_espera > 0:
                if pygame.time.get_ticks() % 400 < 200:
                    colores = [(255, 255, 0, 220), (255, 220, 0, 170), (255, 180, 0, 120)]
            color_texto = (255, 215, 0)
        else:
            colores = [(100, 100, 255, 220), (50, 50, 200, 170), (0, 0, 150, 120)]
            color_texto = (200, 200, 255)

        for i in range(3):
            alpha = colores[i][3]
            radio_i = radio - i * 10
            color = colores[i][:3] + (alpha,)
            pygame.draw.circle(pantalla, color, centro, radio_i, 3)

        color_interior = colores[0][:3] + (180,)
        pygame.draw.circle(pantalla, color_interior, centro, radio - 12)
        pygame.draw.circle(pantalla, (255, 255, 255, 220), centro, 6)

        if tipo == "SALIDA" and self.tiempo_espera > 0:
            fuente2 = pygame.font.SysFont("Arial", 11)
            segundos = (self.tiempo_espera // 6) + 1
            texto_espera = fuente2.render(f"Esperando... {segundos}s", True, (255, 200, 50))
            rect_espera = texto_espera.get_rect(center=(centro[0], centro[1] + radio + 40))
            pantalla.blit(texto_espera, rect_espera)

    def get_rect_entrada(self):
        return pygame.Rect(self.x, self.y, self.ancho, self.alto)

    def esta_activo_entrada(self):
        return self.activo_entrada
