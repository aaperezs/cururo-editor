try:
    from engine.runtime.api import game, Game
    from engine.runtime.vec2 import Vec2
    from engine.runtime import renderer, input, camera
    from engine.runtime.loader import load_script
except ImportError:
    from engine.runtime.api import game, Game
    from engine.runtime.vec2 import Vec2
    from engine.runtime import renderer, input, camera
    from engine.runtime.loader import load_script

__all__ = ["game", "Game", "Vec2", "renderer", "input", "camera", "load_script"]
