import pygame
from engine.utils.sprite_manager import obtener as obtener_sprite


class GenericEntity:
    def __init__(self, x, y, properties=None, sprite_id=None):
        self.x = x
        self.y = y
        self.activo = True
        self.visible = True
        self.sprite_id = sprite_id or ""
        self.z = 0
        self.properties = dict(properties or {})
        self._abs_x = 0
        self._abs_y = 0

    def set_abs_pos(self, ax, ay):
        self._abs_x = ax
        self._abs_y = ay

    def colisiona_con(self, cabeza_x, cabeza_y):
        return self.activo and self.x == cabeza_x and self.y == cabeza_y

    def manejar_colision(self, snake, estado=None):
        pass

    def actualizar(self, estado=None):
        self._update_behavior(estado)

    def _update_behavior(self, estado):
        script_func = self.properties.get("on_update", "")
        if script_func and estado:
            import sys as _sys
            for _mn in list(_sys.modules.keys()):
                if _mn.endswith("_game") or _mn == "game" or _mn == "scripts.game":
                    _mod = _sys.modules[_mn]
                    _fn = getattr(_mod, script_func, None)
                    if _fn and callable(_fn):
                        try:
                            _fn(self, estado)
                        except Exception as e:
                            pass
                    break

    def dibujar(self, surface, ox=0, oy=0):
        if not self.activo or not self.visible:
            return
        sx = self.x + ox
        sy = self.y + oy
        sprite = obtener_sprite(self.sprite_id)
        if sprite:
            surface.blit(sprite, (sx, sy))
        else:
            pygame.draw.rect(surface, (100, 100, 120), (sx, sy, 20, 20))
