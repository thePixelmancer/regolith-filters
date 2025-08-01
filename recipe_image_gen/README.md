# 🍳 Recipe Image Generator

[![Regolith Filter](https://img.shields.io/badge/Regolith-Filter-blue)](https://regolith-mc.github.io/)
[![Python](https://img.shields.io/badge/Python-3.7%2B-brightgreen)](https://python.org)

**Automatically generate recipe images from your Minecraft Bedrock Edition crafting recipe definitions.**

This filter creates visual recipe guides by processing your recipe JSON files and generating composite images showing the crafting grid layout with the appropriate item textures.

---

## ✨ Features

- **Automatic Recipe Processing**: Scans your behavior pack for recipe files
- **Smart Texture Resolution**: Maps items to textures using vanilla mappings and custom paths
- **Configurable Output**: Customize where recipe images are saved
- **Multiple Recipe Types**: Supports shaped and shapeless crafting recipes
- **High Quality Images**: Generates crisp PNG images for your resource pack

---

## 🚀 Quick Start

### Installation
```bash
regolith install recipe_image_gen
```

### Requirements
- **Python 3.7+**
- **Pillow (PIL)**: `pip install pillow`
- **Reticulator**: `pip install reticulator`

### Basic Usage

1. **Add to your Regolith profile**:
   ```json
   {
     "filter": "recipe_image_gen",
     "settings": {}
   }
   ```

2. **Configure the filter** (optional):
   ```json
   {
     "filter": "recipe_image_gen",
     "settings": {
       "output_folder": "RP/textures/recipe_images"
     }
   }
   ```

3. **Run Regolith**:
   ```bash
   regolith run
   ```

---

## ⚙️ Configuration

The filter uses `data/recipe_image_gen/config.json` for configuration:

```json
{
  "recipe_image_generators": [
    {
      "output_folder": "RP/textures/recipe_images",
      "grid_size": 96,
      "item_size": 32
    }
  ]
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `output_folder` | string | `"RP/textures/recipe_images"` | Where to save generated images |
| `grid_size` | number | `96` | Size of the crafting grid in pixels |
| `item_size` | number | `32` | Size of individual item icons |

---

## 📁 File Structure

```
recipe_image_gen/
├── recipe_image_gen.py          # Main filter script
├── filter.json                  # Regolith filter definition
├── README.md                    # This file
├── data/
│   └── recipe_image_gen/
│       ├── config.json          # Filter configuration
│       └── vanilla_texture_mappings.json  # Vanilla item texture mappings
└── test/
    ├── test.py                  # Test script
    └── config.json              # Test configuration
```

---

## 🎯 How It Works

1. **Recipe Discovery**: Scans your behavior pack for `*.recipe.json` files
2. **Texture Mapping**: Maps recipe ingredients to texture paths using:
   - Vanilla texture mappings (built-in)
   - Custom namespace texture paths
   - Fallback texture resolution
3. **Image Generation**: Creates composite images showing:
   - 3x3 crafting grid layout
   - Ingredient textures in correct positions
   - Result item texture
4. **Output**: Saves images to your resource pack's texture folder

---

## 🛠️ Troubleshooting

### Common Issues

**Missing Textures**: If some items appear missing in generated images:
- Ensure texture files exist in your resource pack
- Check that item names match your texture file names
- Verify custom namespace mappings

**Generation Errors**: If the filter fails to run:
- Confirm all dependencies are installed: `pip install pillow reticulator`
- Check that recipe files are valid JSON
- Ensure output directory is writable

---

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

## 🙏 Acknowledgments

- Thanks to the [Regolith](https://regolith-mc.github.io/) team for the amazing development framework
- The Minecraft Bedrock Edition community for inspiration and feedback

---

*Made with ❤️ for Minecraft Bedrock creators*
