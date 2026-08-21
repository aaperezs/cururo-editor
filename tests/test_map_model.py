"""Tests unitarios para editor.map_model — serialización, pintura, multi-tile, spawn."""

import json
import os
import tempfile
import pytest

from editor.map_model import (
    grid_to_json, json_to_grid,
    paint_tile, erase_tile, flood_fill,
    paint_multi_tile, is_multi_tile_anchor, erase_multi_tile,
    save_layer, load_layer,
    save_stacks, load_stacks,
    save_multi_tiles, load_multi_tiles,
    save_meta, load_meta,
    scan_spawn_from_grid,
)


# ── Fake objects ───────────────────────────────────────────

class FakeLayer:
    def __init__(self, ancho=10, alto=10):
        self.grid = {}
        self.ancho = ancho
        self.alto = alto
        self.visible = True
        self.opacity = 100


class FakeTab:
    def __init__(self, ancho=10, alto=10):
        self.map_id = "test_map"
        self.dirty = False
        self.layers = {0: FakeLayer(ancho, alto)}
        self.stacks = {}
        self.multi_tiles = {}
        self.active_z = 0
        self.spawn_pos: tuple[int, int] | None = None
        self.spawn_z = 0
        self.undo_stack = []
        self.redo_stack = []

    @property
    def layer_order(self):
        return sorted(self.layers.keys())

    def push_undo(self):
        self.undo_stack.append({
            "layers": {z: type('L', (), {'grid': dict(l.grid), 'ancho': l.ancho, 'alto': l.alto})() for z, l in self.layers.items()},
            "stacks": dict(self.stacks),
            "multi_tiles": dict(self.multi_tiles),
            "active_z": self.active_z,
            "spawn_pos": self.spawn_pos,
            "spawn_z": self.spawn_z,
        })
        self.redo_stack.clear()
        self.dirty = True


def fake_get_element(element_id):
    """Fake get_element for multi-tile tests."""
    if element_id == "multi_tree":
        return {
            "sprite_id": "tree",
            "behavior": "multi_tile",
            "multi_tile": True,
            "properties": {"tile_rows": 2, "tile_cols": 2},
        }
    return None


# ── Serialización JSON ─────────────────────────────────────

class TestGridJson:
    def test_roundtrip(self):
        grid = {(0, 0): "pasto", (1, 0): "pared", (0, 1): "roca"}
        text = grid_to_json(grid, 10, 8)
        data = json.loads(text)
        assert data["version"] == 2
        assert data["ancho"] == 10
        assert data["alto"] == 8

        result_grid, ancho, alto = json_to_grid(text)
        assert ancho == 10
        assert alto == 8
        assert result_grid[(0, 0)] == "pasto"
        assert result_grid[(1, 0)] == "pared"
        assert result_grid[(0, 1)] == "roca"

    def test_empty_grid(self):
        text = grid_to_json({}, 5, 5)
        result_grid, ancho, alto = json_to_grid(text)
        assert result_grid == {}
        assert ancho == 5
        assert alto == 5


# ── Pintura y borrado ──────────────────────────────────────

class TestPaintTile:
    def test_paint(self):
        ls = FakeLayer()
        paint_tile(ls, 3, 4, "pasto")
        assert ls.grid[(3, 4)] == "pasto"

    def test_overwrite(self):
        ls = FakeLayer()
        paint_tile(ls, 0, 0, "pasto")
        paint_tile(ls, 0, 0, "pared")
        assert ls.grid[(0, 0)] == "pared"


class TestEraseTile:
    def test_erase_existing(self):
        tab = FakeTab()
        ls = tab.layers[0]
        ls.grid[(2, 3)] = "pasto"
        result = erase_tile(tab, ls, 2, 3)
        assert result is True
        assert (2, 3) not in ls.grid

    def test_erase_nonexistent(self):
        tab = FakeTab()
        ls = tab.layers[0]
        result = erase_tile(tab, ls, 9, 9)
        assert result is False

    def test_erase_updates_spawn(self):
        tab = FakeTab()
        ls = tab.layers[0]
        ls.grid[(5, 5)] = "inicio"
        tab.spawn_pos = (5, 5)
        tab.spawn_z = 0
        erase_tile(tab, ls, 5, 5)
        assert tab.spawn_pos is None
        assert tab.spawn_z == 0


