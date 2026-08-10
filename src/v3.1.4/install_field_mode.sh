#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  echo "Bitte mit sudo ausführen: sudo ./install_field_mode.sh" >&2
  exit 1
fi

TARGET_USER="${SUDO_USER:-luca}"
if [[ "$TARGET_USER" == "root" ]]; then
  TARGET_USER="luca"
fi

SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
install -d -m 0755 /usr/local/libexec
install -m 0755 "$SRC_DIR/fieldctl.py" /usr/local/libexec/pph-ap-fieldctl

cat >/etc/sudoers.d/pph-ap-fieldctl <<EOF
$TARGET_USER ALL=(root) NOPASSWD: /usr/local/libexec/pph-ap-fieldctl *
EOF
chmod 0440 /etc/sudoers.d/pph-ap-fieldctl
visudo -cf /etc/sudoers.d/pph-ap-fieldctl >/dev/null

cat >/etc/systemd/system/pph-ap-field.service <<EOF
[Unit]
Description=PPH Access Point Field Mode
After=NetworkManager.service docker.service
Wants=NetworkManager.service

[Service]
Type=simple
ExecStart=/usr/local/libexec/pph-ap-fieldctl watch $TARGET_USER
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now pph-ap-field.service

echo
printf 'PPH Field Mode installiert für Benutzer %s.\n' "$TARGET_USER"
echo 'Ab jetzt: LAN einstecken -> PPH-AccessPoint startet automatisch.'
echo 'Status: systemctl status pph-ap-field.service'
