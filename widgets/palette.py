import pygame
from editor.widgets.base import Widget
from editor.translation import I18n
from editor.sprite_registry import get_sprite_registry, SPRITE_TO_CHAR
from editor.elements import get_all_elements, get_element, get_element_name
from editor.behaviors import BEHAVIORS
from editor.sprite_registry import is_multi_tile
from editor.tileset import Tileset, clear_cache as clear_tileset_cache
from editor.project import get_current_project
from editor.common.sprite_loader import obtener as obtener_sprite


TOOL_SELECT = "select"
TOOL_ERASER = "eraser"
TOOL_BUCKET = "bucket"

# Filter groups: (group_key, display_label)
FILTER_GROUPS = [
    (None, "Todos"),
    ("terreno", "Terreno"),
    ("decoracion", "Decoracion"),
    ("obstaculos", "Obstaculos"),
    ("items", "Items"),
    ("enemigos", "Enemigos"),
]
FILTER_H = 16


class EntityPalette(Widget):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h)
        self.selected_sprite_id = None
        self.tool = TOOL_SELECT
        self._items = []
        self._scroll = 0
        self._item_size = 40
        self._filter_group = None
        self._mode = "elements"
        self._tileset = None
        self._build_items()

    @property
    def mode(self):
        return self._mode

    @property
    def tileset(self):
        if self._tileset is None:
            project = get_current_project()
            if project:
                self._tileset = Tileset.load_from_project(project)
        return self._tileset

    def set_mode(self, mode):
        if mode not in ("elements", "tileset"):
            raise ValueError(f"Invalid mode: {mode}. Must be 'elements' or 'tileset'")
        if mode != self._mode:
            self._mode = mode
            self._scroll = 0
            self._build_items()

    def refresh_tileset(self):
        clear_tileset_cache()
        self._tileset = None
        if self._mode == "tileset":
            self._build_items()

    def _filter_label(self):
        for key, label in FILTER_GROUPS:
            if key == self._filter_group:
                return label
        return "Todos"

    def _get_element_group(self, eid):
        el = get_element(eid)
        if not el:
            return None
        beh = el.get("behavior", "decorative")
        bdata = BEHAVIORS.get(beh)
        return bdata.get("group") if bdata else None

    def _build_items(self):
        self._items = []
        if self._mode == "tileset":
            ts = self.tileset
            if ts and ts.tiles:
                for index, tile in enumerate(ts.tiles):
                    if tile:
                        self._items.append((index, tile, f"Tile {index}", f"tileset:{index}"))
            return

        for eid in get_all_elements():
            if self._filter_group is not None:
                g = self._get_element_group(eid)
                if g != self._filter_group:
                    continue
            el = get_element(eid)
            if not el:
                continue
            sprite_id = el.get("sprite_id")
            info = get_sprite_registry().get(sprite_id) if sprite_id else None
            sprite = obtener_sprite(info["file"]) if info and info.get("file") else None
            display = el.get("name", eid)
            self._items.append((eid, sprite, display, sprite_id))

    def _abs_rect(self):
        if self.parent:
            pr = self.parent.get_abs_rect() if hasattr(self.parent, 'get_abs_rect') else self.parent.rect
            return pygame.Rect(pr.x + self.rect.x, pr.y + self.rect.y, self.rect.w, self.rect.h)
        return self.rect.copy()

    def _filter_rect(self, r):
        return pygame.Rect(r.x, r.y, r.w, FILTER_H)

    def _grid_rect(self, r):
        return pygame.Rect(r.x, r.y + FILTER_H, r.w, r.h - FILTER_H)

    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return False
        r = self._abs_rect()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if not r.collidepoint(mx, my):
                return False
            # Click en filtro (toda la barra superior cicla entre grupos)
            if self._filter_rect(r).collidepoint(mx, my):
                keys = [k for k, _ in FILTER_GROUPS]
                idx = keys.index(self._filter_group)
                self._filter_group = keys[(idx + 1) % len(keys)]
                self._scroll = 0
                return True
            # Click en grid
            gr = self._grid_rect(r)
            if not gr.collidepoint(mx, my):
                return False
            cols = max(1, gr.w // self._item_size)
            local_x = mx - gr.x
            local_y = my - gr.y + self._scroll
            col = local_x // self._item_size
            row = local_y // self._item_size
            idx = row * cols + col
            if 0 <= idx < len(self._items):
                selected = self._items[idx][0]
                if selected == self.selected_sprite_id:
                    self.selected_sprite_id = None
                else:
                    self.selected_sprite_id = selected
                return True

        if event.type == pygame.MOUSEWHEEL:
            self._scroll = max(0, self._scroll - event.y * 20)
            return True
        return False

    def draw(self, surface):
        if not self.visible:
            return
        self._build_items()
        r = self._abs_rect()
        i18n = I18n.instancia()
        fpeq = i18n.fuente(11) if i18n else pygame.font.SysFont("Arial", 11)
        fuente = i18n.fuente(10) if i18n else pygame.font.SysFont("Arial", 10)

        pygame.draw.rect(surface, (35, 40, 45), r)
        pygame.draw.rect(surface, (55, 60, 65), r, 1)

        # Filter bar
        fr = self._filter_rect(r)
        pygame.draw.rect(surface, (50, 55, 65), fr)
        pygame.draw.rect(surface, (60, 65, 75), fr, 1)
        filtro_txt = f"F: {self._filter_label()} ▼"
        sf = fpeq.render(filtro_txt, True, (180, 190, 200))
        surface.blit(sf, (fr.x + 4, fr.y + 2))

        # Grid area
        gr = self._grid_rect(r)
        clip = surface.get_clip()
        surface.set_clip(gr)

        cols = max(1, gr.w // self._item_size)
        item_top = 4

        for i, item in enumerate(self._items):
            eid, sprite, display, sprite_id = item if len(item) == 4 else (item[0], item[1], item[2], item[0])
            col = i % cols
            row = i // cols
            sx = gr.x + col * self._item_size
            sy = gr.y + item_top + row * self._item_size - self._scroll
            if sy + self._item_size < r.y or sy > r.y + r.h:
                continue

            bg = (55, 60, 70) if eid == self.selected_sprite_id else (40, 45, 50)
            pygame.draw.rect(surface, bg, (sx, sy, self._item_size, self._item_size))
            pygame.draw.rect(surface, (60, 65, 70), (sx, sy, self._item_size, self._item_size), 1)

            if sprite:
                if self._mode == "tileset" or not is_multi_tile(sprite_id):
                    surface.blit(sprite, (sx + (self._item_size - sprite.get_width()) // 2, sy + (self._item_size - sprite.get_height()) // 2))
                else:
                    sp_w, sp_h = sprite.get_size()
                    scale = min(self._item_size / sp_w, self._item_size / sp_h, 1.0)
                    if scale < 1:
                        preview = pygame.transform.smoothscale(sprite, (int(sp_w * scale), int(sp_h * scale)))
                    else:
                        preview = sprite
                    px = sx + (self._item_size - preview.get_width()) // 2
                    py = sy + (self._item_size - preview.get_height()) // 2
                    surface.blit(preview, (px, py))
            else:
                pygame.draw.rect(surface, (100, 100, 100), (sx + 8, sy + 8, 4, 4))

            label = display if len(display) <= 12 else display[:11] + "."
            txt = fuente.render(label, True, (180, 180, 180))
            surface.blit(txt, (sx + 2, sy + self._item_size - 12))

        surface.set_clip(clip)

    @property
    def selected_char(self):
        if self.selected_sprite_id:
            return SPRITE_TO_CHAR.get(self.selected_sprite_id)
        return None

    @selected_char.setter
    def selected_char(self, value):
        from editor.sprite_registry import CHAR_TO_SPRITE
        if value is None:
            self.selected_sprite_id = None
        else:
            self.selected_sprite_id = CHAR_TO_SPRITE.get(value)
