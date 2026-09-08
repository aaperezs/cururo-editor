"""Carga de hojas de sprites para bosses (filas = fases, columnas = frames).

Convención de grilla:
- Filas = fases (fila 0 = fase 1; fila N-1 = fase N).
- Columnas = frames del bucle de animación de esa fase.
- Orden de frames fila-mayor: `frames[r*cols + c]`.

Sin archivo o grilla inválida -> None (el llamante usa su fallback procedural).
"""

import os

import pygame

from engine.project_paths import assets_dir

_cache = {}


def cargar_hoja(nombre, rows, cols, fw, fh):
    """Carga assets/<nombre>.png y recorta la grilla rowsxcols de celdas fwxfh.

    Devuelve una lista de `rows*cols` Surface (orden fila-mayor) o None si el
    archivo no existe, la grilla no cabe en la imagen o algo falla.
    """
    rows = max(1, int(rows or 1))
    cols = max(1, int(cols or 1))
    fw = max(1, int(fw or 1))
    fh = max(1, int(fh or 1))
    key = (nombre, rows, cols, fw, fh)
    if key in _cache:
        return _cache[key]

    ruta = assets_dir(nombre + ".png")
    if not os.path.exists(ruta):
        _cache[key] = None
        return None

    try:
        hoja = pygame.image.load(ruta).convert_alpha()
    except pygame.error as e:
        print(f"[SPRITE_SHEET] Error cargando {ruta}: {e}")
        _cache[key] = None
        return None

    w, h = hoja.get_size()
    if fw * cols > w or fh * rows > h:
        print(f"[SPRITE_SHEET] Grilla {rows}x{cols} x {fw}x{fh} no entra en "
              f"{w}x{h} ({nombre}.png)")
        _cache[key] = None
        return None

    frames = []
    for r in range(rows):
        for c in range(cols):
            frame = hoja.subsurface((c * fw, r * fh, fw, fh)).copy()
            frames.append(frame)
    _cache[key] = frames
    return frames

