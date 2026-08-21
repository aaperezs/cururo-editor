import json
import os

from editor.project import Project, create_project, TEMPLATES_DIR


def _write_manifest(root, data):
    with open(os.path.join(root, "cururo.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class TestProjectGraphics:
    def test_fallbacks(self, tmp_path):
        _write_manifest(tmp_path, {"name": "x", "id": "x"})
        p = Project(str(tmp_path))
        assert p.tile_size == 20
        assert p.resolution == (800, 600)
        assert p.pixel_art_scale == 1
        assert p.tileset is None

    def test_graphics_block(self, tmp_path):
        _write_manifest(tmp_path, {
            "name": "x", "id": "x",
            "graphics": {"tile_size": 16, "resolution": [640, 480],
                         "pixel_art_scale": 2, "tileset": "tiles.png"},
        })
        p = Project(str(tmp_path))
        assert p.tile_size == 16
        assert p.resolution == (640, 480)
        assert p.pixel_art_scale == 2
        assert p.tileset == "tiles.png"

    def test_legacy_resolution(self, tmp_path):
        _write_manifest(tmp_path, {"name": "x", "id": "x", "resolution": "960x720"})
        p = Project(str(tmp_path))
        assert p.resolution == (960, 720)

    def test_graphics_gana_a_legacy(self, tmp_path):
        _write_manifest(tmp_path, {
            "name": "x", "id": "x", "resolution": "960x720",
            "graphics": {"tile_size": 24, "resolution": [1200, 900]},
        })
        p = Project(str(tmp_path))
        assert p.resolution == (1200, 900)
        assert p.tile_size == 24

    def test_resolution_string_en_graphics(self, tmp_path):
        _write_manifest(tmp_path, {
            "name": "x", "id": "x",
            "graphics": {"tile_size": 32, "resolution": "1280x960"},
        })
        p = Project(str(tmp_path))
        assert p.resolution == (1280, 960)


class TestCreateProjectGraphics:
    def test_escribe_graphics(self, tmp_path):
        tpl = os.path.join(TEMPLATES_DIR, "blank")
        if not os.path.isdir(tpl):
            return  # sin template: skip
        target = str(tmp_path / "proj")
        create_project("blank", "Test", target,
                       graphics_config={"tile_size": 16, "resolution": [640, 480],
                                        "pixel_art_scale": 2, "tileset": None})
        with open(os.path.join(target, "cururo.json"), encoding="utf-8") as f:
            manifest = json.load(f)
        assert manifest["graphics"]["tile_size"] == 16
        assert manifest["graphics"]["resolution"] == [640, 480]
        assert manifest["graphics"]["pixel_art_scale"] == 2
        assert manifest["graphics"]["tileset"] is None

    def test_sin_graphics_config_no_agrega_bloque(self, tmp_path):
        tpl = os.path.join(TEMPLATES_DIR, "blank")
        if not os.path.isdir(tpl):
            return
        target = str(tmp_path / "proj2")
        create_project("blank", "Test2", target)
        with open(os.path.join(target, "cururo.json"), encoding="utf-8") as f:
            manifest = json.load(f)
        assert "graphics" not in manifest

    def test_normaliza_strings(self, tmp_path):
        tpl = os.path.join(TEMPLATES_DIR, "blank")
        if not os.path.isdir(tpl):
            return
        target = str(tmp_path / "proj3")
        create_project("blank", "Test3", target,
                       graphics_config={"tile_size": "16", "resolution": "640x480",
                                        "pixel_art_scale": 1, "tileset": None})
        with open(os.path.join(target, "cururo.json"), encoding="utf-8") as f:
            manifest = json.load(f)
        assert manifest["graphics"]["tile_size"] == 16
        assert manifest["graphics"]["resolution"] == [640, 480]

    def test_tile_size_invalido_default_20(self, tmp_path):
        tpl = os.path.join(TEMPLATES_DIR, "blank")
        if not os.path.isdir(tpl):
            return
        target = str(tmp_path / "proj4")
        create_project("blank", "Test4", target,
                       graphics_config={"tile_size": "abc", "resolution": [800, 600]})
        with open(os.path.join(target, "cururo.json"), encoding="utf-8") as f:
            manifest = json.load(f)
        assert manifest["graphics"]["tile_size"] == 20


class TestUpdateConfigGraphics:
    def test_sync_graphics_resolution(self, tmp_path):
        _write_manifest(tmp_path, {
            "name": "x", "id": "x",
            "graphics": {"tile_size": 20, "resolution": [800, 600]},
        })
        p = Project(str(tmp_path))
        p.update_config(resolution="960x720")
        assert p.resolution == (960, 720)
        with open(os.path.join(str(tmp_path), "cururo.json"), encoding="utf-8") as f:
            m = json.load(f)
        assert m["graphics"]["resolution"] == [960, 720]

    def test_sin_graphics_no_agrega_bloque(self, tmp_path):
        _write_manifest(tmp_path, {"name": "x", "id": "x", "resolution": "800x600"})
        p = Project(str(tmp_path))
        p.update_config(resolution="960x720")
        with open(os.path.join(str(tmp_path), "cururo.json"), encoding="utf-8") as f:
            m = json.load(f)
        assert m["resolution"] == "960x720"
        assert "graphics" not in m