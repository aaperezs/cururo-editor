from engine.services.config_provider import config_provider

COMIDA_NORMAL = 0
COMIDA_MANA = 1
COMIDA_ESPECIAL = 2

COLOR_COMIDA = {}
NOMBRE_COMIDA = {}

for nombre, config in config_provider.get_food_types().items():
    tid = config["id"]
    COLOR_COMIDA[tid] = tuple(config["color"])
    NOMBRE_COMIDA[tid] = config["nombre"]
