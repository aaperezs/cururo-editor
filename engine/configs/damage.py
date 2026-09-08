from engine.services.config_provider import config_provider

_gp = config_provider.get_gameplay

LONGITUD_MINIMA = _gp("combat", "min_length", default=3)
DANO_MINIMO = _gp("combat", "damage_min", default=2)
DANO_MAXIMO = _gp("combat", "damage_max", default=4)

COLOR_MANTO = tuple(_gp("manto", "color", default=[80, 80, 100]))
EFECTO_MANTO_DURACION = _gp("manto", "effect_duration", default=60)