class TestFloodFill:
    def test_fill_connected(self):
        ls = FakeLayer(5, 5)
        for x in range(3):
            ls.grid[(x, 0)] = "pasto"
        modified = flood_fill(ls, 0, 0, "roca")
        assert len(modified) == 3
        for x in range(3):
            assert ls.grid[(x, 0)] == "roca"

    def test_fill_no_change_same_type(self):
        ls = FakeLayer()
        ls.grid[(0, 0)] = "pasto"
        modified = flood_fill(ls, 0, 0, "pasto")
        assert len(modified) == 0

    def test_fill_respects_bounds(self):
        ls = FakeLayer(3, 3)
        for x in range(3):
            for y in range(3):
                ls.grid[(x, y)] = "pasto"
        modified = flood_fill(ls, 0, 0, "roca")
        assert len(modified) == 9


# ── Multi-tile ─────────────────────────────────────────────

class TestMultiTile:
    def test_paint(self):
        tab = FakeTab()
        ls = tab.layers[0]
        painted = paint_multi_tile(tab, ls, 0, 0, "multi_tree", fake_get_element)
        assert len(painted) == 4
        assert (0, 0) in ls.grid
        assert (1, 1) in ls.grid
        assert (0, 0, 0) in tab.multi_tiles

    def test_is_anchor(self):
        tab = FakeTab()
        ls = tab.layers[0]
        paint_multi_tile(tab, ls, 2, 2, "multi_tree", fake_get_element)
        assert is_multi_tile_anchor(tab, 2, 2, 0, fake_get_element) == (2, 2, 0)
        assert is_multi_tile_anchor(tab, 3, 3, 0, fake_get_element) == (2, 2, 0)
        assert is_multi_tile_anchor(tab, 5, 5, 0, fake_get_element) is None

    def test_erase(self):
        tab = FakeTab()
        ls = tab.layers[0]
        paint_multi_tile(tab, ls, 0, 0, "multi_tree", fake_get_element)
        erase_multi_tile(tab, ls, (0, 0, 0), fake_get_element)
        assert (0, 0) not in ls.grid
        assert (1, 1) not in ls.grid
        assert (0, 0, 0) not in tab.multi_tiles


# ── Spawn scan ─────────────────────────────────────────────

class TestSpawnScan:
    def test_find_spawn(self):
        tab = FakeTab()
        tab.layers[0].grid[(3, 7)] = "inicio"
        pos, z = scan_spawn_from_grid(tab)
        assert pos == (3, 7)
        assert z == 0

    def test_no_spawn(self):
        tab = FakeTab()
        pos, z = scan_spawn_from_grid(tab)
        assert pos is None
        assert z == 0


# ── Persistencia (file I/O) ────────────────────────────────

class TestFilePersistence:
    def test_save_load_layer(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ls = FakeLayer(8, 6)
            ls.grid[(0, 0)] = "pasto"
            ls.grid[(5, 3)] = "pared"
            save_layer("m1", 0, ls, tmpdir)

            loaded = load_layer("m1", 0, tmpdir)
            assert loaded is not None
            grid, ancho, alto = loaded
            assert ancho == 8
            assert alto == 6
            assert grid[(0, 0)] == "pasto"
            assert grid[(5, 3)] == "pared"

    def test_load_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            assert load_layer("nope", 0, tmpdir) is None

    def test_save_load_stacks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stacks = {
                (1, 2, 0): {"pos": [1, 2], "z": 0, "eventos": [{"trigger": "contact"}]},
            }
            save_stacks("m1", stacks, tmpdir)
            loaded = load_stacks("m1", tmpdir)
            assert (1, 2, 0) in loaded
            assert loaded[(1, 2, 0)]["eventos"][0]["trigger"] == "contact"

    def test_save_load_multi_tiles(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mt = {(3, 4, 0): {"element_id": "tree"}}
            save_multi_tiles("m1", mt, tmpdir)
            loaded = load_multi_tiles("m1", tmpdir)
            assert (3, 4, 0) in loaded
            assert loaded[(3, 4, 0)]["element_id"] == "tree"

    def test_save_load_meta(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save_meta("m1", (10, 20), 1, tmpdir)
            loaded = load_meta("m1", tmpdir)
            assert loaded["spawn_pos"] == (10, 20)
            assert loaded["spawn_z"] == 1

    def test_save_meta_no_spawn(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save_meta("m1", None, 0, tmpdir)
            loaded = load_meta("m1", tmpdir)
            assert loaded == {}
