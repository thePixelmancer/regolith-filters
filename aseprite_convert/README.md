# Aseprite Convert Configuration

The script accepts configuration via command line JSON or uses sensible defaults. You can also modify the default configuration in the script itself.

## Changelog

### 1.1.2

- Atlas conversion now outputs PNGs named **only after the layer**, not after the aseprite document name.

Exporting filename.extension`.
  Default configuration:

```json
{
  "aseprite_exe_path": "C:/Program Files/Aseprite/aseprite.exe",
  "spritesheet_type": "vertical"
}
```

Available spritesheet types: `horizontal`, `vertical`, `rows`, `columns`, `packed`script converts Aseprite files (`.ase` or `.aseprite`) from your RP folder into PNG files with different export modes based on file naming conventions. The script supports atlas layers, frame sequences, and spritesheets.

INPUT

![1](https://github.com/user-attachments/assets/0c424ffe-87b5-4ab6-89bb-eadea8423e62)

OUTPUT

![2](https://github.com/user-attachments/assets/994d01fe-58b3-4cf9-a4cf-1947e4747d3d)

## Prerequisites

To use this script, you need to have [Aseprite](https://aseprite.org/) installed on your system. The script will automatically detect Aseprite if it's in your system PATH, or you can specify the path in the configuration.

## Configuration

The configuration for the script can be modified in the `config.json` file located in the `data` folder. You can change the spritesheet orientation by updating the `spritesheet_type` value.

Here’s a sample structure of the `config.json`:

```jsonc
{
  "aseprite_exe_path": "C:/Program Files/Aseprite/aseprite.exe",
  "spritesheet_type": "vertical" // horizontal, vertical, rows, columns, packed
}
```

## Export Modes

The script determines the export mode based on the filename:

### Atlas Mode (`filename_atlas.ase`)

- **Trigger**: Filename ends with `_atlas`
- **Output**: Each layer exported as a separate cropped PNG
- **Example**: `red_maple_atlas.ase` → `red_maple_log.png`, `red_maple_leaves.png`, etc.
- **Features**: Automatic trimming of transparent pixels
- **Important**: Atlas conversion works by **layers**, not image coordinates. Each texture must be on its own separate layer in the Aseprite file. The script will export and trim each layer individually. This allows users to specify the exact name of each texture by naming the layers appropriately.

### Frames Mode (`filename_frames.ase`)

- **Trigger**: Filename ends with `_frames`
- **Output**: Each frame exported as a separate numbered PNG
- **Example**: `character_walk_frames.ase` → `character_walk_0.png`, `character_walk_1.png`, etc.

### Spritesheet Mode (default)

- **Trigger**: Any other filename
- **Output**: Single PNG spritesheet (vertical by default)
- **Example**: `animation.ase` → `animation.png`
- **Features**: Configurable orientation via `spritesheet_type`

## Usage

1. Install the filter in your Regolith project
2. Place Aseprite files in your RP folder using the naming conventions above
3. Run the filter
4. Original `.ase` files are automatically deleted after successful conversion

## Features

- **Automatic Aseprite Detection**: Finds Aseprite in PATH or uses configured path
- **Smart File Processing**: Only processes `.ase` and `.aseprite` files
- **Progress Feedback**: Clear console output with conversion type indicators
- **Error Handling**: Comprehensive error reporting for failed conversions
- **Modular Design**: Separate functions for each conversion type

## Output Messages

The script provides clear feedback during processing:

```
[Atlas] Exporting red_maple_atlas.ase
[Frames] Exporting character_walk_frames.ase
[Spritesheet] Exporting background.ase
```

## Acknowledgments

- [Aseprite](https://aseprite.org/) for the amazing software.
