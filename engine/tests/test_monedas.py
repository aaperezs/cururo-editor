import json

from engine.repositories.repositorio_monedas import RepositorioMonedas
from engine.runtime.monedas import MonedasManager
from engine.systems.stack_manager import StackManager

DEFINICIONES = [
    {"id": "gemas", "label": "Gemas", "valor_inicial": 0, "icono": "\u25c6", "color": [0, 150, 255], "principal": False},
    {"id": "escamas", "label": "Escamas", "valor_inicial": 0, "icono": "\u25c6", "color": [210, 185, 100], "principal": True},
]


class FakeSnake:
    def __init__(self):
        self.escamas = 5

    def get_escamas(self):
        return self.escamas

    def crecer(self, n):
        self.escamas += n

    def perder_escamas(self, n):
        self.escamas = max(0, self.escamas - n)


class FakeEstado:
    def __init__(self):
        self.monedas = MonedasManager(DEFINICIONES)
        self.snake = FakeSnake()


class TestRepositorioMonedas:
    def setup_method(self):
        self.repo = RepositorioMonedas()

    def test_carga_definicion_escamas(self):
        defs = self.repo.get_definiciones()
        assert any(d.get("id") == "escamas" for d in defs)

    def test_get_por_id(self):
        escamas = self.repo.get_por_id("escamas")
        assert escamas is not None
        assert escamas["label"] == "Escamas"
        assert escamas["principal"] is True


class TestMonedasManager:
    def setup_method(self):
        self.m = MonedasManager(DEFINICIONES)

    def test_valores_iniciales(self):
        assert self.m.get("gemas") == 0
        assert self.m.get("escamas") == 0

    def test_dar(self):
        self.m.dar("gemas", 3)
        assert self.m.get("gemas") == 3

    def test_quitar_sin_pasar_de_cero(self):
        self.m.dar("gemas", 2)
        self.m.quitar("gemas", 5)
        assert self.m.get("gemas") == 0

    def test_principal(self):
        assert self.m.principal() == "escamas"

    def test_ids(self):
        assert set(self.m.ids()) == {"gemas", "escamas"}


class TestStackManagerMonedas:
    def setup_method(self):
        self.estado = FakeEstado()
        self.sm = StackManager(self.estado)

    def _cond(self, tipo, **params):
        return self.sm._check_conditions([{"tipo": tipo, "params": params}])

    def test_has_moneda_true(self):
        self.estado.monedas.dar("gemas", 5)
        assert self._cond("has_moneda", moneda="gemas", operador=">=", valor=3)

    def test_has_moneda_false(self):
        self.estado.monedas.dar("gemas", 1)
        assert not self._cond("has_moneda", moneda="gemas", operador=">=", valor=3)

    def test_has_moneda_desconocida_false(self):
        assert not self._cond("has_moneda", moneda="nope", operador=">=", valor=1)

    def test_has_moneda_escamas_usa_snake(self):
        self.estado.snake.escamas = 5
        assert self._cond("has_moneda", moneda="escamas", operador=">=", valor=5)

    def test_give_moneda(self):
        self.sm._ejecutar_acciones(
            [{"tipo": "give_moneda", "params": {"moneda": "gemas", "cantidad": 3}}], 0, 0)
        assert self.estado.monedas.get("gemas") == 3

    def test_remove_moneda(self):
        self.estado.monedas.dar("gemas", 3)
        self.sm._ejecutar_acciones(
            [{"tipo": "remove_moneda", "params": {"moneda": "gemas", "cantidad": 5}}], 0, 0)
        assert self.estado.monedas.get("gemas") == 0

    def test_give_moneda_escamas_crece_snake(self):
        self.sm._ejecutar_acciones(
            [{"tipo": "give_moneda", "params": {"moneda": "escamas", "cantidad": 3}}], 0, 0)
        assert self.estado.snake.escamas == 8

    def test_remove_moneda_escamas_adelgaza_snake(self):
        self.estado.snake.escamas = 5
        self.sm._ejecutar_acciones(
            [{"tipo": "remove_moneda", "params": {"moneda": "escamas", "cantidad": 2}}], 0, 0)
        assert self.estado.snake.escamas == 3


class TestMigracionLegacy:
    def test_condicion_y_accion_escamas_se_migran_al_cargar(self, tmp_path, monkeypatch):
        import orm.systems.stack_manager as sm_module

        monkeypatch.setattr(sm_module, "STACKS_DIR", str(tmp_path))
        data = {
            "stacks": [{
                "pos": [0, 0], "z": 0,
                "eventos": [{
                    "id": "ev1", "trigger": "contact", "once": False,
                    "condiciones": [{"tipo": "escamas", "params": {"operador": ">=", "valor": 3}}],
                    "acciones": [{"tipo": "remove_escamas", "params": {"cantidad": 2}}],
                }],
            }]
        }
        (tmp_path / "testnivel_stacks.json").write_text(json.dumps(data), encoding="utf-8")
        sm = sm_module.StackManager(FakeEstado())
        sm.load_stacks("testnivel")
        ev = sm._stacks[(0, 0, 0)]["eventos"][0]
        assert ev["condiciones"][0]["tipo"] == "has_moneda"
        assert ev["condiciones"][0]["params"]["moneda"] == "escamas"
        assert ev["acciones"][0]["tipo"] == "remove_moneda"
        assert ev["acciones"][0]["params"]["moneda"] == "escamas"

    def test_stack_sin_eventos_no_rompe_migracion(self, tmp_path, monkeypatch):
        import orm.systems.stack_manager as sm_module

        monkeypatch.setattr(sm_module, "STACKS_DIR", str(tmp_path))
        data = {
            "stacks": [
                {"pos": [0, 0], "z": 0, "eventos": []},
                {"pos": [1, 0], "z": 0, "eventos": [{
                    "id": "ev1", "trigger": "contact", "once": False,
                    "condiciones": [{"tipo": "escamas", "params": {"operador": ">=", "valor": 3}}],
                    "acciones": [],
                }]},
            ]
        }
        (tmp_path / "testnivel_stacks.json").write_text(json.dumps(data), encoding="utf-8")
        sm = sm_module.StackManager(FakeEstado())
        sm.load_stacks("testnivel")
        # el stack sin eventos se filtra al final (no rompe la migración)
        assert (0, 0, 0) not in sm._stacks
        ev = sm._stacks[(1, 0, 0)]["eventos"][0]
        assert ev["condiciones"][0]["tipo"] == "has_moneda"

    def test_has_escamas_legacy_converge_a_has_moneda(self, tmp_path, monkeypatch):
        import orm.systems.stack_manager as sm_module

        monkeypatch.setattr(sm_module, "STACKS_DIR", str(tmp_path))
        data = {
            "stacks": [{
                "pos": [0, 0], "z": 0,
                "eventos": [{
                    "id": "ev1", "trigger": "contact", "once": False,
                    "condiciones": [{"tipo": "has_escamas", "params": {"min": 3}}],
                    "acciones": [],
                }],
            }]
        }
        (tmp_path / "testnivel_stacks.json").write_text(json.dumps(data), encoding="utf-8")
        sm = sm_module.StackManager(FakeEstado())
        sm.load_stacks("testnivel")
        cond = sm._stacks[(0, 0, 0)]["eventos"][0]["condiciones"][0]
        assert cond["tipo"] == "has_moneda"
        assert cond["params"]["moneda"] == "escamas"
        assert cond["params"]["operador"] == ">="
        assert cond["params"]["valor"] == 3
