# Image Mixer

Image Mixer is a tool for compositing multiple image layers into a set of output images. Its primary use case is automatically generating recipe card images for a Minecraft Bedrock Edition addon — pulling ingredient textures directly from your behavior and resource packs — but it can be used for any image combination task.

---

## How it works

You define one or more **image mixers** in `data/image_mixer/config.json`. Each mixer describes a stack of image layers and how they should be combined. The tool resolves each layer to one or more image files, generates every combination, composites them in order, and saves the results.

---

## File structure

```
data/
  image_mixer/
    config.json          ← your mixer definitions
    texture_map.json     ← manual texture path overrides
BP/                      ← your behavior pack
RP/                      ← your resource pack
```

---

## config.json

The top-level structure is:

```jsonc
{
  "$schema": "https://raw.githubusercontent.com/thePixelmancer/regolith-filters/refs/heads/main/image_mixer/data/config.schema.json",
  "image_mixers": [ /* one or more mixer definitions */ ]
}
```

Including the `$schema` field is recommended — it enables autocomplete and validation in editors that support JSON Schema.

### Mixer definition

Each entry in `image_mixers` is a mixer object:

| Field | Type | Required | Description |
|---|---|---|---|
| `output_folder` | string | yes | Folder to write output images into. Created if it doesn't exist. |
| `output_template` | string | no | Filename template for output images. Defaults to `image_{index}.png`. |
| `combination_mode` | string | no | How layers are combined. `"cartesian"` (default) or `"zip"`. |
| `layers` | array | yes | Ordered list of layer definitions. |

### output_template

The template is a Python format string. Available placeholders:

| Placeholder | Value |
|---|---|
| `{index}` | Zero-based index of this combination |
| `{layer0}` | Filename stem of the first layer's resolved image |
| `{layer1}` | Filename stem of the second layer's resolved image |
| `{layerN}` | ...and so on for each layer |

Example: `"{index}_{layer1}_icon.png"` → `0_void_crystal_icon.png`

If a placeholder references a layer whose path resolved to nothing (a blank slot), its value will be `"none"`.

### combination_mode

Controls how multiple layers with multiple variants are combined.

**`cartesian`** (default) — generates every possible combination of variants across all layers. If layer A has 3 variants and layer B has 4 variants, you get 12 output images.

**`zip`** — pairs variants by index, like Python's `zip`. If layer A has 3 variants and layer B has 3 variants, you get 3 output images: A[0]+B[0], A[1]+B[1], A[2]+B[2]. Layers with only one variant are broadcast (repeated) to match the length of the longest layer. Layers with any other mismatched count will raise an error.

---

## Layer definition

Each layer in the `layers` array is an object:

