import json
import itertools
import re
import warnings
import concurrent.futures
from pathlib import Path

from PIL import Image

import image_cache
import recipe_image_gen as rig
from slot_template import read_slot_template

# -------------------------------------------------------------------------------------- #
SCHEMA_URL = "https://raw.githubusercontent.com/thePixelmancer/regolith-filters/refs/heads/main/image_mixer/data/config.schema.json"

BLANK_VALUES = {None, "none", "None", ""}


def _build_variable_map(
    id_whitelist: list[str] | None,
    tag_whitelist: list[str] | None,
) -> dict[str, list]:
    """
    Build the recipe variable map for a single mixer, applying any whitelists.

    Called once per mixer so that different mixers can filter different recipe subsets.
    Raises SystemExit with a clear message if any recipe item cannot be resolved.
    """
    try:
        recipe_data = rig.get_flattened_recipe_data(
            id_whitelist=id_whitelist,
            tag_whitelist=tag_whitelist,
        )
    except rig.TextureResolutionError as e:
        raise SystemExit(f"[ERROR] Failed to resolve recipe textures:\n  {e}") from None

    # {recipe_id} is a special variable that resolves to the recipe identifier.
    # Since shaped, shapeless, and furnace recipes are all zipped in parallel by index,
    # we merge all their id lists into one. The user is expected to use a whitelist to
    # ensure only one recipe type is active per mixer, so only one list will be non-empty.
    all_ids = (
        recipe_data["shaped"]["ids"]
        or recipe_data["shapeless"]["ids"]
        or recipe_data["furnace"]["ids"]
    )

    return {
        # Recipe identifier (shared across all types — one type active per mixer)
        "{recipe_id}": all_ids,
        # Shaped recipe (9 slots + result)
        "{shaped_result}": recipe_data["shaped"]["result"],
        **{f"{{shaped_slot_{i}}}": recipe_data["shaped"]["slots"][i] for i in range(9)},
        # Shapeless recipe (9 slots + result)
        "{shapeless_result}": recipe_data["shapeless"]["result"],
        **{
            f"{{shapeless_slot_{i}}}": recipe_data["shapeless"]["slots"][i]
            for i in range(9)
        },
        # Furnace recipe (slot 0 = input, slot 1 = output)
        "{furnace_slot_0}": recipe_data["furnace"]["slots"][0],
        "{furnace_slot_1}": recipe_data["furnace"]["slots"][1],
    }


# -------------------------------------------------------------------------------------- #
# Layer combination strategies
# -------------------------------------------------------------------------------------- #


def cartesian_combinations(all_layers: list[list[dict]]) -> list[tuple[dict, ...]]:
    """Return every possible combination of layer variants (cartesian product)."""
    return list(itertools.product(*all_layers))


def zip_combinations(all_layers: list[list[dict]]) -> list[tuple[dict, ...]]:
    """
    Return combinations by matching layer variants by index, broadcasting
    single-variant layers to match the longest layer's length.

    Returns an empty list if any variable layer has 0 variants — this happens
    when a whitelist filters out all recipes of a given type, and is not an error.

    Raises:
        ValueError: If a layer length is not 1, not 0, and not equal to the longest layer length.
    """
    max_len = max(len(layer) for layer in all_layers)

    if max_len == 0:
        return []

    broadcast = []
    for layer in all_layers:
        if len(layer) == 0:
            # A variable layer with no variants means the whitelist matched nothing.
            # Return early — there is nothing to generate for this mixer.
            return []
        elif len(layer) == 1:
            broadcast.append(layer * max_len)
        elif len(layer) == max_len:
            broadcast.append(layer)
        else:
            raise ValueError(
                f"Layer with {len(layer)} variants cannot be zipped to length {max_len}."
            )
    return [
        tuple(broadcast[j][i] for j in range(len(broadcast))) for i in range(max_len)
    ]


# -------------------------------------------------------------------------------------- #
# Layer variant resolution
# -------------------------------------------------------------------------------------- #


