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
        # You can expand this mapping as needed
        variable_map = {
            "{shaped_result}": RECIPE_DATA["result"],
            "{shaped_slot_0}": RECIPE_DATA["slots"][0],
            "{shaped_slot_1}": RECIPE_DATA["slots"][1],
            "{shaped_slot_2}": RECIPE_DATA["slots"][2],
            "{shaped_slot_3}": RECIPE_DATA["slots"][3],
            "{shaped_slot_5}": RECIPE_DATA["slots"][4],
            "{shaped_slot_6}": RECIPE_DATA["slots"][5],
            "{shaped_slot_7}": RECIPE_DATA["slots"][6],
            "{shaped_slot_8}": RECIPE_DATA["slots"][7],
        }
        return variable_map.get(varStr, None)

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
            error_invalid_path(layer_path)
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
    """
    Given a combination of layer variants, composite the images in order and save the result.

    Args:
        idx (int): Index of the combination (used for output filename).
        combination (tuple[dict, ...]): Tuple of layer variant dicts for this image.
        output_template (str): Output filename template, e.g. 'image_{index}_{layer0}_{layer1}.png'.
        output_folder (Path): Path to the output directory.
    """

    def get_anchor_coords(anchor, base_w, base_h, overlay_w, overlay_h):
        """Return anchor coordinates for overlay placement."""
        anchor_map = {
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
        return anchor_map.get(anchor, anchor_map["center"])

    def scale_image(img, scale, resample):
        """
        Scale an image according to scale (number, [w, h], or {width, height}).
        Returns the scaled image and its new size.
        """
        overlay_w, overlay_h = img.size
        if scale is not None:
            if isinstance(scale, (int, float)):
                overlay_w = int(overlay_w * scale)
                overlay_h = int(overlay_h * scale)
                img = img.resize((overlay_w, overlay_h), resample=resample)
            elif isinstance(scale, (list, tuple)) and len(scale) == 2:
                overlay_w = int(overlay_w * scale[0])
                overlay_h = int(overlay_h * scale[1])
                img = img.resize((overlay_w, overlay_h), resample=resample)
            elif isinstance(scale, dict):
                overlay_w = int(scale.get("width", overlay_w))
                overlay_h = int(scale.get("height", overlay_h))
                img = img.resize((overlay_w, overlay_h), resample=resample)
            # else: invalid scale type, ignore scaling
        return img, (overlay_w, overlay_h)

    # Open base image
    base_layer = combination[0]
    base_img = Image.open(base_layer["path"]).convert("RGBA")
    base_scale = base_layer.get("scale", None)
    if base_scale is not None:
        base_resample_str = base_layer.get("resample", None)
        base_resample = RESAMPLE_MAP.get(base_resample_str, Image.NEAREST)
        resized_base, _ = scale_image(base_img, base_scale, base_resample)
        base_img = resized_base

    # Build layer name mapping for output filename
    layer_names = {
        f"layer{i}": (layer["path"].stem if layer["path"] else "none")
        for i, layer in enumerate(combination)
    }
    # Overlay each layer
    for layer in combination[1:]:
        path = layer["path"]
        if path is None:
            continue  # Skip blank overlays

        overlay_img = Image.open(path).convert("RGBA")
        base_w, base_h = base_img.size
        scale = layer.get("scale")
        resample_str = (layer.get("resample") or "nearest").upper()
        resample_method = RESAMPLE_MAP.get(resample_str, Image.NEAREST)
        overlay_img, (overlay_w, overlay_h) = scale_image(
            overlay_img, scale, resample_method
        )

        # Calculate anchor and offset
        anchor = layer.get("anchor", "center")
        offset = tuple(layer.get("offset", [0, 0]))
        anchor_x, anchor_y = get_anchor_coords(
            anchor, base_w, base_h, overlay_w, overlay_h
        )
        paste_x = anchor_x + offset[0]
        paste_y = anchor_y + offset[1]

        # Composite overlay
        temp = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        temp.paste(overlay_img, (paste_x, paste_y), overlay_img)
        base_img = Image.alpha_composite(base_img, temp)

    # Save output
    try:
        filename = output_template.format(index=idx, **layer_names)
    except KeyError as e:
        missing = str(e).strip("'")
        print(
            f"[WARNING] Output template placeholder '{{{missing}}}' does not match any layer. Skipping placeholder."
        )
        # Remove missing placeholder from template and try again
        import re

        # Remove the missing placeholder (e.g., {layer2}) from the template
        # Use double braces in regex to avoid f-string brace error
        pattern = r"\{" + re.escape(missing) + r"\}"
        filename = re.sub(pattern, "", output_template)
        try:
            filename = filename.format(index=idx, **layer_names)
        except Exception:
            filename = f"image_{idx}.png"
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
