CATEGORIES = {
    "snake_rpg": {
        "id": "snake_rpg",
        "name": "Snake RPG",
        "description": "Juego tipo snake con enemigos, items, habilidades y bosses (estilo Orm)",
        "template_dirs": ["snake_rpg"],
        "panels": [
            "sprites", "maps", "events", "elements", "behaviors",
            "abilities", "items", "bosses", "animations",
            "scripts", "screens", "dialogos", "characters", "assets",
            "scenes", "minigames", "audio", "menus", "monedas",
            "shops", "contadores", "save_system",
        ],
    },
    "visual_novel": {
        "id": "visual_novel",
        "name": "Novela Visual",
        "description": "Simulador de citas / novela visual con imagenes en alta resolucion",
        "template_dirs": ["visual_novel"],
        "panels": [
            "scripts", "dialogos", "characters", "assets", "scenes", "minigames", "audio",
        ],
    },
    "blank": {
        "id": "blank",
        "name": "Vacio",
        "description": "Proyecto vacio sin comportamientos predefinidos",
        "template_dirs": ["blank"],
        "panels": [
            "sprites", "maps", "events", "elements", "behaviors",
            "scripts", "scenes", "minigames", "audio",
        ],
    },
}


def get_category(category_id):
    return CATEGORIES.get(category_id)


def get_all_categories():
    return list(CATEGORIES.values())


def get_panels_for_category(category_id):
    cat = get_category(category_id)
    if cat:
        return list(cat["panels"])
    return []


def get_template_dirs(category_id):
    cat = get_category(category_id)
    if cat:
        return list(cat["template_dirs"])
    return []
