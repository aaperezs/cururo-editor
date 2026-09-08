"""Tests del evaluador compuesto de condiciones (Sprint 4)."""

from engine.systems.conditions import evaluate_condition_node
from engine.systems.event_context import EventContext
from engine.systems.stack_manager import StackManager
from engine.systems.scene_player import evaluate_condition as evaluate_scene_condition


def _leaf_estado(ctx):
    def leaf(cond):
        ct = cond.get("tipo", "")
        params = cond.get("params", {})
        if ct == "flag":
            return bool(ctx.flags.get(params.get("flag", "")))
        if ct == "item_count":
            return ctx.inventario.cantidad(params.get("item", "")) >= int(params.get("valor", 1))
        if ct == "ability":
            return ctx.habilidades.tiene_habilidad(params.get("ability", ""))
        return True
    return leaf


class FakeFlags(dict):
    pass


class FakeInventario:
    def __init__(self):
        self.items = {"pocion": 3}

    def cantidad(self, item):
        return self.items.get(item, 0)


class FakeHabilidades:
    def __init__(self):
        self._tiene = {"manto_oscuridad"}

    def tiene_habilidad(self, hid):
        return hid in self._tiene


class FakeEstado:
    def __init__(self):
        self.flags = FakeFlags({"visto": True})
        self.inventario = FakeInventario()
        self.habilidades = FakeHabilidades()
        self.snake = None


def _ctx():
    return EventContext(state=FakeEstado())


class TestEvaluadorCompuesto:
    def test_lista_plana_es_and(self):
        ctx = _ctx()
        leaf = _leaf_estado(ctx)
        conds = [
            {"tipo": "flag", "params": {"flag": "visto"}},
            {"tipo": "item_count", "params": {"item": "pocion", "valor": 2}},
        ]
        assert evaluate_condition_node(conds, leaf)

    def test_lista_falla_si_una_falla(self):
        ctx = _ctx()
        leaf = _leaf_estado(ctx)
        conds = [
            {"tipo": "flag", "params": {"flag": "visto"}},
            {"tipo": "item_count", "params": {"item": "pocion", "valor": 99}},
        ]
        assert not evaluate_condition_node(conds, leaf)

    def test_and_compuesto(self):
        ctx = _ctx()
        leaf = _leaf_estado(ctx)
        node = {
            "operator": "AND",
            "children": [
                {"tipo": "flag", "params": {"flag": "visto"}},
                {"tipo": "ability", "params": {"ability": "manto_oscuridad"}},
            ],
        }
        assert evaluate_condition_node(node, leaf)

    def test_or_compuesto(self):
        ctx = _ctx()
        leaf = _leaf_estado(ctx)
        node = {
            "operator": "OR",
            "children": [
                {"tipo": "flag", "params": {"flag": "no_existe"}},
                {"tipo": "ability", "params": {"ability": "manto_oscuridad"}},
            ],
        }
        assert evaluate_condition_node(node, leaf)
        node_falso = {
            "operator": "OR",
            "children": [
                {"tipo": "flag", "params": {"flag": "no_existe"}},
                {"tipo": "ability", "params": {"ability": "golpe_roca"}},
            ],
        }
        assert not evaluate_condition_node(node_falso, leaf)

    def test_and_anidado(self):
        ctx = _ctx()
        leaf = _leaf_estado(ctx)
        node = {
            "operator": "AND",
            "children": [
                {"tipo": "flag", "params": {"flag": "visto"}},
                {
                    "operator": "OR",
                    "children": [
                        {"tipo": "item_count", "params": {"item": "pocion", "valor": 1}},
                        {"tipo": "ability", "params": {"ability": "golpe_roca"}},
                    ],
                },
            ],
        }
        assert evaluate_condition_node(node, leaf)

    def test_hoja_simple(self):
        ctx = _ctx()
        leaf = _leaf_estado(ctx)
        assert evaluate_condition_node({"tipo": "flag", "params": {"flag": "visto"}}, leaf)
        assert not evaluate_condition_node({"tipo": "flag", "params": {"flag": "nope"}}, leaf)

    def test_vacio_y_none(self):
        ctx = _ctx()
        leaf = _leaf_estado(ctx)
        assert evaluate_condition_node([], leaf)
        assert evaluate_condition_node({}, leaf)
        assert evaluate_condition_node(None, leaf)


class TestIntegracionStackManager:
    def _sm(self):
        return StackManager(FakeEstado())

    def test_lista_plana_sigue_funcionando(self):
        sm = self._sm()
        assert sm._check_conditions(
            [{"tipo": "flag", "params": {"flag": "visto", "operador": "es_verdadero"}}]
        )
        assert not sm._check_conditions(
            [{"tipo": "flag", "params": {"flag": "nope", "operador": "es_verdadero"}}]
        )

    def test_nodo_compuesto_en_stack_manager(self):
        sm = self._sm()
        node = {
            "operator": "OR",
            "children": [
                {"tipo": "flag", "params": {"flag": "no_existe", "operador": "es_verdadero"}},
                {"tipo": "item_count", "params": {"item": "pocion", "operador": ">=", "valor": 2}},
            ],
        }
        assert sm._check_conditions(node)


class TestScenePlayer:
    class FakeFlags:
        def __init__(self, data):
            self._data = data

        def get(self, k, d=None):
            return self._data.get(k, d)

    def test_hoja_escena(self):
        fm = self.FakeFlags({"capitulo": 2})
        assert evaluate_scene_condition({"flag": "capitulo", "operador": "==", "valor": "2"}, fm)
        assert not evaluate_scene_condition({"flag": "capitulo", "operador": ">", "valor": "5"}, fm)

    def test_escena_lista_and(self):
        fm = self.FakeFlags({"a": True, "b": True})
        conds = [
            {"flag": "a", "operador": "==", "valor": "true"},
            {"flag": "b", "operador": "==", "valor": "true"},
        ]
        assert evaluate_scene_condition(conds, fm)

    def test_escena_or(self):
        fm = self.FakeFlags({"a": True})
        node = {
            "operator": "OR",
            "children": [
                {"flag": "x", "operador": "==", "valor": "true"},
                {"flag": "a", "operador": "==", "valor": "true"},
            ],
        }
        assert evaluate_scene_condition(node, fm)

