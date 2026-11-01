#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
import tempfile
import cv2
import numpy as np

DEFAULT_INPUT1 = "assets/generated-video/replicate-prediction-g31db0zngdrmr0d1jt6an9tedc.mp4"
DEFAULT_INPUT2 = "assets/generated-video/replicate-prediction-xepzedhev1rmy0d1jtm951eq9c.mp4"
DEFAULT_OUT_DIR = "webgameconsole.com/3d-console"

# Maximum brightness any pixel can have to be considered background (#1f1f1f = 31)
MAX_BG_VAL = 32

def resample_indices(start, end, n):
    return [round(start + i * (end - start) / (n - 1)) for i in range(n)]

def clean_border_background(img_path):
    img = cv2.imread(img_path)
    if img is None:
        return

    h, w = img.shape[:2]

    # Mask for cv2.floodFill must be (h+2, w+2), uint8.
    # Pixels set to 1 in the mask block the fill.
    mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
    max_channel = np.max(img, axis=2)
    mask[1:h + 1, 1:w + 1][max_channel > MAX_BG_VAL] = 1

    # Dense seeds along all 4 perimeter borders
    seeds = []
    for x in range(0, w, 8):
        seeds.append((x, 0))
        seeds.append((x, h - 1))
    for y in range(0, h, 8):
        seeds.append((0, y))
        seeds.append((w - 1, y))

    # Floating-range floodFill follows subtle gradients but stops at edges
    flags = 4 | (255 << 8)
    for sx, sy in seeds:
        if mask[sy + 1, sx + 1] == 0:
            cv2.floodFill(img, mask, (sx, sy), (0, 0, 0),
                          loDiff=(3, 3, 3), upDiff=(3, 3, 3),
                          flags=flags)

    cv2.imwrite(img_path, img, [cv2.IMWRITE_JPEG_QUALITY, 95])

def main():
    input1 = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INPUT1
    input2 = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_INPUT2
    out_dir = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_OUT_DIR

    tmp_dir = tempfile.mkdtemp(prefix="console_frames_")
    try:
        print(f"Extracting part 1: {input1}...", flush=True)
        subprocess.run(["ffmpeg", "-y", "-i", input1, "-q:v", "2",
                        os.path.join(tmp_dir, "raw_%04d.jpg")], check=True)

        count1 = len([f for f in os.listdir(tmp_dir) if f.startswith("raw_") and f.endswith(".jpg")])
        start2 = count1 + 1

        print(f"Extracting part 2: {input2} starting at {start2}...", flush=True)
        subprocess.run(["ffmpeg", "-y", "-i", input2, "-start_number", str(start2),
                        "-q:v", "2", os.path.join(tmp_dir, "raw_%04d.jpg")], check=True)

        os.makedirs(out_dir, exist_ok=True)
        for existing in os.listdir(out_dir):
            if existing.startswith("frame_") and (existing.endswith(".jpg") or existing.endswith(".webp")):
                os.remove(os.path.join(out_dir, existing))

        # First half: cut first 5 and last 5 -> 6..76
        # Second half: cut first 4 and last 4 -> 106..164
        h1 = resample_indices(6, 76, 60)
        h2 = resample_indices(106, 164, 60)
        selected_frames = h1 + h2

        print(f"Assembling {len(selected_frames)} frames...", flush=True)
        for dest_idx, src_idx in enumerate(selected_frames, 1):
            src_file = os.path.join(tmp_dir, f"raw_{src_idx:04d}.jpg")
            dst_file = os.path.join(out_dir, f"frame_{dest_idx:04d}.jpg")
            shutil.copyfile(src_file, dst_file)

        print("Flood-filling off-black background from corners...", flush=True)
        for dest_idx in range(1, len(selected_frames) + 1):
            dst_file = os.path.join(out_dir, f"frame_{dest_idx:04d}.jpg")
            clean_border_background(dst_file)

        print(f"Done! {len(selected_frames)} processed frames written to {out_dir}.")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

if __name__ == "__main__":
    main()
