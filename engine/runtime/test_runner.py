"""
Standalone test that proves the runtime API works end-to-end.
Run: python -m engine.runtime.test_runner
"""
import os
import sys

# Make sure the project root is on sys.path
_project_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pygame
from engine.runtime import input as rt_input
from engine.runtime.loader import load_script


def main():
    project_root = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Cururo Runtime - Test")
    clock = pygame.time.Clock()

    module = load_script(project_root, "game")
    if module is None:
        print("No se encontro scripts/game.py")
        pygame.quit()
        return

    from engine.runtime import game
    game.run_init()

    running = True
    while running:
        rt_input.clear_frame()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            rt_input.handle_event(event)
            result = game.run_input(event)
            if result == "quit":
                running = False

        game.run_update()
        game.run_draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
