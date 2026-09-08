from engine.services.data_service import DataService


class TestDataService:
    def setup_method(self):
        self.ds = DataService()

    def test_get_item_name(self):
        name = self.ds.get_item_name("cinta_de_la_vida")
        assert name and name != "Desconocido"

    def test_get_item_name_default(self):
        name = self.ds.get_item_name("__no_existe__")
        assert name == "Desconocido"

    def test_is_item_equippable(self):
        assert self.ds.is_item_equippable("cinta_de_la_vida") is True

    def test_get_skill_name(self):
        name = self.ds.get_skill_name("golpe_cabeza")
        assert name and name != "???"

    def test_get_skill_pp(self):
        pp = self.ds.get_skill_pp("golpe_cabeza")
        assert pp > 0

    def test_get_combat_damage_range(self):
        lo, hi = self.ds.get_combat_damage_range()
        assert lo == 2
        assert hi == 4

    def test_get_float_text_duration(self):
        d = self.ds.get_float_text_duration()
        assert d == 30

