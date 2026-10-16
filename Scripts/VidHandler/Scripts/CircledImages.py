import os
from pathlib import Path
from PIL import Image, ImageDraw

def make_circle_image(input_path, output_path):
    img = Image.open(input_path).convert("RGBA")

    size = min(img.size)
    left = (img.width - size) // 2
    top = (img.height - size) // 2
    img = img.crop((left, top, left + size, top + size))

    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)

    result = Image.new("RGBA", (size, size))
    result.paste(img, (0, 0), mask)

    result.save(output_path, format="PNG")

def process_folder_and_delete(input_folder):
    output_folder = os.path.join(input_folder, "Circled Images")
    os.makedirs(output_folder, exist_ok=True)

    supported_extensions = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".jfif")

    for filename in os.listdir(input_folder):
        if filename.lower().endswith(supported_extensions):
            input_path = os.path.join(input_folder, filename)
            name, _ = os.path.splitext(filename)
            output_path = os.path.join(output_folder, f"{name}_circle.png")

            try:
                make_circle_image(input_path, output_path)
                os.remove(input_path)  # Delete original
                print(f"Processed & deleted: {filename}")
            except Exception as e:
                print(f"Failed to process {filename}: {e}")

# Run on folder
base_dir = Path(__file__).resolve().parent.parent.parent.parent  # from Scripts → VidHandler
Png_folder = base_dir / "Icons\Png"
process_folder_and_delete(Png_folder)
