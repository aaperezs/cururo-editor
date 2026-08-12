import pygame
from editor.translation import I18n
from editor.panels.base_panel import BasePanel
from editor.widgets.button import Button
from editor.widgets.label import Label
from editor.widgets.panel import Panel
from editor.widgets.text_input import TextInput
from editor.character_data import (
    get_characters, get_character, set_character, delete_character,
    create_character, get_character_list, is_protected
)

PADDING = 6
ROW_H = 28
TOOLBAR_H = 36
HEADER_H = 26
LEFT_W = 220
EMOCIONES_PRED = ("normal", "feliz", "triste", "enojado", "sonrojado", "sorpresa")


class CharacterPanel(BasePanel):
    def __init__(self, x, y, w, h, i18n):
        super().__init__(x, y, w, h, i18n)
        self.bg_color = (30, 32, 36)
        self._selected_id = None
        self._list_scroll = 0
        self._dirty = False
        self._build_ui()

    def _build_ui(self):
        self.clear()
        tb = Panel(0, 0, self.rect.w, TOOLBAR_H, bg_color=(42, 46, 55), border_color=(60, 65, 75))
        self.add(tb)
        self._new_btn = Button(8, 4, 72, 28, self.i18n.t("character.new"), callback=self._on_new)
        self._new_btn.parent = tb; tb.children.append(self._new_btn)
        self._clone_btn = Button(86, 4, 72, 28, self.i18n.t("character.clone"), callback=self._on_clone)
        self._clone_btn.parent = tb; tb.children.append(self._clone_btn)
        self._del_btn = Button(164, 4, 72, 28, self.i18n.t("character.delete"), callback=self._on_delete)
        self._del_btn.parent = tb; tb.children.append(self._del_btn)
        self._save_btn = Button(240, 4, 72, 28, self.i18n.t("character.save"), callback=self._on_save)
        self._save_btn.parent = tb; tb.children.append(self._save_btn)
        rx = LEFT_W
        rw = self.rect.w - rx
        cy = TOOLBAR_H
        ch = self.rect.h - cy
        self._editor_panel = Panel(rx, cy, rw, ch, bg_color=(35, 38, 46))
        self.add(self._editor_panel)
        self._build_editor_widgets()

    def _build_editor_widgets(self):
        ep = self._editor_panel
        ep.clear()
        y = PADDING

        self._eid_label = Label(PADDING, y, ep.rect.w - PADDING * 2, 20, "",
                                font_size=13, color=(200, 210, 220))
        self._eid_label.parent = ep; ep.children.append(self._eid_label)
        y += 26

        lbl = Label(PADDING, y, 100, 22, self.i18n.t("character.name") + ":",
                    font_size=12, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._name_input = TextInput(110, y, 200, 22, default="", max_chars=30, numeric_only=False)
        self._name_input.parent = ep; ep.children.append(self._name_input)
        y += 30

        lbl = Label(PADDING, y, 100, 22, self.i18n.t("character.color_text") + ":",
                    font_size=12, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        y += 22

        for ch_name, ch_key in [("R", 0), ("G", 1), ("B", 2)]:
            lbl = Label(PADDING + 10, y, 40, 22, ch_name + ":", font_size=11, color=(180, 185, 195))
            lbl.parent = ep; ep.children.append(lbl)
            inp = TextInput(55, y, 50, 22, default="255", max_chars=3, numeric_only=True)
            inp.parent = ep; ep.children.append(inp)
            setattr(self, f"_color_{ch_key}_input", inp)
            y += 24

        self._color_swatch = pygame.Rect(120, y - 56, 28, 28)

        sep = Panel(PADDING, y, ep.rect.w - PADDING * 2, 2, bg_color=(55, 60, 70))
        sep.parent = ep; ep.children.append(sep)
        y += 10

        lbl = Label(PADDING, y, 200, 18, self.i18n.t("character.portraits"),
                    font_size=12, bold=True, color=(200, 210, 220))
        lbl.parent = ep; ep.children.append(lbl)
        y += 24

        self._retrato_inputs = {}
        for emocion in EMOCIONES_PRED:
            lbl = Label(PADDING + 10, y, 80, 22, emocion + ":", font_size=11, color=(180, 185, 195))
            lbl.parent = ep; ep.children.append(lbl)
            inp = TextInput(100, y, 180, 22, default="", max_chars=60, numeric_only=False)
            inp.parent = ep; ep.children.append(inp)
            self._retrato_inputs[emocion] = inp
            y += 24

    def _on_new(self):
        base = "nuevo_personaje"
        cid = base
        n = 1
        while cid in get_characters():
            cid = f"{base}_{n}"
            n += 1
        create_character(cid)
        self._select_character(cid)

    def _on_clone(self):
        if not self._selected_id:
            return
        data = get_character(self._selected_id)
        if not data:
            return
        base = self._selected_id + "_copia"
        cid = base
        n = 1
        while cid in get_characters():
            cid = f"{base}_{n}"
            n += 1
        set_character(cid, data)
        self._select_character(cid)

    def _on_delete(self):
        if not self._selected_id:
            return
        if is_protected(self._selected_id):
            return
        delete_character(self._selected_id)
        self._selected_id = None
        self._dirty = True
        self._editor_panel.visible = False

    def _on_save(self):
        if not self._selected_id:
            return
        data = get_character(self._selected_id)
        if not data:
            return
        data["nombre"] = self._name_input.text or self._selected_id
        r = int(getattr(self, "_color_0_input").text or "255")
        g = int(getattr(self, "_color_1_input").text or "255")
        b = int(getattr(self, "_color_2_input").text or "255")
        data["color_texto"] = [r, g, b]
        retratos = {}
        for emocion, inp in self._retrato_inputs.items():
            val = inp.text.strip()
            if val:
                retratos[emocion] = val
        data["retratos"] = retratos
        set_character(self._selected_id, data)
        self._dirty = False
        self._select_character(self._selected_id)

    def _select_character(self, cid):
        self._selected_id = cid
        data = get_character(cid)
        if not data:
            self._editor_panel.visible = False
            return
        self._editor_panel.visible = True
        self._build_editor_widgets()
        self._eid_label.text = f"ID: {cid}" + (" " + self.i18n.t("character.protected") if is_protected(cid) else "")
        self._name_input.text = data.get("nombre", cid)
        color = data.get("color_texto", [255, 255, 255])
        for i in range(3):
            getattr(self, f"_color_{i}_input").text = str(color[i]) if i < len(color) else "255"
        retratos = data.get("retratos", {})
        for emocion, inp in self._retrato_inputs.items():
            inp.text = retratos.get(emocion, "")
        self._del_btn.enabled = not is_protected(cid)

    def handle_event(self, event):
        if not self.visible:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            r = self._get_list_rect()
            if r and r.collidepoint(mx, my):
                local_y = my - r.y + self._list_scroll
                idx = local_y // ROW_H
                all_chars = sorted(get_characters().keys())
                if 0 <= idx < len(all_chars):
                    self._select_character(all_chars[idx])
                    return True
        if event.type == pygame.MOUSEWHEEL:
            r = self._get_list_rect()
            mx, my = pygame.mouse.get_pos()
            if r and r.collidepoint(mx, my):
                all_chars = sorted(get_characters().keys())
                max_scroll = max(0, len(all_chars) * ROW_H - r.h)
                self._list_scroll = max(0, min(max_scroll, self._list_scroll - event.y * ROW_H))
                return True
        if self._editor_panel and self._editor_panel.visible:
            if self._editor_panel.handle_event(event):
                return True
        return super().handle_event(event)

    def _get_list_rect(self):
        ar = self.get_abs_rect()
        return pygame.Rect(ar.x, ar.y + TOOLBAR_H + HEADER_H, LEFT_W,
                           self.rect.h - TOOLBAR_H - HEADER_H)

    def draw(self, surface):
        if not self.visible:
            return
        super().draw(surface)
        ar = self.get_abs_rect()
        lx, ly = ar.x, ar.y + TOOLBAR_H
        lw, lh = LEFT_W, self.rect.h - TOOLBAR_H
        hdr = pygame.Rect(lx, ly, lw, HEADER_H)
        pygame.draw.rect(surface, (42, 46, 55), hdr)
        pygame.draw.rect(surface, (55, 60, 70), hdr, 1)
        i18n = I18n.instancia()
        fuente_b = i18n.fuente(12, bold=True) if i18n else pygame.font.SysFont("Arial", 12, bold=True)
        fuente = i18n.fuente(12) if i18n else pygame.font.SysFont("Arial", 12)
        txt = fuente_b.render(self.i18n.t("character.list"), True, (200, 210, 220))
        surface.blit(txt, (lx + PADDING, ly + (HEADER_H - txt.get_height()) // 2))
        cnt = len(get_characters())
        ctxt = fuente.render(f"({cnt})", True, (130, 140, 150))
        surface.blit(ctxt, (lx + lw - ctxt.get_width() - PADDING, ly + (HEADER_H - ctxt.get_height()) // 2))
        lr = self._get_list_rect()
        clip = surface.get_clip()
        surface.set_clip(lr)
        all_chars = sorted(get_characters().keys())
        for i, cid in enumerate(all_chars):
            sy = lr.y + i * ROW_H - self._list_scroll
            if sy + ROW_H < lr.y or sy > lr.y + lr.h:
                continue
            sel = cid == self._selected_id
            bg = (55, 60, 72) if sel else (38, 42, 50)
            pygame.draw.rect(surface, bg, (lr.x, sy, lr.w, ROW_H))
            if sel:
                pygame.draw.rect(surface, (70, 130, 200), (lr.x, sy, 3, ROW_H))
            data = get_character(cid)
            name = data.get("nombre", cid) if data else cid
            tc = (200, 210, 220) if sel else (160, 170, 180)
            txt = fuente.render(cid, True, tc)
            surface.blit(txt, (PADDING, sy + (ROW_H - txt.get_height()) // 2))
            nc = (130, 140, 150) if sel else (110, 120, 130)
            nt = fuente.render(f"({name})", True, nc)
            surface.blit(nt, (100, sy + (ROW_H - nt.get_height()) // 2))
            if is_protected(cid):
                lock = fuente.render("o", True, (200, 180, 60))
                surface.blit(lock, (lr.x + lr.w - 18, sy + (ROW_H - lock.get_height()) // 2))
        surface.set_clip(clip)
        # Color swatch
        if self._selected_id:
            r = int(getattr(self, "_color_0_input").text or "255") if hasattr(self, "_color_0_input") else 255
            g = int(getattr(self, "_color_1_input").text or "255") if hasattr(self, "_color_1_input") else 255
            b = int(getattr(self, "_color_2_input").text or "255") if hasattr(self, "_color_2_input") else 255
            r = max(0, min(255, r)); g = max(0, min(255, g)); b = max(0, min(255, b))
            ep = self._editor_panel
            swatch = pygame.Rect(ep.rect.x + 120, ep.rect.y + self._color_swatch.y, 28, 28)
            pygame.draw.rect(surface, (r, g, b), swatch)
            pygame.draw.rect(surface, (80, 90, 105), swatch, 1)
