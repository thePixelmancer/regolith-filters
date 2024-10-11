import subprocess
from pathlib import Path
import shutil
import json

# Load the configuration JSON file
config_path = Path("data/config.json")  # Adjust the path as necessary
with config_path.open() as f:
    config = json.load(f)

# Check if Aseprite is in PATH, otherwise use the default path
aseprite_exe_path = shutil.which("aseprite") or config["aseprite_exe_path"]


# Convert an Aseprite file to a PNG (or spritesheet if animated) using the Aseprite CLI.
def convert_aseprite_file(aseprite_file_path: Path) -> None:

    # If the file does not have "_frames" in its name, output as a spritesheet or PNG
    if "_frames" not in aseprite_file_path.stem:
        # If it's animated, export as a vertical spritesheet
        command = [
            aseprite_exe_path,
            "-b",  # Run in batch mode (no GUI)
            str(aseprite_file_path),  # Input .ase or .aseprite file
            "--sheet",  # Export as spritesheet
            str(aseprite_file_path.with_suffix(".png")),  # Output path
            "--sheet-type",
            config["spritesheet_type"],  # Make it a vertical spritesheet
        ]
        print(f"Exporting file {aseprite_file_path} as a spritesheet.")
    else:
        # Remove "_frames" from the file name and create the output folder
        folder_name = aseprite_file_path.stem.replace("_frames", "")
        output_folder = aseprite_file_path.parent / folder_name
        output_folder.mkdir(exist_ok=True)

        # Export each frame as a separate PNG inside the folder with simple numbering
        command = [
            aseprite_exe_path,
            "-b",  # Run in batch mode (no GUI)
            str(aseprite_file_path),  # Input .ase or .aseprite file
            "--save-as",
            str(
                output_folder / f"{folder_name}_{'{frame}'}.png"
            ),  # Export numbered frames
        ]
        print(f"Exporting frames of {aseprite_file_path} to folder {output_folder}.")

    # Run the command
    try:
        subprocess.run(
            command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        # Remove the original .aseprite file
        aseprite_file_path.unlink()  # Delete the file

    except subprocess.CalledProcessError as e:
        print(f"Failed to convert {aseprite_file_path}: {e}")


if __name__ == "__main__":
    input_directory = Path("RP")
    # Check if the input directory exists
    if not input_directory.exists():
        print(f"Input directory {input_directory} does not exist.")
    else:
        # Iterate through all .ase and .aseprite files in the directory
        for aseprite_file in input_directory.rglob("*.ase*"):
            convert_aseprite_file(aseprite_file)
