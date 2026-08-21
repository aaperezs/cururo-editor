from typing import Any, Dict, List, Optional, Tuple

from editor.behaviors import BEHAVIORS, DEFAULT_ELEMENT_PROPERTIES
from editor.elements import (
    get_element, set_element, get_element_subtiles, set_element_subtile,
)
from editor.items_data import get_item_list
from editor.ability_data import get_ability_list


def get_behavior_schema(behavior: str) -> Dict[str, Any]:
    bdata = BEHAVIORS.get(behavior, {})
    return bdata.get("properties", {})


def get_current_props(el: Dict[str, Any]) -> Dict[str, Any]:
    return dict(el.get("properties", {}))


def should_reset_props(old_beh: str, new_beh: str) -> bool:
    return new_beh != old_beh


def apply_props_to_element(
    el: Dict[str, Any],
    new_beh: str,
    editing_props: Dict[str, Any],
    drops_data: Optional[List[Dict[str, Any]]] = None,
) -> None:
    if new_beh != el.get("behavior"):
        el["properties"] = dict(DEFAULT_ELEMENT_PROPERTIES.get(new_beh, {}))
    else:
        for k, v in editing_props.items():
            el["properties"][k] = v
        if drops_data is not None:
            for pkey in list(el["properties"].keys()):
                if isinstance(el["properties"][pkey], list):
                    el["properties"][pkey] = list(drops_data)
                    break


def apply_multi_tile(el: Dict[str, Any], sprite_id: str, tiles: List[Dict[str, Any]]) -> None:
    if el.get("behavior") == "multi_tile":
        el["multi_tile"] = True
        if tiles and not el.get("subtiles"):
            el["subtiles"] = [dict(t) for t in tiles]
    else:
        el.pop("multi_tile", None)


def build_drop_options() -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
    item_opts = get_item_list()
    ability_opts = [("", "Cualquiera")] + get_ability_list()
    return item_opts, ability_opts


def create_empty_drop() -> Dict[str, Any]:
    return {"item": "", "prob": 50}


def validate_drop(drop: Dict[str, Any]) -> bool:
    return bool(drop.get("item"))
