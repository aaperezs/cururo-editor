"""Tests de EventContext y su integración con StackManager._check_conditions."""

import pytest

from engine.systems.event_context import EventContext
from engine.systems.stack_manager import StackManager


class FakeInventario:
    def __init__(self, items=None):
        self.items = items or {}

    def cantidad(self, item):
        return self.items.get(item, 0)


class FakeFlags(dict):
    pass


class FakeHabilidades:
    def __init__(self, tiene=None, equipada=None, pp=0):
        self._tiene = set(tiene or [])
        self.habilidad_equipada = equipada
        self._pp = pp

    def tiene_habilidad(self, hid):
        return hid in self._tiene

    def get_pp_actual(self):
        return self._pp


class FakeSnake:
    def get_escamas(self):
        return 10


class FakeEstado:
    def __init__(self):
        self.inventario = FakeInventario({"pocion": 3})
        self.flags = FakeFlags({"visto": True, "nivel": 5})
        self.habilidades = FakeHabilidades({"manto_oscuridad"}, "manto_oscuridad", 20)
        self.monedas = None
        self.snake = FakeSnake()
        self.estado_global = self


class TestEventContextAcceso:
    def test_sub_estados_duck(self):
        st = FakeEstado()
        ctx = EventContext(state=st)
        assert ctx.inventario is st.inventario
        assert ctx.flags is st.flags
        assert ctx.habilidades is st.habilidades
        assert ctx.snake is st.snake
        assert ctx.monedas is None

    def test_get_flags_y_custom(self):
        st = FakeEstado()
        ctx = EventContext(state=st, custom={"damage": 7})
        assert ctx.get("visto") is True
        assert ctx.get("no_existe", 99) == 99
        assert ctx.get("damage") == 7

    def test_get_sin_state(self):
        ctx = EventContext()
        assert ctx.get("cualquiera", "x") == "x"
        assert ctx.inventario is None


class TestStackManagerConCtx:
    def _sm(self):
        return StackManager(FakeEstado())

    def test_condiciones_por_ctx_explicito(self):
        sm = self._sm()
        ctx = EventContext(state=FakeEstado())
        assert sm._check_conditions(
            [{"tipo": "item_count", "params": {"item": "pocion", "operador": ">=", "valor": 2}}],
            ctx=ctx,
        )
        assert not sm._check_conditions(
            [{"tipo": "item_count", "params": {"item": "pocion", "operador": ">=", "valor": 99}}],
            ctx=ctx,
        )

    def test_ctx_autoconstruido_sin_firma_antigua(self):
        sm = self._sm()
        # Sin ctx: usa self.estado internamente (compatibilidad)
        assert sm._check_conditions(
            [{"tipo": "flag", "params": {"flag": "visto", "operador": "es_verdadero"}}]
        )

    def test_custom_en_ctx_para_damage(self):
        sm = self._sm()
        ctx = EventContext(state=FakeEstado(), custom={"damage": 12})
        assert sm._check_conditions(
            [{"tipo": "damage", "params": {"operador": ">=", "valor": 10}}], ctx=ctx
        )
        assert not sm._check_conditions(
            [{"tipo": "damage", "params": {"operador": ">=", "valor": 50}}], ctx=ctx
        )

    def test_custom_via_extra_compat(self):
        sm = self._sm()
        assert sm._check_conditions(
            [{"tipo": "damage", "params": {"operador": ">", "valor": 5}}],
            extra={"damage": 9},
        )

    def test_ability_por_ctx(self):
        sm = self._sm()
        ctx = EventContext(state=FakeEstado())
        assert sm._check_conditions(
            [{"tipo": "ability", "params": {"ability": "manto_oscuridad", "operador": "tiene"}}],
            ctx=ctx,
        )
        assert not sm._check_conditions(
            [{"tipo": "ability", "params": {"ability": "golpe_roca", "operador": "tiene"}}],
            ctx=ctx,
        )

