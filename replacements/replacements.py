from pathlib import Path
import json
import sys
import os


def replace_in_file(file_path, replacements):
    try:
        text = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Skipping {file_path} (cannot read): {e}")
        return

    original_text = text
    for target, replacement in replacements.items():
        text = text.replace(target, replacement)

    if text != original_text:
        file_path.write_text(text, encoding="utf-8")


def rename_folders(root_path, replacements):
    # Walk bottom-up so we rename inner folders before their parents
    for dirpath, dirnames, filenames in os.walk(root_path, topdown=False):
        for dirname in dirnames:
            old_dir = Path(dirpath) / dirname
            new_dirname = dirname
            for target, replacement in replacements.items():
                new_dirname = new_dirname.replace(target, replacement)
            if new_dirname != dirname:
                new_dir = Path(dirpath) / new_dirname
                try:
                    old_dir.rename(new_dir)
                except Exception as e:
                    print(f"Could not rename folder {old_dir} to {new_dir}: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("No replacement settings defined.")
        sys.exit()
    config = json.loads(sys.argv[1])
    replacements = config.get("replace", None)
    if not replacements:
        print("No replacements defined.")
        sys.exit()
    extensions = config.get(
        "extensions", [".js", ".ts", ".json", ".material", ".mcfunction", ".txt", ".md"]
    )
    replace_folders = config.get("replace_folders", False)
    paths = config.get("paths", ["RP", "BP"])

    for path in paths:
        # First, rename folders
        if replace_folders:
            rename_folders(path, replacements)
        # Then, replace in files
        for file in Path(path).rglob("*"):
            if file.is_file() and file.suffix in extensions:
                replace_in_file(file, replacements)
