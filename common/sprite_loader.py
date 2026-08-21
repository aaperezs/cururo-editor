"""Carga de sprites PNG desde assets/ del proyecto (caché en memoria).

Reemplaza orm/utils/sprite_manager.py para eliminar la dependencia
del editor con el runtime ORM. Misma API: obtener(nombre) -> Surface|None.
"""

import os
import pygame

_cache = {}


def _assets_dir():
    try:
        from editor.project import get_current_project
        p = get_current_project()
        if p is not None:
            return os.path.join(p.root, "assets")
    except Exception:
        pass
    return None


def obtener(nombre):
    """Carga un sprite PNG desde assets/ con caché.

    Busca assets/<nombre>.png, lo carga con convert_alpha() y lo almacena
    en _cache para evitar recargar archivos repetidamente. Si el archivo
    no existe o falla la carga, retorna None.
    """
    if nombre in _cache:
        return _cache[nombre]
    assets = _assets_dir()
    if assets is None:
        _cache[nombre] = None
        return None
    ruta = os.path.join(assets, nombre + ".png")
    if os.path.exists(ruta):
        try:
            img = pygame.image.load(ruta).convert_alpha()
            _cache[nombre] = img
            return img
        except pygame.error:
            pass
    _cache[nombre] = None
    return None
