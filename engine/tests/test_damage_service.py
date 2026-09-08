from engine.services.damage_service import DamageService


class FakeEventBus:
    def __init__(self):
        self.published = []

    def publicar(self, evento):
        self.published.append(evento)


class FakeEstado:
    def __init__(self):
        self.game_over = False
        self.death_cause = None
        self.event_bus = FakeEventBus()


class FakeSnake:
    def __init__(self, length=3):
        self._body = [(120, 540), (100, 540), (80, 540)]
        self._length = length

    @property
    def body(self):
        return self._body

    def get_cabeza(self):
        return self._body[0] if self._body else None

    def get_longitud(self):
        return self._length


class TestDamageService:
    def setup_method(self):
        self.svc = DamageService()

    def test_roll_enemy_damage_in_range(self):
        for _ in range(50):
            dmg = self.svc.roll_enemy_damage()
            assert 2 <= dmg <= 4

    def test_roll_projectile_damage_in_range(self):
        for _ in range(50):
            dmg = self.svc.roll_projectile_damage()
            assert 1 <= dmg <= 2

    def test_roll_boss_ram_damage_in_range(self):
        for _ in range(50):
            dmg = self.svc.roll_boss_ram_damage()
            assert 3 <= dmg <= 6

    def test_roll_boss_projectile_damage_in_range(self):
        for _ in range(50):
            dmg = self.svc.roll_boss_projectile_damage()
            assert 2 <= dmg <= 4

    def test_get_enemy_damage_range(self):
        lo, hi = self.svc.get_enemy_damage()
        assert lo == 2
        assert hi == 4

    def test_is_lethal_length_true(self):
        assert self.svc.is_lethal_length(3) is True

    def test_is_lethal_length_false(self):
        assert self.svc.is_lethal_length(10) is False

    def test_apply_damage_lethal(self):
        snake = FakeSnake(length=3)
        estado = FakeEstado()
        result = self.svc.apply_damage(snake, 2, estado, fuente="test")
        assert result is True
        assert estado.game_over is True

    def test_apply_damage_normal(self):
        snake = FakeSnake(length=10)
        estado = FakeEstado()
        result = self.svc.apply_damage(snake, 2, estado, fuente="test")
        assert result is False

