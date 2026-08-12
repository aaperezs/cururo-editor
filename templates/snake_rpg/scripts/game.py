from orm.runtime import game, renderer, input
from orm.runtime.camera import Camera


@game.init
def init():
    global camera
    camera = Camera(800, 600)


@game.update
def update():
    pass


@game.draw
def draw(screen):
    screen.fill((30, 40, 50))
    renderer.draw_text(screen, "Mi Juego - Cururo Runtime",
                       10, 10, size=20, color=(200, 200, 220))
    renderer.draw_text(screen, "Edita scripts/game.py para empezar",
                       10, 36, size=14, color=(150, 160, 170))


@game.input
def handle_input(event):
    import pygame
    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        return "quit"
