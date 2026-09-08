"""ActionRegistry: registro de acciones de eventos (patrón híbrido).

Flujo en StackManager._ejecutar_accion:
  1. Busca la acción en el registro (registry first).
  2. Si existe, ejecuta GameAction.execute(ctx, params).
  3. Si NO existe (o lanza excepción), cae al `elif` legacy como fallback.

Así se migran acciones de a una sin perder compatibilidad con las 85
ramas del dispatcher original.
"""

from __future__ import annotations

from typing import Callable, Optional

from engine.systems.event_context import EventContext

_REGISTRY: dict[str, type["GameAction"]] = {}


def register_action(action_id: str):
    """Decorador que registra una acción en el registry."""
    def decorator(cls):
        cls.action_id = action_id
        _REGISTRY[action_id] = cls
        return cls
    return decorator


def get_action(action_id: str) -> Optional[type["GameAction"]]:
    """Devuelve la clase de acción registrada o None."""
    return _REGISTRY.get(action_id)


def registered_ids() -> list[str]:
    return sorted(_REGISTRY.keys())


class GameAction:
    """Clase base. Cada acción implementa execute(ctx, params).

    Devuelve True si la acción bloquea la cola (como el dispatcher legacy).
    """

    action_id: str = ""

    def execute(self, ctx: EventContext, params: dict) -> bool:
        raise NotImplementedError
