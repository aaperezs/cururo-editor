# entities/enemigos/shooter.py

import pygame
from engine.configs import *

from .base import Iggy


class Eldir(Iggy):
    """Enemigo disparador - Se mueve y dispara proyectiles"""

    def __init__(self, x, y, tipo_movimiento="horizontal", velocidad=1,
                 intervalo_disparo=60, velocidad_proyectil=3):
        super().__init__(x, y, tipo_movimiento, velocidad)

        self.tipo_disparo = "vertical" if tipo_movimiento == "horizontal" else "horizontal"
        self.intervalo_disparo = intervalo_disparo
        self.velocidad_proyectil = velocidad_proyectil
        self.contador_disparo = 0
        self.proyectiles = []
        self.color = (200, 100, 200)  # Morado
        self.radio = TAMANO_CELDA // 2 - 2
        self.vivo = True

    def mover(self, objetos=None):
        """Mueve al enemigo y actualiza disparos, rebotando en objetos sólidos"""
        if not self.vivo or self.aturdido:
            return

        obs = objetos or []

        # Movimiento (rebota en bordes y objetos sólidos)
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

        # Disparo
        self.contador_disparo += 1
        if self.contador_disparo >= self.intervalo_disparo:
            self.contador_disparo = 0
            self._disparar()

        # Actualizar proyectiles
        self._actualizar_proyectiles()

    def _disparar(self):
        """Dispara proyectiles en las direcciones correspondientes"""
        centro_x = self.x + TAMANO_CELDA // 2
        centro_y = self.y + TAMANO_CELDA // 2

        if self.tipo_disparo == "vertical":
            # Dispara ARRIBA y ABAJO
            self.proyectiles.append({
                "x": centro_x,
                "y": centro_y,
                "dx": 0,
                "dy": -self.velocidad_proyectil,
                "radio": 6,
                "color": ROJO,
                "vida": 120
            })
            self.proyectiles.append({
                "x": centro_x,
                "y": centro_y,
                "dx": 0,
                "dy": self.velocidad_proyectil,
                "radio": 6,
                "color": ROJO,
                "vida": 120
            })
        else:  # horizontal
            # Dispara IZQUIERDA y DERECHA
            self.proyectiles.append({
                "x": centro_x,
                "y": centro_y,
                "dx": -self.velocidad_proyectil,
                "dy": 0,
                "radio": 6,
                "color": ROJO,
                "vida": 120
            })
            self.proyectiles.append({
                "x": centro_x,
                "y": centro_y,
                "dx": self.velocidad_proyectil,
                "dy": 0,
                "radio": 6,
                "color": ROJO,
                "vida": 120
            })

    def _actualizar_proyectiles(self):
        """Mueve y elimina proyectiles expirados"""
        for proy in self.proyectiles[:]:
            proy["x"] += proy["dx"]
            proy["y"] += proy["dy"]
            proy["vida"] -= 1
            if proy["vida"] <= 0:
                self.proyectiles.remove(proy)

    def dibujar(self, pantalla, offset_x=0, offset_y=0):
        if not self.vivo:
            return

        x = self.x + offset_x
        y = self.y + offset_y
        centro = (x + TAMANO_CELDA // 2, y + TAMANO_CELDA // 2)

        from engine.utils.sprite_manager import obtener as obtener_sprite
        from engine.systems.animation import get_anim_sprite

        if self.animation:
            sprite_id = get_anim_sprite(self.animation) or "enemigo_shooter"
            sprite = obtener_sprite(sprite_id)
            if sprite:
                pantalla.blit(sprite, (x, y))
                return

        sprite = obtener_sprite("enemigo_shooter")
        if sprite:
            pantalla.blit(sprite, (x, y))
        else:
            pygame.draw.circle(pantalla, self.color, centro, self.radio)
            pygame.draw.circle(pantalla, NEGRO, centro, self.radio, 1)
            if self.color != GRIS:
                pygame.draw.polygon(pantalla, (180, 140, 60), [
                    (centro[0]-7, centro[1]-5), (centro[0]-12, centro[1]-10), (centro[0]-3, centro[1]-5)
                ])
                pygame.draw.polygon(pantalla, (180, 140, 60), [
                    (centro[0]+7, centro[1]-5), (centro[0]+12, centro[1]-10), (centro[0]+3, centro[1]-5)
                ])
            pygame.draw.line(pantalla, (150, 120, 60), (centro[0], centro[1]-6), (centro[0], centro[1]+2), 2)


        # Proyectiles
        for proy in self.proyectiles:
            px = int(proy["x"]) + offset_x
            py = int(proy["y"]) + offset_y
            pygame.draw.circle(pantalla, proy["color"],
                             (px, py), proy["radio"])
            pygame.draw.circle(pantalla, BLANCO,
                             (px, py), proy["radio"] // 2)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.ancho, self.alto)

    def get_proyectiles(self):
        """Devuelve la lista de proyectiles para detección de colisiones"""
        return self.proyectiles

    def recibir_golpe(self):
        """Recibe un golpe (muerte) - para habilidad de manto"""
        self.vivo = False
        return True
