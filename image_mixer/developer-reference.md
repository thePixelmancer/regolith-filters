# Developer reference

Internal architecture and code documentation for `image_mixer.py` and `recipe_image_gen.py`.

---

## Overview

The program is split into two modules:

`recipe_image_gen.py` — reads the Minecraft project (behavior pack + resource pack) and resolves all recipe data into flat lists of texture paths, one entry per recipe per slot.

`image_mixer.py` — reads `config.json`, resolves layer configs into lists of image variants, generates combinations of those variants, and composites + saves the output images. It imports `recipe_image_gen` at startup and exposes recipe slot data as config-level variables.

---

## recipe_image_gen.py

### Globals

| Name | Type | Description |
|---|---|---|
| `TEXTURE_MAP` | `dict[str, str]` | Loaded from `data/image_mixer/texture_map.json`. Maps item identifiers and tag names to texture file paths. |
| `project` | `Project` | Reticulator project pointing at `BP/` and `RP/`. |
| `vanilla` | `Project` | Reticulator project pointing at the vanilla pack copies. |
| `BP` | `BehaviorPack` | Behavior pack from `project`. |
| `RP` | `ResourcePack` | Resource pack from `project`. |

### TextureResolutionError

```python
class TextureResolutionError(Exception)
```

Raised when a named item identifier cannot be found in either `TEXTURE_MAP` or the behavior pack via reticulator. Also raised when a tag name has no entry in `TEXTURE_MAP` (tags cannot be resolved automatically).

Never raised for empty/blank slots — those legitimately return `None`.

---

### get_item_texture_path

```python
def get_item_texture_path(item_name: str | None) -> str | None
```

Resolves an item identifier to a texture file path.

Resolution order:
1. `item_name` is `None` or blank → return `None` (empty slot, not an error)
2. `item_name` is in `TEXTURE_MAP` → return the override path
3. Reticulator finds the item in BP → follow `minecraft:icon` → look up shortname in `item_texture.json` → return `RP/<path>.png`
4. Reticulator does not find the item → raise `TextureResolutionError`

Steps 3's intermediate lookups (`minecraft:icon` missing, shortname missing, texture data missing) return `None` rather than raising — reticulator may locate vanilla items whose textures are not present in the scanned RP, and this is not a configuration error.

---

### get_tag_texture_path

```python
def get_tag_texture_path(tag_name: str) -> str | None
```

Resolves a recipe tag name to a texture file path via `TEXTURE_MAP` only. Tags have no item definition to look up, so a manual override is the only resolution mechanism. Raises `TextureResolutionError` if no entry exists.

---

### get_slot_texture_path

```python
def get_slot_texture_path(slot_entry: dict | None) -> str | None
```

Dispatcher that accepts a raw recipe key entry dict (e.g. `{"item": "minecraft:oak_planks"}` or `{"tag": "some_tag"}`) and routes to `get_item_texture_path` or `get_tag_texture_path`. Returns `None` for empty/missing entries.

---

### flatten_recipe_pattern

```python
def flatten_recipe_pattern(pattern: list[str], key: dict) -> list[dict | None]
```

Converts a shaped recipe `pattern` + `key` into a 9-element list of key entry dicts (or `None` for empty slots), in row-major order for a 3×3 grid.

Sub-3×3 patterns are centred in the grid using integer division:

```python
row_offset = (3 - pattern_rows) // 2
col_offset = (3 - pattern_cols) // 2
```

This means a 1×2 vertical pattern lands in column 1 (slots 1, 4), and a 2×2 pattern lands at slots 0, 1, 3, 4. Centering is left-biased for even sizes.

---

### get_shaped_slot_textures / get_shapeless_slot_textures / get_furnace_slot_textures

```python
def get_shaped_slot_textures(recipe_data: dict) -> dict
def get_shapeless_slot_textures(recipe_data: dict) -> dict
def get_furnace_slot_textures(recipe_data: dict) -> dict
```

Each accepts the inner recipe data dict (the value under `"minecraft:recipe_shaped"` etc.) and returns:

```python
{
    "id":     str,           # recipe identifier
    "slots":  list[str | None],  # resolved texture paths, one per slot
    "result": str | None,   # result texture (shaped and shapeless only)
}
```

`get_shapeless_slot_textures` expands ingredients with `count > 1` into repeated consecutive slot entries before resolving. It works on the full ingredient dict (not just the item name) so tag entries survive expansion.

`get_furnace_slot_textures` has no `"result"` key — the output item is slot 1.

---

### _append_slots

```python
def _append_slots(store: dict, slot_textures: dict, num_slots: int) -> None
```

Appends one recipe's resolved data into the slot-indexed store structure. Writes to `store["slots"][i]` for each slot index, and to `store["result"]` if that key exists. This is what builds the parallel lists that recipe variables ultimately reference.

---

### get_flattened_recipe_data

```python
def get_flattened_recipe_data() -> dict
```

Iterates all recipes in `BP.recipes`, identifies the recipe type, dispatches to the appropriate handler, and accumulates results into:

