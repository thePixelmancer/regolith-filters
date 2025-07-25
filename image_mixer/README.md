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

- **cartesian** (default): All possible combinations of all layers (cartesian product).
  - Example: 2 backgrounds × 3 frames × 3 icons = 18 images.
- **zip**: Layers are matched by index (like Python's `zip`).
  - Single-image layers are automatically repeated (broadcast) to match the length of the longest layer.
  - Example: If you have 1 background, 3 frames, and 3 icons, the background is used for each frame+icon pair, producing 3 images:
    - (background, frame0, icon0)
    - (background, frame1, icon1)
    - (background, frame2, icon2)
  - If a layer has a number of images that is not 1 or the same as the longest layer, an error is raised.

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
