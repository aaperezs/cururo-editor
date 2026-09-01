import pygame
import pygame_gui

from editor.translation import I18n
from editor.widgets.simple_dropdown import SimpleDropdown
from editor.widgets.label import Label
from editor.widgets.text_input import TextInput
from editor.widgets.button import Button
from editor.panels.base_panel import BasePanel
from editor.pygame_gui_theme import create_gui
from editor.dialog_data import (
    get_all_dialogo_keys, get_dialogo_by_key, set_dialogo_by_key,
    delete_dialogo_by_key, create_dialogo_by_key, rename_dialogo,
    get_dialogo_options_by_key, set_dialogo_options_by_key, delete_dialogo_options_by_key,
    get_tree, get_tree_by_key, set_tree_by_key, create_tree_key, add_node, remove_node,
    compile_to_flat, NODE_LABELS, NODE_COLORS, NODE_DEFAULTS,
    _parse_key, _make_key,
)

PADDING = 6
TOOLBAR_H = 36
LEFT_W = 220
NODE_H = 30
NODE_INDENT = 20
MAX_CHOICES = 5

# Área del árbol: 3.5 filas visibles + scrollbar; el detalle ocupa el resto.
TREE_VISIBLE_ROWS = 3.5
TREE_H = int(TREE_VISIBLE_ROWS * NODE_H)  # 105
TREE_TOP_OFFSET = 28
SCROLLBAR_W = 10
DETAIL_TOP = TREE_TOP_OFFSET + TREE_H  # 133

# Campos de parámetros dinámicos por acción (key de la choice -> etiqueta)
OPTION_ACTION_FIELDS = {
    "start_dialog": [("dialog", "Dialogo:")],
    "start_dialogue": [("dialogo_id", "Dialogo ID:")],
    "iniciar_dialogo": [("dialogo_id", "Dialogo ID:")],
    "open_shop": [("shop_id", "Shop:")],
    "close_dialog": [],
    "close_shop": [],
    "give_item": [("item", "Item:"), ("cantidad", "Cantidad:")],
    "remove_item": [("item", "Item:"), ("cantidad", "Cantidad:")],
    "give_moneda": [("moneda", "Moneda:"), ("cantidad", "Cantidad:")],
    "remove_moneda": [("moneda", "Moneda:"), ("cantidad", "Cantidad:")],
    "set_flag": [("flag", "Flag:"), ("valor", "Valor:")],
    "add_flag": [("flag", "Flag:"), ("cantidad", "Cantidad:")],
    "clear_flag": [("flag", "Flag:")],
    "show_message": [("mensaje", "Mensaje:")],
    "play_bgm": [("asset_id", "Asset:"), ("fade_ms", "Fade (ms):")],
    "play_sfx": [("asset_id", "Asset:")],
    "stop_bgm": [("fade_ms", "Fade (ms):")],
    "set_volume": [("volumen", "Volumen:")],
    "set_bgm_volume": [("volumen", "Volumen:")],
    "set_sfx_volume": [("volumen", "Volumen:")],
    "change_map": [("nivel", "Nivel:"), ("exit_id", "Exit ID:")],
    "abrir_menu": [("menu_id", "Menu:")],
    "esperar": [("segundos", "Segundos:")],
    "mover_a": [("evento_id", "Evento ID:")],
    "cambiar_skin": [("skin", "Skin:")],
    "equipar_habilidad": [("habilidad", "Habilidad:")],
    "desbloquear_habilidad": [("habilidad", "Habilidad:")],
    "increment_contador": [("contador_id", "Contador:"), ("cantidad", "Cantidad:")],
    "set_contador": [("contador_id", "Contador:"), ("valor", "Valor:")],
    "save_game": [("slot", "Slot:")],
    "load_game": [("slot", "Slot:")],
    "iniciar_minijuego": [("minijuego_id", "Minijuego:")],
    "ir_a_escena": [("capitulo", "Capítulo:"), ("escena", "Escena:")],
    "mostrar_ventana": [("ventana_id", "Ventana:")],
    "restock_shop": [("shop_id", "Shop:"), ("item_id", "Item:")],
    "add_shop_stock": [("shop_id", "Shop:"), ("item_id", "Item:"), ("cantidad", "Cantidad:")],
    "modify_shop_price": [("shop_id", "Shop:"), ("item_id", "Item:"),
                          ("moneda", "Moneda:"), ("precio", "Precio:")],
    "damage": [("cantidad", "Cantidad:"), ("mensaje", "Mensaje:")],
    "remove_escamas": [("cantidad", "Cantidad:")],
    "consume_pp": [("cantidad", "Cantidad:")],
    "comando_automatico": [("comando", "Comando:")],
    "bloquear_eventos": [("bloquear", "Bloquear:")],
    "bloquear_mandos": [("bloquear", "Bloquear:")],
    "cambiar_fondo": [("sprite_id", "Sprite:")],
    "mostrar_personaje": [("personaje_id", "Personaje:"), ("posicion", "Posición:"),
                          ("expresion", "Expresión:")],
    "ocultar_personaje": [("personaje_id", "Personaje:")],
}

OPTION_ACTION_OPTIONS = sorted(OPTION_ACTION_FIELDS.keys())

# Params que solo aceptan dígitos
NUMERIC_PARAMS = {"cantidad", "fade_ms", "volumen", "segundos", "valor", "precio"}

