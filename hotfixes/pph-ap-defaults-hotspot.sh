#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$HOME/pph-funktest}"
FILE="$ROOT/pph_hub/access_point.py"

if [[ ! -f "$FILE" ]]; then
  echo "access_point.py nicht gefunden: $FILE" >&2
  exit 1
fi

BACKUP="$FILE.bak-ap-defaults-$(date +%Y%m%d-%H%M%S)"
cp -a "$FILE" "$BACKUP"

python3 - "$FILE" <<'PY'
from pathlib import Path
import re, sys

p = Path(sys.argv[1])
text = p.read_text(encoding='utf-8')
orig = text

# Default SSID
text, n1 = re.subn(r'("ssid"\s*:\s*)"[^"]*"', r'\1"Hotspot"', text, count=1)

# Default password if already present in DEFAULT/config literal.
text, n2 = re.subn(r'("password"\s*:\s*)"[^"]*"', r'\1"Keller 098!"', text, count=1)

# If DEFAULT has no password key, inject one next to ssid.
if n2 == 0:
    text, n3 = re.subn(
        r'(DEFAULT\s*=\s*\{[^\n\}]*"ssid"\s*:\s*"Hotspot"\s*,)',
        r'\1 "password": "Keller 098!",',
        text,
        count=1,
    )
else:
    n3 = 0

if text == orig:
    if '"ssid": "Hotspot"' in text and '"password": "Keller 098!"' in text:
        print('AP-Defaults sind bereits gesetzt.')
        raise SystemExit(0)
    raise SystemExit('Erwartete DEFAULT-Konfiguration nicht gefunden; nichts geändert.')

p.write_text(text, encoding='utf-8')
print(f'AP-Defaults aktualisiert: SSID={n1}, Passwort={n2 or n3}')
PY

python3 -m py_compile "$FILE"

echo "Backup: $BACKUP"
echo "Neue Defaults:"
echo "  SSID: Hotspot"
echo "  Passwort: Keller 098!"
echo "Hinweis: Bereits gespeicherte AP-Konfigurationen werden nicht automatisch überschrieben."
