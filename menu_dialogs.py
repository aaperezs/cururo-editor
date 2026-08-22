"""Modal dialogs for MenuTab (template selection, rename).

Pure pygame rendering — no pygame_gui dependency.
Extracted from MenuTab (menu_panel.py) for testability.
"""

from __future__ import annotations

from typing import Any

import pygame


def prompt_template(i18n: Any) -> str | None:
    """Show a template selection dialog. Returns template key or None."""
    i = i18n
    font = i.fuente(14) if i else pygame.font.SysFont("Arial", 14)
    font_b = i.fuente(14, bold=True) if i else pygame.font.SysFont("Arial", 14, bold=True)
    screen = pygame.display.get_surface()
    assert screen is not None
    W, H = screen.get_width(), screen.get_height()
    dw, dh = 460, 220
    dx, dy = (W - dw) // 2, (H - dh) // 2
    tpls = [
        ("vacio", i.t("menu.tpl_vacio")),
        ("inventario", i.t("menu.tpl_inventario")),
        ("opciones", i.t("menu.tpl_opciones")),
        ("relaciones", i.t("menu.tpl_relaciones")),
    ]
    bw, bh, gap = 200, 34, 12
    x0 = dx + (dw - (bw * 2 + gap)) // 2
    y0 = dy + 60
    btn_rects = []
    for n, (key, label) in enumerate(tpls):
        col = n % 2
        row = n // 2
        btn_rects.append(
            (pygame.Rect(x0 + col * (bw + gap), y0 + row * (bh + 10), bw, bh), key, label)
        )
    clock = pygame.time.Clock()
    result = None
    done = False
    bg = pygame.Surface((W, H), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 180))
    while not done:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                done = True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, key, _label in btn_rects:
                    if rect.collidepoint(event.pos):
                        result = key
                        done = True
                        break
        screen.blit(bg, (0, 0))
        pygame.draw.rect(screen, (45, 50, 58), (dx, dy, dw, dh))
        pygame.draw.rect(screen, (70, 80, 95), (dx, dy, dw, dh), 2)
        title = font_b.render(i.t("menu.template_title"), True, (220, 190, 120))
        screen.blit(title, (dx + (dw - title.get_width()) // 2, dy + 16))
        for rect, _key, label in btn_rects:
            pygame.draw.rect(screen, (70, 78, 90), rect)
            pygame.draw.rect(screen, (110, 120, 135), rect, 1)
            txt = font.render(label, True, (210, 210, 210))
            screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))
        pygame.display.flip()
    return result


def prompt_new_id(i18n: Any, current_id: str) -> str | None:
    """Show a rename dialog. Returns new ID or None."""
    i = i18n
    font = i.fuente(14) if i else pygame.font.SysFont("Arial", 14)
    font_b = i.fuente(14, bold=True) if i else pygame.font.SysFont("Arial", 14, bold=True)
    screen = pygame.display.get_surface()
    assert screen is not None
    W, H = screen.get_width(), screen.get_height()
    dw, dh = 400, 160
    dx, dy = (W - dw) // 2, (H - dh) // 2
    input_text = current_id
    cursor_pos = len(input_text)
    clock = pygame.time.Clock()
    result = None
    done = False
    bg = pygame.Surface((W, H), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 180))
    while not done:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    done = True
                    result = None
                elif event.key == pygame.K_RETURN:
                    result = input_text.strip()
                    done = True
                elif event.key == pygame.K_BACKSPACE:
                    if cursor_pos > 0:
                        input_text = input_text[:cursor_pos - 1] + input_text[cursor_pos:]
                        cursor_pos -= 1
                elif event.key == pygame.K_DELETE:
                    if cursor_pos < len(input_text):
                        input_text = input_text[:cursor_pos] + input_text[cursor_pos + 1:]
                elif event.key == pygame.K_LEFT:
                    cursor_pos = max(0, cursor_pos - 1)
                elif event.key == pygame.K_RIGHT:
                    cursor_pos = min(len(input_text), cursor_pos + 1)
                elif event.key == pygame.K_HOME:
                    cursor_pos = 0
                elif event.key == pygame.K_END:
                    cursor_pos = len(input_text)
                elif event.unicode and event.unicode.isprintable():
                    input_text = input_text[:cursor_pos] + event.unicode + input_text[cursor_pos:]
                    cursor_pos += 1
        screen.blit(bg, (0, 0))
        pygame.draw.rect(screen, (45, 50, 58), (dx, dy, dw, dh))
        pygame.draw.rect(screen, (70, 80, 95), (dx, dy, dw, dh), 2)
        title = font_b.render(i.t("menu.rename"), True, (220, 190, 120))
        screen.blit(title, (dx + (dw - title.get_width()) // 2, dy + 14))
        lbl = font.render("Nuevo ID:", True, (180, 190, 200))
        screen.blit(lbl, (dx + 20, dy + 50))
        inp_r = pygame.Rect(dx + 20, dy + 74, dw - 40, 28)
        pygame.draw.rect(screen, (55, 60, 70), inp_r)
        pygame.draw.rect(screen, (80, 90, 105), inp_r, 1)
        txt = font.render(input_text, True, (220, 220, 220))
        screen.blit(txt, (inp_r.x + 4, inp_r.y + (inp_r.h - txt.get_height()) // 2))
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            cx = inp_r.x + 4 + font.size(input_text[:cursor_pos])[0]
            pygame.draw.line(screen, (200, 200, 200), (cx, inp_r.y + 3), (cx, inp_r.y + inp_r.h - 3))
        pygame.display.flip()
    return result
