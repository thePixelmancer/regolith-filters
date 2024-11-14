from pathlib import Path
import json
from colorthief import ColorThief


def rgb_to_hex(color):
    return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"


def get_palette(img, count=2):
    ct = ColorThief(img)
    palette = ct.get_palette(count, quality=1)
    return palette


def get_texture_path(data):
    textures = (
        data.get("minecraft:client_entity", {})
        .get("description", {})
        .get("textures", {})
    )
    texture = textures.get("default", None) or textures.values()[0]
    return texture


def apply_spawn_egg_colors(file_path):
    try:
        with open(file_path, "r") as file:
            entity_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"Failed to load JSON from {file_path}: {error}")
        return

    texture_path = get_texture_path(entity_data)
    if not texture_path:
        return

    texture_file = Path("RP") / f"{texture_path}.png"
    if not texture_file.exists():
        return

    spawn_egg_data = entity_data.get("minecraft:client_entity", {}).get("description", {}).get("spawn_egg")
    if spawn_egg_data is not None:
        return

    try:
        color_palette = get_palette(texture_file)
        if not color_palette or len(color_palette) < 2:
            return

        base_color, overlay_color = map(rgb_to_hex, color_palette[:2])
        entity_data.setdefault("minecraft:client_entity", {}).setdefault("description", {})["spawn_egg"] = {
            "base_color": base_color,
            "overlay_color": overlay_color,
        }
    except Exception as error:
        print(f"Error processing texture {texture_file}: {error}")
        return

    try:
        with open(file_path, "w") as file:
            json.dump(entity_data, file, indent=4)
        print(f"Applied spawn egg colors to {file_path}")
    except IOError as error:
        print(f"Failed to write JSON to {file_path}: {error}")


if __name__ == "__main__":
    for file in Path("RP/entity").rglob("*.json"):
        apply_spawn_egg_colors(file)