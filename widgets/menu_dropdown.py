import pygame
from editor.widgets.base import Widget
from editor.widgets.menu_item import MenuItem


class MenuDropdown(Widget):
    ITEM_H = 24
    PAD_X = 12
    PAD_Y = 4
    MIN_W = 180

    def __init__(self, x, y, items):
        super().__init__(x, y)
        self.items = items
        self._hover_index = -1
        self._calc_size()

    def _calc_size(self):
        fuente = pygame.font.SysFont("Segoe UI", 13)
        max_w = self.MIN_W
        n = len(self.items)
        for item in self.items:
            tw = fuente.size(item.label)[0]
            if item.shortcut:
                tw += fuente.size("  " + item.shortcut)[0]
            tw += self.PAD_X * 2 + 16
            max_w = max(max_w, tw)
        self.rect.w = max_w
        self.rect.h = n * self.ITEM_H + self.PAD_Y * 2

    def get_item_at(self, mx, my):
        r = self._abs_rect()
        if not r.collidepoint(mx, my):
            return -1
        local_y = my - r.y - self.PAD_Y
        idx = local_y // self.ITEM_H
        if 0 <= idx < len(self.items):
            return idx
        return -1

    def handle_event(self, event):
        if not self.visible:
            return False
        r = self._abs_rect()
        if event.type == pygame.MOUSEMOTION:
            inside = r.collidepoint(*event.pos)
            self._hover_index = self.get_item_at(*event.pos) if inside else -1
            return inside
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            idx = self.get_item_at(*event.pos)
            if idx >= 0 and idx < len(self.items):
                item = self.items[idx]
                if item.enabled:
                    if item.action:
                        item.action()
                    return True
            return False
        return False

    def draw(self, surface):
        if not self.visible:
            return
        r = self._abs_rect()
        fuente = pygame.font.SysFont("Segoe UI", 13)

        # Sombra
        shadow_rect = pygame.Rect(r.x + 2, r.y + 2, r.w, r.h)
        shadow_surf = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 80))
        surface.blit(shadow_surf, (r.x + 2, r.y + 2))

        # Fondo
        pygame.draw.rect(surface, (38, 42, 50), r, border_radius=4)
        pygame.draw.rect(surface, (60, 65, 75), r, 1, border_radius=4)

        for i, item in enumerate(self.items):
            yi = r.y + self.PAD_Y + i * self.ITEM_H
            item_rect = pygame.Rect(r.x + 2, yi, r.w - 4, self.ITEM_H)

            # Separator
            if item.separator_before:
                sep_y = yi - 1
                pygame.draw.line(surface, (60, 65, 75),
                                 (r.x + 8, sep_y), (r.x + r.w - 8, sep_y))

            # Hover
            if i == self._hover_index and item.enabled:
                pygame.draw.rect(surface, (55, 60, 72), item_rect, border_radius=3)

            # Label
            label_color = (180, 185, 195) if item.enabled else (80, 85, 95)
            txt = fuente.render(item.label, True, label_color)
            surface.blit(txt, (r.x + self.PAD_X + 4, yi + (self.ITEM_H - txt.get_height()) // 2))

            # Shortcut
            if item.shortcut and item.enabled:
                sc_color = (110, 115, 125)
                sc = fuente.render(item.shortcut, True, sc_color)
                sc_x = r.x + r.w - self.PAD_X - 4 - sc.get_width()
                sc_y = yi + (self.ITEM_H - sc.get_height()) // 2
                surface.blit(sc, (sc_x, sc_y))
