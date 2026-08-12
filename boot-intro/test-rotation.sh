#!/usr/bin/env bash
# Live-Rotationstest, laeuft als normaler Wayland-Client im bereits
# laufenden Desktop (labwc) - kein sudo, kein --vo=drm, kein Kampf um
# DRM-Master. Zeigt 4 Testbilder (A-D) nacheinander je 6s. Einfach
# ablesen, welcher Buchstabe lesbar/richtig-herum erscheint, und mir den
# Buchstaben sagen (z.B. "C") - dann baue ich genau diese Transformation
# fest in intro.mp4 ein.
#
# NICHT mit sudo ausfuehren - der Wayland-Socket gehoert dem normalen
# Desktop-User, root sieht ihn i.d.R. nicht.
set -uo pipefail

if [[ ${EUID:-$(id -u)} -eq 0 ]]; then
  echo "Bitte OHNE sudo ausfuehren (als der Desktop-User, z.B. luca): bash $0" >&2
  exit 1
fi

export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
if [[ -z "${WAYLAND_DISPLAY:-}" ]]; then
  for cand in "$XDG_RUNTIME_DIR"/wayland-*; do
    [[ -S "$cand" ]] || continue
    export WAYLAND_DISPLAY="$(basename "$cand")"
    break
  done
fi
if [[ -z "${WAYLAND_DISPLAY:-}" ]]; then
  echo "Kein Wayland-Socket in $XDG_RUNTIME_DIR gefunden. Laeuft der Desktop?" >&2
  echo "Falls per SSH: WAYLAND_DISPLAY=wayland-0 (o.ae.) manuell setzen und erneut versuchen." >&2
  exit 1
fi
echo "Nutze XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR WAYLAND_DISPLAY=$WAYLAND_DISPLAY"

HERE="$(cd "$(dirname "$0")" && pwd)"
DIR="$HERE/build/rot-test"
mkdir -p "$DIR"

FONT=""
for f in \
  /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf \
  /usr/share/fonts/TTF/DejaVuSans-Bold.ttf
do
  if [[ -f "$f" ]]; then FONT="$f"; break; fi
done
if [[ -z "$FONT" ]]; then
  echo "Keine DejaVu-Bold-Schrift gefunden - Pfad in test-rotation.sh anpassen." >&2
  exit 1
fi

gen() {
  local name="$1" vf="$2"
  ffmpeg -y -f lavfi -i "color=c=0x07100E:s=1280x720:d=1" \
    -vf "drawtext=fontfile=${FONT}:text='TEST ${name}':fontcolor=0x4FE3C1:fontsize=160:x=(w-text_w)/2:y=(h-text_h)/2,${vf}" \
    -frames:v 1 "$DIR/${name}.png" -loglevel error
}

echo "Erzeuge Testbilder ..."
gen A "null"                        # keine Rotation (1280x720, wird ggf. pillarboxed)
gen B "transpose=1"                 # 90 Grad im Uhrzeigersinn
gen C "transpose=2"                 # 90 Grad gegen den Uhrzeigersinn
gen D "transpose=1,transpose=1"     # 180 Grad

for f in A B C D; do
  echo
  echo "=== Zeige TEST $f (6 Sekunden) ==="
  mpv --no-config --fs \
    --no-audio --image-display-duration=6 --loop=no --no-osc \
    "$DIR/${f}.png"
  status=$?
  if [[ $status -ne 0 ]]; then
    echo "!!! mpv ist mit Exit-Code $status fehlgeschlagen bei TEST $f - siehe Fehlermeldung oben." >&2
  fi
done

echo
echo "Welcher Buchstabe (A/B/C/D) war lesbar und richtig herum? Sag mir den Buchstaben."
