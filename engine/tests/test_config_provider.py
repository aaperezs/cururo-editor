from engine.services.config_provider import config_provider, ConfigProvider


class TestConfigProvider:
    def setup_method(self):
        self.cp = config_provider

    def test_get_gameplay(self):
        dmg = self.cp.get_gameplay("combat", "damage_min")
        assert dmg == 2

    def test_get_gameplay_default(self):
        val = self.cp.get_gameplay("nonexistent", default=42)
        assert val == 42

    def test_get_item(self):
        item = self.cp.get_item("cinta_de_la_vida")
        assert item is not None, "cinta_de_la_vida should exist in objects repo"

    def test_get_item_nonexistent(self):
        item = self.cp.get_item("__no_existe__")
        assert item is None

    def test_get_skill(self):
        skill = self.cp.get_skill("golpe_cabeza")
        assert skill is not None

    def test_get_enemy_config(self):
        cfg = self.cp.get_enemy_config("melee", "horizontal")
        assert cfg is not None
        assert "velocidad" in cfg

    def test_get_all_items(self):
        items = self.cp.get_all_items()
        assert isinstance(items, dict)

    def test_get_all_recipes(self):
        recs = self.cp.get_all_recipes()
        assert isinstance(recs, dict)

    def test_module_singleton(self):
        from services.config_provider import ConfigProvider
        cp2 = ConfigProvider()
        assert cp2 is not self.cp

