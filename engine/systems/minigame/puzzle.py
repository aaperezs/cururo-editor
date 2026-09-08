import random
import pygame

from .base import MiniJuegoBase


class PuzzleMiniJuego(MiniJuegoBase):
    def __init__(self, config):
        super().__init__(config)
        self.grid = tuple(config.get("grid", [3, 3]))
        self._rows, self._cols = self.grid
        self._tile_size = config.get("tile_size", 80)
        self._gap = 4
        self._c_width = config.get("canvas_w", 800)
        self._c_height = config.get("canvas_h", 600)
        self._board = []
        self._empty = (self._rows - 1, self._cols - 1)
        self._moves = 0
        self._font = None
        self._solved = False
        self._offset_x = 0
        self._offset_y = 0

    def iniciar(self):
        super().iniciar()
        total = self._rows * self._cols
        self._board = list(range(total))
        random.shuffle(self._board)
        while not self._esoluble(self._board) or self._board == list(range(total)):
            random.shuffle(self._board)
        self._empty = (self._rows - 1, self._cols - 1)
        self._moves = 0
        self._solved = False
        bw = self._cols * (self._tile_size + self._gap)
        bh = self._rows * (self._tile_size + self._gap)
        self._offset_x = (self._c_width - bw) // 2
        self._offset_y = (self._c_height - bh) // 2

    def _esoluble(self, board):
        inversions = 0
        flat = [x for x in board if x != 0]
        for i in range(len(flat)):
            for j in range(i + 1, len(flat)):
                if flat[i] > flat[j]:
                    inversions += 1
        if self._rows % 2 == 0:
            blank_row = board.index(0) // self._cols
            return (inversions + blank_row) % 2 == 0
        return inversions % 2 == 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            r, c = self._empty
            if event.key == pygame.K_UP and r < self._rows - 1:
                self._swap((r, c), (r + 1, c))
            elif event.key == pygame.K_DOWN and r > 0:
                self._swap((r, c), (r - 1, c))
            elif event.key == pygame.K_LEFT and c < self._cols - 1:
                self._swap((r, c), (r, c + 1))
            elif event.key == pygame.K_RIGHT and c > 0:
                self._swap((r, c), (r, c - 1))
        return False

    def _swap(self, empty_pos, tile_pos):
        er, ec = empty_pos
        tr, tc = tile_pos
        ei = er * self._cols + ec
        ti = tr * self._cols + tc
        self._board[ei], self._board[ti] = self._board[ti], self._board[ei]
        self._empty = (tr, tc)
        self._moves += 1
        if self._board == list(range(self._rows * self._cols)):
            self._solved = True
            self._terminado = True

    def actualizar(self, dt_ms):
        return self._terminado

    def dibujar(self, surface):
        surface.fill((20, 25, 35))
        if not self._font:
            self._font = pygame.font.SysFont("Arial", 18)
        info = self._font.render(f"Movimientos: {self._moves}", True, (200, 220, 240))
        surface.blit(info, (10, 10))
        ts = self._tile_size
        gap = self._gap
        ox, oy = self._offset_x, self._offset_y
        board_w = self._cols * (ts + gap)
        board_h = self._rows * (ts + gap)
        pygame.draw.rect(surface, (40, 45, 55), (ox - gap, oy - gap, board_w + gap, board_h + gap))
        for i, val in enumerate(self._board):
            if val == 0:
                continue
            r = i // self._cols
            c = i % self._cols
            x = ox + c * (ts + gap)
            y = oy + r * (ts + gap)
            color = (60 + (val * 10) % 80, 80 + (val * 15) % 60, 120 + (val * 8) % 40)
            pygame.draw.rect(surface, color, (x, y, ts, ts))
            pygame.draw.rect(surface, (180, 190, 200), (x, y, ts, ts), 2)
            label = self._font.render(str(val), True, (255, 255, 255))
            surface.blit(label, (x + ts // 2 - label.get_width() // 2, y + ts // 2 - label.get_height() // 2))
        if self._solved:
            done = pygame.font.SysFont("Arial", 30).render(
                "Ordenado!", True, (100, 220, 100)
            )
            surface.blit(done, (self._c_width // 2 - done.get_width() // 2, 50))
