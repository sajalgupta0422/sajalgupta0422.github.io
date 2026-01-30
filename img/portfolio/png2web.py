#!/usr/bin/env python3
import sys
import os
import glob
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Missing dependency: Pillow\nInstall with: python3 -m pip install --user pillow", file=sys.stderr)
    sys.exit(1)

WILDCARDS = set("*?[")

def expand_args(args):
    """Expand any glob-like args ourselves (works even if the shell doesn't expand)."""
    expanded = []
    for a in args:
        if any(ch in a for ch in WILDCARDS):
            matches = glob.glob(a)
            expanded.extend(matches if matches else [a])  # keep literal if no matches
        else:
            expanded.append(a)
    return expanded

def to_webp(in_path: Path, out_path: Path, quality: int = 95, method: int = 6, lossless: bool = False):
    with Image.open(in_path) as im:
        # Preserve transparency when present; otherwise use RGB.
        if im.mode in ("RGBA", "LA"):
            im2 = im.convert("RGBA")
        elif im.mode == "P":
            # Palette PNG: choose RGBA if it has transparency, else RGB
            im2 = im.convert("RGBA") if ("transparency" in im.info) else im.convert("RGB")
        else:
            # Handles RGB, L, CMYK, I;16, etc. (will become 8-bit RGB)
            im2 = im.convert("RGB")

        save_kwargs = {
            "format": "WEBP",
            "quality": int(quality),
            "method": int(method),  # 0 (fast) .. 6 (best compression)
        }
        if lossless:
            save_kwargs["lossless"] = True
            # For lossless, quality is ignored by Pillow/encoder.

        # Preserve ICC profile if present
        icc = im.info.get("icc_profile")
        if icc:
            save_kwargs["icc_profile"] = icc

        out_path.parent.mkdir(parents=True, exist_ok=True)
        im2.save(out_path, **save_kwargs)

def main(argv):
    if len(argv) < 2:
        print("Usage: python3 png2webp.py <pngs...> [*.webp] [--quality=95] [--lossless] [--method=6]", file=sys.stderr)
        return 2

    raw_args = argv[1:]
    # Simple flag parsing (kept minimal on purpose)
    quality = 95
    method = 6
    lossless = False

    non_flags = []
    for a in raw_args:
        if a.startswith("--quality="):
            quality = int(a.split("=", 1)[1])
        elif a.startswith("--method="):
            method = int(a.split("=", 1)[1])
        elif a == "--lossless":
            lossless = True
        else:
            non_flags.append(a)

    # Treat any "*.webp" / ".webp" arguments as an output extension hint; ignore them.
    non_flags = [a for a in non_flags if not a.lower().endswith(".webp") and a.lower() != "*.webp"]

    files = expand_args(non_flags)
    pngs = []
    for f in files:
        p = Path(f)
        if p.is_file() and p.suffix.lower() == ".png":
            pngs.append(p)

    if not pngs:
        print("No PNG files found to convert.", file=sys.stderr)
        return 1

    # Clamp quality to sane bounds
    quality = max(0, min(100, quality))
    method = max(0, min(6, method))

    failures = 0
    for in_path in pngs:
        out_path = in_path.with_suffix(".webp")
        try:
            to_webp(in_path, out_path, quality=quality, method=method, lossless=lossless)
            print(f"{in_path} -> {out_path}")
        except Exception as e:
            failures += 1
            print(f"FAILED: {in_path} ({e})", file=sys.stderr)

    return 0 if failures == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

