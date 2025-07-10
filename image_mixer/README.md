
# Regolith Image Mixer

A flexible Python tool for batch-generating composite images from layered PNGs, with support for anchor positioning, offsets, and customizable output filenames.

## What is this for?
This script is useful for creating composite image combinations from a few input images. It's especially handy for:
- Generating recipe images (e.g., for games or apps)
- Adding backgrounds or frames to icons for UI elements
- Combining texture variants for resource packs or asset pipelines
- Any scenario where you want to automate the creation of many images from a small set of base layers

## Features
- Combine multiple image layers (backgrounds, frames, icons, etc.) into new images.
- Supports both single files and directories of images for each layer.
- Flexible anchor system: overlays are centered by default, but you can place overlays at corners, edges, or custom offsets.
- Powerful scaling: scale overlays uniformly, non-uniformly, or to an exact pixel size, with selectable resampling methods.
- Output filenames are fully customizable using templates (e.g., `output_{index}_{layer1}_{layer2}.png`).
- Simple JSON configuration for batch processing.

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
- Supported `anchor` values: `center` (default), `top_left`, `top_center`, `bottom_center`, `left_center`, `right_center`, `bottom_left`, `bottom_right`, `top_right`.
- `offset` is `[x, y]` in pixels, applied after anchor positioning.
- `scale` can be:
  - a single number (e.g. `2.0`) for uniform scaling
  - a list of two numbers (e.g. `[1, 2]`) for non-uniform scaling (width, height)
  - an object with `width` and `height` for absolute pixel size (e.g. `{ "width": 64, "height": 32 }`)
- `resample` (optional) sets the scaling method: `nearest` (default), `bilinear`, `bicubic`, `lanczos`, `box`, or `hamming`.

## How It Works
- The script computes all possible combinations of the provided layers (cartesian product).
- For each combination, it overlays the images in order, using anchor and offset for placement.
- The output filename is generated from the template and saved in the output folder.

## License
MIT

---

**Contributions and issues welcome!**
