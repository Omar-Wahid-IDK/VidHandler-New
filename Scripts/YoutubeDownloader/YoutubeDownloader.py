import subprocess
import os
from pathlib import Path
import sys

base_dir = Path(__file__).resolve().parent.parent.parent
txt_dir = base_dir / "Txt Files"
download_folder = str(Path.home() / "Downloads" / "Video")
txt_file = txt_dir / "youtube_links.txt"
yt_dlp_executable = str(base_dir / "Runtime" / "Scripts" / "yt-dlp.exe")
node_executable = str(base_dir / "NodeRuntime" / "node.exe")
video_index = 0

# --- RECEIVE ARGUMENTS FROM GUI ---
selected_mode = sys.argv[1] if len(sys.argv) > 1 else "Videos"
Music_Only = (selected_mode == "Music")

selected_quality = sys.argv[2] if len(sys.argv) > 2 else ("360p" if not Music_Only else "320kbps")

# Receive playlist state from GUI (True/False)
playlist_arg = sys.argv[3] if len(sys.argv) > 3 else "False"
Allow_Playlist = (playlist_arg == "True")

# Verify tools exist upfront
if not Path(yt_dlp_executable).exists():
    print(f"CRITICAL: yt-dlp not found at {yt_dlp_executable}")
    sys.exit(1)
if not Path(node_executable).exists():
    print(f"CRITICAL: node not found at {node_executable}")
    sys.exit(1)

# Configure parameters based on the active mode and selected quality/bitrate
if Music_Only:
    format_string = "ba"
    bitrate_val = selected_quality.replace("kbps", "k")
    mode_label = f"Format: MP3 Audio ({selected_quality})"
else:
    height_val = selected_quality.replace("p", "")
    format_string = (
        f"bv*[height={height_val}]+ba/"
        f"bv*[height<={height_val}]+ba/"
        f"bv*[height>={height_val}]+ba/"
        f"b"
    )
    mode_label = f"Download Quality: {selected_quality}"

if not txt_file.exists():
    print(f"Error: {txt_file} not found.")
    sys.exit(1)

with open(txt_file, "r", encoding="utf-8") as file:
    urls = [line.strip() for line in file if line.strip()]

item_noun = "Tracks Found" if Music_Only else "Videos Found"
item_singular = "Track Found" if Music_Only else "Video Found"

if len(urls) > 1:
    print(f"{len(urls)} {item_noun} | {mode_label}")
    print("-"*60)
elif len(urls) == 1:
    print(f"{len(urls)} {item_singular} | {mode_label}")
    print("-"*60)
else:
    print("No Links Found")

for url in urls:
    print(f"Downloading: {url}")
    video_index += 1
    
    # Base arguments shared by both modes
    cmd_args = [
        yt_dlp_executable,
        "--js-runtimes",
        f"node:{node_executable}",
        "--remote-components",
        "ejs:github",
        "-f",
        format_string,
        "-P",
        download_folder,
        "-o",
        "%(title)s.%(ext)s",
        url
    ]

    # Dynamically apply --no-playlist based on GUI toggle
    if not Allow_Playlist:
        cmd_args.append("--no-playlist")

    # Append mode-specific arguments dynamically
    if Music_Only:
        cmd_args.extend(["-x", "--audio-format", "mp3", "--audio-quality", bitrate_val, "--embed-thumbnail", "--embed-metadata"])
    else:
        cmd_args.extend(["--merge-output-format", "mp4", "--embed-thumbnail", "--embed-metadata"])

    subprocess.run(cmd_args)

    if video_index > 0:
        print(f"{'-'*82}[{video_index}/{len(urls)}]{'-'*82}")