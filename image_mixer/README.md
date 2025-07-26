# Recipe Image Creation: Best Practices

**Recipe image creation is intended to be used with the `zip` combination mode.**
This ensures that each recipe's layers are matched by index, so the correct item icons and slots are combined for each output image. Using `cartesian` mode will generate every possible combination, which is usually not desired for recipes.

**Recommended:** For all layers containing item pictures (such as icons or slot items), always define `scale` as an object with `width` and `height` (e.g., `{"width": 32, "height": 32}`). This guarantees that, even if your item textures are different sizes, they will be resized to fit perfectly into their slots in the final image. This avoids misaligned or oversized icons and ensures a consistent look for all recipe images.

Example layer config for an item icon:
```jsonc
{
  "path": "{shaped_result}",
  "scale": {"width": 32, "height": 32},
  "anchor": "top_left",
  "offset": [25, 0]
}
```

---
# Tutorial: Generating Recipe Images with image_mixer.py

This guide explains how to use `image_mixer.py` to generate recipe images for Minecraft resource packs. It covers setup, configuration, and usage in detail.

## Prerequisites

1. **Python 3.8+** installed on your system.
2. **Pillow** library for image processing:
   ```sh
   pip install pillow
   ```
3. Your workspace should have the following structure (simplified):
   ```
   image_mixer.py
   recipe_image_gen.py
   data/
     image_mixer/
       config.json
   RP/textures/
     vanilla_recipe_background.png
     output/
   BP/items/
   BP/recipes/
   ```

## Step 1: Prepare Your Images

- Place all base and overlay images (e.g., backgrounds, item icons) in appropriate folders, such as `RP/textures/`.
- Ensure all images are PNG format for compatibility.

## Step 2: Configure Your Recipes

- Recipe data should be in JSON format, e.g., in `BP/recipes/`.
- The script uses `recipe_image_gen.py` to flatten and extract recipe slot and result data.

## Step 3: Create the Mixer Config

Edit `data/image_mixer/config.json` to define how images are combined. Example:

```json
{
  "image_mixers": [
    {
      "output_folder": "RP/textures/output/",
      "output_template": "f{index}_{layer1}_icon.png",
      "combination_mode": "zip",
      "layers": [
        {
          "path": "RP/textures/vanilla_recipe_background.png",
          "blend_mode": "normal",
          "scale": 2
        },
        {
          "anchor": "top_left",
          "path": "{shaped_slot_5}",
          "offset": [5, 0],
          "blend_mode": "normal",
          "scale": {"width": 32, "height": 32}
        },
        {
          "anchor": "top_left",
          "path": "{shaped_result}",
          "offset": [25, 0],
          "blend_mode": "normal",
          "scale": {"width": 32, "height": 32}
        }
      ]
    }
  ]
}
```

### Config Fields Explained

- **output_folder**: Where generated images will be saved.
- **output_template**: Filename pattern. Use `{index}` for image number, `{layerN}` for layer names.
- **combination_mode**: `cartesian` (all combinations) or `zip` (match layers by index).
- **layers**: List of layer configs. Each layer can specify:
  - `path`: File path, directory, or variable (e.g., `{shaped_slot_5}`).
  - `anchor`: Where to place the overlay (`center`, `top_left`, etc.).
  - `offset`: [x, y] offset from anchor.
  - `blend_mode`: Only `normal` is supported.
  - `scale`: Number, [w, h], or `{width, height}` for resizing.
  - `resample`: Resampling method (`NEAREST`, `BILINEAR`, etc.).

## Step 4: Run the Script

Run the following command in your workspace:

```sh
python image_mixer.py
```

The script will read your config, process each recipe, and generate composite images in the specified output folder.

## Step 5: Troubleshooting

- If you see errors about missing files or variables, check your config paths and variable names.
- If a variable placeholder (e.g., `{shaped_slot_4}`) is not found, the script will print an error message.
- Make sure all referenced images exist and are accessible.

## Advanced Usage

- You can use directories as layer paths to include all PNGs in that folder.
- Blank layers can be specified with `"none"`, `None`, or `""`.
- The script supports both single and multiple variants per layer.

## Example Output

After running, you should see images like:

```
RP/textures/output/f0_void_fragment_icon.png
RP/textures/output/f1_void_crystal_icon.png
```

## Customization

- Edit `config.json` to change layer order, scaling, anchoring, and output naming.
- Add or remove layers as needed for your recipes.

