# entities/snake/snake.py
from engine.configs import *

from .crecimiento import CrecimientoMixin
from .daño import DañoMixin
from .dibujo import DibujoMixin
from .dormido import DormidoMixin
from .enroscamiento import EnroscamientoMixin
from .movimiento import MovimientoMixin


class Snake(MovimientoMixin, DormidoMixin, EnroscamientoMixin, CrecimientoMixin, DañoMixin, DibujoMixin):
    """Clase principal de la serpiente"""

    def __init__(self, x, y, z=Z_MAPA_PRINCIPAL):
        self.body = [[x, y]]
        self.z = z
        self.direccion = "DERECHA"
        self.siguiente_direccion = "DERECHA"
        self.creciendo = False
        self.longitud = LONGITUD_INICIAL
        self.invencible = False
        self.tiempo_invencible = 0
        self.deuda = False
        self.segmentos_para_saldar = 0
        self.brillo = 0
        self.skin_actual = "base"

        self.dormido = True

        self.enroscado = True
        self.direccion_original = "DERECHA"
        self.segmentos_guardados = []
        self.direcciones_permitidas = []
        self.direccion_prohibida = ""
        self.segmentos_visibles = []
        self.largo_original = 0
        self.etapa = 0
        self.contador_pulsos = 0
        self.segmentos_plegados = 0
        self.segmentos_a_restaurar = 0
        self.segmentos_restaurados = 0
        self.estado_actual = None

        for i in range(1, LONGITUD_INICIAL):
            self.body.append([x - i * TAMANO_CELDA, y])

    def cambiar_z(self, nueva_z):
        self.z = nueva_z
        print(f"[ORM] Orm movido a capa Z={nueva_z}")
