import sys
import os
from PIL import Image, ImageOps

# --- CONFIGURATION ---
TARGET_WIDTH = 640
TARGET_HEIGHT = 360
OUTPUT_QUALITY = 85

def resize_and_crop(input_path, output_path):
    try:
        with Image.open(input_path) as img:
            # Convert to RGB (handles PNG transparency or other modes)
            if img.mode in ("RGBA", "P"): 
                img = img.convert("RGB")

            # This mimics the "object-fit: cover" behavior
            # It resizes and crops from the center automatically
            thumb = ImageOps.fit(
                img, 
                (TARGET_WIDTH, TARGET_HEIGHT), 
                method=Image.Resampling.LANCZOS, 
                centering=(0.5, 0.5)
            )

            # Save
            thumb.save(output_path, 'WEBP', quality=OUTPUT_QUALITY)
            print(f"✅ Success: {input_path} -> {output_path} ({TARGET_WIDTH}x{TARGET_HEIGHT})")

    except Exception as e:
        print(f"❌ Error processing {input_path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 resize.py <input_image> <output_image>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    resize_and_crop(input_file, output_file)
