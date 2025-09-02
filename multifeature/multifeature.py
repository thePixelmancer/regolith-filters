from pathlib import Path
import json
import json5
import shutil
import sys
from pretty_print import (
    Colors,
    print_section,
    print_success,
    print_error,
    print_warning,
    print_info,
)
SETTINGS = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
USE_NAMESPACE = SETTINGS.get("use_namespace", False)

def remove_namespace(value: str) -> tuple[str, str]:
    """
    Splits a string into (namespace, name) at the first colon.
    Example: 'minecraft:feature_rule' -> ('minecraft:', 'feature_rule')
    If no colon is found, returns ('', value).
    """
    if ":" in value:
        namespace, name = value.split(":", 1)
        return namespace, name
    return "", value


def process_feature(feature: dict, file_path: Path):
    # --------------------- Getting basic information from the feature --------------------- #
    if "format_version" not in feature or len(feature) != 2:
        print_error(
            f"Features in [{file_path}] must contain 'format_version' and one feature type."
        )
        sys.exit(1)

    feature_type = next(key for key in feature if key != "format_version")
    feature_data = feature[feature_type]

    is_rule = feature_type == "minecraft:feature_rules"

    desc = feature_data.get("description", {})
    identifier = desc.get("identifier")

    if not identifier:
        print_error(f"Feature in [{file_path}] has no identifier")
        sys.exit(1)

    identifier_namespace, identifier_name = remove_namespace(identifier)

    # Check for invalid characters in feature rule identifiers
    if is_rule:
        invalid_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
        found_invalid = [char for char in invalid_chars if char in identifier_name]

        if found_invalid:
            print_error(
                f"Invalid Character Error:\nFeature rule in [{file_path}] has invalid characters in identifier '{identifier}'."
            )
            print_warning(
                f"Feature rules need to have the same ID as the filename, and these characters aren't allowed in filenames. Consider renaming '{identifier}' to use only letters, numbers, underscores, and hyphens"
            )
            sys.exit(1)

    # Output path
    category = "feature_rules" if is_rule else "features"
    filename = f"{identifier_name}.json"

    output_path = Path("BP", category, filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as out_f:
        json.dump(feature, out_f, indent=2)


def process_multifeature(file_path: Path):
    """
    Processes a multifeature JSON/YAML file and outputs individual feature files
    to their respective directories based on feature type and identifier.
    """
    with file_path.open("r", encoding="utf-8") as f:
        data = json5.load(f)

    if isinstance(data, dict):
        data = [data]
    elif not isinstance(data, list):
        print_error(f"Expected a list or object in file [{file_path}]")
        sys.exit(1)

    for feature in data:
        process_feature(feature, file_path)


# -------------------------------------------------------------------------------------- #
# Entrypoint
# -------------------------------------------------------------------------------------- #
if __name__ == "__main__":
    print_section("MultiFeature", symbol="=", color=Colors.CYAN)
    input_dir = Path("BP/multifeatures")
    input_dir.mkdir(parents=True, exist_ok=True)

    processed_files = 0

    for file_path in input_dir.glob("*.multifeature.json"):
        process_multifeature(file_path)
        processed_files += 1

    if processed_files:
        print_success(f"Successfully processed {processed_files} multifeature file(s)")
    else:
        print_warning("No multifeature files found to process")

    shutil.rmtree(input_dir)  # remove the input directory after processing

    # Notify user about optional schema configuration
    print_info(
        "Optional: For IntelliSense support, visit the documentation to add schema configuration to your .vscode/settings.json"
    )
    print_section(symbol="=", color=Colors.CYAN)
