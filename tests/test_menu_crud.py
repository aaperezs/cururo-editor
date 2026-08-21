"""Tests unitarios para editor.menu_crud — CRUD menus, apartados, config, controles."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch, MagicMock

import pytest

from editor.menu_crud import (
    create_new_menu,
    clone_menu,
    delete_menu_by_id,
    rename_menu_by_id,
    move_apartado,
    add_apartado,
    delete_apartado,
    add_config_item,
    delete_config_item,
    duplicate_config_item,
    add_control,
    delete_control,
    duplicate_control,
)


# ── Fake data ──────────────────────────────────────────────

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


# ── Menu CRUD ──────────────────────────────────────────────

class TestMenuCRUD:
    @patch("editor.menu_crud.menu_exists", return_value=False)
    @patch("editor.menu_crud.create_menu")
    def test_create_new_menu(self, mock_create, mock_exists):
        mid = create_new_menu()
        assert mid == "menu_nuevo"
        mock_create.assert_called_once_with("menu_nuevo", plantilla="vacio")

    @patch("editor.menu_crud.menu_exists", side_effect=[True, False])
    @patch("editor.menu_crud.create_menu")
    def test_create_new_menu_with_conflict(self, mock_create, mock_exists):
        mid = create_new_menu()
        assert mid == "menu_nuevo_1"
        mock_create.assert_called_once_with("menu_nuevo_1", plantilla="vacio")

    @patch("editor.menu_crud.menu_exists", return_value=False)
    @patch("editor.menu_crud.create_menu")
    def test_create_new_menu_with_template(self, mock_create, mock_exists):
        mid = create_new_menu(template="default")
        assert mid == "menu_nuevo"
        mock_create.assert_called_once_with("menu_nuevo", plantilla="default")

    @patch("editor.menu_crud.menu_exists", return_value=False)
    @patch("editor.menu_crud.set_menu")
    @patch("editor.menu_crud.get_menu", return_value={"id": "src", "titulo": "Src"})
    def test_clone_menu(self, mock_get, mock_set, mock_exists):
        mid = clone_menu("src")
        assert mid == "src_copia"
        mock_set.assert_called_once_with("src_copia", {"id": "src", "titulo": "Src"})

    @patch("editor.menu_crud.menu_exists", side_effect=[True, False])
    @patch("editor.menu_crud.set_menu")
    @patch("editor.menu_crud.get_menu", return_value={"id": "src"})
    def test_clone_menu_with_conflict(self, mock_get, mock_set, mock_exists):
        mid = clone_menu("src")
        assert mid == "src_copia_1"

    @patch("editor.menu_crud.get_menu", return_value=None)
    def test_clone_menu_nonexistent(self, mock_get):
        assert clone_menu("nope") is None

    @patch("editor.menu_crud.delete_menu")
    def test_delete_menu_by_id(self, mock_delete):
        delete_menu_by_id("m1")
        mock_delete.assert_called_once_with("m1")

    @patch("editor.menu_crud.rename_menu", return_value=True)
    @patch("editor.menu_crud.menu_exists", return_value=False)
    def test_rename_menu_by_id(self, mock_exists, mock_rename):
        assert rename_menu_by_id("old", "new") is True
        mock_rename.assert_called_once_with("old", "new")

    @patch("editor.menu_crud.menu_exists", return_value=True)
    def test_rename_menu_by_id_conflict(self, mock_exists):
        assert rename_menu_by_id("old", "existing") is False


# ── Apartado CRUD ──────────────────────────────────────────

class TestApartadoCRUD:
    def test_move_apartado_up(self):
        menu = _make_menu(n_apartados=3)
        new_idx = move_apartado(menu, 2, -1)
        assert new_idx == 1
        assert menu["apartados"][1]["id"] == "ap_2"
        assert menu["apartados"][2]["id"] == "ap_1"

    def test_move_apartado_down(self):
        menu = _make_menu(n_apartados=3)
        new_idx = move_apartado(menu, 0, 1)
        assert new_idx == 1
        assert menu["apartados"][0]["id"] == "ap_1"
        assert menu["apartados"][1]["id"] == "ap_0"

    def test_move_apartado_out_of_bounds(self):
        menu = _make_menu(n_apartados=2)
        assert move_apartado(menu, 0, -1) is None
        assert move_apartado(menu, 1, 1) is None

    def test_add_apartado(self):
        menu = _make_menu(n_apartados=1)
        idx = add_apartado(menu)
        assert idx == 1
        assert len(menu["apartados"]) == 2
        assert menu["apartados"][1]["tipo"] == "lista"

    def test_delete_apartado(self):
        menu = _make_menu(n_apartados=3)
        new_idx = delete_apartado(menu, 1)
        assert new_idx == 0
        assert len(menu["apartados"]) == 2

    def test_delete_apartado_last(self):
        menu = _make_menu(n_apartados=1)
        new_idx = delete_apartado(menu, 0)
        assert new_idx is None
        assert len(menu["apartados"]) == 0


# ── Config Item CRUD ───────────────────────────────────────

class TestConfigItemCRUD:
    def test_add_item(self):
        items: list[dict[str, Any]] = []
        idx = add_config_item(items, "items")
        assert idx == 0
        assert items[0]["id"] == "item_1"
        assert items[0]["nombre"] == "Item 1"

    def test_add_flag(self):
        items: list[dict[str, Any]] = []
        idx = add_config_item(items, "flags")
        assert idx == 0
        assert items[0]["id"] == "flag_1"
        assert items[0]["default"] == "0"

    def test_add_stat(self):
        items: list[dict[str, Any]] = []
        idx = add_config_item(items, "stats")
        assert idx == 0
        assert items[0]["id"] == "stat_1"
        assert items[0]["valor"] == ""

    def test_add_item_increment(self):
        items: list[dict[str, Any]] = [{"id": "item_1"}]
        idx = add_config_item(items, "items")
        assert idx == 1
        assert items[1]["id"] == "item_2"

    def test_delete_config_item(self):
        items = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
        new_idx = delete_config_item(items, 1)
        assert new_idx == 0
        assert len(items) == 2
        assert items[0]["id"] == "a"

    def test_delete_config_item_last(self):
        items = [{"id": "a"}]
        new_idx = delete_config_item(items, 0)
        assert new_idx is None
        assert len(items) == 0

    def test_duplicate_config_item(self):
        items = [{"id": "orig", "nombre": "Test"}]
        new_idx = duplicate_config_item(items, 0)
        assert new_idx == 1
        assert len(items) == 2
        assert items[1]["id"] == "orig_copia"
        assert items[1]["nombre"] == "Test"

    def test_duplicate_config_item_out_of_bounds(self):
        items = [{"id": "a"}]
        assert duplicate_config_item(items, 5) is None

    def test_duplicate_preserves_reference(self):
        items = [{"id": "a", "nested": [1, 2]}]
        duplicate_config_item(items, 0)
        items[0]["nested"].append(3)
        assert items[1]["nested"] == [1, 2]  # independent copy


# ── Control CRUD ───────────────────────────────────────────

class TestControlCRUD:
    def test_add_control(self):
        controls: list[dict[str, Any]] = []
        idx = add_control(controls)
        assert idx == 0
        assert controls[0]["accion"] == "Acci\u00f3n 1"
        assert controls[0]["tecla"] == ""

    def test_add_control_increment(self):
        controls = [{"accion": "A1"}]
        idx = add_control(controls)
        assert idx == 1
        assert controls[1]["accion"] == "Acci\u00f3n 2"

    def test_delete_control(self):
        controls = _make_controls(3)
        new_idx = delete_control(controls, 1)
        assert new_idx == 0
        assert len(controls) == 2

    def test_delete_control_last(self):
        controls = _make_controls(1)
        new_idx = delete_control(controls, 0)
        assert new_idx is None
        assert len(controls) == 0

    def test_duplicate_control(self):
        controls = _make_controls(1)
        new_idx = duplicate_control(controls, 0)
        assert new_idx == 1
        assert len(controls) == 2
        assert "_copia" in controls[1]["accion"]

    def test_duplicate_control_out_of_bounds(self):
        controls = _make_controls(1)
        assert duplicate_control(controls, 5) is None

    def test_duplicate_preserves_reference(self):
        controls = [{"accion": "A", "tecla": "k"}]
        duplicate_control(controls, 0)
        controls[0]["tecla"] = "changed"
        assert controls[1]["tecla"] == "k"  # independent copy
