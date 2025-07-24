from pathlib import Path
import json
import sys
from PIL import Image
from reticulator import *

with open("data/recipe_image_gen/config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)
    GENERATORS = CONFIG.get("generators", [])


# -------------------------------------------------------------------------------------- #
def main():
    project = Project("BP", "RP")
    bp = project.behavior_pack
    rp = project.resource_pack
    for recipe in bp.recipes:
        recipe_data = recipe.data.get("minecraft:recipe_shaped", False)
        if recipe_data:
            # Process shaped recipe
            process_shaped_recipe(recipe_data, bp, rp)


# -------------------------------------------------------------------------------------- #
def process_shaped_recipe(recipe_data, bp, rp):
    recipe_id = recipe_data.get("description", {}).get("identifier", None)
    recipe_result = recipe_data.get("result", {}).get("item", None)
    recipe_key = recipe_data.get("key", None)
    recipe_pattern = recipe_data.get("pattern", None)
    flattened_pattern = flatten_pattern(recipe_pattern, recipe_key)
    print(flattened_pattern)
# -------------------------------------------------------------------------------------- #
def flatten_pattern(pattern,key):
    """
    Always iterate over a 3x3 grid. For each (row, col), get the character from pattern if present, else None.
    If character is present, get item from key, else None.
    """
    return [
        [
            key.get(pattern[i][j], {}).get('item', None)
            if i < len(pattern) and j < len(pattern[i]) else None
            for j in range(3)
        ]
        for i in range(3)
    ]

# -------------------------------------------------------------------------------------- #
if __name__ == "__main__":
    main()
