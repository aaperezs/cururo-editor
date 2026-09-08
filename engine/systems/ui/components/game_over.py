import random

import pygame
from engine.configs import ALTO, ANCHO


class GameOverScreen:
    def __init__(self, fuente, fuente_grande, fuente_pequena):
        self.fuente = fuente
        self.fuente_grande = fuente_grande
        self.fuente_pequena = fuente_pequena

    def draw(self, pantalla, snake, estado=None):
        overlay = pygame.Surface((ANCHO, ALTO))
        overlay.set_alpha(200)
        overlay.fill((5, 8, 25))
        pantalla.blit(overlay, (0, 0))

        m = 30
        w, h = ANCHO - 2*m, ALTO - 2*m

        marco_ext = pygame.Rect(m, m, w, h)
        pygame.draw.rect(pantalla, (15, 30, 55), marco_ext)
        pygame.draw.rect(pantalla, (30, 55, 85), marco_ext, 2)
        for vy in range(marco_ext.top + 4, marco_ext.bottom, 8):
            pygame.draw.line(pantalla, (20, 40, 65), (marco_ext.left + 2, vy), (marco_ext.right - 2, vy), 1)

        int_rect = marco_ext.inflate(-12, -12)
        pygame.draw.rect(pantalla, (8, 15, 35), int_rect)
        pygame.draw.rect(pantalla, (20, 40, 65), int_rect, 1)
        pygame.draw.line(pantalla, (20, 40, 65), int_rect.topleft, int_rect.topright, 1)
        pygame.draw.line(pantalla, (20, 40, 65), int_rect.topleft, int_rect.bottomleft, 1)

        col_hielo = (80, 130, 180)
        for cx, cy, flip_x, flip_y in [
            (int_rect.left + 8, int_rect.top + 8, 1, 1),
            (int_rect.right - 8, int_rect.top + 8, -1, 1),
            (int_rect.left + 8, int_rect.bottom - 8, 1, -1),
            (int_rect.right - 8, int_rect.bottom - 8, -1, -1),
        ]:
            pts = [(cx, cy), (cx + 8 * flip_x, cy), (cx + 4 * flip_x, cy + 6 * flip_y)]
            pygame.draw.polygon(pantalla, col_hielo, pts)
            pts2 = [(cx, cy), (cx, cy + 8 * flip_y), (cx + 4 * flip_x, cy + 6 * flip_y)]
            pygame.draw.polygon(pantalla, col_hielo, pts2)

        tit_rect = pygame.Rect(int_rect.centerx - 160, int_rect.centery - 70, 320, 50)
        pygame.draw.rect(pantalla, (15, 30, 50), tit_rect)
        pygame.draw.rect(pantalla, (60, 100, 140), tit_rect, 2)
        titulo = self.fuente_grande.render("GAME OVER", True, (150, 200, 240))
        tit_rect_txt = titulo.get_rect(center=tit_rect.center)
        pantalla.blit(titulo, tit_rect_txt)

        stats = self.fuente.render(f"Escamas: {snake.get_escamas()}  |  Longitud: {snake.get_longitud()}", True, (120, 150, 180))
        stats_rect = stats.get_rect(center=(ANCHO//2, int_rect.centery + 15))
        pantalla.blit(stats, stats_rect)

        death_text = getattr(estado, 'death_cause', None) if estado else None
        if death_text:
            causa = self.fuente.render(f"{death_text}", True, (200, 100, 100))
            causa_rect = causa.get_rect(center=(ANCHO//2, int_rect.centery + 45))
            pantalla.blit(causa, causa_rect)
        inst = self.fuente.render("R: Renacer   ESC: Descansar", True, (60, 90, 120))
        inst_rect = inst.get_rect(center=(ANCHO//2, int_rect.centery + 50))
        pantalla.blit(inst, inst_rect)

        for _ in range(15):
            nx = random.randint(int_rect.left + 10, int_rect.right - 10)
            ny = random.randint(int_rect.top + 10, int_rect.bottom - 10)
            nw = random.randint(20, 60)
            nh = random.randint(3, 8)
            fog = pygame.Surface((nw, nh), pygame.SRCALPHA)
            fog.set_alpha(random.randint(15, 40))
            fog.fill((120, 160, 200))
            pantalla.blit(fog, (nx, ny))
