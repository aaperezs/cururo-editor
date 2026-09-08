"""Tests del ActionRegistry híbrido (Sprint 3)."""

import pytest

from engine.systems.action_registry import GameAction, get_action, register_action, registered_ids
from engine.systems.event_context import EventContext
from engine.systems.stack_manager import StackManager


class FakeAudio:
    def __init__(self):
        self.calls = []
        self.bgm = None

    def play_sfx(self, asset_id):
        self.calls.append(("sfx", asset_id))

    def play_bgm(self, asset_id, fade_ms=0):
        self.calls.append(("bgm", asset_id, fade_ms))

    def stop_bgm(self, fade_ms=0):
        self.calls.append(("stop", fade_ms))

    def set_bgm_volume(self, v):
        self.calls.append(("bgm_vol", v))


class FakeFlags:
    def __init__(self):
        self.data = {}

    def set(self, k, v):
        self.data[k] = v

    def add(self, k, n):
        self.data[k] = self.data.get(k, 0) + n


class FakeInventario:
    def __init__(self):
        self.items = {}

    def agregar_item(self, item, cantidad):
        self.items[item] = self.items.get(item, 0) + cantidad

    def remover_item(self, item, cantidad):
        if item in self.items:
            self.items[item] -= cantidad


class FakeEstado:
    def __init__(self):
        self.audio = FakeAudio()
        self.flags = FakeFlags()
        self.inventario = FakeInventario()
        self.mensaje_temporal = ""
        self.tiempo_mensaje = 0
        self.snake = None
        self.fondo_activo = None


def _sm():
    return StackManager(FakeEstado())


class TestRegistry:
    def test_acciones_migradas_registradas(self):
        migradas = {"show_message", "play_bgm", "stop_bgm", "play_sfx",
                    "set_flag", "add_flag", "give_item", "remove_item"}
        for aid in migradas:
            assert get_action(aid) is not None, f"{aid} debería estar registrada"

    def test_registry_primero_ejecuta_accion(self):
        sm = _sm()
        resultado = sm._ejecutar_accion("play_sfx", {"asset_id": "golpe"}, 0, 0, 0)
        assert resultado is False
        assert ("sfx", "golpe") in sm.estado.audio.calls

    def test_fallback_legacy_para_no_registrada(self):
        sm = _sm()
        # cambiar_fondo no está migrada -> pasa por elif legacy (simple, sin editor)
        sm._ejecutar_accion("cambiar_fondo", {"sprite_id": "bosque"}, 0, 0, 0)
        assert sm.estado.fondo_activo == "bosque"

    def test_show_message_registrada(self):
        sm = _sm()
        sm._ejecutar_accion("show_message", {"mensaje": "Hola"}, 0, 0, 0)
        assert sm.estado.mensaje_temporal == "Hola"
        assert sm.estado.tiempo_mensaje == 90

    def test_give_remove_item_registradas(self):
        sm = _sm()
        sm._ejecutar_accion("give_item", {"item": "pocion", "cantidad": 2}, 0, 0, 0)
        assert sm.estado.inventario.items.get("pocion") == 2
        sm._ejecutar_accion("remove_item", {"item": "pocion", "cantidad": 1}, 0, 0, 0)
        assert sm.estado.inventario.items.get("pocion") == 1

    def test_set_add_flag_registradas(self):
        sm = _sm()
        sm._ejecutar_accion("set_flag", {"flag": "visto", "valor": True}, 0, 0, 0)
        assert sm.estado.flags.data["visto"] is True
        sm._ejecutar_accion("add_flag", {"flag": "contador", "cantidad": 3}, 0, 0, 0)
        assert sm.estado.flags.data["contador"] == 3


class TestRegistroPropio:
    def test_register_y_get_action(self):
        @register_action("_test_custom_action")
        class Custom(GameAction):
            def execute(self, ctx, params):
                return "ok"

        assert get_action("_test_custom_action") is Custom
        assert "_test_custom_action" in registered_ids()

    def test_get_action_inexistente(self):
        assert get_action("_nada_por_aqui_") is None

