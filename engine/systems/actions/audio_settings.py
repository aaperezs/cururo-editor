"""Acciones migradas automaticamente desde stack_manager._ejecutar_accion.

NO EDITAR MANUALMENTE - generado por scripts/migrate_trivial_actions.py
"""

from engine.systems.action_registry import GameAction, register_action
from engine.systems import user_prefs

from engine.configs.constants import TAMANO_CELDA

@register_action("set_bgm_volume")
class SetBgmVolume(GameAction):
    def execute(self, ctx, params):
        vol = float(params.get("volumen", 1.0))
        if hasattr(ctx.state, "audio"):
            ctx.state.audio.set_bgm_volume(vol)
        return False


@register_action("set_sfx_volume")
class SetSfxVolume(GameAction):
    def execute(self, ctx, params):
        vol = float(params.get("volumen", 1.0))
        if hasattr(ctx.state, "audio"):
            ctx.state.audio.set_sfx_volume(vol)
        return False


@register_action("set_volume")
class SetVolume(GameAction):
    def execute(self, ctx, params):
        vol = float(params.get("volumen", 1.0))
        if hasattr(ctx.state, "audio"):
            ctx.state.audio.set_bgm_volume(vol)
            ctx.state.audio.set_sfx_volume(vol)
            prefs = user_prefs.load()
            prefs["bgm_volume"] = vol
            prefs["sfx_volume"] = vol
            user_prefs.save(prefs)
        return False
