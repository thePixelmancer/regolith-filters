# 📦 Fetcher

[![Regolith Filter](https://img.shields.io/badge/Regolith-Filter-blue)](https://regolith-mc.github.io/)
[![Python](https://img.shields.io/badge/Python-3.7%2B-brightgreen)](https://python.org)

**Automatically fetch files and folders from GitHub repositories directly into your Minecraft Bedrock Edition project.**

This filter streamlines the process of importing external resources, scripts, or packs with flexible configuration for advanced workflows, caching, and clean workspace management.

---

## ✨ Features

- 📁 **GitHub Integration**: Fetch files/folders from any public or private GitHub repository
- 🎯 **Flexible Targeting**: Configurable output paths and folder structures
- 🔄 **Smart Caching**: Efficient caching by commit hash for reproducibility
- 🧹 **Clean Workspace**: Automatically removes fetch configuration files after processing
- 🔐 **Private Repo Support**: Token-based authentication for private repositories
- ⚡ **Batch Processing**: Handle multiple fetch operations in a single run

---

## 🚀 Quick Start

### Installation
```bash
regolith install fetcher
```

### Requirements
- **Python 3.7+**
- **Requests**: `pip install requests`

### Basic Usage

1. **Create a `_fetch.json`** file in your project directory
2. **Configure your fetch operations** (see examples below)
3. **Run Regolith**:
   ```bash
   regolith run
   ```

---

## 🎯 How It Works
1. Place a `_fetch.json` file in any subdirectory of your project (e.g., inside a data or pack folder).
2. The filter reads each `_fetch.json`, downloads the specified files/folders from GitHub, and copies them to the desired location.
3. The filter removes the `_fetch.json` after processing, ensuring a clean workspace.
4. Downloads are cached by commit hash for efficiency and reproducibility.
5. The GitHub token is read from `data/fetcher/config.json` (see below). If not present, public repositories can still be fetched, but private repositories will be skipped with a warning.

## Target and Folder Handling
- If `target` is omitted or empty, the filter will create a folder named after the last segment of the GitHub path (e.g., the folder or file name) in the same directory as the `_fetch.json`.
- If `target` is specified, the filter will copy all fetched files/folders directly into the given relative path (relative to the `_fetch.json` location), with no extra top-level folder.

### Examples
#### 1. Fetch a Folder, Default Output
```json
[
  {
    "source": "https://github.com/owner/repo/tree/main/scripts"
  }
]
```
- Output: The contents of `scripts` will be placed in a new folder `scripts` next to the `_fetch.json`.

#### 2. Fetch a Folder, Custom Output
```json
[
  {
    "source": "https://github.com/owner/repo/tree/main/scripts",
    "target": "./custom_folder"
  }
]
```
- Output: The contents of `scripts` will be placed directly in `custom_folder` (no extra top-level folder).

#### 3. Fetch a File
```json
[
  {
    "source": "https://github.com/owner/repo/blob/main/README.md",
    "target": "./docs/readme.md"
  }
]
```
- Output: The file will be placed at `docs/readme.md` relative to the `_fetch.json`.

## GitHub Token Setup
To avoid GitHub API rate limits and to access private repositories (if you modify the script for that), you should provide a personal access token. The token is read from `data/fetcher/config.json` (which is gitignored by default).

1. Create the file `data/fetcher/config.json` (create the folders if they do not exist).
2. Add the following content, replacing `YOUR_TOKEN_HERE` with your GitHub personal access token:

```json
{
  "github_token": "YOUR_TOKEN_HERE"
}
```

3. Make sure this file is not committed to version control (it is gitignored by default).

If the token is missing or invalid:
- The script will still work for public repositories, but you may encounter API rate limits from GitHub.
- Private repositories will be skipped, and a warning will be shown.

> **Note:** You can generate a personal access token from your GitHub account settings under **Developer settings > Personal access tokens**. For public repositories, no special scopes are required.

## Usage

### 1. Add the Filter to Your Regolith Config
In your `config.json`:
```json
{
  "regolith": {
    "filterDefinitions": {
      "fetcher": {
        "runWith": "python",
        "script": "../fetcher.py"
      }
    },
    "profiles": {
      "default": {
        "filters": [
          { "filter": "fetcher" }
        ]
      }
    }
  }
}
```

### 2. Create a _fetch.json
Place a `_fetch.json` in any folder you want to fetch content into. See above for format.

### 3. Run Regolith
Run your Regolith build as usual:
```sh
regolith build
```

The filter will process all `_fetch.json` files, fetch the specified content, and remove the `_fetch.json` files after use.

## Caching & Efficiency
- Downloads are cached by the latest commit hash of the source path. If the content hasn't changed, the filter will use the cached version.
- The cache is stored in your system's temp directory and is managed automatically.

## Notes & Best Practices
- Only public GitHub repositories are supported by default.
- The filter will not copy internal marker files (like `_downloaded`) to your output.
- If you want to always overwrite the output, simply re-run the filter; it will clean and replace the target directory.
- If you specify a `target`, it must be a relative path from the `_fetch.json` location.
- The filter removes `_fetch.json` after processing to avoid repeated downloads.

## Troubleshooting
- If you encounter issues with downloads, check your internet connection and ensure the GitHub URL is correct.
- For private repositories, you must provide a valid GitHub token with access. If you do not, the script will skip the fetch and warn you.
- If the filter does not seem to run, ensure it is correctly referenced in your Regolith config and that Python dependencies are installed (`fsspec`, `requests`).

## License
MIT License

## Contributing
Contributions and suggestions are welcome! Please open an issue or pull request on the repository.

---

For more information about Regolith, see the [Regolith documentation](https://regolith-docs.readthedocs.io/en/latest/).
