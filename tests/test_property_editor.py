from editor.property_editor import (
    build_properties,
)


class TestBuildProperties:
    def test_empty_schema(self):
        widgets, y = build_properties(
            {}, {}, 10, lambda k: k,
            lambda k, v: None, lambda k, v: None,
            lambda k: None, lambda k: None, None,
        )
        assert widgets == {}
        assert y == 10

    def test_bool_property(self):
        schema = {"flag": {"type": "bool", "label": "Flag"}}
        widgets, y = build_properties(
            schema, {"flag": True}, 10, lambda k: k,
            lambda k, v: None, lambda k, v: None,
            lambda k: None, lambda k: None, None,
        )
        assert "flag" in widgets
        assert "lbl_flag" in widgets
        assert y == 36

    def test_choice_property(self):
        schema = {"mode": {"type": "choice", "options": ["a", "b"], "label": "Mode"}}
        widgets, y = build_properties(
            schema, {}, 10, lambda k: k,
            lambda k, v: None, lambda k, v: None,
            lambda k: None, lambda k: None, None,
        )
        assert "mode" in widgets
        assert y == 36

    def test_int_property(self):
        schema = {"hp": {"type": "int", "default": 10, "label": "HP"}}
        widgets, y = build_properties(
            schema, {}, 10, lambda k: k,
            lambda k, v: None, lambda k, v: None,
            lambda k: None, lambda k: None, None,
        )
        assert "hp" in widgets
        assert y == 36

    def test_str_property(self):
        schema = {"desc": {"type": "str", "default": "", "label": "Desc"}}
        widgets, y = build_properties(
            schema, {}, 10, lambda k: k,
            lambda k, v: None, lambda k, v: None,
            lambda k: None, lambda k: None, None,
        )
        assert "desc" in widgets
        assert y == 36

    def test_drop_list_property(self):
        schema = {"drops": {"type": "drop_list", "label": "Drops"}}
        widgets, y = build_properties(
            schema, {"drops": []}, 10, lambda k: k,
            lambda k, v: None, lambda k, v: None,
            lambda k: None, lambda k: None, None,
        )
        assert "drops" in widgets
        assert isinstance(widgets["drops"], list)
        assert y == 34

    def test_multiple_properties(self):
        schema = {
            "a": {"type": "bool", "label": "A"},
            "b": {"type": "int", "default": 0, "label": "B"},
        }
        widgets, y = build_properties(
            schema, {}, 10, lambda k: k,
            lambda k, v: None, lambda k, v: None,
            lambda k: None, lambda k: None, None,
        )
        assert "a" in widgets
        assert "b" in widgets
        assert y == 62

    def test_uses_current_props_value(self):
        schema = {"hp": {"type": "int", "default": 10, "label": "HP"}}
        widgets, _ = build_properties(
            schema, {"hp": 99}, 10, lambda k: k,
            lambda k, v: None, lambda k, v: None,
            lambda k: None, lambda k: None, None,
        )
        assert widgets["hp"].text == "99"
