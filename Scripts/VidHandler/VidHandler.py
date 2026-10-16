from pathlib import Path
import subprocess
import sys
print("Python being used:", sys.executable)

# Get the root project directory (VidHandler/) to find the portable python runtime
# VidHandler.py is at: VidHandler/Scripts/VidHandler/VidHandler.py
base_dir = Path(__file__).resolve().parent.parent.parent
python_executable = base_dir / "Runtime" / "python.exe"

# Sub-scripts are located in: VidHandler/Scripts/VidHandler/Scripts/
scripts_dir = Path(__file__).resolve().parent / "Scripts"

# Directly define script paths
GetChannelName = scripts_dir / "GetChannelName.py"
VidRenamer = scripts_dir / "NewRenamer.py"
CheckVidOpp = scripts_dir / "CheckVidOpp.py"
sort_videos = scripts_dir / "NewSort.py"
CheckVid = scripts_dir / "CheckVid.py"
IconGetter = scripts_dir / "IconGetter.py"
IconAssinger = scripts_dir / "IconAssinger.py"
CricledImages = scripts_dir / "CircledImages.py"
IcoConverter = scripts_dir / "IcoConverter.py"
AnimeDetector = scripts_dir / "AnimeDetector.py"

def runpyfile():
    scripts = [
        GetChannelName,
        VidRenamer,
        CheckVidOpp,
        AnimeDetector,
        sort_videos,
        IconGetter,
        CricledImages,
        IcoConverter,
        IconAssinger,
        CheckVid
    ]

    for script in scripts:
        print("-" * 116)
        print(f"Running: {script.name}")
        
        if not script.exists():
            print(f"[ERROR] Script not found: {script}")
            continue
            
        try:
            subprocess.run(
                [str(python_executable), str(script)], 
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Script {script.name} failed with exit code {e.returncode}")
        except Exception as e:
            print(f"[ERROR] Failed to execute {script.name}: {e}")
            
    print("-" * 116)

if __name__ == "__main__":
    runpyfile()