from pathlib import Path
import json
from reticulator import *


VANILLA_MAPPINGS_PATH = "data/image_mixer/vanilla_texture_map.json"
with open(VANILLA_MAPPINGS_PATH, "r", encoding="utf-8") as f:
    VANILLA_MAP = json.load(f)

project = Project("BP", "RP")
BP = project.behavior_pack
RP = project.resource_pack


# -------------------------------------------------------------------------------------- #
def get_item_texture_path(item_name):
    """Converts an item name like tsu_nat:void_crystal to a texture path."""
    if not item_name:
        return None

    # Check vanilla mappings first
    path_from_vanilla = VANILLA_MAP.get(item_name, None)
    if path_from_vanilla:
        return path_from_vanilla

    item = BP.get_item(item_name)
    if not item:
        return None

    icon = item.get_jsonpath("**/minecraft:icon", default=None)
    if isinstance(icon, str):
        shortname = icon
    elif isinstance(icon, dict):
        shortname = icon.get("textures", {}).get("default", None)
    else:
        return None

    texture_data = RP.item_texture_file.get_jsonpath(
        f"texture_data/{shortname}/textures", default=None
    )
    if not texture_data:
        return None
    if isinstance(texture_data, list) and texture_data:
        return "RP/" + texture_data[0].get("path") + ".png"
    else:
        return "RP/" + texture_data + ".png"


def flatten_recipe_pattern(pattern, key):
    """Flattens a 3x3 recipe pattern into a list of item names."""
    return [
        (
            key.get(pattern[i][j], {}).get("item")
            if i < len(pattern) and j < len(pattern[i])
            else None
        )
        for i in range(3)
        for j in range(3)
    ]


def get_slot_textures(recipe_data):
    """Returns a dict with recipe ID and list of texture paths."""
    id = recipe_data.get("description", {}).get("identifier")
    result = recipe_data.get("result", {}).get("item")
    key = recipe_data.get("key")
    pattern = recipe_data.get("pattern")

    flat_items = flatten_recipe_pattern(pattern, key)
    component_slots = [get_item_texture_path(item) for item in flat_items]
    result_slot = get_item_texture_path(result)
    return {
        "id": id,
        "slots": component_slots,
        "result": result_slot,
    }


def get_flattened_recipe_data():
    final = {
        "slots": [
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
        ],  # 9 lists for slot indices 0-8, each sublist means slot[index][recipe_index]
        "result": [],  # List of result textures, one per recipe
    }

    for recipe in BP.recipes:
        shaped_data = recipe.data.get("minecraft:recipe_shaped")
        if shaped_data:
            slot_textures = get_slot_textures(shaped_data)
            final["result"].append(slot_textures["result"])

            for i in range(9):
                if i < len(slot_textures["slots"]):
                    final["slots"][i].append(slot_textures["slots"][i])
                else:
                    final["slots"][i].append(None)

    return final
