from engine.configs import VELOCIDAD_MULT_GRASS, VELOCIDAD_MULT_NORMAL


class SnakeContext:
    def __init__(self, snake):
        self.snake = snake
        self.segmentos_perdidos = []
        self.velocidad_extra = 1.0

    def get_speed_multiplier(self, hierba_alta, terrenos_negados):
        cabeza = self.snake.get_cabeza()
        if not cabeza:
            return 1.0
        cx, cy = cabeza
        for g in hierba_alta:
            if g.activo and g.x == cx and g.y == cy:
                if "hierba_alta" in terrenos_negados:
                    return VELOCIDAD_MULT_NORMAL
                return VELOCIDAD_MULT_GRASS
        return VELOCIDAD_MULT_NORMAL * self.velocidad_extra
