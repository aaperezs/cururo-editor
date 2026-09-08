# entities/pared.py
import pygame
from engine.configs import *
from engine.entities.objeto_colision import ObjetoPeligroso


class Pared(ObjetoPeligroso):
    def __init__(self, x, y, ancho, alto):
        super().__init__(x, y, ancho, alto)
        self.tipo_daño = "mata"
        self.ignorar_armadura = True

    def colisiona_con(self, cabeza_x, cabeza_y):
        """Verifica si colisiona con la cabeza"""
        if not self.activo or not self.visible or not self.solid:
            return False
        return (self.x <= cabeza_x < self.x + self.ancho and
                self.y <= cabeza_y < self.y + self.alto)

    def manejar_colision(self, snake, estado):
        """Mata a la serpiente si es sólida"""
        if not self.solid:
            return
        estado.game_over = True
        estado.death_cause = f"Pared en ({self.x},{self.y})"
        from engine.managers.colision_manager import mostrar_mensaje
        mostrar_mensaje("¡Chocaste contra la pared!", 60)
        estado.particles.crear_explosion(
            snake.body[0][0] + TAMANO_CELDA//2,
            snake.body[0][1] + TAMANO_CELDA//2,
            30, ROJO
        )
        return "mata"

    def dibujar(self, pantalla, offset_x=0, offset_y=0):
        if not self.visible:
            return

        x = self.x + offset_x
        y = self.y + offset_y

        from engine.utils.sprite_manager import obtener as obtener_sprite
        sprite = obtener_sprite("pared")
        if sprite:
            for tx in range(0, self.ancho, TAMANO_CELDA):
                for ty in range(0, self.alto, TAMANO_CELDA):
                    pantalla.blit(sprite, (x + tx, y + ty))
        else:
            pygame.draw.rect(pantalla, PARED_COLOR, (x, y, self.ancho, self.alto))
            pygame.draw.rect(pantalla, MADERA_OSCURO, (x, y, self.ancho, self.alto), 2)
            pygame.draw.line(pantalla, MADERA_OSCURO, (x+2, y+6), (x+self.ancho-2, y+6), 1)
            pygame.draw.line(pantalla, MADERA_OSCURO, (x+2, y+14), (x+self.ancho-2, y+14), 1)



    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.ancho, self.alto)
