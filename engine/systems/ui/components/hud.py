import pygame
from engine.configs import *
from engine.runtime.renderer import load_sprite


class HUD:
    def __init__(self, fuente, fuente_grande, fuente_pequena):
        self.fuente = fuente
        self.fuente_grande = fuente_grande
        self.fuente_pequena = fuente_pequena

    def draw(self, pantalla, snake, mensaje=None, monedas=None):
        self._draw_escamas(pantalla, snake, monedas)
        self._draw_deuda(pantalla, snake)
        self._draw_controles(pantalla)
        if mensaje:
            self._draw_mensaje(pantalla, mensaje)

    def _icono_moneda(self, monedas):
        if monedas is None:
            return None
        principal = getattr(monedas, "principal", None)
        p = principal() if callable(principal) else None
        for mid in ("escamas", p):
            if not mid:
                continue
            d = monedas.definir(mid)
            if d and d.get("icono"):
                return d["icono"]
        return None

    def _draw_escamas(self, pantalla, snake, monedas=None):
        esc = snake.get_escamas()
        ex = ANCHO - 80
        ey = 14

        if esc > 0:
            c_esc = (210, 185, 100)
            c_brillo = (255, 230, 150)
        else:
            c_esc = (80, 75, 55)
            c_brillo = (110, 100, 70)

        bg = pygame.Surface((70, 30), pygame.SRCALPHA)
        bg.fill((5, 10, 18, 180))
        pantalla.blit(bg, (ex - 10, ey - 12))
        pygame.draw.rect(pantalla, (40, 55, 70), (ex - 10, ey - 12, 70, 30), 1)

        icono = self._icono_moneda(monedas)
        sprite = load_sprite(icono) if icono else None
        if sprite:
            ancho_d = 18
            escala = min(ancho_d / sprite.get_width(), ancho_d / sprite.get_height())
            sw = max(1, int(sprite.get_width() * escala))
            sh = max(1, int(sprite.get_height() * escala))
            s = pygame.transform.scale(sprite, (sw, sh))
            pantalla.blit(s, (ex - sw // 2, ey - sh // 2))
        else:
            pygame.draw.polygon(pantalla, c_esc, [
                (ex, ey - 8), (ex + 7, ey), (ex, ey + 8), (ex - 7, ey)
            ])
            pygame.draw.polygon(pantalla, c_brillo, [
                (ex, ey - 8), (ex + 7, ey), (ex, ey + 8), (ex - 7, ey)
            ], 2)
            pygame.draw.polygon(pantalla, (255, 245, 200), [
                (ex, ey - 6), (ex + 4, ey), (ex, ey + 2)
            ])

        num_surf = self.fuente.render(f"x{esc}", True, c_esc)
        pantalla.blit(num_surf, (ex + 14, ey - 7))

    def _draw_deuda(self, pantalla, snake):
        if snake.tiene_deuda():
            deuda_texto = f"DEUDA: {snake.get_deuda_restante()} frutas para saldar"
            texto_deuda = self.fuente.render(deuda_texto, True, ROJO)
            pantalla.blit(texto_deuda, (10, 35))

    def _draw_controles(self, pantalla):
        texto_controles = self.fuente_pequena.render(
            "Flechas: Mover | P: Pausa | T: Trueque | I: Inventario", True, GRIS)
        pantalla.blit(texto_controles, (10, ALTO - 55))

    def _draw_mensaje(self, pantalla, mensaje):
        sombra = self.fuente.render(mensaje, True, (10, 15, 5))
        texto_mensaje = self.fuente.render(mensaje, True, (220, 190, 120))
        rect_s = sombra.get_rect(center=(ANCHO//2 + 2, 62))
        rect = texto_mensaje.get_rect(center=(ANCHO//2, 60))
        pantalla.blit(sombra, rect_s)
        pantalla.blit(texto_mensaje, rect)
