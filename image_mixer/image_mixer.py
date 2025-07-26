import json
import itertools
from pathlib import Path
from PIL import Image
import concurrent.futures
import recipe_image_gen as rig

# -------------------------------------------------------------------------------------- #
RESAMPLE_MAP = {
    "NEAREST": Image.NEAREST,
    "BILINEAR": Image.BILINEAR,
    "BICUBIC": Image.BICUBIC,
    "LANCZOS": Image.LANCZOS,
    "BOX": Image.BOX,
    "HAMMING": Image.HAMMING,
}
RECIPE_DATA = rig.get_flattened_recipe_data()
# -------------------------------------------------------------------------------------- #


def cartesian_combinations(all_layers):
    """
    Generate all possible combinations of layer variants using the cartesian product.

    Args:
        all_layers (list[list[dict]]): List of lists, each containing dicts for each variant of a layer.

    Returns:
        list[tuple[dict, ...]]: List of tuples, each tuple is a combination of one variant from each layer.
    """
    return list(itertools.product(*all_layers))


def zip_combinations(all_layers):
    """
    Generate combinations by matching layer variants by index (like Python's zip),
    broadcasting single-image layers to match the length of the longest layer.

    Args:
        all_layers (list[list[dict]]): List of lists, each containing dicts for each variant of a layer.

    Returns:
        list[tuple[dict, ...]]: List of tuples, each tuple is a combination of one variant from each layer.

    Raises:
        ValueError: If a layer has a number of variants that is not 1 or the same as the longest layer.
    """
    max_len = max(len(layer) for layer in all_layers)
    zipped_layers = []
    for layer in all_layers:
        if len(layer) == 1:
            zipped_layers.append(layer * max_len)
        elif len(layer) == max_len:
            zipped_layers.append(layer)
        else:
            raise ValueError(
                f"Layer with {len(layer)} images cannot be zipped to length {max_len}."
            )
    return [
        tuple(zipped_layers[j][i] for j in range(len(zipped_layers)))
        for i in range(max_len)
    ]


# -------------------------------------------------------------------------------------- #


def get_layer_variants(layer):
    """
    Given a layer config dict, return a list of variant dicts for that layer.
    Handles directories, lists, files, and blank variants.
    """

    def is_blank(val):
        return val in [None, "none", "None", ""]

    def is_variable(val):
        """
        Check if a value is a variable placeholder (e.g., "{variable_name}").
        Only works for strings.
        """
        return (
            isinstance(val, str)
            and val.startswith("{")
            and val.endswith("}")
            and len(val) > 2
        )

    def replace_variable(varStr):
        # Example switch-like logic for variable replacement
        variable_map = {
            "{shaped_result}": RECIPE_DATA["result"],
            "{shaped_slot_0}": RECIPE_DATA["slots"][0],
            "{shaped_slot_1}": RECIPE_DATA["slots"][1],
            "{shaped_slot_2}": RECIPE_DATA["slots"][2],
            "{shaped_slot_3}": RECIPE_DATA["slots"][3],
            "{shaped_slot_4}": RECIPE_DATA["slots"][4],
            "{shaped_slot_5}": RECIPE_DATA["slots"][5],
            "{shaped_slot_6}": RECIPE_DATA["slots"][6],
            "{shaped_slot_7}": RECIPE_DATA["slots"][7],
            "{shaped_slot_8}": RECIPE_DATA["slots"][8],
        }
        if varStr not in variable_map:
            raise KeyError(
                f"Variable '{varStr}' not found in available variables: {list(variable_map.keys())}"
            )
        return variable_map[varStr]

    # -------------------------------------------------------------------------------------- #
    layer_path = layer["path"]
    layer_props = {
        "offset": layer.get("offset", [0, 0]),
        "blend_mode": layer.get("blend_mode", "normal"),
        "anchor": layer.get("anchor", "center"),
        "scale": layer.get("scale", None),
        "resample": layer.get("resample", None),
    }

    def error_invalid_path(path):
        raise FileNotFoundError(
            f"Layer path '{path}' does not exist or is not a valid file/directory."
        )

    def make_variant(path):
        return {**layer_props, "path": path}

    # -------------------------------------------------------------------------------------- #
    # Handle blank path
    if is_blank(layer_path):
        return [make_variant(None)]
    # Handle variable replacing
    if is_variable(layer_path):
        layer_path = replace_variable(layer_path)
        if layer_path == None:
            error_invalid_path(layer["path"])
    # Handle list of paths
    if isinstance(layer_path, list):
        variants = []
        for entry in layer_path:
            if is_blank(entry):
                variants.append(make_variant(None))
                continue
            p = Path(entry)
            if p.is_file():
                variants.append(make_variant(p))
            else:
                error_invalid_path(entry)
        return variants

    # Handle single path (file or directory)
    p = Path(layer_path)
    if p.is_dir():
        return [make_variant(f) for f in p.glob("*.png")]
    if p.is_file():
        return [make_variant(p)]
    error_invalid_path(layer_path)


def expand_layers(layers):
    return [get_layer_variants(layer) for layer in layers]


def generate_combinations(layers, combination_mode):
    """
    Generate combinations of layers according to the selected mode.

    Args:
        layers (list[dict]): List of layer config dicts.
        combination_mode (str): 'cartesian' (default) for all possible combinations,
            or 'zip' to match layers by index, broadcasting single-image layers as needed.

    Returns:
        list[tuple[dict, ...]]: List of tuples, each tuple is a combination of one variant from each layer.
    """
    all_layers = expand_layers(layers)
    if combination_mode == "zip":
        return zip_combinations(all_layers)
    else:
        return cartesian_combinations(all_layers)


