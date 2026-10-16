import os
import shutil
from datetime import datetime
from pathlib import Path
import sys

# ============================================================
# Paths
# ============================================================

base_dir = Path(__file__).resolve().parent.parent.parent.parent
txt_dir = base_dir / "Txt Files"

config_path = txt_dir / "Paths.txt"
settings_path = txt_dir / "CheckVid_Config.txt"
history_file = txt_dir / "YoutubeChannelHistory.txt"

# ============================================================
# Load YouTube Folder
# ============================================================

if os.path.exists(config_path):
    with open(config_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    if not lines:
        print("Paths.txt is empty.")
        exit()

    Youtube_folder = lines[0].strip()
else:
    print("No Folder Paths Known")
    exit()

# ============================================================
# Settings (CLI Argument Priority with Config File Fallback)
# ============================================================

DELETE_EMPTY_DIR_DEFAULT = False

if len(sys.argv) > 1:
    # GUI passes 'True' or 'False' for Keep Folders.
    # If Keep Folders = True, DELETE_EMPTY_FOLDERS should be False.
    # If Keep Folders = False, DELETE_EMPTY_FOLDERS should be True.
    keep_folders_arg = sys.argv[1].lower() == "true"
    DELETE_EMPTY_FOLDERS = not keep_folders_arg
else:
    DELETE_EMPTY_FOLDERS = DELETE_EMPTY_DIR_DEFAULT
    if os.path.exists(settings_path):
        with open(settings_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith("DELETE_EMPTY_FOLDERS="):
                    DELETE_EMPTY_FOLDERS = (
                        line.strip().split("=")[1].lower() == "true"
                    )

# ============================================================
# History
# ============================================================

existing_channels = set()

if not os.path.exists(history_file):
    open(history_file, 'w', encoding='utf-8').close()

with open(history_file, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue

        if " | " in line:
            _, name = line.split(" | ", 1)
            existing_channels.add(name.strip())
        else:
            existing_channels.add(line)

new_channels = []

for folder in os.listdir(Youtube_folder):

    folder_path = os.path.join(Youtube_folder, folder)

    if not os.path.isdir(folder_path):
        continue

    clean_name = folder.replace(" ✔", "").strip()

    if clean_name not in existing_channels:
        new_channels.append(clean_name)
        existing_channels.add(clean_name)

if new_channels:
    today = datetime.now().strftime("%Y-%m-%d")

    with open(history_file, 'a', encoding='utf-8') as f:
        for channel in sorted(new_channels):
            f.write(f"{today} | {channel}\n")

# ============================================================
# Video Extensions
# ============================================================

video_extensions = {
    ".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".webm"
}

# ============================================================
# Main Loop
# ============================================================

for folder in os.listdir(Youtube_folder):

    folder_path = os.path.join(Youtube_folder, folder)

    if not os.path.isdir(folder_path):
        continue

    items = os.listdir(folder_path)

    contains_videos = any(
        item.lower().endswith(tuple(video_extensions))
        for item in items
    )

    contains_subfolders = any(
        os.path.isdir(os.path.join(folder_path, item))
        for item in items
    )

    # ========================================================
    # DELETE MODE
    # ========================================================

    if DELETE_EMPTY_FOLDERS:

        if not contains_videos and not contains_subfolders:
            try:
                # remove read-only/system/hidden BEFORE deletion
                os.system(f'attrib -r -s -h "{folder_path}" /s /d')

                shutil.rmtree(folder_path)
                print(f"Deleted empty folder: {folder}")

            except Exception as e:
                print(f"Failed to delete {folder}: {e}")

        continue

    # ========================================================
    # NORMAL MODE (✔ system)
    # ========================================================

    if contains_videos and "✔" not in folder:

        new_name = f"{folder} ✔"
        new_path = os.path.join(Youtube_folder, new_name)

        shutil.move(folder_path, new_path)
        print(f"Marked: {new_name}")

    elif not contains_videos and "✔" in folder:

        new_name = folder.replace(" ✔", "")
        new_path = os.path.join(Youtube_folder, new_name)

        shutil.move(folder_path, new_path)
        print(f"Unmarked: {new_name}")