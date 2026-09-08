from engine.systems.ui.components.game_over import GameOverScreen
from engine.systems.ui.components.hud import HUD
from engine.systems.ui.components.inventory_menu import InventoryMenu
from engine.systems.ui.components.pause_menu import PauseMenu
from engine.systems.ui.components.trade_menu import TradeMenu


class UI:
    def __init__(self):
        self.fuente = self._cargar_fuente(20)
        self.fuente_grande = self._cargar_fuente(28)
        self.fuente_pequena = self._cargar_fuente(14)

        self._hud = HUD(self.fuente, self.fuente_grande, self.fuente_pequena)
        self._trade = TradeMenu(self.fuente, self.fuente_grande)
        self._game_over = GameOverScreen(self.fuente, self.fuente_grande, self.fuente_pequena)
        self._pause = PauseMenu(self.fuente, self.fuente_grande, self.fuente_pequena)
        self._inventory = InventoryMenu(self.fuente, self.fuente_grande, self.fuente_pequena)

    def _cargar_fuente(self, tam):
        import pygame
        for nombre in ["Georgia", "Palatino Linotype", "Book Antiqua", None]:
            try:
                if nombre:
                    f = pygame.font.SysFont(nombre, tam)
                else:
                    f = pygame.font.Font(None, tam)
                if f and f.render("A", True, (0, 0, 0)).get_width() > 0:
                    return f
            except Exception:
                continue
        return pygame.font.Font(None, tam)

    def dibujar(self, pantalla, snake, comida=None, mensaje=None, monedas=None):
        self._hud.draw(pantalla, snake, mensaje, monedas)

    def mostrar_menu_trueque(self, pantalla, snake):
        self._trade.draw(pantalla, snake)

    def mostrar_game_over(self, pantalla, snake, estado=None):
        self._game_over.draw(pantalla, snake, estado)

    def mostrar_pausa(self, pantalla):
        self._pause.draw(pantalla)

    def mostrar_inventario(self, pantalla, estado):
        self._inventory.draw(pantalla, estado)
