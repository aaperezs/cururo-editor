import pygame
from engine.configs import *
from engine.display import present as _display_present


class TradeMenu:
    def __init__(self, fuente, fuente_grande):
        self.fuente = fuente
        self.fuente_grande = fuente_grande

    def draw(self, pantalla, snake):
        overlay = pygame.Surface((ANCHO, ALTO))
        overlay.set_alpha(180)
        overlay.fill(NEGRO)
        pantalla.blit(overlay, (0, 0))

        titulo = self.fuente_grande.render("ALTAR DE TRUEQUE", True, DORADO)
        titulo_rect = titulo.get_rect(center=(ANCHO//2, 100))
        pantalla.blit(titulo, titulo_rect)

        esc = snake.get_escamas()
        info = self.fuente.render(f"Escamas: {esc}  |  Longitud: {snake.get_longitud()}", True, BLANCO)
        info_rect = info.get_rect(center=(ANCHO//2, 150))
        pantalla.blit(info, info_rect)

        opciones = [
            ("1", "Vender 1 segmento"),
            ("3", "Vender 3 segmentos"),
            ("5", "Vender 5 segmentos"),
            ("D", "Pedir prestado (deuda)"),
            ("ESC", "Salir del trueque"),
        ]

        y_offset = 200
        for tecla, desc in opciones:
            color = GRIS if tecla == "D" and snake.tiene_deuda() else BLANCO
            texto = self.fuente.render(f"[{tecla}] {desc}", True, color)
            pantalla.blit(texto, (ANCHO//2 - 100, y_offset))
            y_offset += 35

        if snake.tiene_deuda():
            deuda = self.fuente.render(f"DEUDA ACTIVA: {snake.get_deuda_restante()} frutas restantes", True, ROJO)
            deuda_rect = deuda.get_rect(center=(ANCHO//2, ALTO - 50))
            pantalla.blit(deuda, deuda_rect)

        _display_present()

