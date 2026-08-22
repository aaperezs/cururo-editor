"""Panel widgets for the editor UI."""

import pygame

from editor.widgets.base import Widget, Container
from editor.ui.theme import Theme
from editor.ui.icons import get_icon_factory
from editor.ui.widgets.button import Button
from editor.ui.widgets.label import Label


class Panel(Container):
    """Themed panel container."""
    
    def __init__(self, x, y, w, h, title="", padding=0, stretch=False):
        super().__init__(x, y, w, h)
        self.title = title
        self.padding = padding
        self.stretch = stretch
        self._title_label = None
        if title:
            self._title_label = Label(0, 0, 0, 0, title, bold=True)
            self._title_label.parent = self
            self.children.append(self._title_label)
    
    def layout(self):
        theme = Theme.get()
        if self._title_label:
            self._title_label.rect.x = self.padding
            self._title_label.rect.y = self.padding
            self._title_label.rect.w = self.rect.w - self.padding * 2
            self._title_label.rect.h = theme.section_header_h
            self._title_label.layout()
        
        # Layout children below title (relative to this panel)
        content_y = self.padding
        if self._title_label:
            content_y += theme.section_header_h + theme.gap
        
        for child in self.children:
            if child is self._title_label or not child.visible:
                continue
            child.rect.x = self.padding
            child.rect.y = content_y
            child.rect.w = self.rect.w - self.padding * 2
            child.layout()
            content_y += child.rect.h + theme.gap


class SectionPanel(Panel):
    """Panel with a section header (used as section container)."""
    
    def __init__(self, x, y, w, h, title=""):
        super().__init__(x, y, w, h, title, padding=Theme.get().panel_pad)


class CollapsibleSection(Container):
    """Collapsible section - header on top, expands downward."""
    
    def __init__(self, x, y, w, h, title="", expanded=True, icon="chevron_down"):
        super().__init__(x, y, w, h)
        self.title = title
        self.expanded = expanded
        self.icon_name = icon
        self._header = None
        self._content = VBox(padding=0, gap=Theme.get().gap)
        self._content.parent = self
        self.children = [self._content]
        self._build_header()
    
    def _build_header(self):
        theme = Theme.get()
        self._header = Button(
            0, 0, self.rect.w, theme.section_header_h,
            text=("▾ " if self.expanded else "▸ ") + self.title,
            callback=self._toggle,
            variant=Button.VARIANT_GHOST,
            icon=self.icon_name,
            icon_size=12
        )
        self._header.toggle = True
        self._header.toggled = self.expanded
        self._header.parent = self
        self.children.insert(0, self._header)
    
    def _toggle(self):
        self.expanded = not self.expanded
        self._header.toggled = self.expanded
        self._header.text = ("▾ " if self.expanded else "▸ ") + self.title
        self._content.visible = self.expanded
        # Parent will re-layout
        if self.parent:
            self.parent.layout()
    
    def set_expanded(self, expanded: bool):
        if expanded != self.expanded:
            self._toggle()
    
    def add_widget(self, widget: Widget):
        """Add widget to content area."""
        widget.parent = self._content
        self._content.children.append(widget)
        self.layout()
    
    def layout(self):
        theme = Theme.get()
        r = self.rect
        
        # Header always visible at top (relative to this section)
        if self._header:
            self._header.rect.x = 0
            self._header.rect.y = 0
            self._header.rect.w = r.w
            self._header.rect.h = theme.section_header_h
            self._header.layout()
        
        # Content below header
        if self.expanded:
            self._content.visible = True
            self._content.rect.x = 0
            self._content.rect.y = theme.section_header_h + theme.gap
            self._content.rect.w = r.w
            self._content.rect.h = 0  # Let content auto-calculate
            self._content.layout()
        else:
            self._content.visible = False
        
        # Always recompute container height based on content
        content_h = self._content.rect.h if self.expanded else 0
        r.h = theme.section_header_h + (theme.gap + content_h if self.expanded else 0)


class VBox(Container):
    """Vertical box layout - stacks children top to bottom."""
    
    def __init__(self, padding=0, gap=0, align="stretch"):
        super().__init__(0, 0, 0, 0)
        self.padding = padding
        self.gap = gap
        self.align = align  # "stretch", "left", "center", "right"
        self._weights = {}
    
    def set_weight(self, child: Widget, weight: float):
        self._weights[child] = max(0, weight)
    
    def layout(self):
        if not self.children:
            return
        
        theme = Theme.get()
        inner_w = self.rect.w - self.padding * 2
        inner_h = self.rect.h - self.padding * 2
        
        total_weight = 0
        fixed_h = 0
        for child in self.children:
            if not child.visible:
                continue
            w = self._weights.get(child, 0)
            if w > 0:
                total_weight += w
            else:
                fixed_h += child.rect.h
        
        available_h = inner_h - fixed_h - self.gap * (len([c for c in self.children if c.visible]) - 1)
        available_h = max(0, available_h)
        
        y = self.padding
        for child in self.children:
            if not child.visible:
                continue
            
            w = self._weights.get(child, 0)
            if w > 0 and total_weight > 0:
                child_h = int(available_h * w / total_weight)
            else:
                child_h = child.rect.h
            
            if self.align == "stretch":
                child_w = inner_w
                child_x = self.padding
            elif self.align == "center":
                child_w = child.rect.w
                child_x = (self.rect.w - child_w) // 2
            elif self.align == "right":
                child_w = child.rect.w
                child_x = self.rect.w - self.padding - child_w
            else:
                child_w = child.rect.w
                child_x = self.padding
            
            child.rect.x = child_x
            child.rect.y = y
            child.rect.w = child_w
            child.rect.h = child_h
            
            y += child_h + self.gap
        
        # Always recompute container height (auto-height)
        self.rect.h = y + self.padding


# Re-export VBox from layout for convenience
from editor.ui.layout import VBox as LayoutVBox, HBox, DockLayout, Spacer