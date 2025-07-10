
import json
import itertools
from pathlib import Path
from PIL import Image
import concurrent.futures
try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

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
        # Collect all relevant properties to copy to each file entry
        layer_props = {
            "offset": layer.get("offset", [0, 0]),
            "blend_mode": layer.get("blend_mode", "normal"),
            "anchor": layer.get("anchor", "center"),
            "scale": layer.get("scale", None),
            "resample": layer.get("resample", None),
            "suffix": layer.get("suffix", ""),
        }
        if layer_path.is_dir():
            # If the layer is a directory, add each PNG file as a variant
            final_layer = [
                dict(layer_props, path=str(file), suffix=f"_{file.stem}")
                for file in layer_path.glob("*.png")
            ]
        else:
            # If the layer is a single file, just add it as a single variant
            final_layer = [dict(layer_props, path=str(layer_path))]
        all_layers.append(final_layer)
    # Return all possible combinations of layers (cartesian product)
    return list(itertools.product(*all_layers))

def process_combination(idx, combination, output_template, output_folder):
    base_layer = combination[0]
    base_img = Image.open(base_layer["path"]).convert("RGBA")
    layer_names = {}
    for i, layer in enumerate(combination):
        layer_names[f"layer{i}"] = Path(layer["path"]).stem
    for layer in combination[1:]:
        overlay_img = Image.open(layer["path"]).convert("RGBA")
        base_w, base_h = base_img.size
        scale = layer.get("scale", None)
        resample_str = (layer.get("resample") or "nearest").upper()
        resample_map = {
            "NEAREST": Image.NEAREST,
            "BILINEAR": Image.BILINEAR,
            "BICUBIC": Image.BICUBIC,
            "LANCZOS": Image.LANCZOS,
            "BOX": Image.BOX,
            "HAMMING": Image.HAMMING,
        }
        resample_method = resample_map.get(resample_str, Image.NEAREST)
        overlay_w, overlay_h = overlay_img.size
        if scale is not None:
            if isinstance(scale, (int, float)):
                overlay_w = int(overlay_w * scale)
                overlay_h = int(overlay_h * scale)
                overlay_img = overlay_img.resize((overlay_w, overlay_h), resample=resample_method)
            elif isinstance(scale, (list, tuple)) and len(scale) == 2:
                overlay_w = int(overlay_w * scale[0])
                overlay_h = int(overlay_h * scale[1])
                overlay_img = overlay_img.resize((overlay_w, overlay_h), resample=resample_method)
            elif isinstance(scale, dict):
                overlay_w = int(scale.get("width", overlay_w))
                overlay_h = int(scale.get("height", overlay_h))
                overlay_img = overlay_img.resize((overlay_w, overlay_h), resample=resample_method)
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
    For a given image_mixer config, generate all image combinations and save them.
    Each combination overlays the layers in order, using anchor and offset for placement.
    Output filenames are built from a template with variables for index and layer names.
    """
    output_folder = Path(image_mixer["output_folder"])
    output_folder.mkdir(parents=True, exist_ok=True)
    output_template = image_mixer.get("output_template", "image_{index}.png")
    layer_combinations = generate_combinations(image_mixer["layers"])


    total = len(layer_combinations)
    if total > 500:
        print(f"[WARNING] You are about to generate {total} images. This may heavily load your system.")
        while True:
            resp = input("Do you want to continue? (Y/N): ").strip().lower()
            if resp == 'y':
                break
            elif resp == 'n':
                print("Aborted by user.")
                return
    with concurrent.futures.ThreadPoolExecutor() as executor:
        if tqdm:
            futures = [
                executor.submit(process_combination, idx, combination, output_template, output_folder)
                for idx, combination in enumerate(layer_combinations)
            ]
            for f in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Generating images"):
                f.result()
        else:
            futures = [
                executor.submit(process_combination, idx, combination, output_template, output_folder)
                for idx, combination in enumerate(layer_combinations)
            ]
            concurrent.futures.wait(futures)
        if tqdm is None:
            print("(Install tqdm for a progress bar: pip install tqdm)")

# -------------------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Load the config file and generate images for each image_mixer entry
    config_path = Path("data/image_mixer/config.json")
    with config_path.open("r") as f:
        config = json.load(f)
    for image_mixer in config["image_mixers"]:
        generate_images(image_mixer)
