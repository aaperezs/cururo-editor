"""Acción run_script: ejecuta una función de script."""

import sys

from engine.systems.action_registry import GameAction, register_action


@register_action("run_script")
class RunScript(GameAction):
    def execute(self, ctx, params):
        func_name = params.get("function_name", "")
        args_str = params.get("args", "")
        if func_name:
            args_list = [a.strip() for a in args_str.split(",") if a.strip()] if args_str else []
            for mod_name in list(sys.modules.keys()):
                if mod_name.endswith("_game") or mod_name == "game" or mod_name == "scripts.game":
                    module = sys.modules[mod_name]
                    func = getattr(module, func_name, None)
                    if func and callable(func):
                        try:
                            func(*args_list)
                        except Exception as e:
                            print(f"[EVENTO] run_script error: {e}")
                        break
        return False
