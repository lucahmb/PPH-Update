#!/usr/bin/env bash
set -euo pipefail
BASE="$HOME/.local/share/pph-ap-control"
BIN="$HOME/.local/bin"
APPS="$HOME/.local/share/applications"
mkdir -p "$BASE" "$BIN" "$APPS"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
install -m 0755 "$SCRIPT_DIR/pph_ap_control.py" "$BASE/pph_ap_control.py"
cat > "$BIN/pph-ap-control" <<EOF
#!/usr/bin/env bash
exec python3 "$BASE/pph_ap_control.py" "\$@"
EOF
chmod +x "$BIN/pph-ap-control"
cat > "$APPS/pph-ap-control.desktop" <<EOF
[Desktop Entry]
Name=PPH App Control 6
Comment=PPH Field Router Controller
Exec=$BIN/pph-ap-control
Terminal=false
Type=Application
Categories=Network;Utility;
EOF
printf '\nPPH App Control 6.0.0 installiert.\nStart: pph-ap-control\n'
