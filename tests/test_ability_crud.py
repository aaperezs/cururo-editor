from unittest.mock import patch
from editor.ability_crud import create_new_ability, clone_ability, delete_ability_by_id


class TestCreateNewAbility:
    @patch("editor.ability_crud.get_abilities", return_value={})
    @patch("editor.ability_crud.create_ability")
    def test_creates_with_base_id(self, mock_create, mock_all):
        hid = create_new_ability()
        assert hid == "habilidad_nueva"
        mock_create.assert_called_once_with("habilidad_nueva")

    @patch("editor.ability_crud.get_abilities", return_value={"habilidad_nueva": {}})
    @patch("editor.ability_crud.create_ability")
    def test_appends_number(self, mock_create, mock_all):
        hid = create_new_ability()
        assert hid == "habilidad_nueva_1"


class TestCloneAbility:
    @patch("editor.ability_crud.get_ability", return_value=None)
    def test_returns_none_if_not_found(self, _):
        assert clone_ability("nonexistent") is None

    @patch("editor.ability_crud.get_ability")
    @patch("editor.ability_crud.get_abilities", return_value={})
    @patch("editor.ability_crud.set_ability")
    def test_clones_with_copia_suffix(self, mock_set, mock_all, mock_get):
        mock_get.return_value = {"nombre": "fireball"}
        hid = clone_ability("ab1")
        assert hid == "ab1_copia"
        mock_set.assert_called_once()


class TestDeleteAbilityById:
    @patch("editor.ability_crud.is_protected", return_value=True)
    def test_returns_false_if_protected(self, _):
        assert delete_ability_by_id("base") is False

    @patch("editor.ability_crud.is_protected", return_value=False)
    @patch("editor.ability_crud.delete_ability")
    def test_deletes_when_not_protected(self, mock_del, _):
        result = delete_ability_by_id("ab1")
        assert result is True
        mock_del.assert_called_once_with("ab1")

    @patch("editor.ability_crud.is_protected", return_value=False)
    @patch("editor.ability_crud.delete_ability")
    def test_returns_true_on_success(self, mock_del, _):
        assert delete_ability_by_id("ab1") is True
