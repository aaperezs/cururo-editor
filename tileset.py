"""Tileset management for the editor.

Loads a PNG tileset, slices it into tiles based on tile_size,
and provides cached access to individual tile surfaces.
"""

import os

import pygame


_cache = {}


class Tileset:
    """Manages a tileset image divided into uniform tiles."""

    def __init__(self, tileset_path: str, tile_size: int):
        """Load and slice the tileset.

        Args:
            tileset_path: Path to the PNG tileset file.
            tile_size: Size of each tile in pixels (width == height).
        """
        self.tileset_path = os.path.abspath(tileset_path)
        self.tile_size = max(1, int(tile_size))
        self._tiles = []
        self._cols = 0
        self._rows = 0
        self._load_tileset()

    def _load_tileset(self):
        """Load the tileset image and slice into tiles."""
        cache_key = (self.tileset_path, self.tile_size)
        if cache_key in _cache:
            cached = _cache[cache_key]
            self._tiles = cached["tiles"]
            self._cols = cached["cols"]
            self._rows = cached["rows"]
            return

        if not os.path.exists(self.tileset_path):
            self._tiles = []
            self._cols = 0
            self._rows = 0
            _cache[cache_key] = {"tiles": [], "cols": 0, "rows": 0}
            return

        try:
            sheet = pygame.image.load(self.tileset_path).convert_alpha()
        except pygame.error as e:
            print(f"[Tileset] Error loading {self.tileset_path}: {e}")
            self._tiles = []
            self._cols = 0
            self._rows = 0
            _cache[cache_key] = {"tiles": [], "cols": 0, "rows": 0}
            return

        w, h = sheet.get_size()
        self._cols = w // self.tile_size
        self._rows = h // self.tile_size

        if self._cols == 0 or self._rows == 0:
            print(f"[Tileset] Image {w}x{h} too small for tile_size {self.tile_size}")
            self._tiles = []
            self._cols = 0
            self._rows = 0
            _cache[cache_key] = {"tiles": [], "cols": 0, "rows": 0}
            return

        self._tiles = []
        for r in range(self._rows):
            for c in range(self._cols):
                rect = pygame.Rect(c * self.tile_size, r * self.tile_size,
                                   self.tile_size, self.tile_size)
                tile = sheet.subsurface(rect).copy()
                self._tiles.append(tile)

        _cache[cache_key] = {
            "tiles": self._tiles,
            "cols": self._cols,
            "rows": self._rows,
        }

    def get_tile(self, index: int) -> pygame.Surface | None:
        """Return tile surface by index (0-based, row-major order).

        Args:
            index: Tile index.

        Returns:
            pygame.Surface for the tile, or None if index out of range.
        """
        if 0 <= index < len(self._tiles):
            return self._tiles[index]
        return None

    def get_tile_rect(self, index: int) -> pygame.Rect | None:
        """Return source rect in the tileset for the given tile index.

        Args:
            index: Tile index.

        Returns:
            pygame.Rect in tileset coordinates, or None if index out of range.
        """
        if not (0 <= index < len(self._tiles)):
            return None
        c = index % self._cols
        r = index // self._cols
        return pygame.Rect(c * self.tile_size, r * self.tile_size,
                           self.tile_size, self.tile_size)

    @property
    def tile_count(self) -> int:
        """Total number of tiles in the tileset."""
        return len(self._tiles)

    @property
    def cols(self) -> int:
        """Number of tile columns."""
        return self._cols

    @property
    def rows(self) -> int:
        """Number of tile rows."""
        return self._rows

    def draw_tile(self, surface: pygame.Surface, index: int, x: int, y: int) -> bool:
        """Draw a tile onto a surface at the given position.

        Args:
            surface: Target surface to draw on.
            index: Tile index.
            x: X position in pixels.
            y: Y position in pixels.

        Returns:
            True if tile was drawn, False if index invalid.
        """
        tile = self.get_tile(index)
        if tile is None:
            return False
        surface.blit(tile, (x, y))
        return True

    @staticmethod
    def load_from_project(project) -> "Tileset | None":
        """Create a Tileset from a Project instance.

        Args:
            project: Project object with `tileset` path and `tile_size` property.

        Returns:
            Tileset instance, or None if no tileset configured or load failed.
        """
        tileset_rel = getattr(project, "tileset", None)
        if not tileset_rel:
            return None
        tile_size = getattr(project, "tile_size", 20)
        tileset_path = os.path.join(project.root, tileset_rel)
        if not os.path.exists(tileset_path):
            return None
        return Tileset(tileset_path, tile_size)


def clear_cache():
    """Clear the global tileset cache."""
    _cache.clear()