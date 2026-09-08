import pygame


def dibujar_runas(pantalla, x, y, color):
    pygame.draw.line(pantalla, color, (x, y-4), (x+3, y), 1)
    pygame.draw.line(pantalla, color, (x+3, y), (x, y+4), 1)
    pygame.draw.line(pantalla, color, (x, y-4), (x-3, y), 1)
    pygame.draw.line(pantalla, color, (x-3, y), (x, y+4), 1)


def dibujar_marco_madera(pantalla, rect, color_base, color_interno):
    pygame.draw.rect(pantalla, color_base, rect)
    pygame.draw.rect(pantalla, color_interno, rect, 2)
    for vy in range(rect.top + 4, rect.bottom, 6):
        pygame.draw.line(pantalla, color_interno, (rect.left + 2, vy), (rect.right - 2, vy), 1)


def panel_tallado(pantalla, rect, color_piedra, color_borde):
    pygame.draw.rect(pantalla, color_piedra, rect)
    pygame.draw.rect(pantalla, color_borde, rect, 1)
    pygame.draw.line(pantalla, color_borde, rect.topleft, rect.topright, 1)
    pygame.draw.line(pantalla, color_borde, rect.topleft, rect.bottomleft, 1)
    oscuro = tuple(max(0, c-30) for c in color_borde[:3])
    pygame.draw.line(pantalla, oscuro, rect.bottomleft, rect.bottomright, 1)
    pygame.draw.line(pantalla, oscuro, rect.topright, rect.bottomright, 1)
