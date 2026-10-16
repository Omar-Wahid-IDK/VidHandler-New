import customtkinter as ctk
import subprocess
import threading
import os
from pathlib import Path
import sys
import re
from tkinter import filedialog

if getattr(sys, 'frozen', False):
    base_dir = Path(sys.executable).resolve().parent
else:
    base_dir = Path(__file__).resolve().parent.parent.parent

# Point directly to your embedded portable runtimes
python_executable = base_dir / "Runtime" / "python.exe"

txt_dir = base_dir / "Txt Files"
YoutubeLinks = txt_dir / "youtube_links.txt"
PathsFile = txt_dir / "Paths.txt"
AnimeDetect = txt_dir / "anime_detect.txt"
AnimeNames = txt_dir / "anime_names.txt"
config_file = txt_dir / "GUI_Config.txt"

scripts_dir = base_dir / "Scripts"
LinkCopier = scripts_dir / "LinkCopier" / "LinkCopier.py"
YoutubeDownloader = scripts_dir / "YoutubeDownloader" / "YoutubeDownloader.py"
CheckSizes = scripts_dir / "CheckSizes" / "CheckSizes.py"
VidHandler = scripts_dir / "VidHandler" / "VidHandler.py"
DebugScript = scripts_dir / "Debug" / "Debug.py"

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
        self.geometry("1220x700")
        
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
        self.active_process = None

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

        # --- TEXT-SIZED LEFT BUTTONS & RIGHT UTILITIES ---
        ACTIVE_COLOR = "#1f6aa5"
        DEFAULT_COLOR = "transparent"
        BORDER_COLOR = "gray50"

        # Row 1: Link Copier (Left) | CL, AF, YF (Right)
        self.row1_frame = ctk.CTkFrame(self.bottom_container, fg_color="transparent")
        self.row1_frame.pack(fill="x", pady=2)
        
        self.btn_link_copier = ctk.CTkButton(
            self.row1_frame, text="Link Copier", 
            fg_color=ACTIVE_COLOR, border_color=ACTIVE_COLOR, border_width=2,
            command=lambda: self.start_script_thread(LinkCopier)
        )
        self.btn_link_copier.pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            self.row1_frame, text="YF", width=40,
            command=lambda: self.open_custom_folder(0)
        ).pack(side="right", padx=(2, 0))

        ctk.CTkButton(
            self.row1_frame, text="AF", width=40,
            command=lambda: self.open_custom_folder(1)
        ).pack(side="right", padx=(2, 2))

        self.btn_cl = ctk.CTkButton(
            self.row1_frame, text="CL", width=40,
            command=self.clear_youtube_links
        )
        self.btn_cl.pack(side="right", padx=(0, 2))

        # Row 2: Youtube Downloader (Left) | CT, ?, VF (Right)
        self.row2_frame = ctk.CTkFrame(self.bottom_container, fg_color="transparent")
        self.row2_frame.pack(fill="x", pady=2)
        
        self.btn_youtube_downloader = ctk.CTkButton(
            self.row2_frame, text="Youtube Downloader", 
            fg_color=ACTIVE_COLOR, border_color=ACTIVE_COLOR, border_width=2,
            command=lambda: self.start_script_thread(YoutubeDownloader)
        )
        self.btn_youtube_downloader.pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            self.row2_frame, text="VF", width=40,
            command=self.open_download_folder
        ).pack(side="right", padx=(2, 0))

        self.btn_debug = ctk.CTkButton(
            self.row2_frame, text="?", width=40,
            fg_color=ACTIVE_COLOR, border_color=ACTIVE_COLOR, border_width=2, text_color="white",
            command=lambda: self.start_script_thread(DebugScript, extra_args=["check"])
        )
        self.btn_debug.pack(side="right", padx=(2, 2))

        self.btn_ct = ctk.CTkButton(
            self.row2_frame, text="CT", width=40,
            fg_color="#a51f1f", hover_color="#841818", border_color="#a51f1f", border_width=2, text_color="white",
            command=self.terminate_script
        )
        self.btn_ct.pack(side="right", padx=(0, 2))

        # Row 3: VidHandler (Left) | CS, 🛠️, Future Button (Right)
        self.row3_frame = ctk.CTkFrame(self.bottom_container, fg_color="transparent")
        self.row3_frame.pack(fill="x", pady=2)

        self.btn_vid_handler = ctk.CTkButton(
            self.row3_frame, text="VidHandler", 
            fg_color=ACTIVE_COLOR, border_color=ACTIVE_COLOR, border_width=2,
            command=lambda: self.start_script_thread(VidHandler)
        )
        self.btn_vid_handler.pack(side="left", padx=(0, 5))

        self.btn_future = ctk.CTkButton(
            self.row3_frame, text="Future", width=65,
            state="disabled", fg_color="transparent", border_color=BORDER_COLOR, border_width=2, text_color="gray70"
        )
        self.btn_future.pack(side="right", padx=(2, 0))

        self.btn_settings = ctk.CTkButton(
            self.row3_frame, text="🛠️", width=40,
            fg_color="#333333", hover_color="#444444",
            border_color=BORDER_COLOR, border_width=2, text_color="white",
            command=self.show_settings_window
        )
        self.btn_settings.pack(side="right", padx=(2, 2))

        cs_active = (self.download_mode == "Videos")
        self.btn_cs = ctk.CTkButton(
            self.row3_frame, text="CS", width=40,
            fg_color=ACTIVE_COLOR if cs_active else DEFAULT_COLOR,
            border_color=ACTIVE_COLOR if cs_active else BORDER_COLOR,
            border_width=2,
            text_color="white" if cs_active else "gray70",
            command=self.on_cs_click
        )
        self.btn_cs.pack(side="right", padx=(0, 2))

        # Initialize default page states
        self.switch_page("Page 1")
        self.monitor_file()

    # --- SCRIPT TERMINATION (CT) ---
    def terminate_script(self):
        """Immediately terminates any currently running background script process."""
        if self.active_process and self.active_process.poll() is None:
            try:
                self.active_process.terminate()
                self.append_or_update_progress("\n[Process Terminated by User (CT)]\n", is_progress=False)
            except Exception as e:
                print(f"Failed to terminate process: {e}")
        self.active_process = None
        self.set_script_buttons_state(True)

    # --- PATHS.TXT HELPERS ---
    def get_path_from_file(self, index, default=""):
        if PathsFile.exists():
            try:
                with open(PathsFile, "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f if line.strip()]
                    if len(lines) > index:
                        return lines[index]
            except Exception:
                pass
        return default

    def set_path_in_file(self, index, new_path):
        try:
            os.makedirs(txt_dir, exist_ok=True)
            lines = []
            if PathsFile.exists():
                with open(PathsFile, "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f]
            while len(lines) <= index:
                lines.append("")
            lines[index] = new_path
            with open(PathsFile, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
        except Exception as e:
            print(f"Failed to save path: {e}")

    def open_custom_folder(self, index):
        path_str = self.get_path_from_file(index)
        if path_str and Path(path_str).exists() and Path(path_str).is_dir():
            try:
                os.startfile(path_str)
            except Exception as e:
                print(f"Failed to open folder: {e}")
        else:
            target = Path(path_str) if path_str else Path.home() / "Downloads"
            if not target.exists():
                try:
                    os.makedirs(target, exist_ok=True)
                except Exception:
                    pass
            try:
                os.startfile(str(target))
            except Exception as e:
                print(f"Failed to open folder: {e}")

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
    def set_script_buttons_state(self, enabled):
        ACTIVE_COLOR = "#1f6aa5"
        DEFAULT_COLOR = "transparent"
        BORDER_COLOR = "gray50"
        
        if enabled:
            self.btn_link_copier.configure(
                state="normal", fg_color=ACTIVE_COLOR, border_color=ACTIVE_COLOR, border_width=2, text_color="white"
            )
            self.btn_debug.configure(
                state="normal", fg_color=ACTIVE_COLOR, border_color=ACTIVE_COLOR, border_width=2, text_color="white"
            )
            self.btn_settings.configure(
                state="normal", fg_color="#333333", border_color=BORDER_COLOR, border_width=2, text_color="white"
            )
            self.btn_youtube_downloader.configure(
                state="normal", fg_color=ACTIVE_COLOR, border_color=ACTIVE_COLOR, border_width=2, text_color="white"
            )
            self.btn_vid_handler.configure(
                state="normal", fg_color=ACTIVE_COLOR, border_color=ACTIVE_COLOR, border_width=2, text_color="white"
            )
            
            cs_active = (self.download_mode == "Videos")
            self.btn_cs.configure(
                state="normal",
                fg_color=ACTIVE_COLOR if cs_active else DEFAULT_COLOR,
                border_color=ACTIVE_COLOR if cs_active else BORDER_COLOR,
                border_width=2,
                text_color="white" if cs_active else "gray70"
            )
        else:
            for btn in [self.btn_link_copier, self.btn_debug, self.btn_settings, self.btn_youtube_downloader, self.btn_vid_handler, self.btn_cs]:
                btn.configure(
                    state="disabled",
                    fg_color=DEFAULT_COLOR,
                    border_color=BORDER_COLOR,
                    border_width=2,
                    text_color="gray70"
                )

    def set_download_mode(self, mode):
        self.download_mode = mode
        cs_active = (mode == "Videos")
        if hasattr(self, 'btn_cs') and self.btn_cs.cget("state") != "disabled":
            ACTIVE_COLOR = "#1f6aa5"
            DEFAULT_COLOR = "transparent"
            BORDER_COLOR = "gray50"
            self.btn_cs.configure(
                fg_color=ACTIVE_COLOR if cs_active else DEFAULT_COLOR,
                border_color=ACTIVE_COLOR if cs_active else BORDER_COLOR,
                text_color="white" if cs_active else "gray70"
            )
        self.save_config()

    def on_cs_click(self):
        """Only execute CheckSizes script if Videos mode is active."""
        if self.download_mode == "Videos":
            self.start_script_thread(CheckSizes)

    def set_keep_folders(self, state):
        self.keep_folders_state = state
        self.save_config()

    def set_playlist(self, state):
        self.playlist_state = state
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

    # --- STRUCTURED SETTINGS POPUP WINDOW ---
    def show_settings_window(self):
        settings_win = ctk.CTkToplevel(self)
        settings_win.title("VidHandler Settings")
        settings_win.geometry("460x600")
        settings_win.resizable(False, False)
        settings_win.grab_set()

        ACTIVE_COLOR = "#1f6aa5"
        DEFAULT_COLOR = "transparent"
        BORDER_COLOR = "gray50"

        container = ctk.CTkScrollableFrame(settings_win, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # --- 1. LinkCopier Section ---
        ctk.CTkLabel(container, text="LinkCopier", font=("Arial", 13, "bold"), text_color="#1f6aa5").pack(anchor="w", pady=(0, 2))
        sep1 = ctk.CTkFrame(container, height=2, fg_color="gray50")
        sep1.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(container, text="• A future setting will be here", font=("Arial", 11), text_color="gray70").pack(anchor="w", padx=10, pady=(0, 15))

        # --- 2. YoutubeDownloader Section ---
        ctk.CTkLabel(container, text="YoutubeDownloader", font=("Arial", 13, "bold"), text_color="#1f6aa5").pack(anchor="w", pady=(0, 2))
        sep2 = ctk.CTkFrame(container, height=2, fg_color="gray50")
        sep2.pack(fill="x", pady=(0, 8))

        # Mode Setting
        mode_frame = ctk.CTkFrame(container, fg_color="transparent")
        mode_frame.pack(fill="x", pady=4, padx=10)
        ctk.CTkLabel(mode_frame, text="Download Mode:").pack(side="left")
        
        btn_videos = ctk.CTkButton(mode_frame, text="Videos", width=70, height=26,
            fg_color=ACTIVE_COLOR if self.download_mode == "Videos" else DEFAULT_COLOR,
            border_color=ACTIVE_COLOR if self.download_mode == "Videos" else BORDER_COLOR, border_width=2)
        btn_music = ctk.CTkButton(mode_frame, text="Music", width=70, height=26,
            fg_color=ACTIVE_COLOR if self.download_mode == "Music" else DEFAULT_COLOR,
            border_color=ACTIVE_COLOR if self.download_mode == "Music" else BORDER_COLOR, border_width=2)

        # Quality Setting
        qual_frame = ctk.CTkFrame(container, fg_color="transparent")
        qual_frame.pack(fill="x", pady=4, padx=10)
        ctk.CTkLabel(qual_frame, text="Quality / Bitrate:").pack(side="left")
        
        initial_q_vals = ["144p", "360p", "480p", "720p", "1080p"] if self.download_mode == "Videos" else ["128kbps", "192kbps", "256kbps", "320kbps"]
        qual_dropdown = ctk.CTkComboBox(
            qual_frame, values=initial_q_vals, variable=self.quality_var,
            command=lambda choice: self.save_config(), state="readonly", width=120
        )
        qual_dropdown.pack(side="right")

        # Playlist Setting
        pl_frame = ctk.CTkFrame(container, fg_color="transparent")
        pl_frame.pack(fill="x", pady=4, padx=10)
        ctk.CTkLabel(pl_frame, text="Allow Playlist:").pack(side="left")
        
        btn_pl_true = ctk.CTkButton(pl_frame, text="True", width=70, height=26,
            fg_color=ACTIVE_COLOR if self.playlist_state == "True" else DEFAULT_COLOR,
            border_color=ACTIVE_COLOR if self.playlist_state == "True" else BORDER_COLOR, border_width=2)
        btn_pl_false = ctk.CTkButton(pl_frame, text="False", width=70, height=26,
            fg_color=ACTIVE_COLOR if self.playlist_state == "False" else DEFAULT_COLOR,
            border_color=ACTIVE_COLOR if self.playlist_state == "False" else BORDER_COLOR, border_width=2)

        def update_mode(m):
            self.set_download_mode(m)
            if m == "Videos":
                btn_videos.configure(fg_color=ACTIVE_COLOR, border_color=ACTIVE_COLOR)
                btn_music.configure(fg_color=DEFAULT_COLOR, border_color=BORDER_COLOR)
                qual_dropdown.configure(values=["144p", "360p", "480p", "720p", "1080p"])
                if self.quality_var.get() not in ["144p", "360p", "480p", "720p", "1080p"]:
                    self.quality_var.set("360p")
            else:
                btn_music.configure(fg_color=ACTIVE_COLOR, border_color=ACTIVE_COLOR)
                btn_videos.configure(fg_color=DEFAULT_COLOR, border_color=BORDER_COLOR)
                qual_dropdown.configure(values=["128kbps", "192kbps", "256kbps", "320kbps"])
                if self.quality_var.get() not in ["128kbps", "192kbps", "256kbps", "320kbps"]:
                    self.quality_var.set("320kbps")
            self.save_config()

        def update_playlist(st):
            self.set_playlist(st)
            if st == "True":
                btn_pl_true.configure(fg_color=ACTIVE_COLOR, border_color=ACTIVE_COLOR)
                btn_pl_false.configure(fg_color=DEFAULT_COLOR, border_color=BORDER_COLOR)
            else:
                btn_pl_false.configure(fg_color=ACTIVE_COLOR, border_color=ACTIVE_COLOR)
                btn_pl_true.configure(fg_color=DEFAULT_COLOR, border_color=BORDER_COLOR)

        btn_videos.configure(command=lambda: update_mode("Videos"))
        btn_music.configure(command=lambda: update_mode("Music"))
        btn_music.pack(side="right", padx=2)
        btn_videos.pack(side="right", padx=2)

        btn_pl_true.configure(command=lambda: update_playlist("True"))
        btn_pl_false.configure(command=lambda: update_playlist("False"))
        btn_pl_false.pack(side="right", padx=2)
        btn_pl_true.pack(side="right", padx=2)

        ctk.CTkLabel(container, text="").pack(pady=5)

        # --- 3. VidHandler Section ---
        ctk.CTkLabel(container, text="VidHandler", font=("Arial", 13, "bold"), text_color="#1f6aa5").pack(anchor="w", pady=(0, 2))
        sep3 = ctk.CTkFrame(container, height=2, fg_color="gray50")
        sep3.pack(fill="x", pady=(0, 8))

        kf_frame = ctk.CTkFrame(container, fg_color="transparent")
        kf_frame.pack(fill="x", pady=4, padx=10)
        ctk.CTkLabel(kf_frame, text="Keep Folders:").pack(side="left")
        
        btn_kf_true = ctk.CTkButton(kf_frame, text="True", width=70, height=26,
            fg_color=ACTIVE_COLOR if self.keep_folders_state == "True" else DEFAULT_COLOR,
            border_color=ACTIVE_COLOR if self.keep_folders_state == "True" else BORDER_COLOR, border_width=2)
        btn_kf_false = ctk.CTkButton(kf_frame, text="False", width=70, height=26,
            fg_color=ACTIVE_COLOR if self.keep_folders_state == "False" else DEFAULT_COLOR,
            border_color=ACTIVE_COLOR if self.keep_folders_state == "False" else BORDER_COLOR, border_width=2)

        def update_kf(st):
            self.set_keep_folders(st)
            if st == "True":
                btn_kf_true.configure(fg_color=ACTIVE_COLOR, border_color=ACTIVE_COLOR)
                btn_kf_false.configure(fg_color=DEFAULT_COLOR, border_color=BORDER_COLOR)
            else:
                btn_kf_false.configure(fg_color=ACTIVE_COLOR, border_color=ACTIVE_COLOR)
                btn_kf_true.configure(fg_color=DEFAULT_COLOR, border_color=BORDER_COLOR)

        btn_kf_true.configure(command=lambda: update_kf("True"))
        btn_kf_false.configure(command=lambda: update_kf("False"))
        btn_kf_false.pack(side="right", padx=2)
        btn_kf_true.pack(side="right", padx=2)

        ctk.CTkLabel(container, text="").pack(pady=5)

        # --- 4. Paths Section ---
        ctk.CTkLabel(container, text="Paths", font=("Arial", 13, "bold"), text_color="#1f6aa5").pack(anchor="w", pady=(0, 2))
        sep4 = ctk.CTkFrame(container, height=2, fg_color="gray50")
        sep4.pack(fill="x", pady=(0, 8))

        # Youtube Path Setting
        yp_frame = ctk.CTkFrame(container, fg_color="transparent")
        yp_frame.pack(fill="x", pady=4, padx=10)
        ctk.CTkLabel(yp_frame, text="Youtube Path:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 2))
        
        yp_inner = ctk.CTkFrame(yp_frame, fg_color="transparent")
        yp_inner.pack(fill="x")
        
        curr_y_path = self.get_path_from_file(0, "Not Set")
        y_path_label = ctk.CTkLabel(yp_inner, text=curr_y_path, text_color="gray70", anchor="w", width=220)
        y_path_label.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        def browse_youtube_path():
            dir_path = filedialog.askdirectory(title="Select Youtube Folder")
            if dir_path:
                self.set_path_in_file(0, dir_path)
                y_path_label.configure(text=dir_path, text_color="white")

        ctk.CTkButton(yp_inner, text="Browse...", width=90, height=26,
            command=browse_youtube_path, fg_color="#333333", hover_color="#444444",
            border_color=BORDER_COLOR, border_width=2, text_color="white"
        ).pack(side="right")

        # Anime Path Setting
        ap_frame = ctk.CTkFrame(container, fg_color="transparent")
        ap_frame.pack(fill="x", pady=(10, 4), padx=10)
        ctk.CTkLabel(ap_frame, text="Anime Path:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 2))
        
        ap_inner = ctk.CTkFrame(ap_frame, fg_color="transparent")
        ap_inner.pack(fill="x")
        
        curr_a_path = self.get_path_from_file(1, "Not Set")
        a_path_label = ctk.CTkLabel(ap_inner, text=curr_a_path, text_color="gray70", anchor="w", width=220)
        a_path_label.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        def browse_anime_path():
            dir_path = filedialog.askdirectory(title="Select Anime Folder")
            if dir_path:
                self.set_path_in_file(1, dir_path)
                a_path_label.configure(text=dir_path, text_color="white")

        ctk.CTkButton(ap_inner, text="Browse...", width=90, height=26,
            command=browse_anime_path, fg_color="#333333", hover_color="#444444",
            border_color=BORDER_COLOR, border_width=2, text_color="white"
        ).pack(side="right")

    # --- UPDATE PROMPT MODAL ---
    def show_update_prompt(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("yt-dlp Update Available")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog, 
            text="A newer version of yt-dlp is available!\nWould you like to update?", 
            font=("Arial", 14, "bold")
        ).pack(pady=(25, 15))

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)

        def do_update(choice):
            dialog.destroy()
            self.start_script_thread(DebugScript, extra_args=[choice])

        ctk.CTkButton(
            btn_frame, text="Official Release", fg_color="#1f6aa5",
            command=lambda: do_update("stable")
        ).pack(side="left", expand=True, padx=5)

        ctk.CTkButton(
            btn_frame, text="Nightly Build", fg_color="#2b7a45",
            command=lambda: do_update("nightly")
        ).pack(side="left", expand=True, padx=5)

        ctk.CTkButton(
            dialog, text="Cancel", fg_color="gray40", width=100,
            command=dialog.destroy
        ).pack(pady=(0, 15))

    # --- LOGIC ---
    def monitor_file(self):
        path_left = self.pages[self.current_page]["left"]
        if os.path.exists(path_left):
            mtime = os.path.getmtime(path_left)
            if mtime > self.last_mtimes["left"]:
                if self.focus_get() != self.editor_left:
                    self.load_single_file(self.editor_left, path_left, "left")
                else:
                    self.last_mtimes["left"] = mtime

        path_right = self.pages[self.current_page]["right"]
        path_right_str = str(path_right) if isinstance(path_right, Path) else path_right
        if path_right_str != "terminal" and os.path.exists(path_right_str):
            mtime = os.path.getmtime(path_right_str)
            if mtime > self.last_mtimes["right"]:
                if self.focus_get() != self.editor_right:
                    self.load_single_file(self.editor_right, path_right_str, "right")
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

    def start_script_thread(self, script_path, extra_args=[]):
        if self.pages[self.current_page]["right"] != "terminal":
            self.switch_page("Page 1")
            
        self.save_content(self.editor_left, self.pages[self.current_page]["left"], "left")
        
        self.terminal.configure(state="normal")
        self.terminal.delete("1.0", "end")
        self.terminal.configure(state="disabled")
        self.is_progress_line_active = False
        
        self.set_script_buttons_state(False)
        
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
        
        # --- INJECT EMBEDDED FFmpeg RUNTIME PATH ---
        ffmpeg_dir = base_dir / "FFmpegRuntime"
        if ffmpeg_dir.exists():
            current_path = my_env.get("PATH", "")
            my_env["PATH"] = f"{str(ffmpeg_dir)};{current_path}"
        # -------------------------------------------
        
        startup_flags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
        
        try:
            cmd = [str(python_executable), str(script_path)] + extra_args
            self.active_process = subprocess.Popen(
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

            for line in self.active_process.stdout:
                clean_line = line.replace('\r', '').strip()
                if not clean_line:
                    continue

                if "[UPDATE_AVAILABLE]" in clean_line:
                    self.after(0, self.show_update_prompt)
                    continue

                if any(tag in clean_line for tag in ["[youtube]", "[info]", "[debug]"]):
                    continue

                # --- CLEANUP & PROGRESS RULES ---
                if "[ThumbnailsConvertor]" in clean_line or "Falling back to ffmpeg" in clean_line:
                    continue

                if "[Metadata] Adding metadata to" in clean_line:
                    match = re.search(r'\[Metadata\]\s+Adding metadata to\s+"(.*?)"', clean_line)
                    file_name = os.path.basename(match.group(1)) if match else "video"
                    msg = f"Adding metadata to {file_name}...\n"
                    self.after(0, lambda m=msg: self.append_or_update_progress(m, is_progress=False))
                    continue

                if "[EmbedThumbnail]" in clean_line and "Adding thumbnail to" in clean_line:
                    match = re.search(r'Adding thumbnail to\s+"(.*?)"', clean_line)
                    file_name = os.path.basename(match.group(1)) if match else "video"
                    msg = f"Adding thumbnail to {file_name}...\n"
                    self.after(0, lambda m=msg: self.append_or_update_progress(m, is_progress=False))
                    continue

                if "Deleting original file" in clean_line:
                    continue

                # Parse step-based progress (like CheckSizes [1/5], [2/5], etc.)
                if re.search(r'\[(\d+)/(\d+)\]', clean_line) and not "---" in clean_line:
                    match = re.search(r'\[(\d+)/(\d+)\]\s*(.*)', clean_line)
                    if match:
                        curr_str, total_str, action_desc = match.groups()
                        try:
                            curr = int(curr_str)
                            total = int(total_str)
                            pct = (curr / total) * 100
                            
                            bar_len = 15
                            filled = int(curr / total * bar_len)
                            label = "Checking Streams" if "stream checks" in action_desc.lower() else (action_desc or "Progress")
                            bar = f"{label} [ {'|' * filled}{' ' * (bar_len - filled)} ] {pct:.1f}%"
                            
                            self.after(0, lambda b=bar: self.append_or_update_progress(b, is_progress=True))
                            continue
                        except Exception:
                            pass
                # -------------------------------

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
                
            self.active_process.wait()
            self.active_process = None
            self.after(0, lambda: self.set_script_buttons_state(True))
            
        except Exception as e:
            self.active_process = None
            self.after(0, lambda: self.append_or_update_progress(f"\nError: {str(e)}\n", is_progress=False))
            self.after(0, lambda: self.set_script_buttons_state(True))

if __name__ == "__main__":
    app = TerminalGUI()
    app.mainloop()