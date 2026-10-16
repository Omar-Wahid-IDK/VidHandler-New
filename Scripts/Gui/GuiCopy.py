import customtkinter as ctk
import subprocess
import threading
import os
from pathlib import Path
import sys
import re

if getattr(sys, 'frozen', False):
    base_dir = Path(sys.executable).resolve().parent
else:
    base_dir = Path(__file__).resolve().parent.parent.parent

# Point directly to your embedded portable Python runtime
python_executable = base_dir / "Runtime" / "python.exe"

txt_dir = base_dir / "Txt Files"
YoutubeLinks = txt_dir / "youtube_links.txt"
AnimeDetect = txt_dir / "anime_detect.txt"
AnimeNames = txt_dir / "anime_names.txt"
config_file = txt_dir / "GUI_Config.txt"

scripts_dir = base_dir / "Scripts"
LinkCopier = scripts_dir / "LinkCopier" / "LinkCopier.py"
YoutubeDownloader = scripts_dir / "YoutubeDownloader" / "YoutubeDownloader.py"
VidHandler = scripts_dir / "VidHandler" / "VidHandler.py"

def parse_to_bytes(s):
    m = re.search(r'([\d.]+)([KkMmGgTt]?i?B)?', s)
    if not m: return 0.0
    val = float(m.group(1))
    unit = (m.group(2) or '').upper()
    mult = 1
    if 'K' in unit: mult = 1024
    elif 'M' in unit: mult = 1024 * 1024
    elif 'G' in unit: mult = 1024 * 1024 * 1024
    elif 'T' in unit: mult = 1024 * 1024 * 1024 * 1024
    return val * mult

def format_size(bytes_val):
    if bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f}KB"
    else:
        return f"{bytes_val / (1024 * 1024):.1f}MB"

def format_speed(bytes_per_sec):
    if bytes_per_sec < 1024 * 1024:
        return f"{bytes_per_sec / 1024:.1f}KB/s"
    else:
        return f"{bytes_per_sec / (1024 * 1024):.1f}MB/s"

class TerminalGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VidHandler Control Panel")
        self.geometry("1100x700")
        
        self.pages = {
            "Page 1": {
                "left": YoutubeLinks,
                "right": "terminal"
            },
            "Page 2": {
                "left": AnimeDetect,
                "right": AnimeNames
            }
        }
        
        self.current_page = "Page 1"
        self.last_mtimes = {"left": 0, "right": 0}
        self.is_progress_line_active = False

        # Load saved defaults or set fallbacks
        saved_mode = "Videos"
        saved_quality = "360p"
        saved_keep_folders = "True"
        saved_playlist = "False"

        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("MODE="):
                            saved_mode = line.strip().split("=")[1]
                        elif line.startswith("QUALITY="):
                            saved_quality = line.strip().split("=")[1]
                        elif line.startswith("KEEP_FOLDERS="):
                            saved_keep_folders = line.strip().split("=")[1]
                        elif line.startswith("PLAYLIST="):
                            saved_playlist = line.strip().split("=")[1]
            except Exception:
                pass

        # State Variables
        self.download_mode = saved_mode
        self.keep_folders_state = saved_keep_folders
        self.playlist_state = saved_playlist
        self.quality_var = ctk.StringVar(value=saved_quality)

        self.grid_columnconfigure(0, weight=1) 
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # --- LEFT COLUMN ---
        self.left_frame = ctk.CTkFrame(self)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        self.editor_left = ctk.CTkTextbox(self.left_frame)
        self.editor_left.pack(pady=10, padx=10, fill="both", expand=True)
        self.editor_left.bind("<KeyRelease>", lambda e: self.save_content(self.editor_left, self.pages[self.current_page]["left"], "left"))

        # Left Controls Frame (Page Selection Dropdown)
        self.left_controls_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.left_controls_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.page_var = ctk.StringVar(value="Page 1")
        self.page_dropdown = ctk.CTkComboBox(
            self.left_controls_frame,
            values=list(self.pages.keys()),
            variable=self.page_var,
            command=self.switch_page,
            state="readonly"
        )
        self.page_dropdown.pack(side="left", padx=0, expand=True, fill="x")

        # --- RIGHT COLUMN ---
        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.content_container = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.content_container.pack(side="top", fill="both", expand=True)

        self.bottom_container = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.bottom_container.pack(side="bottom", fill="x", pady=5, padx=10)

        # 1. The Terminal
        self.terminal = ctk.CTkTextbox(self.content_container)
        self.terminal.configure(state="disabled")

        # 2. The Right Editor
        self.editor_right = ctk.CTkTextbox(self.content_container)
        self.editor_right.bind("<KeyRelease>", lambda e: self.save_content(self.editor_right, self.pages[self.current_page]["right"], "right"))

        # --- BOTTOM CONTROL PANEL ---
        ACTIVE_COLOR = "#1f6aa5"
        DEFAULT_COLOR = "transparent"
        BORDER_COLOR = "gray50"

        # Row 1: Link Copier + Clear Links Button
        self.row1_frame = ctk.CTkFrame(self.bottom_container, fg_color="transparent")
        self.row1_frame.pack(fill="x", pady=2)
        
        ctk.CTkButton(
            self.row1_frame, text="Link Copier", 
            command=lambda: self.start_script_thread(LinkCopier)
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))

        ctk.CTkButton(
            self.row1_frame, text="Clear Links", width=110,
            command=self.clear_youtube_links
        ).pack(side="left", padx=0)

        # Row 2: Youtube Downloader + Playlist Toggles + Mode Toggles + Quality Dropdown
        self.row2_frame = ctk.CTkFrame(self.bottom_container, fg_color="transparent")
        self.row2_frame.pack(fill="x", pady=2)
        
        ctk.CTkButton(
            self.row2_frame, text="Youtube Downloader", 
            command=lambda: self.start_script_thread(YoutubeDownloader)
        ).pack(side="left", padx=(0, 5))

        ctk.CTkLabel(self.row2_frame, text="Playlist:").pack(side="left", padx=(5, 2))

        self.btn_playlist_true = ctk.CTkButton(
            self.row2_frame, text="True", width=55, 
            fg_color=ACTIVE_COLOR if self.playlist_state == "True" else DEFAULT_COLOR,
            border_color=ACTIVE_COLOR if self.playlist_state == "True" else BORDER_COLOR,
            border_width=2,
            command=lambda: self.set_playlist("True")
        )
        self.btn_playlist_true.pack(side="left", padx=2)

        self.btn_playlist_false = ctk.CTkButton(
            self.row2_frame, text="False", width=55, 
            fg_color=ACTIVE_COLOR if self.playlist_state == "False" else DEFAULT_COLOR,
            border_color=ACTIVE_COLOR if self.playlist_state == "False" else BORDER_COLOR,
            border_width=2,
            command=lambda: self.set_playlist("False")
        )
        self.btn_playlist_false.pack(side="left", padx=2)

        ctk.CTkLabel(self.row2_frame, text="Mode:").pack(side="left", padx=(10, 2))
        
        self.btn_videos = ctk.CTkButton(
            self.row2_frame, text="Videos", width=65, 
            fg_color=ACTIVE_COLOR if self.download_mode == "Videos" else DEFAULT_COLOR,
            border_color=ACTIVE_COLOR if self.download_mode == "Videos" else BORDER_COLOR,
            border_width=2,
            command=lambda: self.set_download_mode("Videos")
        )
        self.btn_videos.pack(side="left", padx=2)

        self.btn_music = ctk.CTkButton(
            self.row2_frame, text="Music", width=65, 
            fg_color=ACTIVE_COLOR if self.download_mode == "Music" else DEFAULT_COLOR,
            border_color=ACTIVE_COLOR if self.download_mode == "Music" else BORDER_COLOR,
            border_width=2,
            command=lambda: self.set_download_mode("Music")
        )
        self.btn_music.pack(side="left", padx=2)

        ctk.CTkLabel(self.row2_frame, text="Quality:").pack(side="left", padx=(10, 2))
        
        initial_quality_values = ["144p", "360p", "480p", "720p", "1080p"] if self.download_mode == "Videos" else ["128kbps", "192kbps", "256kbps", "320kbps"]
        
        self.quality_dropdown = ctk.CTkComboBox(
            self.row2_frame,
            values=initial_quality_values,
            variable=self.quality_var,
            command=lambda choice: self.save_config(),
            state="readonly",
            width=110
        )
        self.quality_dropdown.pack(side="left", padx=2)
        if saved_quality in initial_quality_values:
            self.quality_var.set(saved_quality)

        # Row 3: VidHandler + Keep Folders Toggles + Open Folder Button (Far Right)
        self.row3_frame = ctk.CTkFrame(self.bottom_container, fg_color="transparent")
        self.row3_frame.pack(fill="x", pady=2)

        ctk.CTkButton(
            self.row3_frame, text="VidHandler", 
            command=lambda: self.start_script_thread(VidHandler)
        ).pack(side="left", padx=(0, 5))

        ctk.CTkLabel(self.row3_frame, text="Keep Folders:").pack(side="left", padx=(5, 2))

        self.btn_keep_true = ctk.CTkButton(
            self.row3_frame, text="True", width=55, 
            fg_color=ACTIVE_COLOR if self.keep_folders_state == "True" else DEFAULT_COLOR,
            border_color=ACTIVE_COLOR if self.keep_folders_state == "True" else BORDER_COLOR,
            border_width=2,
            command=lambda: self.set_keep_folders("True")
        )
        self.btn_keep_true.pack(side="left", padx=2)

        self.btn_keep_false = ctk.CTkButton(
            self.row3_frame, text="False", width=55, 
            fg_color=ACTIVE_COLOR if self.keep_folders_state == "False" else DEFAULT_COLOR,
            border_color=ACTIVE_COLOR if self.keep_folders_state == "False" else BORDER_COLOR,
            border_width=2,
            command=lambda: self.set_keep_folders("False")
        )
        self.btn_keep_false.pack(side="left", padx=2)

        # # Quick Open Download Folder Button packed to the far right
        # ctk.CTkButton(
        #     self.row3_frame, text="🗂️", width=5,
        #     command=self.open_download_folder
        # ).pack(side="right", padx=0)

        # Initialize default page states
        self.switch_page("Page 1")
        self.monitor_file()

    # --- CONFIG PERSISTENCE ---
    def save_config(self):
        try:
            os.makedirs(txt_dir, exist_ok=True)
            with open(config_file, "w", encoding="utf-8") as f:
                f.write(f"MODE={self.download_mode}\n")
                f.write(f"QUALITY={self.quality_var.get()}\n")
                f.write(f"KEEP_FOLDERS={self.keep_folders_state}\n")
                f.write(f"PLAYLIST={self.playlist_state}\n")
        except Exception as e:
            print(f"Failed to save config: {e}")

    # --- UI TOGGLE HELPERS ---
    def set_download_mode(self, mode):
        ACTIVE_COLOR = "#1f6aa5"
        DEFAULT_COLOR = "transparent"
        BORDER_COLOR = "gray50"
        self.download_mode = mode
        
        if mode == "Videos":
            self.btn_videos.configure(fg_color=ACTIVE_COLOR, border_color=ACTIVE_COLOR)
            self.btn_music.configure(fg_color=DEFAULT_COLOR, border_color=BORDER_COLOR)
            self.quality_dropdown.configure(values=["144p", "360p", "480p", "720p", "1080p"])
            self.quality_var.set("360p")
        else:
            self.btn_music.configure(fg_color=ACTIVE_COLOR, border_color=ACTIVE_COLOR)
            self.btn_videos.configure(fg_color=DEFAULT_COLOR, border_color=BORDER_COLOR)
            self.quality_dropdown.configure(values=["128kbps", "192kbps", "256kbps", "320kbps"])
            self.quality_var.set("320kbps")
            
        self.save_config()

    def set_keep_folders(self, state):
        ACTIVE_COLOR = "#1f6aa5"
        DEFAULT_COLOR = "transparent"
        BORDER_COLOR = "gray50"
        self.keep_folders_state = state
        
        if state == "True":
            self.btn_keep_true.configure(fg_color=ACTIVE_COLOR, border_color=ACTIVE_COLOR)
            self.btn_keep_false.configure(fg_color=DEFAULT_COLOR, border_color=BORDER_COLOR)
        else:
            self.btn_keep_false.configure(fg_color=ACTIVE_COLOR, border_color=ACTIVE_COLOR)
            self.btn_keep_true.configure(fg_color=DEFAULT_COLOR, border_color=BORDER_COLOR)
            
        self.save_config()

    def set_playlist(self, state):
        ACTIVE_COLOR = "#1f6aa5"
        DEFAULT_COLOR = "transparent"
        BORDER_COLOR = "gray50"
        self.playlist_state = state
        
        if state == "True":
            self.btn_playlist_true.configure(fg_color=ACTIVE_COLOR, border_color=ACTIVE_COLOR)
            self.btn_playlist_false.configure(fg_color=DEFAULT_COLOR, border_color=BORDER_COLOR)
        else:
            self.btn_playlist_false.configure(fg_color=ACTIVE_COLOR, border_color=ACTIVE_COLOR)
            self.btn_playlist_true.configure(fg_color=DEFAULT_COLOR, border_color=BORDER_COLOR)
            
        self.save_config()

    def clear_youtube_links(self):
        try:
            if os.path.exists(YoutubeLinks):
                with open(YoutubeLinks, "w", encoding="utf-8") as f:
                    f.write("")
            if self.current_page == "Page 1":
                self.editor_left.delete("1.0", "end")
                self.last_mtimes["left"] = os.path.getmtime(YoutubeLinks) if os.path.exists(YoutubeLinks) else 0
        except Exception as e:
            print(f"Failed to clear links: {e}")

    def open_download_folder(self):
        download_folder = Path.home() / "Downloads" / "Video"
        if not download_folder.exists():
            os.makedirs(download_folder, exist_ok=True)
        try:
            os.startfile(str(download_folder))
        except Exception as e:
            print(f"Failed to open folder: {e}")

    # --- LOGIC ---
    def monitor_file(self):
        """Checks every 1000ms if the files on disk have changed."""
        path_left = self.pages[self.current_page]["left"]
        if os.path.exists(path_left):
            mtime = os.path.getmtime(path_left)
            if mtime > self.last_mtimes["left"]:
                if self.focus_get() != self.editor_left:
                    self.load_single_file(self.editor_left, path_left, "left")
                else:
                    self.last_mtimes["left"] = mtime

        path_right = self.pages[self.current_page]["right"]
        if path_right != "terminal" and os.path.exists(path_right):
            mtime = os.path.getmtime(path_right)
            if mtime > self.last_mtimes["right"]:
                if self.focus_get() != self.editor_right:
                    self.load_single_file(self.editor_right, path_right, "right")
                else:
                    self.last_mtimes["right"] = mtime
                
        self.after(1000, self.monitor_file)

    def switch_page(self, page_name):
        self.current_page = page_name
        if hasattr(self, 'page_var') and self.page_var.get() != page_name:
            self.page_var.set(page_name)

        self.terminal.pack_forget()
        self.editor_right.pack_forget()
        
        right_mode = self.pages[page_name]["right"]
        if right_mode == "terminal":
            self.terminal.pack(in_=self.content_container, pady=10, padx=10, fill="both", expand=True)
        else:
            self.editor_right.pack(in_=self.content_container, pady=10, padx=10, fill="both", expand=True)
            
        self.load_single_file(self.editor_left, self.pages[self.current_page]["left"], "left")
        if right_mode != "terminal":
            self.load_single_file(self.editor_right, right_mode, "right")

    def load_single_file(self, widget, path, key):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                widget.delete("1.0", "end")
                widget.insert("1.0", f.read())
            self.last_mtimes[key] = os.path.getmtime(path)

    def save_content(self, widget, path, key):
        if path != "terminal":
            with open(path, "w", encoding="utf-8") as f:
                f.write(widget.get("1.0", "end-1c"))
            self.last_mtimes[key] = os.path.getmtime(path)

    def append_or_update_progress(self, text, is_progress=False):
        self.terminal.configure(state="normal")
        if is_progress:
            if self.is_progress_line_active:
                self.terminal.delete("end-2l", "end-1c")
            self.terminal.insert("end", text + "\n")
            self.is_progress_line_active = True
        else:
            self.terminal.insert("end", text)
            self.is_progress_line_active = False
        self.terminal.see("end")
        self.terminal.configure(state="disabled")

    def start_script_thread(self, script_path):
        if self.pages[self.current_page]["right"] != "terminal":
            self.switch_page("Page 1")
            
        self.save_content(self.editor_left, self.pages[self.current_page]["left"], "left")
        
        self.terminal.configure(state="normal")
        self.terminal.delete("1.0", "end")
        self.terminal.configure(state="disabled")
        self.is_progress_line_active = False
        
        extra_args = []
        if script_path == YoutubeDownloader:
            extra_args = [self.download_mode, self.quality_var.get(), self.playlist_state]
        elif script_path == VidHandler:
            extra_args = [self.keep_folders_state]
            
        threading.Thread(target=self.run_script, args=(script_path, extra_args), daemon=True).start()

    def run_script(self, script_path, extra_args=[]):
        my_env = os.environ.copy()
        my_env["FORCE_TERMINAL"] = "1"
        my_env["FORCE_COLOR"] = "1"
        my_env["PYTHONUNBUFFERED"] = "1"
        
        startup_flags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
        
        try:
            cmd = [str(python_executable), str(script_path)] + extra_args
            process = subprocess.Popen(
                cmd,  
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True, 
                bufsize=1,
                env=my_env,
                creationflags=startup_flags
            )
            
            stream_type = "Video"
            download_count = 0

            for line in process.stdout:
                clean_line = line.replace('\r', '').strip()
                if not clean_line:
                    continue
                
                if clean_line.startswith("Downloading:"):
                    download_count = 0
                    stream_type = "Video"
                    self.after(0, lambda l=clean_line: self.append_or_update_progress(l + "\n", is_progress=False))
                    continue

                if any(tag in clean_line for tag in ["[youtube]", "[info]", "[debug]"]):
                    continue

                if "has already been downloaded" in clean_line:
                    match = re.search(r'\[download\]\s+(.*?)\s+has already been downloaded', clean_line)
                    if match:
                        file_path = match.group(1).strip()
                        file_name = os.path.basename(file_path)
                        friendly_msg = f"[ {file_name} ] Is already downloaded\n"
                        self.after(0, lambda m=friendly_msg: self.append_or_update_progress(m, is_progress=False))
                    continue

                if "[download] Destination:" in clean_line:
                    if self.is_progress_line_active:
                        self.is_progress_line_active = False
                    
                    download_count += 1
                    stream_type = "Audio" if download_count >= 2 else "Video"
                    continue

                if "[Merger]" in clean_line:
                    self.after(0, lambda: self.append_or_update_progress("Merging video and audio streams into final MP4...\n", is_progress=False))
                    continue

                if "Deleting original file" in clean_line:
                    continue

                if "[download]" in clean_line:
                    if "%" in clean_line and "of" in clean_line and "ETA" in clean_line:
                        match = re.search(r'([\d.]+)%\s+of\s+([^\s]+)\s+at\s+([^\s]+)\s+ETA\s+([^\s]+)', clean_line)
                        if match:
                            pct_str, total_str, speed_str, eta_str = match.groups()
                            try:
                                pct = float(pct_str)
                                total_bytes = parse_to_bytes(total_str)
                                downloaded_bytes = total_bytes * (pct / 100.0)
                                downloaded_str = format_size(downloaded_bytes)
                                total_sz_str = format_size(total_bytes)
                                speed_bytes = parse_to_bytes(speed_str.replace('/s', ''))
                                speed_st_str = format_speed(speed_bytes)
                                
                                bar_len = 15
                                filled = int(pct / 100 * bar_len)
                                bar = f"Downloading {stream_type} [ {'|' * filled}{' ' * (bar_len - filled)} ] {pct:.1f}% | {downloaded_str}/{total_sz_str} | {speed_st_str} | ETA {eta_str}"
                                
                                self.after(0, lambda b=bar: self.append_or_update_progress(b, is_progress=True))
                                continue
                            except Exception:
                                pass
                    continue
                
                self.after(0, lambda l=clean_line: self.append_or_update_progress(l + "\n", is_progress=False))
                
            process.wait()
            self.after(0, lambda: self.append_or_update_progress("\n[Process Finished]\n", is_progress=False))
            
        except Exception as e:
            self.after(0, lambda: self.append_or_update_progress(f"\nError: {str(e)}\n", is_progress=False))

if __name__ == "__main__":
    app = TerminalGUI()
    app.mainloop()