import pygame
from engine.configs import ALTO, ANCHO
from engine.systems.ui.components.base import dibujar_marco_madera, dibujar_runas, panel_tallado


class PauseMenu:
    def __init__(self, fuente, fuente_grande, fuente_pequena):
        self.fuente = fuente
        self.fuente_grande = fuente_grande
        self.fuente_pequena = fuente_pequena

    def draw(self, pantalla):
        overlay = pygame.Surface((ANCHO, ALTO))
        overlay.set_alpha(180)
        overlay.fill((10, 30, 8))
        pantalla.blit(overlay, (0, 0))

        m = 30
        w, h = ANCHO - 2*m, ALTO - 2*m

        marco_ext = pygame.Rect(m, m, w, h)
        dibujar_marco_madera(pantalla, marco_ext, (60, 40, 20), (80, 55, 30))

        int_rect = marco_ext.inflate(-12, -12)
        panel_tallado(pantalla, int_rect, (15, 38, 12), (35, 60, 25))

        col_runa = (100, 75, 40)
        dibujar_runas(pantalla, int_rect.left + 15, int_rect.top + 15, col_runa)
        dibujar_runas(pantalla, int_rect.right - 15, int_rect.top + 15, col_runa)
        dibujar_runas(pantalla, int_rect.left + 15, int_rect.bottom - 15, col_runa)
        dibujar_runas(pantalla, int_rect.right - 15, int_rect.bottom - 15, col_runa)

        tit_rect = pygame.Rect(int_rect.centerx - 140, int_rect.centery - 40, 280, 50)
        panel_tallado(pantalla, tit_rect, (80, 55, 30), (120, 80, 45))
        titulo = self.fuente_grande.render("PAUSA", True, (220, 190, 120))
        tit_rect_txt = titulo.get_rect(center=tit_rect.center)
        pantalla.blit(titulo, tit_rect_txt)

        inst = self.fuente_pequena.render("P: Reanudar   ESC: Salir", True, (100, 130, 80))
        inst_rect = inst.get_rect(center=(ANCHO//2, int_rect.centery + 30))
        pantalla.blit(inst, inst_rect)
