from pathlib import Path
import json
import sys
import os
from pynbt import NBTFile, TAG_String
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

# Lock for thread-safe printing
print_lock = Lock()

# Global config with defaults
CONFIG = {
    "replace": None,
    "rename_folders": True,
    "rename_files": True,
    "replace_in_nbt": False,
    "extension_whitelist": [],
    "paths": ["RP", "BP"],
}
if len(sys.argv) > 1:
    CONFIG.update(json.loads(sys.argv[1]))


def replace_in_nbt(obj):
    """Recursively replace strings in all NBT tag values."""
    if isinstance(obj, TAG_String):
        for target, replacement in CONFIG["replace"].items():
            obj.value = obj.value.replace(target, replacement)
    elif isinstance(obj, dict):
        for key, value in obj.items():
            replace_in_nbt(value)
    elif isinstance(obj, list):
        for item in obj:
            replace_in_nbt(item)


def replace_in_nbt_file(file_path):
    """Replace strings in an NBT file (.mcstructure format)."""
    try:
        with open(file_path, "rb") as io:
            nbt = NBTFile(io, little_endian=True)

        replace_in_nbt(nbt.value)

        with open(file_path, "wb") as io:
            nbt.save(io, little_endian=True)
    except Exception as e:
        with print_lock:
            print(f"Could not process NBT file {file_path}: {e}")
        sys.exit(1)


def replace_in_text_file(file_path):
    try:
        text = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return

    original_text = text
    for target, replacement in CONFIG["replace"].items():
        text = text.replace(target, replacement)

    if text != original_text:
        file_path.write_text(text, encoding="utf-8")


def rename_folders(root_path):
    # Walk bottom-up so we rename inner folders before their parents
    for dirpath, dirnames, filenames in os.walk(root_path, topdown=False):
        for dirname in dirnames:
            old_dir = Path(dirpath) / dirname
            new_dirname = dirname
            for target, replacement in CONFIG["replace"].items():
                new_dirname = new_dirname.replace(target, replacement)
            if new_dirname != dirname:
                new_dir = Path(dirpath) / new_dirname
                try:
                    old_dir.rename(new_dir)
                except Exception as e:
                    with print_lock:
                        print(
                            f"Could not rename folder {old_dir.resolve()} to {new_dir.resolve()}: {e}"
                        )
                    sys.exit(1)


def rename_files(root_path):
    # Walk bottom-up so we rename files after their folders
    for file in sorted(Path(root_path).rglob("*"), key=lambda p: -len(p.parts)):
        if file.is_file():
            new_name = file.name
            for target, replacement in CONFIG["replace"].items():
                new_name = new_name.replace(target, replacement)
            if new_name != file.name:
                new_file = file.parent / new_name
                try:
                    file.rename(new_file)
                except Exception as e:
                    with print_lock:
                        print(f"Could not rename file {file} to {new_file}: {e}")
                    sys.exit(1)


def process_file(file):
    """Process a single file for replacements."""

    # Handle text files
    if (
        CONFIG["extension_whitelist"] is None
        or len(CONFIG["extension_whitelist"]) == 0
        or (isinstance(CONFIG["extension_whitelist"], list) and file.suffix in CONFIG["extension_whitelist"])
    ):
        if CONFIG["replace_in_nbt"] and file.suffix == ".mcstructure":
            replace_in_nbt_file(file)
        else:
            replace_in_text_file(file)


def main():
    if not CONFIG["replace"]:
        print("No replacements defined.")
        sys.exit()

    for path in CONFIG["paths"]:
        # First, rename folders
        if CONFIG["rename_folders"]:
            rename_folders(path)
        # Then, rename files
        if CONFIG["rename_files"]:
            rename_files(path)
        # Then, replace in files using thread pool for I/O operations
        files_to_process = [file for file in Path(path).rglob("*") if file.is_file()]

        with ThreadPoolExecutor(max_workers=8) as executor:
            for file in files_to_process:
                executor.submit(process_file, file)


if __name__ == "__main__":
    main()
