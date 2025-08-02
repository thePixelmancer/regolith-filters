# 🥚 Auto Spawn Egg

[![Regolith Filter](https://img.shields.io/badge/Regolith-Filter-blue)](https://github.com/Bedrock-OSS/regolith)
[![Python](https://img.shields.io/badge/Python-3.7%2B-brightgreen)](https://python.org)

**Automatically generate spawn egg colors for custom entities based on their dominant texture colors.**

This filter analyzes your custom entity textures and intelligently generates spawn egg color definitions, eliminating the tedious manual process of color picking and ensuring your spawn eggs match your entity's visual design.

---

## ✨ Features

- 🎨 **Intelligent Color Analysis**: Uses advanced color extraction to find dominant colors from entity textures
- 🔍 **Smart Texture Detection**: Automatically finds and analyzes entity textures from various sources
- ⚡ **Zero Configuration**: Works out of the box - just run and forget
- 🎯 **Precision Targeting**: Only processes entities that are missing spawn egg definitions
- 🔄 **Flexible Texture Sources**: Uses "default" texture when available, falls back to any defined texture

---

## 🚀 Quick Start

### Installation
```bash
regolith install auto_spawn_egg
```

### Requirements
- **Python 3.7+**
- **ColorThief**: `pip install colorthief`

### Basic Usage

1. **Install dependencies**:
   ```bash
   pip install colorthief
   ```

2. **Add to your Regolith profile**:
   ```json
   {
     "filter": "auto_spawn_egg"
   }
   ```

3. **Run Regolith**:
   ```bash
   regolith run
   ```

The filter will automatically detect entities missing spawn egg definitions and generate them based on texture analysis.

---

## 🎯 How It Works

1. **Entity Scanning**: Analyzes all entity files in your behavior pack
2. **Missing Detection**: Identifies entities without `"spawn_egg"` definitions
3. **Texture Analysis**: Extracts the two most dominant colors from entity textures
4. **Color Generation**: Creates spawn egg color definitions using the dominant colors
5. **File Updates**: Automatically adds the spawn egg definitions to your entity files

### Texture Priority
The filter uses this priority order for texture selection:
1. **"default" texture** (if defined)
2. **First available texture** from the entity's texture list
3. **Fallback handling** for entities without textures

---

## 📁 File Structure

```
auto_spawn_egg/
├── auto_spawn_egg.py            # Main filter script
├── filter.json                  # Regolith filter definition
├── README.md                    # This file
└── requirements.txt             # Python dependencies
```

---

## 📝 Example

### Before (Entity without spawn egg)
```json
{
  "format_version": "1.16.0",
  "minecraft:entity": {
    "description": {
      "identifier": "mymod:custom_zombie",
      "spawn_category": "monster"
    },
    "component_groups": {},
    "components": {
      "minecraft:type_family": {
        "family": ["zombie", "undead", "monster"]
      }
    }
  }
}
```

### After (With auto-generated spawn egg)
```json
{
  "format_version": "1.16.0",
  "minecraft:entity": {
    "description": {
      "identifier": "mymod:custom_zombie",
      "spawn_category": "monster",
      "spawn_egg": {
        "base_color": "#4a7c59",
        "overlay_color": "#2d4a37"
      }
    },
    "component_groups": {},
    "components": {
      "minecraft:type_family": {
        "family": ["zombie", "undead", "monster"]
      }
    }
  }
}
```

---

## ⚙️ Configuration

The filter works with minimal configuration. Simply add it to your Regolith profile:

```json
{
  "regolith": {
    "profiles": {
      "default": {
        "filters": [
          {
            "filter": "json_cleaner"
          },
          {
            "filter": "auto_spawn_egg"
          }
        ]
      }
    }
  }
}
```

> 💡 **Tip**: Use the `json_cleaner` filter before `auto_spawn_egg` for best results.

---

## 🛠️ Troubleshooting

### Common Issues

**No spawn eggs generated**: 
- Ensure your entities have texture definitions
- Check that texture files exist in your resource pack
- Verify entities don't already have spawn egg definitions

**Color extraction errors**:
- Confirm ColorThief is installed: `pip install colorthief`
- Ensure texture files are valid PNG/JPG images
- Check file paths and permissions

**Filter not running**:
- Verify the filter is added to your Regolith profile
- Ensure all dependencies are installed
- Check Regolith logs for error messages

---

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with various entity types
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

*Made with ❤️ for Minecraft Bedrock creators*