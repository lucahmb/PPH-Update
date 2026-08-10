#!/usr/bin/env bash
set -euo pipefail

VERSION="6.0.1"
BASE="$HOME/.local/share/pph-ap-control"
BIN="$HOME/.local/bin"
APPS="$HOME/.local/share/applications"
TARGET="$BASE/pph_ap_control.py"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

mkdir -p "$BASE" "$BIN" "$APPS"

python3 - "$TMP" <<'PY'
import sys, urllib.request
out=sys.argv[1]
url='https://api.github.com/repos/lucahmb/PPH-Update/contents/laptop/v6.0.1/pph_ap_control.py?ref=main'
req=urllib.request.Request(url, headers={
    'User-Agent':'PPH-App-Control-Installer',
    'Accept':'application/vnd.github.raw+json',
    'Cache-Control':'no-cache',
    'Pragma':'no-cache',
})
with urllib.request.urlopen(req, timeout=20) as r:
    data=r.read()
if not data.startswith(b'#!/usr/bin/env python3'):
    raise SystemExit('Download ungültig: keine Python-Datei erhalten')
open(out,'wb').write(data)
PY

python3 -m py_compile "$TMP"
ACTUAL="$(grep -m1 '^VERSION=' "$TMP" || true)"
if [[ "$ACTUAL" != "VERSION='6.0.1'" ]]; then
  echo "Downloadprüfung fehlgeschlagen: $ACTUAL" >&2
  exit 1
fi
if ! grep -q 'msg=str(e)' "$TMP"; then
  echo "Downloadprüfung fehlgeschlagen: Python-3.13 Closure-Fix fehlt" >&2
  exit 1
fi

install -m 0755 "$TMP" "$TARGET"

cat > "$BIN/pph-ap-control" <<EOF
#!/usr/bin/env bash
exec python3 "$TARGET" "\$@"
EOF
cat > "$BIN/pph-app-control" <<EOF
#!/usr/bin/env bash
exec python3 "$TARGET" "\$@"
EOF
chmod +x "$BIN/pph-ap-control" "$BIN/pph-app-control"

cat > "$APPS/pph-ap-control.desktop" <<EOF
[Desktop Entry]
Name=PPH App Control $VERSION
Comment=PPH Field Router Controller
Exec=$BIN/pph-ap-control
Terminal=false
Type=Application
Categories=Network;Utility;
EOF

FINAL="$(grep -m1 '^VERSION=' "$TARGET" || true)"
if [[ "$FINAL" != "VERSION='6.0.1'" ]]; then
  echo "Installationsprüfung fehlgeschlagen: $FINAL" >&2
  exit 1
fi

printf '\nPPH App Control %s installiert und verifiziert.\nStart: pph-ap-control oder pph-app-control\n' "$VERSION"
