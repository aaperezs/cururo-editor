import math

import pygame

from engine.configs.constants import ANCHO, ALTO

_real = None
buffer = None
_fill = None
_stretch = False


def get_buffer():
    return buffer


def set_letterbox_fill(surf):
    """Imagen usada como relleno decorativo en las barras de letterbox (None = negro)."""
    global _fill
    _fill = surf


def _tamano_ventana(window_size):
    """Calcula el tamaño de ventana para que SIEMPRE entre en el escritorio.

    window_size explicito se clampa al monitor; si es None se mantiene la
    proporcion logica (ANCHO x ALTO) con escala uniforme que nunca supera
    la resolucion del escritorio actual.
    """
    desktop = pygame.display.get_desktop_sizes()
    if not desktop:
        desk_w, desk_h = window_size or (ANCHO, ALTO)
    else:
        desk_w, desk_h = max(desktop, key=lambda s: s[0] * s[1])
    if window_size:
        ancho = min(window_size[0], desk_w)
        alto = min(window_size[1], desk_h)
        return max(1, ancho), max(1, alto)
    escala = min(desk_w / ANCHO, desk_h / ALTO)
    ancho = max(1, int(ANCHO * escala))
    alto = max(1, int(ALTO * escala))
    return ancho, alto


def setup(window_size=None, fullscreen=False):
    """Crea la ventana y el buffer interno de logica (ANCHO x ALTO).

    - fullscreen=True: pantalla completa (el contenido se estira para llenar).
    - fullscreen=False: ventana; window_size explicito (clamped al escritorio)
      o None -> escala uniforme que entra en el escritorio.
    El contenido se escala al presentar (ver present()).
    """
    global _real, buffer, _stretch
    _stretch = bool(fullscreen)
    if fullscreen:
        _real = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        _real = pygame.display.set_mode(_tamano_ventana(window_size or (ANCHO, ALTO)))
    buffer = pygame.Surface((ANCHO, ALTO))
    return buffer


def set_window_size(size):
    """Recrea la ventana con el nuevo tamaño (clamped al escritorio). No toca el buffer lógico."""
    global _real
    if _real is None or _stretch:
        return  # sin ventana o fullscreen: no-op
    _real = pygame.display.set_mode(_tamano_ventana(size))


def present():
    """Vuelca el buffer a la ventana con letterbox (escala uniforme, contenido centrado).

    Las barras se rellenan con la imagen registrada en set_letterbox_fill()
    (escala cover) o en negro si no hay ninguna.
    """
    if _real is None or buffer is None:
        return
    rw, rh = _real.get_size()

    if _stretch:
        contenido = pygame.transform.smoothscale(buffer, (rw, rh))
        _real.blit(contenido, (0, 0))
        pygame.display.flip()
        return

    escala = min(rw / ANCHO, rh / ALTO)
    cw = max(1, int(ANCHO * escala))
    ch = max(1, int(ALTO * escala))

    if _fill is not None:
        fescala = max(rw / _fill.get_width(), rh / _fill.get_height())
        fw = max(1, int(_fill.get_width() * fescala))
        fh = max(1, int(_fill.get_height() * fescala))
        relleno = pygame.transform.smoothscale(_fill, (fw, fh))
        _real.blit(relleno, ((rw - fw) // 2, (rh - fh) // 2))
    else:
        _real.fill((0, 0, 0))

    contenido = pygame.transform.smoothscale(buffer, (cw, ch))
    _real.blit(contenido, ((rw - cw) // 2, (rh - ch) // 2))
    pygame.display.flip()
