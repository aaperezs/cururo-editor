import os


def _project_root():
    """Obtiene la raíz del proyecto activo."""
    try:
        from editor.project import get_current_project
        p = get_current_project()
        if p is not None:
            return p.root
    except Exception:
        pass
    return None


def runtime_root():
    """Raíz del proyecto actual; si no hay proyecto, la raíz del motor.

    Cuando el motor está en editor/engine/, devuelve el project root del editor.
    Cuando el motor está en project/engine/ (standalone), devuelve project/.
    """
    root = _project_root()
    if root:
        return root
    # El motor vive en engine/; la data está un nivel arriba
    engine_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(engine_dir)


def data_dir(*parts):
    return os.path.join(runtime_root(), "data", *parts)


def assets_dir(*parts):
    return os.path.join(runtime_root(), "assets", *parts)


def levels_dir(*parts):
    return os.path.join(runtime_root(), "levels", *parts)
