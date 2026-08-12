BOSS_FIGHT_TYPES = {
    "orbital": {
        "label": "Orbital",
        "description": "Jefe orbita circularmente y lanza proyectiles radiales",
        "phase_params": {
            "speed_mult": {"type": "float", "default": 1.0, "label": "Mult. velocidad", "min": 0.1, "group": "movimiento"},
            "attack_cooldown": {"type": "int", "default": 60, "label": "Cooldown (frames)", "min": 5, "group": "ataque"},
            "projectile_speed": {"type": "float", "default": 2.0, "label": "Vel. proyectil", "min": 0.5, "group": "ataque"},
            "projectile_count_bonus": {"type": "int", "default": 0, "label": "Proyectiles extra", "min": 0, "group": "ataque"},
            "comestible_chance": {"type": "float", "default": 0.6, "label": "Prob. comestible", "min": 0.0, "max": 1.0, "group": "proyectiles"},
            "angle_spread": {"type": "float", "default": 0.2, "label": "Disp. angular", "min": 0.0, "group": "ataque"},
            "orbit_radius": {"type": "int", "default": 100, "label": "Radio orbita", "min": 20, "group": "movimiento"},
            "orbit_speed": {"type": "float", "default": 0.02, "label": "Vel. orbita", "min": 0.001, "group": "movimiento"},
            "projectile_lifetime": {"type": "int", "default": 180, "label": "Vida proyectil", "min": 10, "group": "proyectiles"},
            "golden_radius": {"type": "int", "default": 10, "label": "Radio dorado", "min": 2, "group": "proyectiles"},
            "red_radius": {"type": "int", "default": 8, "label": "Radio rojo", "min": 2, "group": "proyectiles"}
        },
        "phase_groups": {
            "movimiento": {"label_key": "boss.group.movimiento"},
            "ataque": {"label_key": "boss.group.ataque"},
            "proyectiles": {"label_key": "boss.group.proyectiles"},
            "general": {"label_key": "boss.group.general"}
        },
        "visual_schema": {
            "trunk_color": {"type": "color", "default": [95, 60, 28], "label": "Color tronco", "group": "cuerpo"},
            "eye_color": {"type": "color", "default": [150, 200, 80], "label": "Color ojos", "group": "cuerpo"},
            "eye_size": {"type": "int", "default": 5, "label": "Tam. ojos", "min": 1, "group": "cuerpo"},
            "rune": {"type": "string", "default": "\u00de\u00be", "label": "Simbolo fase", "group": "runa"},
            "rune_color": {"type": "color", "default": [100, 200, 100], "label": "Color runa", "group": "runa"},
            "bar_color": {"type": "color", "default": None, "label": "Color barra (opcional)", "group": "barra"}
        },
        "visual_groups": {
            "cuerpo": {"label_key": "boss.group.cuerpo"},
            "runa": {"label_key": "boss.group.runa"},
            "barra": {"label_key": "boss.group.barra"},
            "general": {"label_key": "boss.group.general"}
        }
    }
}


DEFAULT_PHASE_PARAMS = {}
for ft_id, ft_data in BOSS_FIGHT_TYPES.items():
    DEFAULT_PHASE_PARAMS[ft_id] = {}
    for pkey, pdata in ft_data.get("phase_params", {}).items():
        DEFAULT_PHASE_PARAMS[ft_id][pkey] = pdata.get("default")


DEFAULT_VISUAL = {}
for ft_id, ft_data in BOSS_FIGHT_TYPES.items():
    DEFAULT_VISUAL[ft_id] = {}
    for pkey, pdata in ft_data.get("visual_schema", {}).items():
        DEFAULT_VISUAL[ft_id][pkey] = pdata.get("default")


def get_default_phase(ftype):
    params = dict(DEFAULT_PHASE_PARAMS.get(ftype, {}))
    visual = dict(DEFAULT_VISUAL.get(ftype, {}))
    return {"hp_threshold": 0.0, "params": params, "visual": visual}
