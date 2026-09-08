import pygame
from engine.configs.constants import ANCHO, ALTO
BLANCO = (255, 255, 255)


COLOR_FONDO = (20, 20, 30)
COLOR_BORDE = (100, 100, 140)
COLOR_TEXTO = BLANCO
COLOR_SELECCION = (60, 60, 90)
PADDING = 12
MARGEN_Y = 80
ANCHO_CAJA = 500
ALTO_OPCION = 40


class ChoiceBox:
    """Renders a list of selectable options. Stateless — reads from game state."""

    def dibujar(self, pantalla, opciones, seleccion, pregunta=""):
        if not opciones:
            return
        total_alto = len(opciones) * (ALTO_OPCION + 4) + PADDING * 2
        if pregunta:
            total_alto += ALTO_OPCION + 4
        cx = (ANCHO - ANCHO_CAJA) // 2
        cy = MARGEN_Y
        rect = pygame.Rect(cx, cy, ANCHO_CAJA, total_alto)
        pygame.draw.rect(pantalla, COLOR_FONDO, rect, border_radius=8)
        pygame.draw.rect(pantalla, COLOR_BORDE, rect, 2, border_radius=8)

        y_offset = cy + PADDING
        if pregunta:
            fuente_p = pygame.font.SysFont("Arial", 18)
            lbl_p = fuente_p.render(pregunta, True, (220, 220, 120))
            pantalla.blit(lbl_p, (cx + 10, y_offset))
            y_offset += ALTO_OPCION + 4

        for idx, opcion in enumerate(opciones):
            texto = opcion.get("texto", f"Opción {idx}")
            oy_local = y_offset + idx * (ALTO_OPCION + 4)
            orect = pygame.Rect(cx + 8, oy_local, ANCHO_CAJA - 16, ALTO_OPCION)
            if idx == seleccion:
                pygame.draw.rect(pantalla, COLOR_SELECCION, orect, border_radius=6)
            fuente = pygame.font.SysFont("Arial", 20)
            lbl = fuente.render(texto, True, COLOR_TEXTO)
            pantalla.blit(lbl, (orect.x + 10, orect.y + (ALTO_OPCION - lbl.get_height()) // 2))

        instr = pygame.font.SysFont("Arial", 14).render(
            "↑↓ Navegar  |  ENTER Confirmar", True, (140, 140, 160))
        pantalla.blit(instr, (cx + 10, cy + total_alto + 8))
