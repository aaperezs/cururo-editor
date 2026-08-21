"""Modelo de datos del editor de mapas.

Extrae lógica de serialización JSON, pintura multi-tile, flood fill,
borrado y gestión de spawn del MapEditorPanel monolítico.
Trabaja sobre MapTab (in-memory) y provee métodos de persistencia.
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable, Protocol


# ── Type aliases ───────────────────────────────────────────

Grid = dict[tuple[int, int], str]
Stacks = dict[tuple[int, int, int], dict[str, Any]]
MultiTiles = dict[tuple[int, int, int], dict[str, Any]]
Coords = tuple[int, int]
Coords3 = tuple[int, int, int]


# ── Protocols (duck-typed interfaces) ─────────────────────

class LayerLike(Protocol):
    grid: Grid
    ancho: int
    alto: int


class TabLike(Protocol):
    layers: dict[int, Any]
    active_z: int
    spawn_pos: tuple[int, int] | None
    spawn_z: int
    multi_tiles: MultiTiles
    stacks: Stacks
    dirty: bool
    undo_stack: list[Any]
    redo_stack: list[Any]

    @property
    def layer_order(self) -> list[int]: ...
    def push_undo(self) -> None: ...


GetElementFn = Callable[[str], dict[str, Any] | None]


# ── Serialización JSON ─────────────────────────────────────

def grid_to_json(grid: Grid, ancho: int, alto: int) -> str:
    """Convierte grid {(gx,gy): sprite_id} a JSON v2 string."""
    raw: dict[str, str] = {}
    for (gx, gy), sprite_id in grid.items():
        raw[f"{gx},{gy}"] = sprite_id
    return json.dumps({
        "version": 2,
        "ancho": ancho,
        "alto": alto,
        "grid": raw,
    }, indent=2, ensure_ascii=False)


def json_to_grid(text: str) -> tuple[Grid, int, int]:
    """Parsea JSON v2 y devuelve (grid, ancho, alto)."""
    data: dict[str, Any] = json.loads(text)
    raw: dict[str, str] = data.get("grid", {})
    grid: Grid = {}
    for key, sprite_id in raw.items():
        if "," in key:
            parts = key.split(",")
            gx, gy = int(parts[0]), int(parts[1])
            grid[(gx, gy)] = sprite_id
    return grid, data.get("ancho", 0), data.get("alto", 0)


# ── Persistencia de layers ─────────────────────────────────

def save_layer(map_id: str, z: int, ls: LayerLike, maps_dir: str) -> str:
    """Guarda una capa como JSON v2. Crea directorio si no existe."""
    suffix = "" if z == 0 else f"_z{z}"
    path = os.path.join(maps_dir, f"{map_id}{suffix}.json")
    if not ls.grid:
        if os.path.exists(path):
            os.remove(path)
        return path
    text = grid_to_json(ls.grid, ls.ancho, ls.alto)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def load_layer(map_id: str, z: int, maps_dir: str) -> tuple[Grid, int, int] | None:
    """Carga una capa desde JSON v2 o legacy .txt. Devuelve (grid, ancho, alto) o None."""
    suffix = "" if z == 0 else f"_z{z}"
    path_json = os.path.join(maps_dir, f"{map_id}{suffix}.json")
    path_txt = os.path.join(maps_dir, f"{map_id}{suffix}.txt")

    if os.path.exists(path_json):
        with open(path_json, "r", encoding="utf-8") as f:
            text = f.read()
        return json_to_grid(text)

    if os.path.exists(path_txt):
        from editor.common.parser import parsear_mapa
        with open(path_txt, "r", encoding="utf-8") as f:
            text = f.read()
        parsed = parsear_mapa(text)
        return parsed["grid"], parsed["ancho"], parsed["alto"]

    return None


# ── Persistencia de stacks ─────────────────────────────────

def save_stacks(map_id: str, stacks: Stacks, stacks_dir: str) -> str:
    """Guarda stacks (eventos) de un mapa."""
    stacks_list: list[dict[str, Any]] = []
    for key, data in stacks.items():
        entry: dict[str, Any] = {"pos": [key[0], key[1]], "z": key[2]}
        if "eventos" in data:
            entry["eventos"] = data["eventos"]
        elif "capas" in data:
            entry["eventos"] = data["capas"][0].get("eventos", []) if data.get("capas") else []
        stacks_list.append(entry)
    os.makedirs(stacks_dir, exist_ok=True)
    path = os.path.join(stacks_dir, f"{map_id}_stacks.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"stacks": stacks_list}, f, indent=2, ensure_ascii=False)
    return path


def load_stacks(map_id: str, stacks_dir: str) -> Stacks:
    """Carga stacks desde disco. Devuelve dict {(gx,gy,z): data}."""
    path = os.path.join(stacks_dir, f"{map_id}_stacks.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
        result: Stacks = {}
        for s in data.get("stacks", []):
            pos = tuple(s["pos"])
            z = s.get("z", s.get("z_layer", 0))
            eventos: list[dict[str, Any]] = s.get("eventos", [])
            if not eventos and "capas" in s:
                capas = s.get("capas", [])
                if capas:
                    for capa in capas:
                        for ev in capa.get("eventos", []):
                            old_tipo = ev.get("tipo", "")
                            new_trigger = ("contact" if old_tipo == "on_destroy" else
                                           "interact" if old_tipo == "on_interact" else "contact")
                            eventos.append({
                                "trigger": new_trigger,
                                "condiciones": [],
                                "acciones": [{"tipo": ev.get("accion", "show_message"),
                                              "params": dict(ev.get("parametros", {}))}]
                            })
            s["eventos"] = eventos
            result[(pos[0], pos[1], z)] = s
        return result
    except (json.JSONDecodeError, KeyError):
        return {}


# ── Persistencia de multi_tiles ────────────────────────────

def save_multi_tiles(map_id: str, multi_tiles: MultiTiles, maps_dir: str) -> str:
    """Guarda multi_tiles de un mapa."""
    path = os.path.join(maps_dir, f"{map_id}_multitiles.json")
    if multi_tiles:
        mt_data: dict[str, dict[str, Any]] = {}
        for (gx, gy, z), info in multi_tiles.items():
            key = f"{gx},{gy},{z}"
            mt_data[key] = info
        with open(path, "w", encoding="utf-8") as f:
            json.dump(mt_data, f, indent=2, ensure_ascii=False)
    elif os.path.exists(path):
        os.remove(path)
    return path


def load_multi_tiles(map_id: str, maps_dir: str) -> MultiTiles:
    """Carga multi_tiles desde disco. Devuelve dict {(gx,gy,z): info}."""
    path = os.path.join(maps_dir, f"{map_id}_multitiles.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw: dict[str, dict[str, Any]] = json.load(f)
        result: MultiTiles = {}
        for key, info in raw.items():
            parts = key.split(",")
            gx, gy, z = int(parts[0]), int(parts[1]), int(parts[2])
            result[(gx, gy, z)] = info
        return result
    except (json.JSONDecodeError, KeyError):
        return {}


# ── Persistencia de meta (spawn) ───────────────────────────

def save_meta(map_id: str, spawn_pos: Coords | None, spawn_z: int, maps_dir: str) -> str | None:
    """Guarda meta (spawn point) de un mapa."""
    meta: dict[str, Any] = {}
    if spawn_pos:
        meta["spawn"] = {"pos": list(spawn_pos), "z": spawn_z}
    if meta:
        path = os.path.join(maps_dir, f"{map_id}_meta.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        return path
    return None


def load_meta(map_id: str, maps_dir: str) -> dict[str, Any]:
    """Carga meta desde disco. Devuelve dict con spawn_pos, spawn_z."""
    path = os.path.join(maps_dir, f"{map_id}_meta.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            meta: dict[str, Any] = json.load(f)
        result: dict[str, Any] = {}
        spawn = meta.get("spawn")
        if spawn:
            result["spawn_pos"] = tuple(spawn["pos"])
            result["spawn_z"] = spawn.get("z", 0)
        return result
    except (json.JSONDecodeError, KeyError):
        return {}


# ── Operaciones de edición en grid ─────────────────────────

def paint_tile(ls: LayerLike, gx: int, gy: int, sprite_id: str) -> None:
    """Coloca un tile en el grid de una capa."""
    ls.grid[(gx, gy)] = sprite_id


def erase_tile(tab: TabLike, ls: LayerLike, gx: int, gy: int) -> bool:
    """Borra un tile, actualizando spawn si es necesario. Devuelve True si borró."""
    if (gx, gy) not in ls.grid:
        return False
    sid = ls.grid[(gx, gy)]
    if sid == "inicio" and tab.spawn_pos == (gx, gy):
        tab.spawn_pos = None
        tab.spawn_z = 0
    del ls.grid[(gx, gy)]
    return True


def flood_fill(ls: LayerLike, gx: int, gy: int, replacement: str) -> set[Coords]:
    """Rellena tiles conectados del mismo tipo con replacement. Devuelve set de celdas modificadas."""
    target = ls.grid.get((gx, gy))
    if target == replacement:
        return set()
    w, h = ls.ancho, ls.alto
    q: list[Coords] = [(gx, gy)]
    visited: set[Coords] = set()
    modified: set[Coords] = set()
    while q:
        cx, cy = q.pop()
        if (cx, cy) in visited:
            continue
        if cx < 0 or cx >= w or cy < 0 or cy >= h:
            continue
        if ls.grid.get((cx, cy)) != target:
            continue
        visited.add((cx, cy))
        ls.grid[(cx, cy)] = replacement
        modified.add((cx, cy))
        q.append((cx + 1, cy))
        q.append((cx - 1, cy))
        q.append((cx, cy + 1))
        q.append((cx, cy - 1))
    return modified


# ── Operaciones multi-tile ─────────────────────────────────

def paint_multi_tile(
    tab: TabLike,
    ls: LayerLike,
    gx: int,
    gy: int,
    element_id: str,
    get_element_fn: GetElementFn,
) -> list[Coords]:
    """Coloca un multi-tile en el grid. Devuelve lista de celdas pintadas."""
    el = get_element_fn(element_id)
    if not el or not el.get("multi_tile"):
        return []
    props = el.get("properties", {})
    rows: int = props.get("tile_rows", 1)
    cols: int = props.get("tile_cols", 1)
    painted: list[Coords] = []
    for r in range(rows):
        for c in range(cols):
            cx, cy = gx + c, gy + r
            if 0 <= cx < ls.ancho and 0 <= cy < ls.alto:
                ls.grid[(cx, cy)] = element_id
                painted.append((cx, cy))
    if painted:
        tab.multi_tiles[(gx, gy, tab.active_z)] = {"element_id": element_id}
    return painted


def is_multi_tile_anchor(
    tab: TabLike,
    gx: int,
    gy: int,
    z: int,
    get_element_fn: GetElementFn | None = None,
) -> Coords3 | None:
    """Devuelve la key del anchor si (gx,gy) es parte de un multi-tile, o None."""
    if get_element_fn is None:
        from editor.elements import get_element
        get_element_fn = get_element
    for (ax, ay, az), info in list(tab.multi_tiles.items()):
        if az != z:
            continue
        el = get_element_fn(info.get("element_id", ""))
        props = el.get("properties", {}) if el else {}
        rows: int = props.get("tile_rows", 1)
        cols: int = props.get("tile_cols", 1)
        if ax <= gx < ax + cols and ay <= gy < ay + rows:
            return (ax, ay, az)
    return None


def erase_multi_tile(
    tab: TabLike,
    ls: LayerLike,
    anchor_key: Coords3,
    get_element_fn: GetElementFn,
) -> None:
    """Borra un multi-tile completo desde su anchor."""
    info = tab.multi_tiles.get(anchor_key, {})
    el = get_element_fn(info.get("element_id", ""))
    props = el.get("properties", {}) if el else {}
    rows: int = props.get("tile_rows", 1)
    cols: int = props.get("tile_cols", 1)
    ax, ay, az = anchor_key
    for r in range(rows):
        for c in range(cols):
            cx, cy = ax + c, ay + r
            if (cx, cy) in ls.grid:
                del ls.grid[(cx, cy)]
    tab.multi_tiles.pop(anchor_key, None)


def scan_spawn_from_grid(tab: TabLike) -> tuple[Coords | None, int]:
    """Escanea todas las capas buscando sprite 'inicio' como spawn source of truth."""
    for z in tab.layer_order:
        ls = tab.layers.get(z)
        if ls:
            for (gx, gy), sid in ls.grid.items():
                if sid == "inicio":
                    return (gx, gy), z
    return None, 0
