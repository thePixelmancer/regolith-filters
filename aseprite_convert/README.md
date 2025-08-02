# 🎨 Aseprite Convert

[![Regolith Filter](https://img.shields.io/badge/Regolith-Filter-blue)](https://github.com/Bedrock-OSS/regolith)
[![Python](https://img.shields.io/badge/Python-3.7%2B-brightgreen)](https://python.org)

**Seamlessly convert Aseprite files into PNG textures for Minecraft Bedrock Edition with multiple export modes.**

Transform your Aseprite artwork into Minecraft-ready textures with intelligent export modes including atlas layers, frame sequences, and configurable spritesheets. Perfect for game developers using Aseprite for texture creation.

---

## ✨ Features

- 🎯 **Multiple Export Modes**: Atlas, frame sequences, and spritesheets
- 📁 **Smart File Detection**: Automatic export mode based on filename conventions
- ⚡ **Batch Processing**: Converts entire directories of Aseprite files
- 🔧 **Configurable Output**: Customizable spritesheet orientations and settings
- 🗜️ **Automatic Trimming**: Intelligent cropping of transparent pixels
- 📊 **Layer Support**: Export individual layers as separate textures

---

## 🚀 Quick Start

### Installation
```bash
regolith install aseprite_convert
```

### Prerequisites
- **[Aseprite](https://aseprite.org/)** - Pixel art editor (required)
- **Python 3.7+**

### Basic Usage

1. **Install Aseprite** and ensure it's in your system PATH or note the installation path

2. **Configure the filter** (optional):
   ```json
   {
     "filter": "aseprite_convert",
     "settings": {
       "aseprite_exe_path": "C:/Program Files/Aseprite/aseprite.exe",
       "spritesheet_type": "vertical"
     }
   }
   ```

3. **Name your Aseprite files** according to the export modes (see below)

4. **Run Regolith**:
   ```bash
   regolith run
   ```

---

## 🎯 Export Modes

The filter automatically determines export mode based on filename patterns:

### 🗺️ Atlas Mode (`*_atlas.ase`)
**Trigger**: Filename ends with `_atlas`  
**Output**: Each layer exported as a separate cropped PNG  
**Example**: `red_maple_atlas.ase` → `red_maple_log.png`, `red_maple_leaves.png`

- ✅ Automatic trimming of transparent pixels
- ✅ Each texture named after its layer
- ✅ Perfect for block/item texture atlases

```
Input:  textures/blocks/wood_atlas.ase
Output: textures/blocks/wood_log.png
        textures/blocks/wood_planks.png
        textures/blocks/wood_bark.png
```

### 🎞️ Frame Sequence Mode (`*_frames.ase`)
**Trigger**: Filename ends with `_frames`  
**Output**: Each frame exported as a numbered PNG sequence  
**Example**: `fire_frames.ase` → `fire_0.png`, `fire_1.png`, `fire_2.png`

- ✅ Maintains frame order and timing
- ✅ Ideal for animated textures
- ✅ Compatible with Minecraft's animation system

```
Input:  textures/blocks/water_frames.ase
Output: textures/blocks/water_0.png
        textures/blocks/water_1.png
        textures/blocks/water_2.png
```

### 📋 Spritesheet Mode (default)
**Trigger**: Any other filename  
**Output**: Single spritesheet PNG with all frames  
**Configuration**: Customizable orientation

- ✅ Compact single-file output
- ✅ Multiple layout options
- ✅ Efficient for simple animations

---

## ⚙️ Configuration

Configure the filter in your Regolith profile or modify `data/config.json`:

```json
{
  "aseprite_exe_path": "C:/Program Files/Aseprite/aseprite.exe",
  "spritesheet_type": "vertical"
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `aseprite_exe_path` | string | Auto-detect | Path to Aseprite executable |
| `spritesheet_type` | string | `"vertical"` | Spritesheet layout orientation |

### Spritesheet Types

| Type | Description | Best For |
|------|-------------|----------|
| `vertical` | Frames stacked vertically | Most Minecraft textures |
| `horizontal` | Frames arranged horizontally | Wide animations |
| `rows` | Frames in a grid (rows) | Complex animations |
| `columns` | Frames in a grid (columns) | Square animations |
| `packed` | Optimally packed layout | Memory efficiency |

---

## 📁 File Structure

```
aseprite_convert/
├── aseprite_convert.py          # Main filter script
├── filter.json                  # Regolith filter definition
├── README.md                    # This file
├── data/
│   └── config.json              # Filter configuration
└── test/
    ├── config.json              # Test configuration
    └── packs/                   # Test assets
```

---

## 📝 Examples

### Atlas Conversion Example
**Input Structure**:
```
RP/textures/blocks/
└── custom_wood_atlas.ase       # Contains layers: "log", "planks", "leaves"
```

**Output**:
```
RP/textures/blocks/
├── custom_wood_log.png         # Cropped log texture
├── custom_wood_planks.png      # Cropped planks texture
└── custom_wood_leaves.png      # Cropped leaves texture
```

### Frame Sequence Example
**Input Structure**:
```
RP/textures/blocks/
└── lava_flow_frames.ase        # 4-frame animation
```

**Output**:
```
RP/textures/blocks/
├── lava_flow_0.png             # Frame 1
├── lava_flow_1.png             # Frame 2
├── lava_flow_2.png             # Frame 3
└── lava_flow_3.png             # Frame 4
```

---

## 🛠️ Troubleshooting

### Common Issues

**Aseprite not found**:
- Ensure Aseprite is installed and in your system PATH
- Or specify the full path in `aseprite_exe_path` configuration

**No files converted**:
- Check that your `.ase` or `.aseprite` files are in the RP folder
- Verify filename patterns match the export modes
- Ensure files are valid Aseprite documents

**Output quality issues**:
- Check your Aseprite color mode (RGB recommended)
- Verify layer names for atlas mode
- Ensure proper canvas size for your textures

---

## 🆕 Changelog

### Version 1.1.2
- ✨ Atlas conversion now outputs PNGs named only after the layer (not document name)
- 🐛 Fixed naming conflicts in atlas mode
- 📦 Improved file organization

---

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with various Aseprite files
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

*Made with ❤️ for Minecraft Bedrock creators*
