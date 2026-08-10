#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$HOME/pph-funktest}"
FILE="$ROOT/pph_hub/polished_hub.py"

if [[ ! -f "$FILE" ]]; then
  echo "Datei nicht gefunden: $FILE" >&2
  exit 1
fi

BACKUP="$FILE.bak-pph6-snapshot-bypass-$(date +%Y%m%d-%H%M%S)"
cp -a "$FILE" "$BACKUP"

python3 - "$FILE" <<'PY'
from pathlib import Path
import sys

p = Path(sys.argv[1])
text = p.read_text(encoding='utf-8')
lines = text.splitlines()

marker = '# PPH6: legacy polished snapshot UI bypass'
if marker in text:
    print('PPH6 Snapshot-Bypass ist bereits aktiv.')
    raise SystemExit(0)

in_func = False
inserted = False
out = []
for line in lines:
    stripped = line.lstrip()
    indent = line[:len(line)-len(stripped)]

    if stripped.startswith('def _apply_snapshot('):
        in_func = True
        out.append(line)
        continue

    if in_func and stripped.startswith('super()._apply_snapshot(snapshot)'):
        out.append(line)
        child = indent
        out.append(f"{child}{marker}")
        out.append(f"{child}return")
        inserted = True
        in_func = False
        continue

    out.append(line)

if not inserted:
    raise SystemExit('Erwarteter super()._apply_snapshot(snapshot)-Aufruf wurde nicht gefunden; nichts verändert.')

p.write_text('\n'.join(out) + ('\n' if text.endswith('\n') else ''), encoding='utf-8')
print('Legacy-Polished-Snapshot-UI vollständig deaktiviert.')
PY

python3 -m py_compile "$FILE"

echo "Backup: $BACKUP"
echo "Hotfix erfolgreich installiert."
echo "Jetzt Hub neu starten."
