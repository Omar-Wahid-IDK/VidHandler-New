import os
import subprocess
from pathlib import Path

def normalize_name(name):
    # Normalize by converting to lowercase and removing spaces or underscores
    return name.lower().replace(" ", "").replace("_", "")

def set_folder_icon(folder_path, icon_path):
    desktop_ini_path = os.path.join(folder_path, 'desktop.ini')

    # Write desktop.ini with full icon path
    with open(desktop_ini_path, 'w') as f:
        f.write(f"""[.ShellClassInfo]
IconResource={icon_path},0
ConfirmFileOp=0
""")

    # Set file attributes: Hidden and Read-only
    subprocess.run(['attrib', '+h', desktop_ini_path], shell=True)
    subprocess.run(['attrib', '+r', folder_path], shell=True)

def apply_icon_to_folder(folder_path, icon_filename, icons_folder):
    icon_path = os.path.join(icons_folder, icon_filename)
    desktop_ini_path = os.path.join(folder_path, 'desktop.ini')

    if os.path.isdir(folder_path):
        if os.path.exists(desktop_ini_path):
            print(f"Icon already set for: {folder_path}")
            return

        try:
            set_folder_icon(folder_path, icon_path)
            print(f"Applied {icon_filename} to {folder_path}")
        except PermissionError as e:
            print(f"Permission denied for {folder_path}: {e}")
    else:
        print(f"Folder not found: {folder_path}")

# Main
script_dir = os.path.dirname(__file__)
config_path = os.path.join(script_dir, '..', '..', '..', 'Txt Files', 'Paths.txt')
base_dir = Path(__file__).resolve().parent.parent.parent.parent

if os.path.exists(config_path):
    with open(config_path, 'r') as file:
        lines = file.readlines()
        base_folder = lines[0].strip()
else:
    print("No Folder Paths Known")
    exit()

icons_folder = base_dir / "Icons" / "Icon"

# Get icon files and folders
icon_files = [f for f in os.listdir(icons_folder) if f.lower().endswith('.ico')]
folders = [f for f in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, f))]

# Preprocess normalized icon names without extensions
normalized_icons = {
    normalize_name(icon).replace('.ico', ''): icon
    for icon in icon_files
}

for folder in folders:
    normalized_folder = normalize_name(folder)
    matched_icon = None

    # First: exact match
    if normalized_folder in normalized_icons:
        matched_icon = normalized_icons[normalized_folder]
    else:
        # Second: partial matches only where folder is prefix
        possible_matches = [
            (icon_norm, original_icon)
            for icon_norm, original_icon in normalized_icons.items()
            if icon_norm.startswith(normalized_folder)
            and icon_norm != normalized_folder
        ]

        if possible_matches:
            # Prefer shorter suffixes (e.g., avoid MK2 when possible)
            possible_matches.sort(key=lambda x: len(x[0]))
            matched_icon = possible_matches[0][1]

    if matched_icon:
        folder_path = os.path.join(base_folder, folder)
        apply_icon_to_folder(folder_path, matched_icon, icons_folder)
    else:
        print(f"No matching icon found for {folder}")
    print("-" * 30)
