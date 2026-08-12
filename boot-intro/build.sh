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

# Frames werden in 1280x720 Landscape gerendert. Keine Rotation beim
# Encodieren mehr noetig: mpv laeuft als normaler Wayland-Client im
# labwc-Desktop, der Compositor kompensiert die physische Panel-Montage
# bereits selbst (live per Testbild bestaetigt - "TEST A", ohne jede
# Rotation, war die richtige Ausrichtung).
ffmpeg -y -framerate 25 \
  -i "$HERE/build/frames/frame_%05d.png" \
  -c:v libx264 -pix_fmt yuv420p -profile:v baseline -level 3.0 \
  -movflags +faststart \
  "$HERE/build/intro.mp4"

rm -rf "$HERE/build/frames"

echo
echo "Fertig: $HERE/build/intro.mp4"
