from engine.services.config_provider import config_provider


class HabilidadID:
    BASE = "base"
    GOLPE_CABEZA = "golpe_cabeza"
    MANTO_OSCURIDAD = "manto_oscuridad"
    COLA_LATIGO = "cola_latigo"


HABILIDADES = config_provider.get_skills_all()

_COLORES_HABILIDAD = {}
for efecto in ["base", "golpe", "manto", "latigo"]:
    skin = config_provider.get_skin(efecto)
    _COLORES_HABILIDAD[efecto] = (tuple(skin.get("cabeza", (0, 0, 0))),
                                   tuple(skin.get("cuerpo", (0, 0, 0))))
_COLORES_HABILIDAD[None] = _COLORES_HABILIDAD["base"]
COLORES_HABILIDAD = _COLORES_HABILIDAD


class SkinSnake:
    _base = config_provider.get_skin("base")
    _golpe = config_provider.get_skin("golpe")
    _manto = config_provider.get_skin("manto")
    _latigo = config_provider.get_skin("latigo")

    BASE_CABEZA = tuple(_base.get("cabeza", (100, 255, 100)))
    BASE_CUERPO = tuple(_base.get("cuerpo", (0, 200, 0)))
    GOLPE_CABEZA = tuple(_golpe.get("cabeza", (210, 180, 140)))
    GOLPE_CUERPO = tuple(_golpe.get("cuerpo", (139, 90, 43)))
    MANTO_CABEZA = tuple(_manto.get("cabeza", (180, 180, 190)))
    MANTO_CUERPO = tuple(_manto.get("cuerpo", (80, 80, 90)))
    LATIGO_CABEZA = tuple(_latigo.get("cabeza", (230, 120, 50)))
    LATIGO_CUERPO = tuple(_latigo.get("cuerpo", (200, 60, 30)))


def get_habilidad_por_efecto(efecto):
    return config_provider.get_skill_by_effect(efecto)


def get_colores_skin(efecto):
    return _COLORES_HABILIDAD.get(efecto, _COLORES_HABILIDAD["base"])