# Params con dropdown de datos reales (None = no aplica dropdown)
DATA_PARAM_SOURCES = {
    "dialog": "dialogos",
    "dialogo_id": "dialogos",
    "shop_id": "shops",
    "item": "items",
    "item_id": "items",
    "moneda": "monedas",
    "nivel": "mapas",
    "skin": "skins",
    "habilidad": "habilidades",
    "ventana_id": "ventanas",
    "bloquear": "booleano",
    "sprite_id": "sprites",
    "contador_id": "contadores",
    "menu_id": "menus",
}


def _param_data_options(pkey):
    """Devuelve [(valor, etiqueta)] para un param de acción, o None si no es dropdown.

    Devuelve [] si el param es de datos pero su lista está vacía (no se puede
    crear la opción hasta que haya elementos).
    """
    source = DATA_PARAM_SOURCES.get(pkey)
    if source is None:
        return None
    try:
        if source == "dialogos":
            from editor.dialog_data import _load_dialogos
            _load_dialogos()
            return [(k, k) for k in get_all_dialogo_keys()]
        if source == "shops":
            from editor.shops_data import _load_shops, get_all_shops
            _load_shops()
            shops = sorted(get_all_shops())
            if not shops:
                return []
            return [("", "(ninguna)")] + [(s, s) for s in shops]
        if source == "items":
            from editor.items_data import _load_items, get_item_list
            _load_items()
            return get_item_list()
        if source == "monedas":
            from editor.monedas_data import _load_monedas, get_monedas
            _load_monedas()
            return [(m.get("id", ""), m.get("label") or m.get("id", "")) for m in get_monedas()]
        if source == "mapas":
            from editor.widgets.event_constants import get_map_list
            return get_map_list()
        if source == "skins":
            from editor.ability_data import _load_abilities, get_skin_list
            _load_abilities()
            return get_skin_list()
        if source == "habilidades":
            from editor.ability_data import _load_abilities, get_ability_list
            _load_abilities()
            return get_ability_list()
        if source == "ventanas":
            from editor.widgets.event_constants import get_param_options
            return get_param_options("ventana_id")
        if source == "booleano":
            return [("True", "Bloquear"), ("False", "Desbloquear")]
        if source == "sprites":
            from editor.sprite_registry import get_sprite_options
            return get_sprite_options()
        if source == "contadores":
            from editor.contadores_data import _load_contadores, get_all_contadores
            _load_contadores()
            return [(c, c) for c in get_all_contadores()]
        if source == "menus":
            from editor.menu.data import _load_menus, get_all_menus
            _load_menus()
            return [(m, m) for m in get_all_menus()]
    except Exception:
        return []
    return []


