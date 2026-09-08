import json
import os
import pygame

from engine.project_paths import data_dir

_RUTA = data_dir("scenes.json")


def load_scenes():
    if not os.path.exists(_RUTA):
        return {"chapters": [], "titulo": {"enabled": False}}
    with open(_RUTA, "r", encoding="utf-8") as f:
        return json.load(f)


def get_chapters(data):
    return data.get("chapters", [])


def get_title_config(data):
    return data.get("titulo", {"enabled": False})


def find_first_scene(data):
    chapters = get_chapters(data)
    if not chapters:
        return None
    first = chapters[0]
    scenes = first.get("escenas", [])
    if not scenes:
        return None
    return scenes[0]


def evaluate_condition(condition, flags_manager):
    """Evalúa una condición de escena (hoja, lista o compuesto AND/OR)."""
    if not condition:
        return True
    from engine.systems.conditions import evaluate_condition_node
    return evaluate_condition_node(
        condition, lambda leaf: _eval_leaf(leaf, flags_manager)
    )


def _eval_leaf(condition, flags_manager):
    if not condition or not isinstance(condition, dict):
        return True
    flag_key = condition.get("flag", "")
    op = condition.get("operador", "==")
    raw_val = condition.get("valor", "")
    current = flags_manager.get(flag_key, None)
    try:
        val = json.loads(raw_val)
    except (json.JSONDecodeError, TypeError):
        val = raw_val
    if op == "==":
        return current == val
    elif op == "!=":
        return current != val
    elif op == ">":
        return (current is not None) and (current > val)
    elif op == "<":
        return (current is not None) and (current < val)
    elif op == ">=":
        return (current is not None) and (current >= val)
    elif op == "<=":
        return (current is not None) and (current <= val)
    return True

