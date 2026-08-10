#!/usr/bin/env bash
set -euo pipefail
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
BASE="https://raw.githubusercontent.com/lucahmb/PPH-Update/main/laptop/v6.0.1"
curl -fsSL "$BASE/pph_ap_control.py?cb=$(date +%s%N)" -o "$TMP/pph_ap_control.py"
curl -fsSL "$BASE/install.sh?cb=$(date +%s%N)" -o "$TMP/install.sh"
chmod +x "$TMP/install.sh"
"$TMP/install.sh"
