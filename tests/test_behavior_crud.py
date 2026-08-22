from unittest.mock import patch
from editor.behavior_crud import (
    create_new_behavior, save_behavior, delete_behavior_by_id,
    add_property_to_behavior, remove_property_from_behavior,
)


class TestCreateNewBehavior:
    @patch("editor.behavior_crud.get_behavior_list", return_value=[])
    @patch("editor.behavior_crud.set_behavior")
    def test_creates_with_base_id(self, mock_set, mock_list):
        bid = create_new_behavior()
        assert bid == "custom_behavior"
        mock_set.assert_called_once()
        data = mock_set.call_args[0][1]
        assert data["group"] == "custom"
        assert data["properties"] == {}

    @patch("editor.behavior_crud.get_behavior_list", return_value=[("custom_behavior", "x")])
    @patch("editor.behavior_crud.set_behavior")
    def test_appends_number(self, mock_set, mock_list):
        bid = create_new_behavior()
        assert bid == "custom_behavior_1"


class TestSaveBehavior:
    @patch("editor.behavior_crud.set_behavior")
    def test_saves_without_rename(self, mock_set):
        result = save_behavior("b1", {"label": "test"})
        assert result is True
        mock_set.assert_called_once_with("b1", {"label": "test"})

    @patch("editor.behavior_crud.delete_behavior")
    @patch("editor.behavior_crud.set_behavior")
    def test_deletes_old_on_rename(self, mock_set, mock_del):
        result = save_behavior("new_id", {"label": "test"}, old_id="old_id")
        assert result is True
        mock_del.assert_called_once_with("old_id")
        mock_set.assert_called_once_with("new_id", {"label": "test"})

    @patch("editor.behavior_crud.set_behavior")
    def test_no_delete_when_same_id(self, mock_set):
        result = save_behavior("b1", {"label": "test"}, old_id="b1")
        assert result is True
        mock_set.assert_called_once_with("b1", {"label": "test"})


class TestDeleteBehaviorById:
    @patch("editor.behavior_crud.delete_behavior")
    def test_calls_delete(self, mock_del):
        delete_behavior_by_id("b1")
        mock_del.assert_called_once_with("b1")


class TestAddPropertyToBehavior:
    @patch("editor.behavior_crud.get_behavior", return_value=None)
    def test_returns_false_if_not_found(self, _):
        assert add_property_to_behavior("x") is False

    @patch("editor.behavior_crud.get_behavior")
    @patch("editor.behavior_crud.set_behavior")
    def test_adds_new_prop(self, mock_set, mock_get):
        mock_get.return_value = {"properties": {}}
        result = add_property_to_behavior("b1")
        assert result is True
        saved = mock_set.call_args[0][1]
        props = saved["properties"]
        assert "prop_1" in props
        assert props["prop_1"]["type"] == "bool"

    @patch("editor.behavior_crud.get_behavior")
    @patch("editor.behavior_crud.set_behavior")
    def test_avoids_id_collision(self, mock_set, mock_get):
        mock_get.return_value = {"properties": {"prop_1": {}, "prop_2": {}}}
        result = add_property_to_behavior("b1")
        assert result is True
        props = mock_set.call_args[0][1]["properties"]
        assert "prop_3" in props


class TestRemovePropertyFromBehavior:
    @patch("editor.behavior_crud.get_behavior", return_value=None)
    def test_returns_false_if_not_found(self, _):
        assert remove_property_from_behavior("x", "key") is False

    @patch("editor.behavior_crud.get_behavior")
    @patch("editor.behavior_crud.set_behavior")
    def test_removes_existing_prop(self, mock_set, mock_get):
        mock_get.return_value = {"properties": {"key": {"type": "bool"}}}
        result = remove_property_from_behavior("b1", "key")
        assert result is True
        props = mock_set.call_args[0][1]["properties"]
        assert "key" not in props

    @patch("editor.behavior_crud.get_behavior")
    def test_returns_false_if_key_not_found(self, mock_get):
        mock_get.return_value = {"properties": {"other": {}}}
        result = remove_property_from_behavior("b1", "missing")
        assert result is False
