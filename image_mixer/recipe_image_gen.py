from pathlib import Path
import json
from reticulator import Project

# -------------------------------------------------------------------------------------- #
TEXTURE_MAP_PATH = "data/image_mixer/texture_map.json"

with open(TEXTURE_MAP_PATH, "r", encoding="utf-8") as f:
    TEXTURE_MAP: dict[str, str] = json.load(f)

project = Project("BP", "RP")
vanilla = Project(
    "data/vanilla_packs/behavior_pack", "data/vanilla_packs/resource_pack"
)
BP = project.behavior_pack
RP = project.resource_pack


# -------------------------------------------------------------------------------------- #
class TextureResolutionError(Exception):
    """Raised when a named recipe item cannot be found in the texture map or behavior pack."""


def get_item_texture_path(item_name: str | None) -> str | None:
    """
    Convert an item identifier like 'tsu_nat:void_crystal' to its texture path.

    Resolution order:
      1. Empty slot (item_name is None/blank) → return None
      2. Manual override in texture_map.json → return that path
      3. Reticulator BP scan → resolve icon shortname → return RP texture path
      4. Not found by reticulator → raise TextureResolutionError
    """
    if not item_name:
        return None

    if path_override := TEXTURE_MAP.get(item_name):
        return path_override

    item = BP.get_item(item_name)
    if not item:
        raise TextureResolutionError(
            f"Item '{item_name}' was not found in the behavior pack and has no entry in "
            f"'{TEXTURE_MAP_PATH}'. Add a manual texture path override there to fix this."
        )

    icon = item.get_jsonpath("**/minecraft:icon", default=None)
    if isinstance(icon, str):
        shortname = icon
    elif isinstance(icon, dict):
        shortname = icon.get("textures", {}).get("default")
    else:
        return None

    if not shortname:
        return None

    texture_data = RP.item_texture_file.get_jsonpath(
        f"texture_data/{shortname}/textures", default=None
    )
    if not texture_data:
        return None

    path = (
        texture_data[0].get("path") if isinstance(texture_data, list) else texture_data
    )
    return f"RP/{path}.png"


def get_tag_texture_path(tag_name: str) -> str | None:
    """
    Resolve a tag name to a texture path via the manual override map.

    Tags have no item definition to look up, so the override map is the only
    resolution mechanism. Raises TextureResolutionError if no override is present.
    """
    if path_override := TEXTURE_MAP.get(tag_name):
        return path_override

    raise TextureResolutionError(
        f"Tag '{tag_name}' has no entry in '{TEXTURE_MAP_PATH}'. "
        f"Tags cannot be resolved automatically — add a manual texture path override there to fix this."
    )


def get_slot_texture_path(slot_entry: dict | None) -> str | None:
    """
    Resolve a recipe key entry (which may be an item or a tag) to a texture path.

    Dispatches to get_item_texture_path or get_tag_texture_path based on which
    key is present in the entry dict.
    """
    if not slot_entry:
        return None
    if item := slot_entry.get("item"):
        return get_item_texture_path(item)
    if tag := slot_entry.get("tag"):
        return get_tag_texture_path(tag)
    return None


def flatten_recipe_pattern(pattern: list[str], key: dict) -> list[str | None]:
    """
    Flatten a shaped recipe pattern into a centred 9-element slot list.

    The pattern may be smaller than 3x3 (e.g. 1x2, 2x2). It is centred within
    the 3x3 grid so that the generated image reflects how the recipe appears
    in-game, where it can be placed anywhere it fits.

    Returns a list of 9 key entry dicts (or None for empty slots), in row-major
    order for a 3x3 grid.
    """
    pattern_rows = len(pattern)
    pattern_cols = max(len(row) for row in pattern) if pattern else 0

    row_offset = (3 - pattern_rows) // 2
    col_offset = (3 - pattern_cols) // 2

    grid: list[dict | None] = [None] * 9
    for pr, row in enumerate(pattern):
        for pc, symbol in enumerate(row):
            if symbol != " " and symbol in key:
                grid_index = (pr + row_offset) * 3 + (pc + col_offset)
                grid[grid_index] = key[symbol]

    return grid


