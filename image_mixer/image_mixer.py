
import json
import itertools
from pathlib import Path
from PIL import Image


# -------------------------------------------------------------------------------------- #
def generate_combinations(layers):
    """
    For each layer in the config, build a list of possible layer variants.
    If a layer path is a directory, include all PNG files in that directory as variants.
    Returns a list of all possible combinations (cartesian product) of layers.
    """
    all_layers = []
    for layer in layers:
        layer_path = Path(layer["path"])
        if layer_path.is_dir():
            # If the layer is a directory, add each PNG file as a variant
            final_layer = [
                {
                    "path": str(file),
                    "offset": layer.get("offset", [0, 0]),
                    "blend_mode": layer.get("blend_mode", "normal"),
                    "suffix": f"_{file.stem}",
                    "anchor": layer.get("anchor", "top_left"),
                }
                for file in layer_path.glob("*.png")
            ]
        else:
            # If the layer is a single file, just add it as a single variant
            final_layer = [
                {
                    "path": str(layer_path),
                    "offset": layer.get("offset", [0, 0]),
                    "blend_mode": layer.get("blend_mode", "normal"),
                    "suffix": layer.get("suffix", ""),
                    "anchor": layer.get("anchor", "top_left"),
                }
            ]
        all_layers.append(final_layer)
    # Return all possible combinations of layers (cartesian product)
    return list(itertools.product(*all_layers))



def generate_images(image_mixer):
    """
    For a given image_mixer config, generate all image combinations and save them.
    Each combination overlays the layers in order, using anchor and offset for placement.
    Output filenames are built from a template with variables for index and layer names.
    """
    output_folder = Path(image_mixer["output_folder"])
    output_folder.mkdir(parents=True, exist_ok=True)
    output_template = image_mixer.get("output_template", "image_{index}.png")
    layer_combinations = generate_combinations(image_mixer["layers"])

    for idx, combination in enumerate(layer_combinations):
        # Open the first layer as the base image
        base_layer = combination[0]
        base_img = Image.open(base_layer["path"]).convert("RGBA")
        # Build a dict of layer names for use in the output template
        layer_names = {}
        for i, layer in enumerate(combination):
            # Store the stem (filename without extension) for each layer
            layer_names[f"layer{i}"] = Path(layer["path"]).stem
        # Overlay each subsequent layer
        for layer in combination[1:]:
            overlay_img = Image.open(layer["path"]).convert("RGBA")
            base_w, base_h = base_img.size
            overlay_w, overlay_h = overlay_img.size
            anchor = layer.get("anchor", "top_left")
            offset = tuple(layer.get("offset", [0, 0]))

            # Map anchor names to position calculation lambdas
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
            # Calculate anchor position and apply offset
            anchor_x, anchor_y = anchor_map.get(anchor, anchor_map["center"])()
            paste_x = anchor_x + offset[0]
            paste_y = anchor_y + offset[1]

            # Paste the overlay image onto a transparent temp image, then composite
            temp = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
            temp.paste(overlay_img, (paste_x, paste_y), overlay_img)
            base_img = Image.alpha_composite(base_img, temp)
        # Build output filename from template, using index and layer names
        filename = output_template.format(index=idx, **layer_names)
        out_path = Path(output_folder) / filename
        base_img.save(out_path)


# -------------------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Load the config file and generate images for each image_mixer entry
    config_path = Path("data/image_mixer/config.json")
    with config_path.open("r") as f:
        config = json.load(f)
    for image_mixer in config["image_mixers"]:
        generate_images(image_mixer)
