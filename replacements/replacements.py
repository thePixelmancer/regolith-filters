from pathlib import Path
import json
import sys

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


if __name__ == "__main__":

    config = json.loads("data/replacements/config.json")
    replacements = config.get("replacements", {})
    extensions = config.get("extensions", [])
    paths = config.get("paths", [])
    
    for path in paths:
        for file in path.rglob("*"):
            if file.is_file() and file.suffix in extensions:
                replace_in_file(file, replacements)
