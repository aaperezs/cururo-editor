"""Parser de mapas de texto plano (formato legacy).

Extraído de orm/levels/level_parser.py para eliminar la dependencia
del editor con el runtime ORM. Solo contiene la lógica de parsing de
texto a grilla de sprite_ids — NO crea entidades del juego.
"""

CHAR_MAP = {
    '_': None,
    '.': None,
    '&': None,
    '*': 'pared',
    '#': 'bloque_acero',
    'I': 'inicio',
    'O': 'comida_normal',
    'M': 'comida_mana',
    'G': 'comida_dorada',
    'V': 'enemigo_melee_v',
    'H': 'enemigo_melee_h',
    'C': 'enemigo_melee_c',
    'S': 'enemigo_shooter_h',
    'T': 'enemigo_shooter_v',
    'R': 'roca',
    'A': 'arbol',
    'F': 'roca_hielo',
    'N': 'roca_nieve',
    'Y': 'hierba_0',
    'P': 'portal',
    'B': 'jefe',
    '$': 'cofre',
    '=': 'restricted',
}

CHAR_MAP_REVERSE = {v: k for k, v in CHAR_MAP.items() if v is not None}


def parsear_lineas(mapa_texto):
    """Parsea texto plano de mapa a grilla de sprite_ids.

    Returns:
        dict con claves: grid, ancho, alto (en celdas, no píxeles)
    """
    lineas = mapa_texto.strip().split('\n')
    lineas = [l.rstrip() for l in lineas if l.strip() and not l.startswith('# ')]

    alto = len(lineas)
    ancho = max(len(l) for l in lineas) if lineas else 0

    grid = {}
    for y, linea in enumerate(lineas):
        for x, ch in enumerate(linea):
            sprite_id = CHAR_MAP.get(ch)
            if sprite_id is not None:
                grid[(x, y)] = sprite_id

    return {"grid": grid, "ancho": ancho, "alto": alto}


def parsear_mapa(mapa_texto):
    """Parsea mapa legacy y devuelve diccionario con dimensiones en celdas."""
    return parsear_lineas(mapa_texto)
