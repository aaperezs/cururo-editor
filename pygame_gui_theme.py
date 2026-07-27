import os
import pygame

_FONTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts")


def create_gui(resolution, offset_getter=None):
    import json
    import pygame_gui

    font_path = os.path.join(_FONTS_DIR, "DejaVuSans.ttf")
    bold_path = os.path.join(_FONTS_DIR, "DejaVuSans-Bold.ttf")
    theme_path = os.path.join(_FONTS_DIR, "theme.json")

    with open(theme_path, "r", encoding="utf-8") as f:
        theme_data = json.load(f)

    gui = pygame_gui.UIManager(resolution)

    gui.get_theme().get_font_dictionary().add_font_path(
        "dejavu_sans", font_path, bold_path=bold_path
    )

    gui.get_theme().load_theme(theme_data)

    if offset_getter is not None:
        orig = gui._update_mouse_position
        def _patched():
            mx, my = pygame.mouse.get_pos()
            ox, oy = offset_getter()
            gui.mouse_position = gui.calculate_scaled_mouse_position((mx - ox, my - oy))
        gui._update_mouse_position = _patched

    return gui
