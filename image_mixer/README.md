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
    { "path": "RP/textures/frames" }, // 3 images
    { "path": "RP/textures/icons" } // 3 images
  ]
}
```

## How It Works

- The script computes all possible combinations of the provided layers (cartesian product).
- For each combination, it overlays the images in order, using anchor, scaling, and offset for placement.
- Image generation is parallelized using multithreading for speed.
- The output filename is generated from the template and saved in the output folder.

## Slot Variables: Dynamic Layer Paths for Recipes

When creating recipe images, you can use curly-brace `{}` variables in your config to dynamically reference recipe slots and results. These variables are replaced at runtime with the correct image path for each recipe.

**How do slot variables work?**

- For each recipe, the script extracts the item in each slot and the result, and builds a list of textures for each slot variable.
- For example, `{shaped_slot_0}` will resolve to a list of textures: one for each recipe, showing the item in slot 0 (or blank if the slot is empty for that recipe).
- `{shaped_result}` will resolve to a list of result item textures, one for each recipe.
- This means that when you use a slot variable in a layer, the script will generate one output image per recipe, overlaying the correct item (or blank) for each slot.

**Supported slot variables:**

- `{shaped_result}`: The output item of the recipe.
- `{shaped_slot_0}` to `{shaped_slot_8}`: The input slots for shaped recipes (left-to-right, top-to-bottom).

Example usage in a layer config:

```jsonc
{
  "path": "{shaped_slot_5}",
  "anchor": "top_left",
  "offset": [5, 0],
  "scale": { "width": 32, "height": 32 }
}
```

If a slot is empty for a recipe, the variable will resolve to `None` and the layer will be treated as blank. This ensures that the output image accurately reflects the recipe layout, including empty slots.

---

## Creating Recipe Images with Slot Variables

To generate recipe images that show the correct items in each slot, follow these steps:

1. **Use slot variables in your config:**

   - Reference `{shaped_slot_0}` to `{shaped_slot_8}` for input slots, and `{shaped_result}` for the output item.
   - Example:
     ```jsonc
     {
       "path": "{shaped_slot_0}", "anchor": "top_left", "offset": [x0, y0], "scale": {"width": 32, "height": 32}
     }
     {
       "path": "{shaped_result}", "anchor": "top_left", "offset": [rx, ry], "scale": {"width": 32, "height": 32}
     }
     ```
     Adjust `offset` for each slot to position items correctly in your background.

2. **Always use `zip` mode:**

   - Set `combination_mode` to `zip` in your config. This ensures each recipe's slots and result are matched by index, so the correct items appear in each output image.

3. **Explicitly define slot sizes:**

   - For all layers containing item pictures, set `scale` as an object with `width` and `height` (e.g., `{ "width": 32, "height": 32 }`).
   - This guarantees that, even if your item textures are different sizes, they will be resized to fit perfectly into their slots.

4. **Example recipe image config:**
   ```jsonc
   {
     "output_folder": "RP/textures/output/",
     "output_template": "recipe_{index}_{layer2}.png",
     "combination_mode": "zip",
     "layers": [
       { "path": "RP/textures/vanilla_recipe_background.png" },
       { "path": "{shaped_slot_0}", "anchor": "top_left", "offset": [5, 5], "scale": { "width": 32, "height": 32 } },
       { "path": "{shaped_slot_1}", "anchor": "top_left", "offset": [42, 5], "scale": { "width": 32, "height": 32 } },
       { "path": "{shaped_slot_2}", "anchor": "top_left", "offset": [79, 5], "scale": { "width": 32, "height": 32 } },
       { "path": "{shaped_result}", "anchor": "top_left", "offset": [120, 5], "scale": { "width": 32, "height": 32 } }
     ]
   }
   ```

**Tips:**

- Adjust `offset` values to match your background layout.
- You can omit unused slots or set their path to a blank value.
- The output filename can use `{layerN}` to include the item name in the filename.

---


## JSON Schema: Autocomplete & Validation

This tool supports JSON Schema for config files, enabling:

- **Autocomplete** for config fields, slot variables, and layer properties in editors like VS Code.
- **Validation** to catch typos, missing fields, and structural errors before running the script.

### How to Use

1. Make sure your config file includes a `$schema` property at the top:

   ```jsonc
   {
     "$schema": "https://raw.githubusercontent.com/thePixelmancer/regolith-filters/refs/heads/main/image_mixer/data/config.schema.json",
     "image_mixers": [ ... ]
   }
   ```

2. Open your config file in VS Code (or any schema-aware editor). You should see autocomplete suggestions and validation errors inline.

3. The schema is available at:
   - `https://raw.githubusercontent.com/thePixelmancer/regolith-filters/refs/heads/main/image_mixer/data/config.schema.json`
   - Or use a local path if working offline.

