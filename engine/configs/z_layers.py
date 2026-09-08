# configs/z_layers.py
"""
Definición de capas Z para el juego ORM
"""

# Capas principales
Z_MAPA_PRINCIPAL = 0      # Nivel principal
Z_ARENA_JEFE = -2         # Arena del jefe (debajo del mapa)
Z_PLATAFORMA_SUPERIOR = 1 # Plataformas elevadas
Z_SOTANO = -1             # Sótanos o cuevas profundas

# Transiciones entre capas
TRANSICIONES = {
    # (z_origen, z_destino): (sprite, mensaje)
    (Z_MAPA_PRINCIPAL, Z_ARENA_JEFE): {
        "sprite": "portal_jefe",
        "mensaje": "⚔️ Entrando a la arena del jefe..."
    },
    (Z_ARENA_JEFE, Z_MAPA_PRINCIPAL): {
        "sprite": "portal_salida",
        "mensaje": "🏆 ¡Jefe derrotado! Regresando..."
    },
    (Z_MAPA_PRINCIPAL, Z_PLATAFORMA_SUPERIOR): {
        "sprite": "escalera",
        "mensaje": "⬆️ Subiendo..."
    },
}
