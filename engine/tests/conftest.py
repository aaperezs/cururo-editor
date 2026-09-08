import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.display.init()
pygame.font.init()
pygame.event.set_allowed(None)
pygame.event.set_allowed(pygame.KEYDOWN)
pygame.event.set_allowed(pygame.QUIT)
