import subprocess
import os
import json
from pathlib import Path
import sys
import concurrent.futures

base_dir = Path(__file__).resolve().parent.parent.parent
txt_dir = base_dir / "Txt Files"
txt_file = txt_dir / "youtube_links.txt"
yt_dlp_executable = str(base_dir / "Runtime" / "Scripts" / "yt-dlp.exe")
node_executable = str(base_dir / "NodeRuntime" / "node.exe")

if not Path(yt_dlp_executable).exists():
    print(f"CRITICAL: yt-dlp not found at {yt_dlp_executable}")
    sys.exit(1)
if not Path(node_executable).exists():
    print(f"CRITICAL: node not found at {node_executable}")
    sys.exit(1)

if not txt_file.exists():
    print(f"Error: {txt_file} not found.")
    sys.exit(1)

with open(txt_file, "r", encoding="utf-8") as file:
    urls = [line.strip() for line in file if line.strip()]

if not urls:
    print("No Links Found to check sizes.")
    sys.exit(0)

qualities = [144, 360, 480, 720, 1080]
print(f"Checking exact download sizes for {len(urls)} link(s) across {len(qualities)} qualities using parallel workers...")
print("-" * 60)

totals = {q: 0 for q in qualities}
unknown_sizes = {q: False for q in qualities}

def format_bytes(b):
    if b == 0:
        return "Unknown / N/A"
    if b < 1024 * 1024:
        return f"{b / 1024:.1f} KB"
    elif b < 1024 * 1024 * 1024:
        return f"{b / (1024 * 1024):.1f} MB"
    else:
        return f"{b / (1024 * 1024 * 1024):.2f} GB"

def inspect_single_stream(task_info):
    url_idx, url, q = task_info
    format_string = (
        f"bv*[height={q}]+ba/"
        f"bv*[height<={q}]+ba/"
        f"bv*[height>={q}]+ba/"
        f"b"
    )
    cmd = [
        yt_dlp_executable,
        "--js-runtimes", f"node:{node_executable}",
        "--remote-components", "ejs:github",
        "--no-playlist",
        "-f", format_string,
        "--dump-json",
        "--skip-download",
        url
    ]
    
    startup_flags = subprocess.CREATE_NO_WINDOW
    try:
        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            encoding="utf-8", 
            creationflags=startup_flags
        )
        if result.returncode != 0:
            return (q, 0, False)
        
        data = json.loads(result.stdout)
        req_formats = data.get("requested_formats")
        size = 0
        if req_formats:
            for rf in req_formats:
                sz = rf.get("filesize") or rf.get("filesize_approx") or 0
                size += sz
        else:
            size = data.get("filesize") or data.get("filesize_approx") or 0
        
        return (q, size, size > 0)
    except Exception:
        return (q, 0, False)

# Build all tasks (every URL combined with every quality)
tasks = []
for i, url in enumerate(urls, 1):
    for q in qualities:
        tasks.append((i, url, q))

total_tasks = len(tasks)
completed_count = 0

# Run inspections in parallel using a ThreadPoolExecutor (8 concurrent workers)
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    futures = {executor.submit(inspect_single_stream, task): task for task in tasks}
    
    for future in concurrent.futures.as_completed(futures):
        completed_count += 1
        q, size, success = future.result()
        
        if success:
            totals[q] += size
        else:
            unknown_sizes[q] = True
            
        print(f"[{completed_count}/{total_tasks}] Processed stream checks...", end="\r", flush=True)

print("\n" + "=" * 60)
print("TOTAL ESTIMATED DOWNLOAD SIZES:")
print("=" * 60)
for q in qualities:
    size_str = format_bytes(totals[q])
    if unknown_sizes[q] and totals[q] == 0:
        size_str = "Not Available / Unsupported"
    elif unknown_sizes[q]:
        size_str += " (some streams missing size info)"
    print(f"  {q}p : {size_str}")
print("=" * 60)
print("[Size Check Finished]")