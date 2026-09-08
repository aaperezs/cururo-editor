# entities/enemigos/melee.py
from engine.configs.colors import ROJO  # <--- IMPORTAR ROJO

from .base import Iggy


class EnemyMelee(Iggy):
    """Enemigo cuerpo a cuerpo (H, V, C)"""

    def __init__(self, x, y, patron="horizontal", velocidad=1):
        super().__init__(x, y, patron, velocidad)
        self.color = ROJO
