# Jsonify

Jsonify is a regolith filter for batch-converting YAML, JSON5, JSONC, and TOML files to standard JSON format. It recursively scans a directory, detects supported file types, and outputs `.json` files, optionally deleting the originals.

## Why Use Other Formats?

YAML, TOML, and JSON5 offer advantages over standard JSON, such as:
- Improved readability for complex data
- Support for multiline strings
- Easier editing and maintenance

Jsonify lets you use these formats for authoring, then convert them to JSON for compatibility.

## Features

- Converts YAML (`.yaml`, `.yml`), JSON5 (`.json5`), JSONC (`.jsonc`), and TOML (`.toml`) files to JSON.
- Recursively processes all files in a directory tree.
- Optionally deletes the original files after conversion.
- Handles date and time objects, serializing them as ISO strings.

## Installation

Run the filter from the command line:

```bash
regolith install jsonify
```

By default, it will process the current directory and delete the original files after conversion.

## Requirements

- Python 3.11+ (for `tomllib`). For older Python versions, install `tomli` and change the import to `import tomli as tomllib`.
- `ruamel.yaml` for YAML support
- `json5` for JSON5/JSONC support

Install dependencies:

```bash
pip install ruamel.yaml json5 tomli  # Only tomli if Python < 3.11
```

## How It Works

- For each supported file type, the script loads the file, converts its contents to JSON, and writes the result to a new `.json` file.
- The original file is deleted.

## License

MIT License