# -------------------------------------------------------------------------------------- #
# Per-type slot texture extractors
# -------------------------------------------------------------------------------------- #


def get_shaped_slot_textures(recipe_data: dict) -> dict:
    """Return the identifier, per-slot textures, and result texture for a shaped recipe."""
    identifier = recipe_data.get("description", {}).get("identifier")
    result_item = recipe_data.get("result", {}).get("item")
    slot_entries = flatten_recipe_pattern(
        recipe_data.get("pattern"), recipe_data.get("key")
    )
    return {
        "id": identifier,
        "slots": [get_slot_texture_path(entry) for entry in slot_entries],
        "result": get_item_texture_path(result_item),
    }


def get_shapeless_slot_textures(recipe_data: dict) -> dict:
    """
    Return the identifier, per-slot textures, and result texture for a shapeless recipe.

    Ingredients are placed into slots 0-8 in order. Ingredients with count > 1
    are expanded into repeated entries. Unused slots are None.
    Ingredients may specify either 'item' or 'tag'.
    """
    identifier = recipe_data.get("description", {}).get("identifier")
    result_item = recipe_data.get("result", {}).get("item")
    ingredients = recipe_data.get("ingredients", [])

    expanded: list[dict] = []
    for ingredient in ingredients:
        count = ingredient.get("count", 1)
        expanded.extend([ingredient] * count)

    slots = [
        get_slot_texture_path(expanded[i]) if i < len(expanded) else None
        for i in range(9)
    ]
    return {
        "id": identifier,
        "slots": slots,
        "result": get_item_texture_path(result_item),
    }


def get_furnace_slot_textures(recipe_data: dict) -> dict:
    """
    Return the identifier and slot textures for a furnace recipe.

    Slot 0 = input, slot 1 = output.
    """
    identifier = recipe_data.get("description", {}).get("identifier")
    input_item = recipe_data.get("input")
    output_item = recipe_data.get("output")
    return {
        "id": identifier,
        "slots": [
            get_item_texture_path(input_item),
            get_item_texture_path(output_item),
        ],
    }


# -------------------------------------------------------------------------------------- #


def _append_slots(store: dict, slot_textures: dict, num_slots: int) -> None:
    """Append one recipe's resolved slot textures into a flattened slot-indexed store."""
    slots = slot_textures["slots"]
    for i in range(num_slots):
        store["slots"][i].append(slots[i] if i < len(slots) else None)

    if "result" in store:
        store["result"].append(slot_textures.get("result"))


def get_flattened_recipe_data() -> dict:
    """
    Return all recipe data in a slot-indexed format, separated by recipe type.

    Structure:
        {
            "shaped":    {"slots": [[...], ...],  "result": [...]},  # 9 slots
            "shapeless": {"slots": [[...], ...],  "result": [...]},  # 9 slots
            "furnace":   {"slots": [[...], ...]},                    # 2 slots: input, output
        }
    """
    final: dict = {
        "shaped": {"slots": [[] for _ in range(9)], "result": []},
        "shapeless": {"slots": [[] for _ in range(9)], "result": []},
        "furnace": {"slots": [[] for _ in range(2)]},
    }

    # Maps recipe type key -> (store key, handler, num_slots)
    recipe_handlers = {
        "minecraft:recipe_shaped": ("shaped", get_shaped_slot_textures, 9),
        "minecraft:recipe_shapeless": ("shapeless", get_shapeless_slot_textures, 9),
        "minecraft:recipe_furnace": ("furnace", get_furnace_slot_textures, 2),
    }

    for recipe in BP.recipes:
        for recipe_type, (store_key, handler, num_slots) in recipe_handlers.items():
            if recipe_data := recipe.data.get(recipe_type):
                _append_slots(final[store_key], handler(recipe_data), num_slots)
                break

    return final
