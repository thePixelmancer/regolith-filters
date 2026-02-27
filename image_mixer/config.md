# config.json reference

Full annotated example covering shaped, shapeless, and furnace recipe image generation.

```jsonc
{
  // Enables JSON Schema validation and autocomplete in supporting editors
  "$schema": "https://raw.githubusercontent.com/thePixelmancer/regolith-filters/refs/heads/main/image_mixer/data/config.schema.json",

  "image_mixers": [

    // -------------------------------------------------------------------------
    // SHAPED RECIPES
    // Generates one image per shaped recipe.
    // The 3x3 grid of ingredient slots maps to shaped_slot_0 through shaped_slot_8:
    //
    //   slot_0 | slot_1 | slot_2
    //   slot_3 | slot_4 | slot_5
    //   slot_6 | slot_7 | slot_8
    //
    // Sub-3x3 patterns are automatically centred in the grid.
    // -------------------------------------------------------------------------
    {
      "output_folder": "RP/textures/output/shaped/",

      // {index}  = combination index
      // {layer1} = filename stem of the first ingredient (slot_0); useful as a unique name
      "output_template": "{index}_{layer1}_icon.png",

      // zip: one output image per recipe, pairing each slot variable with
      // the same recipe index across all layers
      "combination_mode": "zip",

      "layers": [
        // Layer 0: background — single file, broadcast to all recipes
        {
          "path": "RP/textures/vanilla_recipe_background.png",
          "blend_mode": "normal",
          "scale": 2
        },

        // Layers 1–9: ingredient slots, top-left origin, 32x32px each
        // Offsets position each slot within the 3x3 grid area of the background
        { "anchor": "top_left", "path": "{shaped_slot_0}", "offset": [12, 12],  "scale": { "width": 32, "height": 32 } },
        { "anchor": "top_left", "path": "{shaped_slot_1}", "offset": [48, 12],  "scale": { "width": 32, "height": 32 } },
        { "anchor": "top_left", "path": "{shaped_slot_2}", "offset": [84, 12],  "scale": { "width": 32, "height": 32 } },
        { "anchor": "top_left", "path": "{shaped_slot_3}", "offset": [12, 48],  "scale": { "width": 32, "height": 32 } },
        { "anchor": "top_left", "path": "{shaped_slot_4}", "offset": [48, 48],  "scale": { "width": 32, "height": 32 } },
        { "anchor": "top_left", "path": "{shaped_slot_5}", "offset": [84, 48],  "scale": { "width": 32, "height": 32 } },
        { "anchor": "top_left", "path": "{shaped_slot_6}", "offset": [12, 84],  "scale": { "width": 32, "height": 32 } },
        { "anchor": "top_left", "path": "{shaped_slot_7}", "offset": [48, 84],  "scale": { "width": 32, "height": 32 } },
        { "anchor": "top_left", "path": "{shaped_slot_8}", "offset": [84, 84],  "scale": { "width": 32, "height": 32 } },

        // Layer 10: result item, positioned to the right of the grid
        { "anchor": "top_left", "path": "{shaped_result}", "offset": [170, 48], "scale": { "width": 32, "height": 32 } }
      ]
    },

    // -------------------------------------------------------------------------
    // SHAPELESS RECIPES
    // Generates one image per shapeless recipe.
    // Ingredients are laid out in the same 3x3 grid in declaration order.
    // Ingredients with count > 1 fill multiple consecutive slots.
    // -------------------------------------------------------------------------
    {
      "output_folder": "RP/textures/output/shapeless/",
      "output_template": "{index}_{layer1}_icon.png",
      "combination_mode": "zip",

      "layers": [
        {
          "path": "RP/textures/vanilla_recipe_background.png",
          "blend_mode": "normal",
          "scale": 2
        },

        { "anchor": "top_left", "path": "{shapeless_slot_0}", "offset": [12, 12],  "scale": { "width": 32, "height": 32 } },
        { "anchor": "top_left", "path": "{shapeless_slot_1}", "offset": [48, 12],  "scale": { "width": 32, "height": 32 } },
        { "anchor": "top_left", "path": "{shapeless_slot_2}", "offset": [84, 12],  "scale": { "width": 32, "height": 32 } },
        { "anchor": "top_left", "path": "{shapeless_slot_3}", "offset": [12, 48],  "scale": { "width": 32, "height": 32 } },
        { "anchor": "top_left", "path": "{shapeless_slot_4}", "offset": [48, 48],  "scale": { "width": 32, "height": 32 } },
        { "anchor": "top_left", "path": "{shapeless_slot_5}", "offset": [84, 48],  "scale": { "width": 32, "height": 32 } },
        { "anchor": "top_left", "path": "{shapeless_slot_6}", "offset": [12, 84],  "scale": { "width": 32, "height": 32 } },
        { "anchor": "top_left", "path": "{shapeless_slot_7}", "offset": [48, 84],  "scale": { "width": 32, "height": 32 } },
        { "anchor": "top_left", "path": "{shapeless_slot_8}", "offset": [84, 84],  "scale": { "width": 32, "height": 32 } },

        { "anchor": "top_left", "path": "{shapeless_result}", "offset": [170, 48], "scale": { "width": 32, "height": 32 } }
      ]
    },

    // -------------------------------------------------------------------------
    // FURNACE RECIPES
    // Generates one image per furnace recipe (covers all furnace tag variants).
    // Only two slots: input (slot_0) and output (slot_1).
    // Uses a separate furnace-style background image.
    // Adjust the slot offsets to match your specific background dimensions.
    // -------------------------------------------------------------------------
    {
      "output_folder": "RP/textures/output/furnace/",
      "output_template": "{index}_{layer1}_icon.png",
      "combination_mode": "zip",

      "layers": [
        {
          "path": "RP/textures/vanilla_furnace_background.png",
          "blend_mode": "normal",
          "scale": 2
        },

        // Input item: left side of the furnace UI
        { "anchor": "top_left", "path": "{furnace_slot_0}", "offset": [12,  48], "scale": { "width": 32, "height": 32 } },

        // Output item: right side of the furnace UI
        // Adjust this offset to match your background's arrow and slot positions
        { "anchor": "top_left", "path": "{furnace_slot_1}", "offset": [120, 48], "scale": { "width": 32, "height": 32 } }
      ]
    }

  ]
}
```