class DialogTreePanel(BasePanel):
    def __init__(self, x, y, w, h, i18n):
        super().__init__(0, 0, w, h, i18n)
        self.bg_color = (30, 32, 36)
        self._gui = create_gui((w, h), offset_getter=lambda: (
            self.get_abs_rect().x, self.get_abs_rect().y
        ))
        self._selected_key = None
        self._selected_nid = None
        self._selected_flat_idx = None
        self._selected_child = None
        self._selected_choice = None
        self._tree_scroll = 0
        self._options_scroll = 0
        self._action_rebuild = False
        self._dirty = False
        self._node_widgets = {}
        self._detail_widgets = {}
        self._dropdown_host = _DropdownHost(None)
        self._options_host = _DropdownHost(None)
        self._options_top = None
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
        self._dropdown_host = _DropdownHost(self._editor_panel)
        self._options_host = _DropdownHost(self._editor_panel)
        self._options_top = None
        y = DETAIL_TOP
        ew = ep.rect.w

        if self._selected_flat_idx is not None:
            flat = get_dialogo_by_key(self._selected_key)
            if flat and self._selected_flat_idx < len(flat):
                lbl = pygame_gui.elements.UILabel(
                    pygame.Rect(PADDING, y, ew - PADDING * 2, 18),
                    f"Línea {self._selected_flat_idx + 1}/{len(flat)}", self._gui, container=ep
                )
                self._detail_widgets["type_label"] = lbl
                y += 24
                inp = pygame_gui.elements.UITextEntryLine(
                    pygame.Rect(PADDING, y, ew - PADDING * 2, 22),
                    initial_text=flat[self._selected_flat_idx],
                    manager=self._gui, container=ep
                )
                self._detail_widgets["flat_text"] = inp
                y += 28
                up_btn = pygame_gui.elements.UIButton(
                    pygame.Rect(PADDING, y, 80, 22), "Subir", self._gui, container=ep
                )
                self._detail_widgets["flat_up"] = up_btn
                down_btn = pygame_gui.elements.UIButton(
                    pygame.Rect(PADDING + 86, y, 80, 22), "Bajar", self._gui, container=ep
                )
                self._detail_widgets["flat_down"] = down_btn
                add_btn = pygame_gui.elements.UIButton(
                    pygame.Rect(PADDING + 172, y, 80, 22), "+ Línea", self._gui, container=ep
                )
                self._detail_widgets["flat_add"] = add_btn
            return

        if self._selected_child == "options":
            options = get_dialogo_options_by_key(self._selected_key)
            if not options:
                options = [{"text": "", "choices": []}]
            opt = options[0]
            choices = opt.get("choices", [])
            cy = y

            save_btn = Button(PADDING, y, 70, 22, text="Guardar",
                              callback=self._on_save)
            self._detail_widgets["opt_save"] = save_btn
            self._dropdown_host.add(save_btn)
            y += 26

            lbl = Label(PADDING, y, 76, 22, "Pregunta:")
            self._detail_widgets["l_opt_pregunta"] = lbl
            self._dropdown_host.add(lbl)
            inp = TextInput(PADDING + 82, y, ew - PADDING * 2 - 82, 22,
                            default=opt.get("text", ""), max_chars=200, numeric_only=False)
            self._detail_widgets["opt_pregunta"] = inp
            self._dropdown_host.add(inp)
            y += 26

            add_btn = Button(PADDING, y, 110, 22, text="Agregar Opción",
                             callback=self._add_option_choice)
            self._detail_widgets["opt_add_choice"] = add_btn
            self._dropdown_host.add(add_btn)
            del_btn = Button(PADDING + 118, y, 160, 22, text="Eliminar Pregunta",
                             color=(120, 50, 50), hover_color=(150, 70, 70),
                             callback=self._delete_option_question)
            self._detail_widgets["opt_del_question"] = del_btn
            self._dropdown_host.add(del_btn)
            y += 26

            sep = Label(PADDING, y, ew - PADDING * 2, 18, "─── opciones ───",
                        color=(120, 130, 145), font_size=12)
            self._detail_widgets["l_opt_sep"] = sep
            self._dropdown_host.add(sep)
            y += 22

            self._options_top = y
            cy = y
            scroll = self._options_scroll
            n = len(choices)
            total_filas = sum(
                2 + len(OPTION_ACTION_FIELDS.get(ch.get("action", ""), []))
                for ch in choices
            )
            has_oscroll = total_filas * 24 > (ep.rect.h - y)
            ozw = ew - (SCROLLBAR_W if has_oscroll else 0)

            for ci, ch in enumerate(choices):
                lbl = Label(PADDING, y - scroll, 66, 22, f"Opción {ci + 1}:")
                self._detail_widgets[f"choice_hdr_{ci}"] = lbl
                self._options_host.add(lbl)
                inp = TextInput(PADDING + 72, y - scroll, ozw - PADDING * 2 - 72 - 92, 22,
                                default=ch.get("text", ""), max_chars=200, numeric_only=False)
                self._detail_widgets[f"choice_text_{ci}"] = inp
                self._options_host.add(inp)
                bx = ozw - 26
                if ci < n - 1:
                    dn = Button(bx, y - scroll, 20, 20, text="▼",
                                callback=lambda c=ci: self._move_option_choice(c, 1))
                    self._detail_widgets[f"choice_down_{ci}"] = dn
                    self._options_host.add(dn)
                    bx -= 24
                if ci > 0:
                    up = Button(bx, y - scroll, 20, 20, text="▲",
                                callback=lambda c=ci: self._move_option_choice(c, -1))
                    self._detail_widgets[f"choice_up_{ci}"] = up
                    self._options_host.add(up)
                    bx -= 24
                del_btn = Button(bx, y - scroll, 20, 20, text="✕",
                                 callback=lambda c=ci: self._remove_option_choice(c))
                self._detail_widgets[f"choice_del_{ci}"] = del_btn
                self._options_host.add(del_btn)
                y += 24

                albl = Label(PADDING + 16, y - scroll, 56, 22, "Acción:")
                self._detail_widgets[f"l_choice_action_{ci}"] = albl
                self._options_host.add(albl)
                opts = [(a, a) for a in OPTION_ACTION_OPTIONS]
                dd = SimpleDropdown(PADDING + 76, y - scroll, ozw - PADDING * 2 - 76, 22,
                                    opts, selected=ch.get("action", ""))
                dd._on_select = (lambda val, c=ci: self._on_choice_action_changed(c, val))
                self._detail_widgets[f"choice_action_{ci}"] = dd
                self._options_host.add(dd)
                y += 24

                action = ch.get("action", "")
                for pkey, plabel in OPTION_ACTION_FIELDS.get(action, []):
                    lbl = Label(PADDING + 32, y - scroll, 100, 22, plabel)
                    self._detail_widgets[f"l_choice_param_{ci}_{pkey}"] = lbl
                    self._options_host.add(lbl)
                    w = self._make_param_widget(
                        PADDING + 136, y - scroll, ozw - PADDING * 2 - 136, 22,
                        pkey, ch.get(pkey, ""),
                    )
                    self._detail_widgets[f"choice_param_{ci}_{pkey}"] = w
                    self._options_host.add(w)
                    y += 24

            self._detail_content_h = y - cy
            return

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
            dd = SimpleDropdown(70, y, ew - 80, 22, opts, selected=node.get("next", ""))
            self._detail_widgets["next"] = dd
            y += 28

        elif tipo == "opcion":
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
            choices = node.get("choices", [])
            for ci, ch in enumerate(choices):
                lbl = pygame_gui.elements.UILabel(
                    pygame.Rect(PADDING, y, 20, 22), f"{ci+1}:", self._gui, container=ep
                )
                self._detail_widgets[f"l_choice_{ci}"] = lbl
                inp = pygame_gui.elements.UITextEntryLine(
                    pygame.Rect(30, y, ew - 160, 22),
                    initial_text=ch.get("texto", ""),
                    manager=self._gui, container=ep
                )
                self._detail_widgets[f"choice_text_{ci}"] = inp
                nids = [n for n in tree["nodes"].keys() if n != self._selected_nid]
                opts = [("", "(ninguno)")] + [(n, n) for n in sorted(nids)]
                dd = SimpleDropdown(ew - 120, y, 90, 22, opts, selected=ch.get("next", ""))
                self._detail_widgets[f"choice_next_{ci}"] = dd
                del_btn = pygame_gui.elements.UIButton(
                    pygame.Rect(ew - 26, y, 22, 22), "X", self._gui, container=ep
                )
                self._detail_widgets[f"choice_del_{ci}"] = del_btn
                y += 28
            add_btn = pygame_gui.elements.UIButton(
                pygame.Rect(PADDING, y, 90, 22), "+ Choice", self._gui, container=ep
            )
            self._detail_widgets["choice_add"] = add_btn

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
                    dd = SimpleDropdown(x, y, fw - 4, 22, opts, selected=node.get("operador", "=="))
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
            dd = SimpleDropdown(90, y, ew - 100, 22, opts, selected=node.get("next", ""))
            self._detail_widgets["next"] = dd
            y += 28
            lbl2 = pygame_gui.elements.UILabel(
                pygame.Rect(PADDING, y, 80, 22), "Si falso:", self._gui, container=ep
            )
            self._detail_widgets["l_next_false"] = lbl2
            dd2 = SimpleDropdown(90, y, ew - 100, 22, opts, selected=node.get("next_false", ""))
            self._detail_widgets["next_false"] = dd2

        elif tipo == "accion":
            opts = [
                ("set_flag", "set_flag"),
                ("add_flag", "add_flag"),
                ("cambiar_fondo", "cambiar_fondo"),
                ("mostrar_personaje", "mostrar_personaje"),
                ("ocultar_personaje", "ocultar_personaje"),
                ("ocultar_todos_personajes", "ocultar_todos_personajes"),
                ("open_shop", "open_shop"),
                ("close_shop", "close_shop"),
            ]
            lbl = pygame_gui.elements.UILabel(
                pygame.Rect(PADDING, y, 80, 22), "Acción:", self._gui, container=ep
            )
            self._detail_widgets["l_tipo_accion"] = lbl
            dd = SimpleDropdown(90, y, ew - 100, 22, opts, selected=node.get("tipo_accion", "set_flag"))
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
            dd = SimpleDropdown(90, y, ew - 100, 22, opts, selected=node.get("next", ""))
            self._detail_widgets["next"] = dd

        elif tipo == "salto":
            lbl = pygame_gui.elements.UILabel(
                pygame.Rect(PADDING, y, 80, 22), "Destino:", self._gui, container=ep
            )
            self._detail_widgets["l_destino"] = lbl
            opts = [("", "(seleccionar)")] + [(k, k) for k in get_all_dialogo_keys()]
            dd = SimpleDropdown(90, y, ew - 100, 22, opts, selected=node.get("destino", ""))
            self._detail_widgets["destino"] = dd

        for w in self._detail_widgets.values():
            if isinstance(w, SimpleDropdown):
                self._dropdown_host.add(w)

    # ── Tree rendering ──

    def _get_tree_rect(self):
        ar = self.get_abs_rect()
        ep = self._editor_panel
        return pygame.Rect(ar.x + ep.rect.x, ar.y + ep.rect.y + TREE_TOP_OFFSET,
                           ep.rect.w, TREE_H)

    def _get_detail_rect(self):
        ar = self.get_abs_rect()
        ep = self._editor_panel
        return pygame.Rect(ar.x + ep.rect.x, ar.y + ep.rect.y + DETAIL_TOP,
                           ep.rect.w, ep.rect.h - DETAIL_TOP)

    def _get_options_rect(self):
        ar = self.get_abs_rect()
        ep = self._editor_panel
        top = self._options_top
        if top is None:
            return None
        return pygame.Rect(ar.x + ep.rect.x, ar.y + ep.rect.y + top,
                           ep.rect.w, ep.rect.h - top)

    def _tree_total_rows(self):
        tree = get_tree_by_key(self._selected_key)
        if tree:
            return len(tree["nodes"])
        filas = len(get_dialogo_by_key(self._selected_key) or [])
        if get_dialogo_options_by_key(self._selected_key):
            filas += 1
        return filas

    def _draw_tree(self, surface):
        if not self._selected_key:
            return
        tree = get_tree_by_key(self._selected_key)
        flat = get_dialogo_by_key(self._selected_key)

        tr = self._get_tree_rect()
        total = self._tree_total_rows()
        has_scroll = total * NODE_H > tr.h
        tw = tr.w - (SCROLLBAR_W if has_scroll else 0)
        clip = surface.get_clip()
        surface.set_clip(tr)

        i18n = I18n.instancia()
        fuente = i18n.fuente(11) if i18n else pygame.font.SysFont("Arial", 11)

        if tree:
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
                    self._draw_node(surface, tr.x, sy, tw, nid, nodes[nid])
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
        elif flat or get_dialogo_options_by_key(self._selected_key):
            options = get_dialogo_options_by_key(self._selected_key)
            for i, line in enumerate(flat):
                sy = tr.y + i * NODE_H - self._tree_scroll
                if sy + NODE_H >= tr.y and sy <= tr.y + tr.h:
                    sel = i == self._selected_flat_idx
                    bg = (55, 60, 78) if sel else (45, 48, 56)
                    pygame.draw.rect(surface, bg, (tr.x, sy, tw, NODE_H))
                    pygame.draw.rect(surface, (70, 75, 85), (tr.x, sy, tw, NODE_H), 1)
                    if sel:
                        pygame.draw.rect(surface, (70, 130, 200), (tr.x, sy, 3, NODE_H))
                    badge = pygame.Rect(tr.x + 4, sy + 4, 60, NODE_H - 8)
                    pygame.draw.rect(surface, (70, 130, 200), badge, border_radius=3)
                    lbl_s = fuente.render("Dialogo", True, (255, 255, 255))
                    surface.blit(lbl_s, (badge.x + (badge.w - lbl_s.get_width()) // 2,
                                         badge.y + (badge.h - lbl_s.get_height()) // 2))
                    txt = line if isinstance(line, str) else str(line)
                    prev_s = fuente.render(txt, True, (180, 190, 200))
                    surface.blit(prev_s, (tr.x + 72, sy + (NODE_H - prev_s.get_height()) // 2))
                    self._node_widgets[f"flat_{i}"] = {
                        "rect": pygame.Rect(tr.x, sy, tw, NODE_H),
                        "del_rect": pygame.Rect(tr.x + tw - 22, sy + 4, 18, NODE_H - 8),
                        "flat_idx": i,
                    }
            if options:
                oi = len(flat)
                sy = tr.y + oi * NODE_H - self._tree_scroll
                if sy + NODE_H >= tr.y and sy <= tr.y + tr.h:
                    sel = self._selected_child == "options"
                    bg = (55, 60, 78) if sel else (45, 48, 56)
                    pygame.draw.rect(surface, bg, (tr.x, sy, tw, NODE_H))
                    pygame.draw.rect(surface, (70, 75, 85), (tr.x, sy, tw, NODE_H), 1)
                    if sel:
                        pygame.draw.rect(surface, (200, 180, 60), (tr.x, sy, 3, NODE_H))
                    badge = pygame.Rect(tr.x + 4, sy + 4, 60, NODE_H - 8)
                    pygame.draw.rect(surface, (200, 180, 60), badge, border_radius=3)
                    lbl_s = fuente.render("Options", True, (255, 255, 255))
                    surface.blit(lbl_s, (badge.x + (badge.w - lbl_s.get_width()) // 2,
                                         badge.y + (badge.h - lbl_s.get_height()) // 2))
                    preview = ""
                    if options:
                        preg = options[0].get("text", "")
                        nch = len(options[0].get("choices", []))
                        preview = f"{preg} ({nch} choices)"
                    prev_s = fuente.render(preview, True, (180, 190, 200))
                    surface.blit(prev_s, (tr.x + 72, sy + (NODE_H - prev_s.get_height()) // 2))
                    self._node_widgets["options"] = {
                        "rect": pygame.Rect(tr.x, sy, tw, NODE_H),
                        "del_rect": pygame.Rect(tr.x + tw - 22, sy + 4, 18, NODE_H - 8),
                        "child": "options",
                    }

        if has_scroll:
            sb_x = tr.x + tr.w - SCROLLBAR_W
            track = pygame.Rect(sb_x, tr.y, SCROLLBAR_W, tr.h)
            pygame.draw.rect(surface, (35, 38, 44), track)
            thumb_h = max(12, int(tr.h * tr.h / (total * NODE_H)))
            max_scroll = max(0, total * NODE_H - tr.h)
            thumb_y = (
                tr.y + int((self._tree_scroll / max_scroll) * (tr.h - thumb_h))
                if max_scroll > 0
                else tr.y
            )
            thumb = pygame.Rect(sb_x + 1, thumb_y, SCROLLBAR_W - 2, thumb_h)
            pygame.draw.rect(surface, (100, 110, 125), thumb)
            pygame.draw.rect(surface, (130, 140, 155), thumb, 1)

        surface.set_clip(clip)

    def _draw_node(self, surface, x, y, w, nid, node):
        tipo = node.get("tipo", "")
        color = NODE_COLORS.get(tipo, (100, 100, 100))
        label = NODE_LABELS.get(tipo, tipo)
        preview = ""
        if tipo == "dialogo":
            preview = node.get("texto", "")[:150]
        elif tipo == "opcion":
            preview = node.get("texto", "")[:60]
            choices = " / ".join(c.get("texto", "?")[:20] for c in node.get("choices", []))
            if preview and choices:
                preview = f"{preview} [{choices}]"
            elif not preview:
                preview = choices
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
        self._save_current_flat_line()
        self._save_current_options()
        self._save_current_node()
        # Also save flat version for legacy runtime
        flat = compile_to_flat(*_parse_key(self._selected_key))
        set_dialogo_by_key(self._selected_key, flat)
        self._dirty = False
        self._build_ui()

    def persistir_dialogos(self):
        """Persiste en disco el estado actual de los diálogos sin rebuild de UI.

        Usado por el Guardar global de la ventana (Ctrl+S / save_workspace).
        """
        if self._selected_key:
            self._save_current_flat_line()
            self._save_current_options()
            self._save_current_node()
            flat = compile_to_flat(*_parse_key(self._selected_key))
            set_dialogo_by_key(self._selected_key, flat)
            self._dirty = False

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
            node["texto"] = self._detail_widgets.get("texto", fake_input("")).get_text()
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
        self._save_current_node()
        p, c = _parse_key(self._selected_key)
        create_tree_key(p, c)
        nid = add_node(p, c, tipo, after_id=self._selected_nid)
        if nid:
            self._selected_nid = nid
            self._build_ui()

    def _add_choice(self):
        if not self._selected_key or not self._selected_nid:
            return
        self._save_current_node()
        tree = get_tree_by_key(self._selected_key)
        if not tree or self._selected_nid not in tree["nodes"]:
            return
        node = tree["nodes"][self._selected_nid]
        if node["tipo"] != "opcion":
            return
        node.setdefault("choices", []).append({"texto": "", "next": ""})
        set_tree_by_key(self._selected_key, tree)
        self._dirty = True
        self._build_ui()

    def _remove_choice(self, idx):
        if not self._selected_key or not self._selected_nid:
            return
        self._save_current_node()
        tree = get_tree_by_key(self._selected_key)
        if not tree or self._selected_nid not in tree["nodes"]:
            return
        node = tree["nodes"][self._selected_nid]
        if node["tipo"] != "opcion":
            return
        choices = node.get("choices", [])
        if 0 <= idx < len(choices):
            choices.pop(idx)
        set_tree_by_key(self._selected_key, tree)
        self._dirty = True
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
        self._save_current_flat_line()
        self._save_current_options()
        self._save_current_node()
        self._selected_nid = nid
        self._selected_flat_idx = None
        self._selected_choice = None
        self._options_scroll = 0
        self._build_ui()

    def _save_current_flat_line(self):
        if self._selected_flat_idx is None or not self._selected_key:
            return
        flat = get_dialogo_by_key(self._selected_key)
        if not flat or self._selected_flat_idx >= len(flat):
            return
        inp = self._detail_widgets.get("flat_text")
        if inp:
            flat[self._selected_flat_idx] = inp.get_text()
            set_dialogo_by_key(self._selected_key, flat)
            self._dirty = True

    def _save_current_options(self):
        if self._selected_child != "options" or not self._selected_key:
            return
        options = get_dialogo_options_by_key(self._selected_key)
        if not options:
            options = [{"text": "", "choices": []}]
        opt = options[0]
        inp = self._detail_widgets.get("opt_pregunta")
        if inp:
            opt["text"] = inp.get_text()
        choices = []
        for key, w in list(self._detail_widgets.items()):
            if key.startswith("choice_text_"):
                ci = int(key.split("_")[2])
                while len(choices) <= ci:
                    choices.append({"text": "", "action": ""})
                choices[ci]["text"] = w.get_text()
            elif key.startswith("choice_action_"):
                ci = int(key.split("_")[2])
                while len(choices) <= ci:
                    choices.append({"text": "", "action": ""})
                choices[ci]["action"] = w.get_selected()
            elif key.startswith("choice_param_"):
                parts = key.split("_")
                ci = int(parts[2])
                pkey = "_".join(parts[3:])
                while len(choices) <= ci:
                    choices.append({"text": "", "action": ""})
                choices[ci][pkey] = w.get_selected() if isinstance(w, SimpleDropdown) else w.get_text()
        opt["choices"] = choices
        set_dialogo_options_by_key(self._selected_key, options)
        self._dirty = True

    def _on_choice_action_changed(self, ci, val=None):
        prev = self._current_choice_action(ci)
        if val and self._action_has_empty_data(val):
            self.notify(
                f"La acción '{val}' requiere datos que están vacíos. No se puede "
                "crear esta opción hasta que la lista tenga algún elemento.",
                "error",
            )
            dd = self._detail_widgets.get(f"choice_action_{ci}")
            if dd:
                dd.set_selected(prev)
            return
        self._save_current_options()
        self._selected_choice = ci
        self._action_rebuild = True

    def _current_choice_action(self, ci):
        options = get_dialogo_options_by_key(self._selected_key) if self._selected_key else None
        if not options:
            return ""
        choices = options[0].get("choices", [])
        if 0 <= ci < len(choices):
            return choices[ci].get("action", "")
        return ""

    def _action_has_empty_data(self, action):
        for pkey, _plabel in OPTION_ACTION_FIELDS.get(action, []):
            if pkey in DATA_PARAM_SOURCES:
                opts = _param_data_options(pkey)
                if opts == []:
                    return True
        return False

    def _make_param_widget(self, x, y, w, h, pkey, value):
        """Crea el widget dinámico para un param de acción.

        - Param de datos (tienda/item/moneda/...): SimpleDropdown con datos reales.
          Si la lista está vacía, notifica error y devuelve un dropdown bloqueado
          ("(vacío)") para que no se pueda guardar la opción.
        - Param numérico: TextInput que solo acepta dígitos.
        - Resto: TextInput de texto libre (hasta 200 caracteres).
        """
        opts = _param_data_options(pkey)
        if opts is not None:
            if not opts:
                dd = SimpleDropdown(x, y, w, h, [("", "(vacío)")], selected="")
                dd.enabled = False
                return dd
            dd = SimpleDropdown(x, y, w, h, opts, selected=str(value) if value else "")
            dd._on_select = None
            return dd
        if pkey in NUMERIC_PARAMS:
            return TextInput(x, y, w, h, default=str(value), max_chars=8, numeric_only=True)
        return TextInput(x, y, w, h, default=str(value), max_chars=200, numeric_only=False)

    def _add_option_choice(self):
        if self._selected_child != "options" or not self._selected_key:
            return
        self._save_current_options()
        options = get_dialogo_options_by_key(self._selected_key)
        if not options:
            options = [{"text": "", "choices": []}]
        choices = options[0].get("choices", [])
        if len(choices) >= MAX_CHOICES:
            return
        choices.append({"text": "", "action": ""})
        options[0]["choices"] = choices
        set_dialogo_options_by_key(self._selected_key, options)
        self._selected_choice = len(choices) - 1
        self._dirty = True
        self._build_ui()

    def _delete_option_question(self):
        if self._selected_child != "options" or not self._selected_key:
            return
        if not self._confirm_delete_options():
            return
        delete_dialogo_options_by_key(self._selected_key)
        self._selected_child = None
        self._selected_flat_idx = None
        self._selected_choice = None
        self._options_scroll = 0
        self._dirty = True
        self._build_ui()

    def _confirm_delete_options(self):
        """Modal de confirmación Sí/Cancelar antes de eliminar la pregunta."""
        font = I18n.instancia().fuente(14) if I18n.instancia() else pygame.font.SysFont("Arial", 14)
        font_b = I18n.instancia().fuente(14, bold=True) if I18n.instancia() else pygame.font.SysFont("Arial", 14, bold=True)
        screen = pygame.display.get_surface()
        W, H = screen.get_width(), screen.get_height()
        dw, dh = 400, 160
        dx, dy = (W - dw) // 2, (H - dh) // 2
        clock = pygame.time.Clock()
        result = False
        done = False
        bg = pygame.Surface((W, H), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 180))
        btn_si = pygame.Rect(dx + dw - 220, dy + dh - 50, 90, 30)
        btn_no = pygame.Rect(dx + dw - 120, dy + dh - 50, 90, 30)
        while not done:
            clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        done = True
                    elif event.key == pygame.K_RETURN:
                        result = True
                        done = True
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_si.collidepoint(event.pos):
                        result = True
                        done = True
                    elif btn_no.collidepoint(event.pos):
                        done = True
            screen.blit(bg, (0, 0))
            pygame.draw.rect(screen, (45, 50, 58), (dx, dy, dw, dh))
            pygame.draw.rect(screen, (70, 80, 95), (dx, dy, dw, dh), 2)
            title = font_b.render("Eliminar pregunta", True, (220, 190, 120))
            screen.blit(title, (dx + (dw - title.get_width()) // 2, dy + 18))
            msg = font.render("Se eliminará el Options completo de este diálogo.", True, (220, 220, 220))
            screen.blit(msg, (dx + (dw - msg.get_width()) // 2, dy + 58))
            msg2 = font.render("¿Continuar?", True, (180, 190, 200))
            screen.blit(msg2, (dx + (dw - msg2.get_width()) // 2, dy + 84))
            pygame.draw.rect(screen, (120, 50, 50), btn_si)
            pygame.draw.rect(screen, (150, 70, 70), btn_si, 1)
            si_s = font_b.render("Sí", True, (255, 255, 255))
            screen.blit(si_s, (btn_si.x + (btn_si.w - si_s.get_width()) // 2,
                               btn_si.y + (btn_si.h - si_s.get_height()) // 2))
            pygame.draw.rect(screen, (60, 70, 80), btn_no)
            pygame.draw.rect(screen, (80, 90, 105), btn_no, 1)
            no_s = font_b.render("No", True, (220, 220, 220))
            screen.blit(no_s, (btn_no.x + (btn_no.w - no_s.get_width()) // 2,
                               btn_no.y + (btn_no.h - no_s.get_height()) // 2))
            pygame.display.flip()
        return result

    def _remove_option_choice(self, idx):
        if self._selected_child != "options" or not self._selected_key:
            return
        self._save_current_options()
        options = get_dialogo_options_by_key(self._selected_key)
        if not options:
            return
        choices = options[0].get("choices", [])
        if 0 <= idx < len(choices):
            choices.pop(idx)
        options[0]["choices"] = choices
        set_dialogo_options_by_key(self._selected_key, options)
        self._selected_choice = None
        self._dirty = True
        self._build_ui()

    def _move_option_choice(self, idx, delta):
        if self._selected_child != "options" or not self._selected_key:
            return
        self._save_current_options()
        options = get_dialogo_options_by_key(self._selected_key)
        if not options:
            return
        choices = options[0].get("choices", [])
        j = idx + delta
        if not (0 <= j < len(choices)):
            return
        choices[idx], choices[j] = choices[j], choices[idx]
        options[0]["choices"] = choices
        set_dialogo_options_by_key(self._selected_key, options)
        self._selected_choice = j
        self._dirty = True
        self._build_ui()

    def _delete_flat_line(self, idx):
        if not self._selected_key:
            return
        flat = get_dialogo_by_key(self._selected_key)
        if not flat or idx >= len(flat):
            return
        flat.pop(idx)
        set_dialogo_by_key(self._selected_key, flat)
        if self._selected_flat_idx == idx:
            self._selected_flat_idx = min(idx, len(flat) - 1) if flat else None
        elif self._selected_flat_idx is not None and self._selected_flat_idx > idx:
            self._selected_flat_idx -= 1
        self._dirty = True
        self._build_ui()

    def _add_flat_line(self):
        if not self._selected_key:
            return
        flat = get_dialogo_by_key(self._selected_key)
        if flat is None:
            flat = []
        flat.append("")
        set_dialogo_by_key(self._selected_key, flat)
        self._selected_flat_idx = len(flat) - 1
        self._dirty = True
        self._build_ui()

    def _move_flat_line(self, delta):
        if self._selected_flat_idx is None or not self._selected_key:
            return
        flat = get_dialogo_by_key(self._selected_key)
        if not flat:
            return
        new_idx = self._selected_flat_idx + delta
        if new_idx < 0 or new_idx >= len(flat):
            return
        flat[self._selected_flat_idx], flat[new_idx] = flat[new_idx], flat[self._selected_flat_idx]
        set_dialogo_by_key(self._selected_key, flat)
        self._selected_flat_idx = new_idx
        self._dirty = True
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
            if el == self._detail_widgets.get("flat_up"): self._move_flat_line(-1); return True
            if el == self._detail_widgets.get("flat_down"): self._move_flat_line(1); return True
            if el == self._detail_widgets.get("flat_add"): self._add_flat_line(); return True
            if el == self._detail_widgets.get("choice_add"): self._add_choice(); return True
            for key, w in self._detail_widgets.items():
                if key.startswith("choice_del_") and el == w:
                    if self._selected_child == "options":
                        self._remove_option_choice(int(key.split("_")[2]))
                    else:
                        self._remove_choice(int(key.split("_")[2]))
                    return True

        elif e.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            key = e.text
            if key in get_all_dialogo_keys():
                self._save_current_node()
                self._save_current_flat_line()
                self._save_current_options()
                self._selected_key = key
                self._selected_nid = None
                self._selected_flat_idx = None
                self._selected_child = None
                self._selected_choice = None
                self._options_scroll = 0
                self._build_ui()
                return True

        # Detail custom widgets (dropdowns, text inputs, buttons) — before node
        # clicks / tree wheel so an open dropdown captures wheel and outside-click
        # closes without selecting tree nodes.
        for key, w in list(self._detail_widgets.items()):
            if not isinstance(w, (SimpleDropdown, TextInput, Button)):
                continue
            if w.handle_event(e):
                if self._action_rebuild:
                    self._action_rebuild = False
                    self._build_ui()
                return True

        # Custom node/line click handling
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            mx, my = pygame.mouse.get_pos()
            for nid, info in self._node_widgets.items():
                if info["del_rect"].collidepoint(mx, my):
                    if "flat_idx" in info:
                        self._delete_flat_line(info["flat_idx"])
                    else:
                        self._on_delete_node(nid)
                    return True
                if info["rect"].collidepoint(mx, my):
                    if "flat_idx" in info:
                        self._save_current_flat_line()
                        self._save_current_options()
                        self._selected_flat_idx = info["flat_idx"]
                        self._selected_nid = None
                        self._selected_child = None
                        self._selected_choice = None
                        self._options_scroll = 0
                        self._build_ui()
                    elif "child" in info:
                        self._save_current_flat_line()
                        self._save_current_options()
                        self._selected_child = info["child"]
                        self._selected_flat_idx = None
                        self._selected_nid = None
                        self._selected_choice = None
                        self._options_scroll = 0
                        self._build_ui()
                    else:
                        self._select_node(nid)
                    return True

        # Mouse wheel for tree scroll
        if e.type == pygame.MOUSEWHEEL:
            tr = self._get_tree_rect()
            mx, my = pygame.mouse.get_pos()
            if self._selected_child == "options":
                oz = self._get_options_rect()
                if oz and oz.collidepoint(mx, my):
                    content = getattr(self, "_detail_content_h", 0)
                    max_scroll = max(0, content - oz.h)
                    nuevo = max(0, min(max_scroll, self._options_scroll - e.y * 24))
                    if nuevo != self._options_scroll:
                        self._options_scroll = nuevo
                        self._build_ui()
                    return True
            if tr and tr.collidepoint(mx, my):
                filas = self._tree_total_rows()
                max_scroll = max(0, filas * NODE_H - tr.h)
                self._tree_scroll = max(0, min(max_scroll, self._tree_scroll - e.y * NODE_H))
                return True

        return True

    def draw(self, surface):
        if not self.visible:
            return
        r = self.get_abs_rect()
        pygame.draw.rect(surface, self.bg_color, r)
        sub = surface.subsurface(r)
        self._gui.draw_ui(sub)
        self._draw_tree(surface)
        for w in self._dropdown_host.children:
            w.draw(sub)

        # Zona de opciones: clip propio + scrollbar visible.
        ep = self._editor_panel
        if self._options_top is not None:
            oz = pygame.Rect(ep.rect.x, ep.rect.y + self._options_top,
                             ep.rect.w, ep.rect.h - self._options_top)
            old_clip = sub.get_clip()
            sub.set_clip(oz)
            abiertos = []
            for w in self._options_host.children:
                w.draw(sub)
                if getattr(w, "_open", False):
                    abiertos.append(w)
            content = getattr(self, "_detail_content_h", 0)
            visible = oz.h
            if content > visible:
                sb_x = oz.x + oz.w - SCROLLBAR_W
                track = pygame.Rect(sb_x, oz.y, SCROLLBAR_W, visible)
                pygame.draw.rect(sub, (35, 38, 44), track)
                thumb_h = max(12, int(visible * visible / content))
                max_scroll = max(0, content - visible)
                thumb_y = (
                    oz.y + int((self._options_scroll / max_scroll) * (visible - thumb_h))
                    if max_scroll > 0
                    else oz.y
                )
                thumb = pygame.Rect(sb_x + 1, thumb_y, SCROLLBAR_W - 2, thumb_h)
                pygame.draw.rect(sub, (100, 110, 125), thumb)
                pygame.draw.rect(sub, (130, 140, 155), thumb, 1)
            sub.set_clip(old_clip)
            for w in abiertos:
                w.draw(sub)

    def set_size(self, w, h):
        if self.rect.w != w or self.rect.h != h:
            self.rect.w = w
            self.rect.h = h
            self._gui.set_window_resolution((w, h))
            self._build_ui()


# ── Helpers ──


class _FakeInput:
    def __init__(self, default=""):
        self._text = default
    def get_text(self):
        return self._text


class _DropdownHost:
    """Contenedor que agrupa los SimpleDropdown del detalle.

    El UIPanel de pygame_gui no expone una lista .children con los widgets
    custom, así que este host la mantiene para que SimpleDropdown pueda
    cerrar los demás (close_others) y elevar el abierto (bring_to_front).
    """

    def __init__(self, ep):
        self.ep = ep
        self.children = []

    def get_abs_rect(self):
        return self.ep.get_abs_rect()

    def add(self, w):
        w.parent = self
        self.children.append(w)


class _FakeDropdown:
    def __init__(self, default=""):
        self._selected = default
    def get_selected(self):
        return self._selected


def fake_input(default=""):
    return _FakeInput(default)


def fake_dd(default=""):
    return _FakeDropdown(default)
