# 🗃️ Jsonify

[![Regolith Filter](https://img.shields.io/badge/Regolith-Filter-blue)](https://github.com/Bedrock-OSS/regolith)
[![Python](https://img.shields.io/badge/Python-3.7%2B-brightgreen)](https://python.org)

**A powerful Regolith filter for converting multiple file formats to JSON and enhancing your Minecraft development workflow.**

Jsonify opens more doors and ways to work with Minecraft data files by converting readable formats like YAML, JSON5, JSONC, and TOML to standard JSON, while expanding JSON syntax with helpful features.

---

## 🎯 Why Use Other Formats?

YAML, TOML, and JSON5 offer significant advantages over standard JSON:

- 📖 **Improved readability** for complex data structures
- 📝 **Support for multiline strings** and comments
- ✏️ **Easier editing and maintenance** of large files
- 🔧 **Enhanced developer experience** with better syntax

Jsonify lets you author in these human-friendly formats, then converts them to JSON for Minecraft compatibility.

--- ## ✨ Features

- 🔄 **Multi-Format Support**: Converts YAML (`.yaml`, `.yml`), JSON5 (`.json5`), JSONC (`.jsonc`), and TOML (`.toml`) files to JSON
- 📁 **Recursive Processing**: Handles entire directory trees automatically
- 🗑️ **Clean Workflow**: Optionally deletes original files after conversion
- 📅 **Smart Serialization**: Handles date and time objects as ISO strings
- 📄 **Multiline String Normalization**: Advanced `>-` feature for cleaner syntax

---

## 🧩 Multiline String Normalization (`>-` Feature)

Jsonify can normalize multiline strings in your data using two methods, controlled by the `multiline_method` filter setting:

- **first_index**:  
  If a list starts with the string `">-"`, it will be replaced by a space-joined string of the remaining list items.  

  Example (great for Molang):
  ```json
  [">-", "query.is_sprinting", "&&", "query.is_on_ground"]
  ```
  becomes
  ```json
  "query.is_sprinting && query.is_on_ground"
  ```
  This allows you to write Molang expressions across multiple lines for readability, and they will be neatly packed into a single line in the final JSON.

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

---

## ⚙️ Configuration

Configure the filter in your Regolith profile:

```json
{
  "filter": "jsonify",
  "settings": {
    "folders": ["data", "RP", "BP"],
    "multiline_method": "first_index",
    "delete_original": true
  }
}
```

### Settings Options

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `folders` | array | `["data", "RP", "BP"]` | Folders to process for conversion |
| `multiline_method` | string | `"first_index"` | Choose `"first_index"` or `"key_suffix"` |
| `delete_original` | boolean | `true` | Whether to delete original files after conversion |

---

## 🚀 Installation & Usage

### Installation
```bash
regolith install jsonify
```

### Requirements
- **Python 3.11+** (for `tomllib`) or **Python 3.7+** with `tomli`
- **ruamel.yaml**: `pip install ruamel.yaml`
- **json5**: `pip install json5`

### Install Dependencies
```bash
# Python 3.11+
pip install ruamel.yaml json5

# Python < 3.11
pip install ruamel.yaml json5 tomli
```

### Basic Usage

Add to your Regolith profile and run:
```bash
regolith run
```

The filter will automatically convert all supported files in your specified folders.

---

## 📁 Supported File Types

| Format | Extensions | Description |
|--------|------------|-------------|
| **YAML** | `.yaml`, `.yml` | Human-readable data serialization |
| **JSON5** | `.json5` | JSON with comments and trailing commas |
| **JSONC** | `.jsonc` | JSON with comments |
| **TOML** | `.toml` | Tom's Obvious Minimal Language |

---

## 🛠️ Advanced Examples

### YAML to JSON Conversion
**Input** (`config.yaml`):
```yaml
entity:
  identifier: "mymod:custom_mob"
  health: 20
  description: |
    This is a custom mob
    with multiple lines
```

**Output** (`config.json`):
```json
{
  "entity": {
    "identifier": "mymod:custom_mob",
    "health": 20,
    "description": "This is a custom mob\nwith multiple lines"
  }
}
```

### Multiline Molang Example
**Input**:
```json
{
  "condition": [">-", "query.is_sprinting", "&&", "query.is_on_ground", "&&", "!query.is_jumping"]
}
```

**Output**:
```json
{
  "condition": "query.is_sprinting && query.is_on_ground && !query.is_jumping"
}
```

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

*Made with ❤️ for Minecraft Bedrock creators*

## How It Works

- For each supported file type, the script loads the file, converts its contents to JSON, and writes the result to a new `.json` file.
- The original file is deleted.
- Multiline normalization is applied to all `.json` files according to your chosen method.

## License

MIT License