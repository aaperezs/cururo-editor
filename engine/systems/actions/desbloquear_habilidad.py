"""Acción desbloquear_habilidad: desbloquea una habilidad."""

from engine.systems.action_registry import GameAction, register_action


@register_action("desbloquear_habilidad")
class DesbloquearHabilidad(GameAction):
    def execute(self, ctx, params):
        habilidad = params.get("habilidad", "")
        if habilidad and hasattr(ctx.state, "habilidades"):
            from engine.configs.habilidades import HabilidadID
            hid = getattr(HabilidadID, habilidad.upper(), habilidad)
            if not ctx.state.habilidades.tiene_habilidad(hid):
                ctx.state.habilidades.desbloquear_habilidad(hid)
            print(f"[EVENTO] habilidad '{habilidad}' desbloqueada")
        return False
