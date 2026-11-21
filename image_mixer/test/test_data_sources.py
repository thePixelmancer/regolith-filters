import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MIXER_FIXTURE = (
    PROJECT_ROOT / "test" / "packs" / "data" / "image_mixer" / "mixers" / "data_sources.json"
)


class DataSourceTest(unittest.TestCase):
    def test_composites_images_from_data_without_pack_sources(self):
        fixture_root = PROJECT_ROOT / "test" / "packs"
        data_root = (fixture_root / "data").resolve()
        mixer = json.loads(MIXER_FIXTURE.read_text(encoding="utf-8"))
        for layer in mixer["layers"]:
            source = (fixture_root / layer["path"]).resolve()
            self.assertTrue(source.is_relative_to(data_root), str(source))
            self.assertTrue(source.is_file(), str(source))

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "BP").mkdir()
            (root / "RP").mkdir()
            mixer_dir = root / "data" / "image_mixer" / "mixers"
            mixer_dir.mkdir(parents=True)
            shutil.copyfile(MIXER_FIXTURE, mixer_dir / MIXER_FIXTURE.name)
            recipe_dir = root / "BP" / "recipes"
            recipe_dir.mkdir()
            (recipe_dir / "diamond.json").write_text(
                json.dumps({
                    "format_version": "1.20.10",
                    "minecraft:recipe_furnace": {
                        "description": {"identifier": "test:diamond"},
                        "tags": ["furnace"],
                        "input": "minecraft:diamond",
                        "output": "minecraft:diamond",
                    },
                }),
                encoding="utf-8",
            )

            source_dir = mixer_dir.parent / "vanilla_items"
            source_dir.mkdir()
            Image.new("RGBA", (4, 4), (255, 0, 0, 255)).save(source_dir / "apple.png")
            Image.new("RGBA", (2, 2), (0, 0, 255, 255)).save(source_dir / "stick.png")

            result = subprocess.run(
                [sys.executable, str(PROJECT_ROOT / "image_mixer.py")],
                cwd=root,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("[WARNING]", result.stdout + result.stderr)

            output = root / "RP" / "textures" / "output" / "data_sources" / "data_sources.png"
            with Image.open(output) as image:
                self.assertEqual(image.size, (4, 4))
                self.assertEqual(image.getpixel((0, 0)), (255, 0, 0, 255))
                self.assertEqual(image.getpixel((1, 1)), (0, 0, 255, 255))

            (mixer_dir.parent / "texture_map.json").write_text("{", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(PROJECT_ROOT / "image_mixer.py")],
                cwd=root,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("[WARNING]", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
