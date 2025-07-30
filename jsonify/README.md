# Jsonify

Jsonify is a regolith filter aimed at opening more doors and ways to work with Minecraft data files. First and foremost, it can convert readable filetypes like YAML, JSON5, JSONC, and TOML to standard JSON. Secondly, it expands the syntax of standard JSON with extra features that will be added as the filter is developed, making authoring and maintaining Minecraft data files easier and more flexible.

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
- **Supports multiline string normalization using the `>-` feature.**

## Multiline String Normalization (`>-` Feature)

Jsonify can normalize multiline strings in your data using two methods, controlled by the `multiline_method` filter setting:

- **first_index**:  
  If a list starts with the string `">-"`, it will be replaced by a space-joined string of the remaining list items.  
  Example:
  ```json
  [">-", "line 1", "line 2"]
  ```
  becomes
  ```json
  "line 1 line 2"
  ```

- **key_suffix**:  
  If a dictionary key ends with `">-"` and its value is a list, the key is renamed (removing `">-"`) and the value is replaced by a space-joined string of the list items.  
  Example:
  ```json
  { "description>-": ["line 1", "line 2"] }
  ```
  becomes
  ```json
  { "description": "line 1 line 2" }
  ```

Set your preferred method in the filter settings.

## Filter Settings

You can configure the filter in your Regolith profile:

```jsonc
{
  "filter": "jsonify",
  "settings": {
    "folders": ["data", "RP", "BP"],
    "multiline_method": "first_index" // or "key_suffix"
  }
}
```

- `folders`: List of folders to process.
- `multiline_method`: Choose `"first_index"` or `"key_suffix"` for multiline normalization.

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
- Multiline normalization is applied to all `.json` files according to your chosen method.

## License

MIT License