def process_combination(idx, combination, output_template, output_folder):
    """Composite a combination of image layers and save the result."""

    def get_anchor_offset(anchor, base_size, overlay_size, offset):
        base_w, base_h = base_size
        overlay_w, overlay_h = overlay_size
        anchors = {
            "center": ((base_w - overlay_w) // 2, (base_h - overlay_h) // 2),
            "top_center": ((base_w - overlay_w) // 2, 0),
            "bottom_center": ((base_w - overlay_w) // 2, base_h - overlay_h),
            "left_center": (0, (base_h - overlay_h) // 2),
            "right_center": (base_w - overlay_w, (base_h - overlay_h) // 2),
            "bottom_left": (0, base_h - overlay_h),
            "bottom_right": (base_w - overlay_w, base_h - overlay_h),
            "top_right": (base_w - overlay_w, 0),
            "top_left": (0, 0),
        }
        anchor_x, anchor_y = anchors.get(anchor, anchors["center"])
        return anchor_x + offset[0], anchor_y + offset[1]

    def scale_image(img, scale, resample):
        """Scale an image based on scalar, tuple, or dict format."""
        w, h = img.size
        if scale is not None:
            if isinstance(scale, (int, float)):
                w, h = int(w * scale), int(h * scale)
            elif isinstance(scale, (list, tuple)) and len(scale) == 2:
                w, h = int(w * scale[0]), int(h * scale[1])
            elif isinstance(scale, dict):
                w = int(scale.get("width", w))
                h = int(scale.get("height", h))
            img = img.resize((w, h), resample=resample)
        return img, (w, h)

    def safe_open(path):
        return Image.open(path).convert("RGBA") if path else None

    def get_resample(method):
        return RESAMPLE_MAP.get((method or "nearest").upper(), Image.NEAREST)

    # --- Prepare base image ---
    base_layer = combination[0]
    base_img = safe_open(base_layer["path"])
    if base_img is None:
        print(f"[ERROR] Base image missing for combination {idx}")
        return

    base_img, _ = scale_image(
        base_img, base_layer.get("scale"), get_resample(base_layer.get("resample"))
    )

    # --- Overlay remaining layers ---
    for layer in combination[1:]:
        overlay = safe_open(layer["path"])
        if overlay is None:
            continue

        overlay, size = scale_image(
            overlay, layer.get("scale"), get_resample(layer.get("resample"))
        )
        pos = get_anchor_offset(
            layer.get("anchor", "center"),
            base_img.size,
            size,
            tuple(layer.get("offset", [0, 0])),
        )

        temp_layer = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        temp_layer.paste(overlay, pos, overlay)
        base_img = Image.alpha_composite(base_img, temp_layer)

    # --- Format filename ---
    layer_names = {
        f"layer{i}": (Path(layer["path"]).stem if layer["path"] else "none")
        for i, layer in enumerate(combination)
    }

    try:
        filename = output_template.format(index=idx, **layer_names)
    except KeyError as e:
        import re

        missing = str(e).strip("'")
        print(f"[WARNING] Template placeholder {{{missing}}} missing. Stripping it.")
        pattern = r"\{" + re.escape(missing) + r"\}"
        cleaned_template = re.sub(pattern, "", output_template)
        try:
            filename = cleaned_template.format(index=idx, **layer_names)
        except Exception:
            filename = f"image_{idx}.png"

    # --- Save output ---
    out_path = Path(output_folder) / filename
    base_img.save(out_path)


def generate_images(image_mixer):
    """
    For a given image_mixer config, generate and save all composite images.

    Each combination overlays the layers in order, using anchor, scaling, and offset for placement.
    Output filenames are built from a template with variables for index and layer names.
    Supports 'combination_mode': 'cartesian' (default, all possible combinations) or 'zip' (match layers by index).

    Args:
        image_mixer (dict): Image mixer config dict, must contain 'output_folder', 'output_template', 'layers', and optionally 'combination_mode'.
    """
    output_folder = Path(image_mixer["output_folder"])
    output_folder.mkdir(parents=True, exist_ok=True)
    output_template = image_mixer.get("output_template", "image_{index}.png")
    combination_mode = image_mixer.get("combination_mode", "cartesian")
    if combination_mode not in ["cartesian", "zip"]:
        raise ValueError(
            f"Invalid combination_mode '{combination_mode}'. Must be 'cartesian' or 'zip'."
        )
    layer_combinations = generate_combinations(
        image_mixer["layers"], combination_mode=combination_mode
    )

    total = len(layer_combinations)
    if total > 500:
        print(
            f"[WARNING] You are about to generate {total} images. This may heavily load your system."
        )
        while True:
            resp = input("Do you want to continue? (Y/N): ").strip().lower()
            if resp == "y":
                break
            elif resp == "n":
                print("Aborted by user.")
                return
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(
                process_combination, idx, combination, output_template, output_folder
            )
            for idx, combination in enumerate(layer_combinations)
        ]
        concurrent.futures.wait(futures)


# -------------------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Load the config file and generate images for each image_mixer entry
    config_path = Path("data/image_mixer/config.json")
    with config_path.open("r") as f:
        config = json.load(f)
    for image_mixer in config["image_mixers"]:
        generate_images(image_mixer)
