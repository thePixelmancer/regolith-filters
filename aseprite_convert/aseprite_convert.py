from pathlib import Path
import subprocess
import shutil
import sys
import json

# Constants
ASEPRITE_EXTENSIONS = [".ase", ".aseprite"]
DEFAULT_CONFIG = {
    "aseprite_exe_path": "C:/Program Files/Aseprite/aseprite.exe",
    "spritesheet_type": "vertical",
}


def load_config():
    """Load configuration from command line arguments or use defaults."""
    try:
        if len(sys.argv) > 1:
            config = json.loads(sys.argv[1])
        else:
            config = DEFAULT_CONFIG.copy()
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON configuration: {e}")
        return None

    # Check for Aseprite installation
    aseprite_path = shutil.which("aseprite")
    if aseprite_path:
        config["aseprite_exe_path"] = aseprite_path
        print("Aseprite found in PATH.")
        return config
    elif (
        config.get("aseprite_exe_path") and Path(config["aseprite_exe_path"]).is_file()
    ):
        print(f"Aseprite found at {config['aseprite_exe_path']}.")
        return config
    else:
        print("Aseprite installation not found!")
        return None


def convert_atlas_layers(imgpath: Path, aseprite_exe: str) -> list[str]:
    """Convert Aseprite atlas file to separate layer PNGs with 16x16 grid alignment."""
    command = [
        aseprite_exe,
        "-b",  # Run in batch mode (no GUI)
        str(imgpath),  # Input .ase or .aseprite file
        "--split-layers",  # Export each layer separately
        # "--trim",  # Trim to content
        "--trim-by-grid",  # Then align to 16x16 grid
        "--save-as",
        f"{imgpath.parent / '{layer}'}.png",  # Export with layer name
    ]
    print(f"[Atlas] Exporting {imgpath.name} with 16x16 grid alignment")
    return command


def convert_frames(imgpath: Path, aseprite_exe: str) -> list[str]:
    """Convert Aseprite frames file to separate frame PNGs."""
    frame_path = imgpath.parent / imgpath.stem.replace("_frames", "")
    command = [
        aseprite_exe,
        "-b",  # Run in batch mode (no GUI)
        str(imgpath),  # Input .ase or .aseprite file
        "--save-as",
        f"{frame_path}_{'{frame}'}.png",  # Export numbered frames
    ]
    print(f"[Frames] Exporting {imgpath.name}")
    return command


def convert_spritesheet(
    imgpath: Path, aseprite_exe: str, spritesheet_type: str
) -> list[str]:
    """Convert Aseprite file to a spritesheet."""
    command = [
        aseprite_exe,
        "-b",  # Run in batch mode (no GUI)
        str(imgpath),  # Input .ase or .aseprite file
        "--sheet",  # Export as spritesheet
        str(imgpath.with_suffix(".png")),  # Output path
        "--sheet-type",
        spritesheet_type,  # Make it a vertical spritesheet
    ]
    print(f"[Spritesheet] Exporting {imgpath.name}")
    return command


def run_aseprite_command(command: list[str], imgpath: Path) -> None:
    """Execute the Aseprite command and handle errors."""
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to convert {imgpath}: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
    except FileNotFoundError:
        print(f"Aseprite executable not found at: {command[0]}")


def convert_aseprite(imgpath: Path, config: dict) -> None:
    """Convert Aseprite files based on their naming convention."""
    aseprite_exe = config["aseprite_exe_path"]

    # Determine conversion type and get the appropriate command
    if imgpath.stem.endswith("_atlas"):
        command = convert_atlas_layers(imgpath, aseprite_exe)
    elif imgpath.stem.endswith("_frames"):
        command = convert_frames(imgpath, aseprite_exe)
    else:
        # Everything is a spritesheet even with 1 frame
        spritesheet_type = config.get("spritesheet_type", "vertical")
        command = convert_spritesheet(imgpath, aseprite_exe, spritesheet_type)

    # Execute the command
    run_aseprite_command(command, imgpath)


def main():
    """Process all Aseprite files in the current directory and subdirectories."""
    config = load_config()
    if not config:
        return

    # Use rglob to recursively search for Aseprite files
    aseprite_files = []
    for extension in ASEPRITE_EXTENSIONS:
        aseprite_files.extend(Path("RP").rglob(f"*{extension}"))

    if not aseprite_files:
        print("No Aseprite files found.")
        return

    for imgpath in aseprite_files:
        convert_aseprite(imgpath, config)
        try:
            imgpath.unlink()  # Delete the original file
        except OSError as e:
            print(f"Failed to delete {imgpath}: {e}")


if __name__ == "__main__":
    main()
