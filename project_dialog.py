import os
import pygame
from editor.project import discover_projects, list_templates, create_project

STATE_LIST = 0
STATE_NEW = 1


class ProjectDialog:
    def __init__(self, search_dir):
        self.search_dir = search_dir
        self.projects = discover_projects(search_dir)
        self.templates = list_templates()
        self.selected_index = 0
        self.font = None
        self.font_b = None
        self.font_title = None
        self.W, self.H = 500, 400
        self.ITEM_H = 40
        self.done = False
        self.result = None

        self.state = STATE_LIST

        self._new_name = ""
        self._new_template_id = self.templates[0]["id"] if self.templates else "empty_rpg"
        self._cursor_visible = True
        self._cursor_timer = 0
        self._error_msg = ""

    def _input_key(self, event):
        if event.key == pygame.K_RETURN:
            return self._do_create()
        if event.key == pygame.K_ESCAPE:
            self.state = STATE_LIST
            return True
        if event.key == pygame.K_BACKSPACE:
            self._new_name = self._new_name[:-1]
        elif event.key == pygame.K_TAB:
            idx = next((i for i, t in enumerate(self.templates)
                        if t["id"] == self._new_template_id), 0)
            self._new_template_id = self.templates[(idx + 1) % len(self.templates)]["id"]
        else:
            if event.unicode and len(self._new_name) < 40:
                self._new_name += event.unicode
        return True

    def _do_create(self):
        name = self._new_name.strip()
        if not name:
            self._error_msg = "Ingresa un nombre para el proyecto"
            return True
        safe = name.lower().replace(" ", "_").replace("-", "_")
        base = os.path.join(self.search_dir, safe)
        n = 1
        path = base
        while os.path.exists(path):
            path = f"{base}_{n}"
            n += 1
        result = create_project(self._new_template_id, name, path)
        if result:
            self.result = {"path": result, "name": name, "id": safe}
            self.done = True
        else:
            self._error_msg = "Error al crear el proyecto"
        return True

    def run(self):
        pygame.init()
        pygame.font.init()
        self.font = pygame.font.SysFont("Arial", 14)
        self.font_b = pygame.font.SysFont("Arial", 14, bold=True)
        self.font_title = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 12)
        screen = pygame.display.set_mode((self.W, self.H))
        pygame.display.set_caption("Cururo Editor")
        clock = pygame.time.Clock()

        while not self.done:
            clock.tick(30)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True
                    self.result = None

                elif self.state == STATE_LIST:
                    if event.type == pygame.KEYDOWN:
                        total = len(self.projects) + 1
                        if event.key == pygame.K_UP:
                            self.selected_index = max(0, self.selected_index - 1)
                        elif event.key == pygame.K_DOWN:
                            self.selected_index = min(total - 1, self.selected_index + 1)
                        elif event.key == pygame.K_RETURN:
                            if self.selected_index == 0:
                                self.state = STATE_NEW
                                self._new_name = ""
                                self._error_msg = ""
                            elif self.projects:
                                idx = self.selected_index - 1
                                if 0 <= idx < len(self.projects):
                                    self.result = self.projects[idx]
                                    self.done = True
                        elif event.key == pygame.K_ESCAPE:
                            self.done = True
                            self.result = None
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        mx, my = event.pos
                        if 40 <= mx <= self.W - 40 and 80 <= my <= 80 + self.ITEM_H - 4:
                            self.state = STATE_NEW
                            self._new_name = ""
                            self._error_msg = ""
                        for i, p in enumerate(self.projects):
                            ry = 80 + self.ITEM_H + i * self.ITEM_H
                            if 40 <= mx <= self.W - 40 and ry <= my <= ry + self.ITEM_H - 4:
                                self.result = p
                                self.done = True

                elif self.state == STATE_NEW:
                    if event.type == pygame.KEYDOWN:
                        self._input_key(event)
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        mx, my = event.pos
                        template_area = pygame.Rect(40, 170, self.W - 80, 40)
                        if template_area.collidepoint(mx, my):
                            idx = next((i for i, t in enumerate(self.templates)
                                        if t["id"] == self._new_template_id), 0)
                            self._new_template_id = self.templates[
                                (idx + 1) % len(self.templates)
                            ]["id"]
                        create_btn = pygame.Rect(self.W // 2 - 60, 250, 120, 36)
                        if create_btn.collidepoint(mx, my):
                            self._do_create()
                        cancel_btn = pygame.Rect(self.W // 2 - 60, 300, 120, 36)
                        if cancel_btn.collidepoint(mx, my):
                            self.state = STATE_LIST

            screen.fill((25, 28, 32))

            if self.state == STATE_LIST:
                self._draw_list(screen)
            else:
                self._draw_new(screen)

            pygame.display.flip()

        return self.result["path"] if self.result else None

    def _draw_list(self, screen):
        title = self.font_title.render("Cururo Editor", True, (200, 210, 220))
        screen.blit(title, (self.W // 2 - title.get_width() // 2, 20))

        sub = self.font.render("Proyectos:", True, (150, 160, 170))
        screen.blit(sub, (20, 55))

        ry = 80
        sel = self.selected_index == 0
        bg = (55, 70, 90) if sel else (42, 55, 70)
        pygame.draw.rect(screen, bg, (40, ry, self.W - 80, self.ITEM_H - 4))
        if sel:
            pygame.draw.rect(screen, (70, 160, 220), (40, ry, 3, self.ITEM_H - 4))
        plus = self.font_b.render("+ Nuevo Proyecto", True, (160, 210, 255))
        screen.blit(plus, (54, ry + 10))

        for i, p in enumerate(self.projects):
            ry = 80 + self.ITEM_H + i * self.ITEM_H
            sel = self.selected_index == i + 1
            bg = (55, 60, 72) if sel else (38, 42, 50)
            pygame.draw.rect(screen, bg, (40, ry, self.W - 80, self.ITEM_H - 4))
            if sel:
                pygame.draw.rect(screen, (70, 130, 200), (40, ry, 3, self.ITEM_H - 4))
            name = self.font_b.render(p["name"], True, (200, 210, 220))
            screen.blit(name, (54, ry + 4))
            pid = self.font.render(p["id"], True, (130, 140, 150))
            screen.blit(pid, (54, ry + 22))

        if not self.projects:
            txt = self.font.render(
                "No hay proyectos. Cree uno nuevo.", True, (160, 170, 180))
            screen.blit(txt, (54, 80 + self.ITEM_H + 10))

        hint = self.font.render(
            "\u2191\u2193: navegar  Enter: abrir/crear  ESC: salir",
            True, (100, 110, 120))
        screen.blit(hint, (self.W // 2 - hint.get_width() // 2, self.H - 30))

    def _draw_new(self, screen):
        title = self.font_title.render("Nuevo Proyecto", True, (200, 210, 220))
        screen.blit(title, (self.W // 2 - title.get_width() // 2, 20))

        lbl = self.font.render("Nombre del proyecto:", True, (180, 190, 200))
        screen.blit(lbl, (40, 65))

        input_rect = pygame.Rect(40, 90, self.W - 80, 32)
        pygame.draw.rect(screen, (50, 55, 65), input_rect)
        pygame.draw.rect(screen, (70, 130, 200), input_rect, 2)

        display_name = self._new_name
        self._cursor_timer += 1
        if self._cursor_timer >= 30:
            self._cursor_timer = 0
            self._cursor_visible = not self._cursor_visible
        if self._cursor_visible:
            display_name += "|"

        txt = self.font_b.render(display_name, True, (220, 220, 220))
        screen.blit(txt, (48, 96))

        safe = self._new_name.lower().replace(" ", "_").replace("-", "_") if self._new_name else "..."
        path_preview = self.font_small.render(
            os.path.join(self.search_dir, safe), True, (120, 130, 140))
        screen.blit(path_preview, (48, 128))

        tmpl_lbl = self.font.render("Plantilla:", True, (180, 190, 200))
        screen.blit(tmpl_lbl, (40, 170))

        tmpl_name = next((t["name"] for t in self.templates
                          if t["id"] == self._new_template_id), "Empty RPG")
        tmpl_rect = pygame.Rect(40, 190, self.W - 80, 28)
        pygame.draw.rect(screen, (55, 60, 72), tmpl_rect)
        pygame.draw.rect(screen, (65, 70, 80), tmpl_rect, 1)
        tmpl_txt = self.font.render(tmpl_name + "  [Click para cambiar]", True, (180, 200, 230))
        screen.blit(tmpl_txt, (48, 196))

        create_btn = pygame.Rect(self.W // 2 - 60, 250, 120, 36)
        pygame.draw.rect(screen, (50, 100, 50), create_btn)
        pygame.draw.rect(screen, (70, 140, 70), create_btn, 2)
        c_txt = self.font_b.render("Crear", True, (220, 220, 220))
        screen.blit(c_txt, (create_btn.centerx - c_txt.get_width() // 2,
                            create_btn.centery - c_txt.get_height() // 2))

        cancel_btn = pygame.Rect(self.W // 2 - 60, 300, 120, 36)
        pygame.draw.rect(screen, (60, 60, 65), cancel_btn)
        pygame.draw.rect(screen, (75, 75, 80), cancel_btn, 2)
        esc_txt = self.font.render("Cancelar", True, (180, 180, 185))
        screen.blit(esc_txt, (cancel_btn.centerx - esc_txt.get_width() // 2,
                              cancel_btn.centery - esc_txt.get_height() // 2))

        if self._error_msg:
            err = self.font.render(self._error_msg, True, (220, 80, 80))
            screen.blit(err, (self.W // 2 - err.get_width() // 2, 230))

        hint = self.font.render(
            "Enter: crear  |  ESC: volver  |  TAB: cambiar plantilla",
            True, (100, 110, 120))
        screen.blit(hint, (self.W // 2 - hint.get_width() // 2, self.H - 30))
