from editor.sprite_registry import get_sprite_registry, CHAR_TO_SPRITE, SPRITE_TO_CHAR


SPRITE_FILE_MAP = {
    "enemigo_v": "enemigo_melee",
    "enemigo_h": "enemigo_melee",
    "enemigo_c": "enemigo_melee",
    "enemy_shooter_h": "enemigo_shooter",
    "enemy_shooter_v": "enemigo_shooter",
    "enemigo": "enemigo_melee",
    "boss": "boss",
    "inicio": None,
}

ENTITY_DISPLAY = {
    "enemigo_v": "V (melee V)",
    "enemigo_h": "H (melee H)",
    "enemigo_c": "C (melee C)",
    "enemy_shooter_h": "S (shooter H)",
    "enemy_shooter_v": "T (shooter V)",
}


def get_sprite_file(tipo):
    return SPRITE_FILE_MAP.get(tipo, tipo)


def sprite_id_to_file(sprite_id):
    info = get_sprite_registry().get(sprite_id)
    if info:
        return info.get("file")
    return None


def sprite_id_to_display(sprite_id):
    info = get_sprite_registry().get(sprite_id)
    if info:
        return info.get("display", sprite_id)
    return sprite_id


def char_to_sprite_id(char):
    return CHAR_TO_SPRITE.get(char)
