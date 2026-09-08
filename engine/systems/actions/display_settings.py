"""Acciones migradas automaticamente desde stack_manager._ejecutar_accion.

NO EDITAR MANUALMENTE - generado por scripts/migrate_trivial_actions.py
"""

from engine.systems.action_registry import GameAction, register_action
from engine.display import set_window_size
from engine.systems import user_prefs

from engine.configs.constants import TAMANO_CELDA

@register_action("set_resolution")
class SetResolution(GameAction):
    def execute(self, ctx, params):
        ancho = int(params.get("ancho", 0))
        alto = int(params.get("alto", 0))
        if ancho > 0 and alto > 0:
            set_window_size((ancho, alto))
            prefs = user_prefs.load()
            prefs["resolution"] = f"{ancho}x{alto}"
            user_prefs.save(prefs)
        return False

