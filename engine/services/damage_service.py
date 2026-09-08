import random

from engine.services.config_provider import config_provider


class DamageService:
    """Domain service: calculates damage based on config, equipment, and attack type."""

    def __init__(self):
        self._gp = config_provider.get_gameplay

    def get_enemy_damage(self):
        return (
            self._gp("combat", "damage_min", default=2),
            self._gp("combat", "damage_max", default=4),
        )

    def get_projectile_damage(self):
        return (
            self._gp("combat", "manto_damage_min", default=1),
            self._gp("combat", "manto_damage_max", default=2),
        )

    def get_boss_ram_damage(self):
        return (
            self._gp("combat", "boss_ram_damage_min", default=3),
            self._gp("combat", "boss_ram_damage_max", default=6),
        )

    def get_boss_projectile_damage(self):
        return (
            self._gp("combat", "damage_min", default=2),
            self._gp("combat", "damage_max", default=4),
        )

    def get_invincibility_frames(self):
        return self._gp("combat", "invincibility_frames", default=30)

    def get_min_length(self):
        return self._gp("combat", "min_length", default=3)

    def roll_enemy_damage(self):
        lo, hi = self.get_enemy_damage()
        return random.randint(lo, hi)

    def roll_projectile_damage(self):
        lo, hi = self.get_projectile_damage()
        return random.randint(lo, hi)

    def roll_boss_ram_damage(self):
        lo, hi = self.get_boss_ram_damage()
        return random.randint(lo, hi)

    def roll_boss_projectile_damage(self):
        lo, hi = self.get_boss_projectile_damage()
        return random.randint(lo, hi)

    def is_lethal_length(self, snake_length):
        return snake_length <= self.get_min_length()

    def apply_damage(self, snake, cantidad, estado, fuente="", on_perder_segmentos=None):
        """Aplica daño a la serpiente. Retorna True si es game over."""
        from engine.systems.event_bus import EventoDamageInfligido

        if self.is_lethal_length(snake.get_longitud()):
            estado.game_over = True
            estado.death_cause = f"{fuente} con {snake.get_longitud()} segs"
            estado.event_bus.publicar(EventoDamageInfligido(
                cantidad=cantidad, fuente=fuente,
                posicion=tuple(snake.body[0]) if snake.body else (0, 0),
                letal=True
            ))
            return True

        if on_perder_segmentos:
            if on_perder_segmentos(cantidad, estado):
                return True

        estado.event_bus.publicar(EventoDamageInfligido(
            cantidad=cantidad, fuente=fuente,
            posicion=tuple(snake.body[0]) if snake.body else (0, 0),
            letal=False
        ))
        return False


damage_service = DamageService()