---
For further help, review the code in `image_mixer.py` and `recipe_image_gen.py`, or ask for support.
## Changelog

### 1.2.0 (2025-07-25)
- You can now specify a list of file paths for a layer's `path` in the config, instead of just a directory or single file. This allows for precise control over which images are used and their order.
- Added a `zip` mode for combination generation. In `zip` mode, the script takes the first image from each layer and combines them, then the second image from each layer, and so on. If a layer has only one image, it is reused for every combination. In contrast, the default `cartesian` mode creates every possible combination of images from all layers (for example, if you have 2 backgrounds, 3 frames, and 3 icons, you get 2 × 3 × 3 = 18 images, covering every possible mix). Zip mode was added in anticipation of future support for automatically generating data from recipes, making it easier to create comprehensive recipe images.
- Improved code readability, refactored the codebase, and updated the documentation for clarity and maintainability.
> **Note:** The original images used for generating composites are never deleted or moved by this script. If you do not want the source images to appear in your final RP (resource pack), simply place them outside your RP folder (for example, in a `data/` or `source/` directory). Only the generated output images will be saved to your specified output folder.
<p align="center">
 <img width="100%" alt="banner" src="https://github.com/user-attachments/assets/3b42c3dc-2fbf-4659-b170-946c7c2e2a4b" />
</p>

A flexible, scriptable Python tool for batch-generating composite images from layered PNGs, with support for anchor positioning, scaling, offsets, and customizable output filenames.

## Why use this?
This script is ideal for creating many composite image combinations from a few input images. It's especially handy for:
- Generating recipe images (e.g., for games, apps, or wikis)
- Adding backgrounds, frames, or effects to icons for UI elements
- Combining texture variants for resource packs, modding, or asset pipelines
- Automating the creation of image sets for GUIs, previews, or batch art tasks

- Fast: Uses multithreading to generate images in parallel for much faster batch processing.
- Combine multiple image layers (backgrounds, frames, icons, etc.) into new images.
- Supports both single files and directories of images for each layer.
- Flexible anchor system: overlays are centered by default, but you can place overlays at corners, edges, or custom offsets.
- Powerful scaling: scale overlays uniformly, non-uniformly, or to an exact pixel size, with selectable resampling methods (nearest, bilinear, bicubic, lanczos, box, hamming).
- Output filenames are fully customizable using templates (e.g., `output_{index}_{layer1}_{layer2}.png`).
- Simple, human-readable JSON configuration for batch processing.

