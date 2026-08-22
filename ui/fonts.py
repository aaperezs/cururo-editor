"""Font management for the editor UI."""

import os
import pygame

from editor.ui.theme import Theme


class FontManager:
    """Loads and caches TTF fonts from assets/fonts/."""
    
    def __init__(self):
        self._cache = {}
        self._font_dir = self._find_font_dir()
        self._regular_path = os.path.join(self._font_dir, "DejaVuSans.ttf")
        self._bold_path = os.path.join(self._font_dir, "DejaVuSans-Bold.ttf")
    
    def _find_font_dir(self) -> str:
        """Find the assets/fonts directory."""
        # Try relative to this file
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        font_dir = os.path.join(base, "assets", "fonts")
        if os.path.exists(font_dir):
            return font_dir
        # Fallback: project root
        return os.path.join(os.getcwd(), "assets", "fonts")
    
    def get(self, size: int, bold: bool = False) -> pygame.font.Font:
        """Get a font by size and weight (cached)."""
        key = (size, bold)
        if key in self._cache:
            return self._cache[key]
        
        path = self._bold_path if bold else self._regular_path
        try:
            font = pygame.font.Font(path, size)
        except (pygame.error, FileNotFoundError):
            # Fallback to system font
            font = pygame.font.SysFont("DejaVu Sans", size, bold=bold)
        
        self._cache[key] = font
        return font
    
    def get_regular(self, size: int) -> pygame.font.Font:
        return self.get(size, bold=False)
    
    def get_bold(self, size: int) -> pygame.font.Font:
        return self.get(size, bold=True)


# Global instance
_font_manager = None

def get_font_manager() -> FontManager:
    global _font_manager
    if _font_manager is None:
        _font_manager = FontManager()
    return _font_manager