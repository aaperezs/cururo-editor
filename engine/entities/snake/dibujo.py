# entities/snake/dibujo.py
import pygame
from engine.configs import *


class DibujoMixin:
    """Mixin para el dibujo de la serpiente"""

    def set_skin(self, habilidad_efecto):
        """Cambia la skin según la habilidad equipada"""
        if habilidad_efecto == "golpe":
            self.skin_actual = "golpe"
        elif habilidad_efecto == "manto":
            self.skin_actual = "manto"
        elif habilidad_efecto == "latigo":
            self.skin_actual = "latigo"
        else:
            self.skin_actual = "base"

    def dibujar(self, pantalla, manto_activo=False, offset_x=0, offset_y=0):
        if self.enroscado or self.etapa == 2:
            if not self.segmentos_visibles:
                return
            cuerpo = self.segmentos_visibles
        else:
            cuerpo = self.body

        if not cuerpo:
            return

        for i, segmento in enumerate(cuerpo):
            if i == 0:
                if self.skin_actual == "golpe":
                    color = SkinSnake.GOLPE_CABEZA
                elif self.skin_actual == "manto" or manto_activo:
                    color = SkinSnake.MANTO_CABEZA
                elif self.skin_actual == "latigo":
                    color = SkinSnake.LATIGO_CABEZA
                else:
                    color = SkinSnake.BASE_CABEZA

                if self.invencible and pygame.time.get_ticks() % 200 < 100:
                    color = BLANCO
            else:
                if self.skin_actual == "golpe":
                    color = (139, 90, 43)
                elif self.skin_actual == "manto" or manto_activo:
                    color = (80, 80, 90)
                elif self.skin_actual == "latigo":
                    color = SkinSnake.LATIGO_CUERPO
                else:
                    intensidad = max(50, 200 - (i * 3))
                    color = (0, intensidad, 0)

            sx = segmento[0] + offset_x
            sy = segmento[1] + offset_y
            if i == 0:
                # Cabeza triangular orientada según dirección
                cx, cy = sx + TAMANO_CELDA // 2, sy + TAMANO_CELDA // 2
                if self.direccion == "DERECHA":
                    pts = [(sx+20, sy+10), (sx, sy), (sx, sy+20)]
                    ojos = [(sx+14, sy+5), (sx+14, sy+15)]
                    pup = (1, 0)
                elif self.direccion == "IZQUIERDA":
                    pts = [(sx, sy+10), (sx+20, sy), (sx+20, sy+20)]
                    ojos = [(sx+6, sy+5), (sx+6, sy+15)]
                    pup = (-1, 0)
                elif self.direccion == "ABAJO":
                    pts = [(sx+10, sy+20), (sx, sy), (sx+20, sy)]
                    ojos = [(sx+5, sy+14), (sx+15, sy+14)]
                    pup = (0, 1)
                else:
                    pts = [(sx+10, sy), (sx, sy+20), (sx+20, sy+20)]
                    ojos = [(sx+5, sy+6), (sx+15, sy+6)]
                    pup = (0, -1)
                pygame.draw.polygon(pantalla, color, pts)
                pygame.draw.polygon(pantalla, NEGRO, pts, 1)
                for ox, oy in ojos:
                    pygame.draw.circle(pantalla, BLANCO, (ox, oy), 2)
                    pygame.draw.circle(pantalla, NEGRO, (ox+pup[0], oy+pup[1]), 1)
            else:
                # Cuerpo: círculos ovalados (segmentos conectados)
                radio = TAMANO_CELDA // 2 - 2
                pygame.draw.circle(pantalla, color, (sx + radio + 2, sy + radio + 2), radio)
                pygame.draw.circle(pantalla, NEGRO, (sx + radio + 2, sy + radio + 2), radio, 1)
                # Escamas 8-bit
                if self.skin_actual == "golpe":
                    escama = (100, 65, 30)
                elif self.skin_actual == "manto" or manto_activo:
                    escama = (55, 55, 65)
                elif self.skin_actual == "latigo":
                    escama = (160, 45, 20)
                else:
                    escama = (intensidad // 2, intensidad, intensidad // 2)
                pygame.draw.line(pantalla, escama, (sx+5, sy+5), (sx+10, sy+10), 1)
                pygame.draw.line(pantalla, escama, (sx+15, sy+5), (sx+10, sy+10), 1)

        if self.brillo > 0:
            cabeza = self.get_cabeza()
            if cabeza:
                surf = pygame.Surface((TAMANO_CELDA * 3, TAMANO_CELDA * 3), pygame.SRCALPHA)
                alpha = min(100, self.brillo * 3)
                pygame.draw.circle(surf, (255, 215, 0, alpha),
                                 (TAMANO_CELDA * 1.5, TAMANO_CELDA * 1.5),
                                 TAMANO_CELDA * 1.5)
                pantalla.blit(surf, (cabeza[0] + offset_x - TAMANO_CELDA, cabeza[1] + offset_y - TAMANO_CELDA))

            if self.brillo > 0:
                self.brillo -= 0.5
                if self.brillo < 0:
                    self.brillo = 0
        if self.dormido:
            cabeza = self.get_cabeza()
            if cabeza:
                fuente = pygame.font.SysFont("Arial", 14, bold=True)
                ayuda = fuente.render("apreta", True, (200, 230, 255))
                pantalla.blit(ayuda, (cabeza[0] + offset_x - 16, cabeza[1] + offset_y - 30))
                flechas = fuente.render(u"\u2190 \u2191 \u2192 \u2193", True, (180, 210, 255))
                pantalla.blit(flechas, (cabeza[0] + offset_x - 26, cabeza[1] + offset_y - 16))

    def get_cabeza(self):
        """Devuelve la posición de la cabeza"""
        if self.body:
            return self.body[0]
        return None

    def get_longitud(self):
        """Devuelve la longitud actual"""
        return self.longitud

    def get_escamas(self):
        from engine.configs import LONGITUD_INICIAL
        reduced = self.dormido or self.enroscado or self.creciendo
        total = max(self.longitud, self.largo_original) if (reduced and self.largo_original > 0) else self.longitud
        return max(0, total - LONGITUD_INICIAL)

    def perder_escamas(self, cantidad):
        """Consume escamas reduciendo la longitud, nunca baja de LONGITUD_INICIAL"""
        from engine.configs import LONGITUD_INICIAL
        max_perder = self.longitud - LONGITUD_INICIAL
        if max_perder <= 0:
            return 0
        perder = min(cantidad, max_perder)
        for _ in range(perder):
            if len(self.body) > 1:
                self.body.pop()
                self.longitud -= 1
        return perder

    def tiene_deuda(self):
        """Verifica si tiene deuda activa"""
        return self.deuda

    def get_deuda_restante(self):
        """Devuelve cuántos segmentos debe comer para saldar"""
        return self.segmentos_para_saldar
