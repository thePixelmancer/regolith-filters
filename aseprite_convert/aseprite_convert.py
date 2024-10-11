from pathlib import Path  # Import the Path class for cleaner path handling.
import json
import subprocess
import shutil

# Load the configuration JSON file
with Path("data/config.json").open() as file:
    config = json.load(file)
    # Check for Aseprite installation
    if shutil.which("aseprite"):
        config["aseprite_exe_path"] = shutil.which("aseprite")
        print("Aseprite found in PATH.")
    elif Path(config["aseprite_exe_path"]).is_file():
        config["aseprite_exe_path"] = Path(config["aseprite_exe_path"])
        print(f"Aseprite found at {config['aseprite_exe_path']}.")
    else:
        print(f"Aseprite installation not found!")


def convert_aseprite(imgpath: Path) -> None:
    # If the has "_frames" in its name, output frames as separate PNGs
    if "_frames" in imgpath.stem:
        # Remove "_frames" from the file name and create the output folder
        frame_path = imgpath.parent / imgpath.stem.replace("_frames", "")

        # Export each frame as a separate PNG inside the folder with simple numbering
        command = [
            config["aseprite_exe_path"],
            "-b",  # Run in batch mode (no GUI)
            str(imgpath),  # Input .ase or .aseprite file
            "--save-as",
            f"{frame_path}_{'{frame}'}.png",  # Export numbered frames
        ]
        print(f"Exporting frames of {imgpath}.")

    else:
        # If it's animated or layered, export as a vertical spritesheet
        command = [
            config["aseprite_exe_path"],
            "-b",  # Run in batch mode (no GUI)
            str(imgpath),  # Input .ase or .aseprite file
            "--sheet",  # Export as spritesheet
            str(imgpath.with_suffix(".png")),  # Output path
            "--sheet-type",
            config["spritesheet_type"],  # Make it a vertical spritesheet
        ]
        print(f"Exporting file {imgpath} as a spritesheet.")

    # Run the command
    try:
        subprocess.run(
            command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError as e:
        print(f"Failed to convert {imgpath}: {e}")


# EXECUTE SCRIPT
if __name__ == "__main__":

    # Use rglob to recursively search for files in all subdirectories.
    for imgpath in Path(".").rglob("*"):

        # Check if the current item is a file.
        if imgpath.is_file():
            # Handle Aseprite files
            if imgpath.suffix in [".ase", ".aseprite"]:
                convert_aseprite(imgpath)  # Convert layered formats to png
                imgpath.unlink()  # Delete the original file.
