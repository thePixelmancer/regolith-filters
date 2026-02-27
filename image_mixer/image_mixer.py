import json
import itertools
import re
import warnings
import concurrent.futures
from pathlib import Path

from PIL import Image
import recipe_image_gen as rig

# -------------------------------------------------------------------------------------- #
SCHEMA_URL = "https://raw.githubusercontent.com/thePixelmancer/regolith-filters/refs/heads/main/image_mixer/data/config.schema.json"

try:
    RECIPE_DATA = rig.get_flattened_recipe_data()
except rig.TextureResolutionError as e:
    raise SystemExit(f"[ERROR] Failed to resolve recipe textures:\n  {e}") from None

VARIABLE_MAP: dict[str, list] = {
    # Shaped recipe (9 slots + result)
    "{shaped_result}": RECIPE_DATA["shaped"]["result"],
    **{f"{{shaped_slot_{i}}}": RECIPE_DATA["shaped"]["slots"][i] for i in range(9)},
    # Shapeless recipe (9 slots + result)
    "{shapeless_result}": RECIPE_DATA["shapeless"]["result"],
    **{
        f"{{shapeless_slot_{i}}}": RECIPE_DATA["shapeless"]["slots"][i]
        for i in range(9)
    },
    # Furnace recipe (slot 0 = input, slot 1 = output)
    "{furnace_slot_0}": RECIPE_DATA["furnace"]["slots"][0],
    "{furnace_slot_1}": RECIPE_DATA["furnace"]["slots"][1],
}

BLANK_VALUES = {None, "none", "None", ""}


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

    Raises:
        ValueError: If a layer length is not 1 and not equal to the longest layer length.
    """
    max_len = max(len(layer) for layer in all_layers)
    broadcast = []
    for layer in all_layers:
        if len(layer) == 1:
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


def _resolve_variable(placeholder: str) -> list:
    """Resolve a placeholder string to its recipe data list."""
    if placeholder not in VARIABLE_MAP:
        raise KeyError(
            f"Variable '{placeholder}' not found. Available: {list(VARIABLE_MAP.keys())}"
        )
    return VARIABLE_MAP[placeholder]


def get_layer_variants(layer: dict) -> list[dict]:
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
    }

    def make_variant(path: Path | None) -> dict:
        return {**layer_props, "path": path}

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
        resolved = _resolve_variable(layer_path)
        return [make_variant(Path(p) if p else None) for p in resolved]

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


def expand_layers(layers: list[dict]) -> list[list[dict]]:
    return [get_layer_variants(layer) for layer in layers]


def generate_combinations(
    layers: list[dict], combination_mode: str
) -> list[tuple[dict, ...]]:
    """
    Generate all layer combinations according to the selected mode.

    Args:
        layers: List of layer config dicts.
        combination_mode: 'cartesian' for all possible combinations, 'zip' to match by index.

    Returns:
        List of tuples, each a combination of one variant from each layer.
    """
    all_layers = expand_layers(layers)
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
    try:
        return template.format(index=idx, **layer_names)
    except KeyError as e:
        missing = str(e).strip("'")
        print(f"[WARNING] Template placeholder {{{missing}}} not found. Removing it.")
        cleaned = re.sub(r"\{" + re.escape(missing) + r"\}", "", template)
        try:
            return cleaned.format(index=idx, **layer_names)
        except Exception:
            return f"image_{idx}.png"


def composite_layers(combination: tuple[dict, ...]) -> Image.Image | None:
    """Composite a tuple of layer variants into a single RGBA image."""
    base_layer = combination[0]
    if not base_layer["path"]:
        return None

    resample = _get_resample(base_layer.get("resample"))
    base_img = _scale_image(
        Image.open(base_layer["path"]).convert("RGBA"),
        base_layer.get("scale"),
        resample,
    )

    for layer in combination[1:]:
        if not layer["path"]:
            continue

        resample = _get_resample(layer.get("resample"))
        overlay = _scale_image(
            Image.open(layer["path"]).convert("RGBA"),
            layer.get("scale"),
            resample,
        )
        pos = _get_paste_position(
            layer.get("anchor", "center"),
            base_img.size,
            overlay.size,
            tuple(layer.get("offset", [0, 0])),
        )
        temp = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        temp.paste(overlay, pos, overlay)
        base_img = Image.alpha_composite(base_img, temp)

    return base_img


def process_combination(
    idx: int, combination: tuple[dict, ...], output_template: str, output_folder: Path
) -> None:
    """Composite a layer combination and save the result to disk."""
    result = composite_layers(combination)
    if result is None:
        print(f"[ERROR] Base image missing for combination {idx}.")
        return

    filename = _format_filename(output_template, idx, combination)
    result.save(output_folder / filename)


# -------------------------------------------------------------------------------------- #
# Entry point
# -------------------------------------------------------------------------------------- #


def generate_images(image_mixer: dict) -> None:
    """
    Generate and save all composite images for a given image_mixer config.

    Args:
        image_mixer: Config dict with keys: 'output_folder', 'output_template',
                     'layers', and optionally 'combination_mode' ('cartesian' or 'zip').
    """
    output_folder = Path(image_mixer["output_folder"])
    output_folder.mkdir(parents=True, exist_ok=True)

    output_template = image_mixer.get("output_template", "image_{index}.png")
    combination_mode = image_mixer.get("combination_mode", "cartesian")

    if combination_mode not in ("cartesian", "zip"):
        raise ValueError(
            f"Invalid combination_mode '{combination_mode}'. Must be 'cartesian' or 'zip'."
        )

    combinations = generate_combinations(image_mixer["layers"], combination_mode)
    total = len(combinations)

    if total > 500:
        print(
            f"[WARNING] About to generate {total} images. This may heavily load your system."
        )
        if input("Continue? (Y/N): ").strip().lower() != "y":
            print("Aborted.")
            return

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(
                process_combination, idx, combo, output_template, output_folder
            )
            for idx, combo in enumerate(combinations)
        ]
        for future in concurrent.futures.as_completed(futures):
            future.result()  # Surface any exceptions from worker threads


if __name__ == "__main__":
    config_path = Path("data/image_mixer/config.json")
    with config_path.open("r") as f:
        config = json.load(f)

    for image_mixer in config["image_mixers"]:
        generate_images(image_mixer)

    if config.get("$schema") != SCHEMA_URL:
        warnings.warn(
            f"\n{'-' * 80}\nSchema not found, get it at:\n\n{SCHEMA_URL}\n{'-' * 80}"
        )
