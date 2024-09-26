import json
from PIL import Image
from pathlib import Path
import itertools


# Function to overlay images with scaling and offsets
def overlay_image(base_image, overlay_image):
    # Get the sizes of both images
    base_width, base_height = base_image.size
    overlay_width, overlay_height = overlay_image.size

    # Calculate the size of the output image (largest width and height)
    output_width = max(base_width, overlay_width)
    output_height = max(base_height, overlay_height)

    # Create a new blank image with the size of the largest image
    canvas = Image.new("RGBA", (output_width, output_height), (0, 0, 0, 0))

    # Calculate the position to paste the base image (centered)
    base_x = (output_width - base_width) // 2
    base_y = (output_height - base_height) // 2

    # Paste the base image onto the output image
    canvas.paste(base_image, (base_x, base_y))

    # Calculate the position to paste the overlay image (centered)
    overlay_x = (output_width - overlay_width) // 2
    overlay_y = (output_height - overlay_height) // 2

    # Paste the overlay image onto the output image
    canvas.paste(overlay_image, (overlay_x, overlay_y), overlay_image)
    return canvas


# -------------------------------------------------------------------------------------- #
def offset_image(image, offset):
    width, height = image.size
    new_width = width + offset[0] * 2
    new_height = height + offset[1] * 2
    canvas = Image.new("RGBA", (new_width, new_height), (0, 0, 0, 0))

    offset_x = (canvas.width - image.width) // 2 + offset[0]
    offset_y = (canvas.height - image.height) // 2 + offset[1]
    canvas.paste(image, (offset_x, offset_y))
    return canvas


# -------------------------------------------------------------------------------------- #
def generate_combinations(layers):
    all_layers = []

    for layer in layers:
        layer_path = Path(layer["path"])
        final_layer = []

        if layer_path.is_dir():  # If the path is a directory
            # Find all PNG files in the directory
            for file in layer_path.glob("*.png"):
                final_layer.append(
                    {
                        "path": str(file),
                        "offset": layer["offset"],
                        "blend_mode": layer["blend_mode"],
                        "suffix": "_" + file.stem,
                    }
                )
        else:  # It's a single file
            final_layer.append(
                {
                    "path": str(layer_path),
                    "offset": layer["offset"],
                    "blend_mode": layer["blend_mode"],
                    "suffix": "",
                }
            )

        all_layers.append(final_layer)

    return list(itertools.product(*all_layers))


def generate_images(generator):
    output_folder = Path(generator["output_folder"])
    output_folder.mkdir(parents=True, exist_ok=True)
    output_suffix = generator["output_suffix"]
    output_prefix = generator["output_prefix"]
    layer_combinations = generate_combinations(generator["layers"])
    for combination in layer_combinations:
        image = Image.open(combination[0]["path"])
        variant_suffix = ""
        for layer in combination[1:]:
            print(layer)
            image = overlay_image(
                image,
                offset_image(Image.open(layer["path"]), layer["offset"]),
            )
            if layer["suffix"]:
                variant_suffix += layer["suffix"]
        image.save(
            Path(output_folder)
            / f"{output_prefix}{variant_suffix.lstrip('_')}{output_suffix}.png"
        )


# -------------------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Load JSON config
    with Path("data/image_generators.json").open("r") as f:
        config = json.load(f)

    # Ensure output directory exists
    for generator in config["generators"]:
        generate_images(generator)
