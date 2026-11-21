import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class RecipeTextureTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.recipe_dir = self.root / "BP" / "recipes"
        self.recipe_dir.mkdir(parents=True)
        (self.root / "RP").mkdir()
        self.data_dir = self.root / "data" / "image_mixer"
        (self.data_dir / "mixers").mkdir(parents=True)
        Image.new("RGBA", (2, 2), (255, 0, 0, 255)).save(self.data_dir / "base.png")
        self.write_json(self.data_dir / "mixers" / "test.json", {
            "output_folder": "RP/output",
            "output_template": "{recipe_id}.png",
            "combination_mode": "zip",
            "recipe_generation": {"id_whitelist": ["included"]},
            "layers": [
                {"path": "data/image_mixer/base.png"},
                {"path": "{shapeless_slot_0}"},
            ],
        })
        self.write_recipe("included", "minecraft:diamond", "minecraft:unused")
        self.write_recipe("excluded", "minecraft:excluded", "minecraft:excluded_result")

    def write_json(self, path, value):
        path.write_text(json.dumps(value), encoding="utf-8")

    def write_recipe(self, name, ingredient, result):
        self.write_json(self.recipe_dir / f"{name}.json", {
            "format_version": "1.20.10",
            "minecraft:recipe_shapeless": {
                "description": {"identifier": f"test:{name}"},
                "tags": ["crafting_table"],
                "ingredients": [{"item": ingredient}],
                "result": {"item": result},
            },
        })

    def run_mixer(self):
        return subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "image_mixer.py")],
            cwd=self.root,
            capture_output=True,
            text=True,
        )

    def test_missing_mapping_warns_only_for_requested_texture(self):
        result = self.run_mixer()
        self.assertEqual(result.returncode, 0, result.stderr)
        output = result.stdout + result.stderr
        self.assertIn("[WARNING]", output)
        self.assertIn("minecraft:diamond", output)
        self.assertNotIn("minecraft:unused", output)
        self.assertNotIn("minecraft:excluded", output)
        with Image.open(self.root / "RP" / "output" / "included.png") as image:
            self.assertEqual(image.getpixel((0, 0)), (255, 0, 0, 255))

    def test_explicit_mapping_resolves_requested_texture(self):
        Image.new("RGBA", (2, 2), (0, 255, 0, 255)).save(self.data_dir / "diamond.png")
        self.write_json(self.data_dir / "texture_map.json", {
            "minecraft:diamond": "data/image_mixer/diamond.png",
        })
        result = self.run_mixer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("[WARNING]", result.stdout + result.stderr)
        with Image.open(self.root / "RP" / "output" / "included.png") as image:
            self.assertEqual(image.getpixel((0, 0)), (0, 255, 0, 255))

    def test_invalid_mapping_is_reported_when_needed(self):
        (self.data_dir / "texture_map.json").write_text("{", encoding="utf-8")
        result = self.run_mixer()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("JSONDecodeError", result.stderr)

    def test_missing_tag_warns_for_requested_shaped_slot(self):
        mixer_path = self.data_dir / "mixers" / "test.json"
        mixer = json.loads(mixer_path.read_text(encoding="utf-8"))
        mixer["layers"][1]["path"] = "{shaped_slot_0}"
        self.write_json(mixer_path, mixer)
        self.write_json(self.recipe_dir / "shaped.json", {
            "format_version": "1.20.10",
            "minecraft:recipe_shaped": {
                "description": {"identifier": "test:included"},
                "pattern": ["XX", "XX"],
                "key": {"X": {"tag": "test:missing_tag"}},
                "result": {"item": "minecraft:unused"},
            },
        })
        result = self.run_mixer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("test:missing_tag", result.stdout + result.stderr)
        self.assertNotIn("minecraft:unused", result.stdout + result.stderr)
        self.assertTrue((self.root / "RP" / "output" / "included.png").is_file())

    def test_furnace_input_does_not_resolve_unused_output(self):
        mixer_path = self.data_dir / "mixers" / "test.json"
        mixer = json.loads(mixer_path.read_text(encoding="utf-8"))
        mixer["layers"][1]["path"] = "{furnace_slot_0}"
        self.write_json(mixer_path, mixer)
        self.write_json(self.recipe_dir / "furnace.json", {
            "format_version": "1.20.10",
            "minecraft:recipe_furnace": {
                "description": {"identifier": "test:included"},
                "tags": ["furnace"],
                "input": "minecraft:diamond",
                "output": "minecraft:unused",
            },
        })
        result = self.run_mixer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("minecraft:diamond", result.stdout + result.stderr)
        self.assertNotIn("minecraft:unused", result.stdout + result.stderr)
        self.assertTrue((self.root / "RP" / "output" / "included.png").is_file())

    def test_behavior_pack_item_is_resolved_without_mapping(self):
        item_dir = self.root / "BP" / "items"
        item_dir.mkdir()
        self.write_json(item_dir / "diamond.json", {
            "format_version": "1.21.70",
            "minecraft:item": {
                "description": {"identifier": "minecraft:diamond"},
                "components": {"minecraft:icon": "test.diamond"},
            },
        })
        texture_dir = self.root / "RP" / "textures"
        texture_dir.mkdir()
        self.write_json(texture_dir / "item_texture.json", {
            "resource_pack_name": "test",
            "texture_name": "atlas.items",
            "texture_data": {"test.diamond": {"textures": "textures/diamond"}},
        })
        Image.new("RGBA", (2, 2), (0, 0, 255, 255)).save(texture_dir / "diamond.png")
        result = self.run_mixer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("[WARNING]", result.stdout + result.stderr)
        with Image.open(self.root / "RP" / "output" / "included.png") as image:
            self.assertEqual(image.getpixel((0, 0)), (0, 0, 255, 255))

    def test_missing_resource_pack_texture_warns(self):
        item_dir = self.root / "BP" / "items"
        item_dir.mkdir()
        self.write_json(item_dir / "diamond.json", {
            "format_version": "1.21.70",
            "minecraft:item": {
                "description": {"identifier": "minecraft:diamond"},
                "components": {"minecraft:icon": "test.diamond"},
            },
        })
        result = self.run_mixer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("minecraft:diamond", result.stdout + result.stderr)
        self.assertIn("[WARNING]", result.stdout + result.stderr)
        self.assertTrue((self.root / "RP" / "output" / "included.png").is_file())


if __name__ == "__main__":
    unittest.main()
