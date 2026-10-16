import os
import re
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent.parent.parent
txt_dir = base_dir / "Txt Files"
video_folder = os.path.expanduser('~') + r'\Downloads\Video'
anime_detect_path = txt_dir / "anime_detect.txt"
anime_names_path = txt_dir / "anime_names.txt"

# ------------------ Resolution filters ------------------
RESOLUTION_NUMBERS = {
    '360', '480', '540', '720', '900',
    '1080', '1440', '2160'
}

RESOLUTION_KEYWORDS = {
    '360p', '480p', '540p', '720p', '900p',
    '1080p', '1440p', '2160p', '4k'
}
# -------------------------------------------------------

def clean_string(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())

def extract_season_ep(filename):
    season = ''
    episode = ''

    ordinal_words = {
        'first': 1, 'second': 2, 'third': 3, 'fourth': 4,
        'fifth': 5, 'sixth': 6, 'seventh': 7, 'eighth': 8,
        'ninth': 9, 'tenth': 10, 'eleventh': 11, 'twelfth': 12
    }

    # -------- Season detection --------
    season_match = re.search(r'(?:S|Season)[ _\-]?(\d{1,2})', filename, re.IGNORECASE)
    if not season_match:
        season_match = re.search(r'\bs(\d{1,2})\b', filename, re.IGNORECASE)

    if not season_match:
        season_match = re.search(r'(\d{1,2})(?:st|nd|rd|th)[ _\-]?Season', filename, re.IGNORECASE)

    if not season_match:
        word_match = re.search(
            r'\b(' + '|'.join(ordinal_words.keys()) + r')[ _\-]?Season',
            filename,
            re.IGNORECASE
        )
        if word_match:
            season = ordinal_words[word_match.group(1).lower()]

    if season_match and not season:
        season = season_match.group(1)

    # -------- Episode detection (IMPROVED) --------
    episode_matches = re.findall(
        r'(?:S\d+)?E(\d{1,3})'
        r'|(?:Ep|Episode)[ _\-]?(\d{1,3})'
        r'|[_\-\s\.](\d{1,3})(?=[_\-\s\.])'
        r'|(?<!\d)(\d{1,3})v\d+',
        filename,
        re.IGNORECASE
    )

    # Flatten matches
    raw_episodes = [g for match in episode_matches for g in match if g]

    # Remove resolution numbers
    episodes = []
    for ep in raw_episodes:
        ep_clean = ep.lstrip('0') or '0'
        if ep_clean not in RESOLUTION_NUMBERS:
            episodes.append(ep)

    # Decide which episode to use
    if len(episodes) >= 2:
        episode = episodes[1]   # SECOND episode
    elif len(episodes) == 1:
        episode = episodes[0]   # fallback to old behavior

    return season, episode

# ------------------ Load anime detect list ------------------
try:
    with open(anime_detect_path, 'r', encoding='utf-8') as file:
        anime_detect_list = [line.strip() for line in file if line.strip()]
except FileNotFoundError:
    print(f"❌ File not found: {anime_detect_path}")
    exit()

# ------------------ Load English name mappings ------------------
anime_english_map = {}
try:
    with open(anime_names_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if '=' in line:
                jp, en = line.split('=', 1)
                anime_english_map[clean_string(jp)] = en.strip()
except FileNotFoundError:
    print(f"❌ File not found: {anime_names_path}")
    exit()

print(f"✅ Loaded {len(anime_detect_list)} anime names for detection.")
print(f"✅ Loaded {len(anime_english_map)} English name mappings.")

video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.flv', '.webm', '.ts'}

try:
    files = os.listdir(video_folder)
except FileNotFoundError:
    print(f"❌ Folder not found: {video_folder}")
    exit()

print(f"📂 Found {len(files)} files in folder.")

found_any = False
for filename in files:
    file_path = os.path.join(video_folder, filename)
    if os.path.isfile(file_path):
        name, ext = os.path.splitext(filename)
        if ext.lower() in video_extensions:
            cleaned_filename = clean_string(name)
            for anime_jp in anime_detect_list:
                cleaned_anime = clean_string(anime_jp)
                if cleaned_anime in cleaned_filename:
                    display_name = anime_english_map.get(cleaned_anime, anime_jp)

                    season, episode = extract_season_ep(filename)

                    parts = ['[AH]', display_name, '(1080p)']

                    if season and episode:
                        parts.append(f'S{int(season)}E{int(episode)}')
                    elif episode:
                        parts.append(f'E{int(episode)}')

                    new_name = ' '.join(parts) + ext.lower()
                    new_path = os.path.join(video_folder, new_name)

                    if os.path.exists(new_path):
                        print(f"⚠️ Skipping rename, target file exists: {new_name}")
                    else:
                        print(f"🔄 Renaming:\n  From: {filename}\n  To:   {new_name}")
                        os.rename(file_path, new_path)

                    found_any = True
                    break

if not found_any:
    print("🚫 No anime videos found.")
