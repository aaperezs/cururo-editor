# entities/food.py
import random

import pygame
from engine.configs import *
from engine.utils.helpers import alinear_a_grid


class Food:
    _TIPO_SPRITE = {
        COMIDA_NORMAL: "comida_normal",
        COMIDA_MANA: "comida_mana",
        COMIDA_ESPECIAL: "comida_dorada",
    }

    @staticmethod
    def _resolve_animation(tipo):
        sprite_id = Food._TIPO_SPRITE.get(tipo)
        if not sprite_id:
            return ""
        try:
            from editor.elements import get_all_elements, get_element
            for eid in get_all_elements():
                el = get_element(eid)
                if el and el.get("sprite_id") == sprite_id:
                    return el.get("properties", {}).get("animation", "")
        except Exception:
            pass
        return ""

    def __init__(self, x, y, tipo=COMIDA_NORMAL):
        x, y = alinear_a_grid(x, y)
        self.x = x
        self.y = y
        self.tipo = tipo
        self.color = COLOR_COMIDA[tipo]
        self.nombre = NOMBRE_COMIDA[tipo]
        self.animation = Food._resolve_animation(tipo)
        self.efecto = {
            COMIDA_NORMAL: "Crece +1",
            COMIDA_MANA: "Recarga PP",
            COMIDA_ESPECIAL: "Crece +3"
        }[tipo]

    def dibujar(self, pantalla, offset_x=0, offset_y=0):
        ox = self.x + offset_x
        oy = self.y + offset_y
        cx = ox + TAMANO_CELDA // 2
        cy = oy + TAMANO_CELDA // 2
        from engine.utils.sprite_manager import obtener as obtener_sprite

        def _draw_glow(anim_name, sx, sy):
            from engine.systems.animation import get_anim_glow
            glow = get_anim_glow(anim_name)
            if not glow:
                return
            color = tuple(glow.get("color", [255, 255, 0]))
            radius = glow.get("radius", 8)
            alpha = glow.get("alpha", 80)
            gcx = sx + TAMANO_CELDA // 2
            gcy = sy + TAMANO_CELDA // 2
            for r in range(radius, 1, -2):
                surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(surf, (*color, alpha), (r + 2, r + 2), r)
                pantalla.blit(surf, (gcx - r - 2, gcy - r - 2))

        # Check for per-instance animation override
        anim_name = getattr(self, "animation", None)
        if anim_name:
            from engine.systems.animation import get_anim_sprite
            sprite_id = get_anim_sprite(anim_name) or anim_name
            sprite = obtener_sprite(sprite_id)
            if sprite:
                _draw_glow(anim_name, ox, oy)
                pantalla.blit(sprite, (ox, oy))
                return

        if self.tipo == COMIDA_NORMAL:
            sprite = obtener_sprite("comida_normal")
            if sprite:
                pantalla.blit(sprite, (ox, oy))
            else:
                pygame.draw.circle(pantalla, (220, 30, 30), (cx, cy+1), 7)
                pygame.draw.circle(pantalla, NEGRO, (cx, cy+1), 7, 1)
                pygame.draw.line(pantalla, (80, 50, 20), (cx, cy-6), (cx, cy-9), 2)
                pygame.draw.ellipse(pantalla, (50, 180, 50), (cx+1, cy-9, 5, 3))

        elif self.tipo == COMIDA_ESPECIAL:
            from engine.systems.animation import get_anim_sprite, get_anim_glow
            sprite_id = get_anim_sprite("comida_dorada") or "comida_dorada"
            sprite = obtener_sprite(sprite_id)
            if sprite:
                _draw_glow("comida_dorada", ox, oy)
                pantalla.blit(sprite, (ox, oy))
            else:
                pygame.draw.circle(pantalla, (255, 215, 0), (cx, cy+1), 7)
                pygame.draw.circle(pantalla, (200, 160, 0), (cx, cy+1), 7, 1)
                pygame.draw.line(pantalla, (80, 50, 20), (cx, cy-6), (cx, cy-9), 2)
                pygame.draw.ellipse(pantalla, (180, 200, 50), (cx+1, cy-9, 5, 3))

        elif self.tipo == COMIDA_MANA:
            sprite = obtener_sprite("comida_mana")
            if sprite:
                pantalla.blit(sprite, (ox, oy))
            else:
                pygame.draw.ellipse(pantalla, (140, 30, 140), (ox+4, oy+7, 12, 9))
                pygame.draw.ellipse(pantalla, NEGRO, (ox+4, oy+7, 12, 9), 1)
                pygame.draw.circle(pantalla, NEGRO, (ox+9, oy+10), 1)
                pygame.draw.circle(pantalla, (200, 120, 160), (ox+13, oy+11), 1)

    def get_posicion(self):
        return [self.x, self.y]

    @staticmethod
    def generar(snake_body, ancho, alto, prob_mana=0.15, prob_especial=0.05):
        rand = random.random()
        if rand < prob_especial:
            tipo = COMIDA_ESPECIAL
        elif rand < prob_especial + prob_mana:
            tipo = COMIDA_MANA
        else:
            tipo = COMIDA_NORMAL

        MARGEN = TAMANO_CELDA * 2

        intentos = 0
        while intentos < 100:
            x = random.randrange(MARGEN, ancho - MARGEN, TAMANO_CELDA)
            y = random.randrange(MARGEN, alto - MARGEN, TAMANO_CELDA)
            if [x, y] not in snake_body:
                return Food(x, y, tipo)
            intentos += 1
        return Food(ANCHO // 2, ALTO // 2, COMIDA_NORMAL)

    @staticmethod
    def generar_en_posicion(x, y, tipo=None):
        # Asegurar que la posición sea múltiplo de TAMANO_CELDA
        x = (x // TAMANO_CELDA) * TAMANO_CELDA
        y = (y // TAMANO_CELDA) * TAMANO_CELDA
        if tipo is None:
            rand = random.random()
            if rand < 0.05:
                tipo = COMIDA_ESPECIAL
            elif rand < 0.20:
                tipo = COMIDA_MANA
            else:
                tipo = COMIDA_NORMAL
        return Food(x, y, tipo)

    @staticmethod
    def generar_cerca(snake_body, posicion_referencia, tipo=None, distancia_max=10):
        """Genera comida cerca de una posición de referencia (distancia_max en celdas)"""
        from engine.utils.helpers import generar_comida_cerca
        x, y = generar_comida_cerca(snake_body, posicion_referencia, distancia_max)
        if tipo is None:
            rand = random.random()
            if rand < 0.05:
                tipo = COMIDA_ESPECIAL
            elif rand < 0.20:
                tipo = COMIDA_MANA
            else:
                tipo = COMIDA_NORMAL
        return Food(x, y, tipo)
