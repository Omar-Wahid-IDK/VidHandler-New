import os
import shutil
import re

# --------------------------------------------------------------------------------- Folders
script_dir = os.path.dirname(__file__)
config_path = os.path.join(script_dir, '..', '..', '..', 'Txt Files', 'Paths.txt')

if os.path.exists(config_path):
    with open(config_path, 'r') as file:
        lines = file.readlines()
        Youtube_folder = lines[0].strip()
        Anime_folder = lines[1].strip()
else:
    print("No Folder Paths Known")

VID_FOLDER = os.path.expanduser('~') + r'\Downloads\Video'

print(f"[CONFIG] Youtube Folder: {Youtube_folder}")
print(f"[CONFIG] Anime Folder: {Anime_folder}")
print(f"[CONFIG] Source Folder: {VID_FOLDER}")

SORTED_FOLDERS = {}

# -------------------------------------------------------------------------------- Populate SORTED_FOLDERS with YouTube folders
print("\n[INIT] Populating SORTED_FOLDERS from YouTube folder...")
for Folder in os.listdir(Youtube_folder):
    Folder_Path = os.path.join(Youtube_folder, Folder)
    if not os.path.isdir(Folder_Path):
        continue
    SORTED_FOLDERS[Folder.lower()] = Folder_Path
    print(f" → Added YouTube folder: {Folder_Path}")

# -------------------------------------------------------------------------------- Populate SORTED_FOLDERS with Anime folders
print("\n[INIT] Populating SORTED_FOLDERS from Anime folder...")
for Folder in os.listdir(Anime_folder):
    Folder_Path = os.path.join(Anime_folder, Folder)
    if not os.path.isdir(Folder_Path):
        continue
    SORTED_FOLDERS[Folder.lower()] = Folder_Path
    print(f" → Added Anime folder: {Folder_Path}")

# -------------------------------------------------------------------------------- Load known anime titles as dictionary {original_name: english_name}
anime_titles_path = os.path.join(script_dir, '..', '..', 'anime_name.txt')
KNOWN_ANIME_TITLES = {}