def _is_blank(value: object) -> bool:
    return value in BLANK_VALUES


def _is_variable(value: object) -> bool:
    """Return True if value is a placeholder like '{variable_name}'."""
    return (
        isinstance(value, str)
        and value.startswith("{")
        and value.endswith("}")
        and len(value) > 2
    )


def _resolve_variable(placeholder: str, variable_map: dict[str, list]) -> list:
    """Resolve a placeholder string to its recipe data list."""
    if placeholder not in variable_map:
        raise KeyError(
            f"Variable '{placeholder}' not found. Available: {list(variable_map.keys())}"
        )
    return variable_map[placeholder]


def get_layer_variants(layer: dict, variable_map: dict[str, list]) -> list[dict]:
    """
    Resolve a layer config into a list of variant dicts, one per image.

    Handles: blank paths, variable placeholders, file lists, directories, and single files.
    """
    layer_path = layer["path"]
    layer_props = {
        "offset": layer.get("offset", [0, 0]),
        "blend_mode": layer.get("blend_mode", "normal"),
        "anchor": layer.get("anchor", "center"),
        "scale": layer.get("scale", None),
        "resample": layer.get("resample", None),
        "slot_bbox": layer.get("slot_bbox", None),
        "recipe_id": layer.get("recipe_id", None),
    }

    def make_variant(path: Path | None, recipe_id: str | None = None) -> dict:
        return {**layer_props, "path": path, "recipe_id": recipe_id}

    def resolve_path(p: str) -> Path:
        resolved = Path(p)
        if not resolved.is_file():
            raise FileNotFoundError(
                f"Layer path '{p}' does not exist or is not a file."
            )
        return resolved

    if _is_blank(layer_path):
        return [make_variant(None)]

    if _is_variable(layer_path):
        resolved = _resolve_variable(layer_path, variable_map)
        recipe_ids = variable_map.get("{recipe_id}", [])
        return [
            make_variant(
                Path(p) if p else None, recipe_ids[i] if i < len(recipe_ids) else None
            )
            for i, p in enumerate(resolved)
        ]

    if isinstance(layer_path, list):
        return [
            (
                make_variant(None)
                if _is_blank(entry)
                else make_variant(resolve_path(entry))
            )
            for entry in layer_path
        ]

    p = Path(layer_path)
    if p.is_dir():
        return [make_variant(f) for f in sorted(p.glob("*.png"))]
    if p.is_file():
        return [make_variant(p)]

    raise FileNotFoundError(
        f"Layer path '{layer_path}' does not exist or is not a valid file/directory."
    )


def expand_layers(
    layers: list[dict], variable_map: dict[str, list]
) -> list[list[dict]]:
    return [get_layer_variants(layer, variable_map) for layer in layers]


def generate_combinations(
    layers: list[dict],
    combination_mode: str,
    variable_map: dict[str, list],
) -> list[tuple[dict, ...]]:
    """
    Generate all layer combinations according to the selected mode.

    Args:
        layers: List of layer config dicts.
        combination_mode: 'cartesian' for all possible combinations, 'zip' to match by index.
        variable_map: Resolved recipe variable map for this mixer.
    """
    all_layers = expand_layers(layers, variable_map)
    combinator = (
        zip_combinations if combination_mode == "zip" else cartesian_combinations
    )
    return combinator(all_layers)


# -------------------------------------------------------------------------------------- #
# Image compositing
# -------------------------------------------------------------------------------------- #


def _get_resample(method: str | None) -> Image.Resampling:
    return getattr(
        Image.Resampling, (method or "nearest").upper(), Image.Resampling.NEAREST
    )


