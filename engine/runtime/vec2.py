from dataclasses import dataclass


@dataclass
class Vec2:
    x: float = 0.0
    y: float = 0.0

    def __add__(self, other):
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar):
        return Vec2(self.x * scalar, self.y * scalar)

    def __repr__(self):
        return f"Vec2({self.x:.1f}, {self.y:.1f})"

    def as_tuple(self):
        return (int(self.x), int(self.y))
