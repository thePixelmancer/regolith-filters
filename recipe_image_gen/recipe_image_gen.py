from pathlib import Path
import json
from PIL import Image
from reticulator import *

# -------------------------------------------------------------------------------------- #
CONFIG_PATH = "data/recipe_image_gen/config.json"
DEFAULT_OUTPUT_FOLDER = ("RP/textures/recipe_images",)
VANILLA_MAPPINGS_PATH = "data/recipe_image_gen/vanilla_texture_mappings.json"

project = Project("BP", "RP")
bp = project.behavior_pack
rp = project.resource_pack

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)
    GENERATORS = CONFIG.get("recipe_image_generators", [])
with open(VANILLA_MAPPINGS_PATH, "r", encoding="utf-8") as f:
    VANILLA_MAPPINGS = json.load(f)


# -------------------------------------------------------------------------------------- #
def get_item_texture_path(item_name):
    """Converts an item name like tsu_nat:void_crystal to a texture path."""
    if not item_name:
        return None

    # Check vanilla mappings first
    path_from_vanilla = VANILLA_MAPPINGS.get(item_name, None)
    if path_from_vanilla:
        return path_from_vanilla

    item = bp.get_item(item_name)
    if not item:
        return None

    icon = item.get_jsonpath("**/minecraft:icon", default=None)
    if isinstance(icon, str):
        shortname = icon
    elif isinstance(icon, dict):
        shortname = icon.get("textures", {}).get("default", None)
    else:
        return None

    texture_data = rp.item_texture_file.get_jsonpath(
        f"texture_data/{shortname}/textures", default=None
    )
    if not texture_data:
        return None
    if isinstance(texture_data, list) and texture_data:
        return "RP/" + texture_data[0].get("path") + ".png"
    else:
        return "RP/" + texture_data + ".png"


def flatten_pattern(pattern, key):
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


def get_recipe_texture_slots(recipe_data):
    """Returns a dict with recipe ID and list of texture paths."""
    rid = recipe_data.get("description", {}).get("identifier")
    result = recipe_data.get("result", {}).get("item")
    key = recipe_data.get("key")
    pattern = recipe_data.get("pattern")

    flat_items = flatten_pattern(pattern, key)
    slots = [get_item_texture_path(result)] + [
        get_item_texture_path(item) for item in flat_items
    ]
    return {"id": rid, "slots": slots}


def remove_namespace(identifier):
    return identifier.split(":", 1)[-1] if isinstance(identifier, str) else identifier


def generate_recipe_image(generator):

    background_path = generator.get("background")
    output_folder = generator.get("output", DEFAULT_OUTPUT_FOLDER)
    slot_size = generator.get("slot_size", 32)  # default slot size if not specified
    background_scale = generator.get("background_scale", 2)
    slots = generator["slots"]

    Path(output_folder).mkdir(parents=True, exist_ok=True)

    bg_file = Path(background_path)
    if not bg_file.exists():
        print(f"Background image not found: {background_path}")
        return

    background = Image.open(bg_file).convert("RGBA")
    if background_scale != 1:
        background = background.resize(
            (
                int(background.width * background_scale),
                int(background.height * background_scale),
            ),
            Image.Resampling.NEAREST,
        )

    for slot in slots:
        texture_path = slot.get("texture")
        if not texture_path:
            continue

        texture_file = Path(texture_path)
        if not texture_file.exists():
            print(f"Texture file not found: {texture_file}")
            continue

        item_img = Image.open(texture_file).convert("RGBA")
        # Use slot_size from slot if present, else global slot_size
        slot_sz = slot.get("slot_size", slot_size)
        iw, ih = item_img.size
        scale = min(slot_sz / iw, slot_sz / ih)
        new_size = (int(iw * scale), int(ih * scale))
        if new_size != item_img.size:
            item_img = item_img.resize(new_size, Image.Resampling.NEAREST)

        x, y = slot["position"]
        x = int(x * background_scale)
        y = int(y * background_scale)
        background.alpha_composite(item_img, (x, y))

    out_name = f"{remove_namespace(generator.get('id', 'recipe'))}_recipe.png"
    out_path = Path(output_folder) / out_name
    background.save(out_path)
    print(f"Saved recipe image: {out_path}")


def process_recipe(recipe_data):
    """For each recipe, cycle though the generators and create images."""
    texture_info = get_recipe_texture_slots(recipe_data)
    for template in GENERATORS:
        if template.get("type") != "shaped":
            continue
        gen = dict(template)
        gen["id"] = texture_info["id"]
        for idx, slot in enumerate(gen["slots"]):
            slot["texture"] = texture_info["slots"][idx]
        generate_recipe_image(gen)


# -------------------------------------------------------------------------------------- #
def main():
    """Go through all recipes process them."""
    for recipe in bp.recipes:
        shaped_data = recipe.data.get("minecraft:recipe_shaped")
        if shaped_data:
            process_recipe(shaped_data)


if __name__ == "__main__":
    main()
