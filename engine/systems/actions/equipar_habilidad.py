"""Acción equipar_habilidad: equipa una habilidad."""

from engine.systems.action_registry import GameAction, register_action


@register_action("equipar_habilidad")
class EquiparHabilidad(GameAction):
    def execute(self, ctx, params):
        habilidad = params.get("habilidad", "")
        if habilidad and hasattr(ctx.state, "habilidades"):
            from engine.configs.habilidades import HabilidadID
            hid = getattr(HabilidadID, habilidad.upper(), habilidad)
            ctx.state.habilidades.equipar_habilidad(hid)
            print(f"[EVENTO] habilidad '{habilidad}' equipada")
        return False
