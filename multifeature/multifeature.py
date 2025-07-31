from pathlib import Path
import json
import json5
import shutil
import sys


# -------------------------------------------------------------------------------------- #
# Configuration
# -------------------------------------------------------------------------------------- #
SETTINGS = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
SUBFOLDERS = SETTINGS.get("subfolders", "")


# -------------------------------------------------------------------------------------- #
# Utility Functions
# -------------------------------------------------------------------------------------- #
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

    if not isinstance(data, list):
        raise ValueError(f"Expected a list in file [{file_path}]")

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
    for file_path in input_dir.glob("*.multifeature.json"):
        process_multifeature(file_path)

    shutil.rmtree(input_dir)
