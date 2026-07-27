import pygame


class Widget:
    def __init__(self, x=0, y=0, w=0, h=0):
        self.rect = pygame.Rect(x, y, w, h)
        self.parent = None
        self.visible = True
        self.enabled = True

    def handle_event(self, event):
        return False

    def draw(self, surface):
        pass

    def get_abs_rect(self):
        if self.parent:
            pr = self.parent.get_abs_rect()
            return pygame.Rect(
                pr.x + self.rect.x, pr.y + self.rect.y,
                self.rect.w, self.rect.h
            )
        return self.rect.copy()

    def _abs_rect(self):
        return self.get_abs_rect()

    def contains(self, point):
        return self.get_abs_rect().collidepoint(point)

    def set_pos(self, x, y):
        self.rect.x = x
        self.rect.y = y

    def set_size(self, w, h):
        self.rect.w = w
        self.rect.h = h


class Container(Widget):
    def __init__(self, x=0, y=0, w=0, h=0):
        super().__init__(x, y, w, h)
        self.children = []

    def add(self, child):
        child.parent = self
        self.children.append(child)

    def remove(self, child):
        if child in self.children:
            child.parent = None
            self.children.remove(child)

    def clear(self):
        for c in self.children:
            c.parent = None
        self.children.clear()

    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return False
        for child in reversed(self.children):
            if child.visible and child.handle_event(event):
                return True
        return False

    def draw(self, surface):
        if not self.visible:
            return
        for child in self.children:
            if child.visible:
                child.draw(surface)
