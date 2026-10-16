import re
import requests
import html
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

# 📂 Universal File Paths
base_dir = Path(__file__).resolve().parent.parent.parent.parent  # From Scripts → VidHandler
txt_dir = base_dir / "Txt Files"

VIDEO_LINKS_FILE = txt_dir / "youtube_links.txt"
CHANNELS_FILE = txt_dir / "youtube_channels.txt"
CHANNEL_LINKS_FILE = txt_dir / "channel_links.txt"

# 🔹 Function to get video title, channel name, and channel handle
def get_video_details(youtube_url):
    try:
        response = requests.get(youtube_url, timeout=10)
        if response.status_code != 200:
            print(f"❌ Error fetching: {youtube_url} (status {response.status_code})")
            return None, None, None, None

        html_text = response.text

        # ✅ Extract and decode video title
        title_match = re.search(r'<title>(.*?)</title>', html_text)
        title = html.unescape(title_match.group(1)).replace(" - YouTube", "").strip() if title_match else None

        # ✅ Extract channel name
        channel_match = re.search(r'ownerChannelName":"(.*?)"', html_text)
        channel_name = html.unescape(channel_match.group(1)).strip() if channel_match else None

        # ✅ Extract channel handle (e.g., "@SomeChannel")
        handle_match = re.search(r'"canonicalBaseUrl":"\/@(.*?)"', html_text)
        channel_handle = handle_match.group(1).strip() if handle_match else None

        return youtube_url, title, channel_name, channel_handle

    except Exception as e:
        print(f"❌ Exception on {youtube_url}: {e}")
        return None, None, None, None

# 🔹 Function to process all video links
def process_video_links():
    if not VIDEO_LINKS_FILE.exists():
        print(f"❌ ERROR: {VIDEO_LINKS_FILE} not found!")
        return

    with VIDEO_LINKS_FILE.open("r", encoding="utf-8") as f:
        video_links = [line.strip() for line in f if line.strip()]

    if not video_links:
        print("⚠ No video links found.")
        return

    # Load existing entries to avoid duplicates
    existing_channels = set()
    existing_handles = set()

    if CHANNELS_FILE.exists():
        with CHANNELS_FILE.open("r", encoding="utf-8") as f:
            existing_channels = set(line.strip() for line in f if line.strip())

    if CHANNEL_LINKS_FILE.exists():
        with CHANNEL_LINKS_FILE.open("r", encoding="utf-8") as f:
            existing_handles = set(line.strip() for line in f if line.strip())

    with CHANNELS_FILE.open("a", encoding="utf-8") as f_channels, \
         CHANNEL_LINKS_FILE.open("a", encoding="utf-8") as f_handles:

        with ProcessPoolExecutor() as executor:
            results = executor.map(get_video_details, video_links)

            for link, (url, title, channel_name, channel_handle) in zip(video_links, results):
                if title and channel_name:
                    invalid_chars = r'[<>:"/\\|?*]'
                    if re.search(invalid_chars, title):
                        # Title contains invalid characters — save both versions
                        title_dash = re.sub(invalid_chars, "-", title).strip()
                        title_underscore = re.sub(invalid_chars, "_", title).strip()

                        channel_entry_dash = f"{title_dash} | {channel_name}"
                        if channel_entry_dash not in existing_channels:
                            f_channels.write(channel_entry_dash + "\n")
                            print(f"✅ Saved (dash): {channel_entry_dash}")
                            existing_channels.add(channel_entry_dash)
                        else:
                            print(f"⏭ Skipped duplicate (dash): {channel_entry_dash}")

                        channel_entry_underscore = f"{title_underscore} | {channel_name}"
                        if channel_entry_underscore not in existing_channels:
                            f_channels.write(channel_entry_underscore + "\n")
                            print(f"✅ Saved (underscore): {channel_entry_underscore}")
                            existing_channels.add(channel_entry_underscore)
                        else:
                            print(f"⏭ Skipped duplicate (underscore): {channel_entry_underscore}")
                    else:
                        # Title is clean — save only once
                        clean_entry = f"{title} | {channel_name}"
                        if clean_entry not in existing_channels:
                            f_channels.write(clean_entry + "\n")
                            print(f"✅ Saved (clean): {clean_entry}")
                            existing_channels.add(clean_entry)
                        else:
                            print(f"⏭ Skipped duplicate (clean): {clean_entry}")

                    # Save mismatched handle (only once)
                    if channel_handle and channel_handle.lower() != channel_name.lower().replace(" ", ""):
                        handle_entry = f"{channel_name} | @{channel_handle}"
                        if handle_entry not in existing_handles:
                            f_handles.write(handle_entry + "\n")
                            print(f"🔁 Mismatch saved: {handle_entry}")
                            existing_handles.add(handle_entry)
                        else:
                            print(f"⏭ Skipped duplicate handle: {handle_entry}")
                else:
                    print(f"⚠ Skipping: {link}")

    # Clean up the input file
    VIDEO_LINKS_FILE.write_text("", encoding="utf-8")
    print("🧹 Cleaned up youtube_links.txt!")

# 🔹 Entry point
if __name__ == "__main__":
    process_video_links()
