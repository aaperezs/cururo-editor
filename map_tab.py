import copy


class LayerState:
    def __init__(self):
        self.grid = {}
        self.ancho = 0
        self.alto = 0
        self.visible = False
        self.opacity = 100

    def clone(self):
        c = LayerState()
        c.grid = copy.deepcopy(self.grid)
        c.ancho = self.ancho
        c.alto = self.alto
        c.visible = self.visible
        c.opacity = self.opacity
        return c


class MapTab:
    MAX_LAYERS = 5

    def __init__(self, map_id=None):
        self.map_id = map_id
        self.dirty = False
        self.undo_stack = []
        self.redo_stack = []
        self.layers = {}
        self.layers[0] = LayerState()
        self.stacks = {}
        self.multi_tiles = {}  # {(anchor_gx, anchor_gy, z): {"element_id": str, "subtiles": [...]}}
        self.active_z = 0
        self.spawn_pos = None
        self.spawn_z = 0
        self._max_undo = 50

    @property
    def layer_count(self):
        return len(self.layers)

    @property
    def layer_order(self):
        return sorted(self.layers.keys())

    def add_layer(self):
        if self.layer_count >= self.MAX_LAYERS:
            return None
        for z in range(1, self.MAX_LAYERS):
            if z not in self.layers:
                ls = LayerState()
                # Inherit dimensions from base layer (0)
                base = self.layers.get(0)
                if base:
                    ls.ancho = base.ancho
                    ls.alto = base.alto
                ls.visible = True
                ls.opacity = 100
                self.layers[z] = ls
                return z
        return None

    def remove_layer(self, z):
        if z == 0 or z not in self.layers:
            return False
        if self.active_z == z:
            candidates = [k for k in sorted(self.layers.keys(), reverse=True) if k < z]
            self.active_z = candidates[0] if candidates else 0
        del self.layers[z]
        return True

    def label(self):
        base = self.map_id if self.map_id else "sin_titulo"
        return f"{base}*" if self.dirty else base

    def snapshot(self):
        return {
            "layers": {z: self.layers[z].clone() for z in self.layers},
            "stacks": copy.deepcopy(self.stacks),
            "multi_tiles": copy.deepcopy(self.multi_tiles),
            "active_z": self.active_z,
            "spawn_pos": self.spawn_pos,
            "spawn_z": self.spawn_z,
        }

    def push_undo(self):
        self.undo_stack.append(self.snapshot())
        if len(self.undo_stack) > self._max_undo:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
        self.dirty = True

    def undo(self):
        if not self.undo_stack:
            return False
        self.redo_stack.append(self.snapshot())
        prev = self.undo_stack.pop()
        self._restore(prev)
        self.dirty = True
        return True

    def redo(self):
        if not self.redo_stack:
            return False
        self.undo_stack.append(self.snapshot())
        nxt = self.redo_stack.pop()
        self._restore(nxt)
        self.dirty = True
        return True

    def _restore(self, state):
        for z, ls in state["layers"].items():
            if z in self.layers:
                self.layers[z].grid = copy.deepcopy(ls.grid)
                self.layers[z].ancho = ls.ancho
                self.layers[z].alto = ls.alto
                self.layers[z].visible = ls.visible
                self.layers[z].opacity = ls.opacity
        self.stacks = copy.deepcopy(state["stacks"])
        self.multi_tiles = copy.deepcopy(state.get("multi_tiles", {}))
        self.active_z = state["active_z"]
        self.spawn_pos = state.get("spawn_pos")
        self.spawn_z = state.get("spawn_z", 0)
