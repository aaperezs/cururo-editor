import pygame
from editor.widgets.base import Widget
from editor.menu.dropdown import MenuDropdown


SECTION_PAD_X = 14
SECTION_PAD_Y = 4


class MenuBar(Widget):
    HEIGHT = 26

    def __init__(self, x, y, w):
        super().__init__(x, y, w, self.HEIGHT)
        self.sections = []
        self._open_section = -1
        self._hover_section = -1
        self._dropdown = None
        self._section_positions = []

    def add_section(self, label, items):
        self.sections.append({"label": label, "items": items})

    def is_open(self):
        return self._open_section >= 0

    def close_all(self):
        self._open_section = -1
        self._dropdown = None

    def _get_font(self):
        return pygame.font.SysFont("Segoe UI", 13)

    def _build_positions(self):
        fuente = self._get_font()
        self._section_positions = []
        cx = self._abs_rect().x + SECTION_PAD_X
        cy = self._abs_rect().y
        for sec in self.sections:
            tw = fuente.size(sec["label"])[0]
            sx, sy = cx + 4, cy + SECTION_PAD_Y
            sw = tw + 16
            sh = self.HEIGHT - SECTION_PAD_Y * 2
            self._section_positions.append(pygame.Rect(sx, sy, sw, sh))
            cx += sw + 4

    def get_section_at(self, mx, my):
        for i, r in enumerate(self._section_positions):
            if r.collidepoint(mx, my):
                return i
        return -1

    def handle_event(self, event):
        if not self.visible:
            return False

        r = self._abs_rect()
        mx, my = event.pos if hasattr(event, 'pos') else (0, 0)

        if self._open_section >= 0 and self._dropdown:
            if self._dropdown.handle_event(event):
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.close_all()
                return True
            if event.type == pygame.MOUSEMOTION:
                self._build_positions()
                self._hover_section = self.get_section_at(mx, my)
                if self._hover_section >= 0 and self._hover_section != self._open_section:
                    self._open_section = self._hover_section
                    self._update_dropdown()
                return True
            if event.type == pygame.MOUSEBUTTONDOWN:
                if r.collidepoint(mx, my):
                    self._build_positions()
                    idx = self.get_section_at(mx, my)
                    if idx >= 0:
                        if idx == self._open_section:
                            self.close_all()
                        else:
                            self._open_section = idx
                            self._update_dropdown()
                        return True
                elif not self._dropdown._abs_rect().collidepoint(mx, my):
                    self.close_all()
                    return False
                return True

        if event.type == pygame.MOUSEMOTION:
            inside = r.collidepoint(mx, my)
            if inside:
                self._build_positions()
                self._hover_section = self.get_section_at(mx, my)
            else:
                self._hover_section = -1
            return inside  # only consume events inside menu bar

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if r.collidepoint(mx, my):
                self._build_positions()
                idx = self.get_section_at(mx, my)
                if idx >= 0:
                    if self._open_section == idx:
                        self.close_all()
                    else:
                        self._open_section = idx
                        self._update_dropdown()
                    return True
            return False

        return False

    def _update_dropdown(self):
        if self._open_section < 0 or self._open_section >= len(self.sections):
            self._dropdown = None
            return
        sec = self.sections[self._open_section]
        r = self._abs_rect()
        if self._section_positions and self._open_section < len(self._section_positions):
            sr = self._section_positions[self._open_section]
            dx = sr.x
        else:
            dx = r.x + SECTION_PAD_X
        dy = r.y + self.HEIGHT
        self._dropdown = MenuDropdown(dx, dy, sec["items"])

    def draw(self, surface):
        if not self.visible:
            return
        r = self._abs_rect()
        fuente = self._get_font()

        # Background
        pygame.draw.rect(surface, (32, 35, 42), r)
        # Bottom border (more visible than background)
        pygame.draw.line(surface, (55, 60, 70), (r.x, r.y + r.h - 1),
                         (r.x + r.w - 1, r.y + r.h - 1), 2)

        self._build_positions()

        for i, sec in enumerate(self.sections):
            sr = self._section_positions[i]
            is_open = i == self._open_section
            is_hover = i == self._hover_section and not is_open

            if is_open:
                pygame.draw.rect(surface, (38, 42, 50), sr, border_radius=3)
            elif is_hover:
                pygame.draw.rect(surface, (35, 38, 46), sr, border_radius=3)

            label_color = (220, 222, 228) if (is_open or is_hover) else (170, 175, 185)
            txt = fuente.render(sec["label"], True, label_color)
            tx = sr.x + (sr.w - txt.get_width()) // 2
            ty = sr.y + (sr.h - txt.get_height()) // 2
            surface.blit(txt, (tx, ty))

    def draw_dropdown(self, surface):
        if self._dropdown and self._open_section >= 0:
            self._dropdown.draw(surface)
