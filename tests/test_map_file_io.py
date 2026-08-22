import os
import json
import tempfile
import shutil
from editor.map_tab import MapTab
from editor.map_file_io import (
    create_new_map, load_map, resize_map, save_map,
    get_workspace_data, sync_events_from_widget,
)


class TestCreateNewMap:
    def test_creates_tab_with_dimensions(self):
        tab = create_new_map(50, 40)
        assert tab.layers[0].ancho == 50
        assert tab.layers[0].alto == 40
        assert tab.layers[0].visible is True
        assert tab.layers[0].opacity == 100
        assert tab.map_id.startswith("_new_")

    def test_default_dimensions_clamped(self):
        tab = create_new_map(5, 5)
        assert tab.layers[0].ancho == 5
        assert tab.layers[0].alto == 5


class TestLoadMap:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.maps_dir = os.path.join(self.tmpdir, "maps")
        self.stacks_dir = os.path.join(self.tmpdir, "stacks")
        os.makedirs(self.maps_dir)
        os.makedirs(self.stacks_dir)

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def _write_layer(self, map_id, z, grid, ancho, alto):
        data = {"grid": {f"{k[0]},{k[1]}": v for k, v in grid.items()}, "ancho": ancho, "alto": alto}
        suffix = "" if z == 0 else f"_z{z}"
        path = os.path.join(self.maps_dir, f"{map_id}{suffix}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def _write_meta(self, map_id, meta):
        path = os.path.join(self.maps_dir, f"{map_id}_meta.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"spawn": {"pos": list(meta["spawn_pos"]), "z": meta.get("spawn_z", 0)}}, f)

    def test_load_existing_map(self):
        self._write_layer("test_map", 0, {(0, 0): "pasto", (1, 0): "muro"}, 10, 8)
        self._write_meta("test_map", {"spawn_pos": [0, 0], "spawn_z": 0})
        tab = MapTab(map_id="test_map")
        load_map(tab, "test_map", self.maps_dir, self.stacks_dir)
        assert tab.layers[0].ancho == 10
        assert tab.layers[0].alto == 8
        assert tab.layers[0].grid[(0, 0)] == "pasto"
        assert tab.layers[0].grid[(1, 0)] == "muro"
        assert tab.spawn_pos == (0, 0)

    def test_load_nonexistent_map_defaults(self):
        tab = MapTab(map_id="nonexistent")
        load_map(tab, "nonexistent", self.maps_dir, self.stacks_dir)
        assert tab.layers[0].ancho == 40
        assert tab.layers[0].alto == 30

    def test_load_multi_layer(self):
        self._write_layer("ml_map", 0, {(0, 0): "pasto"}, 5, 5)
        self._write_layer("ml_map", 1, {(0, 0): "agua"}, 5, 5)
        tab = MapTab(map_id="ml_map")
        load_map(tab, "ml_map", self.maps_dir, self.stacks_dir)
        assert 1 in tab.layers
        assert tab.layers[1].grid[(0, 0)] == "agua"


class TestResizeMap:
    def test_crop_tiles_outside_bounds(self):
        tab = MapTab(map_id="r1")
        tab.layers[0].ancho = 10
        tab.layers[0].alto = 10
        tab.layers[0].grid = {(0, 0): "a", (5, 5): "b", (9, 9): "c"}
        resize_map(tab, 6, 6)
        assert (0, 0) in tab.layers[0].grid
        assert (5, 5) in tab.layers[0].grid
        assert (9, 9) not in tab.layers[0].grid

    def test_resize_updates_dimensions(self):
        tab = MapTab(map_id="r2")
        tab.layers[0].ancho = 10
        tab.layers[0].alto = 10
        resize_map(tab, 20, 15)
        assert tab.layers[0].ancho == 20
        assert tab.layers[0].alto == 15

    def test_crop_multi_tiles_outside_bounds(self):
        tab = MapTab(map_id="r3")
        tab.layers[0].ancho = 10
        tab.layers[0].alto = 10
        tab.multi_tiles = {(8, 8, 0): {"element_id": "tree"}, (2, 2, 0): {"element_id": "rock"}}
        resize_map(tab, 5, 5)
        assert (8, 8, 0) not in tab.multi_tiles
        assert (2, 2, 0) in tab.multi_tiles

    def test_pushes_undo(self):
        tab = MapTab(map_id="r4")
        tab.layers[0].ancho = 10
        tab.layers[0].alto = 10
        resize_map(tab, 5, 5)
        assert len(tab.undo_stack) == 1


class TestSaveMap:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.maps_dir = os.path.join(self.tmpdir, "maps")
        self.stacks_dir = os.path.join(self.tmpdir, "stacks")
        os.makedirs(self.maps_dir)
        os.makedirs(self.stacks_dir)

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def test_save_and_reload(self):
        tab = MapTab(map_id="save_test")
        tab.layers[0].ancho = 5
        tab.layers[0].alto = 5
        tab.layers[0].grid = {(0, 0): "pasto", (1, 1): "muro"}
        tab.layers[0].visible = True
        tab.layers[0].opacity = 100
        tab.spawn_pos = (0, 0)
        tab.spawn_z = 0

        save_map(tab, self.maps_dir, self.stacks_dir)
        assert tab.dirty is False

        tab2 = MapTab(map_id="save_test")
        load_map(tab2, "save_test", self.maps_dir, self.stacks_dir)
        assert tab2.layers[0].grid[(0, 0)] == "pasto"
        assert tab2.layers[0].grid[(1, 1)] == "muro"

    def test_save_new_map_noop(self):
        tab = MapTab(map_id="_new_123")
        save_map(tab, self.maps_dir, self.stacks_dir)
        assert not os.listdir(self.maps_dir)

    def test_save_spawn_meta(self):
        tab = MapTab(map_id="spawn_test")
        tab.layers[0].ancho = 5
        tab.layers[0].alto = 5
        tab.layers[0].grid = {(2, 3): "inicio"}
        tab.layers[0].visible = True
        tab.layers[0].opacity = 100
        tab.spawn_pos = (2, 3)
        tab.spawn_z = 0

        save_map(tab, self.maps_dir, self.stacks_dir)

        meta_path = os.path.join(self.maps_dir, "spawn_test_meta.json")
        assert os.path.exists(meta_path)
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        assert meta["spawn"]["pos"] == [2, 3]
        assert meta["spawn"]["z"] == 0


class TestGetWorkspaceData:
    def test_basic_workspace(self):
        tab = MapTab(map_id="w1")
        tab.active_z = 1
        tab.spawn_pos = (5, 5)
        tabs = {"w1": tab}
        data = get_workspace_data(tabs, ["w1"], "w1", 1.5, 10, 20)
        assert data["open_tabs"] == ["w1"]
        assert data["active_tab"] == "w1"
        t = data["tabs"]["w1"]
        assert t["active_z"] == 1
        assert t["spawn_pos"] == [5, 5]
        assert t["zoom"] == 1.5
        assert t["scroll_x"] == 10
        assert t["scroll_y"] == 20

    def test_empty_workspace(self):
        data = get_workspace_data({}, [], None, 1.0)
        assert data["open_tabs"] == []
        assert data["active_tab"] is None
        assert data["tabs"] == {}


class TestSyncEventsFromWidget:
    def test_sync_to_existing_stack(self):
        tab = MapTab(map_id="ev1")
        tab.stacks = {(1, 2, 0): {"pos": [1, 2], "z": 0, "eventos": []}}
        sync_events_from_widget(tab, (1, 2), 0, [{"event": "dialog"}])
        assert tab.stacks[(1, 2, 0)]["eventos"] == [{"event": "dialog"}]

    def test_sync_creates_new_stack(self):
        tab = MapTab(map_id="ev2")
        tab.stacks = {}
        sync_events_from_widget(tab, (3, 4), 1, [{"event": "give_item"}])
        key = (3, 4, 1)
        assert key in tab.stacks
        assert tab.stacks[key]["pos"] == [3, 4]
        assert tab.stacks[key]["z"] == 1
        assert tab.stacks[key]["eventos"] == [{"event": "give_item"}]

    def test_sync_no_selection(self):
        tab = MapTab(map_id="ev3")
        tab.stacks = {}
        sync_events_from_widget(tab, None, 0, [])
        assert tab.stacks == {}
