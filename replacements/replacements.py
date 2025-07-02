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
    paths = config.get("paths", ["RP", "BP"])

    for path in paths:
        for file in Path(path).rglob("*"):
            if file.is_file() and file.suffix in extensions:
                replace_in_file(file, replacements)
