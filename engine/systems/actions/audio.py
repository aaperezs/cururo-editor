"""Acciones de audio (play_bgm, stop_bgm, play_sfx)."""

from engine.systems.action_registry import GameAction, register_action


@register_action("play_bgm")
class PlayBgm(GameAction):
    def execute(self, ctx, params):
        asset_id = params.get("asset_id", "")
        fade_ms = int(params.get("fade_ms", 0))
        if asset_id and hasattr(ctx.state, "audio"):
            ctx.state.audio.play_bgm(asset_id, fade_ms)
        return False


@register_action("stop_bgm")
class StopBgm(GameAction):
    def execute(self, ctx, params):
        fade_ms = int(params.get("fade_ms", 0))
        if hasattr(ctx.state, "audio"):
            ctx.state.audio.stop_bgm(fade_ms)
        return False


@register_action("play_sfx")
class PlaySfx(GameAction):
    def execute(self, ctx, params):
        asset_id = params.get("asset_id", "")
        if asset_id and hasattr(ctx.state, "audio"):
            ctx.state.audio.play_sfx(asset_id)
        return False
