#!/usr/bin/env bash
set -euo pipefail

PPH_DIR="${1:-$HOME/pph-funktest}"
BASE_CHANNEL_URL="https://raw.githubusercontent.com/lucahmb/PPH-Update/main/channels/stable.json"
INBOX="$HOME/.local/share/pph/updates/inbox"
CACHE_BUST="$(date +%s%N)"
CHANNEL_URL="${BASE_CHANNEL_URL}?cb=${CACHE_BUST}"

if [[ ! -f "$PPH_DIR/pph_update_manager.py" ]]; then
  echo "PPH Updater nicht gefunden: $PPH_DIR/pph_update_manager.py" >&2
  exit 1
fi

mkdir -p "$INBOX"

echo "PPH GitHub Bootstrap"
echo "Projekt: $PPH_DIR"

readarray -t INFO < <(python3 - "$CHANNEL_URL" <<'PY'
import json, sys, urllib.request
url=sys.argv[1]
req=urllib.request.Request(url, headers={'User-Agent':'PPH-Bootstrap/2','Cache-Control':'no-cache','Pragma':'no-cache'})
with urllib.request.urlopen(req, timeout=10) as r:
    data=json.load(r)
if data.get('product') != 'pph-funktest' or data.get('channel') != 'stable':
    raise SystemExit('Ungültiger Stable Channel')
for key in ('version','package_url','sha256'):
    if not data.get(key):
        raise SystemExit(f'Fehlender Wert: {key}')
print(data['version'])
print(data['package_url'])
print(data['sha256'])
PY
)

VERSION="${INFO[0]}"
URL="${INFO[1]}"
SHA="${INFO[2]}"
PACKAGE="$INBOX/pph-update-$VERSION.tar.gz"
PACKAGE_URL="${URL}?cb=${CACHE_BUST}"

echo "Stable: $VERSION"
echo "Download …"
rm -f "$PACKAGE"
python3 - "$PACKAGE_URL" "$PACKAGE" <<'PY'
import pathlib, sys, urllib.request
url, target=sys.argv[1], pathlib.Path(sys.argv[2])
req=urllib.request.Request(url, headers={'User-Agent':'PPH-Bootstrap/2','Cache-Control':'no-cache','Pragma':'no-cache'})
with urllib.request.urlopen(req, timeout=30) as r, target.open('wb') as f:
    while True:
        chunk=r.read(1024*256)
        if not chunk: break
        f.write(chunk)
PY

ACTUAL="$(sha256sum "$PACKAGE" | awk '{print $1}')"
if [[ "$ACTUAL" != "$SHA" ]]; then
  rm -f "$PACKAGE"
  echo "SHA-256-Prüfung fehlgeschlagen" >&2
  echo "Erwartet: $SHA" >&2
  echo "Geladen:  $ACTUAL" >&2
  exit 1
fi

echo "SHA-256 OK"
cd "$PPH_DIR"
PYTHONPATH=. python3 pph_update_manager.py install "$PACKAGE"

echo
echo "Bootstrap abgeschlossen. PPH neu starten."
