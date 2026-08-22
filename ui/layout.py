"""Layout containers for the editor UI (flexbox-like)."""

import pygame

from editor.widgets.base import Widget, Container
from editor.ui.theme import Theme


class VBox(Container):
    """Vertical box layout - stacks children top to bottom."""
    
    def __init__(self, padding=0, gap=0, align="stretch"):
        super().__init__(0, 0, 0, 0)
        self.padding = padding
        self.gap = gap
        self.align = align  # "stretch", "left", "center", "right"
        self._weights = {}  # child -> weight
    
    def set_weight(self, child: Widget, weight: float):
        """Set flex weight for a child (proportional space allocation)."""
        self._weights[child] = max(0, weight)
    
    def layout(self):
        """Calculate positions and sizes of children."""
        if not self.children:
            return
        
        theme = Theme.get()
        inner_w = self.rect.w - self.padding * 2
        inner_h = self.rect.h - self.padding * 2
        
        # First pass: measure natural sizes
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
        
        # Available space for weighted children
        available_h = inner_h - fixed_h - self.gap * (len([c for c in self.children if c.visible]) - 1)
        available_h = max(0, available_h)
        
        # Second pass: assign positions (relative to this container)
        y = self.padding
        for child in self.children:
            if not child.visible:
                continue
            
            w = self._weights.get(child, 0)
            if w > 0 and total_weight > 0:
                child_h = int(available_h * w / total_weight)
            else:
                child_h = child.rect.h
            
            # Width based on alignment
            if self.align == "stretch":
                child_w = inner_w
                child_x = self.padding
            elif self.align == "center":
                child_w = child.rect.w
                child_x = (self.rect.w - child_w) // 2
            elif self.align == "right":
                child_w = child.rect.w
                child_x = self.rect.w - self.padding - child_w
            else:  # left
                child_w = child.rect.w
                child_x = self.padding
            
            child.rect.x = child_x
            child.rect.y = y
            child.rect.w = child_w
            child.rect.h = child_h
            
            y += child_h + self.gap
        
        # Always recompute container height (auto-height)
        self.rect.h = y + self.padding


class HBox(Container):
    """Horizontal box layout - stacks children left to right."""
    
    def __init__(self, padding=0, gap=0, align="stretch"):
        super().__init__(0, 0, 0, 0)
        self.padding = padding
        self.gap = gap
        self.align = align  # "stretch", "top", "center", "bottom"
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
        fixed_w = 0
        for child in self.children:
            if not child.visible:
                continue
            w = self._weights.get(child, 0)
            if w > 0:
                total_weight += w
            else:
                fixed_w += child.rect.w
        
        available_w = inner_w - fixed_w - self.gap * (len([c for c in self.children if c.visible]) - 1)
        available_w = max(0, available_w)
        
        x = self.padding
        for child in self.children:
            if not child.visible:
                continue
            
            w = self._weights.get(child, 0)
            if w > 0 and total_weight > 0:
                child_w = int(available_w * w / total_weight)
            else:
                child_w = child.rect.w
            
            if self.align == "stretch":
                child_h = inner_h
                child_y = self.padding
            elif self.align == "center":
                child_h = child.rect.h
                child_y = (self.rect.h - child_h) // 2
            elif self.align == "bottom":
                child_h = child.rect.h
                child_y = self.rect.h - self.padding - child_h
            else:  # top
                child_h = child.rect.h
                child_y = self.padding
            
            child.rect.x = x
            child.rect.y = child_y
            child.rect.w = child_w
            child.rect.h = child_h
            
            x += child_w + self.gap
        
        if self.rect.w == 0:
            self.rect.w = x + self.padding


class DockLayout(Container):
    """Dock layout with left, center, right panels."""
    
    def __init__(self, left_width=0, right_width=0):
        super().__init__(0, 0, 0, 0)
        self.left_width = left_width
        self.right_width = right_width
        self.left_panel = None
        self.center_panel = None
        self.right_panel = None
    
    def set_left(self, panel: Widget, width: int = None):
        self.left_panel = panel
        if width is not None:
            self.left_width = width
        panel.parent = self
        self.children.append(panel)
    
    def set_center(self, panel: Widget):
        self.center_panel = panel
        panel.parent = self
        self.children.append(panel)
    
    def set_right(self, panel: Widget, width: int = None):
        self.right_panel = panel
        if width is not None:
            self.right_width = width
        panel.parent = self
        self.children.append(panel)
    
    def layout(self):
        if not self.left_panel and not self.center_panel and not self.right_panel:
            return
        
        # Use relative coordinates (0,0 origin for this dock)
        # Left panel (fixed width)
        if self.left_panel and self.left_panel.visible:
            self.left_panel.rect.x = 0
            self.left_panel.rect.y = 0
            self.left_panel.rect.w = self.left_width
            self.left_panel.rect.h = self.rect.h
            self.left_panel.layout()
        
        # Right panel (fixed width, from right)
        if self.right_panel and self.right_panel.visible:
            self.right_panel.rect.x = self.rect.w - self.right_width
            self.right_panel.rect.y = 0
            self.right_panel.rect.w = self.right_width
            self.right_panel.rect.h = self.rect.h
            self.right_panel.layout()
        
        # Center panel (fills remaining)
        if self.center_panel and self.center_panel.visible:
            self.center_panel.rect.x = self.left_width
            self.center_panel.rect.y = 0
            self.center_panel.rect.w = self.rect.w - self.left_width - self.right_width
            self.center_panel.rect.h = self.rect.h
            self.center_panel.layout()

    # No draw() override: children draw at absolute positions via get_abs_rect().
    # A translated surface would double-offset them.


class Spacer(Widget):
    """Flexible spacer that expands to fill available space."""
    
    def __init__(self, weight=1):
        super().__init__(0, 0, 0, 0)
        self.weight = weight
    
    def layout(self):
        pass  # Handled by parent VBox/HBox

class Grid(Container):
    """Grid layout (like CSS grid). Declares cols + gap, auto-positions children."""
    
    def __init__(self, cols=2, gap=6, padding=6):
        super().__init__(0, 0, 0, 0)
        self.cols = cols
        self.gap = gap
        self.padding = padding
    
    def layout(self):
        if not self.children:
            return
        inner_w = self.rect.w - self.padding * 2
        cell_w = (inner_w - self.gap * (self.cols - 1)) // self.cols
        row_h = max((c.rect.h for c in self.children if c.visible), default=0)
        x = self.padding
        y = self.padding
        col = 0
        for child in self.children:
            if not child.visible:
                continue
            child.rect.x = x
            child.rect.y = y
            child.rect.w = cell_w
            child.rect.h = row_h
            col += 1
            if col >= self.cols:
                col = 0
                x = self.padding
                y += row_h + self.gap
            else:
                x += cell_w + self.gap
        self.rect.h = y + row_h + self.padding