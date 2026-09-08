import json
import os
import sys

from engine.project_paths import data_dir

PREFS_FILE = "user_prefs.json"
DEFAULTS = {
    "resolution": "auto",
    "fullscreen": False,
    "bgm_volume": 0.7,
    "sfx_volume": 1.0,
}


def prefs_path():
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), PREFS_FILE)
    return data_dir(PREFS_FILE)


def load():
    prefs = dict(DEFAULTS)
    try:
        with open(prefs_path(), "r", encoding="utf-8") as f:
            saved = json.load(f)
        if isinstance(saved, dict):
            prefs.update(saved)
    except (IOError, OSError, json.JSONDecodeError):
        pass
    return prefs


def save(prefs):
    try:
        os.makedirs(os.path.dirname(prefs_path()), exist_ok=True)
        with open(prefs_path(), "w", encoding="utf-8") as f:
            json.dump(prefs, f, indent=2)
    except (IOError, OSError):
        pass


def parse_resolution(value):
    """'auto' -> None; '1280x720' -> (1280, 720); invalido -> None."""
    if not value or str(value).strip().lower() == "auto":
        return None
    try:
        w, h = str(value).strip().lower().replace(" ", "").split("x")
        w, h = int(w), int(h)
        if w >= 320 and h >= 240:
            return (w, h)
    except (ValueError, AttributeError):
        pass
    return None

