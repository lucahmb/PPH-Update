#!/usr/bin/env bash
# Auf dem Raspberry Pi ausfuehren.
set -euo pipefail

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  echo "Bitte mit sudo ausfuehren: sudo ./install.sh" >&2
  exit 1
fi

HERE="$(cd "$(dirname "$0")" && pwd)"

if ! grep -q '/mnt/storage' /etc/fstab; then
  echo "Kein /mnt/storage-Eintrag in /etc/fstab gefunden - das Skript verlaesst sich" >&2
  echo "bewusst auf den bestehenden fstab-Eintrag (mount /mnt/storage) statt eine" >&2
  echo "eigene UUID zu hardcoden. Erst fstab einrichten, dann erneut versuchen." >&2
  exit 1
fi

install -d -m 0755 /usr/local/sbin
install -m 0755 "$HERE/pph-storage-mount.sh" /usr/local/sbin/pph-storage-mount.sh
install -m 0644 "$HERE/pph-storage-mount.service" /etc/systemd/system/pph-storage-mount.service
install -m 0644 "$HERE/pph-storage-mount.timer" /etc/systemd/system/pph-storage-mount.timer

systemctl daemon-reload
systemctl enable --now pph-storage-mount.timer

echo
echo "Installiert und aktiv."
echo "Status:  systemctl status pph-storage-mount.timer"
echo "Log:     journalctl -t pph-storage-mount -b --no-pager"
echo "Sofort testen: sudo systemctl start pph-storage-mount.service"
