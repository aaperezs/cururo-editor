# camera.py
from engine.configs import *


class Camera:
    def __init__(self, ancho_mundo, alto_mundo):
        self.ancho_mundo = ancho_mundo
        self.alto_mundo = alto_mundo
        # Si el mundo cabe en pantalla, posicionar centrado de entrada
        if ancho_mundo < ANCHO:
            self.x = (ancho_mundo - ANCHO) // 2
        else:
            self.x = 0
        if alto_mundo < ALTO:
            self.y = (alto_mundo - ALTO) // 2
        else:
            self.y = 0
        self.target = None
        self.smooth = True
        # Si el mundo es más chico que la pantalla en algún eje,
        # la cámara no se mueve en ese eje (ya está centrada)
        self._fijo_x = ancho_mundo < ANCHO
        self._fijo_y = alto_mundo < ALTO

    def seguir(self, target):
        """Establece el objetivo de la cámara"""
        self.target = target

    def snap_to(self, target_x, target_y):
        """Posiciona la cámara instantáneamente en un punto del mundo (sin suavizado).

        Si el mundo es más chico que la pantalla en algún eje,
        centra el mapa en ese eje en vez de seguir al target.
        """
        if self._fijo_x:
            self.x = (self.ancho_mundo - ANCHO) // 2
        else:
            self.x = max(0, min(target_x - ANCHO // 2, self.ancho_mundo - ANCHO))

        if self._fijo_y:
            self.y = (self.alto_mundo - ALTO) // 2
        else:
            self.y = max(0, min(target_y - ALTO // 2, self.alto_mundo - ALTO))

    def actualizar(self):
        """Actualiza la posición de la cámara"""
        if not self.target:
            return

        target_x = self.target[0] - ANCHO // 2
        target_y = self.target[1] - ALTO // 2

        # Eje fijo → no mover (ya está centrado en __init__)
        if self._fijo_x:
            target_x = self.x
        else:
            target_x = max(0, min(target_x, self.ancho_mundo - ANCHO))

        if self._fijo_y:
            target_y = self.y
        else:
            target_y = max(0, min(target_y, self.alto_mundo - ALTO))

        if self.smooth:
            self.x += (target_x - self.x) * 0.1
            self.y += (target_y - self.y) * 0.1
        else:
            self.x = target_x
            self.y = target_y

    def aplicar(self, posicion):
        """Aplica el offset de cámara a una posición"""
        x, y = posicion
        return (x - self.x, y - self.y)

    def get_offset(self):
        """Devuelve el offset de cámara (negativo: el mundo se mueve opuesto a la cámara)"""
        return (-int(self.x), -int(self.y))
