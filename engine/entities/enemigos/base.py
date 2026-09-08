# entities/enemigos/base.py
import pygame
from engine.configs import *


class Iggy:
    """Clase base para todos los enemigos"""

    def __init__(self, x, y, patron="horizontal", velocidad=1):
        self.x = x
        self.y = y
        self.patron = patron
        self.velocidad = velocidad
        self.direccion = 1
        self.vivo = True
        self.aturdido = False
        self.tiempo_aturdido = 0
        self.ancho = TAMANO_CELDA
        self.alto = TAMANO_CELDA
        self.color = ROJO
        self.drops = []

        self.x_inicial = x
        self.y_inicial = y
        self.rango = 100
        self.animation = ""

    def _tile_colisiona(self, x, y, objetos):
        gx = x // TAMANO_CELDA
        gy = y // TAMANO_CELDA
        for obj in objetos:
            if hasattr(obj, 'activo') and not obj.activo:
                continue
            if obj.x // TAMANO_CELDA == gx and obj.y // TAMANO_CELDA == gy:
                return True
        return False

    def mover(self, objetos=None):
        """Mueve al enemigo según su patrón, rebotando en objetos sólidos"""
        if not self.vivo or self.aturdido:
            return

        obs = objetos or []

        if self.patron == "horizontal":
            nueva_x = self.x + self.velocidad * self.direccion
            if self._tile_colisiona(nueva_x, self.y, obs):
                self.direccion *= -1
            else:
                self.x = nueva_x
                if self.x > self.x_inicial + self.rango or self.x < self.x_inicial - self.rango:
                    self.direccion *= -1
        elif self.patron == "vertical":
            nueva_y = self.y + self.velocidad * self.direccion
            if self._tile_colisiona(self.x, nueva_y, obs):
                self.direccion *= -1
            else:
                self.y = nueva_y
                if self.y > self.y_inicial + self.rango or self.y < self.y_inicial - self.rango:
                    self.direccion *= -1
        elif self.patron == "circular":
            pass

    def aturdir(self):
        """Aturde al enemigo"""
        self.aturdido = True
        self.tiempo_aturdido = 30
        self.color = GRIS

    def actualizar_aturdimiento(self):
        """Actualiza el estado de aturdimiento"""
        if self.aturdido:
            self.tiempo_aturdido -= 1
            if self.tiempo_aturdido <= 0:
                self.aturdido = False
                self.color = ROJO

    def dibujar(self, pantalla, offset_x=0, offset_y=0):
        if not self.vivo:
            return

        x = self.x + offset_x
        y = self.y + offset_y
        c = self.color

        from engine.utils.sprite_manager import obtener as obtener_sprite
        from engine.systems.animation import get_anim_sprite

        if self.animation:
            sprite_id = get_anim_sprite(self.animation) or "enemigo_melee"
            sprite = obtener_sprite(sprite_id)
            if sprite:
                pantalla.blit(sprite, (x, y))
                return

        sprite = obtener_sprite("enemigo_melee")
        if sprite:
            pantalla.blit(sprite, (x, y))
        else:
            casco = [
                (x+1, y+15), (x+2, y+2), (x+5, y), (x+10, y-1),
                (x+15, y), (x+18, y+2), (x+19, y+15)
            ]
            pygame.draw.polygon(pantalla, c, casco)
            pygame.draw.polygon(pantalla, NEGRO, casco, 1)
            if c != GRIS:
                pygame.draw.polygon(pantalla, (180, 140, 60),
                                  [(x+1, y+3), (x-3, y-4), (x+5, y+2)])
                pygame.draw.polygon(pantalla, (180, 140, 60),
                                  [(x+19, y+3), (x+23, y-4), (x+15, y+2)])
            pygame.draw.line(pantalla, (150, 120, 60), (x+10, y+2), (x+10, y+12), 2)



    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.ancho, self.alto)

    def recibir_golpe(self):
        """Recibe un golpe (muerte)"""
        self.vivo = False
        return True
