"""Herramientas de edición del mapa — pintar, borrar, cubo, arrastrar.

Extrae la lógica de interacción (start/drag/stop) del MapEditorPanel.
Cada método opera sobre el tab (modelo) y notifica cambios via callbacks.
"""

from __future__ import annotations

from typing import Any, Callable

from editor.elements import is_multi_tile_element
from editor.map_model import (
    Grid,
    Coords,
    Coords3,
    GetElementFn,
    TabLike,
    LayerLike,
    paint_tile,
    erase_tile,
    flood_fill,
    paint_multi_tile as _paint_multi_tile,
    is_multi_tile_anchor as _is_multi_tile_anchor,
    erase_multi_tile as _erase_multi_tile,
)


class MapTools:
    """Gestiona las herramientas de edición del mapa."""

    def __init__(self, get_element_fn: GetElementFn | None = None) -> None:
        self.active_tool: str = "select"
        self.selected_sprite_id: str | None = None
        self.is_dragging: bool = False
        self.drag_button: int = 0
        self.last_paint_pos: Coords | None = None
        self.drag_source: tuple[int, int, str, int] | None = None  # (gx, gy, sprite_id, z)
        self._get_element: GetElementFn | None = get_element_fn

    def set_tool(self, tool: str) -> None:
        self.active_tool = tool
        if tool in ("eraser", "drag"):
            self.selected_sprite_id = None

    def set_sprite(self, sprite_id: str) -> None:
        self.selected_sprite_id = sprite_id

    # ── Click simple en el mapa ─────────────────────────────

    def handle_map_click(self, tab: TabLike, gx: int, gy: int, get_element_fn: GetElementFn) -> bool:
        """Maneja click izquierdo en el mapa. Devuelve True si procesó."""
        ls = tab.layers.get(tab.active_z)
        if not ls or gx < 0 or gx >= ls.ancho or gy < 0 or gy >= ls.alto:
            return False

        if self.selected_sprite_id is not None:
            tab.push_undo()
            if is_multi_tile_element(self.selected_sprite_id):
                _paint_multi_tile(tab, ls, gx, gy, self.selected_sprite_id, get_element_fn)
            else:
                paint_tile(ls, gx, gy, self.selected_sprite_id)
            if self.selected_sprite_id == "inicio":
                tab.spawn_pos = (gx, gy)
                tab.spawn_z = tab.active_z
            tab.dirty = True
            return True

        # Click sin sprite seleccionado: solo selección (no-op aquí)
        return False

    # ── Start paint/erase drag ──────────────────────────────

    def start_drag(self, tab: TabLike, gx: int, gy: int, button: int, get_element_fn: GetElementFn) -> bool:
        """Inicia una operación de pintar/borrar/bucket. Devuelve True si procesó."""
        ls = tab.layers.get(tab.active_z)
        if not ls or gx < 0 or gx >= ls.ancho or gy < 0 or gy >= ls.alto:
            return False

        # Bucket (clic único, sin drag)
        if button == 1 and self.active_tool == "bucket":
            tab.push_undo()
            flood_fill(ls, gx, gy, self.selected_sprite_id or "")
            tab.dirty = True
            return True

        # Iniciar drag
        tab.push_undo()
        self.is_dragging = True
        self.drag_button = button
        self.last_paint_pos = (gx, gy)

        # Eraser en click
        if button == 1 and self.active_tool == "eraser":
            anchor = _is_multi_tile_anchor(tab, gx, gy, tab.active_z, self._get_element)
            if anchor:
                _erase_multi_tile(tab, ls, anchor, get_element_fn)
            else:
                erase_tile(tab, ls, gx, gy)

        # Paint en click
        if button == 1 and self.selected_sprite_id is not None:
            if is_multi_tile_element(self.selected_sprite_id):
                _paint_multi_tile(tab, ls, gx, gy, self.selected_sprite_id, get_element_fn)
            else:
                paint_tile(ls, gx, gy, self.selected_sprite_id)
            if self.selected_sprite_id == "inicio":
                tab.spawn_pos = (gx, gy)
                tab.spawn_z = tab.active_z

        # Click derecho = borrar
        elif button == 3:
            anchor = _is_multi_tile_anchor(tab, gx, gy, tab.active_z, self._get_element)
            if anchor:
                _erase_multi_tile(tab, ls, anchor, get_element_fn)
            else:
                erase_tile(tab, ls, gx, gy)

        tab.dirty = True
        return True

    # ── Drag continuo ───────────────────────────────────────

    def continue_drag(self, tab: TabLike, gx: int, gy: int, get_element_fn: GetElementFn) -> None:
        """Continúa el drag hacia (gx, gy). Interpola tiles."""
        ls = tab.layers.get(tab.active_z)
        if not ls or self.last_paint_pos is None:
            return
        if self.last_paint_pos == (gx, gy):
            return

        lx, ly = self.last_paint_pos
        dx = gx - lx
        dy = gy - ly
        steps = max(abs(dx), abs(dy))

        if steps > 0:
            for i in range(1, steps + 1):
                ix = lx + int(dx * i / steps)
                iy = ly + int(dy * i / steps)
                if 0 <= ix < ls.ancho and 0 <= iy < ls.alto:
                    if self.drag_button == 1 and self.active_tool == "eraser":
                        anchor = _is_multi_tile_anchor(tab, ix, iy, tab.active_z, self._get_element)
                        if anchor:
                            _erase_multi_tile(tab, ls, anchor, get_element_fn)
                        else:
                            erase_tile(tab, ls, ix, iy)
                        tab.dirty = True
                    elif self.drag_button == 1 and self.selected_sprite_id is not None:
                        if is_multi_tile_element(self.selected_sprite_id):
                            _paint_multi_tile(tab, ls, ix, iy, self.selected_sprite_id, get_element_fn)
                        else:
                            paint_tile(ls, ix, iy, self.selected_sprite_id)
                        if self.selected_sprite_id == "inicio":
                            tab.spawn_pos = (ix, iy)
                            tab.spawn_z = tab.active_z
                        tab.dirty = True
                    elif self.drag_button == 3:
                        anchor = _is_multi_tile_anchor(tab, ix, iy, tab.active_z, self._get_element)
                        if anchor:
                            _erase_multi_tile(tab, ls, anchor, get_element_fn)
                        elif (ix, iy) in ls.grid:
                            erase_tile(tab, ls, ix, iy)
                            tab.dirty = True

        self.last_paint_pos = (gx, gy)

    # ── Stop drag ───────────────────────────────────────────

    def stop_drag(self) -> None:
        """Detiene el drag activo."""
        self.is_dragging = False
        self.last_paint_pos = None

    # ── Drag tool (mover tile de un sitio a otro) ───────────

    def handle_drag_click(self, tab: TabLike, gx: int, gy: int) -> bool:
        """Maneja click con herramienta drag. Devuelve True si procesó."""
        ls = tab.layers.get(tab.active_z)
        if not ls or gx < 0 or gx >= ls.ancho or gy < 0 or gy >= ls.alto:
            return False

        if self.drag_source is None:
            # Pick up
            sid = ls.grid.get((gx, gy))
            if sid is None:
                return False
            anchor = _is_multi_tile_anchor(tab, gx, gy, tab.active_z, self._get_element)
            if anchor:
                return False
            self.drag_source = (gx, gy, sid, tab.active_z)
            return True

        # Place
        sx, sy, sid, sz = self.drag_source
        if sz != tab.active_z:
            return False
        if sx == gx and sy == gy:
            self.drag_source = None
            return True

        tab.push_undo()
        ls.grid[(gx, gy)] = sid
        del ls.grid[(sx, sy)]

        if sid == "inicio" and tab.spawn_pos == (sx, sy):
            tab.spawn_pos = (gx, gy)
            tab.spawn_z = tab.active_z

        # Mover eventos
        src_key: Coords3 = (sx, sy, tab.active_z)
        dst_key: Coords3 = (gx, gy, tab.active_z)
        if src_key in tab.stacks:
            tab.stacks[dst_key] = tab.stacks.pop(src_key)

        self.drag_source = None
        tab.dirty = True
        return True

    def cancel_drag(self) -> None:
        """Cancela la operación de drag tool."""
        self.drag_source = None
