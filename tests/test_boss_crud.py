from unittest.mock import patch, MagicMock
from editor.boss_crud import (
    create_new_boss, clone_boss, delete_boss_by_id, save_boss,
    add_phase, delete_phase,
)


def _mock_bosses(data=None):
    return data or {}


class TestCreateNewBoss:
    @patch("editor.boss_crud.get_all_bosses", return_value=[])
    @patch("editor.boss_crud.create_boss")
    def test_creates_with_base_id(self, mock_create, mock_all):
        bid = create_new_boss()
        assert bid == "nuevo_boss"
        mock_create.assert_called_once_with("nuevo_boss")

    @patch("editor.boss_crud.get_all_bosses", return_value=["nuevo_boss"])
    @patch("editor.boss_crud.create_boss")
    def test_appends_number_when_exists(self, mock_create, mock_all):
        bid = create_new_boss()
        assert bid == "nuevo_boss_1"


class TestCloneBoss:
    @patch("editor.boss_crud.get_boss", return_value=None)
    def test_returns_none_if_not_found(self, _):
        assert clone_boss("nonexistent") is None

    @patch("editor.boss_crud.get_boss")
    @patch("editor.boss_crud.get_all_bosses", return_value=[])
    @patch("editor.boss_crud.set_boss")
    def test_clones_with_copia_suffix(self, mock_set, mock_all, mock_get):
        mock_get.return_value = {"vida_maxima": 80}
        bid = clone_boss("boss1")
        assert bid == "boss1_copia"
        mock_set.assert_called_once()
        args = mock_set.call_args[0]
        assert args[0] == "boss1_copia"


class TestDeleteBossById:
    @patch("editor.boss_crud.delete_boss")
    def test_calls_delete(self, mock_del):
        delete_boss_by_id("b1")
        mock_del.assert_called_once_with("b1")


class TestSaveBoss:
    @patch("editor.boss_crud.get_boss", return_value=None)
    def test_returns_false_if_not_found(self, _):
        assert save_boss("x", {}) is False

    @patch("editor.boss_crud.get_boss")
    @patch("editor.boss_crud.set_boss")
    def test_merges_fields(self, mock_set, mock_get):
        mock_get.return_value = {"vida_maxima": 80, "nombre": "old"}
        result = save_boss("b1", {"nombre": "new"})
        assert result is True
        saved = mock_set.call_args[0]
        assert saved[1]["nombre"] == "new"
        assert saved[1]["vida_maxima"] == 80


class TestAddPhase:
    @patch("editor.boss_crud.get_boss", return_value=None)
    def test_returns_false_if_not_found(self, _):
        assert add_phase("x") is False

    @patch("editor.boss_crud.get_boss")
    @patch("editor.boss_crud.set_boss")
    def test_adds_phase_at_half_threshold(self, mock_set, mock_get):
        boss = {"fight_type": "orbital", "phases": [{"hp_threshold": 1.0}]}
        mock_get.return_value = boss
        result = add_phase("b1")
        assert result is True
        phases = mock_set.call_args[0][1]["phases"]
        assert len(phases) == 2
        assert phases[-1]["hp_threshold"] == 0.5

    @patch("editor.boss_crud.get_boss")
    @patch("editor.boss_crud.set_boss")
    def test_adds_default_threshold_when_no_phases(self, mock_set, mock_get):
        boss = {"fight_type": "orbital", "phases": []}
        mock_get.return_value = boss
        result = add_phase("b1")
        assert result is True
        phases = mock_set.call_args[0][1]["phases"]
        assert phases[0]["hp_threshold"] == 0.5


class TestDeletePhase:
    @patch("editor.boss_crud.get_boss", return_value=None)
    def test_returns_false_if_not_found(self, _):
        assert delete_phase("x", 0) is False

    @patch("editor.boss_crud.get_boss")
    @patch("editor.boss_crud.set_boss")
    def test_returns_false_if_out_of_range(self, mock_set, mock_get):
        mock_get.return_value = {"phases": [{"hp_threshold": 1.0}]}
        assert delete_phase("b1", 5) is False

    @patch("editor.boss_crud.get_boss")
    @patch("editor.boss_crud.set_boss")
    def test_returns_false_if_only_one_phase(self, mock_set, mock_get):
        mock_get.return_value = {"phases": [{"hp_threshold": 1.0}]}
        assert delete_phase("b1", 0) is False

    @patch("editor.boss_crud.get_boss")
    @patch("editor.boss_crud.set_boss")
    def test_deletes_second_phase(self, mock_set, mock_get):
        mock_get.return_value = {"phases": [{"hp_threshold": 1.0}, {"hp_threshold": 0.0}]}
        result = delete_phase("b1", 1)
        assert result is True
        phases = mock_set.call_args[0][1]["phases"]
        assert len(phases) == 1
