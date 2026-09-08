import json
import os

from engine.repositories import (
    RepositorioComida,
    RepositorioEnemigos,
    RepositorioHabilidades,
    RepositorioJefes,
    RepositorioObjetos,
    RepositorioRecetas,
)
from engine.repositories.base import RUTA_DATA


class ConfigProvider:
    """Singleton que provee acceso lazy a todas las configuraciones desde JSON."""

    def __init__(self):
        self._repo_hab = None
        self._repo_food = None
        self._repo_enemigos = None
        self._repo_jefes = None
        self._repo_objetos = None
        self._repo_recetas = None
        self._gameplay = None

    # ── Skills ──

    @property
    def _habilidades(self):
        if self._repo_hab is None:
            self._repo_hab = RepositorioHabilidades()
        return self._repo_hab

    def get_skills_all(self):
        return self._habilidades.get_todas()

    def get_skill(self, hid):
        return self._habilidades.get_habilidad(hid)

    def get_skin(self, efecto):
        return self._habilidades.get_skin(efecto)

    def get_initial_skills(self):
        return self._habilidades.get_iniciales()

    def get_skill_by_effect(self, efecto):
        return self._habilidades.get_habilidad_por_efecto(efecto)

    # ── Food ──

    @property
    def _comida(self):
        if self._repo_food is None:
            self._repo_food = RepositorioComida()
        return self._repo_food

    def get_food_types(self):
        return self._comida.get_tipos()

    def get_food_type(self, nombre):
        return self._comida.get_tipo(nombre)

    def get_food_probability(self, tipo):
        return self._comida.get_probabilidad(tipo)

    # ── Enemies ──

    @property
    def _enemigos(self):
        if self._repo_enemigos is None:
            self._repo_enemigos = RepositorioEnemigos()
        return self._repo_enemigos

    def get_enemy_config(self, tipo, subtipo):
        return self._enemigos.get_enemigo_config(tipo, subtipo)

    def get_enemy_char_map(self):
        return self._enemigos.get_char_map()

    # ── Bosses ──

    @property
    def _jefes(self):
        if self._repo_jefes is None:
            self._repo_jefes = RepositorioJefes()
        return self._repo_jefes

    def get_boss_config(self, boss_id):
        return self._jefes.get_boss_config(boss_id)

    # ── Items/Objects ──

    @property
    def _objetos(self):
        if self._repo_objetos is None:
            self._repo_objetos = RepositorioObjetos()
        return self._repo_objetos

    def get_item(self, item_id):
        return self._objetos.get_objeto(item_id)

    def get_all_items(self):
        return self._objetos.get_todos()

    # ── Recipes ──

    @property
    def _recetas(self):
        if self._repo_recetas is None:
            self._repo_recetas = RepositorioRecetas()
        return self._repo_recetas

    def get_all_recipes(self):
        return self._recetas.get_todas()

    def get_recipe(self, rid):
        return self._recetas.get_receta(rid)



    # ── Gameplay tunables ──

    @property
    def _gameplay_data(self):
        if self._gameplay is None:
            ruta = os.path.join(RUTA_DATA, "gameplay.json")
            try:
                with open(ruta, "r", encoding="utf-8") as f:
                    self._gameplay = json.load(f)
            except FileNotFoundError:
                print(f"[CONFIG] gameplay.json no encontrado en {ruta}")
                self._gameplay = {}
        return self._gameplay

    def get_gameplay(self, *keys, default=None):
        data = self._gameplay_data
        for k in keys:
            if isinstance(data, dict):
                data = data.get(k)
            else:
                return default
        return data if data is not None else default


config_provider = ConfigProvider()
