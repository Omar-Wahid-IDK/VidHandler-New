import subprocess
import os
from pathlib import Path
import sys
import re
import urllib.request
import json

base_dir = Path(__file__).resolve().parent.parent.parent
txt_dir = base_dir / "Txt Files"
paths_file = txt_dir / "Paths.txt"
yt_dlp_executable = str(base_dir / "Runtime" / "Scripts" / "yt-dlp.exe")
python_executable = str(base_dir / "Runtime" / "python.exe")

# Accept action argument from GUI: "check", "stable", or "nightly"
action = sys.argv[1] if len(sys.argv) > 1 else "check"

print("=" * 60)
print("VIDHANDLER SYSTEM, PATHS & YT-DLP DIAGNOSTIC TOOL")
print("=" * 60)

if not Path(yt_dlp_executable).exists():
    print(f"CRITICAL: yt-dlp not found at {yt_dlp_executable}")
    sys.exit(1)

# Handle updates using pip via your embedded python runtime
if action == "stable":
    print("Updating yt-dlp to the latest official release via pip...")
    result = subprocess.run(
        [python_executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    print(result.stdout)
    print("[Update Complete]")
    sys.exit(0)
elif action == "nightly":
    print("Updating yt-dlp to the latest nightly build via pip (--pre)...")
    result = subprocess.run(
        [python_executable, "-m", "pip", "install", "--upgrade", "--pre", "yt-dlp"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    print(result.stdout)
    print("[Update Complete]")
    sys.exit(0)

# 1. Check local version vs GitHub latest release tag
local_version = "Unknown"
try:
    res = subprocess.run(
        [yt_dlp_executable, "--version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    local_version = res.stdout.strip()
    print(f"Current installed yt-dlp version: {local_version}")
except Exception as e:
    print(f"Could not check local version: {e}")

latest_version = None
try:
    url = "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=4) as response:
        data = json.loads(response.read().decode())
        latest_version = data.get("tag_name")
        print(f"Latest official GitHub version: {latest_version}")
except Exception:
    print("[!] Unable to check online for updates (No internet connection or API limit).")

if latest_version and local_version != "Unknown":
    if local_version < latest_version:
        print(f"[UPDATE_AVAILABLE] A newer version of yt-dlp is available ({latest_version})!")
    else:
        print("yt-dlp version is up to date.")

print("-" * 60)

# 2. Check Folders/Paths in Paths.txt (Strictly checking only the first 2 lines)
if paths_file.exists():
    with open(paths_file, "r", encoding="utf-8") as f:
        path_lines = [line.strip() for line in f if line.strip()][:2]
    
    print(f"Scanning '{paths_file.name}' (Checking first {len(path_lines)} path entries)...")
    valid_paths = 0
    invalid_paths = 0
    
    for idx, p_str in enumerate(path_lines, 1):
        p = Path(p_str)
        if p.exists() and p.is_dir():
            valid_paths += 1
            print(f"  [Valid Folder] Path {idx}: {p_str}")
        else:
            invalid_paths += 1
            print(f"  [INVALID / NON-EXISTENT] Path {idx}: {p_str}")
            
    print(f"Path Health Check: {valid_paths} valid folders, {invalid_paths} invalid/fake paths found.")
else:
    print(f"[WARNING] '{paths_file.name}' not found in Txt Files folder.")

print("=" * 60)
print("[Diagnostic Completed]")