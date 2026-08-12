#!/usr/bin/env bash
# Live-Rotationstest direkt auf der Konsole, ohne Reboot. Zeigt 4
# Testbilder (A-D) nacheinander je 6s, jedes gross beschriftet und in
# eine andere Rotation/Kein-Rotation gebracht. Einfach ablesen, welcher
# Buchstabe lesbar/richtig-herum auf dem Panel erscheint, und mir den
# Buchstaben sagen (z.B. "C") - dann baue ich genau diese Transformation
# fest in intro.mp4 ein.
set -uo pipefail

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  echo "Bitte mit sudo ausfuehren: sudo $0" >&2
  echo "(mpv --vo=drm braucht Root-Rechte fuer /dev/dri, genau wie der echte Boot-Service.)" >&2
  exit 1
fi

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
  mpv --no-config --fs --vo=drm \
    --no-audio --image-display-duration=6 --loop=no --no-osc \
    "$DIR/${f}.png"
  status=$?
  if [[ $status -ne 0 ]]; then
    echo "!!! mpv ist mit Exit-Code $status fehlgeschlagen bei TEST $f - siehe Fehlermeldung oben." >&2
  fi
done

echo
echo "Welcher Buchstabe (A/B/C/D) war lesbar und richtig herum? Sag mir den Buchstaben."
