import pygame

_key_map = {
    "up": pygame.K_UP, "down": pygame.K_DOWN,
    "left": pygame.K_LEFT, "right": pygame.K_RIGHT,
    "space": pygame.K_SPACE, "return": pygame.K_RETURN,
    "escape": pygame.K_ESCAPE, "tab": pygame.K_TAB,
    "a": pygame.K_a, "b": pygame.K_b, "c": pygame.K_c,
    "d": pygame.K_d, "e": pygame.K_e, "f": pygame.K_f,
    "g": pygame.K_g, "h": pygame.K_h, "i": pygame.K_i,
    "j": pygame.K_j, "k": pygame.K_k, "l": pygame.K_l,
    "m": pygame.K_m, "n": pygame.K_n, "o": pygame.K_o,
    "p": pygame.K_p, "q": pygame.K_q, "r": pygame.K_r,
    "s": pygame.K_s, "t": pygame.K_t, "u": pygame.K_u,
    "v": pygame.K_v, "w": pygame.K_w, "x": pygame.K_x,
    "y": pygame.K_y, "z": pygame.K_z,
    "0": pygame.K_0, "1": pygame.K_1, "2": pygame.K_2,
    "3": pygame.K_3, "4": pygame.K_4, "5": pygame.K_5,
    "6": pygame.K_6, "7": pygame.K_7, "8": pygame.K_8,
    "9": pygame.K_9,
    "lshift": pygame.K_LSHIFT, "rshift": pygame.K_RSHIFT,
    "lctrl": pygame.K_LCTRL, "rctrl": pygame.K_RCTRL,
    "lalt": pygame.K_LALT, "ralt": pygame.K_RALT,
}

_just_pressed = set()
_just_released = set()


def is_key_down(key):
    if isinstance(key, str):
        key = _key_map.get(key.lower())
        if key is None:
            return False
    keys = pygame.key.get_pressed()
    return bool(keys[key]) if key < len(keys) else False


def is_key_just_pressed(key):
    if isinstance(key, str):
        key = _key_map.get(key.lower())
        if key is None:
            return False
    return key in _just_pressed


def is_key_just_released(key):
    if isinstance(key, str):
        key = _key_map.get(key.lower())
        if key is None:
            return False
    return key in _just_released


def get_mouse_pos():
    return pygame.mouse.get_pos()


def get_mouse_buttons():
    return pygame.mouse.get_pressed()


def is_mouse_button_down(button=1):
    return pygame.mouse.get_pressed()[button - 1]


def handle_event(event):
    if event.type == pygame.KEYDOWN:
        _just_pressed.add(event.key)
        if event.key in _just_released:
            _just_released.discard(event.key)
    elif event.type == pygame.KEYUP:
        _just_released.add(event.key)
        if event.key in _just_pressed:
            _just_pressed.discard(event.key)


def clear_frame():
    _just_pressed.clear()
    _just_released.clear()
