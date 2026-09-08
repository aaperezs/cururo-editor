# systems/particles.py
import random

import pygame
from engine.configs import *


class Particle:
    def __init__(self, x, y, color, velocidad, direccion, vida=30):
        self.x = x
        self.y = y
        self.color = color
        self.vida = vida
        self.max_vida = vida
        self.velocidad = velocidad
        self.direccion = direccion  # [dx, dy]

        # Tamaño inicial (se encoge con el tiempo)
        self.tamaño = random.randint(4, 8)

    def actualizar(self):
        """Actualiza la partícula"""
        self.x += self.velocidad * self.direccion[0]
        self.y += self.velocidad * self.direccion[1]
        self.vida -= 1
        self.tamaño = max(1, self.tamaño * 0.97)

    def dibujar(self, pantalla, offset_x=0, offset_y=0):
        if self.vida <= 0 or self.tamaño <= 0:
            return

        alpha = int(255 * (self.vida / self.max_vida))

        surf = pygame.Surface((self.tamaño * 3, self.tamaño * 3), pygame.SRCALPHA)

        color_con_alpha = (*self.color, alpha)
        pygame.draw.circle(surf, color_con_alpha,
                          (self.tamaño * 1.5, self.tamaño * 1.5),
                          self.tamaño)

        pantalla.blit(surf, (self.x + offset_x - self.tamaño * 1.5, self.y + offset_y - self.tamaño * 1.5))

    def esta_viva(self):
        """Verifica si la partícula está viva"""
        return self.vida > 0

class ParticleSystem:
    def __init__(self):
        self.particulas = []

    def limpiar(self):
        """Elimina todas las partículas"""
        self.particulas = []

    def crear_explosion(self, x, y, cantidad=20, color=AMARILLO):
        """Crea una explosión de partículas"""
        for _ in range(cantidad):
            angulo = random.uniform(0, 3.14159 * 2)
            velocidad = random.uniform(1, 5)
            direccion = (pygame.math.Vector2(1, 0).rotate_rad(angulo).x,
                        pygame.math.Vector2(1, 0).rotate_rad(angulo).y)

            # Variación de color
            color_variado = (
                min(255, max(0, color[0] + random.randint(-40, 40))),
                min(255, max(0, color[1] + random.randint(-40, 40))),
                min(255, max(0, color[2] + random.randint(-40, 40)))
            )

            vida = random.randint(15, 40)
            particula = Particle(x, y, color_variado, velocidad, direccion, vida)
            self.particulas.append(particula)

    def crear_anillo_sonico(self, x, y, color):
        """Crea un anillo expansivo (efecto sonic)"""
        for i in range(12):
            angulo = (3.14159 * 2 / 12) * i
            direccion = (pygame.math.Vector2(1, 0).rotate_rad(angulo).x,
                        pygame.math.Vector2(1, 0).rotate_rad(angulo).y)
            vida = random.randint(12, 22)
            particula = Particle(x, y, color, 3, direccion, vida)
            particula.tamaño = 3
            self.particulas.append(particula)

    def actualizar(self):
        """Actualiza todas las partículas"""
        for particula in self.particulas[:]:
            particula.actualizar()
            if not particula.esta_viva():
                self.particulas.remove(particula)

    def dibujar(self, pantalla, offset_x=0, offset_y=0):
        for particula in self.particulas:
            particula.dibujar(pantalla, offset_x, offset_y)
