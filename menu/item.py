from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class MenuItem:
    label: str
    action: Optional[Callable] = None
    panel_id: Optional[str] = None
    shortcut: str = ""
    enabled: bool = True
    separator_before: bool = False


@dataclass
class MenuSection:
    label: str
    items: list = field(default_factory=list)
