import os
from PIL import Image
from pathlib import Path

def convert_png_to_ico_and_delete(source_folder, destination_folder):
    os.makedirs(destination_folder, exist_ok=True)

    for filename in os.listdir(source_folder):
        if filename.lower().endswith(".png"):
            input_path = os.path.join(source_folder, filename)
            name, _ = os.path.splitext(filename)
            output_path = os.path.join(destination_folder, f"{name}.ico")

            try:
                img = Image.open(input_path).convert("RGBA")
                sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
                img.save(output_path, format="ICO", sizes=sizes)

                os.remove(input_path)  # Delete used PNG
                print(f"Converted & deleted: {filename}")
            except Exception as e:
                print(f"Failed to convert {filename}: {e}")

# Run on folders
base_dir = Path(__file__).resolve().parent.parent.parent.parent  # from Scripts → VidHandler
convert_png_to_ico_and_delete(
    source_folder = base_dir / "Icons\Png\Circled Images",
    destination_folder = base_dir / "Icons\Icon"
)