def _scale_image(
    img: Image.Image, scale: float | list | dict | None, resample: Image.Resampling
) -> Image.Image:
    """Scale an image using a scalar, (x, y) tuple, or {width, height} dict."""
    if scale is None:
        return img

    w, h = img.size
    if isinstance(scale, (int, float)):
        w, h = int(w * scale), int(h * scale)
    elif isinstance(scale, (list, tuple)) and len(scale) == 2:
        w, h = int(w * scale[0]), int(h * scale[1])
    elif isinstance(scale, dict):
        w = int(scale.get("width", w))
        h = int(scale.get("height", h))

    return img.resize((w, h), resample=resample)


def _get_paste_position(
    anchor: str, base_size: tuple, overlay_size: tuple, offset: tuple
) -> tuple[int, int]:
    """Calculate the top-left paste position for an overlay given an anchor and offset."""
    base_w, base_h = base_size
    overlay_w, overlay_h = overlay_size

    anchor_positions = {
        "center": ((base_w - overlay_w) // 2, (base_h - overlay_h) // 2),
        "top_center": ((base_w - overlay_w) // 2, 0),
        "bottom_center": ((base_w - overlay_w) // 2, base_h - overlay_h),
        "left_center": (0, (base_h - overlay_h) // 2),
        "right_center": (base_w - overlay_w, (base_h - overlay_h) // 2),
        "top_left": (0, 0),
        "top_right": (base_w - overlay_w, 0),
        "bottom_left": (0, base_h - overlay_h),
        "bottom_right": (base_w - overlay_w, base_h - overlay_h),
    }
    ax, ay = anchor_positions.get(anchor, anchor_positions["center"])
    return ax + offset[0], ay + offset[1]


def _format_filename(template: str, idx: int, combination: tuple[dict, ...]) -> str:
    """Format the output filename from a template, falling back gracefully on missing placeholders."""
    layer_names = {
        f"layer{i}": (Path(layer["path"]).stem if layer["path"] else "none")
        for i, layer in enumerate(combination)
    }
    # Extract recipe_id from the first layer that has it set (from variable resolution)
    recipe_id = next(
        (layer["recipe_id"] for layer in combination if layer.get("recipe_id")),
        None,
    )
    placeholders = {"index": idx, "recipe_id": recipe_id or "unknown", **layer_names}
    try:
        return template.format(**placeholders)
    except KeyError as e:
        missing = str(e).strip("'")
        print(f"[WARNING] Template placeholder {{{missing}}} not found. Removing it.")
        cleaned = re.sub(r"\{" + re.escape(missing) + r"\}", "", template)
        try:
            return cleaned.format(**placeholders)
        except Exception:
            return f"image_{idx}.png"


def composite_layers(
    combination: tuple[dict, ...], base_img: Image.Image
) -> Image.Image:
    """
    Composite a tuple of layer variants onto a copy of base_img.

    The base image is passed in pre-loaded and pre-scaled so it is not
    re-opened on every combination. Overlay images are fetched from the
    image cache to avoid redundant file IO across combinations.
    """
    result = base_img.copy()

    for layer in combination[1:]:
        if not layer["path"]:
            continue

        resample = _get_resample(layer.get("resample"))

        # Slot bbox from a template: position and size come directly from the bbox.
        # Fallback: use the manually specified scale / anchor / offset.
        if slot_bbox := layer.get("slot_bbox"):
            x_min, y_min, x_max, y_max = slot_bbox
            slot_w = x_max - x_min + 1
            slot_h = y_max - y_min + 1
            overlay = image_cache.get(layer["path"]).resize(
                (slot_w, slot_h), resample=resample
            )
            pos = (x_min, y_min)
        else:
            overlay = _scale_image(
                image_cache.get(layer["path"]), layer.get("scale"), resample
            )
            pos = _get_paste_position(
                layer.get("anchor", "center"),
                result.size,
                overlay.size,
                tuple(layer.get("offset", [0, 0])),
            )

        temp = Image.new("RGBA", result.size, (0, 0, 0, 0))
        temp.paste(overlay, pos, overlay)
        result = Image.alpha_composite(result, temp)

    return result


def process_combination(
    idx: int,
    combination: tuple[dict, ...],
    base_img: Image.Image,
    output_template: str,
    output_folder: Path,
) -> None:
    """Composite a layer combination and save the result to disk."""
    result = composite_layers(combination, base_img)
    filename = _format_filename(output_template, idx, combination)
    result.save(output_folder / filename)


# -------------------------------------------------------------------------------------- #
# Entry point
# -------------------------------------------------------------------------------------- #


def generate_images(image_mixer: dict, large_batch_threshold: int = 500) -> None:
    """
    Generate and save all composite images for a given image_mixer config.

    Args:
        image_mixer: Config dict with keys:
            - output_folder (str): Where to write output images.
            - output_template (str): Filename template. Defaults to 'image_{index}.png'.
            - combination_mode (str): 'cartesian' or 'zip'. Defaults to 'cartesian'.
            - layers (list): Layer definitions.
            - slot_template (str, optional): Path to a slot template PNG.
        large_batch_threshold: Print a warning if this many images would be generated.
            Set to 0 to disable. Defaults to 500.
    """
    output_folder = Path(image_mixer["output_folder"])
    output_folder.mkdir(parents=True, exist_ok=True)

    output_template = image_mixer.get("output_template", "image_{index}.png")
    combination_mode = image_mixer.get("combination_mode", "cartesian")

    if combination_mode not in ("cartesian", "zip"):
        raise ValueError(
            f"Invalid combination_mode '{combination_mode}'. Must be 'cartesian' or 'zip'."
        )

    # Build the variable map for this mixer, filtered by the whitelists.
    # Done per-mixer so different mixers can target different recipe subsets
    # (e.g. one mixer for furnace-only, another for smoker-only).
    recipe_gen = image_mixer.get("recipe_generation", {})
    id_whitelist = recipe_gen.get("id_whitelist") or None
    tag_whitelist = recipe_gen.get("tag_whitelist") or None
    variable_map = _build_variable_map(id_whitelist, tag_whitelist)

    # Read slot template if provided and inject slot_bbox into each layer config.
    # Layers are matched to slots by their position in the array, skipping layer 0
    # (the base). Layer 1 → slot 0, layer 2 → slot 1, etc.
    # The template must be the same pixel dimensions as the scaled output canvas.
    layers = image_mixer["layers"]
    if template_path := image_mixer.get("slot_template"):
        slot_bboxes = read_slot_template(template_path)
        for layer_index, layer in enumerate(layers[1:], start=0):
            if layer_index in slot_bboxes:
                layer["slot_bbox"] = slot_bboxes[layer_index]

    # Load and scale the base image once — shared across all combinations.
    base_layer_config = layers[0]
    base_img = _scale_image(
        image_cache.get(Path(base_layer_config["path"])),
        base_layer_config.get("scale"),
        _get_resample(base_layer_config.get("resample")),
    )

    combinations = generate_combinations(layers, combination_mode, variable_map)
    total = len(combinations)

    if total == 0:
        print(
            f"[INFO] Mixer '{output_folder}' produced no combinations — whitelist may have filtered out all recipes."
        )
        return

    if large_batch_threshold and total > large_batch_threshold:
        print(
            f"[WARNING] About to generate {total} images. This may heavily load your system."
        )

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(
                process_combination,
                idx,
                combo,
                base_img,
                output_template,
                output_folder,
            )
            for idx, combo in enumerate(combinations)
        ]
        for future in concurrent.futures.as_completed(futures):
            future.result()  # Surface any exceptions from worker threads


if __name__ == "__main__":
    mixers_dir = Path("data/image_mixer/mixers")
    mixer_files = sorted(mixers_dir.glob("*.json"))

    if not mixer_files:
        print(f"[WARNING] No mixer files found in '{mixers_dir}'.")

    for mixer_path in mixer_files:
        with mixer_path.open("r") as f:
            image_mixer = json.load(f)
        print(f"[INFO] Running mixer: {mixer_path.name}")
        generate_images(image_mixer)
