import pygame
from engine.configs import *
from engine.entities.bloque_acero import BloqueAcero


class Arbol(BloqueAcero):
    def __init__(self, x, y):
        super().__init__(x, y)

    def dibujar(self, pantalla, offset_x=0, offset_y=0):
        if not self.visible:
            return
        from engine.utils.sprite_manager import obtener as obtener_sprite
        sprite = obtener_sprite("arbol")
        if sprite:
            pantalla.blit(sprite, (self.x + offset_x, self.y + offset_y))
        else:
            x, y = self.x + offset_x, self.y + offset_y
            pygame.draw.rect(pantalla, (25, 110, 15), (x, y, TAMANO_CELDA, TAMANO_CELDA))
            pygame.draw.rect(pantalla, NEGRO, (x, y, TAMANO_CELDA, TAMANO_CELDA), 1)
