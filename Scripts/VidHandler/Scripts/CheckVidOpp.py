import os
import shutil
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent.parent.parent
txt_dir = base_dir / "Txt Files"
config_path = txt_dir / "Paths.txt" # Navigate to E:\Projects\VidHandler(Port)\Paths.txt

# Read the Paths.txt file to load YouTube and Anime folder paths
if os.path.exists(config_path):
    with open(config_path, 'r') as file:
        lines = file.readlines()
        Youtube_folder = lines[0].strip()  # Assuming the first line contains the YouTube folder path

else:
    print("No Folder Paths Known")

# Iterate through subfolders in the parent directory
for folder in os.listdir(Youtube_folder):
    folder_path = os.path.join(Youtube_folder, folder)

    # Check if it's a folder and contains a check mark
    if os.path.isdir(folder_path) and "✔" in folder:
        new_folder_name = folder.replace(" ✔", "")
        new_folder_path = os.path.join(Youtube_folder, new_folder_name)

        # Ensure there's no name conflict before renaming
        if not os.path.exists(new_folder_path):
            shutil.move(folder_path, new_folder_path)
            print(f"Check mark removed: {new_folder_name}")