| Field | Type | Default | Description |
|---|---|---|---|
| `path` | string, array, or blank | — | Image source. See [Path types](#path-types) below. |
| `anchor` | string | `"center"` | Where to position this layer relative to the base. See [Anchors](#anchors). |
| `offset` | [x, y] | `[0, 0]` | Pixel offset applied after anchoring. |
| `scale` | number, [x, y], or object | none | Scale factor(s) to apply. See [Scale](#scale). |
| `resample` | string | `"nearest"` | Resampling filter used when scaling. See [Resample](#resample). |
| `blend_mode` | string | `"normal"` | Blend mode. Currently only `"normal"` (alpha composite) is applied. |

The first layer in the list is always the **base image**. All subsequent layers are composited on top of it in order. The final output image has the same dimensions as the (scaled) base image.

### Path types

**Single file**
```jsonc
{ "path": "RP/textures/my_background.png" }
```
This layer always uses the same image. It contributes one variant.

**Directory**
```jsonc
{ "path": "RP/textures/icons/" }
```
All `.png` files in the directory are used, sorted alphabetically. The layer contributes one variant per file.

**Explicit list**
```jsonc
{ "path": ["RP/textures/a.png", "RP/textures/b.png", "none"] }
```
Each entry is used as a separate variant. Use `"none"`, `"None"`, `""`, or `null` for a blank slot (nothing composited for that variant).

**Recipe variable**
```jsonc
{ "path": "{shaped_slot_0}" }
```
Resolved from recipe data at startup. The layer contributes one variant per recipe. See [Recipe variables](#recipe-variables).

**Blank**
```jsonc
{ "path": "none" }
```
This layer is always skipped. Useful as a placeholder.

### Anchors

The anchor determines which point on the base image the overlay is aligned to before applying the offset.

| Value | Position |
|---|---|
| `center` | Centre of the base image (default) |
| `top_left` | Top-left corner |
| `top_center` | Top edge, horizontally centred |
| `top_right` | Top-right corner |
| `left_center` | Left edge, vertically centred |
| `right_center` | Right edge, vertically centred |
| `bottom_left` | Bottom-left corner |
| `bottom_center` | Bottom edge, horizontally centred |
| `bottom_right` | Bottom-right corner |

### Scale

**Scalar** — multiply both dimensions by the same factor:
```jsonc
{ "scale": 2 }
```

**Per-axis multiplier** — multiply width and height by different factors:
```jsonc
{ "scale": [2.0, 1.5] }
```

**Exact dimensions** — set absolute pixel size:
```jsonc
{ "scale": { "width": 32, "height": 32 } }
```

If `scale` is omitted, the image is used at its original size.

### Resample

The filter used when resizing. Only relevant when `scale` is set.

| Value | Description |
|---|---|
| `nearest` | Nearest-neighbour. Preserves hard pixel edges. Best for pixel art. (default) |
| `bilinear` | Linear interpolation. Smooth, fast. |
| `bicubic` | Cubic interpolation. Smoother than bilinear, slower. |
| `lanczos` | High-quality downsampling filter. |
| `box` | Box filter. Good for downscaling. |
| `hamming` | Similar to box but with less aliasing. |

---

## Recipe variables

When a layer path is a recipe variable placeholder, it is resolved to a list of texture paths — one per recipe of that type — at startup. This lets you drive image generation directly from your pack's recipe files.

All variables follow the format `{type_slotname}`.

### Shaped recipes (`minecraft:recipe_shaped`)

| Variable | Description |
|---|---|
| `{shaped_slot_0}` … `{shaped_slot_8}` | Ingredient texture at grid position 0–8 (row-major, left-to-right, top-to-bottom) |
| `{shaped_result}` | Result item texture |

Sub-3×3 patterns are automatically centred in the grid. For example, a 1×2 vertical pattern is placed in the centre column, slots 1 and 4.

### Shapeless recipes (`minecraft:recipe_shapeless`)

| Variable | Description |
|---|---|
| `{shapeless_slot_0}` … `{shapeless_slot_8}` | Ingredients in declaration order, expanded by count |
| `{shapeless_result}` | Result item texture |

Ingredients with `"count": N` are expanded into N consecutive slots. Unused slots beyond the ingredient count resolve to `None` (blank).

### Furnace recipes (`minecraft:recipe_furnace`)

| Variable | Description |
|---|---|
| `{furnace_slot_0}` | Input item texture |
| `{furnace_slot_1}` | Output item texture |

This covers all furnace-tag variants (`furnace`, `smoker`, `campfire`, `soul_campfire`) — the recipe file determines which stations accept it, not the variable.

---

## texture_map.json

This file contains manual texture path overrides. It is a flat JSON object mapping item identifiers (or tag names) to texture file paths:

```jsonc
{
  "minecraft:oak_planks": "RP/textures/blocks/planks_oak.png",
  "some_tag_name": "RP/textures/items/tag_icon.png"
}
```

Use this for:

- **Vanilla items** — items that exist in the vanilla behavior pack but whose textures are not in your RP
- **Tags** — recipe key entries that use `"tag"` instead of `"item"` cannot be resolved automatically; they always require an entry here
- **Any item** — you can override any item's texture here regardless of what the RP contains

### Texture resolution order

For every item identifier encountered in a recipe, the tool resolves it in this order:

1. Check `texture_map.json` for a manual override → use it if found
2. Look up the item in the behavior pack via reticulator → follow `minecraft:icon` → look up in `item_texture.json` → return the path
3. If the item is not found anywhere → **error**, the program stops

Tags skip step 2 entirely since they have no item definition. If a tag has no entry in `texture_map.json` the program stops with an error.

---

## Errors

**`TextureResolutionError`**
An item or tag referenced in a recipe could not be resolved to a texture. The error message will name the item/tag and tell you to add it to `texture_map.json`.

**`FileNotFoundError`**
A layer `path` points to a file or directory that does not exist.

**`ValueError`**
`combination_mode` is not `"cartesian"` or `"zip"`, or a `"zip"` layer has a variant count that is neither 1 nor equal to the longest layer.

**Large combination warning**
If a mixer would generate more than 500 images, the tool will print a warning and ask for confirmation before proceeding.

---

## Example config

See [config.json](config.md) for a full working example covering shaped, shapeless, and furnace recipe image generation.
