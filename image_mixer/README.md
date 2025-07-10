# Regolith Image Mixer

A flexible, scriptable Python tool for batch-generating composite images from layered PNGs, with support for anchor positioning, scaling, offsets, and customizable output filenames.

## Why use this?
This script is ideal for creating many composite image combinations from a few input images. It's especially handy for:
- Generating recipe images (e.g., for games, apps, or wikis)
- Adding backgrounds, frames, or effects to icons for UI elements
- Combining texture variants for resource packs, modding, or asset pipelines
- Automating the creation of image sets for GUIs, previews, or batch art tasks

## Features
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
2. **Run the script:**
   ```bash
   python image_mixer.py
   ```
3. **Find your output images** in the specified output folder.

## Example Configuration
```jsonc
{
  "image_mixers": [
    {
      "output_folder": "RP/textures/output/",
      "output_template": "output_{index}_{layer1}_{layer2}.png",
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

## How It Works
- The script computes all possible combinations of the provided layers (cartesian product).
- For each combination, it overlays the images in order, using anchor, scaling, and offset for placement.
- The output filename is generated from the template and saved in the output folder.

## License
MIT

## Screenshots & Examples

<!--
Replace these placeholders with your own screenshots!
-->

### Example: Input Folder Structure
![Input Folder Structure](docs/screenshots/input_structure.png)

### Example: Output Images (After Running Script)
![Output Images](docs/screenshots/output_images.png)

### Example: Output Image Preview
![Sample Output Image](docs/screenshots/sample_output.png)

---

**Contributions, suggestions, and issues welcome!**
