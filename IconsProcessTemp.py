from PIL import Image
from pathlib import Path

INPUT_DIR = Path("icons")
OUTPUT_DIR = INPUT_DIR / "output"

OUTPUT_DIR.mkdir(exist_ok=True)

for image_path in INPUT_DIR.iterdir():
    if not image_path.is_file():
        continue

    try:
        with Image.open(image_path) as image:
            if image.size != (64, 64):
                print(f"Skipping {image_path.name}: size is {image.size}, not 64x64")
                continue

            resized = image.resize((48, 48), Image.Resampling.BILINEAR)

            output_path = OUTPUT_DIR / image_path.name
            resized.save(output_path)

            print(f"Resized: {image_path.name}")

    except Exception as e:
        print(f"Could not process {image_path.name}: {e}")

print("Done!")