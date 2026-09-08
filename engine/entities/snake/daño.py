# entities/snake/daño.py
from engine.configs import *


class DañoMixin:
    """Mixin para el sistema de daño"""

    def perder_segmentos(self, cantidad):
        """Pierde segmentos al recibir daño - NUNCA baja de 3"""
        if self.invencible:
            return []

        self.invencible = True
        self.tiempo_invencible = 5

        segmentos_perdidos = []
        longitud_minima = LONGITUD_MINIMA
        max_perder = self.longitud - longitud_minima

        if max_perder <= 0:
            return []

        perder = min(cantidad, max_perder)
        perder = max(0, perder)

        if perder <= 0:
            return []

        for _ in range(perder):
            if len(self.body) > 1:
                segmento = self.body.pop()
                segmentos_perdidos.append(segmento)
                self.longitud -= 1

        if self.longitud < longitud_minima:
            self.longitud = longitud_minima

        return segmentos_perdidos
