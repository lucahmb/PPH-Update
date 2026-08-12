#!/usr/bin/env bash
# Auf dem Raspberry Pi ausfuehren - entweder direkt aus diesem Dev-Ordner
# (nach ./build.sh) oder aus dem boot_intro/-Unterordner eines installierten
# PPH-Update-Pakets (dort liegt intro.mp4 bereits fertig daneben).
set -euo pipefail

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  echo "Bitte mit sudo ausfuehren: sudo ./install.sh" >&2
  exit 1
fi

HERE="$(cd "$(dirname "$0")" && pwd)"

if [[ -f "$HERE/build/intro.mp4" ]]; then
  SRC="$HERE/build/intro.mp4"
elif [[ -f "$HERE/intro.mp4" ]]; then
  SRC="$HERE/intro.mp4"
else
  echo "intro.mp4 fehlt - zuerst ./build.sh ausfuehren." >&2
  exit 1
fi

if ! command -v mpv >/dev/null; then
  echo "mpv ist nicht installiert: sudo apt install -y mpv" >&2
  exit 1
fi

install -d -m 0755 /opt/luca-boot-intro
install -m 0644 "$SRC" /opt/luca-boot-intro/intro.mp4
install -m 0644 "$HERE/pph-boot-intro.service" /etc/systemd/system/pph-boot-intro.service

systemctl daemon-reload
systemctl enable pph-boot-intro.service

echo
echo "Installiert."
echo "Test ohne Neustart:  sudo systemctl start pph-boot-intro.service"
echo "Ab dem naechsten Boot laeuft die Intro automatisch vor Login/App."
