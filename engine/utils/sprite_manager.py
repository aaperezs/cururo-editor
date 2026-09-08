import os

import pygame


def _assets_dir():
    try:
        from editor.project import get_current_project
        p = get_current_project()
        if p is not None:
            return os.path.join(p.root, "assets")
    except Exception:
        pass
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")


_cache = {}

def obtener(nombre):
    """Carga un sprite PNG desde assets/ con caché.

    Busca assets/<nombre>.png, lo carga con convert_alpha() y lo almacena
    en _cache para evitar recargar archivos repetidamente. Si el archivo
    no existe o falla la carga, retorna None (el llamante debe tener un
    fallback de dibujo con primitivas Pygame).
    """
    if nombre in _cache:
        return _cache[nombre]
    ruta = os.path.join(_assets_dir(), nombre + ".png")
    if os.path.exists(ruta):
        try:
            img = pygame.image.load(ruta).convert_alpha()
            _cache[nombre] = img
            return img
        except pygame.error:
            pass
    _cache[nombre] = None
    return None
