"""Preview viewport widget for the sprite editor."""

import pygame

from editor.widgets.base import Widget
from editor.ui.theme import Theme


class PreviewViewport(Widget):
    """Preview viewport showing sprite at 1:1 scale, centered, clipped."""

    def __init__(self, x, y, w, h, get_surface, get_cut_cell):
        super().__init__(x, y, w, h)
        self.get_surface = get_surface  # callable -> pygame.Surface
        self.get_cut_cell = get_cut_cell  # callable -> (cell_w, cell_h)
        self._checker_cache = None
        self._checker_size = (0, 0)

    def draw(self, surface):
        if not self.visible:
            return

        theme = Theme.get()
        r = self.get_abs_rect()

        # Get sprite surface
        sprite_surf = self.get_surface()
        if not sprite_surf:
            return

        # Determine tile size (for multi-tile sprites)
        cut_w, cut_h = self.get_cut_cell()
        rows = sprite_surf.get_height() // cut_h if cut_h > 0 else 1
        cols = sprite_surf.get_width() // cut_w if cut_w > 0 else 1

        if cols > 1 or rows > 1:
            tile_surf = sprite_surf.subsurface((0, 0, cut_w, cut_h))
            sw, sh = tile_surf.get_width(), tile_surf.get_height()
        else:
            tile_surf = sprite_surf
            sw, sh = sprite_surf.get_width(), sprite_surf.get_height()

        # 1:1 scale, clipped to viewport
        nw = min(sw, r.w)
        nh = min(sh, r.h)

        # Center in viewport
        cx = r.x + max(0, (r.w - nw) // 2)
        cy = r.y + max(0, (r.h - nh) // 2)

        # Checkerboard background (viewport size)
        if self._checker_cache is None or self._checker_size != (nw, nh):
            self._checker_size = (nw, nh)
            self._checker_cache = pygame.Surface((nw, nh), pygame.SRCALPHA)
            CHECK_C1 = (45, 45, 50)
            CHECK_C2 = (35, 35, 40)
            for py in range(0, nh, 4):
                for px in range(0, nw, 4):
                    ck = CHECK_C1 if ((px // 4 + py // 4) % 2 == 0) else CHECK_C2
                    self._checker_cache.fill(ck, (px, py, min(4, nw - px), min(4, nh - py)))

        surface.blit(self._checker_cache, (cx, cy))

        # Sprite at actual size (clipped)
        clip_rect = pygame.Rect(0, 0, nw, nh)
        surface.blit(tile_surf, (cx, cy), clip_rect)

        # Border around viewport
        pygame.draw.rect(surface, (100, 110, 120), (r.x - 1, r.y - 1, r.w + 2, r.h + 2), 1)