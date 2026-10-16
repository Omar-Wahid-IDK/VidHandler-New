import pyperclip
import time
import os
import sys
import winsound
from pathlib import Path
import sys

def get_base_dir():
    if getattr(sys, 'frozen', False):
        exe_path = Path(sys.executable).resolve()
        #print(f"[DEBUG] Running as .exe from: {exe_path}")
        try:
            return exe_path.parents[2]
        except IndexError:
            print("[ERROR] Not enough parent directories. Using current directory instead.")
            return exe_path.parent
    else:
        script_path = Path(__file__).resolve()
        #print(f"[DEBUG] Running as script from: {script_path}")
        return script_path.parents[2]

def run():
    # === Clear clipboard at the start ===
    try:
        pyperclip.copy("")  # Clears the clipboard content
    except pyperclip.PyperclipException as e:
        print(f"[ERROR] Failed to clear clipboard: {e}")

    # === Setup paths ===
    base_dir = get_base_dir()
    txt_dir = base_dir / "Txt Files"
    FILE_NAME = txt_dir / "youtube_links.txt"
    #print(f"[DEBUG] Will write to: {FILE_NAME}")

    # === Create folders and file ===
    try:
        txt_dir.mkdir(parents=True, exist_ok=True)
        if not FILE_NAME.exists():
            FILE_NAME.touch()
            print(f"[INFO] Created file: {FILE_NAME}")
    except Exception as e:
        print(f"[ERROR] Failed to create folders or file: {e}")
        sys.exit(1)

    #print(f"[INFO] Saving to: {os.path.abspath(FILE_NAME)}")
    print("Script Running Go Ahead And Copy Youtube Links, Script Auto Stops After 5 Seconds Of Inactivity")
    print("------------------------------------------------------------------------------------------------")

    INACTIVITY_TIMEOUT = 5  # seconds

    def get_saved_links():
        try:
            with open(FILE_NAME, "r", encoding="utf-8") as f:
                return set(line.strip() for line in f if line.strip())
        except Exception as e:
            print(f"[ERROR] Reading saved links failed: {e}")
            return set()
    
    def save_link(link):
        link = link.strip()
        if not link:
            return

        saved_links = get_saved_links()
        if link not in saved_links:
            try:
                with open(FILE_NAME, "a", encoding="utf-8") as f:
                    f.write(link + "\n")
                print(f"[ {link} ] Ready To Process ")
                winsound.Beep(3000, 150)
            except PermissionError:
                print(f"[ERROR] Permission denied writing to {FILE_NAME}")
            except Exception as e:
                print(f"[ERROR] Unexpected error writing to file: {e}")
        else:
            print(f"[SKIPPED] {link} (already exists)")

    def is_youtube_link(text):
        return any(domain in text for domain in [
            "youtube.com/watch?v=",
            "youtu.be/",
            "youtube.com/shorts/",
            "youtube.com/playlist?"
        ])

    def get_clipboard_content():
        try:
            return pyperclip.paste().strip()
        except pyperclip.PyperclipException as e:
            print(f"[ERROR] Clipboard error: {e}")
            sys.exit(1)

    #print("[INFO] Monitoring clipboard for YouTube links...")
    try:
        last_content = ""
        last_active = time.time()

        while True:
            content = get_clipboard_content()
            
            if content != last_content and is_youtube_link(content):
                save_link(content)
                last_content = content
                last_active = time.time()

            if time.time() - last_active > INACTIVITY_TIMEOUT:
                #print("[INFO] No new links for 5 seconds. Exiting...")
                break
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n[INFO] Stopped by user.")

if __name__ == "__main__":
    run()