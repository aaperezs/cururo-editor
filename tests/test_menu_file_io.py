"""Tests unitarios para editor.menu.file_io — commit, persist, save."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch, MagicMock

import pytest

from editor.menu.file_io import (
    commit_current,
    commit_config,
    commit_controles,
    persist,
    persist_controles,
    sel_option,
)


# ── Helpers ────────────────────────────────────────────────

def _make_menu(menu_id: str = "test_menu", n_apartados: int = 2) -> dict[str, Any]:
    apartados = []
    for i in range(n_apartados):
        apartados.append({
            "id": f"ap_{i}",
            "nombre": f"Apartado {i}",
            "tipo": "lista",
            "items": [{"id": f"item_{i}_0", "nombre": f"Item {i}-0", "descripcion": ""}],
        })
    return {"id": menu_id, "titulo": "Test Menu", "tecla": "m", "apartados": apartados}


def _make_controls(n: int = 2) -> list[dict[str, Any]]:
    return [{"accion": f"Accion {i}", "tecla": f"key_{i}"} for i in range(n)]


def _mock_inp(text: str = "test") -> MagicMock:
    inp = MagicMock()
    inp.get_text.return_value = text
    return inp


def _mock_dd(option: str = "option|Label") -> MagicMock:
    dd = MagicMock()
    dd.selected_option = option
    return dd


def _mock_status(text: str, error: bool) -> None:
    pass


# ── sel_option ─────────────────────────────────────────────

class TestSelOption:
    def test_string_option(self):
        dd = MagicMock()
        dd.selected_option = "value"
        assert sel_option(dd) == "value"

    def test_tuple_option(self):
        dd = MagicMock()
        dd.selected_option = ("value", "Label")
        assert sel_option(dd) == "value"


# ── commit_controles ───────────────────────────────────────

class TestCommitControles:
    def test_none_controles(self):
        commit_controles(None, 0, None)

    def test_none_control_idx(self):
        controls = _make_controls()
        commit_controles(controls, None, None)

    def test_out_of_range_idx(self):
        controls = _make_controls()
        commit_controles(controls, 10, None)

    def test_commit_accion_and_tecla(self):
        controls = _make_controls()
        inps = {"accion": _mock_inp("new_accion"), "tecla": _mock_inp("new_tecla")}
        commit_controles(controls, 0, inps)
        assert controls[0]["accion"] == "new_accion"
        assert controls[0]["tecla"] == "new_tecla"

    def test_no_inps(self):
        controls = _make_controls()
        original = controls[0].copy()
        commit_controles(controls, 0, None)
        assert controls[0] == original


# ── commit_config ──────────────────────────────────────────

class TestCommitConfig:
    def test_none_config_key(self):
        ap = {"tipo": "lista", "items": []}
        commit_config(ap, None, [], None, None, None, None)

    def test_none_item_idx(self):
        ap = {"tipo": "lista", "items": [{"id": "i1"}]}
        commit_config(ap, "items", [{"id": "i1"}], None, None, None, None)

    def test_out_of_range_idx(self):
        ap = {"tipo": "lista", "items": []}
        commit_config(ap, "items", [], 5, None, None, None)

    def test_commit_items(self):
        items = [{"id": "old", "nombre": "Old", "descripcion": ""}]
        ap = {"tipo": "lista", "items": items}
        inps = {
            "id": _mock_inp("new_id"),
            "nombre": _mock_inp("New Name"),
            "descripcion": _mock_inp("Desc"),
        }
        commit_config(ap, "items", items, 0, inps, None, None)
        assert items[0]["id"] == "new_id"
        assert items[0]["nombre"] == "New Name"
        assert items[0]["descripcion"] == "Desc"

    def test_commit_flags(self):
        flags = [{"id": "f1", "nombre": "Flag 1", "default": "0"}]
        ap = {"tipo": "stats_flags", "flags": flags}
        inps = {
            "id": _mock_inp("f2"),
            "nombre": _mock_inp("Flag 2"),
            "default": _mock_inp("1"),
        }
        commit_config(ap, "flags", flags, 0, inps, None, None)
        assert flags[0]["id"] == "f2"
        assert flags[0]["nombre"] == "Flag 2"
        assert flags[0]["default"] == "1"

    def test_commit_stats(self):
        stats = [{"id": "s1", "nombre": "HP", "valor": "100"}]
        ap = {"tipo": "stats", "stats": stats}
        inps = {
            "id": _mock_inp("hp"),
            "nombre": _mock_inp("Health"),
            "valor": _mock_inp("200"),
        }
        commit_config(ap, "stats", stats, 0, inps, None, None)
        assert stats[0]["id"] == "hp"
        assert stats[0]["nombre"] == "Health"
        assert stats[0]["valor"] == "200"


# ── commit_current ─────────────────────────────────────────

class TestCommitCurrent:
    def test_none_selected_id(self):
        commit_current(None, None, None, None, [], None, None, None)

    def test_none_menu(self):
        commit_current(None, "id", None, None, [], None, None, None)

    def test_commit_tecla_titulo(self):
        menu = _make_menu()
        commit_current(menu, "test_menu", None, None, [], None, None, None,
                       tecla_inp=_mock_inp("new_key"),
                       titulo_inp=_mock_inp("New Title"))
        assert menu["tecla"] == "new_key"
        assert menu["titulo"] == "New Title"

    def test_commit_apartado_name(self):
        menu = _make_menu()
        commit_current(menu, "test_menu", 0, None, [], None, None, None,
                       ap_name_inp=_mock_inp("New Name"))
        assert menu["apartados"][0]["nombre"] == "New Name"

    def test_commit_apartado_tipo(self):
        menu = _make_menu()
        commit_current(menu, "test_menu", 0, None, [], None, None, None,
                       ap_tipo_dd=_mock_dd("opciones|Opciones"))
        assert menu["apartados"][0]["tipo"] == "opciones"


# ── persist ────────────────────────────────────────────────

class TestPersist:
    @patch("editor.menu.file_io.validar_menu", return_value=([], []))
    @patch("editor.menu.file_io.set_menu")
    def test_persist_menu_ok(self, mock_set, mock_val):
        menu = _make_menu()
        result = persist(menu, "test_menu", None, _mock_status)
        assert result is True
        mock_set.assert_called_once_with("test_menu", menu)

    @patch("editor.menu.file_io.validar_menu", return_value=(["error msg"], []))
    def test_persist_menu_validation_error(self, mock_val):
        menu = _make_menu()
        result = persist(menu, "test_menu", None, _mock_status)
        assert result is False

    @patch("editor.menu.file_io.validar_menu", return_value=([], []))
    @patch("editor.menu.file_io.set_menu")
    @patch("editor.menu.file_io.validar_controles", return_value=([], []))
    @patch("editor.menu.file_io.set_controles")
    def test_persist_menu_and_controles(self, mock_sc, mock_vc, mock_sm, mock_vm):
        menu = _make_menu()
        controls = _make_controls()
        result = persist(menu, "test_menu", controls, _mock_status)
        assert result is True
        mock_sm.assert_called_once()
        mock_sc.assert_called_once()

    @patch("editor.menu.file_io.validar_menu", return_value=([], []))
    @patch("editor.menu.file_io.set_menu")
    def test_persist_no_menu(self, mock_set, mock_val):
        result = persist(None, None, None, _mock_status)
        assert result is True


# ── persist_controles ──────────────────────────────────────

class TestPersistControles:
    def test_none_controles(self):
        result = persist_controles(None, _mock_status)
        assert result is True

    @patch("editor.menu.file_io.validar_controles", return_value=(["error"], []))
    def test_validation_error(self, mock_val):
        controls = _make_controls()
        result = persist_controles(controls, _mock_status)
        assert result is False

    @patch("editor.menu.file_io.validar_controles", return_value=([], []))
    @patch("editor.menu.file_io.set_controles")
    def test_persist_ok(self, mock_set, mock_val):
        controls = _make_controls()
        result = persist_controles(controls, _mock_status)
        assert result is True
        mock_set.assert_called_once_with(controls)