## Requirements
- Python 3.7+
- [Pillow](https://python-pillow.org/) (PIL fork)

Install dependencies:
```bash
pip install pillow
```

## Usage
1. **Configure your layers** in a JSON file (see example below).
2. **Run regolith:**
   ```bash
   regolith run
   ```
3. **Find your output images** in the specified output folder.

## Example Configuration

### Note on Empty Layer Variants

If a layer's `path` is set to `None`, an empty string (`""`), or the string `"none"` or `"None"`, or is not a valid file, that variant will be counted as an empty (blank) layer. **The combination will still be generated, but nothing will be overlayed for that layer in that output.**

This allows you to intentionally include empty slots in your combinations. For example:

```jsonc
{
  "layers": [
    {
      "path": ["icon1.png", "none", "icon2.png"]
    }
  ]
}
```
In this example, the second variant will be empty (no overlay), but the output will still be generated for that combination.
```jsonc
{
  "image_mixers": [
    {
      "output_folder": "RP/textures/output/",
      "output_template": "icon_{index}_{layer1}_{layer2}.png",
      "combination_mode": "cartesian", // or "zip" (optional, default: "cartesian")
      "layers": [
        { "path": "RP/textures/background.png", "offset": [0, 0] },
        { "path": "RP/textures/frames", "offset": [0, 0] },
        {
          "path": "RP/textures/icons",
          "scale": [1, 2], // Non-uniform scaling: width x1, height x2
          "resample": "lanczos", // Optional: resampling method (nearest, bilinear, bicubic, lanczos, box, hamming)
          "offset": [0, 0]
        }
      ]
## Combination Modes

You can control how image combinations are generated using the `combination_mode` option in your config:

**cartesian** (default): All possible combinations of all layers (cartesian product).
  - Example: 2 backgrounds × 3 frames × 3 icons = 18 images.
  
  ```
  backgrounds:  [A] [B]
  frames:       [1] [2] [3]
  icons:        [X] [Y] [Z]

  Output (cartesian):
  [A][1][X]  [A][1][Y]  [A][1][Z]
  [A][2][X]  [A][2][Y]  [A][2][Z]
  [A][3][X]  [A][3][Y]  [A][3][Z]
  [B][1][X]  [B][1][Y]  [B][1][Z]
  [B][2][X]  [B][2][Y]  [B][2][Z]
  [B][3][X]  [B][3][Y]  [B][3][Z]
  ```
**zip**: Layers are matched by index (like Python's `zip`).
  - Single-image layers are automatically repeated (broadcast) to match the length of the longest layer.
  - Example: If you have 1 background, 3 frames, and 3 icons, the background is used for each frame+icon pair, producing 3 images:
  ```
  backgrounds:  [A]
  frames:       [1] [2] [3]
  icons:        [X] [Y] [Z]

  Output (zip):
  [A][1][X]
  [A][2][Y]
  [A][3][Z]
  ```
  - If a layer has a number of images that is not 1 or the same as the longest layer, an error is raised.
  - **Tip:** Zip mode is best used when you define image paths as a list for each layer, so you have full control over which images are combined together in each output.

  For example, with lists:
  ```
  backgrounds:  [A] [B] [C]
  frames:       [1] [2] [3]
  icons:        [X] [Y] [Z]

  Output (zip):
  [A][1][X]
  [B][2][Y]
  [C][3][Z]
  ```

**Example zip mode config:**
```jsonc
{
  "output_folder": "RP/textures/output/",
  "output_template": "icon_{index}_{layer1}_{layer2}.png",
  "combination_mode": "zip",
  "layers": [
    { "path": "RP/textures/background.png" }, // 1 image, will be repeated
    { "path": "RP/textures/frames" },         // 3 images
    { "path": "RP/textures/icons" }           // 3 images
  ]
}
```
    }
  ]
}
```
- `output_template` can use `{index}` (combination number) and `{layer0}`, `{layer1}`, etc. (filename stem for each layer).
- Each `layer` can be a single PNG file or a directory of PNGs.
- **output_template**: Use `{index}` (combination number) and `{layer0}`, `{layer1}`, etc. (filename stem for each layer).
- **Each layer** can be a single PNG file or a directory of PNGs.
- **anchor**: `center` (default), `top_left`, `top_center`, `bottom_center`, `left_center`, `right_center`, `bottom_left`, `bottom_right`, `top_right`.
- **offset**: `[x, y]` in pixels, applied after anchor positioning.
- **scale**:
  - Single number (e.g. `2.0`) for uniform scaling
  - List of two numbers (e.g. `[1, 2]`) for non-uniform scaling (width, height)
  - Object with `width` and `height` for absolute pixel size (e.g. `{ "width": 64, "height": 32 }`)
- **resample** (optional): Scaling method: `nearest` (default), `bilinear`, `bicubic`, `lanczos`, `box`, or `hamming`.

- The script computes all possible combinations of the provided layers (cartesian product).
- For each combination, it overlays the images in order, using anchor, scaling, and offset for placement.
- The output filename is generated from the template and saved in the output folder.
## How It Works
- The script computes all possible combinations of the provided layers (cartesian product).
- For each combination, it overlays the images in order, using anchor, scaling, and offset for placement.
- Image generation is parallelized using multithreading for speed.
- The output filename is generated from the template and saved in the output folder.

## License
MIT

## Screenshots & Examples

### Example: Input Folder Structure
<img src="https://github.com/user-attachments/assets/c21b9460-e054-4b88-9921-f07738cf9899" alt="1" style="image-rendering: pixelated; image-rendering: crisp-edges; width: 100%; max-width: 600px;" />
<img src="https://github.com/user-attachments/assets/f9d6e2ea-0226-4ee8-b129-802dd8d796d0" alt="2" style="image-rendering: pixelated; image-rendering: crisp-edges; width: 100%; max-width: 600px;" />

### Example: Output Images (After Running Script)
<img src="https://github.com/user-attachments/assets/71738963-fc10-4ad4-adab-d437dc59defd" alt="3" style="image-rendering: pixelated; image-rendering: crisp-edges; width: 100%; max-width: 600px;" />

---

**Contributions, suggestions, and issues welcome!**
