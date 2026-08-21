"""Tests unitarios para editor.map_viewport — zoom, scroll, coordenadas."""

from __future__ import annotations

import pytest

from editor.map_viewport import MapViewport


# ── Mock de pygame.Rect ────────────────────────────────────

class FakeRect:
    """Mock ligero de pygame.Rect para tests sin dependencia gráfica."""

    def __init__(self, x: int = 0, y: int = 0, w: int = 800, h: int = 600):
        self.x = x
        self.y = y
        self.width = w
        self.height = h

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height


# ── Init y tile_size ───────────────────────────────────────

class TestMapViewportInit:
    def test_default_values(self):
        vp = MapViewport()
        assert vp.zoom == 1.0
        assert vp.scroll_x == 0
        assert vp.scroll_y == 0
        assert vp.show_grid is True
        assert vp.tile_size == 20

    def test_custom_base_tile_size(self):
        vp = MapViewport(base_tile_size=32)
        assert vp.tile_size == 32

    def test_tile_size_min_limit(self):
        vp = MapViewport(base_tile_size=1)
        vp.zoom = 0.25
        assert vp.tile_size >= 4  # minimum enforced


# ── Zoom ───────────────────────────────────────────────────

class TestZoom:
    def test_zoom_in(self):
        vp = MapViewport()
        vp.zoom_in()
        assert vp.zoom == 1.25

    def test_zoom_out(self):
        vp = MapViewport()
        vp.zoom_out()
        assert vp.zoom == 0.75

    def test_zoom_in_max(self):
        vp = MapViewport()
        vp.zoom = 3.75
        vp.zoom_in()
        assert vp.zoom == 4.0
        vp.zoom_in()
        assert vp.zoom == 4.0  # capped

    def test_zoom_out_min(self):
        vp = MapViewport()
        vp.zoom = 0.50
        vp.zoom_out()
        assert vp.zoom == 0.25
        vp.zoom_out()
        assert vp.zoom == 0.25  # capped

    def test_zoom_label(self):
        vp = MapViewport()
        assert vp.zoom_label() == "100%"
        vp.zoom = 2.0
        assert vp.zoom_label() == "200%"
        vp.zoom = 0.5
        assert vp.zoom_label() == "50%"

    def test_tile_size_scales_with_zoom(self):
        vp = MapViewport(base_tile_size=20)
        vp.zoom = 2.0
        assert vp.tile_size == 40
        vp.zoom = 0.5
        assert vp.tile_size == 10

    def test_set_base_tile_size(self):
        vp = MapViewport()
        vp.set_base_tile_size(16)
        assert vp.tile_size == 16


# ── Coordenadas screen↔grid ────────────────────────────────

class TestCoordinates:
    def test_screen_to_grid_basic(self):
        vp = MapViewport()
        rect = FakeRect(0, 0, 800, 600)
        gx, gy = vp.screen_to_grid(40, 60, rect)
        assert gx == 2  # 40 / 20
        assert gy == 3  # 60 / 20

    def test_screen_to_grid_with_offset(self):
        vp = MapViewport()
        vp.scroll_x = 100
        vp.scroll_y = 50
        rect = FakeRect(100, 50, 800, 600)
        gx, gy = vp.screen_to_grid(140, 110, rect)
        assert gx == 7  # (140 - 100 + 100) // 20
        assert gy == 5  # (110 - 50 + 50) // 20

    def test_grid_to_screen_basic(self):
        vp = MapViewport()
        rect = FakeRect(0, 0, 800, 600)
        sx, sy = vp.grid_to_screen(2, 3, rect)
        assert sx == 40  # 2 * 20
        assert sy == 60  # 3 * 20

    def test_grid_to_screen_with_scroll(self):
        vp = MapViewport()
        vp.scroll_x = 100
        vp.scroll_y = 50
        rect = FakeRect(0, 0, 800, 600)
        sx, sy = vp.grid_to_screen(5, 5, rect)
        assert sx == 0   # 5 * 20 - 100 + 0
        assert sy == 50  # 5 * 20 - 50 + 0

    def test_roundtrip_conversion(self):
        vp = MapViewport()
        rect = FakeRect(100, 50, 800, 600)
        original_gx, original_gy = 7, 12
        sx, sy = vp.grid_to_screen(original_gx, original_gy, rect)
        gx, gy = vp.screen_to_grid(sx, sy, rect)
        assert gx == original_gx
        assert gy == original_gy

    def test_screen_to_grid_negative(self):
        vp = MapViewport()
        rect = FakeRect(0, 0, 800, 600)
        gx, gy = vp.screen_to_grid(-10, -10, rect)
        assert gx < 0
        assert gy < 0

    def test_zoom_affects_coordinates(self):
        vp = MapViewport(base_tile_size=20)
        vp.zoom = 2.0
        rect = FakeRect(0, 0, 800, 600)
        gx, gy = vp.screen_to_grid(80, 120, rect)
        assert gx == 2  # 80 / 40
        assert gy == 3  # 120 / 40


# ── Content size ───────────────────────────────────────────

class TestContentSize:
    def test_content_size_basic(self):
        vp = MapViewport()

        class FakeLayer:
            def __init__(self, a, al):
                self.ancho = a
                self.alto = al

        class FakeTab:
            layers = {0: FakeLayer(50, 40)}

        w, h = vp.content_size(FakeTab())
        assert w == 1000  # 50 * 20
        assert h == 800   # 40 * 20

    def test_content_size_with_zoom(self):
        vp = MapViewport()
        vp.zoom = 2.0

        class FakeLayer:
            def __init__(self, a, al):
                self.ancho = a
                self.alto = al

        class FakeTab:
            layers = {0: FakeLayer(50, 40)}

        w, h = vp.content_size(FakeTab())
        assert w == 2000  # 50 * 40
        assert h == 1600  # 40 * 40

    def test_content_size_multiple_layers(self):
        vp = MapViewport()

        class FakeLayer:
            def __init__(self, a, al):
                self.ancho = a
                self.alto = al

        class FakeTab:
            layers = {0: FakeLayer(50, 40), 1: FakeLayer(30, 60)}

        w, h = vp.content_size(FakeTab())
        assert w == 1000  # max(50, 30) * 20
        assert h == 1200  # max(40, 60) * 20

    def test_content_size_empty_layers(self):
        vp = MapViewport()

        class FakeTab:
            layers = {}

        w, h = vp.content_size(FakeTab())
        assert w == 0
        assert h == 0
