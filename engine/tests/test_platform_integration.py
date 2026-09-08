"""
Integration tests for Cururo Platform.
Tests the full flow: template → project → script → runtime API.

Run: pytest tests/test_platform_integration.py -v
"""
import os
import sys
import tempfile
import json

_project_root = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pytest


class TestTemplateSystem:
    def test_list_templates(self):
        from editor.project import list_templates
        templates = list_templates()
        assert len(templates) >= 1
        ids = [t["id"] for t in templates]
        assert "snake_rpg" in ids

    def test_create_project(self):
        from editor.project import create_project
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "test_game")
            result = create_project("snake_rpg", "Test Game", path)
            assert result == path
            assert os.path.exists(os.path.join(path, "cururo.json"))
            assert os.path.exists(os.path.join(path, "scripts", "game.py"))
            assert os.path.exists(os.path.join(path, "data", "elementos.json"))
            assert os.path.exists(os.path.join(path, "data", "behaviors.json"))

            with open(os.path.join(path, "cururo.json")) as f:
                manifest = json.load(f)
            assert manifest["name"] == "Test Game"
            assert manifest["id"] == "test_game"


class TestBehaviorsData:
    def test_behaviors_load_hardcoded(self):
        from editor.project import set_current_project, create_project
        from editor.behaviors import _load, BEHAVIORS, get_behavior_list
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "test_beh_hard")
            create_project("snake_rpg", "Test", path)
            set_current_project(path)
            _load()
            assert len(BEHAVIORS) >= 10
            items = get_behavior_list()
            ids = [i[0] for i in items]
            assert "bloqueante" in ids

    def test_behaviors_json_exists(self):
        path = os.path.join(_project_root, "data", "behaviors.json")
        assert os.path.exists(path)
        with open(path) as f:
            data = json.load(f)
        assert "bloqueante" in data
        assert "properties" in data["bloqueante"]
        assert "destructible" in data["bloqueante"]["properties"]

    def test_behaviors_load_from_project(self):
        from editor.project import set_current_project, create_project
        from editor.behaviors import _load, get_behaviors
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "test_beh")
            create_project("snake_rpg", "Test", path)
            set_current_project(path)
            _load()
            behs = get_behaviors()
            assert "bloqueante" in behs


class TestRuntimeAPI:
    def test_game_hooks(self):
        from engine.runtime.api import Game
        g = Game()
        calls = []

        @g.init
        def i(): calls.append("init")
        @g.update
        def u(): calls.append("update")
        @g.draw
        def d(s): calls.append("draw")
        @g.input
        def h(e): calls.append("input")

        g.run_init()
        g.run_update()
        g.run_draw(None)
        g.run_input(None)

        assert calls == ["init", "update", "draw", "input"]

    def test_vec2_operations(self):
        from engine.runtime.vec2 import Vec2
        a = Vec2(3, 4)
        b = Vec2(1, 2)
        assert a + b == Vec2(4, 6)
        assert a - b == Vec2(2, 2)
        assert a * 2 == Vec2(6, 8)
        assert a.as_tuple() == (3, 4)

    def test_camera(self):
        from engine.runtime.camera import Camera
        cam = Camera(800, 600)
        cam.set_pos(100, 100)
        assert cam.apply((200, 200)) == (100.0, 100.0)
        assert cam.get_offset() == (100, 100)

        cam.snap_to(400, 300)
        assert cam.x == 0.0
        assert cam.y == 0.0

        cam.set_bounds(0, 0, 100, 100)
        cam.set_pos(-50, 150)
        assert cam.x == 0.0
        assert cam.y == 100.0

    def test_loader(self):
        import pygame
        pygame.init()
        screen = pygame.Surface((100, 100))
        from engine.runtime.loader import load_script
        from editor.project import create_project
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "test_loader")
            create_project("snake_rpg", "Test", path)
            mod = load_script(path, "game")
            assert mod is not None
            assert hasattr(mod, "game")
            from engine.runtime import game as runtime_game
            runtime_game.run_init()
            runtime_game.run_update()
            runtime_game.run_draw(screen)
            import pygame as _pg
            fake_event = _pg.event.Event(_pg.KEYDOWN, key=_pg.K_ESCAPE)
            runtime_game.run_input(fake_event)

    def test_renderer_primitives(self):
        from engine.runtime.renderer import text_width, text_height
        assert text_width("hello") > 0
        assert text_height(16) > 0

    def test_input_keymap(self):
        from engine.runtime.input import is_key_down, _key_map
        assert "up" in _key_map
        assert "space" in _key_map
        assert "a" in _key_map
        assert "1" in _key_map


class TestStackManager:
    def test_run_script_in_event(self):
        pass  # Requires full pygame init + game state


class TestBedrock:
    """Verify no import errors across the platform."""

    def test_editor_imports(self):
        from editor.scripts import list_scripts
        assert callable(list_scripts)

    def test_script_editor_widget(self):
        from editor.widgets.script_editor import ScriptEditor
        se = ScriptEditor(0, 0, 100, 100)
        assert se.text == ""

    def test_script_panel(self):
        from editor.script_panel import ScriptPanel
        assert ScriptPanel is not None

    def test_custom_behaviors_panel(self):
        from editor.custom_behaviors import CustomBehaviorsPanel
        assert CustomBehaviorsPanel is not None

    def test_generic_entity(self):
        from engine.entities.generic import GenericEntity
        e = GenericEntity(10, 20, {"hp": 5}, "hero")
        assert e.x == 10
        assert e.y == 20
        assert e.properties["hp"] == 5
        assert e.colisiona_con(10, 20) == True
        assert e.colisiona_con(11, 20) == False

    def test_project_dialog_imports(self):
        from editor.project_dialog import ProjectDialog, STATE_LIST, STATE_NEW
        assert STATE_LIST == 0
        assert STATE_NEW == 1

