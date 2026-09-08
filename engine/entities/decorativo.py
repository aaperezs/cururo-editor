import pygame
from engine.configs import TAMANO_CELDA
from engine.utils.sprite_manager import obtener as obtener_sprite
from engine.systems.animation import get_anim_sprite, get_anim_glow


class Decorativo:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.z = 0
        self.sprite_id = ""
        self.animation = ""

    def dibujar(self, pantalla, offset_x=0, offset_y=0):
        ox = self.x + offset_x
        oy = self.y + offset_y

        if self.animation:
            sprite_id = get_anim_sprite(self.animation) or self.sprite_id
            sprite = obtener_sprite(sprite_id)
            if sprite:
                glow = get_anim_glow(self.animation)
                if glow:
                    color = tuple(glow.get("color", [255, 255, 0]))
                    radius = glow.get("radius", 8)
                    alpha = glow.get("alpha", 80)
                    gcx = ox + TAMANO_CELDA // 2
                    gcy = oy + TAMANO_CELDA // 2
                    for r in range(radius, 1, -2):
                        surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
                        pygame.draw.circle(surf, (*color, alpha), (r + 2, r + 2), r)
                        pantalla.blit(surf, (gcx - r - 2, gcy - r - 2))
                pantalla.blit(sprite, (ox, oy))
                return

        if self.sprite_id:
            sprite = obtener_sprite(self.sprite_id)
            if sprite:
                pantalla.blit(sprite, (ox, oy))
