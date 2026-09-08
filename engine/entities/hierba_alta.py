import pygame
from engine.configs import *
from engine.entities.objeto_colision import ObjetoColision


class HierbaAlta(ObjetoColision):
    def __init__(self, x, y, sprite_id="hierba_0"):
        super().__init__(x, y)
        self.activo = True
        self.visible = True
        self._sprite_id = sprite_id

    def colisiona_con(self, cabeza_x, cabeza_y):
        if not self.activo:
            return False
        return (cabeza_x == self.x and cabeza_y == self.y)

    def manejar_colision(self, snake, estado):
        pass

    def es_obstaculo(self):
        return False

    def get_rect(self):
        if not self.activo:
            return None
        return pygame.Rect(self.x, self.y, self.ancho, self.alto)
    def dibujar(self, pantalla, offset_x=0, offset_y=0):
        if not self.visible:
            return
        from engine.utils.sprite_manager import obtener as obtener_sprite
        sprite = obtener_sprite(self._sprite_id)
        if sprite:
            pantalla.blit(sprite, (self.x + offset_x, self.y + offset_y))
        else:
            x, y = self.x + offset_x, self.y + offset_y
            pygame.draw.rect(pantalla, (100, 155, 40), (x, y, TAMANO_CELDA, TAMANO_CELDA))
            pygame.draw.rect(pantalla, NEGRO, (x, y, TAMANO_CELDA, TAMANO_CELDA), 1)
