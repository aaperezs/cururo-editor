# entities/bloque_acero.py
import pygame
from engine.configs import *
from engine.entities.objeto_colision import ObjetoBloqueante


class BloqueAcero(ObjetoBloqueante):
    """Bloque de acero indestructible - Bloquea el paso y activa enroscamiento"""

    def __init__(self, x, y):
        super().__init__(x, y)
        self.color_base = (130, 140, 160)      # Gris acero
        self.color_oscuro = (80, 90, 110)      # Gris oscuro
        self.color_claro = (180, 190, 210)     # Gris claro
        self.color_brillo = (220, 230, 250)    # Brillo
        self.rotura = 0
        self.rompible = False
        self.se_puede_destruir = False
        self.parpadeo = 0
        self.animacion_brillo = 0

    def colisiona_con(self, cabeza_x, cabeza_y):
        if not self.activo or not self.solid:
            return False
        return (cabeza_x == self.x and cabeza_y == self.y)

    def golpear(self, snake=None, estado=None, damage=1, attack_type=""):
        return False

    def es_obstaculo(self):
        return self.activo

    def get_rect(self):
        if not self.activo:
            return None
        return pygame.Rect(self.x, self.y, self.ancho, self.alto)

    def dibujar(self, pantalla, offset_x=0, offset_y=0):
        if not self.visible:
            return
        from engine.utils.sprite_manager import obtener as obtener_sprite
        sprite = obtener_sprite("bloque_acero")
        if sprite:
            pantalla.blit(sprite, (self.x + offset_x, self.y + offset_y))
        else:
            x, y = self.x + offset_x, self.y + offset_y
            pygame.draw.rect(pantalla, (105, 95, 80), (x, y, TAMANO_CELDA, TAMANO_CELDA))
            pygame.draw.rect(pantalla, NEGRO, (x, y, TAMANO_CELDA, TAMANO_CELDA), 1)
