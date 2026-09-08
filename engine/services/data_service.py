from engine.services.config_provider import config_provider


class DataService:
    """Application service: validates and coordinates data access across repositories."""

    def __init__(self):
        self._config = config_provider

    # ── Item helpers ──

    def get_item_name(self, item_id, default="Desconocido"):
        item = self._config.get_item(item_id)
        if item:
            return item.get("nombre", item.get("name", default))
        return default

    def is_item_equippable(self, item_id):
        item = self._config.get_item(item_id)
        return bool(item and item.get("slot"))

    def get_item_slot(self, item_id):
        item = self._config.get_item(item_id)
        return item.get("slot") if item else None

    # ── Skill helpers ──

    def get_skill_name(self, skill_id, default="???"):
        skill = self._config.get_skill(skill_id)
        return skill.get("nombre", default) if skill else default

    def get_skill_pp(self, skill_id):
        skill = self._config.get_skill(skill_id)
        return skill.get("pp_max", 0) if skill else 0

    def get_skill_effect(self, skill_id):
        skill = self._config.get_skill(skill_id)
        return skill.get("efecto") if skill else None

    # ── Food helpers ──

    def get_food_color(self, food_id):
        from engine.configs.food import COLOR_COMIDA
        return COLOR_COMIDA.get(food_id, (255, 255, 255))

    def get_food_name(self, food_id):
        from engine.configs.food import NOMBRE_COMIDA
        return NOMBRE_COMIDA.get(food_id, "Desconocido")

    # ── Recipe helpers ──

    def get_recipe_result(self, recipe_id):
        recipe = self._config.get_recipe(recipe_id)
        return recipe.get("resultado") if recipe else None

    def get_recipe_materials(self, recipe_id):
        recipe = self._config.get_recipe(recipe_id)
        return recipe.get("materiales", []) if recipe else []

    # ── Gameplay helpers ──

    def get_combat_damage_range(self):
        return (
            self._config.get_gameplay("combat", "damage_min", default=2),
            self._config.get_gameplay("combat", "damage_max", default=4),
        )

    def get_food_spawn_retries(self):
        return self._config.get_gameplay("food", "spawn_retries", default=200)

    # ── UI / text helpers ──

    def get_float_text_duration(self, short=True):
        key = "floating_text_duration" if short else "floating_text_duration_long"
        return self._config.get_gameplay("ui", key, default=30)

    def get_overlay_alpha(self, pause=True):
        key = "pause_overlay_alpha" if pause else "gameover_overlay_alpha"
        return self._config.get_gameplay("ui", key, default=180)


data_service = DataService()
