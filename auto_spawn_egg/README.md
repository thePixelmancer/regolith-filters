# Auto Spawn Egg Filter

## Description

The Auto Spawn Egg filter automatically creates texture-based spawn egg colors in entity files if "spawn_egg" isnt specified.
The filter uses a Python script (`auto_spawn_egg.py`) to generate the colors. It uses the `colorthief` library to determine the two most dominant colors.
Contributions are welcome!

## Usage

Simply forget to add "spawn_egg": {...} in the entity file and ensure you have at least one texture defined. If no "default" texture is defined, the filter will use one of the other textures for generating colors.

## Requirements

Use the json cleaner filter before applying this filter.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.