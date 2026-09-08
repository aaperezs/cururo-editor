import pygame
from engine.services.text_service import TextService


class TestTextService:
    def setup_method(self):
        self.ts = TextService(pool_size=16)

    def test_spawn_adds_to_pool(self):
        self.ts.spawn("+1", 100, 100, 30, (0, 255, 0))
        assert len(self.ts._pool) == 1

    def test_spawn_returns_floating_text(self):
        ft = self.ts.spawn("test", 10, 10, 10)
        assert ft.texto == "test"
        assert ft.active is True

    def test_update_decrements_timer(self):
        ft = self.ts.spawn("x", 0, 0, 5)
        self.ts.update()
        assert ft.timer == 4

    def test_update_removes_expired(self):
        self.ts.spawn("x", 0, 0, 1)
        self.ts.update()
        assert len(self.ts._pool) == 0

    def test_update_moves_text(self):
        ft = self.ts.spawn("x", 100, 100, 10, dx=1, dy=-2)
        self.ts.update()
        assert ft.x == 101
        assert ft.y == 98

    def test_clear_removes_all(self):
        self.ts.spawn("a", 0, 0, 10)
        self.ts.spawn("b", 0, 0, 10)
        self.ts.clear()
        assert len(self.ts._pool) == 0

    def test_max_pool_size(self):
        ts = TextService(pool_size=3)
        for i in range(5):
            ts.spawn(str(i), 0, 0, 10)
        assert len(ts._pool) == 3

    def test_draw_does_not_crash(self):
        surf = pygame.Surface((800, 600))
        self.ts.spawn("test", 100, 100, 10)
        self.ts.draw(surf)

    def test_font_caching(self):
        f1 = self.ts._get_font(16)
        f2 = self.ts._get_font(16)
        assert f1 is f2

    def test_different_font_sizes(self):
        f1 = self.ts._get_font(12)
        f2 = self.ts._get_font(20)
        assert f1 is not f2

