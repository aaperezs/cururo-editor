from engine.domain.snake_context import SnakeContext
from engine.domain.world_state import WorldState


class FakeSnake:
    def __init__(self):
        self.body = [(120, 540), (100, 540), (80, 540)]
        self.direccion = "DERECHA"
        self.vivo = True
        self.escamas = 5
        self.velocidad_extra = 0

    def get_cabeza(self):
        return self.body[0] if self.body else None

    def get_longitud(self):
        return len(self.body)

    def get_escamas(self):
        return self.escamas

    def tiene_deuda(self):
        return False


class TestSnakeContext:
    def setup_method(self):
        self.snake = FakeSnake()
        self.ctx = SnakeContext(self.snake)

    def test_get_speed_multiplier_default(self):
        mult = self.ctx.get_speed_multiplier([], [])
        assert mult == 1.0

    def test_get_speed_multiplier_with_extra(self):
        self.ctx.velocidad_extra = 1.5
        mult = self.ctx.get_speed_multiplier([], [])
        assert mult == 1.5

    def test_snake_reference(self):
        assert self.ctx.snake is self.snake

    def test_segmentos_perdidos(self):
        assert self.ctx.segmentos_perdidos == []

    def test_velocidad_extra(self):
        assert self.ctx.velocidad_extra == 1.0


class TestWorldState:
    def setup_method(self):
        self.ws = WorldState()

    def test_tile_overrides_empty(self):
        assert self.ws.tile_overrides == {}

    def test_replace_tile_sprite(self):
        self.ws.grid = {(0, 0): "pasto"}
        self.ws.replace_tile_sprite(0, 0, "pared")
        assert self.ws.tile_overrides[(0, 0, 0)] == "pared"

    def test_grid_initially_empty(self):
        assert self.ws.grid == {}

    def test_has_arena_boss(self):
        assert hasattr(self.ws, "arena_boss")

    def test_boss_initial(self):
        assert self.ws.boss is None

