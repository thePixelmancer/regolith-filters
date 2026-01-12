# 🔄 Replacements

[![Regolith Filter](https://img.shields.io/badge/Regolith-Filter-blue)](https://github.com/Bedrock-OSS/regolith)
[![Python](https://img.shields.io/badge/Python-3.7%2B-brightgreen)](https://python.org)

**Powerful string replacement filter for automating namespace and identifier management in Bedrock Edition packs.**

Automate the process of replacing placeholder strings (such as `@namespace`, `@team`, `@proj`) with your desired values across multiple files in your project. Perfect for adapting templates and managing project-wide identifiers.

---

## 🎯 Why Use This Filter?

This filter is especially useful for **namespacing and project management**:

- 🏷️ **Centralized Identifiers**: Define preset values in one place and apply them project-wide
- 🔄 **Template Adaptation**: Quickly update all relevant identifiers when copying from other projects
- 🧩 **Modular Workflow**: Works seamlessly with other Regolith filters for streamlined development
- ⚡ **Batch Processing**: Replace thousands of strings across hundreds of files instantly

---

## ✨ Features

- 🎯 **Smart String Replacement**: Replace placeholders like `@namespace`, `@team`, `@proj` across all files
- 📁 **Project-Wide Processing**: Handles entire behavior and resource pack directories
- ⚙️ **Flexible Configuration**: Define custom replacement patterns and values
- 🔧 **Template-Friendly**: Perfect for project templates and boilerplates
- 🧩 **Filter Integration**: Designed to work with other Regolith filters

---

## 🚀 Quick Start

### Installation
```bash
regolith install replacements
```

### Basic Usage

Add the filter to your Regolith profile in your `config.json`:

```json
{
  "regolith": {
    "profiles": {
      "default": {
        "filters": [
          {
            "filter": "replacements",
            "settings": {
              "replace": {
                "@namespace": "namespace",
                "@team": "teamname",
                "@proj": "project"
              }
            }
          }
        ]
      }
    }
  }
}
```

## Settings

The filter accepts the following settings:

- **replace**:  
  A dictionary mapping strings to their replacements.  
  Example:
  ```json
  {
    "@namespace": "namespace",
    "@team": "teamname",
    "@proj": "project"
  }
  ```

- **replace_nbt** (optional):  
  If set to `true`, the filter will also process `.mcstructure` files (NBT binary format) and replace strings in their string tags.  
  Default: `false`

- **replace_folders** (optional):  
  If set to `true`, the filter will also rename folders whose names contain any of the target strings, applying the same replacement rules as for file contents.  
  Default: `false`

- **extension_whitelist** (optional):  
  A list of file extensions to process.  
  Default:  
  ```json
  []
  ```

- **paths** (optional):  
  A list of directories to search for files and folders to process.  
  Default:  
  ```json
  ["RP", "BP"]
  ```

## How it works

The filter scans all files in the specified `paths` with the given `extensions` and replaces every occurrence of the keys in `replace` with their corresponding values.  

If `replace_nbt` is enabled, it will also process `.mcstructure` files (Minecraft structure files in NBT binary format). The filter recursively traverses all NBT tags and replaces strings found in TAG_String values. **Note:** NBT replacements work by walking through the NBT object structure rather than performing string-based replacements. This is set as a toggle to save processing time when NBT file processing is not needed.

If `replace_folders` is enabled, it will also rename folders whose names match any of the target strings, applying the same replacement rules.

### NBT Files (.mcstructure)

**Important:** `pynbt` library must be installed for NBT support:
```bash
pip install pynbt
```

When `"replace_nbt": true` is set, the filter will:
1. Read `.mcstructure` files as NBT (binary format)
2. Recursively search all string values in the NBT structure
3. Apply replacements to matched strings
4. Save the modified NBT back to the `.mcstructure` file

This is useful for replacing namespaces, team names, or project identifiers embedded in structure files.

Example configuration:
```json
{
  "filter": "replacements",
  "settings": {
    "replace": {
      "@namespace": "myproject",
      "@owner": "developer"
    },
    "replace_nbt": true,
    "paths": ["RP", "BP"]
  }
}
```

## Example

Given a file with the following content:

```json
{
  "test1": "@namespace@namespace",
  "test2": "@team@namespace",
  "test3": "@proj"
}
```

With the above settings, after running the filter, it will become:

```json
{
  "test1": "namespacenamespace",
  "test2": "teamnamenamespace",
  "test3": "project"
}
```