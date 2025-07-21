# Regolith Filters Collection

A curated collection of custom Regolith filters for Minecraft Bedrock Edition development. These filters help automate common tasks, streamline workflows, and enhance your Bedrock Edition project development experience.

## 🛠️ Available Filters

### 🎨 [Aseprite Convert](./aseprite_convert/)
Converts Aseprite files (`.ase` or `.aseprite`) from your Resource Pack into PNG files with multiple export modes.

**Features:**
- **Atlas Mode**: Export layers as separate cropped PNGs
- **Frame Sequences**: Export animation frames as numbered sequences  
- **Spritesheets**: Generate sprite sheets in various orientations
- Automatic trimming and optimization
- Configurable export settings

**Use Case:** Perfect for game developers using Aseprite for texture creation who need automated conversion to Minecraft-compatible formats.

### 🥚 [Auto Spawn Egg](./auto_spawn_egg/)
Automatically generates spawn egg colors for custom entities based on their textures.

**Features:**
- Analyzes entity textures to determine dominant colors
- Automatically creates spawn egg definitions when missing
- Uses ColorThief library for intelligent color extraction
- Seamless integration with existing entity files

**Use Case:** Eliminates manual color picking for spawn eggs when creating custom mobs.

### 📦 [Fetcher](./fetcher/)
Downloads files and folders from GitHub repositories directly into your Minecraft project.

**Features:**
- Fetch from public and private repositories
- Flexible target directory configuration
- Caching system for efficient downloads
- Support for specific commits and branches
- Clean workspace management (removes `_fetch.json` after processing)

**Use Case:** Import external libraries, scripts, or assets from GitHub repositories into your project automatically.

### 🖼️ [Image Mixer](./image_mixer/)
Batch-generates composite images from layered PNGs with advanced positioning and scaling options.

**Features:**
- Multi-threaded batch processing for speed
- Flexible anchor positioning system
- Advanced scaling with multiple resampling methods
- Customizable output filename templates
- Support for backgrounds, frames, overlays, and icons

**Use Case:** Generate recipe images, UI elements, texture variants, or any composite imagery for your resource packs.

### 🌐 [MCLocalize](./mclocalize/)
Manages localization files for Minecraft Bedrock Edition.

**Supported Languages:**
- English (en_US)
- German (de)
- Spanish (es)  
- French (fr)
- Italian (it)
- Portuguese (pt)
- Serbian (sr)

**Use Case:** Streamline the localization process for international Minecraft projects.

### 🔄 [Replacements](./replacements/)
Performs intelligent string replacements across your entire project.

**Features:**
- Namespace and identifier management
- Placeholder replacement system (e.g., `@namespace`, `@team`, `@proj`)
- Bulk file processing
- Perfect for project template conversion

**Use Case:** Quickly adapt copied files to your project's naming conventions and namespaces.

## 🚀 Quick Start

### Installation
Each filter can be installed individually using Regolith:

```bash
# Install specific filters by folder name
regolith install aseprite_convert
regolith install auto_spawn_egg
regolith install fetcher
regolith install image_mixer
regolith install mclocalize
regolith install replacements

# Or clone the entire repository
git clone https://github.com/thePixelmancer/regolith-filters.git
```

### Usage
Add filters to your Regolith profile in `config.json`:

```json
{
  "regolith": {
    "profiles": {
      "default": {
        "filters": [
          {
            "filter": "filter-name",
            "settings": {
              // Filter-specific configuration
            }
          }
        ]
      }
    }
  }
}
```

## 📋 Requirements

### General Requirements
- [Regolith](https://regolith-mc.github.io/) - Bedrock Edition development framework
- Python 3.7+ (for Python-based filters)

### Filter-Specific Requirements
- **Aseprite Convert**: [Aseprite](https://aseprite.org/) software
- **Auto Spawn Egg**: `colorthief` Python library
- **Image Mixer**: `Pillow` (PIL) Python library
- **Fetcher**: `requests` Python library

Install Python dependencies:
```bash
pip install colorthief pillow requests
```

## 🤝 Contributing

Contributions are welcome! Whether you want to:
- 🐛 Report bugs
- 💡 Suggest new features  
- 🔧 Submit pull requests
- 📚 Improve documentation

Please feel free to open an issue or submit a pull request.

### Development Guidelines
1. Each filter should be self-contained in its own directory
2. Include comprehensive README documentation
3. Provide example configurations and test cases
4. Follow Python best practices for code quality
5. Test thoroughly with various Minecraft project setups

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Thanks to the [Regolith](https://regolith-mc.github.io/) team for creating an amazing development framework
- The Minecraft Bedrock Edition community for inspiration and feedback
- Contributors who help improve and maintain these filters

## 📞 Support

If you encounter issues or need help:
1. Check the individual filter README files for specific documentation
2. Search existing [GitHub issues](https://github.com/thePixelmancer/regolith-filters/issues)
3. Create a new issue with detailed information about your problem

---

⭐ **Star this repository if you find these filters helpful!** ⭐
