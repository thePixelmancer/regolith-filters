# Pixelmancer's Regolith Filters

A curated collection of custom Regolith filters for Minecraft Bedrock Edition development. These filters help automate common tasks, streamline workflows, and enhance your Bedrock Edition project development experience.

# Pixelmancer's Regolith Filters

A curated collection of **custom Regolith filters** for Minecraft Bedrock Edition development. These filters help automate common tasks, streamline workflows, and enhance your Bedrock Edition project development experience.

## 📦 Available Filters

|                 | Link                                    | Short Description                                                                     |
| ------------------- | --------------------------------------- | ------------------------------------------------------------------------------------- |
| 🎨 | [Aseprite Convert](./aseprite_convert/) | Convert Aseprite files into PNGs in multiple modes, including spritesheets and atlas. |
| 🥚 | [Auto Spawn Egg](./auto_spawn_egg/)     | Auto-generate spawn egg colors for custom entities based on dominant texture colors.  |
| 📦 | [Fetcher](./fetcher/)                   | Download files or folders from GitHub into your Minecraft project.                    |
| 🖼️ | [Image Mixer](./image_mixer/)           | Batch-generate composite images from layered PNGs with advanced positioning/scaling.  |
| 🌐 | [MCLocalize](./mclocalize/)             | Manage localization files for multiple languages in Bedrock Edition.                  |
| 🔄 | [Replacements](./replacements/)         | Perform project-wide intelligent string replacements for identifiers and namespaces.  |
| 🗃️ | [Jsonify](./jsonify/)                   | Convert YAML, JSON5, JSONC, and TOML files to JSON recursively.                       |
| <img src="./multifeature/images/icon.png" width="100" height="100"> | [MultiFeature](./multifeature/)         | Combine multiple feature definitions in one file and split into .json during build.   |

---

_Detailed filter usage, installation, and requirements are provided below._

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
regolith install jsonify
regolith install multifeature
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
