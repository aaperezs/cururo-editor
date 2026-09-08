# entities/snake/dormido.py
from engine.configs import *


class DormidoMixin:
    """Mixin para el sistema de sueño/despertar de Orm"""

    def iniciar_dormido(self, posicion):
        """Pone a Orm dormido al inicio de un nivel, esperando input del jugador"""
        self.segmentos_guardados = self.body.copy()
        self.largo_original = len(self.body)

        self.dormido = True
        self.direccion = "DERECHA"
        self.siguiente_direccion = "DERECHA"
        self.etapa = 0

        self.segmentos_visibles = [self.body[0].copy()]
        self.body = self.segmentos_visibles.copy()
        self.longitud = len(self.body)

        print(f"[SNAKE] Orm dormido en inicio en: {self.body[0]}")
        print(f"   Cuerpo guardado: {len(self.segmentos_guardados)} segmentos")

    def despertar(self):
        """Despierta a Orm y restaura su cuerpo completo"""
        if self.dormido:
            self.dormido = False
            self.enroscado = False
            if self.segmentos_guardados:
                target = len(self.segmentos_guardados)
                current = len(self.body)
                if current < target:
                    diff = target - current
                    self.crecer(diff)
                self.segmentos_guardados = []
            self.etapa = 0
            return True
        return False
