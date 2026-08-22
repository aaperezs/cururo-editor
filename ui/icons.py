"""Procedural icon factory for the editor UI."""

import os
import pygame

from editor.ui.theme import Theme


class IconFactory:
    """Generates icons as procedural sprites (2x render + smoothscale down).
    
    Icons are white silhouettes tinted via BLEND_RGB_MULT for any color.
    Supports PNG override from assets/ico/.
    """
    
    def __init__(self):
        self._cache = {}  # (name, size, color) -> Surface
        self._base_cache = {}  # (name, size) -> base white surface
        self._ico_dir = self._find_ico_dir()
    
    def _find_ico_dir(self) -> str:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ico_dir = os.path.join(base, "assets", "ico")
        if os.path.exists(ico_dir):
            return ico_dir
        return os.path.join(os.getcwd(), "assets", "ico")
    
    def get(self, name: str, size: int = 16, color=None) -> pygame.Surface:
        """Get icon surface (cached)."""
        if color is None:
            color = Theme.get().text
        key = (name, size, color)
        if key in self._cache:
            return self._cache[key]
        
        # Try PNG override first
        png_path = os.path.join(self._ico_dir, f"ico_{name}.png")
        if os.path.exists(png_path):
            try:
                surf = pygame.image.load(png_path).convert_alpha()
                if surf.get_size() != (size, size):
                    surf = pygame.transform.smoothscale(surf, (size, size))
                if color != (255, 255, 255, 255):
                    surf = self._tint(surf, color)
                self._cache[key] = surf
                return surf
            except pygame.error:
                pass
        
        # Generate procedural
        base = self._get_base(name, size)
        if color != (255, 255, 255, 255):
            surf = self._tint(base, color)
        else:
            surf = base
        self._cache[key] = surf
        return surf
    
    def _get_base(self, name: str, size: int) -> pygame.Surface:
        """Get or create base white silhouette at 2x then downscale."""
        base_key = (name, size)
        if base_key in self._base_cache:
            return self._base_cache[base_key]
        
        # Render at 2x for better quality
        render_size = size * 2
        surf = pygame.Surface((render_size, render_size), pygame.SRCALPHA)
        self._draw_icon(surf, name, render_size)
        
        # Downscale
        if render_size != size:
            surf = pygame.transform.smoothscale(surf, (size, size))
        
        self._base_cache[base_key] = surf
        return surf
    
    def _tint(self, surface: pygame.Surface, color) -> pygame.Surface:
        """Tint a white silhouette with color using BLEND_RGB_MULT."""
        if isinstance(color, (tuple, list)):
            color = pygame.Color(*color[:3], color[3] if len(color) > 3 else 255)
        elif isinstance(color, pygame.Color):
            pass
        else:
            color = pygame.Color(255, 255, 255, 255)
        tinted = surface.copy()
        tinted.fill((color.r, color.g, color.b, 0), special_flags=pygame.BLEND_RGB_MULT)
        return tinted
    
    def _draw_icon(self, surface: pygame.Surface, name: str, size: int):
        """Draw icon at given size (white silhouette)."""
        c = size // 2
        s = size * 0.45  # icon scale factor
        h = s / 2
        color = (255, 255, 255, 255)
        
        if name == "chevron_down":
            pygame.draw.polygon(surface, color, [
                (c - h, c - h * 0.5), (c + h, c - h * 0.5), (c, c + h)
            ])
        elif name == "chevron_right":
            pygame.draw.polygon(surface, color, [
                (c - h * 0.5, c - h), (c + h * 0.5, c), (c - h * 0.5, c + h)
            ])
        elif name == "chevron_up":
            pygame.draw.polygon(surface, color, [
                (c - h, c + h * 0.5), (c + h, c + h * 0.5), (c, c - h)
            ])
        elif name == "chevron_left":
            pygame.draw.polygon(surface, color, [
                (c + h * 0.5, c - h), (c - h * 0.5, c), (c + h * 0.5, c + h)
            ])
        elif name == "pencil":
            pygame.draw.polygon(surface, color, [
                (c - s * 0.4, c + s * 0.4), (c - s * 0.1, c + s * 0.1),
                (c + s * 0.4, c - s * 0.4), (c + s * 0.7, c - s * 0.7)
            ])
            pygame.draw.line(surface, color, (c - s * 0.4, c + s * 0.4), (c - s * 0.7, c + s * 0.7), max(1, size // 16))
        elif name == "eraser":
            pygame.draw.rect(surface, color, (c - s * 0.5, c - s * 0.3, s, s * 0.6), max(1, size // 16))
            pygame.draw.polygon(surface, color, [
                (c - s * 0.5, c - s * 0.3), (c - s * 0.8, c - s * 0.6), (c - s * 0.8, c + s * 0.6)
            ])
        elif name == "bucket":
            pygame.draw.polygon(surface, color, [
                (c - s * 0.4, c - s * 0.5), (c + s * 0.4, c - s * 0.5),
                (c + s * 0.5, c + s * 0.5), (c - s * 0.5, c + s * 0.5)
            ])
            pygame.draw.line(surface, color, (c - s * 0.2, c - s * 0.5), (c - s * 0.2, c - s * 0.8), max(1, size // 16))
            pygame.draw.line(surface, color, (c + s * 0.2, c - s * 0.5), (c + s * 0.2, c - s * 0.8), max(1, size // 16))
        elif name in ("eyedropper", "gotero"):
            pygame.draw.polygon(surface, color, [
                (c - s * 0.3, c + s * 0.4), (c + s * 0.3, c - s * 0.4), (c + s * 0.5, c - s * 0.2)
            ])
            pygame.draw.circle(surface, color, (int(c - s * 0.3), int(c + s * 0.4)), max(1, size // 16))
        elif name == "select":
            pygame.draw.rect(surface, color, (c - s * 0.5, c - s * 0.5, s, s), max(1, size // 16))
        elif name == "shapes_rect":
            pygame.draw.rect(surface, color, (c - s * 0.5, c - s * 0.5, s, s), max(1, size // 16))
        elif name == "shapes_ellipse":
            pygame.draw.ellipse(surface, color, (c - s * 0.5, c - s * 0.5, s, s), max(1, size // 16))
        elif name == "shapes_line":
            pygame.draw.line(surface, color, (c - s * 0.5, c + s * 0.5), (c + s * 0.5, c - s * 0.5), max(1, size // 16))
        elif name == "new":
            pygame.draw.line(surface, color, (c, c - s * 0.5), (c, c + s * 0.5), max(2, size // 8))
            pygame.draw.line(surface, color, (c - s * 0.5, c), (c + s * 0.5, c), max(2, size // 8))
        elif name == "open":
            pygame.draw.polygon(surface, color, [
                (c - s * 0.5, c + s * 0.2), (c - s * 0.5, c - s * 0.5),
                (c + s * 0.5, c - s * 0.5), (c + s * 0.5, c + s * 0.2)
            ])
            pygame.draw.line(surface, color, (c - s * 0.3, c + s * 0.2), (c, c - s * 0.1), max(1, size // 16))
            pygame.draw.line(surface, color, (c, c - s * 0.1), (c + s * 0.3, c + s * 0.2), max(1, size // 16))
        elif name == "save":
            pygame.draw.rect(surface, color, (c - s * 0.4, c - s * 0.5, s * 0.8, s), max(1, size // 16))
            pygame.draw.rect(surface, color, (c - s * 0.4, c - s * 0.5, s * 0.8, s * 0.3), max(1, size // 16))
        elif name == "save_as":
            pygame.draw.rect(surface, color, (c - s * 0.4, c - s * 0.5, s * 0.8, s), max(1, size // 16))
            pygame.draw.rect(surface, color, (c - s * 0.4, c - s * 0.5, s * 0.8, s * 0.3), max(1, size // 16))
            pygame.draw.line(surface, color, (c - s * 0.2, c + s * 0.1), (c + s * 0.2, c + s * 0.1), max(1, size // 16))
            pygame.draw.line(surface, color, (c, c - s * 0.1), (c, c + s * 0.3), max(1, size // 16))
        elif name == "grid":
            step = max(1, size // 8)
            for x in range(0, size, step * 2):
                for y in range(0, size, step * 2):
                    pygame.draw.rect(surface, color, (x, y, step, step))
        elif name == "tileset":
            step = max(1, size // 6)
            for i in range(3):
                for j in range(3):
                    if (i + j) % 2 == 0:
                        pygame.draw.rect(surface, color, (c - s * 0.5 + i * step, c - s * 0.5 + j * step, step, step))
        elif name == "symmetry_h":
            pygame.draw.line(surface, color, (c - s * 0.5, c), (c + s * 0.5, c), max(2, size // 8))
            pygame.draw.line(surface, color, (c - s * 0.5, c - s * 0.3), (c - s * 0.5, c + s * 0.3), max(1, size // 16))
            pygame.draw.line(surface, color, (c + s * 0.5, c - s * 0.3), (c + s * 0.5, c + s * 0.3), max(1, size // 16))
        elif name == "symmetry_v":
            pygame.draw.line(surface, color, (c, c - s * 0.5), (c, c + s * 0.5), max(2, size // 8))
            pygame.draw.line(surface, color, (c - s * 0.3, c - s * 0.5), (c + s * 0.3, c - s * 0.5), max(1, size // 16))
            pygame.draw.line(surface, color, (c - s * 0.3, c + s * 0.5), (c + s * 0.3, c + s * 0.5), max(1, size // 16))
        elif name == "symmetry_both":
            # Cross shape for both horizontal and vertical symmetry
            pygame.draw.line(surface, color, (c - s * 0.5, c), (c + s * 0.5, c), max(2, size // 8))
            pygame.draw.line(surface, color, (c, c - s * 0.5), (c, c + s * 0.5), max(2, size // 8))
            pygame.draw.line(surface, color, (c - s * 0.5, c - s * 0.3), (c - s * 0.5, c + s * 0.3), max(1, size // 16))
            pygame.draw.line(surface, color, (c + s * 0.5, c - s * 0.3), (c + s * 0.5, c + s * 0.3), max(1, size // 16))
            pygame.draw.line(surface, color, (c - s * 0.3, c - s * 0.5), (c + s * 0.3, c - s * 0.5), max(1, size // 16))
            pygame.draw.line(surface, color, (c - s * 0.3, c + s * 0.5), (c + s * 0.3, c + s * 0.5), max(1, size // 16))
        elif name == "drag":
            # Four-way arrow for drag/move
            pygame.draw.polygon(surface, color, [
                (c, c - s * 0.5), (c - s * 0.2, c - s * 0.2), (c + s * 0.2, c - s * 0.2)
            ])
            pygame.draw.polygon(surface, color, [
                (c, c + s * 0.5), (c - s * 0.2, c + s * 0.2), (c + s * 0.2, c + s * 0.2)
            ])
            pygame.draw.polygon(surface, color, [
                (c - s * 0.5, c), (c - s * 0.2, c - s * 0.2), (c - s * 0.2, c + s * 0.2)
            ])
            pygame.draw.polygon(surface, color, [
                (c + s * 0.5, c), (c + s * 0.2, c - s * 0.2), (c + s * 0.2, c + s * 0.2)
            ])
        elif name == "play":
            # Play triangle
            pygame.draw.polygon(surface, color, [
                (c - s * 0.4, c - s * 0.4), (c - s * 0.4, c + s * 0.4), (c + s * 0.3, c)
            ])
        elif name == "zoom_in":
            pygame.draw.circle(surface, color, (c, c), int(s * 0.6), max(2, size // 8))
            pygame.draw.line(surface, color, (c, c), (c, c - s * 0.6), max(2, size // 8))
            pygame.draw.line(surface, color, (c - s * 0.2, c - s * 0.2), (c + s * 0.2, c + s * 0.2), max(2, size // 8))
        elif name == "zoom_out":
            pygame.draw.circle(surface, color, (c, c), int(s * 0.6), max(2, size // 8))
            pygame.draw.line(surface, color, (c - s * 0.6, c), (c + s * 0.6, c), max(2, size // 8))
        elif name == "fit":
            pygame.draw.rect(surface, color, (c - s * 0.5, c - s * 0.5, s, s), max(2, size // 8))
            pygame.draw.line(surface, color, (c - s * 0.5, c), (c + s * 0.5, c), max(1, size // 16))
            pygame.draw.line(surface, color, (c, c - s * 0.5), (c, c + s * 0.5), max(1, size // 16))
        elif name == "undo":
            pygame.draw.arc(surface, color, (c - s * 0.5, c - s * 0.5, s, s), 0.5, 5.5, max(2, size // 8))
            pygame.draw.polygon(surface, color, [
                (c + s * 0.5, c), (c + s * 0.2, c - s * 0.2), (c + s * 0.2, c + s * 0.2)
            ])
        elif name == "redo":
            pygame.draw.arc(surface, color, (c - s * 0.5, c - s * 0.5, s, s), 3.5, 8.5, max(2, size // 8))
            pygame.draw.polygon(surface, color, [
                (c - s * 0.5, c), (c - s * 0.2, c - s * 0.2), (c - s * 0.2, c + s * 0.2)
            ])
        else:
            # Fallback: question mark
            pygame.draw.circle(surface, color, (c, c), int(s * 0.6), max(1, size // 16))
        
        self._base_cache[(name, size)] = surface


# Global instance
_icon_factory = None

def get_icon_factory() -> IconFactory:
    global _icon_factory
    if _icon_factory is None:
        _icon_factory = IconFactory()
    return _icon_factory