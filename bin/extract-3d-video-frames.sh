#!/usr/bin/env bash
set -euo pipefail

INPUT1="${1:-assets/generated-video/replicate-prediction-g31db0zngdrmr0d1jt6an9tedc.mp4}"
INPUT2="${2:-assets/generated-video/replicate-prediction-xepzedhev1rmy0d1jtm951eq9c.mp4}"
OUT_DIR="${3:-webgameconsole.com/3d-console}"

TMP_DIR=$(mktemp -d /tmp/console-frames-XXXXXX)
trap 'rm -rf "$TMP_DIR"' EXIT

echo "Extracting part 1 from $INPUT1..."
ffmpeg -y -i "$INPUT1" -q:v 2 "$TMP_DIR/raw_%04d.jpg"

COUNT1=$(ls -1 "$TMP_DIR"/raw_*.jpg | wc -l)
START_NUM=$((COUNT1 + 1))

echo "Extracting part 2 from $INPUT2 starting at frame $START_NUM..."
ffmpeg -y -i "$INPUT2" -start_number "$START_NUM" -q:v 2 "$TMP_DIR/raw_%04d.jpg"

mkdir -p "$OUT_DIR"
rm -f "$OUT_DIR"/frame_*.jpg

# Resample first half (81 frames) down to 67 frames to match second half (67 frames)
dest_idx=1

# 67 evenly spaced indices across 1..81
FIRST_HALF_FRAMES=$(python3 -c '
n = 67
start, end = 1, 81
indices = [round(start + i * (end - start) / (n - 1)) for i in range(n)]
print(" ".join(map(str, indices)))
')

for i in $FIRST_HALF_FRAMES $(seq 102 168); do
  src_file=$(printf "$TMP_DIR/raw_%04d.jpg" "$i")
  dst_file=$(printf "$OUT_DIR/frame_%04d.jpg" "$dest_idx")
  cp "$src_file" "$dst_file"
  dest_idx=$((dest_idx + 1))
done

echo "Assembled $((dest_idx - 1)) frames in $OUT_DIR."

echo "Flood-filling background from border with threshold #242424..."
python3 -c '
import glob
import sys
from collections import deque
from PIL import Image

MAX_VAL = 0x24
files = sorted(glob.glob("'"$OUT_DIR"'/frame_*.jpg"))
total = len(files)

for i, f in enumerate(files, 1):
    print(f"[{i}/{total}] Flood-filling {f}...", flush=True)
    with Image.open(f) as im:
        rgb = im.convert("RGB")
        w, h = rgb.size
        pixels = rgb.load()

        queue = deque()
        visited = bytearray(w * h)

        # Seed from all pixels along outer border
        for x in range(w):
            for y in (0, h - 1):
                idx = y * w + x
                visited[idx] = 1
                r, g, b = pixels[x, y]
                if r <= MAX_VAL and g <= MAX_VAL and b <= MAX_VAL:
                    queue.append((x, y))
                    pixels[x, y] = (0, 0, 0)

        for y in range(h):
            for x in (0, w - 1):
                idx = y * w + x
                if not visited[idx]:
                    visited[idx] = 1
                    r, g, b = pixels[x, y]
                    if r <= MAX_VAL and g <= MAX_VAL and b <= MAX_VAL:
                        queue.append((x, y))
                        pixels[x, y] = (0, 0, 0)

        while queue:
            cx, cy = queue.popleft()
            for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                if 0 <= nx < w and 0 <= ny < h:
                    nidx = ny * w + nx
                    if not visited[nidx]:
                        visited[nidx] = 1
                        r, g, b = pixels[nx, ny]
                        if r <= MAX_VAL and g <= MAX_VAL and b <= MAX_VAL:
                            pixels[nx, ny] = (0, 0, 0)
                            queue.append((nx, ny))

        rgb.save(f, quality=95)
'
echo "Flood-fill complete."
