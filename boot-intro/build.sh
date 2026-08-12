#!/usr/bin/env bash
# Rendert die Boot-Intro und muxt sie zu build/intro.mp4.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
VENV="$HERE/.venv"

if [[ ! -d "$VENV" ]]; then
  python3 -m venv "$VENV"
fi
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet pillow

rm -rf "$HERE/build/frames"
"$VENV/bin/python" "$HERE/render_frames.py"

ffmpeg -y -framerate 25 \
  -i "$HERE/build/frames/frame_%05d.png" \
  -c:v libx264 -pix_fmt yuv420p -profile:v baseline -level 3.0 \
  -movflags +faststart \
  "$HERE/build/intro.mp4"

rm -rf "$HERE/build/frames"

echo
echo "Fertig: $HERE/build/intro.mp4"
