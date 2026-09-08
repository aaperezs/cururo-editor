# entities/snake/crecimiento.py
from engine.configs import *


class CrecimientoMixin:
    """Mixin para el crecimiento y venta de segmentos"""

    def crecer(self, cantidad=1):
        """Aumenta la longitud de la serpiente"""
        for _ in range(cantidad):
            if self.body:
                ultimo = self.body[-1].copy()
                self.body.append(ultimo)
                self.longitud += 1

                if self.creciendo:
                    self.largo_original += 1

        if self.deuda:
            self.segmentos_para_saldar -= cantidad
            if self.segmentos_para_saldar <= 0:
                self.deuda = False
                print("¡Deuda saldada! Velocidad normal.")

    def vender_segmentos(self, cantidad):
        """Vende segmentos de la cola"""
        if cantidad <= 0:
            return False
        if cantidad >= self.longitud:
            return False

        for _ in range(cantidad):
            if len(self.body) > 1:
                self.body.pop()
                self.longitud -= 1
        return True

    def pedir_prestado(self, cantidad):
        """Pide prestados segmentos (sistema de deuda)"""
        if cantidad <= 0 or self.deuda:
            return False

        for _ in range(cantidad):
            if self.body:
                ultimo = self.body[-1].copy()
                self.body.append(ultimo)
                self.longitud += 1

        self.deuda = True
        self.segmentos_para_saldar = cantidad * 2
        return True
