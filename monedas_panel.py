import os
import shutil
import tkinter as tkinter
import tkinter.filedialog as fd

import pygame

from editor.panels.base_panel import BasePanel
from editor.widgets.button import Button
from editor.widgets.label import Label
from editor.widgets.panel import Panel
from editor.widgets.text_input import TextInput
from editor.project import get_current_project
from editor.monedas_data import (
    _load_monedas,
    get_monedas,
    set_monedas,
    validar_monedas,
)

PADDING = 6
ROW_H = 28
TOOLBAR_H = 36
HEADER_H = 26
LEFT_W = 220


class MonedasTab(BasePanel):
    """Editor de monedas (contadores de primera clase, data/monedas.json)."""

    def __init__(self, x, y, w, h, i18n):
        super().__init__(x, y, w, h, i18n)
        self.bg_color = (30, 32, 36)
        _load_monedas()
        self._monedas = get_monedas()
        self._selected_idx = None
        self._list_scroll = 0
        self._status_text = ""
        self._status_error = False
        self._build_ui()

    # ── Construcción ─────────────────────────────────────────

    def _build_ui(self):
        self.clear()
        self.mostrar_descripcion(
            self.i18n.t("tab.monedas.desc") if not self._monedas else ""
        )
        tb = Panel(0, 0, self.rect.w, TOOLBAR_H, bg_color=(42, 46, 55), border_color=(60, 65, 75))
        self.add(tb)
        self._new_btn = Button(8, 4, 72, 28, self.i18n.t("moneda.new"), callback=self._on_new)
        self._new_btn.parent = tb; tb.children.append(self._new_btn)
        self._clone_btn = Button(86, 4, 72, 28, self.i18n.t("moneda.clone"), callback=self._on_clone)
        self._clone_btn.parent = tb; tb.children.append(self._clone_btn)
        self._del_btn = Button(164, 4, 72, 28, self.i18n.t("moneda.delete"), callback=self._on_delete)
        self._del_btn.parent = tb; tb.children.append(self._del_btn)
        self._save_btn = Button(240, 4, 72, 28, self.i18n.t("moneda.save"), callback=self._on_save)
        self._save_btn.parent = tb; tb.children.append(self._save_btn)
        self._status_lbl = Label(320, 4, max(60, self.rect.w - 330), 28, "", font_size=12,
                                 color=(150, 200, 150))
        self._status_lbl.parent = tb; tb.children.append(self._status_lbl)

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
        self._inps = None
        self._id_input = None
        self._label_input = None
        self._valor_input = None
        self._icono_value = None
        self._icono_btn = None
        self._icono_clear_btn = None
        self._principal_btn = None
        for i in range(3):
            setattr(self, f"_color_{i}_input", None)
        y = PADDING

        if self._selected_idx is None or not (0 <= self._selected_idx < len(self._monedas)):
            ep.visible = False
            return
        ep.visible = True
        moneda = self._monedas[self._selected_idx]

        self._eid_label = Label(PADDING, y, ep.rect.w - PADDING * 2, 20,
                                f"ID: {moneda.get('id', '')}", font_size=13, color=(200, 210, 220))
        self._eid_label.parent = ep; ep.children.append(self._eid_label)
        y += 26

        lbl = Label(PADDING, y, 110, 22, self.i18n.t("moneda.id") + ":", font_size=12,
                    color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._id_input = TextInput(120, y, 220, 22, default=moneda.get("id", ""),
                                   max_chars=40, numeric_only=False)
        self._id_input.parent = ep; ep.children.append(self._id_input)
        y += 30

        lbl = Label(PADDING, y, 110, 22, self.i18n.t("moneda.label") + ":", font_size=12,
                    color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._label_input = TextInput(120, y, 220, 22, default=moneda.get("label", ""),
                                      max_chars=40, numeric_only=False)
        self._label_input.parent = ep; ep.children.append(self._label_input)
        y += 30

        lbl = Label(PADDING, y, 110, 22, self.i18n.t("moneda.valor_inicial") + ":", font_size=12,
                    color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._valor_input = TextInput(120, y, 100, 22, default=str(moneda.get("valor_inicial", 0)),
                                      max_chars=9, numeric_only=True)
        self._valor_input.parent = ep; ep.children.append(self._valor_input)
        y += 30

        lbl = Label(PADDING, y, 110, 22, self.i18n.t("moneda.icono") + ":", font_size=12,
                    color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._icono_value = Label(120, y, 150, 22, "", font_size=12, color=(200, 210, 220))
        self._icono_value.parent = ep; ep.children.append(self._icono_value)
        self._icono_btn = Button(274, y, 52, 22, "...", callback=self._on_pick_icono)
        self._icono_btn.parent = ep; ep.children.append(self._icono_btn)
        self._icono_clear_btn = Button(330, y, 28, 22, "X", callback=self._on_clear_icono)
        self._icono_clear_btn.parent = ep; ep.children.append(self._icono_clear_btn)
        self._icono_preview_rect = pygame.Rect(362, y, 22, 22)
        self._update_icono_label(moneda)
        y += 30

        lbl = Label(PADDING, y, 110, 22, self.i18n.t("moneda.color") + ":", font_size=12,
                    color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        y += 22
        color = moneda.get("color") or [0, 0, 0]
        if not isinstance(color, list) or len(color) != 3:
            color = [0, 0, 0]
        for ch_name, ch_idx in [("R", 0), ("G", 1), ("B", 2)]:
            lbl = Label(PADDING + 10, y, 40, 22, ch_name + ":", font_size=11, color=(180, 185, 195))
            lbl.parent = ep; ep.children.append(lbl)
            inp = TextInput(55, y, 50, 22, default=str(color[ch_idx]), max_chars=3, numeric_only=True)
            inp.parent = ep; ep.children.append(inp)
            setattr(self, f"_color_{ch_idx}_input", inp)
            y += 24
        self._color_swatch = pygame.Rect(120, y - 56, 28, 28)

        y += 10
        self._principal_btn = Button(PADDING, y, 160, 28, "", toggle=True,
                                     callback=self._on_toggle_principal)
        self._principal_btn.parent = ep; ep.children.append(self._principal_btn)
        self._principal_btn.toggled = bool(moneda.get("principal"))
        self._principal_btn.text = self._principal_label()
        y += 36

        sep = Panel(PADDING, y, ep.rect.w - PADDING * 2, 2, bg_color=(55, 60, 70))
        sep.parent = ep; ep.children.append(sep)
        y += 10
        self._hint_lbl = Label(PADDING, y, ep.rect.w - PADDING * 2, 20,
                               self.i18n.t("moneda.hint"), font_size=11, color=(130, 140, 150))
        self._hint_lbl.parent = ep; ep.children.append(self._hint_lbl)

    def _principal_label(self):
        if getattr(self, "_principal_btn", None) is None:
            return self.i18n.t("moneda.principal") + ": " + self.i18n.t("moneda.principal_no")
        if self._principal_btn.toggled:
            return self.i18n.t("moneda.principal") + ": " + self.i18n.t("moneda.principal_si")
        return self.i18n.t("moneda.principal") + ": " + self.i18n.t("moneda.principal_no")

    # ── Edición ──────────────────────────────────────────────

    def _commit_current(self):
        if self._selected_idx is None:
            return
        if not (0 <= self._selected_idx < len(self._monedas)):
            return
        moneda = self._monedas[self._selected_idx]
        if self._id_input is not None:
            moneda["id"] = self._id_input.text.strip()
            moneda["label"] = self._label_input.text.strip()
            moneda["valor_inicial"] = int(self._valor_input.text or "0")
            try:
                moneda["color"] = [
                    int(getattr(self, "_color_0_input").text or "0"),
                    int(getattr(self, "_color_1_input").text or "0"),
                    int(getattr(self, "_color_2_input").text or "0"),
                ]
            except ValueError:
                pass
            if self._principal_btn is not None and self._principal_btn.toggled:
                moneda["principal"] = True
                for otro in self._monedas:
                    if otro is not moneda:
                        otro["principal"] = False
            else:
                moneda["principal"] = False
        self._eid_label.text = f"ID: {moneda.get('id', '')}"

    # ── Ícono (sprite desde explorador de Windows) ──────────

    def _update_icono_label(self, moneda=None):
        if moneda is None and self._selected_idx is not None and 0 <= self._selected_idx < len(self._monedas):
            moneda = self._monedas[self._selected_idx]
        icono = (moneda or {}).get("icono", "")
        if getattr(self, "_icono_value", None):
            self._icono_value.text = icono or self.i18n.t("moneda.icono_ninguno")
            self._icono_value.color = (200, 210, 220) if icono else (130, 140, 150)

    def _on_pick_icono(self):
        self._commit_current()
        if self._selected_idx is None:
            return
        moneda = self._monedas[self._selected_idx]
        p = get_current_project()
        initial = p.assets_path() if p else None
        root = tkinter.Tk()
        root.withdraw()
        try:
            fpath = fd.askopenfilename(
                title=self.i18n.t("moneda.icono_dialog"),
                initialdir=initial,
                filetypes=[("PNG", "*.png")])
        finally:
            root.destroy()
        if not fpath:
            return
        sid = self._icono_asset_id(fpath)
        if not sid:
            self._set_status("! " + self.i18n.t("moneda.icono_invalido"), error=True)
            return
        moneda["icono"] = sid
        self._update_icono_label(moneda)

    def _on_clear_icono(self):
        self._commit_current()
        if self._selected_idx is None:
            return
        self._monedas[self._selected_idx]["icono"] = ""
        self._update_icono_label()

    def _icono_asset_id(self, fpath):
        """Devuelve el sprite_id (stem) del PNG elegido, copiándolo a assets/ si viene de fuera."""
        p = get_current_project()
        if not p or not os.path.exists(fpath):
            return None
        ext = os.path.splitext(fpath)[1].lower()
        if ext != ".png":
            return None
        assets_dir = os.path.normpath(p.assets_path())
        norm = os.path.normpath(os.path.abspath(fpath))
        stem = os.path.splitext(os.path.basename(fpath))[0]
        if norm.startswith(assets_dir + os.sep):
            return stem
        os.makedirs(assets_dir, exist_ok=True)
        dest = os.path.join(assets_dir, f"{stem}.png")
        if os.path.normpath(dest) != norm and os.path.exists(dest):
            base, n = stem, 1
            while os.path.exists(os.path.join(assets_dir, f"{base}_{n}.png")):
                n += 1
            dest = os.path.join(assets_dir, f"{base}_{n}.png")
            stem = f"{base}_{n}"
        try:
            shutil.copy2(fpath, dest)
        except (IOError, OSError):
            return None
        return stem

    def _set_status(self, text, error=False):
        self._status_text = text
        self._status_error = error
        lbl = getattr(self, "_status_lbl", None)
        if lbl:
            lbl.text = text
            lbl.color = (220, 120, 120) if error else (150, 200, 150)

    def _on_toggle_principal(self):
        btn = getattr(self, "_principal_btn", None)
        if btn:
            btn.text = self._principal_label()

    def _select(self, idx):
        self._commit_current()
        self._selected_idx = idx
        self._build_editor_widgets()

    # ── Acciones de toolbar ──────────────────────────────────

    def _on_new(self):
        self._commit_current()
        base = "moneda_nueva"
        mid = base
        n = 1
        existing = {m.get("id", "") for m in self._monedas}
        while mid in existing:
            mid = f"{base}_{n}"
            n += 1
        self._monedas.append({
            "id": mid,
            "label": mid,
            "valor_inicial": 0,
            "icono": "",
            "color": [255, 255, 255],
            "principal": False,
        })
        self._select(len(self._monedas) - 1)

    def _on_clone(self):
        if self._selected_idx is None:
            return
        self._commit_current()
        src = self._monedas[self._selected_idx]
        base = (src.get("id") or "moneda") + "_copia"
        mid = base
        n = 1
        existing = {m.get("id", "") for m in self._monedas}
        while mid in existing:
            mid = f"{base}_{n}"
            n += 1
        copia = dict(src)
        copia["id"] = mid
        copia["principal"] = False
        self._monedas.append(copia)
        self._select(len(self._monedas) - 1)

    def _on_delete(self):
        if self._selected_idx is None:
            return
        self._commit_current()
        if not (0 <= self._selected_idx < len(self._monedas)):
            return
        del self._monedas[self._selected_idx]
        self._selected_idx = None
        self._build_ui()

    def _on_save(self):
        self._commit_current()
        bloq, adv = validar_monedas(self._monedas)
        if bloq:
            self._set_status("! " + " · ".join(bloq), error=True)
            return
        set_monedas(self._monedas)
        if adv:
            self._set_status("! " + " · ".join(adv), error=False)
        else:
            self._set_status("OK", error=False)
        self._build_editor_widgets()

    # ── Eventos y dibujado ───────────────────────────────────

    def handle_event(self, event):
        if not self.visible:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            r = self._get_list_rect()
            if r and r.collidepoint(mx, my):
                local_y = my - r.y + self._list_scroll
                idx = local_y // ROW_H
                if 0 <= idx < len(self._monedas):
                    self._select(idx)
                    return True
        if event.type == pygame.MOUSEWHEEL:
            r = self._get_list_rect()
            mx, my = pygame.mouse.get_pos()
            if r and r.collidepoint(mx, my):
                max_scroll = max(0, len(self._monedas) * ROW_H - r.h)
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
        if self._descripcion:
            self.draw_descripcion(surface)
        ar = self.get_abs_rect()
        lx, ly = ar.x, ar.y + TOOLBAR_H
        lw, lh = LEFT_W, self.rect.h - TOOLBAR_H
        hdr = pygame.Rect(lx, ly, lw, HEADER_H)
        pygame.draw.rect(surface, (42, 46, 55), hdr)
        pygame.draw.rect(surface, (55, 60, 70), hdr, 1)
        from editor.translation import I18n
        i18n = I18n.instancia()
        fuente_b = i18n.fuente(12, bold=True) if i18n else pygame.font.SysFont("Arial", 12, bold=True)
        fuente = i18n.fuente(12) if i18n else pygame.font.SysFont("Arial", 12)
        txt = fuente_b.render(self.i18n.t("moneda.list"), True, (200, 210, 220))
        surface.blit(txt, (lx + PADDING, ly + (HEADER_H - txt.get_height()) // 2))
        cnt = len(self._monedas)
        ctxt = fuente.render(f"({cnt})", True, (130, 140, 150))
        surface.blit(ctxt, (lx + lw - ctxt.get_width() - PADDING, ly + (HEADER_H - ctxt.get_height()) // 2))
        lr = self._get_list_rect()
        clip = surface.get_clip()
        surface.set_clip(lr)
        for i, moneda in enumerate(self._monedas):
            sy = lr.y + i * ROW_H - self._list_scroll
            if sy + ROW_H < lr.y or sy > lr.y + lr.h:
                continue
            sel = i == self._selected_idx
            bg = (55, 60, 72) if sel else (38, 42, 50)
            pygame.draw.rect(surface, bg, (lr.x, sy, lr.w, ROW_H))
            if sel:
                pygame.draw.rect(surface, (70, 130, 200), (lr.x, sy, 3, ROW_H))
            mid = moneda.get("id", "")
            label = moneda.get("label") or mid
            tc = (200, 210, 220) if sel else (160, 170, 180)
            txt = fuente.render(mid, True, tc)
            surface.blit(txt, (PADDING, sy + (ROW_H - txt.get_height()) // 2))
            nc = (130, 140, 150) if sel else (110, 120, 130)
            nt = fuente.render(f"({label})", True, nc)
            surface.blit(nt, (100, sy + (ROW_H - nt.get_height()) // 2))
            if moneda.get("principal"):
                star = fuente.render("*", True, (200, 180, 60))
                surface.blit(star, (lr.x + lr.w - 18, sy + (ROW_H - star.get_height()) // 2))
        surface.set_clip(clip)
        # Color swatch
        if self._selected_idx is not None and 0 <= self._selected_idx < len(self._monedas):
            try:
                r = max(0, min(255, int(getattr(self, "_color_0_input").text or "0")))
                g = max(0, min(255, int(getattr(self, "_color_1_input").text or "0")))
                b = max(0, min(255, int(getattr(self, "_color_2_input").text or "0")))
            except ValueError:
                r, g, b = 0, 0, 0
            ep = self._editor_panel
            swatch = pygame.Rect(ep.rect.x + 120, ep.rect.y + self._color_swatch.y, 28, 28)
            pygame.draw.rect(surface, (r, g, b), swatch)
            pygame.draw.rect(surface, (80, 90, 105), swatch, 1)
            # Preview del ícono (sprite)
            pr = getattr(self, "_icono_preview_rect", None)
            if pr:
                icono = self._monedas[self._selected_idx].get("icono", "")
                p = get_current_project()
                fpath = p.assets_path(f"{icono}.png") if icono and p else None
                thumb = None
                if fpath and os.path.exists(fpath):
                    try:
                        thumb = pygame.image.load(fpath).convert_alpha()
                    except Exception:
                        thumb = None
                prect = pygame.Rect(ep.rect.x + pr.x, ep.rect.y + pr.y, pr.w, pr.h)
                pygame.draw.rect(surface, (45, 50, 60), prect)
                pygame.draw.rect(surface, (80, 90, 105), prect, 1)
                if thumb:
                    escala = min(prect.w / thumb.get_width(), prect.h / thumb.get_height())
                    tw = max(1, int(thumb.get_width() * escala))
                    th = max(1, int(thumb.get_height() * escala))
                    t = pygame.transform.scale(thumb, (tw, th))
                    surface.blit(t, (prect.x + (prect.w - tw) // 2, prect.y + (prect.h - th) // 2))
