from engine.services.config_provider import config_provider

_gp = config_provider.get_gameplay

VELOCIDAD_BASE = _gp("snake", "speed_base", default=10)
VELOCIDAD_DEUDA = _gp("snake", "speed_debt", default=12)

VELOCIDAD_MULT_GRASS = 0.6
VELOCIDAD_MULT_SPEED = 1.3
VELOCIDAD_MULT_NORMAL = 1.0

LONGITUD_INICIAL = _gp("snake", "initial_length", default=3)

SCREENS_ENABLED = True