if os.path.exists(anime_titles_path):
    with open(anime_titles_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or '|' not in line:
                continue
            original, english = map(str.strip, line.split('|', 1))
            KNOWN_ANIME_TITLES[original.lower()] = english
    print(f"\n[LOAD] Loaded {len(KNOWN_ANIME_TITLES)} known anime titles")

# -------------------------------------------------------------------------------- Check if this vid is anime or not
def is_anime_video(filename):
    """Detect anime video if filename has [AH], (1080p), and either S1E2 or E2."""
    name = filename.lower()

    has_ah = re.search(r'\[ah\]', name)
    has_1080p = re.search(r'\(1080p\)', name)
    has_ep = re.search(r's\d+e\d+|e\d+|[_\-\s](\d{1,3})(?=[_\-\s\.])', name) # Match S1E2 or E2

    if has_ah and has_1080p and has_ep:
        print(f"[ANIME DETECTED] Filename contains [AH], (1080p), and episode: {filename}")
        return True

    return False

# -------------------------------------------------------------------------------- Ensure Folders Exist
print("\n[CHECK] Ensuring all folders exist...")
for key, folder in SORTED_FOLDERS.items():
    folder = folder.strip()
    SORTED_FOLDERS[key] = folder
    print(f" → Checking folder: {repr(folder)}")
    if not os.path.exists(folder):
        print(f"   ➤ Creating folder: {folder}")
        os.makedirs(folder, exist_ok=True)

# -------------------------------------------------------------------------------- Anime Season Detection and Folder Naming
def get_anime_folder_and_season(filename):
    """Returns the correct folder and season subfolder if it's an anime episode."""
    if not is_anime_video(filename):
        print(f"[SKIP] Not anime: {filename}")
        return None

    name_without_ext = os.path.splitext(filename)[0]

    # Remove [AH], (1080p), S1E2, E2 etc. but keep the name only
    # Inside get_anime_folder_and_season(), replace the cleaning block with this:

    # Remove [AH], (1080p), S1E2, E2, P1, Part 1 etc., but keep the name only
    cleaned_name = re.sub(r'\[.*?\]', '', name_without_ext)  # Remove [AH]
    cleaned_name = re.sub(r'\(.*?p\)', '', cleaned_name)  # Remove (1080p)
    cleaned_name = re.sub(r's\d{1,2}e?\d{0,3}', '', cleaned_name, flags=re.IGNORECASE)  # Remove S1E2
    cleaned_name = re.sub(r'\bE\d+\b', '', cleaned_name, flags=re.IGNORECASE)  # Remove E2, E10 etc.
    cleaned_name = re.sub(r'\bP\d+\b', '', cleaned_name, flags=re.IGNORECASE)  # Remove P1
    cleaned_name = re.sub(r'\bPart\s?\d+\b', '', cleaned_name, flags=re.IGNORECASE)  # Remove Part 1
    cleaned_name = cleaned_name.strip()
    cleaned_name = re.sub(r'\s+', ' ', cleaned_name)


    print(f"[CLEAN] Original: {filename} → Cleaned: {cleaned_name}")

    if not cleaned_name:
        cleaned_name = "Etc"

    anime_key = cleaned_name.lower()

    # Use English name if exists in known titles
    if anime_key in KNOWN_ANIME_TITLES:
        folder_name = KNOWN_ANIME_TITLES[anime_key]
        print(f"[MATCH] Using English name for folder: {folder_name}")
    else:
        folder_name = cleaned_name.title()

    base_folder = os.path.join(Anime_folder, folder_name)

    if anime_key not in SORTED_FOLDERS:
        print(f"[NEW FOLDER] Registering anime folder: {base_folder}")
        SORTED_FOLDERS[anime_key] = base_folder

    # Detect season number
    season_match = re.search(r's(\d+)', filename.lower())
    if season_match:
        season_num = season_match.group(1)
        season_folder_name = f"Season ({season_num})"
        full_season_path = os.path.join(base_folder, season_folder_name)
        print(f"[SEASON] Season detected: {season_num} → {full_season_path}")
    else:
        season_folders = [f for f in os.listdir(base_folder) if re.match(r'Season \(\d+\)', f)] if os.path.exists(base_folder) else []
        if season_folders:
            full_season_path = os.path.join(base_folder, "Season (1)")
            print(f"[SEASON] No season tag, defaulting to: {full_season_path}")
        else:
            full_season_path = base_folder
            print(f"[SEASON] No season folders found → Using base folder: {base_folder}")

    if not os.path.exists(full_season_path):
        print(f"[CREATE] Making season path: {full_season_path}")
        os.makedirs(full_season_path, exist_ok=True)

    return full_season_path

# -------------------------------------------------------------------------------- General Folder Detection for YouTube videos
def get_channel_folder(filename):
    """Returns the correct folder based on the channel name before the '-' or 'Etc' if invalid."""
    name_without_ext = os.path.splitext(filename)[0]
    match = re.match(r'^(.+?)\s*-\s+.+', name_without_ext)
    if match:
        channel_name = match.group(1).strip()
        if len(channel_name.split()) > 4 or not re.match(r'^[\w\s\-\.\']+$', channel_name):
            channel_name = "Etc"
    else:
        channel_name = "Etc"

    cleaned_name = re.sub(r'[^a-zA-Z0-9\s\-\.\']', '', channel_name)
    cleaned_name = re.sub(r'\s+', ' ', cleaned_name).strip()

    print(f"[CHANNEL] Extracted: {filename} → Channel: {cleaned_name}")

    if not cleaned_name:
        cleaned_name = "Etc"

    new_folder_path = os.path.join(Youtube_folder, cleaned_name)

    if not os.path.exists(new_folder_path):
        print(f"[CREATE] Creating channel folder: {new_folder_path}")
        os.makedirs(new_folder_path, exist_ok=True)

    SORTED_FOLDERS[cleaned_name.lower()] = new_folder_path

    return new_folder_path

# -------------------------------------------------------------------------------- Video Moving
def move_videos():
    """Move videos to their respective folders based on channel names and seasons."""
    moved_files = 0
    print(f"\n[START] Scanning {VID_FOLDER} for videos...\n")

    for file in os.listdir(VID_FOLDER):
        src = os.path.join(VID_FOLDER, file)
        if not os.path.isfile(src):
            continue

        print(f"\n[FILE] Processing: {file}")
        anime_dest = get_anime_folder_and_season(file)
        dest_folder = anime_dest if anime_dest else get_channel_folder(file)

        if dest_folder.startswith(VID_FOLDER):
            print(f"⚠️ Skipping {file}: Preventing accidental nesting.")
            continue

        dest = os.path.join(dest_folder, file)

        try:
            shutil.move(src, dest)
            print(f"✅ Moved: {file} → {dest_folder}")
            moved_files += 1
        except Exception as e:
            print(f"❌ Error moving {file}: {e}")

    if moved_files == 0:
        print("\n[INFO] No videos found to move.")

# -------------------------------------------------------------------------------- Run the script
if __name__ == "__main__":
    print(f"Sorting videos from: {VID_FOLDER}")
    move_videos()
