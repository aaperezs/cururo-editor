"""Map file I/O — load, save, create, resize maps.

Pure logic operating on MapTab instances. No pygame, no widget updates.
Extracted from MapEditorPanel to separate data persistence from GUI.
"""

from __future__ import annotations

from typing import Optional

from editor.map_tab import MapTab
from editor.map_model import (
    load_layer, save_layer, load_stacks, save_stacks,
    load_multi_tiles, save_multi_tiles, load_meta, save_meta,
    scan_spawn_from_grid,
)


def create_new_map(w: int, h: int) -> MapTab:
    """Create a new MapTab with given dimensions."""
    tab = MapTab(map_id=None)
    tab.layers[0].ancho = w
    tab.layers[0].alto = h
    tab.layers[0].visible = True
    tab.layers[0].opacity = 100
    uid = f"_new_{id(tab)}"
    tab.map_id = uid
    return tab


def load_map(tab: MapTab, map_id: str, maps_dir: str, stacks_dir: str) -> None:
    """Load a map from disk into an existing MapTab.

    Populates layers, stacks, multi_tiles, and spawn point.
    """
    def _try_load_layer(z: int) -> bool:
        result = load_layer(map_id, z, maps_dir)
        if result is None:
            return False
        grid, ancho, alto = result
        if z not in tab.layers:
            tab.layers[z] = tab.layers[0].__class__()
        tab.layers[z].grid = grid
        tab.layers[z].ancho = ancho
        tab.layers[z].alto = alto
        return True

    if _try_load_layer(0):
        tab.layers[0].visible = True
        tab.layers[0].opacity = 100
    else:
        tab.layers[0].ancho = 40
        tab.layers[0].alto = 30
        tab.layers[0].visible = True
        tab.layers[0].opacity = 100

    for z in range(1, 5):
        if _try_load_layer(z):
            tab.layers[z].visible = True
            tab.layers[z].opacity = 100

    tab.stacks = load_stacks(map_id, stacks_dir)
    tab.multi_tiles = load_multi_tiles(map_id, maps_dir)

    meta = load_meta(map_id, maps_dir)
    if meta:
        tab.spawn_pos = meta.get("spawn_pos")
        tab.spawn_z = meta.get("spawn_z", 0)

    if not tab.spawn_pos:
        spawn_pos, spawn_z = scan_spawn_from_grid(tab)
        if spawn_pos:
            tab.spawn_pos = spawn_pos
            tab.spawn_z = spawn_z


def resize_map(tab: MapTab, nuevo_w: int, nuevo_h: int) -> None:
    """Resize a map tab, cropping layers and multi_tiles outside new bounds."""
    tab.push_undo()

    for z, ls in tab.layers.items():
        old_w = ls.ancho
        old_h = ls.alto
        if nuevo_w < old_w or nuevo_h < old_h:
            ls.grid = {
                (gx, gy): sid
                for (gx, gy), sid in ls.grid.items()
                if gx < nuevo_w and gy < nuevo_h
            }
        ls.ancho = nuevo_w
        ls.alto = nuevo_h

    for key in list(tab.multi_tiles.keys()):
        gx, gy, z = key
        if gx >= nuevo_w or gy >= nuevo_h:
            del tab.multi_tiles[key]


def save_map(tab: MapTab, maps_dir: str, stacks_dir: str) -> None:
    """Write all map data to disk."""
    map_id = tab.map_id
    if not map_id or map_id.startswith("_new_"):
        return

    for z, ls in tab.layers.items():
        save_layer(map_id, z, ls, maps_dir)

    save_stacks(map_id, tab.stacks, stacks_dir)
    save_multi_tiles(map_id, tab.multi_tiles, maps_dir)

    spawn_pos, spawn_z = scan_spawn_from_grid(tab)
    if spawn_pos:
        tab.spawn_pos = spawn_pos
        tab.spawn_z = spawn_z
    elif tab.spawn_pos:
        ls = tab.layers.get(tab.spawn_z)
        if not ls or ls.grid.get(tab.spawn_pos) != "inicio":
            tab.spawn_pos = None
            tab.spawn_z = 0

    save_meta(map_id, tab.spawn_pos, tab.spawn_z, maps_dir)
    tab.dirty = False


def get_workspace_data(
    tabs: dict[str, MapTab],
    tab_order: list[str],
    active_tab_id: Optional[str],
    zoom: float,
    scroll_x: int = 0,
    scroll_y: int = 0,
) -> dict:
    """Serialize editor state for workspace persistence."""
    data = {
        "open_tabs": list(tab_order),
        "active_tab": active_tab_id,
    }
    tabs_data = {}
    for tid, tab in tabs.items():
        tabs_data[tid] = {
            "active_z": tab.active_z,
            "spawn_pos": list(tab.spawn_pos) if tab.spawn_pos else None,
            "spawn_z": tab.spawn_z,
            "zoom": zoom,
            "scroll_x": scroll_x,
            "scroll_y": scroll_y,
        }
    data["tabs"] = tabs_data
    return data


def sync_events_from_widget(tab: MapTab, selected_pos, selected_z, eventos) -> None:
    """Write events from the event widget back into tab.stacks."""
    if selected_pos:
        key = (selected_pos[0], selected_pos[1], selected_z)
        if key in tab.stacks:
            tab.stacks[key]["eventos"] = eventos
        else:
            tab.stacks[key] = {"pos": list(selected_pos), "z": selected_z, "eventos": eventos}
