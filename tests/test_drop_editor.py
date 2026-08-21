from editor.drop_editor import (
    add_drop, remove_drop, update_drop_prob,
    update_drop_item, update_drop_ability,
)


class TestAddDrop:
    def test_adds_empty_drop(self):
        data = []
        add_drop(data)
        assert len(data) == 1
        assert data[0] == {"item": "", "prob": 50}

    def test_adds_to_existing(self):
        data = [{"item": "a", "prob": 10}]
        add_drop(data)
        assert len(data) == 2


class TestRemoveDrop:
    def test_removes_valid_index(self):
        data = [{"item": "a"}, {"item": "b"}]
        assert remove_drop(data, 0) is True
        assert len(data) == 1
        assert data[0]["item"] == "b"

    def test_rejects_out_of_range(self):
        data = [{"item": "a"}]
        assert remove_drop(data, 5) is False
        assert len(data) == 1

    def test_rejects_negative(self):
        data = [{"item": "a"}]
        assert remove_drop(data, -1) is False


class TestUpdateDropProb:
    def test_valid_int(self):
        d = {"prob": 0}
        assert update_drop_prob(d, "75") is True
        assert d["prob"] == 75

    def test_empty_string(self):
        d = {"prob": 50}
        assert update_drop_prob(d, "") is True
        assert d["prob"] == 0

    def test_invalid_string(self):
        d = {"prob": 50}
        assert update_drop_prob(d, "abc") is False
        assert d["prob"] == 50


class TestUpdateDropItem:
    def test_sets_item(self):
        d = {"item": ""}
        update_drop_item(d, "sword")
        assert d["item"] == "sword"


class TestUpdateDropAbility:
    def test_sets_ability(self):
        d = {}
        update_drop_ability(d, "fire")
        assert d["ability"] == "fire"

    def test_clears_ability(self):
        d = {"ability": "fire"}
        update_drop_ability(d, "")
        assert "ability" not in d
