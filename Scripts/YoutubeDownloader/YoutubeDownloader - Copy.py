import subprocess
import os
from pathlib import Path
import sys
print("Python being used:", sys.executable)

# Base directory setup (adjusts if frozen or running as script)
base_dir = Path(__file__).resolve().parent.parent.parent

txt_dir = base_dir / "Txt Files"
download_folder = str(Path.home() / "Downloads" / "Video")
txt_file = txt_dir / "youtube_links.txt"

# Point directly to your embedded tools inside the Runtime/NodeRuntime folders
yt_dlp_executable = str(base_dir / "Runtime" / "Scripts" / "yt-dlp.exe")
node_executable = str(base_dir / "NodeRuntime" / "node.exe")

video_item = 0
os.makedirs(download_folder, exist_ok=True)

if not txt_file.exists():
    print(f"Error: {txt_file} not found.")
    exit()

with open(txt_file, "r", encoding="utf-8") as file:
    urls = [line.strip() for line in file if line.strip()]

if len(urls) > 1:
    print(f"{len(urls)} Videos Found")
elif len(urls) == 1:
    print(f"{len(urls)} Video Found")
else:
    print("No Videos Found")

for url in urls:
    print(f"Downloading: {url}")
    video_item += 1
    
    # Using explicit paths ensures it works on a system without Python or Node installed globally!
    subprocess.run([
        yt_dlp_executable,
        "--js-runtimes",
        f"node:{node_executable}",  # Points yt-dlp straight to your bundled node.exe
        "--remote-components",
        "ejs:github",
        "-f",
        "bv*[height<=360][ext=mp4]+ba[ext=m4a]/bv*[height<=360]+ba/b[height<=360]",
        "--merge-output-format",
        "mp4",
        "-P",
        download_folder,
        "-o",
        "%(title)s.%(ext)s",
        url,
        "--no-playlist"
    ])
    
    remaining = len(urls) - video_item
    if remaining > 1:
        print(f"{remaining} Videos Remaining")
    elif remaining == 1:
        print(f"{remaining} Video Remaining")
    else:
        print("Done")

if not Path(yt_dlp_executable).exists():
    print(f"CRITICAL: yt-dlp not found at {yt_dlp_executable}")
if not Path(node_executable).exists():
    print(f"CRITICAL: node not found at {node_executable}")