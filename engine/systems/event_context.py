"""EventContext: contexto tipado que fluye por condiciones y acciones.

Elimina el acceso directo a `self.estado` dentro de StackManager y
permite reutilizar condiciones/acciones fuera del manager (testeo,
otras escenas, eventos globales).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EventContext:
    """Estado compartido durante la evaluación de un evento.

    Campos:
        source:  entidad que origina el evento (snake, enemigo, objeto...).
        target:  entidad sobre la que actúa (opcional).
        position: (gx, gy, z) celda donde ocurrió el evento.
        state:   GameState global (inventario, flags, habilidades, monedas...).
        custom:  datos extra arbitrarios (damage, attack_type, etc.).
        manager: StackManager actual (para acciones que necesitan estado interno).
        dialog_service:  DialogoSystem (para acciones de diálogo).
        shop_service:    ShopSystem (para acciones de tienda).
        battle_service:  arena_boss / boss (para acciones de combate).
    """

    source: Any = None
    target: Any = None
    position: tuple[int, int, int] = (0, 0, 0)
    state: Any = None
    custom: dict[str, Any] = field(default_factory=dict)
    manager: Any = None
    dialog_service: Any = None
    shop_service: Any = None
    battle_service: Any = None

    # ── Acceso directo a sub-estados (duck-typing) ─────────

    @property
    def snake(self):
        state = self.state
        return getattr(state, "snake", None)

    @property
    def inventario(self):
        return getattr(self.state, "inventario", None)

    @property
    def flags(self):
        return getattr(self.state, "flags", None)

    @property
    def habilidades(self):
        return getattr(self.state, "habilidades", None)

    @property
    def monedas(self):
        return getattr(self.state, "monedas", None)

    def get(self, key, default=None):
        """Lee una variable de estado (flags) o del custom context."""
        if key in self.custom:
            return self.custom[key]
        if self.flags is not None:
            return self.flags.get(key, default)
        return default
