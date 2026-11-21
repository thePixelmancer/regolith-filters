# Mixer file reference

Annotated examples covering shaped, shapeless, and furnace recipe image generation. Each example is a separate file in `data/image_mixer/mixers/`. Add the `$schema` line to every file to enable validation and autocomplete in supporting editors.

## shaped.json

```jsonc
{
  "$schema": "https://raw.githubusercontent.com/thePixelmancer/regolith-filters/refs/heads/main/image_mixer/data/config.schema.json",

  // Generates one image per shaped recipe.
  // The 3x3 grid of ingredient slots maps to shaped_slot_0 through shaped_slot_8:
  //
  //   slot_0 | slot_1 | slot_2
  //   slot_3 | slot_4 | slot_5
  //   slot_6 | slot_7 | slot_8
  //
  // Sub-3x3 patterns are automatically centred in the grid.
  "output_folder": "RP/textures/output/shaped/",

  // {recipe_id} = recipe identifier without its namespace; {index} = combination index
  "output_template": "{recipe_id}.png",

  // zip: one output image per recipe, pairing each slot variable with
  // the same recipe index across all layers
  "combination_mode": "zip",

  "layers": [
    // Layer 0: background — single file, broadcast to all recipes
    { "path": "RP/textures/vanilla_recipe_background.png", "scale": 2 },

    // Layers 1–9: ingredient slots, 32x32px each on the 2x scaled background
    { "anchor": "top_left", "path": "{shaped_slot_0}", "offset": [12, 12], "scale": { "width": 32, "height": 32 } },
    { "anchor": "top_left", "path": "{shaped_slot_1}", "offset": [48, 12], "scale": { "width": 32, "height": 32 } },
    { "anchor": "top_left", "path": "{shaped_slot_2}", "offset": [84, 12], "scale": { "width": 32, "height": 32 } },
    { "anchor": "top_left", "path": "{shaped_slot_3}", "offset": [12, 48], "scale": { "width": 32, "height": 32 } },
    { "anchor": "top_left", "path": "{shaped_slot_4}", "offset": [48, 48], "scale": { "width": 32, "height": 32 } },
    { "anchor": "top_left", "path": "{shaped_slot_5}", "offset": [84, 48], "scale": { "width": 32, "height": 32 } },
    { "anchor": "top_left", "path": "{shaped_slot_6}", "offset": [12, 84], "scale": { "width": 32, "height": 32 } },
    { "anchor": "top_left", "path": "{shaped_slot_7}", "offset": [48, 84], "scale": { "width": 32, "height": 32 } },
    { "anchor": "top_left", "path": "{shaped_slot_8}", "offset": [84, 84], "scale": { "width": 32, "height": 32 } },

    // Layer 10: result item, to the right of the grid
    { "anchor": "top_left", "path": "{shaped_result}", "offset": [170, 48], "scale": { "width": 32, "height": 32 } }
  ]
}
```

### Using a slot template instead of offsets

Instead of an `anchor`/`offset`/`scale` per layer, point `slot_template` at a PNG the same size as the scaled base (here 220x128) with one rectangle per slot, filled with red channel values 10, 20, … 90 for slots 0–8 and 100 for the result. The layers then only need a `path`:

```jsonc
{
  "output_folder": "RP/textures/output/shaped/",
  "output_template": "{recipe_id}.png",
  "combination_mode": "zip",
  "slot_template": "RP/textures/shaped_slots.png",
  "layers": [
    { "path": "RP/textures/vanilla_recipe_background.png", "scale": 2 },
    { "path": "{shaped_slot_0}" },
    // ... shaped_slot_1 to shaped_slot_8 ...
    { "path": "{shaped_result}" }
  ]
}
```

## shapeless.json

Ingredients are laid out in the same 3x3 grid in declaration order. Ingredients with `count > 1` fill multiple consecutive slots. The layout is identical to `shaped.json` with `shapeless_slot_N` / `shapeless_result` variables.

```jsonc
{
  "output_folder": "RP/textures/output/shapeless/",
  "output_template": "{recipe_id}.png",
  "combination_mode": "zip",
  "layers": [
    { "path": "RP/textures/vanilla_recipe_background.png", "scale": 2 },
    { "anchor": "top_left", "path": "{shapeless_slot_0}", "offset": [12, 12], "scale": { "width": 32, "height": 32 } },
    // ... shapeless_slot_1 to shapeless_slot_8 at the same offsets as shaped.json ...
    { "anchor": "top_left", "path": "{shapeless_result}", "offset": [170, 48], "scale": { "width": 32, "height": 32 } }
  ]
}
```

## furnace.json

Furnace recipes have two slots: input (`furnace_slot_0`) and output (`furnace_slot_1`). A recipe can list several station tags (`furnace`, `smoker`, `campfire`, `soul_campfire`); use `tag_whitelist` to pick the recipes for this mixer's background. A `smoker.json` mixer is identical apart from `"tag_whitelist": ["smoker"]`, its own output folder and a smoker background.

```jsonc
{
  "output_folder": "RP/textures/output/furnace/",
  "output_template": "{recipe_id}.png",
  "combination_mode": "zip",

  "recipe_generation": {
    "tag_whitelist": ["furnace"],
    "id_whitelist": []
  },

  "layers": [
    // 100x100 background scaled 2x -> 200x200
    { "path": "RP/textures/vanilla_furnace_background.png", "scale": 2 },

    // Input slot (26,74)-(57,105) on the scaled background
    { "anchor": "top_left", "path": "{furnace_slot_0}", "offset": [26, 74], "scale": { "width": 32, "height": 32 } },

    // Output slot is 48x48 at (138,74); a centred 32x32 item sits at (146,82)
    { "anchor": "top_left", "path": "{furnace_slot_1}", "offset": [146, 82], "scale": { "width": 32, "height": 32 } }
  ]
}
```

Adjust the offsets to match your own background image.
