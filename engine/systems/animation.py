import json
import os

import pygame
from engine.project_paths import data_dir

_animations = {}
_loaded = False


def _load():
    global _loaded
    if _loaded:
        return
    path = data_dir("animations.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            _animations.update(json.load(f))
    _loaded = True


def get_anim_sprite(anim_name):
    _load()
    cfg = _animations.get(anim_name)
    if not cfg:
        return None
    frames = cfg["frames"]
    if not frames:
        return None
    interval = cfg.get("interval", 500)
    idx = (pygame.time.get_ticks() // interval) % len(frames)
    return frames[idx]


def get_anim_config(anim_name):
    _load()
    return _animations.get(anim_name)


def get_anim_glow(anim_name):
    cfg = get_anim_config(anim_name)
    if not cfg:
        return None
    glow = cfg.get("glow")
    if glow and glow.get("enabled"):
        return glow
    return None

