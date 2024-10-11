# Aseprite File Converter

This script converts Aseprite files (`.ase` or `.aseprite`) from your RP folder - into PNG files. If the Aseprite file is animated, it will be exported as a vertical spritesheet. If the file has `_frames` in its name, a folder will be created containing separate numbered PNG files.

## Prerequisites

To use this script, you need to have [Aseprite](https://aseprite.org/) installed on your system. Make sure the path to the Aseprite executable is correctly set in the `config.json` file or added to your system's PATH as `aseprite.exe`.

## Configuration

The configuration for the script can be modified in the `config.json` file located in the `data` folder. You can change the spritesheet orientation by updating the `spritesheet_type` value. 

Here’s a sample structure of the `config.json`:

```json
{
    "aseprite_exe_path": "C:/Program Files/Aseprite/aseprite.exe",
    "spritesheet_type": "vertical"  // horizontal, vertical, rows, columns, packed
}
```

## File Output

- **Regular Aseprite Files**: If the Aseprite file is animated, it will be exported as a PNG spritesheet. The script will create a vertical spritesheet by default. You can change the orientation in the `config.json`.

- **Files with `_frames` in the Name**: If the Aseprite file has `_frames` in its name, a folder will be created with the same name but without `_frames`. Inside this folder, each frame will be exported as separate numbered PNG file.

## Usage

1. Install the filter
2. Place aseprite files in your RP folder
3. ???
4. Profit

## Example


## License

You can freely use the project

## Acknowledgments

- [Aseprite](https://aseprite.org/) for the amazing software.