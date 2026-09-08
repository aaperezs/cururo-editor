import importlib.util
import sys
import os


def load_script(project_root, script_name="game"):
    script_path = os.path.join(project_root, "scripts", f"{script_name}.py")
    if not os.path.exists(script_path):
        return None

    spec = importlib.util.spec_from_file_location(script_name, script_path)
    if spec is None:
        return None

    module = importlib.util.module_from_spec(spec)
    sys.modules[script_name] = module
    spec.loader.exec_module(module)
    return module
