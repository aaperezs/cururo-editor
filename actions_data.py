# Registro de acciones conocidas para items de menú (data/menus.json).
#
# Fuente única de verdad: orm/systems/stack_manager.py (_ejecutar_accion) y
# orm/handlers/input_manager.py (_ejecutar_accion_menu). Si una acción cambia
# de params en el runtime, hay que actualizarla acá.
#
# Formato: tipo -> (label, [(param, label_param, tipo_dato, default), ...])
#   tipo_dato: "text" | "int" | "float" | "bool"

NONE_ACTION = "Ninguna"

ACCIONES = {
    "usar_item": ("Usar item", []),
    "equipar_habilidad": ("Equipar habilidad", [("habilidad", "Habilidad", "text", "")]),
    "show_message": ("Mostrar mensaje", [("mensaje", "Mensaje", "text", "")]),
    "give_item": ("Dar item", [("item", "Item", "text", ""), ("cantidad", "Cantidad", "int", 1)]),
    "remove_item": ("Quitar item", [("item", "Item", "text", ""), ("cantidad", "Cantidad", "int", 1)]),
    "set_flag": ("Poner flag", [("flag", "Flag", "text", ""), ("valor", "Valor", "bool", True)]),
    "add_flag": ("Sumar flag", [("flag", "Flag", "text", ""), ("cantidad", "Cantidad", "int", 1)]),
    "clear_flag": ("Limpiar flag", [("flag", "Flag", "text", "")]),
    "change_map": ("Cambiar mapa", [("nivel", "Nivel", "text", ""), ("exit_id", "Exit ID", "text", "")]),
    "iniciar_dialogo": ("Iniciar diálogo", [("dialogo_id", "ID diálogo", "text", "")]),
    "dialogo_tree": ("Árbol de diálogo", [("dialogo_id", "ID diálogo", "text", "")]),
    "start_dialogue": ("Iniciar diálogo (eng)", [("dialogo_id", "ID diálogo", "text", "")]),
    "dialogo_inline": ("Diálogo inline", [("lineas", "Líneas (json)", "text", ""), ("quien", "Quién", "text", "")]),
    "spawn_entity": ("Spawn entidad", [("sprite_id", "Sprite", "text", ""), ("offset_x", "Offset X", "int", 0), ("offset_y", "Offset Y", "int", 0), ("z", "Z", "int", 0)]),
    "consume_pp": ("Consumir PP", [("cantidad", "Cantidad", "int", 1)]),
    "play_bgm": ("Reproducir BGM", [("asset_id", "Asset", "text", ""), ("fade_ms", "Fade (ms)", "int", 0)]),
    "stop_bgm": ("Detener BGM", [("fade_ms", "Fade (ms)", "int", 0)]),
    "play_sfx": ("Reproducir SFX", [("asset_id", "Asset", "text", "")]),
    "set_bgm_volume": ("Volumen BGM", [("volumen", "Volumen", "float", 1.0)]),
    "set_sfx_volume": ("Volumen SFX", [("volumen", "Volumen", "float", 1.0)]),
    "iniciar_minijuego": ("Iniciar minijuego", [("minijuego_id", "Minijuego", "text", "")]),
    "ir_a_escena": ("Ir a escena", [("capitulo", "Capítulo", "int", 0), ("escena", "Escena", "int", 0)]),
    "cambiar_fondo": ("Cambiar fondo", [("sprite_id", "Sprite", "text", ""), ("modo", "Modo", "text", "fill")]),
    "mostrar_personaje": ("Mostrar personaje", [("personaje_id", "Personaje", "text", ""), ("posicion", "Posición", "text", "centro"), ("expresion", "Expresión", "text", "normal")]),
    "ocultar_personaje": ("Ocultar personaje", [("personaje_id", "Personaje", "text", "")]),
    "mostrar_opciones": ("Mostrar opciones", [("opciones", "Opciones (json)", "text", "")]),
    "desbloquear_habilidad": ("Desbloquear habilidad", [("habilidad", "Habilidad", "text", "")]),
    "cambiar_skin": ("Cambiar skin", [("sprite_id", "Sprite", "text", "")]),
    "fin_demo": ("Fin demo", []),
}


def acciones_disponibles():
    """Lista (tipo, label) de acciones seleccionables en items de menú."""
    return [(t, lbl) for t, (lbl, _) in ACCIONES.items()]


def label_accion(tipo):
    entry = ACCIONES.get(tipo)
    return entry[0] if entry else tipo


def schema(tipo):
    """Esquema de params para una acción: [(param, label, tipo_dato, default)]."""
    entry = ACCIONES.get(tipo)
    return entry[1] if entry else []