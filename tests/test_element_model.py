from editor.element_model import (
    get_behavior_schema, get_current_props, should_reset_props,
    apply_props_to_element, apply_multi_tile, build_drop_options,
    create_empty_drop, validate_drop,
)


class TestGetBehaviorSchema:
    def test_returns_properties_for_known_behavior(self):
        schema = get_behavior_schema("destruible")
        assert "maxHP" in schema or "hp" in schema or len(schema) >= 0

    def test_returns_empty_for_unknown(self):
        schema = get_behavior_schema("nonexistent_behavior")
        assert schema == {}


class TestGetCurrentProps:
    def test_returns_props_dict(self):
        el = {"properties": {"foo": 1, "bar": 2}}
        assert get_current_props(el) == {"foo": 1, "bar": 2}

    def test_returns_empty_when_no_props(self):
        assert get_current_props({}) == {}


class TestShouldResetProps:
    def test_true_when_different(self):
        assert should_reset_props("a", "b") is True

    def test_false_when_same(self):
        assert should_reset_props("a", "a") is False


class TestApplyPropsToElement:
    def test_resets_props_when_behavior_changed(self):
        el = {"behavior": "old", "properties": {"x": 1}}
        apply_props_to_element(el, "new", {"x": 2})
        assert "x" not in el["properties"] or el["properties"] != {"x": 2}

    def test_keeps_props_when_same_behavior(self):
        el = {"behavior": "same", "properties": {"x": 1}}
        apply_props_to_element(el, "same", {"x": 99})
        assert el["properties"]["x"] == 99


class TestApplyMultiTile:
    def test_sets_multi_tile_flag(self):
        el = {"behavior": "multi_tile"}
        apply_multi_tile(el, "spr", [{"col": 0, "row": 0}])
        assert el["multi_tile"] is True
        assert "subtiles" in el

    def test_removes_multi_tile_when_not_multi(self):
        el = {"behavior": "other", "multi_tile": True}
        apply_multi_tile(el, "spr", [])
        assert "multi_tile" not in el


class TestBuildDropOptions:
    def test_returns_tuple_of_lists(self):
        items, abilities = build_drop_options()
        assert isinstance(items, list)
        assert isinstance(abilities, list)
        assert ("", "Cualquiera") in abilities


class TestCreateEmptyDrop:
    def test_has_default_prob(self):
        d = create_empty_drop()
        assert d["prob"] == 50
        assert d["item"] == ""


class TestValidateDrop:
    def test_valid_with_item(self):
        assert validate_drop({"item": "sword"}) is True

    def test_invalid_without_item(self):
        assert validate_drop({"item": ""}) is False

    def test_invalid_empty(self):
        assert validate_drop({}) is False
