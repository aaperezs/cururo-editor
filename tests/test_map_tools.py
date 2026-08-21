"""Tests unitarios para editor.map_tools — pintar, borrar, cubo, arrastrar."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from editor.map_tools import MapTools


# -- Fake objects -------------------------------------------

class FakeLayer:
    def __init__(self, ancho: int = 10, alto: int = 10):
        self.grid: dict[tuple[int, int], str] = {}
        self.ancho = ancho
        self.alto = alto


class FakeTab:
    def __init__(self, ancho: int = 10, alto: int = 10):
        self.map_id = "test_map"
        self.dirty = False
        self.layers: dict[int, FakeLayer] = {0: FakeLayer(ancho, alto)}
        self.stacks: dict[tuple[int, int, int], dict[str, Any]] = {}
        self.multi_tiles: dict[tuple[int, int, int], dict[str, Any]] = {}
        self.active_z = 0
        self.spawn_pos: tuple[int, int] | None = None
        self.spawn_z = 0
        self.undo_stack: list[dict[str, Any]] = []
        self.redo_stack: list[dict[str, Any]] = []

    @property
    def layer_order(self) -> list[int]:
        return sorted(self.layers.keys())

    def push_undo(self) -> None:
        self.undo_stack.append({"snapshot": True})
        self.redo_stack.clear()
        self.dirty = True


def fake_get_element(element_id: str) -> dict[str, Any] | None:
    if element_id == "multi_tree":
        return {
            "sprite_id": "tree",
            "behavior": "multi_tile",
            "multi_tile": True,
            "properties": {"tile_rows": 2, "tile_cols": 2},
        }
    if element_id == "single_sprite":
        return {"sprite_id": "spr", "multi_tile": False}
    return None


def fake_is_multi_tile(sprite_id: str) -> bool:
    return sprite_id == "multi_tree"


# -- Init y configuracion ----------------------------------

class TestMapToolsInit:
    def test_default_state(self):
        mt = MapTools()
        assert mt.active_tool == "select"
        assert mt.selected_sprite_id is None
        assert mt.is_dragging is False
        assert mt.drag_button == 0
        assert mt.last_paint_pos is None
        assert mt.drag_source is None

    def test_set_tool(self):
        mt = MapTools()
        mt.set_tool("eraser")
        assert mt.active_tool == "eraser"
        assert mt.selected_sprite_id is None

    def test_set_tool_clears_sprite(self):
        mt = MapTools()
        mt.set_sprite("pasto")
        mt.set_tool("drag")
        assert mt.selected_sprite_id is None

    def test_set_sprite(self):
        mt = MapTools()
        mt.set_sprite("pasto")
        assert mt.selected_sprite_id == "pasto"

    def test_with_get_element_fn(self):
        mt = MapTools(get_element_fn=fake_get_element)
        assert mt._get_element is fake_get_element

    def test_cancel_drag(self):
        mt = MapTools()
        mt.drag_source = (1, 1, "sid", 0)
        mt.cancel_drag()
        assert mt.drag_source is None


# -- handle_map_click --------------------------------------

class TestHandleMapClick:
    @patch("editor.map_tools.is_multi_tile_element", fake_is_multi_tile)
    def test_click_with_sprite(self):
        mt = MapTools()
        mt.set_sprite("pasto")
        tab = FakeTab()
        result = mt.handle_map_click(tab, 2, 3, fake_get_element)
        assert result is True
        assert tab.layers[0].grid[(2, 3)] == "pasto"
        assert tab.dirty is True
        assert len(tab.undo_stack) == 1

    def test_click_no_sprite_returns_false(self):
        mt = MapTools()
        tab = FakeTab()
        result = mt.handle_map_click(tab, 0, 0, fake_get_element)
        assert result is False

    @patch("editor.map_tools.is_multi_tile_element", fake_is_multi_tile)
    def test_click_out_of_bounds(self):
        mt = MapTools()
        mt.set_sprite("pasto")
        tab = FakeTab()
        result = mt.handle_map_click(tab, 15, 15, fake_get_element)
        assert result is False

    @patch("editor.map_tools.is_multi_tile_element", fake_is_multi_tile)
    def test_click_sets_spawn(self):
        mt = MapTools()
        mt.set_sprite("inicio")
        tab = FakeTab()
        mt.handle_map_click(tab, 5, 5, fake_get_element)
        assert tab.spawn_pos == (5, 5)
        assert tab.spawn_z == 0

    @patch("editor.map_tools.is_multi_tile_element", fake_is_multi_tile)
    def test_click_multi_tile(self):
        mt = MapTools()
        mt.set_sprite("multi_tree")
        tab = FakeTab()
        mt.handle_map_click(tab, 0, 0, fake_get_element)
        assert (0, 0) in tab.layers[0].grid
        assert (1, 1) in tab.layers[0].grid
        assert len(tab.layers[0].grid) == 4


# -- start_drag --------------------------------------------

class TestStartDrag:
    def test_bucket_flood_fill(self):
        mt = MapTools()
        mt.set_tool("bucket")
        mt.set_sprite("roca")
        tab = FakeTab(5, 5)
        ls = tab.layers[0]
        for x in range(3):
            ls.grid[(x, 0)] = "pasto"
        result = mt.start_drag(tab, 0, 0, 1, fake_get_element)
        assert result is True
        for x in range(3):
            assert ls.grid[(x, 0)] == "roca"

    @patch("editor.map_tools.is_multi_tile_element", fake_is_multi_tile)
    def test_eraser_click(self):
        mt = MapTools()
        mt.set_tool("eraser")
        tab = FakeTab()
        ls = tab.layers[0]
        ls.grid[(2, 3)] = "pasto"
        mt.start_drag(tab, 2, 3, 1, fake_get_element)
        assert (2, 3) not in ls.grid
        assert mt.is_dragging is True
        assert mt.last_paint_pos == (2, 3)

    @patch("editor.map_tools.is_multi_tile_element", fake_is_multi_tile)
    def test_paint_drag_start(self):
        mt = MapTools()
        mt.set_sprite("pasto")
        tab = FakeTab()
        mt.start_drag(tab, 1, 1, 1, fake_get_element)
        assert tab.layers[0].grid[(1, 1)] == "pasto"
        assert mt.is_dragging is True
        assert mt.drag_button == 1

    @patch("editor.map_tools.is_multi_tile_element", fake_is_multi_tile)
    def test_right_click_erases(self):
        mt = MapTools()
        tab = FakeTab()
        ls = tab.layers[0]
        ls.grid[(3, 3)] = "pasto"
        mt.start_drag(tab, 3, 3, 3, fake_get_element)
        assert (3, 3) not in ls.grid

    def test_out_of_bounds_returns_false(self):
        mt = MapTools()
        mt.set_sprite("pasto")
        tab = FakeTab(5, 5)
        result = mt.start_drag(tab, 10, 10, 1, fake_get_element)
        assert result is False

    @patch("editor.map_tools.is_multi_tile_element", fake_is_multi_tile)
    def test_drag_sets_spawn(self):
        mt = MapTools()
        mt.set_sprite("inicio")
        tab = FakeTab()
        mt.start_drag(tab, 4, 4, 1, fake_get_element)
        assert tab.spawn_pos == (4, 4)

    @patch("editor.map_tools.is_multi_tile_element", fake_is_multi_tile)
    def test_multi_tile_drag(self):
        mt = MapTools()
        mt.set_sprite("multi_tree")
        tab = FakeTab(10, 10)
        mt.start_drag(tab, 0, 0, 1, fake_get_element)
        assert len(tab.layers[0].grid) == 4


# -- continue_drag -----------------------------------------

class TestContinueDrag:
    @patch("editor.map_tools.is_multi_tile_element", fake_is_multi_tile)
    def test_interpolates_tiles(self):
        mt = MapTools()
        mt.set_sprite("pasto")
        mt.is_dragging = True
        mt.drag_button = 1
        mt.last_paint_pos = (0, 0)
        tab = FakeTab(10, 10)
        mt.continue_drag(tab, 3, 0, fake_get_element)
        assert (1, 0) in tab.layers[0].grid
        assert (2, 0) in tab.layers[0].grid
        assert (3, 0) in tab.layers[0].grid
        assert mt.last_paint_pos == (3, 0)

    @patch("editor.map_tools.is_multi_tile_element", fake_is_multi_tile)
    def test_same_position_noop(self):
        mt = MapTools()
        mt.set_sprite("pasto")
        mt.is_dragging = True
        mt.drag_button = 1
        mt.last_paint_pos = (2, 2)
        tab = FakeTab()
        mt.continue_drag(tab, 2, 2, fake_get_element)
        assert tab.layers[0].grid.get((2, 2)) is None

    @patch("editor.map_tools.is_multi_tile_element", fake_is_multi_tile)
    def test_eraser_drag(self):
        mt = MapTools()
        mt.set_tool("eraser")
        mt.is_dragging = True
        mt.drag_button = 1
        mt.last_paint_pos = (0, 0)
        tab = FakeTab(10, 10)
        ls = tab.layers[0]
        ls.grid[(1, 0)] = "pasto"
        ls.grid[(2, 0)] = "pasto"
        ls.grid[(3, 0)] = "pasto"
        mt.continue_drag(tab, 3, 0, fake_get_element)
        assert (1, 0) not in ls.grid
        assert (2, 0) not in ls.grid
        assert (3, 0) not in ls.grid

    @patch("editor.map_tools.is_multi_tile_element", fake_is_multi_tile)
    def test_right_click_drag_erases(self):
        mt = MapTools()
        mt.is_dragging = True
        mt.drag_button = 3
        mt.last_paint_pos = (0, 0)
        tab = FakeTab(10, 10)
        ls = tab.layers[0]
        ls.grid[(1, 0)] = "pasto"
        mt.continue_drag(tab, 1, 0, fake_get_element)
        assert (1, 0) not in ls.grid

    def test_no_last_pos_returns(self):
        mt = MapTools()
        mt.is_dragging = True
        mt.drag_button = 1
        mt.last_paint_pos = None
        tab = FakeTab()
        mt.continue_drag(tab, 1, 1, fake_get_element)
        assert tab.layers[0].grid == {}


# -- stop_drag ---------------------------------------------

class TestStopDrag:
    def test_stop_drag(self):
        mt = MapTools()
        mt.is_dragging = True
        mt.last_paint_pos = (5, 5)
        mt.stop_drag()
        assert mt.is_dragging is False
        assert mt.last_paint_pos is None


# -- handle_drag_click (drag tool) -------------------------

class TestHandleDragClick:
    @patch("editor.map_tools.is_multi_tile_element", fake_is_multi_tile)
    def test_pickup_tile(self):
        mt = MapTools()
        mt.set_tool("drag")
        tab = FakeTab()
        tab.layers[0].grid[(2, 2)] = "pasto"
        result = mt.handle_drag_click(tab, 2, 2)
        assert result is True
        assert mt.drag_source == (2, 2, "pasto", 0)

    @patch("editor.map_tools.is_multi_tile_element", fake_is_multi_tile)
    def test_place_tile(self):
        mt = MapTools()
        mt.set_tool("drag")
        tab = FakeTab()
        ls = tab.layers[0]
        ls.grid[(2, 2)] = "pasto"
        mt.drag_source = (2, 2, "pasto", 0)
        result = mt.handle_drag_click(tab, 5, 5)
        assert result is True
        assert (5, 5) in ls.grid
        assert (2, 2) not in ls.grid
        assert mt.drag_source is None

    @patch("editor.map_tools.is_multi_tile_element", fake_is_multi_tile)
    def test_pickup_empty_returns_false(self):
        mt = MapTools()
        mt.set_tool("drag")
        tab = FakeTab()
        result = mt.handle_drag_click(tab, 0, 0)
        assert result is False

    @patch("editor.map_tools.is_multi_tile_element", fake_is_multi_tile)
    def test_same_position_cancels(self):
        mt = MapTools()
        mt.set_tool("drag")
        tab = FakeTab()
        tab.layers[0].grid[(2, 2)] = "pasto"
        mt.drag_source = (2, 2, "pasto", 0)
        result = mt.handle_drag_click(tab, 2, 2)
        assert result is True
        assert mt.drag_source is None

    @patch("editor.map_tools.is_multi_tile_element", fake_is_multi_tile)
    def test_different_z_returns_false(self):
        mt = MapTools()
        mt.set_tool("drag")
        tab = FakeTab()
        tab.layers[0].grid[(2, 2)] = "pasto"
        tab.active_z = 1
        mt.drag_source = (2, 2, "pasto", 0)
        result = mt.handle_drag_click(tab, 5, 5)
        assert result is False

    @patch("editor.map_tools.is_multi_tile_element", fake_is_multi_tile)
    def test_out_of_bounds(self):
        mt = MapTools()
        mt.set_tool("drag")
        tab = FakeTab(5, 5)
        result = mt.handle_drag_click(tab, 10, 10)
        assert result is False

    @patch("editor.map_tools.is_multi_tile_element", fake_is_multi_tile)
    def test_drag_moves_spawn(self):
        mt = MapTools()
        mt.set_tool("drag")
        tab = FakeTab()
        ls = tab.layers[0]
        ls.grid[(2, 2)] = "inicio"
        tab.spawn_pos = (2, 2)
        tab.spawn_z = 0
        mt.drag_source = (2, 2, "inicio", 0)
        mt.handle_drag_click(tab, 5, 5)
        assert tab.spawn_pos == (5, 5)

    @patch("editor.map_tools.is_multi_tile_element", fake_is_multi_tile)
    def test_drag_moves_stack(self):
        mt = MapTools()
        mt.set_tool("drag")
        tab = FakeTab()
        ls = tab.layers[0]
        ls.grid[(2, 2)] = "pasto"
        tab.stacks[(2, 2, 0)] = {"eventos": []}
        mt.drag_source = (2, 2, "pasto", 0)
        mt.handle_drag_click(tab, 5, 5)
        assert (5, 5, 0) in tab.stacks
        assert (2, 2, 0) not in tab.stacks

    @patch("editor.map_tools.is_multi_tile_element", fake_is_multi_tile)
    def test_pickup_multi_tile_returns_false(self):
        mt = MapTools()
        mt.set_tool("drag")
        tab = FakeTab()
        ls = tab.layers[0]
        ls.grid[(2, 2)] = "multi_tree"
        tab.multi_tiles[(2, 2, 0)] = {"element_id": "multi_tree"}
        result = mt.handle_drag_click(tab, 2, 2)
        assert result is False
