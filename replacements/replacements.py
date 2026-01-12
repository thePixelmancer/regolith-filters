from pathlib import Path
import json
import sys
import os
from pynbt import NBTFile, TAG_String


def replace_in_nbt(obj, replacements):
    """Recursively replace strings in all NBT tag values."""
    if isinstance(obj, TAG_String):
        for target, replacement in replacements.items():
            obj.value = obj.value.replace(target, replacement)
    elif isinstance(obj, dict):
        for key, value in obj.items():
            replace_in_nbt(value, replacements)
    elif isinstance(obj, list):
        for item in obj:
            replace_in_nbt(item, replacements)


def replace_in_nbt_file(file_path, replacements):
    """Replace strings in an NBT file (.mcstructure format)."""
    try:
        with open(file_path, "rb") as io:
            nbt = NBTFile(io, little_endian=True)

        replace_in_nbt(nbt.value, replacements)

        with open(file_path, "wb") as io:
            nbt.save(io, little_endian=True)
    except Exception as e:
        print(f"Could not process NBT file {file_path}: {e}")
        sys.exit()


def replace_in_text_file(file_path, replacements):
    try:
        text = file_path.read_text(encoding="utf-8")
    except Exception as e:
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
                    sys.exit()


def rename_files(root_path, replacements):
    # Walk bottom-up so we rename files after their folders
    for file in sorted(Path(root_path).rglob("*"), key=lambda p: -len(p.parts)):
        if file.is_file():
            new_name = file.name
            for target, replacement in replacements.items():
                new_name = new_name.replace(target, replacement)
            if new_name != file.name:
                new_file = file.parent / new_name
                try:
                    file.rename(new_file)
                except Exception as e:
                    print(f"Could not rename file {file} to {new_file}: {e}")
                    sys.exit()


def main():
    if len(sys.argv) < 2:
        print("No replacement settings defined.")
        sys.exit()
    config = json.loads(sys.argv[1])
    replacements = config.get("replace", None)
    extensions = config.get("extension_whitelist", None)
    replace_folders = config.get("rename_folders", False)
    replace_nbt = config.get("replace_nbt", False)
    replace_files = config.get("rename_files", False)
    paths = config.get("paths", ["RP", "BP"])
    if not replacements:
        print("No replacements defined.")
        sys.exit()

    for path in paths:
        # First, rename folders
        if replace_folders:
            rename_folders(path, replacements)
        # Then, rename files
        if replace_files:
            rename_files(path, replacements)
        # Then, replace in files
        for file in Path(path).rglob("*"):
            if file.is_file():
                # Handle NBT files (.mcstructure)
                if replace_nbt and file.suffix == ".mcstructure":
                    replace_in_nbt_file(file, replacements)
                # Handle text files
                elif extensions is None or (
                    isinstance(extensions, list) and file.suffix in extensions
                ):
                    replace_in_text_file(file, replacements)


if __name__ == "__main__":
    main()
