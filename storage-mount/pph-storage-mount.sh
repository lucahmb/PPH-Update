#!/usr/bin/env bash
# Stellt sicher, dass /mnt/storage gemountet ist. Nutzt den bestehenden
# /etc/fstab-Eintrag (UUID=643C-9877) als einzige Quelle der Wahrheit -
# hier ist absichtlich keine UUID hardcodiert, damit sich Skript und fstab
# nie widersprechen koennen. Wird von pph-storage-mount.timer regelmaessig
# erneut ausgefuehrt, ist also bei bereits gemountetem Storage ein no-op.
set -uo pipefail

MOUNT_POINT="/mnt/storage"
LOG_TAG="pph-storage-mount"

if mountpoint -q "$MOUNT_POINT"; then
  exit 0
fi

logger -t "$LOG_TAG" "$MOUNT_POINT ist nicht gemountet, versuche zu mounten"

for i in 1 2 3 4 5; do
  mount "$MOUNT_POINT" 2>&1 | logger -t "$LOG_TAG"
  if mountpoint -q "$MOUNT_POINT"; then
    logger -t "$LOG_TAG" "OK: $MOUNT_POINT gemountet (Versuch $i)"
    exit 0
  fi
  sleep 2
done

logger -t "$LOG_TAG" "FEHLER: $MOUNT_POINT konnte nach 5 Versuchen nicht gemountet werden"
exit 1
