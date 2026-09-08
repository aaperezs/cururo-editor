"""Acción ir_a_escena: navega a una escena del juego."""

from engine.systems.action_registry import GameAction, register_action


@register_action("ir_a_escena")
class IrAEscena(GameAction):
    def execute(self, ctx, params):
        capitulo_idx = int(params.get("capitulo", 0))
        escena_idx = int(params.get("escena", 0))
        if hasattr(ctx.state, "_scene_navegacion"):
            ctx.state._scene_navegacion = (capitulo_idx, escena_idx)
        ctx.state.cambiando_nivel = True
        if hasattr(ctx.state, "audio") and ctx.state.audio.get_current_bgm():
            ctx.state.audio.stop_bgm(500)
        return False
