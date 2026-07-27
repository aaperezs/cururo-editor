import pygame
from editor.widgets.base import Widget
from editor.translation import I18n

CHECKBOX_KEYS = ["solid", "destructible", "pushable",]
DROPDOWN_KEYS = ["damage_type"]
DROPDOWN_OPTIONS = {
    "damage_type": ["none", "mata", "dano"],
}


class PropertyEditor(Widget):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h)
        self._properties = {}
        self._sprite_id = ""
        self._file = ""
        self._entity = ""
        self._row_h = 24
        self._hover = -1
        self._on_property_change = None

    def set_properties(self, sprite_id, file_name, entity_name, props):
        self._sprite_id = sprite_id
        self._file = file_name
        self._entity = entity_name
        self._properties = dict(props)

    def get_properties(self):
        return dict(self._properties)

    def set_on_change(self, callback):
        self._on_property_change = callback

    def _abs_rect(self):
        if self.parent:
            pr = self.parent.get_abs_rect() if hasattr(self.parent, 'get_abs_rect') else self.parent.rect
            return pygame.Rect(pr.x + self.rect.x, pr.y + self.rect.y, self.rect.w, self.rect.h)
        return self.rect.copy()

    def _get_checkbox_rect(self, row_idx):
        r = self._abs_rect()
        return pygame.Rect(r.x + 8, r.y + 48 + row_idx * self._row_h, 14, 14)

    def _get_dropdown_rect(self, row_idx):
        r = self._abs_rect()
        return pygame.Rect(r.x + 28, r.y + 48 + row_idx * self._row_h, r.w - 36, 18)

    def _get_prop_rows(self):
        rows = []
        for key in CHECKBOX_KEYS:
            if key in self._properties:
                rows.append(("checkbox", key))
        for key in DROPDOWN_KEYS:
            if key in self._properties:
                rows.append(("dropdown", key))
        return rows

    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return False
        r = self._abs_rect()
        rows = self._get_prop_rows()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if not r.collidepoint(mx, my):
                return False

            for i, (typ, key) in enumerate(rows):
                if typ == "checkbox":
                    cb = self._get_checkbox_rect(i)
                    if cb.collidepoint(mx, my):
                        self._properties[key] = not self._properties[key]
                        if self._on_property_change:
                            self._on_property_change(key, self._properties[key])
                        return True

                elif typ == "dropdown":
                    dd = self._get_dropdown_rect(i)
                    if dd.collidepoint(mx, my):
                        opts = DROPDOWN_OPTIONS.get(key, [])
                        if opts:
                            cur = self._properties.get(key, opts[0])
                            try:
                                idx = opts.index(cur)
                            except ValueError:
                                idx = 0
                            nxt = opts[(idx + 1) % len(opts)]
                            self._properties[key] = nxt
                            if self._on_property_change:
                                self._on_property_change(key, nxt)
                        return True

        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self._hover = -1
            for i, (typ, key) in enumerate(rows):
                if typ == "dropdown":
                    dd = self._get_dropdown_rect(i)
                    if dd.collidepoint(mx, my):
                        self._hover = i
                        break

        return False

    def draw(self, surface):
        if not self.visible:
            return
        r = self._abs_rect()
        i18n = I18n.instancia()
        fuente = i18n.fuente(12) if i18n else pygame.font.SysFont("Arial", 12)
        fuente_peq = i18n.fuente(11) if i18n else pygame.font.SysFont("Arial", 11)

        pygame.draw.rect(surface, (35, 40, 48), r)
        pygame.draw.rect(surface, (55, 60, 68), r, 1)

        titulo = fuente.render(i18n.t("sprite.properties") if i18n else "Properties", True, (180, 190, 200))
        surface.blit(titulo, (r.x + 6, r.y + 4))

        info_lines = [
            f"ID: {self._sprite_id}",
            f"File: {self._file}.png",
            f"Entity: {self._entity}",
        ]
        y = r.y + 24
        for line in info_lines:
            txt = fuente_peq.render(line, True, (140, 145, 155))
            surface.blit(txt, (r.x + 6, y))
            y += 14

        rows = self._get_prop_rows()
        for i, (typ, key) in enumerate(rows):
            y = r.y + 48 + i * self._row_h
            val = self._properties.get(key)
            display_key = i18n.t(f"sprite.prop.{key}") if i18n else key

            if typ == "checkbox":
                cb = self._get_checkbox_rect(i)
                check_color = (80, 160, 80) if val else (60, 65, 75)
                pygame.draw.rect(surface, check_color, cb)
                pygame.draw.rect(surface, (100, 105, 115), cb, 1)
                if val:
                    # Checkmark
                    pts = [(cb.x + 2, cb.y + 7), (cb.x + 5, cb.y + 10), (cb.x + 11, cb.y + 3)]
                    pygame.draw.lines(surface, (220, 255, 220), False, pts, 2)
                txt = fuente_peq.render(display_key, True, (200, 200, 200))
                surface.blit(txt, (cb.x + 20, cb.y - 1))

            elif typ == "dropdown":
                dd = self._get_dropdown_rect(i)
                lbl = fuente_peq.render(display_key + ":", True, (200, 200, 200))
                surface.blit(lbl, (dd.x - 40, dd.y))
                bg = (60, 75, 90) if self._hover == i else (50, 60, 75)
                pygame.draw.rect(surface, bg, dd)
                pygame.draw.rect(surface, (80, 95, 115), dd, 1)
                display_val = i18n.t(f"sprite.prop.{key}.{val}") if i18n else str(val)
                vt = fuente_peq.render(display_val, True, (200, 200, 200))
                surface.blit(vt, (dd.x + 4, dd.y + (dd.h - vt.get_height()) // 2))
                # Dropdown arrow
                pygame.draw.polygon(surface, (140, 145, 155),
                                    [(dd.x + dd.w - 12, dd.y + 4),
                                     (dd.x + dd.w - 4, dd.y + 4),
                                     (dd.x + dd.w - 8, dd.y + 12)])
