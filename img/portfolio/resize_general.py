#!/usr/bin/env python3
import sys
from pathlib import Path
from PIL import Image, ImageOps

# --- CONFIGURATION ---
TARGET_WIDTH = 640
TARGET_HEIGHT = 360

# For lossy formats (e.g., WEBP/JPEG). Ignored for lossless PNG.
OUTPUT_QUALITY = 85

# ----------------------

WILDCARDS = set("*?[")

def has_wildcard(s: str) -> bool:
    return any(ch in s for ch in WILDCARDS)

def pillow_format_from_suffix(suffix: str) -> str:
    s = suffix.lower().lstrip(".")
    if s == "jpg":
        s = "jpeg"
    mapping = {
        "webp": "WEBP",
        "png": "PNG",
        "jpeg": "JPEG",
        "tif": "TIFF",
        "tiff": "TIFF",
        "bmp": "BMP",
        "gif": "GIF",
    }
    if s not in mapping:
        raise ValueError(f"Unsupported output extension: .{s}")
    return mapping[s]

def prepare_mode_for_output(img: Image.Image, out_fmt: str) -> Image.Image:
    """
    Convert image mode as needed for the target format while preserving alpha when possible.
    """
    out_fmt = out_fmt.upper()

    # Formats that cannot store alpha.
    if out_fmt in {"JPEG", "BMP"}:
        return img.convert("RGB")

    # WEBP and PNG can store alpha; keep it when present.
    if img.mode in ("RGBA", "LA"):
        return img.convert("RGBA")
    if img.mode == "P":
        # Palette images may have transparency.
        if "transparency" in img.info:
            return img.convert("RGBA")
        return img.convert("RGB")

    # Other modes -> RGB is fine for most.
    if img.mode not in ("RGB", "RGBA"):
        return img.convert("RGB")

    return img

def save_with_format(img: Image.Image, output_path: Path, out_fmt: str):
    out_fmt = out_fmt.upper()
    kwargs = {}

    if out_fmt in {"WEBP", "JPEG"}:
        kwargs["quality"] = int(OUTPUT_QUALITY)
        if out_fmt == "WEBP":
            # 0 (fast) .. 6 (best compression); mostly affects size/time.
            kwargs["method"] = 6

    if out_fmt == "PNG":
        # "quality" isn't a thing for PNG; use compression/optimization instead.
        kwargs["optimize"] = True
        kwargs["compress_level"] = 6  # 0..9 (higher = smaller, slower)

    img.save(str(output_path), format=out_fmt, **kwargs)

def resize_and_crop(input_path: Path, output_path: Path):
    try:
        out_fmt = pillow_format_from_suffix(output_path.suffix)

        with Image.open(input_path) as img:
            img = prepare_mode_for_output(img, out_fmt)

            # "object-fit: cover" style center crop
            thumb = ImageOps.fit(
                img,
                (TARGET_WIDTH, TARGET_HEIGHT),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            )

            output_path.parent.mkdir(parents=True, exist_ok=True)
            save_with_format(thumb, output_path, out_fmt)

        print(f"✅ Success: {input_path} -> {output_path} ({TARGET_WIDTH}x{TARGET_HEIGHT})")

    except Exception as e:
        print(f"❌ Error processing {input_path}: {e}", file=sys.stderr)

def usage():
    print(
        "Usage:\n"
        "  1) Single file:\n"
        "     python3 resize.py input.ext output.ext\n\n"
        "  2) Batch with output pattern (use * as placeholder for input stem):\n"
        "     python3 resize.py <many inputs...> '*_resized.png'\n"
        "     e.g. python3 resize.py *.png '*_resized.png'\n\n"
        "Notes:\n"
        "  - Output format is inferred from the output extension (png, webp, jpg/jpeg, tif/tiff, bmp, gif).\n"
        "  - If your shell expands *_resized.png (because matching files already exist), quote it as shown.\n"
    )

def main(argv):
    if len(argv) < 3:
        usage()
        return 1

    args = argv[1:]

    # Case 1: single input + single output
    if len(args) == 2 and not has_wildcard(args[1]):
        resize_and_crop(Path(args[0]), Path(args[1]))
        return 0

    # Case 2: batch: multiple inputs + a single output pattern as the last arg
    out_spec = args[-1]
    inputs = args[:-1]

    if not inputs:
        usage()
        return 1

    # If the output spec contains wildcard characters, treat it as a template.
    # '*' will be replaced with the input file's stem.
    if has_wildcard(out_spec):
        pattern = out_spec
        for inp in inputs:
            in_path = Path(inp)
            if not in_path.is_file():
                print(f"⚠️ Skipping (not a file): {in_path}", file=sys.stderr)
                continue

            out_name = pattern.replace("*", in_path.stem)
            out_path = Path(out_name)
            resize_and_crop(in_path, out_path)
        return 0

    # Otherwise, we don't know how to map many inputs to one output.
    usage()
    return 1

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
