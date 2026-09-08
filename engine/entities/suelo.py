# entities/suelo.py

class Suelo:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.ancho = 20
        self.alto = 20
        self.visible = True
        self.activo = True
        self.solid = False
        self.no_food_spawn = False
        self.z = 0
        self.properties = {}

    def dibujar(self, pantalla, offset_x=0, offset_y=0):
        pass

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.ancho, self.alto)


class Pasto(Suelo):
    def __init__(self, x, y):
        super().__init__(x, y)


class PastoEsteril(Suelo):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.no_food_spawn = True
