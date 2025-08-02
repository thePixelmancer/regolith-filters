import datetime
from pathlib import Path
import json
from ruamel.yaml import YAML
import json5
import tomllib  # Use 'import tomli as tomllib' if on Python < 3.11
from typing import Union
import sys

# --------------------------------- CONVERSION FEATURES --------------------------------- #
yaml = YAML(typ="safe")

if len(sys.argv) > 1:
    settings = json.loads(sys.argv[1])
FOLDERS = settings.get("folders", ["RP", "BP"])
MULTILINE_METHOD = settings.get("multiline_method", "first_index")

def yaml_loader(f):
    docs = list(yaml.load_all(f))
    if len(docs) == 1:
        return docs[0]  # Single document
    else:
        return docs  # Multiple documents as a list

EXTENSION_LOADERS = {
    ".yaml": yaml_loader,
    ".yml": yaml_loader,
    ".json5": json5.load,
    ".jsonc": json5.load,
    ".toml": lambda f: tomllib.load(f),
}


def json_default(obj):
    if isinstance(obj, (datetime.date, datetime.datetime, datetime.time)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def convert_file(path: Path, loader, mode: str = "r", delete_original: bool = True):
    print(f"Converting: {path}")
    open_mode = mode
    with path.open(open_mode, encoding="utf-8" if "b" not in mode else None) as f:
        data = loader(f)

    json_path = path.with_suffix(".json")
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=json_default)

    if delete_original:
        path.unlink()


def process_file(root_dir: Path, delete_original: bool = True):
    for ext, loader in EXTENSION_LOADERS.items():
        mode = "rb" if ext == ".toml" else "r"
        for path in root_dir.rglob(f"*{ext}"):
            convert_file(path, loader, mode=mode, delete_original=delete_original)

    # Normalize .json files only (not YAML or TOML)
    for path in root_dir.rglob("*.json"):
        normalize_multiline_json(path)


# ------------------------------------ JSON FEATURES ----------------------------------- #
def normalize_multiline_json(path: Path):
    """Reads a JSON file, finds arrays starting with '>-' and replaces them
    with a space-joined string of the rest of the array. The result is saved
    back to the same file.
    """

    def transform_with_value(value):
        if isinstance(value, list):
            if value and value[0] == ">-":
                return " ".join(str(item) for item in value[1:])
            else:
                return [transform_with_value(v) for v in value]
        elif isinstance(value, dict):
            return {k: transform_with_value(v) for k, v in value.items()}
        else:
            return value

    def transform_with_key(obj):
        if isinstance(obj, dict):
            new_obj = {}
            for k, v in obj.items():
                if k.endswith(">-") and isinstance(v, list):
                    new_key = k[:-2]  # Remove the >-
                    new_obj[new_key] = " ".join(str(item) for item in v)
                else:
                    new_obj[k] = transform_with_key(v)
            return new_obj
        elif isinstance(obj, list):
            return [transform_with_key(item) for item in obj]
        else:
            return obj

    data = json5.loads(path.read_text(encoding="utf-8"))
    if MULTILINE_METHOD == "first_index":
        transformed = transform_with_value(data)
    elif MULTILINE_METHOD == "key_suffix":
        transformed = transform_with_key(data)
    else:
        transformed = data
    path.write_text(
        json.dumps(transformed, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# -------------------------------------------------------------------------------------- #
if __name__ == "__main__":
    for folder in FOLDERS:
        folder_path = Path(folder)
        if folder_path.is_dir():
            print(f"Processing folder: {folder_path}")
            process_file(folder_path, delete_original=True)
        else:
            print(f"Folder does not exist: {folder_path}")
