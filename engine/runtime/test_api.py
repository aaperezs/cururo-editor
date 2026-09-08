"""
Headless test for the runtime API.
Run: python -m engine.runtime.test_api
No display required - just verifies the API logic.
"""
import os
import sys

_project_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import os
import tempfile


def test_game_api():
    from engine.runtime.api import Game

    g = Game()
    results = []

    @g.init
    def my_init():
        results.append("init")

    @g.update
    def my_update():
        results.append("update")

    @g.draw
    def my_draw(screen):
        results.append("draw")

    @g.input
    def my_input(event):
        results.append("input")

    g.run_init()
    g.run_update()
    g.run_draw(None)
    g.run_input(None)

    assert results == ["init", "update", "draw", "input"], f"Got {results}"
    print("[PASS] test_game_api")


def test_game_singleton():
    from engine.runtime import game

    assert hasattr(game, "run_init")
    assert hasattr(game, "run_update")
    assert hasattr(game, "run_draw")
    assert hasattr(game, "run_input")
    print("[PASS] test_game_singleton")


def test_vec2():
    from engine.runtime.vec2 import Vec2

    a = Vec2(3, 4)
    b = Vec2(1, 2)

    assert (a + b) == Vec2(4, 6)
    assert (a - b) == Vec2(2, 2)
    assert (a * 2) == Vec2(6, 8)
    assert a.as_tuple() == (3, 4)
    print("[PASS] test_vec2")


def test_loader():
    from engine.runtime.loader import load_script

    with tempfile.TemporaryDirectory() as td:
        scripts_dir = os.path.join(td, "scripts")
        os.makedirs(scripts_dir)
        with open(os.path.join(scripts_dir, "test_game.py"), "w") as f:
            f.write("from orm.runtime import game\n")
            f.write("@game.init\ndef init():\n")
            f.write("    pass\n")

        module = load_script(td, "test_game")
        assert module is not None
        assert hasattr(module, "init")
        print("[PASS] test_loader")


def test_camera():
    from engine.runtime.camera import Camera

    cam = Camera(800, 600)
    cam.set_pos(100, 100)

    assert cam.apply((200, 200)) == (100.0, 100.0)
    assert cam.apply((100, 100)) == (0.0, 0.0)

    cam.snap_to(400, 300)
    assert cam.x == 0.0
    assert cam.y == 0.0

    print("[PASS] test_camera")


def test_input_keymap():
    from engine.runtime.input import _key_map

    assert _key_map["up"] is not None
    assert _key_map["space"] is not None
    assert _key_map["a"] is not None
    assert _key_map["1"] is not None
    print("[PASS] test_input_keymap")


def test_renderer_functions():
    from engine.runtime.renderer import text_width, text_height

    assert text_width("hello", 16) > 0
    assert text_height(16) > 0
    print("[PASS] test_renderer_functions")


if __name__ == "__main__":
    os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
    import pygame
    pygame.init()
    pygame.display.set_mode((1, 1))

    test_game_api()
    test_game_singleton()
    test_vec2()
    test_loader()
    test_camera()
    test_input_keymap()
    test_renderer_functions()

    pygame.quit()
    print("\nAll tests passed!")
