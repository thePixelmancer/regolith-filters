import json
import itertools
from pathlib import Path
from PIL import Image
import concurrent.futures

# -------------------------------------------------------------------------------------- #
RESAMPLE_MAP = {
    "NEAREST": Image.NEAREST,
    "BILINEAR": Image.BILINEAR,
    "BICUBIC": Image.BICUBIC,
    "LANCZOS": Image.LANCZOS,
    "BOX": Image.BOX,
    "HAMMING": Image.HAMMING,
}
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


def is_blank(val):
    return val in [None, "none", "None", ""]


def get_layer_variants(layer):
    """
    Given a layer config dict, return a list of variant dicts for that layer.
    Handles directories, lists, files, and blank variants.
    """
    layer_path = layer["path"]
    layer_props = {
        "offset": layer.get("offset", [0, 0]),
        "blend_mode": layer.get("blend_mode", "normal"),
        "anchor": layer.get("anchor", "center"),
        "scale": layer.get("scale", None),
        "resample": layer.get("resample", None),
    }
    variants = []
    def error_invalid_path(path):
        raise FileNotFoundError(f"Layer path '{path}' does not exist or is not a valid file/directory.")

    if isinstance(layer_path, list):
        for entry in layer_path:
            if is_blank(entry):
                variants.append({**layer_props, "path": None})
            else:
                p = Path(entry)
                if p.is_file():
                    variants.append({**layer_props, "path": p})
                else:
                    error_invalid_path(entry)
    else:
        if is_blank(layer_path):
            variants.append({**layer_props, "path": None})
        else:
            p = Path(layer_path)
            if p.is_dir():
                variants.extend({**layer_props, "path": f} for f in p.glob("*.png"))
            elif p.is_file():
                variants.append({**layer_props, "path": p})
            else:
                error_invalid_path(layer_path)
    return variants


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
    base_layer = combination[0]
    base_img = Image.open(base_layer["path"]).convert("RGBA")
    layer_names = {}
    for i, layer in enumerate(combination):
        # layer["path"] is always a Path object or None now
        layer_names[f"layer{i}"] = layer["path"].stem if layer["path"] else "none"
    for layer in combination[1:]:
        if layer["path"] is None:
            continue  # Skip blank overlays
        overlay_img = Image.open(layer["path"]).convert("RGBA")
        base_w, base_h = base_img.size
        scale = layer.get("scale", None)
        resample_str = (layer.get("resample") or "nearest").upper()
        resample_method = RESAMPLE_MAP.get(resample_str, Image.NEAREST)
        overlay_w, overlay_h = overlay_img.size
        if scale is not None:
            if isinstance(scale, (int, float)):
                overlay_w = int(overlay_w * scale)
                overlay_h = int(overlay_h * scale)
                overlay_img = overlay_img.resize(
                    (overlay_w, overlay_h), resample=resample_method
                )
            elif isinstance(scale, (list, tuple)) and len(scale) == 2:
                overlay_w = int(overlay_w * scale[0])
                overlay_h = int(overlay_h * scale[1])
                overlay_img = overlay_img.resize(
                    (overlay_w, overlay_h), resample=resample_method
                )
            elif isinstance(scale, dict):
                overlay_w = int(scale.get("width", overlay_w))
                overlay_h = int(scale.get("height", overlay_h))
                overlay_img = overlay_img.resize(
                    (overlay_w, overlay_h), resample=resample_method
                )
        else:
            overlay_w, overlay_h = overlay_img.size

        anchor = layer.get("anchor", "center")
        offset = tuple(layer.get("offset", [0, 0]))
        anchor_map = {
            "center": lambda: ((base_w - overlay_w) // 2, (base_h - overlay_h) // 2),
            "top_center": lambda: ((base_w - overlay_w) // 2, 0),
            "bottom_center": lambda: ((base_w - overlay_w) // 2, base_h - overlay_h),
            "left_center": lambda: (0, (base_h - overlay_h) // 2),
            "right_center": lambda: (base_w - overlay_w, (base_h - overlay_h) // 2),
            "bottom_left": lambda: (0, base_h - overlay_h),
            "bottom_right": lambda: (base_w - overlay_w, base_h - overlay_h),
            "top_right": lambda: (base_w - overlay_w, 0),
            "top_left": lambda: (0, 0),
        }
        anchor_x, anchor_y = anchor_map.get(anchor, anchor_map["center"])()
        paste_x = anchor_x + offset[0]
        paste_y = anchor_y + offset[1]
        temp = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        temp.paste(overlay_img, (paste_x, paste_y), overlay_img)
        base_img = Image.alpha_composite(base_img, temp)
    filename = output_template.format(index=idx, **layer_names)
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
