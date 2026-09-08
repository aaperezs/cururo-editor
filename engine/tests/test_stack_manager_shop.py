"""Tests del adaptador de clave legacy "shop" -> "shop_id" en StackManager."""

import pytest

from engine.systems.stack_manager import StackManager


class FakeDialogo:
    def __init__(self, choices):
        self.options = [{"text": "pregunta", "choices": choices}]


class FakeEstado:
    def __init__(self, choices):
        self.dialogo = FakeDialogo(choices)
        self.opcion_pregunta = ""
        self.opciones = []


def _sm(choices):
    estado = FakeEstado(choices)
    sm = StackManager(estado)
    return sm, estado


class TestAdaptadorShopLegacy:
    def test_convierte_shop_a_shop_id(self):
        sm, estado = _sm([
            {"text": "Tienda", "action": "open_shop", "shop": "fenrir_shop"},
            {"text": "Salir", "action": "close_dialog"},
        ])
        sm._mostrar_opciones_plano(estado)
        tienda = [o for o in estado.opciones if o["texto"] == "Tienda"][0]
        params = tienda["acciones"][0]["params"]
        assert params["shop_id"] == "fenrir_shop"
        assert "shop" not in params

    def test_respeta_shop_id_existente(self):
        sm, estado = _sm([
            {"text": "Tienda", "action": "open_shop", "shop_id": "otra"},
        ])
        sm._mostrar_opciones_plano(estado)
        params = estado.opciones[0]["acciones"][0]["params"]
        assert params["shop_id"] == "otra"
        assert "shop" not in params

    def test_ignora_choices_sin_shop(self):
        sm, estado = _sm([
            {"text": "Hablar", "action": "start_dialogue", "dialogo_id": "x/y"},
        ])
        sm._mostrar_opciones_plano(estado)
        params = estado.opciones[0]["acciones"][0]["params"]
        assert params == {"dialogo_id": "x/y"}

