import json
from functools import lru_cache

from reticulator import Project
from reticulator.core import AssetNotFoundError

# -------------------------------------------------------------------------------------- #
TEXTURE_MAP_PATH = "data/image_mixer/texture_map.json"

project = Project("BP", "RP")
vanilla = Project("data/vanilla_packs/behavior_pack", "data/vanilla_packs/resource_pack")
BP = project.behavior_pack
RP = project.resource_pack


# -------------------------------------------------------------------------------------- #
@lru_cache(maxsize=1)
def _texture_map() -> dict[str, str]:
    try:
        with open(TEXTURE_MAP_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def _warn_missing_texture(kind: str, name: str) -> None:
    print(
        f"[WARNING] No texture found for {kind} '{name}'. "
        f"Add an entry to '{TEXTURE_MAP_PATH}'; this layer will be blank."
    )


def get_item_texture_path(item_name: str | None) -> str | None:
    """
    Convert an item identifier like 'tsu_nat:void_crystal' to its texture path.

    Resolution order:
      1. Empty slot (item_name is None/blank) → return None
      2. Manual override in texture_map.json → return that path
      3. Reticulator BP scan → resolve icon shortname → return RP texture path
      4. If unresolved → warn and return None
    """
    if not item_name:
        return None

    if path_override := _texture_map().get(item_name):
        return path_override

    item = BP.get_item(item_name)
    if not item:
        _warn_missing_texture("item", item_name)
        return None

    icon = item.get_jsonpath("**/minecraft:icon", default=None)
    if isinstance(icon, str):
        shortname = icon
    elif isinstance(icon, dict):
        shortname = icon.get("textures", {}).get("default")
    else:
        shortname = None
    if not shortname:
        _warn_missing_texture("item", item_name)
        return None

    try:
        texture_file = RP.item_texture_file
    except AssetNotFoundError:
        _warn_missing_texture("item", item_name)
        return None
    texture_data = texture_file.get_jsonpath(
        f"texture_data/{shortname}/textures", default=None
    )
    if not texture_data:
        _warn_missing_texture("item", item_name)
        return None

    path = texture_data[0].get("path") if isinstance(texture_data, list) else texture_data
    return f"RP/{path}.png"


def get_tag_texture_path(tag_name: str) -> str | None:
    """
    Resolve a tag name to a texture path via the manual override map.

    Tags have no item definition to look up, so the override map is the only
    resolution mechanism. Warns and returns None if no override is present.
    """
    if path_override := _texture_map().get(tag_name):
        return path_override

    _warn_missing_texture("tag", tag_name)
    return None


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
#
# Each handler returns a dict with:
#   id    (str)        — recipe identifier
#   tags  (list[str]) — station tags (furnace only; empty list for shaped/shapeless)
#   slots (list)      — resolved texture paths, one per slot
#   result (str|None) — result texture (shaped and shapeless only)
# -------------------------------------------------------------------------------------- #

def _strip_namespace(identifier: str | None) -> str | None:
    """Extract the part after the colon from a namespaced identifier (e.g., 'minecraft:apple_stew' -> 'apple_stew')."""
    if not identifier:
        return None
    if ":" in identifier:
        return identifier.split(":", 1)[1]
    return identifier


def get_shaped_slot_textures(
    recipe_data: dict, requested_variables: set[str] | None = None
) -> dict:
    """Return the identifier, per-slot textures, and result texture for a shaped recipe."""
    identifier = _strip_namespace(recipe_data.get("description", {}).get("identifier"))
    result_item = recipe_data.get("result", {}).get("item")
    slot_entries = flatten_recipe_pattern(recipe_data.get("pattern"), recipe_data.get("key"))
    return {
        "id":     identifier,
        "tags":   [],
        "slots":  [
            get_slot_texture_path(entry)
            if requested_variables is None or f"{{shaped_slot_{i}}}" in requested_variables
            else None
            for i, entry in enumerate(slot_entries)
        ],
        "result": (
            get_item_texture_path(result_item)
            if requested_variables is None or "{shaped_result}" in requested_variables
            else None
        ),
    }


def get_shapeless_slot_textures(
    recipe_data: dict, requested_variables: set[str] | None = None
) -> dict:
    """
    Return the identifier, per-slot textures, and result texture for a shapeless recipe.

    Ingredients are placed into slots 0-8 in order. Ingredients with count > 1
    are expanded into repeated entries. Unused slots are None.
    Ingredients may specify either 'item' or 'tag'.
    """
    identifier = _strip_namespace(recipe_data.get("description", {}).get("identifier"))
    result_item = recipe_data.get("result", {}).get("item")
    ingredients = recipe_data.get("ingredients", [])

    expanded: list[dict] = []
    for ingredient in ingredients:
        count = ingredient.get("count", 1)
        expanded.extend([ingredient] * count)

    slots = [
        get_slot_texture_path(expanded[i])
        if i < len(expanded) and (
            requested_variables is None or f"{{shapeless_slot_{i}}}" in requested_variables
        )
        else None
        for i in range(9)
    ]
    return {
        "id":     identifier,
        "tags":   [],
        "slots":  slots,
        "result": (
            get_item_texture_path(result_item)
            if requested_variables is None or "{shapeless_result}" in requested_variables
            else None
        ),
    }


def get_furnace_slot_textures(
    recipe_data: dict, requested_variables: set[str] | None = None
) -> dict:
    """
    Return the identifier, station tags, and slot textures for a furnace recipe.

    Slot 0 = input, slot 1 = output.
    Tags reflect which stations accept this recipe (e.g. 'furnace', 'smoker',
    'campfire', 'soul_campfire') and come from the 'tags' array in the recipe data.
    """
    identifier = _strip_namespace(recipe_data.get("description", {}).get("identifier"))
    tags = recipe_data.get("tags", [])
    input_item = recipe_data.get("input")
    output_item = recipe_data.get("output")
    return {
        "id":    identifier,
        "tags":  tags,
        "slots": [
            get_item_texture_path(item)
            if requested_variables is None or f"{{furnace_slot_{i}}}" in requested_variables
            else None
            for i, item in enumerate((input_item, output_item))
        ],
    }


# -------------------------------------------------------------------------------------- #

def _passes_whitelist(
    slot_textures: dict,
    id_whitelist: list[str] | None,
    tag_whitelist: list[str] | None,
) -> bool:
    """
    Return True if a recipe should be included given the active whitelists.

    Rules:
      - If both whitelists are None or empty, all recipes pass.
      - If either whitelist is non-empty, the recipe must match at least one
        entry in at least one of the active whitelists.
      - id_whitelist matches against the recipe identifier.
      - tag_whitelist matches against the recipe's station tags.
    """
    has_id_filter  = bool(id_whitelist)
    has_tag_filter = bool(tag_whitelist)

    if not has_id_filter and not has_tag_filter:
        return True

    if has_id_filter and slot_textures["id"] in id_whitelist:
        return True

    if has_tag_filter and any(tag in tag_whitelist for tag in slot_textures["tags"]):
        return True

    return False


def _append_slots(store: dict, slot_textures: dict, num_slots: int) -> None:
    """Append one recipe's resolved slot textures into a flattened slot-indexed store."""
    slots = slot_textures["slots"]
    for i in range(num_slots):
        store["slots"][i].append(slots[i] if i < len(slots) else None)

    store["ids"].append(slot_textures.get("id"))

    if "result" in store:
        store["result"].append(slot_textures.get("result"))


def get_flattened_recipe_data(
    id_whitelist: list[str] | None = None,
    tag_whitelist: list[str] | None = None,
    requested_variables: set[str] | None = None,
) -> dict:
    """
    Return all recipe data in a slot-indexed format, separated by recipe type.

    Args:
        id_whitelist:  If provided, only recipes whose identifier is in this list
                       are included. Combined with tag_whitelist via OR.
        tag_whitelist: If provided, only recipes with at least one matching station
                       tag are included. Combined with id_whitelist via OR.
        requested_variables: Resolve only these recipe placeholders, or all if None.

    Structure:
        {
            "shaped":    {"slots": [[...], ...],  "result": [...]},  # 9 slots
            "shapeless": {"slots": [[...], ...],  "result": [...]},  # 9 slots
            "furnace":   {"slots": [[...], ...]},                    # 2 slots: input, output
        }
    """
    final: dict = {
        "shaped":    {"ids": [], "slots": [[] for _ in range(9)], "result": []},
        "shapeless": {"ids": [], "slots": [[] for _ in range(9)], "result": []},
        "furnace":   {"ids": [], "slots": [[] for _ in range(2)]},
    }

    # Maps recipe type key -> (store key, handler, num_slots)
    recipe_handlers = {
        "minecraft:recipe_shaped":    ("shaped",    get_shaped_slot_textures,    9),
        "minecraft:recipe_shapeless": ("shapeless", get_shapeless_slot_textures, 9),
        "minecraft:recipe_furnace":   ("furnace",   get_furnace_slot_textures,   2),
    }

    for recipe in BP.recipes:
        for recipe_type, (store_key, handler, num_slots) in recipe_handlers.items():
            if recipe_data := recipe.data.get(recipe_type):
                if requested_variables is not None and not any(
                    variable.startswith(f"{{{store_key}_")
                    for variable in requested_variables
                ):
                    break
                metadata = {
                    "id": _strip_namespace(recipe_data.get("description", {}).get("identifier")),
                    "tags": recipe_data.get("tags", []) if store_key == "furnace" else [],
                }
                if _passes_whitelist(metadata, id_whitelist, tag_whitelist):
                    slot_textures = handler(recipe_data, requested_variables)
                    _append_slots(final[store_key], slot_textures, num_slots)
                break

    return final