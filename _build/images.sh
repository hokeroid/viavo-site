#!/bin/bash
# Builds the site's raster images from the real screens: AVIF + WebP at the sizes the pages use.
# Usage: _build/images.sh <source dir with carplay-*.png, phone-*.png, app-*.png>
set -euo pipefail
shopt -s nullglob
SRC="$1"; OUT="$(cd "$(dirname "$0")/.." && pwd)/assets/img"
mkdir -p "$OUT"
enc() { # enc <in.png> <out base> <width>
  local in="$1" base="$2" w="$3"
  cwebp -quiet -q 85 -sharp_yuv -resize "$w" 0 -metadata none "$in" -o "$base-$w.webp"
  ffmpeg -loglevel error -y -i "$in" -vf "scale=$w:-2:flags=lanczos" -pix_fmt yuv444p10le \
    -c:v libsvtav1 -crf 20 -svtav1-params avif=1 "$base-$w.avif" 2>/dev/null  # 10-bit: no banding in the amber glow; libaom fails to start on this Mac
}
for f in "$SRC"/carplay-*.png; do
  b="$OUT/$(basename "${f%.png}")"; enc "$f" "$b" 1920; enc "$f" "$b" 1080
done
for f in "$SRC"/phone-*.png; do
  b="$OUT/$(basename "${f%.png}")"; enc "$f" "$b" 660
done
for f in "$SRC"/app-*.png; do
  b="$OUT/$(basename "${f%.png}")"; cwebp -quiet -q 90 -resize 112 112 -metadata none "$f" -o "$b-112.webp"
done