### Benefits

- Instantly see available fields, slot variable names, and valid values.
- Get warnings for missing or invalid properties before running the script.
- Easier onboarding for new users and contributors.

### Advanced

- You can customize the schema for your own extensions or stricter validation.
- The schema is updated as new features are added—always use the latest version for best results.

---
## Additional Tips & Notes

### Error Handling

- If your config references a variable that does not exist (e.g., a typo in `{shaped_slot_4}`), the script will print a clear error message and treat the layer as blank for that combination.
- If a file or directory path does not exist, the script will raise an error and skip that variant.

### Performance

- The script uses multithreading (`ThreadPoolExecutor`) to process images in parallel, which greatly speeds up batch generation.
- If you are generating a very large number of images (500+), the script will warn you and ask for confirmation before proceeding.

### Supported File Formats

- Only PNG images are supported for compositing. Other formats will be ignored or may cause errors.

### Layer Properties

- Each layer can specify:
  - `offset`: `[x, y]` pixel offset from the anchor position.
  - `anchor`: Placement anchor (`center`, `top_left`, etc.).
  - `blend_mode`: Only `normal` is supported (future versions may add more).
  - `scale`: Uniform (number), non-uniform (list), or absolute size (object with `width` and `height`).
  - `resample`: Resampling method for scaling (`NEAREST`, `BILINEAR`, `BICUBIC`, `LANCZOS`, `BOX`, `HAMMING`).

### Advanced Features

- You can use a directory as a layer path to automatically include all PNGs in that folder as variants.
- You can specify a list of file paths for a layer to control exactly which images are used and their order.
- Blank layers are supported and will be skipped in compositing.

### Custom Output Filenames

- The `output_template` field lets you customize output filenames using `{index}` (combination number) and `{layerN}` (filename stem for each layer).
- If a placeholder in the template does not match any layer, it will be skipped and a warning will be printed.

---

## Screenshots & Examples

### Example: Input Folder Structure

<img src="https://github.com/user-attachments/assets/c21b9460-e054-4b88-9921-f07738cf9899" alt="1" style="image-rendering: pixelated; image-rendering: crisp-edges; width: 100%; max-width: 600px;" />
<img src="https://github.com/user-attachments/assets/f9d6e2ea-0226-4ee8-b129-802dd8d796d0" alt="2" style="image-rendering: pixelated; image-rendering: crisp-edges; width: 100%; max-width: 600px;" />

### Example: Output Images (After Running Script)

<img src="https://github.com/user-attachments/assets/71738963-fc10-4ad4-adab-d437dc59defd" alt="3" style="image-rendering: pixelated; image-rendering: crisp-edges; width: 100%; max-width: 600px;" />

## License

MIT

---

## Changelog

### 1.2.0 (2025-07-25)

- You can now specify a list of file paths for a layer's `path` in the config, instead of just a directory or single file. This allows for precise control over which images are used and their order.
- Added a `zip` mode for combination generation. In `zip` mode, the script takes the first image from each layer and combines them, then the second image from each layer, and so on. If a layer has only one image, it is reused for every combination. In contrast, the default `cartesian` mode creates every possible combination of images from all layers (for example, if you have 2 backgrounds, 3 frames, and 3 icons, you get 2 × 3 × 3 = 18 images, covering every possible mix). Zip mode was added in anticipation of future support for automatically generating data from recipes, making it easier to create comprehensive recipe images.
- Improved code readability, refactored the codebase, and updated the documentation for clarity and maintainability.
  > **Note:** The original images used for generating composites are never deleted or moved by this script. If you do not want the source images to appear in your final RP (resource pack), simply place them outside your RP folder (for example, in a `data/` or `source/` directory). Only the generated output images will be saved to your specified output folder.
