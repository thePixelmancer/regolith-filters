import datetime
from pathlib import Path
import json
from ruamel.yaml import YAML
import json5
import tomllib  # Use 'import tomli as tomllib' if on Python < 3.11
from typing import Union

yaml = YAML(typ="safe")


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


def to_json(root_dir: Union[str, Path], delete_original: bool = True):
    root = Path(root_dir)

    # YAML/YML
    def yaml_loader(f): return list(yaml.load_all(f))[0]
    for ext in ("*.yaml", "*.yml"):
        for path in root.rglob(ext):
            convert_file(path, yaml_loader, delete_original=delete_original)

    # JSON5 + JSONC
    for ext in ("*.json5", "*.jsonc"):
        for path in root.rglob(ext):
            convert_file(path, json5.load, delete_original=delete_original)

    # TOML
    for path in root.rglob("*.toml"):
        convert_file(path, tomllib.load, mode="rb", delete_original=delete_original)


if __name__ == "__main__":
    to_json(".", delete_original=True)
