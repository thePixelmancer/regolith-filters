from pathlib import Path
import json
import json5
import shutil
import sys
import os
from pathlib import Path
import json
from typing import Union

# -------------------------------------------------------------------------------------- #
# Configuration
# -------------------------------------------------------------------------------------- #
SETTINGS = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
SUBFOLDERS = SETTINGS.get("subfolders", "")


# -------------------------------------------------------------------------------------- #
# Utility Functions
# -------------------------------------------------------------------------------------- #
def deep_merge_dicts(base_data, new_data):
    """
    Recursively merges new_data into base_data.
    - Merges nested dictionaries
    - Appends to lists (avoids duplicates in json.schemas)
    """
    result = base_data.copy()
    for key, value in new_data.items():
        if key in result:
            if isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge_dicts(result[key], value)
            elif isinstance(result[key], list) and isinstance(value, list):
                # Special handling for json.schemas to avoid duplicate 'url'
                if key == "json.schemas":
                    existing_urls = {
                        item.get("url")
                        for item in result[key]
                        if isinstance(item, dict)
                    }
                    for item in value:
                        if (
                            isinstance(item, dict)
                            and item.get("url") not in existing_urls
                        ):
                            result[key].append(item)
                            existing_urls.add(item.get("url"))
                else:
                    result[key].extend(x for x in value if x not in result[key])
            else:
                result[key] = value  # Overwrite scalar or type mismatch
        else:
            result[key] = value
    return result


def remove_namespace(value: str) -> tuple[str, str]:
    """
    Splits a string into (namespace, name) at the first colon.
    Example: 'minecraft:feature_rule' -> ('minecraft:', 'feature_rule')
    If no colon is found, returns ('', value).
    """
    if ":" in value:
        namespace, name = value.split(":", 1)
        return f"{namespace}:", name
    return "", value


def normalize_path(path: str) -> str:
    """
    Normalizes a path string by removing leading slashes
    and ensuring exactly one trailing slash if not empty.
    """
    path = path.lstrip("/")
    return f"{path}/" if path and not path.endswith("/") else path


def merge_json_files(base_data: Union[Path, dict], new_data: Union[Path, dict]):
    """
    Merges JSON content from `from_data` into `to_data`.

    Arguments can be either file paths (`Path`) or already-loaded dictionaries.
    If `to_data` is a file path, the result will be saved back to it.
    If both arguments are dicts, the merged result is returned.
    """

    def load_json(source):
        if isinstance(source, dict):
            return source
        elif isinstance(source, Path):
            if not source.exists():
                return {}
            with source.open("r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    print(f"Warning: {source} is not valid JSON. Using empty dict.")
                    return {}
        else:
            raise TypeError(f"Unsupported type for JSON input: {type(source)}")

    # Load both sides
    from_dict = load_json(new_data)
    to_dict = load_json(base_data)

    # Merge
    merged_settings = deep_merge_dicts(to_dict, from_dict)

    # If to_data is a Path, write result
    if isinstance(base_data, Path):
        base_data.parent.mkdir(parents=True, exist_ok=True)
        with base_data.open("w", encoding="utf-8") as f:
            json.dump(merged_settings, f, indent=2)
    else:
        return merged_settings


# -------------------------------------------------------------------------------------- #
# Main Processing Function
# -------------------------------------------------------------------------------------- #
def process_multifeature(file_path: Path):
    """
    Processes a multifeature JSON file and rewrites its identifiers
    based on the configured subfolder structure.
    """
    with file_path.open("r", encoding="utf-8") as f:
        data = json5.load(f)

    if isinstance(data, dict):
        data = [data]
    elif not isinstance(data, list):
        raise ValueError(f"Expected a list or object in file [{file_path}]")

    for feature in data:
        if not isinstance(feature, dict):
            raise ValueError(f"Feature in [{file_path}] is not an object")

        if "format_version" not in feature or len(feature) != 2:
            raise ValueError(
                "Feature must contain 'format_version' and one feature type."
            )

        feature_type = next(key for key in feature if key != "format_version")
        feature_data = feature[feature_type]

        is_rule = feature_type == "minecraft:feature_rules"
        desc = feature_data.get("description", {})
        identifier = desc.get("identifier")
        places = (
            desc.get("places_feature")
            if is_rule
            else feature_data.get("places_feature")
        )

        if not identifier:
            raise ValueError(f"Feature in [{file_path}] has no identifier")
        if not places:
            raise ValueError(f"Feature in [{file_path}] has no places_feature")

        ns_id, name_id = remove_namespace(identifier)
        ns_places, name_places = remove_namespace(places)

        suffix = normalize_path(SUBFOLDERS)
        new_identifier = f"{ns_id}{suffix}{name_id}"
        new_places = f"{ns_places}{suffix}{name_places}"

        desc["identifier"] = new_identifier
        if is_rule:
            desc["places_feature"] = new_places
        else:
            feature_data["places_feature"] = new_places

        # Output path
        category = "feature_rules" if is_rule else "features"
        subdirs = SUBFOLDERS.split("/") if SUBFOLDERS else []
        output_path = Path("BP", category, *subdirs, f"{name_id}.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as out_f:
            json.dump(feature, out_f, indent=2)


# -------------------------------------------------------------------------------------- #
# Entrypoint
# -------------------------------------------------------------------------------------- #
if __name__ == "__main__":
    input_dir = Path("BP/multifeatures")
    if not input_dir.exists():
        print(f"Input directory {input_dir} does not exist. Exiting.")
        sys.exit(1)
    for file_path in input_dir.glob("*.multifeature.json"):
        process_multifeature(file_path)
        print(f"Processed {file_path}")

    shutil.rmtree(input_dir)
    # -------------------------------------------------------------------------------------- #
    # Merge settings.json from data/.vscode/settings.json into project .vscode/settings.json
    ROOT_DIR = Path(os.environ.get("ROOT_DIR", "."))
    VSCODE_SETTINGS = {
        "json.schemas": [
            {
                "fileMatch": ["*.multifeature.json"],
                "url": "https://raw.githubusercontent.com/thePixelmancer/regolith-filters/refs/heads/main/multifeature/data/multifeature.schema.json",
            }
        ],
        "yaml.schemas": {
            "https://raw.githubusercontent.com/thePixelmancer/regolith-filters/refs/heads/main/multifeature/data/multifeature.schema.json": "*.multifeature.yaml"
        },
    }

    vscode_project_path = ROOT_DIR / ".vscode" / "settings.json"
    merge_json_files(vscode_project_path, VSCODE_SETTINGS)