```python
{
    "shaped": {
        "slots": [
            [slot0_recipe0, slot0_recipe1, ...],  # index 0
            [slot1_recipe0, slot1_recipe1, ...],  # index 1
            # ... 9 lists total
        ],
        "result": [result_recipe0, result_recipe1, ...]
    },
    "shapeless": { /* same structure, 9 slots */ },
    "furnace":   { /* same structure, 2 slots, no result key */ }
}
```

Each list at `slots[i]` has one entry per recipe, so `slots[i][j]` is the texture path for slot `i` of recipe `j`. This parallel-list structure is what allows `zip` combination mode to pair slot variables correctly across layers.

The dispatch table:

```python
recipe_handlers = {
    "minecraft:recipe_shaped":    ("shaped",    get_shaped_slot_textures,    9),
    "minecraft:recipe_shapeless": ("shapeless", get_shapeless_slot_textures, 9),
    "minecraft:recipe_furnace":   ("furnace",   get_furnace_slot_textures,   2),
}
```

Adding support for a new recipe type means adding one entry here and writing a handler function.

---

## image_mixer.py

### Globals

| Name | Type | Description |
|---|---|---|
| `RECIPE_DATA` | `dict` | Output of `rig.get_flattened_recipe_data()`. Built at import time; raises `SystemExit` on `TextureResolutionError`. |
| `VARIABLE_MAP` | `dict[str, list]` | Maps variable placeholder strings like `"{shaped_slot_0}"` to their corresponding recipe data lists. |
| `BLANK_VALUES` | `set` | `{None, "none", "None", ""}` — all values treated as intentionally empty paths. |

---

### Combination strategies

```python
def cartesian_combinations(all_layers: list[list[dict]]) -> list[tuple[dict, ...]]
def zip_combinations(all_layers: list[list[dict]]) -> list[tuple[dict, ...]]
```

Both accept a list of layer variant lists and return a list of combinations (tuples).

`cartesian_combinations` uses `itertools.product` — every possible combination.

`zip_combinations` matches by index. Single-variant layers are broadcast (repeated) to the length of the longest layer. Raises `ValueError` if any layer has a count that is neither 1 nor the max length.

---

### Layer variant resolution

```python
def get_layer_variants(layer: dict) -> list[dict]
```

Resolves a single layer config dict to a list of variant dicts. Each variant is a copy of the layer's properties (`offset`, `anchor`, `scale`, `resample`, `blend_mode`) with a resolved `path` value (`Path` object or `None`).

Path resolution logic:

| `path` value | Result |
|---|---|
| Blank (`None`, `"none"`, `""`, etc.) | `[{..., "path": None}]` |
| Variable (`"{shaped_slot_0}"` etc.) | One variant per entry in `VARIABLE_MAP[placeholder]` |
| List of strings | One variant per entry; blanks → `None`, files validated |
| Directory path | One variant per `.png` file, sorted alphabetically |
| Single file path | One variant |
| Anything else | `FileNotFoundError` |

```python
def expand_layers(layers: list[dict]) -> list[list[dict]]
```

Maps `get_layer_variants` over a list of layer configs. Returns the expanded list-of-lists consumed by the combination functions.

---

### Image compositing

```python
def _get_resample(method: str | None) -> Image.Resampling
```

Converts a string like `"nearest"` to the corresponding `Image.Resampling` enum value via `getattr`. Defaults to `NEAREST`.

```python
def _scale_image(img, scale, resample) -> Image.Image
```

Resizes an image. `scale` can be a scalar, `[x, y]` list, or `{"width": w, "height": h}` dict.

```python
def _get_paste_position(anchor, base_size, overlay_size, offset) -> tuple[int, int]
```

Returns the top-left pixel coordinate at which to paste an overlay, given the anchor name and pixel offset.

```python
def composite_layers(combination: tuple[dict, ...]) -> Image.Image | None
```

Composites a tuple of layer variants into a single RGBA image. The first variant is the base; all others are pasted on top in order using `Image.alpha_composite`. Returns `None` if the base layer has no path.

```python
def _format_filename(template, idx, combination) -> str
```

Formats the output filename. Falls back by stripping unknown placeholders if a `KeyError` occurs. Final fallback is `image_{idx}.png`.

```python
def process_combination(idx, combination, output_template, output_folder) -> None
```

Calls `composite_layers` and saves the result. Called from a thread pool — exceptions propagate back to the main thread via `future.result()`.

---

### generate_images

```python
def generate_images(image_mixer: dict) -> None
```

Main entry point per mixer. Creates the output folder, validates `combination_mode`, generates all combinations, warns and prompts if count exceeds 500, then dispatches to a `ThreadPoolExecutor`. Exceptions from worker threads are re-raised in the main thread via `future.result()` inside `as_completed`.

---

### Entry point

```python
if __name__ == "__main__":
    config_path = Path("data/image_mixer/config.json")
    ...
    for image_mixer in config["image_mixers"]:
        generate_images(image_mixer)
```

Loads `config.json` and calls `generate_images` for each mixer. Warns if the `$schema` key is missing from the config.
