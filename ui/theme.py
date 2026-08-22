"""Design system theme for the editor UI."""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Color:
    """RGBA color with helper methods."""
    r: int
    g: int
    b: int
    a: int = 255

    def as_tuple(self) -> Tuple[int, int, int, int]:
        return (self.r, self.g, self.b, self.a)

    def as_rgb(self) -> Tuple[int, int, int]:
        return (self.r, self.g, self.b)

    def with_alpha(self, a: int) -> "Color":
        return Color(self.r, self.g, self.b, a)


class Theme:
    """Singleton theme with all design tokens."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        # ── Colors ──
        self.bg = Color(30, 32, 36)              # #1E2024
        self.surface = Color(51, 58, 65)         # #333A41
        self.surface_elevated = Color(45, 50, 58) # #2D323A
        self.border = Color(100, 109, 120)       # #646D78
        self.border_focus = Color(110, 122, 138) # #6E7A8A
        self.text = Color(220, 220, 220)         # #DCDCDC
        self.text_dim = Color(150, 160, 170)     # #96A0AC
        self.text_disabled = Color(100, 105, 115) # #646973
        self.bg_disabled = Color(38, 42, 47)     # #262A2F
        self.border_disabled = Color(58, 63, 69) # #3A3F45
        self.bg_hover = Color(58, 66, 75)        # #3A424B
        self.accent = Color(70, 130, 200)        # #4682C8
        self.accent_hover = Color(90, 150, 220)  # #5A96DC
        self.accent_active = Color(50, 110, 180) # #326EB4
        self.danger = Color(200, 80, 80)         # #C85050
        self.danger_hover = Color(220, 100, 100) # #DC6464
        self.success = Color(100, 180, 120)      # #64B478
        self.checker_a = Color(45, 45, 50)       # #2D2D32
        self.checker_b = Color(35, 35, 40)       # #232328
        self.shadow = Color(0, 0, 0, 65)         # rgba(0,0,0,0.25)
        
        # ── Spacing (4px base) ──
        self.space_xs = 2
        self.space_sm = 4
        self.space_md = 8
        self.space_lg = 12
        self.space_xl = 16
        
        # ── Border radius ──
        self.radius = 6
        self.radius_sm = 4
        self.radius_lg = 8
        
        # ── Control metrics ──
        self.control_h = 24
        self.control_h_sm = 20
        self.control_h_lg = 28
        
        # ── Panel ──
        self.panel_pad = 8
        self.section_header_h = 22
        
        # ── Gap ──
        self.gap = 6
        
        # ── Typography ──
        self.font_regular = "DejaVuSans.ttf"
        self.font_bold = "DejaVuSans-Bold.ttf"
        self.font_sizes = {
            "caption": 10,
            "body": 12,
            "body_lg": 14,
            "title": 16,
        }
        
        # ── Shadow ──
        self.shadow_offset = (0, 2)
        self.shadow_blur = 4
    
    @classmethod
    def get(cls) -> "Theme":
        return cls()