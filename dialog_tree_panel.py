import pygame
import pygame_gui

from editor.translation import I18n
from editor.panels.base_panel import BasePanel
from editor.pygame_gui_theme import create_gui
from editor.dialog_data import (
    get_all_dialogo_keys, get_dialogo_by_key, set_dialogo_by_key,
    delete_dialogo_by_key, create_dialogo_by_key, rename_dialogo,
    get_tree, set_tree_by_key, create_tree_key, add_node, remove_node,
    compile_to_flat, NODE_LABELS, NODE_COLORS, NODE_DEFAULTS,
    _parse_key, _make_key,
)

PADDING = 6
TOOLBAR_H = 36
LEFT_W = 220
NODE_H = 30
NODE_INDENT = 20


class DialogTreePanel(BasePanel):
    def __init__(self, x, y, w, h, i18n):
        super().__init__(0, 0, w, h, i18n)
        self.bg_color = (30, 32, 36)
        self._gui = create_gui((w, h), offset_getter=lambda: (
            self.get_abs_rect().x, self.get_abs_rect().y
        ))
        self._selected_key = None
        self._selected_nid = None
        self._tree_scroll = 0
        self._dirty = False
        self._node_widgets = {}
        self._detail_widgets = {}
        self._build_ui()

    # ── UI ─────────────────────────────────────────────────

    def _build_ui(self):
        prev_key = self._selected_key
        self._gui.clear_and_reset()
        self._node_widgets.clear()
        self._detail_widgets.clear()
        w, h = self.rect.w, self.rect.h

        self._new_btn = pygame_gui.elements.UIButton(
            pygame.Rect(8, 4, 72, 28), self.i18n.t("dialog.new"), self._gui
        )
        self._clone_btn = pygame_gui.elements.UIButton(
            pygame.Rect(86, 4, 72, 28), self.i18n.t("dialog.clone"), self._gui
        )
        self._del_btn = pygame_gui.elements.UIButton(
            pygame.Rect(164, 4, 72, 28), self.i18n.t("dialog.delete"), self._gui
        )
        self._save_btn = pygame_gui.elements.UIButton(
            pygame.Rect(240, 4, 72, 28), self.i18n.t("dialog.save"), self._gui
        )
        self._add_dialogo_btn = pygame_gui.elements.UIButton(
            pygame.Rect(320, 4, 80, 28), "+ Diálogo", self._gui
        )
        self._add_opcion_btn = pygame_gui.elements.UIButton(
            pygame.Rect(406, 4, 74, 28), "+ Opción", self._gui
        )
        self._add_condicion_btn = pygame_gui.elements.UIButton(
            pygame.Rect(486, 4, 84, 28), "+ Condición", self._gui
        )
        self._add_accion_btn = pygame_gui.elements.UIButton(
            pygame.Rect(576, 4, 70, 28), "+ Acción", self._gui
        )
        self._add_salto_btn = pygame_gui.elements.UIButton(
            pygame.Rect(652, 4, 62, 28), "+ Salto", self._gui
        )

        cy = TOOLBAR_H
        self._text_list = pygame_gui.elements.UISelectionList(
            pygame.Rect(0, cy, LEFT_W, h - cy),
            item_list=get_all_dialogo_keys(),
            manager=self._gui,
            default_selection=prev_key,
        )

        rx, rw = LEFT_W, w - LEFT_W
        self._editor_panel = pygame_gui.elements.UIPanel(
            pygame.Rect(rx, cy, rw, h - cy), manager=self._gui
        )

        if prev_key:
            self._selected_key = prev_key
            self._build_tree_widgets()

    def _build_tree_widgets(self):
        ep = self._editor_panel
        w = ep.rect.w

        # ID label at top
        self._eid_label = pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, 4, w - PADDING * 2, 20),
            f"ID: {self._selected_key}", self._gui, container=ep
        )

        # Tree list area will be custom-drawn
        # Detail area below tree
        self._build_detail_area()

    def _build_detail_area(self):
        ep = self._editor_panel
        self._detail_widgets.clear()
        y = 0
        ew = ep.rect.w

        if not self._selected_nid:
            return
        tree = get_tree_by_key(self._selected_key)
        if not tree or self._selected_nid not in tree["nodes"]:
            return
        node = tree["nodes"][self._selected_nid]
        tipo = node["tipo"]

        # Type label
        lbl = pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, ew - PADDING * 2, 18),
            f"Tipo: {NODE_LABELS.get(tipo, tipo)}", self._gui, container=ep
        )
        self._detail_widgets["type_label"] = lbl
        y += 24

        if tipo == "dialogo":
            lbl = pygame_gui.elements.UILabel(
                pygame.Rect(PADDING, y, 60, 22), "Texto:", self._gui, container=ep
            )
            self._detail_widgets["l_texto"] = lbl
            inp = pygame_gui.elements.UITextEntryLine(
                pygame.Rect(70, y, ew - 80, 22),
                initial_text=node.get("texto", ""),
                manager=self._gui, container=ep
            )
            self._detail_widgets["texto"] = inp
            y += 28
            lbl2 = pygame_gui.elements.UILabel(
                pygame.Rect(PADDING, y, 60, 22), "Siguiente:", self._gui, container=ep
            )
            self._detail_widgets["l_next"] = lbl2
            nids = [n for n in tree["nodes"].keys() if n != self._selected_nid]
            opts = [("", "(ninguno)")] + [(n, n) for n in sorted(nids)]
            dd = _TreeDropdown(70, y, ew - 80, 22, opts, selected=node.get("next", ""))
            self._detail_widgets["next"] = dd
            y += 28

        elif tipo == "opcion":
            choices = node.get("choices", [])
            for ci, ch in enumerate(choices):
                lbl = pygame_gui.elements.UILabel(
                    pygame.Rect(PADDING, y, 20, 22), f"{ci+1}:", self._gui, container=ep
                )
                self._detail_widgets[f"l_choice_{ci}"] = lbl
                inp = pygame_gui.elements.UITextEntryLine(
                    pygame.Rect(30, y, ew - 140, 22),
                    initial_text=ch.get("texto", ""),
                    manager=self._gui, container=ep
                )
                self._detail_widgets[f"choice_text_{ci}"] = inp
                nids = [n for n in tree["nodes"].keys() if n != self._selected_nid]
                opts = [("", "(ninguno)")] + [(n, n) for n in sorted(nids)]
                dd = _TreeDropdown(ew - 100, y, 90, 22, opts, selected=ch.get("next", ""))
                self._detail_widgets[f"choice_next_{ci}"] = dd
                y += 28

        elif tipo == "condicion":
            fields = [
                ("flag", "Flag:", 80),
                ("operador", "Op:", 60),
                ("valor", "Valor:", 60),
            ]
            x = PADDING
            for key, label, fw in fields:
                lbl = pygame_gui.elements.UILabel(
                    pygame.Rect(x, y, fw, 22), label, self._gui, container=ep
                )
                self._detail_widgets[f"l_{key}"] = lbl
                x += fw
            x = PADDING
            for key, label, fw in fields:
                if key == "operador":
                    opts = [("==", "=="), ("!=", "!="), (">=", ">="), ("<=", "<="),
                            (">", ">"), ("<", "<"), ("es_verdadero", "es_verdadero"),
                            ("es_falso", "es_falso")]
                    dd = _TreeDropdown(x, y, fw - 4, 22, opts, selected=node.get("operador", "=="))
                    self._detail_widgets[key] = dd
                else:
                    inp = pygame_gui.elements.UITextEntryLine(
                        pygame.Rect(x, y, fw - 4, 22),
                        initial_text=node.get(key, ""),
                        manager=self._gui, container=ep
                    )
                    self._detail_widgets[key] = inp
                x += fw + 4
            y += 28
            nids = [n for n in tree["nodes"].keys() if n != self._selected_nid]
            opts = [("", "(ninguno)")] + [(n, n) for n in sorted(nids)]
            lbl = pygame_gui.elements.UILabel(
                pygame.Rect(PADDING, y, 80, 22), "Si verdad:", self._gui, container=ep
            )
            self._detail_widgets["l_next"] = lbl
            dd = _TreeDropdown(90, y, ew - 100, 22, opts, selected=node.get("next", ""))
            self._detail_widgets["next"] = dd
            y += 28
            lbl2 = pygame_gui.elements.UILabel(
                pygame.Rect(PADDING, y, 80, 22), "Si falso:", self._gui, container=ep
            )
            self._detail_widgets["l_next_false"] = lbl2
            dd2 = _TreeDropdown(90, y, ew - 100, 22, opts, selected=node.get("next_false", ""))
            self._detail_widgets["next_false"] = dd2

        elif tipo == "accion":
            opts = [
                ("set_flag", "set_flag"),
                ("add_flag", "add_flag"),
                ("cambiar_fondo", "cambiar_fondo"),
                ("mostrar_personaje", "mostrar_personaje"),
                ("ocultar_personaje", "ocultar_personaje"),
                ("ocultar_todos_personajes", "ocultar_todos_personajes"),
            ]
            lbl = pygame_gui.elements.UILabel(
                pygame.Rect(PADDING, y, 80, 22), "Acción:", self._gui, container=ep
            )
            self._detail_widgets["l_tipo_accion"] = lbl
            dd = _TreeDropdown(90, y, ew - 100, 22, opts, selected=node.get("tipo_accion", "set_flag"))
            self._detail_widgets["tipo_accion"] = dd
            y += 28
            p = node.get("params", {})
            lbl = pygame_gui.elements.UILabel(
                pygame.Rect(PADDING, y, 100, 22), "Params (flag=valor):", self._gui, container=ep
            )
            self._detail_widgets["l_params"] = lbl
            inp = pygame_gui.elements.UITextEntryLine(
                pygame.Rect(120, y, ew - 130, 22),
                initial_text=",".join(f"{k}={v}" for k, v in p.items()),
                manager=self._gui, container=ep
            )
            self._detail_widgets["params"] = inp
            y += 28
            nids = [n for n in tree["nodes"].keys() if n != self._selected_nid]
            opts = [("", "(ninguno)")] + [(n, n) for n in sorted(nids)]
            lbl = pygame_gui.elements.UILabel(
                pygame.Rect(PADDING, y, 80, 22), "Siguiente:", self._gui, container=ep
            )
            self._detail_widgets["l_next"] = lbl
            dd = _TreeDropdown(90, y, ew - 100, 22, opts, selected=node.get("next", ""))
            self._detail_widgets["next"] = dd

        elif tipo == "salto":
            lbl = pygame_gui.elements.UILabel(
                pygame.Rect(PADDING, y, 80, 22), "Destino:", self._gui, container=ep
            )
            self._detail_widgets["l_destino"] = lbl
            opts = [("", "(seleccionar)")] + [(k, k) for k in get_all_dialogo_keys()]
            dd = _TreeDropdown(90, y, ew - 100, 22, opts, selected=node.get("destino", ""))
            self._detail_widgets["destino"] = dd

    # ── Tree rendering ──

    def _get_tree_rect(self):
        ar = self.get_abs_rect()
        ep = self._editor_panel
        return pygame.Rect(ar.x + ep.rect.x, ar.y + ep.rect.y + 28,
                           ep.rect.w, ep.rect.h - 220)

    def _draw_tree(self, surface):
        if not self._selected_key:
            return
        tree = get_tree_by_key(self._selected_key)
        if not tree:
            return

        tr = self._get_tree_rect()
        clip = surface.get_clip()
        surface.set_clip(tr)

        nodes = tree.get("nodes", {})
        start = tree.get("start", "")
        visited = []
        queue = [start] if start else []
        drawn = 0
        while queue and drawn < 100:
            nid = queue.pop(0)
            if nid in visited or nid not in nodes:
                continue
            visited.append(nid)
            sy = tr.y + drawn * NODE_H - self._tree_scroll
            if sy + NODE_H >= tr.y and sy <= tr.y + tr.h:
                self._draw_node(surface, tr.x, sy, tr.w, nid, nodes[nid])
            drawn += 1
            node = nodes[nid]
            if node["tipo"] == "opcion":
                for ch in node.get("choices", []):
                    if ch.get("next") and ch["next"] not in visited:
                        queue.append(ch["next"])
            elif node["tipo"] == "condicion":
                if node.get("next") and node["next"] not in visited:
                    queue.append(node["next"])
                if node.get("next_false") and node["next_false"] not in visited:
                    queue.append(node["next_false"])
            else:
                if node.get("next") and node["next"] not in visited:
                    queue.append(node["next"])

        surface.set_clip(clip)

    def _draw_node(self, surface, x, y, w, nid, node):
        tipo = node.get("tipo", "")
        color = NODE_COLORS.get(tipo, (100, 100, 100))
        label = NODE_LABELS.get(tipo, tipo)
        preview = ""
        if tipo == "dialogo":
            preview = node.get("texto", "")[:40]
        elif tipo == "opcion":
            preview = " / ".join(c.get("texto", "?")[:20] for c in node.get("choices", []))
        elif tipo == "condicion":
            preview = f"{node.get('flag','?')} {node.get('operador','')} {node.get('valor','')}"
        elif tipo == "accion":
            preview = node.get("tipo_accion", "")
        elif tipo == "salto":
            preview = f"→ {node.get('destino','')}"

        sel = nid == self._selected_nid
        bg = (45, 48, 56) if not sel else (55, 60, 78)
        pygame.draw.rect(surface, bg, (x, y, w, NODE_H))
        pygame.draw.rect(surface, (70, 75, 85), (x, y, w, NODE_H), 1)
        if sel:
            pygame.draw.rect(surface, (70, 130, 200), (x, y, 3, NODE_H))

        # Type badge
        badge = pygame.Rect(x + 4, y + 4, 60, NODE_H - 8)
        pygame.draw.rect(surface, color, badge, border_radius=3)
        i18n = I18n.instancia()
        fuente = i18n.fuente(10) if i18n else pygame.font.SysFont("Arial", 10)
        lbl_s = fuente.render(label, True, (255, 255, 255))
        surface.blit(lbl_s, (badge.x + (badge.w - lbl_s.get_width()) // 2,
                             badge.y + (badge.h - lbl_s.get_height()) // 2))

        # Preview text
        px = x + 72
        fuente2 = i18n.fuente(11) if i18n else pygame.font.SysFont("Arial", 11)
        prev_s = fuente2.render(preview, True, (180, 190, 200))
        surface.blit(prev_s, (px, y + (NODE_H - prev_s.get_height()) // 2))

        # Delete button
        del_r = pygame.Rect(x + w - 22, y + 4, 18, NODE_H - 8)
        pygame.draw.rect(surface, (180, 60, 60), del_r, border_radius=3)
        xs = fuente.render("X", True, (255, 255, 255))
        surface.blit(xs, (del_r.x + (del_r.w - xs.get_width()) // 2,
                          del_r.y + (del_r.h - xs.get_height()) // 2))

        self._node_widgets[nid] = {
            "rect": pygame.Rect(x, y, w, NODE_H),
            "del_rect": del_r,
        }

    # ── Actions ───────────────────────────────────────────

    def _on_new(self):
        result = self._prompt_new_key("nuevo_personaje", "nuevo_contexto")
        if result is None:
            return
        if create_dialogo_by_key(result):
            p, c = _parse_key(result)
            create_tree_key(p, c)
            self._selected_key = result
            self._selected_nid = None
            self._dirty = True
            self._build_ui()

    def _on_clone(self):
        if not self._selected_key:
            return
        p, c = _parse_key(self._selected_key)
        result = self._prompt_new_key(p + "_copia", c)
        if result is None or result == self._selected_key:
            return
        tree = get_tree_by_key(self._selected_key)
        if create_dialogo_by_key(result):
            if tree:
                np, nc = _parse_key(result)
                set_tree_by_key(result, tree)
            self._selected_key = result
            self._selected_nid = None
            self._dirty = True
            self._build_ui()

    def _on_delete(self):
        if not self._selected_key:
            return
        delete_dialogo_by_key(self._selected_key)
        self._selected_key = None
        self._selected_nid = None
        self._dirty = True
        self._build_ui()

    def _on_save(self):
        if not self._selected_key:
            return
        self._save_current_node()
        # Also save flat version for legacy runtime
        flat = compile_to_flat(*_parse_key(self._selected_key))
        set_dialogo_by_key(self._selected_key, flat)
        self._dirty = False
        self._build_ui()

    def _save_current_node(self):
        if not self._selected_key or not self._selected_nid:
            return
        tree = get_tree_by_key(self._selected_key)
        if not tree or self._selected_nid not in tree["nodes"]:
            return
        node = tree["nodes"][self._selected_nid]
        tipo = node["tipo"]

        if tipo == "dialogo":
            node["texto"] = self._detail_widgets.get("texto", fake_input("")).get_text()
            node["next"] = self._detail_widgets.get("next", fake_dd("")).get_selected()
        elif tipo == "opcion":
            choices = []
            for key, w in list(self._detail_widgets.items()):
                if key.startswith("choice_text_"):
                    ci = int(key.split("_")[2])
                    while len(choices) <= ci:
                        choices.append({"texto": "", "next": ""})
                    choices[ci]["texto"] = w.get_text()
                elif key.startswith("choice_next_"):
                    ci = int(key.split("_")[2])
                    while len(choices) <= ci:
                        choices.append({"texto": "", "next": ""})
                    choices[ci]["next"] = w.get_selected()
            node["choices"] = choices
        elif tipo == "condicion":
            node["flag"] = self._detail_widgets.get("flag", fake_input("")).get_text()
            node["operador"] = self._detail_widgets.get("operador", fake_dd("==")).get_selected()
            node["valor"] = self._detail_widgets.get("valor", fake_input("")).get_text()
            node["next"] = self._detail_widgets.get("next", fake_dd("")).get_selected()
            node["next_false"] = self._detail_widgets.get("next_false", fake_dd("")).get_selected()
        elif tipo == "accion":
            node["tipo_accion"] = self._detail_widgets.get("tipo_accion", fake_dd("set_flag")).get_selected()
            params_text = self._detail_widgets.get("params", fake_input("")).get_text()
            params = {}
            for part in params_text.split(","):
                part = part.strip()
                if "=" in part:
                    k, v = part.split("=", 1)
                    params[k.strip()] = v.strip()
            node["params"] = params
            node["next"] = self._detail_widgets.get("next", fake_dd("")).get_selected()
        elif tipo == "salto":
            node["destino"] = self._detail_widgets.get("destino", fake_dd("")).get_selected()

        set_tree_by_key(self._selected_key, tree)
        self._dirty = True

    def _on_add_node(self, tipo):
        if not self._selected_key:
            return
        p, c = _parse_key(self._selected_key)
        create_tree_key(p, c)
        nid = add_node(p, c, tipo, after_id=self._selected_nid)
        if nid:
            self._selected_nid = nid
            self._save_current_node()
            self._build_ui()

    def _on_delete_node(self, nid):
        if not self._selected_key:
            return
        p, c = _parse_key(self._selected_key)
        remove_node(p, c, nid)
        if self._selected_nid == nid:
            self._selected_nid = None
        self._build_ui()

    def _select_node(self, nid):
        self._save_current_node()
        self._selected_nid = nid
        self._build_ui()

    # ── Modal ─────────────────────────────────────────────

    def _prompt_new_key(self, default_personaje="", default_contexto=""):
        font = I18n.instancia().fuente(14) if I18n.instancia() else pygame.font.SysFont("Arial", 14)
        font_b = I18n.instancia().fuente(14, bold=True) if I18n.instancia() else pygame.font.SysFont("Arial", 14, bold=True)
        screen = pygame.display.get_surface()
        W, H = screen.get_width(), screen.get_height()
        dw, dh = 420, 200
        dx, dy = (W - dw) // 2, (H - dh) // 2
        fields = [
            {"label": self.i18n.t("dialog.character"), "value": default_personaje},
            {"label": self.i18n.t("dialog.context"), "value": default_contexto},
        ]
        cursor_pos = [len(f["value"]) for f in fields]
        focus = 0
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
                        p = fields[0]["value"].strip()
                        c = fields[1]["value"].strip()
                        if p and c:
                            result = _make_key(p, c)
                            done = True
                        else:
                            focus = 0 if not p else 1
                    elif event.key == pygame.K_TAB:
                        focus = (focus + 1) % len(fields)
                    elif event.key == pygame.K_BACKSPACE:
                        if cursor_pos[focus] > 0:
                            fields[focus]["value"] = fields[focus]["value"][:cursor_pos[focus] - 1] + fields[focus]["value"][cursor_pos[focus]:]
                            cursor_pos[focus] -= 1
                    elif event.key == pygame.K_DELETE:
                        if cursor_pos[focus] < len(fields[focus]["value"]):
                            fields[focus]["value"] = fields[focus]["value"][:cursor_pos[focus]] + fields[focus]["value"][cursor_pos[focus] + 1:]
                    elif event.key == pygame.K_LEFT:
                        cursor_pos[focus] = max(0, cursor_pos[focus] - 1)
                    elif event.key == pygame.K_RIGHT:
                        cursor_pos[focus] = min(len(fields[focus]["value"]), cursor_pos[focus] + 1)
                    elif event.key == pygame.K_HOME:
                        cursor_pos[focus] = 0
                    elif event.key == pygame.K_END:
                        cursor_pos[focus] = len(fields[focus]["value"])
                    elif event.unicode and event.unicode.isprintable():
                        fields[focus]["value"] = fields[focus]["value"][:cursor_pos[focus]] + event.unicode + fields[focus]["value"][cursor_pos[focus]:]
                        cursor_pos[focus] += 1
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    for fi, f in enumerate(fields):
                        fx = dx + 20
                        fy = dy + 50 + fi * 50
                        fr = pygame.Rect(fx + 100, fy, dw - 120, 28)
                        if fr.collidepoint(mx, my):
                            focus = fi
                            rel_x = mx - fr.x - 4
                            txt = font.render(f["value"], True, (220, 220, 220))
                            for ci in range(len(f["value"]) + 1):
                                w_txt = font.render(f["value"][:ci], True, (220, 220, 220))
                                if w_txt.get_width() >= rel_x:
                                    cursor_pos[fi] = ci
                                    break
            screen.blit(bg, (0, 0))
            pygame.draw.rect(screen, (45, 50, 58), (dx, dy, dw, dh))
            pygame.draw.rect(screen, (70, 80, 95), (dx, dy, dw, dh), 2)
            title = font_b.render(self.i18n.t("dialog.new_title"), True, (220, 190, 120))
            screen.blit(title, (dx + (dw - title.get_width()) // 2, dy + 14))
            for fi, f in enumerate(fields):
                fy = dy + 50 + fi * 50
                lbl = font.render(f["label"] + ":", True, (180, 190, 200))
                screen.blit(lbl, (dx + 20, fy + 4))
                inp_r = pygame.Rect(dx + 120, fy, dw - 140, 28)
                bg_c = (70, 80, 100) if fi == focus else (55, 60, 70)
                pygame.draw.rect(screen, bg_c, inp_r)
                pygame.draw.rect(screen, (80, 90, 105), inp_r, 1)
                txt_surf = font.render(f["value"], True, (220, 220, 220))
                screen.blit(txt_surf, (inp_r.x + 4, inp_r.y + (inp_r.h - txt_surf.get_height()) // 2))
                if fi == focus and (pygame.time.get_ticks() // 500) % 2 == 0:
                    cx = inp_r.x + 4 + font.render(f["value"][:cursor_pos[fi]], True, (220, 220, 220)).get_width()
                    pygame.draw.line(screen, (200, 200, 200), (cx, inp_r.y + 3), (cx, inp_r.y + inp_r.h - 3))
            hint = font.render("TAB: cambiar campo  ENTER: aceptar  ESC: cancelar", True, (130, 140, 150))
            screen.blit(hint, (dx + (dw - hint.get_width()) // 2, dy + dh - 22))
            pygame.display.flip()
        return result

    # ── Integración ───────────────────────────────────────

    def update(self, dt):
        self._gui.update(dt)

    def handle_event(self, event):
        if not self.visible:
            return False
        r = self.get_abs_rect()
        if hasattr(event, 'pos'):
            e = pygame.event.Event(event.type, {
                "pos": (event.pos[0] - r.x, event.pos[1] - r.y),
                "button": getattr(event, "button", 0),
                "buttons": getattr(event, "buttons", (0, 0, 0)),
                "rel": getattr(event, "rel", (0, 0)),
            })
        else:
            e = event
        self._gui.process_events(e)

        if e.type == pygame_gui.UI_BUTTON_PRESSED:
            el = e.ui_element
            if el == self._new_btn: self._on_new(); return True
            if el == self._clone_btn: self._on_clone(); return True
            if el == self._del_btn: self._on_delete(); return True
            if el == self._save_btn: self._on_save(); return True
            if el == self._add_dialogo_btn: self._on_add_node("dialogo"); return True
            if el == self._add_opcion_btn: self._on_add_node("opcion"); return True
            if el == self._add_condicion_btn: self._on_add_node("condicion"); return True
            if el == self._add_accion_btn: self._on_add_node("accion"); return True
            if el == self._add_salto_btn: self._on_add_node("salto"); return True

        elif e.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            key = e.text
            if key in get_all_dialogo_keys():
                self._save_current_node()
                self._selected_key = key
                self._selected_nid = None
                self._build_ui()
                return True

        # Custom node click handling
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            mx, my = e.pos[0] + r.x, e.pos[1] + r.y
            for nid, info in self._node_widgets.items():
                if info["del_rect"].collidepoint(mx, my):
                    self._on_delete_node(nid)
                    return True
                if info["rect"].collidepoint(mx, my):
                    self._select_node(nid)
                    return True

        # Mouse wheel for tree scroll
        if e.type == pygame.MOUSEWHEEL:
            tr = self._get_tree_rect()
            mx, my = pygame.mouse.get_pos()
            if tr and tr.collidepoint(mx, my):
                tree = get_tree_by_key(self._selected_key)
                if tree:
                    max_scroll = max(0, len(tree["nodes"]) * NODE_H - tr.h)
                    self._tree_scroll = max(0, min(max_scroll, self._tree_scroll - e.y * NODE_H))
                    return True

        # Detail dropdowns
        for key, w in self._detail_widgets.items():
            if isinstance(w, (_TreeDropdown,)) and w.handle_event(e):
                return True

        return True

    def draw(self, surface):
        if not self.visible:
            return
        r = self.get_abs_rect()
        pygame.draw.rect(surface, self.bg_color, r)
        self._draw_tree(surface)
        self._gui.draw_ui(surface.subsurface(r))

    def set_size(self, w, h):
        if self.rect.w != w or self.rect.h != h:
            self.rect.w = w
            self.rect.h = h
            self._gui.set_window_resolution((w, h))
            self._build_ui()


# ── Helpers ──

class _TreeDropdown:
    MAX_VISIBLE = 8

    def __init__(self, x, y, w, h, options, selected=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.parent = None
        self.visible = True
        self.enabled = True
        self._all_options = list(options)
        self._selected = selected or (options[0][0] if options else None)
        self._open = False
        self._on_select = None
        self._filter_text = ""
        self._filtered = list(options)
        self._scroll_offset = 0
        self._focus = False

    def __repr__(self):
        return f"_TreeDropdown({self._selected})"

    def _abs_rect(self):
        if self.parent:
            pr = (self.parent.get_abs_rect() if hasattr(self.parent, 'get_abs_rect')
                  else self.parent.rect)
            return pygame.Rect(pr.x + self.rect.x, pr.y + self.rect.y,
                               self.rect.w, self.rect.h)
        return self.rect.copy()

    def set_selected(self, value):
        self._selected = value

    def get_selected(self):
        return self._selected

    def _close_others(self):
        pass

    def _bring_to_front(self):
        pass

    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return False
        r = self._abs_rect()
        if self._open:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._open = False
                    self._filter_text = ""
                    self._filtered = list(self._all_options)
                    self._scroll_offset = 0
                    return True
                elif event.key == pygame.K_RETURN:
                    if self._filtered:
                        val = self._filtered[0][0]
                        self._selected = val
                        self._open = False
                        self._filter_text = ""
                        self._filtered = list(self._all_options)
                        self._scroll_offset = 0
                        if self._on_select:
                            self._on_select(val)
                    return True
                elif event.key == pygame.K_UP:
                    if self._filtered:
                        idx = self._get_selected_filtered_idx()
                        new_idx = max(0, idx - 1)
                        if new_idx < self._scroll_offset:
                            self._scroll_offset = new_idx
                        self._selected = self._filtered[new_idx][0]
                    return True
                elif event.key == pygame.K_DOWN:
                    if self._filtered:
                        idx = self._get_selected_filtered_idx()
                        new_idx = min(len(self._filtered) - 1, idx + 1)
                        if new_idx >= self._scroll_offset + self.MAX_VISIBLE:
                            self._scroll_offset = new_idx - self.MAX_VISIBLE + 1
                        self._selected = self._filtered[new_idx][0]
                    return True
                elif event.key == pygame.K_BACKSPACE:
                    self._filter_text = self._filter_text[:-1]
                    self._apply_filter()
                    return True
                elif event.unicode and event.unicode.isprintable():
                    self._filter_text += event.unicode
                    self._apply_filter()
                    return True
            if event.type == pygame.MOUSEWHEEL:
                max_scroll = max(0, len(self._filtered) - self.MAX_VISIBLE)
                self._scroll_offset = max(0, min(max_scroll, self._scroll_offset - event.y))
                return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if r.collidepoint(mx, my):
                if not self._open:
                    self._close_others()
                self._open = not self._open
                self._filter_text = ""
                self._filtered = list(self._all_options)
                self._scroll_offset = 0
                if self._open and self.parent:
                    self._bring_to_front()
                return True
            if self._open:
                ih = 20
                vis = min(len(self._filtered), self.MAX_VISIBLE)
                total_h = vis * ih + 2
                scr_h = pygame.display.get_surface().get_height() if pygame.display.get_surface() else 600
                space_below = scr_h - (r.y + r.h)
                open_up = total_h > space_below and r.y > total_h
                dy = r.y - total_h if open_up else r.y + r.h
                dd_rect = pygame.Rect(r.x, dy, r.w, total_h)
                if dd_rect.y < 0:
                    dd_rect.y = 0
                if scr_h and dd_rect.y + dd_rect.h > scr_h:
                    dd_rect.y = scr_h - dd_rect.h
                has_scroll = len(self._filtered) > self.MAX_VISIBLE
                if dd_rect.collidepoint(mx, my):
                    click_idx = (my - dd_rect.y) // ih
                    idx = self._scroll_offset + click_idx
                    if 0 <= idx < len(self._filtered):
                        val, lbl = self._filtered[idx]
                        self._selected = val
                        self._open = False
                        self._filter_text = ""
                        self._filtered = list(self._all_options)
                        self._scroll_offset = 0
                        if self._on_select:
                            self._on_select(val)
                        return True
                self._open = False
                self._filter_text = ""
                self._filtered = list(self._all_options)
                self._scroll_offset = 0
                return True
        if event.type == pygame.MOUSEBUTTONDOWN and self._open:
            self._open = False
            self._filter_text = ""
            self._filtered = list(self._all_options)
            self._scroll_offset = 0
            return True
        return False

    def _get_selected_filtered_idx(self):
        for i, (val, lbl) in enumerate(self._filtered):
            if val == self._selected:
                return i
        return 0

    def _apply_filter(self):
        ft = self._filter_text.lower()
        if not ft:
            self._filtered = list(self._all_options)
        else:
            self._filtered = [(v, l) for v, l in self._all_options
                              if ft in v.lower() or ft in l.lower()]
        self._scroll_offset = 0

    def draw(self, surface):
        if not self.visible:
            return
        r = self._abs_rect()
        i18n = I18n.instancia()
        fuente = i18n.fuente(12) if i18n else pygame.font.SysFont("Arial", 12)
        label = str(self._selected)
        for val, lbl in self._all_options:
            if val == self._selected:
                label = lbl
                break
        pygame.draw.rect(surface, (50, 55, 65), r)
        pygame.draw.rect(surface, (80, 90, 105), r, 1)
        txt = fuente.render(label, True, (220, 220, 220))
        surface.blit(txt, (r.x + 6, r.y + (r.h - txt.get_height()) // 2))
        pygame.draw.polygon(surface, (160, 170, 180), [
            (r.x + r.w - 12, r.y + r.h // 2 - 2),
            (r.x + r.w - 6, r.y + r.h // 2 - 2),
            (r.x + r.w - 9, r.y + r.h // 2 + 3)
        ])
        if self._open:
            ih = 20
            vis = min(len(self._filtered), self.MAX_VISIBLE)
            total_h = vis * ih + 2
            space_below = surface.get_height() - (r.y + r.h)
            open_up = total_h > space_below and r.y > total_h
            dy = r.y - total_h if open_up else r.y + r.h
            dd_rect = pygame.Rect(r.x, dy, r.w, total_h)
            if dd_rect.y < 0:
                dd_rect.y = 0
            if dd_rect.y + dd_rect.h > surface.get_height():
                dd_rect.y = surface.get_height() - dd_rect.h
            has_scroll = len(self._filtered) > self.MAX_VISIBLE
            sb_w = 10 if has_scroll else 0
            item_w = r.w - sb_w
            pygame.draw.rect(surface, (45, 48, 56), dd_rect)
            pygame.draw.rect(surface, (70, 75, 85), dd_rect, 1)
            clip = surface.get_clip()
            surface.set_clip(dd_rect)
            for i in range(vis):
                idx = self._scroll_offset + i
                if idx >= len(self._filtered):
                    break
                val, lbl = self._filtered[idx]
                ir = pygame.Rect(r.x, dy + i * ih, item_w, ih)
                sel = val == self._selected
                bg = (60, 65, 78) if sel else (45, 48, 56)
                pygame.draw.rect(surface, bg, ir)
                if i < vis - 1:
                    pygame.draw.line(surface, (70, 75, 85), (ir.x, ir.y + ih), (ir.x + ir.w, ir.y + ih))
                txt = fuente.render(lbl, True, (200, 200, 200))
                surface.blit(txt, (ir.x + 6, ir.y + (ih - txt.get_height()) // 2))
            if has_scroll:
                sb_x = r.x + r.w - sb_w
                track = pygame.Rect(sb_x, dy, sb_w, total_h)
                pygame.draw.rect(surface, (35, 38, 44), track)
                total = len(self._filtered)
                thumb_h = max(12, int(total_h * vis / total))
                max_scroll = total - vis
                thumb_y = dy + int((self._scroll_offset / max_scroll) * (total_h - thumb_h)) if max_scroll > 0 else dy
                thumb = pygame.Rect(sb_x + 1, thumb_y, sb_w - 2, thumb_h)
                pygame.draw.rect(surface, (100, 110, 125), thumb)
                pygame.draw.rect(surface, (130, 140, 155), thumb, 1)
            surface.set_clip(clip)


class _FakeInput:
    def __init__(self, default=""):
        self._text = default
    def get_text(self):
        return self._text


class _FakeDropdown:
    def __init__(self, default=""):
        self._selected = default
    def get_selected(self):
        return self._selected


def fake_input(default=""):
    return _FakeInput(default)


def fake_dd(default=""):
    return _FakeDropdown(default)
