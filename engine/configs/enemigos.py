from engine.services.config_provider import config_provider

CHAR_TO_ENEMIGO = config_provider.get_enemy_char_map()


def get_enemigo_config(tipo, subtipo):
    return config_provider.get_enemy_config(tipo, subtipo)
