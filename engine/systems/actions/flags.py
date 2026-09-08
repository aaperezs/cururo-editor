"""Acciones de flags (set_flag, add_flag)."""

from engine.systems.action_registry import GameAction, register_action


@register_action("set_flag")
class SetFlag(GameAction):
    def execute(self, ctx, params):
        flag = params.get("flag", "")
        valor = params.get("valor", True)
        if flag and hasattr(ctx.state, "flags"):
            ctx.state.flags.set(flag, valor)
        return False


@register_action("add_flag")
class AddFlag(GameAction):
    def execute(self, ctx, params):
        flag = params.get("flag", "")
        cantidad = int(params.get("cantidad", 1))
        if flag and hasattr(ctx.state, "flags"):
            ctx.state.flags.add(flag, cantidad)
        return False
