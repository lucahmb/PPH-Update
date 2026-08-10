#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$HOME/pph-funktest}"
FILE="$ROOT/pph_hub/pph_hub.py"

if [[ ! -f "$FILE" ]]; then
  echo "PPH Hub Datei nicht gefunden: $FILE" >&2
  exit 1
fi

BACKUP="$FILE.bak-system-vars-$(date +%Y%m%d-%H%M%S)"
cp -a "$FILE" "$BACKUP"

python3 - "$FILE" <<'PY'
from pathlib import Path
import re, sys

p = Path(sys.argv[1])
text = p.read_text(encoding='utf-8')
lines = text.splitlines()
out = []
changed = 0

# PPH 6 owns the visible UI and no longer creates the legacy system_vars
# dictionary. Guard legacy snapshot writes so backend polling continues.
pat = re.compile(r'^(\s*)self\.system_vars\[(["\'][^"\']+["\'])\]\.set\((.*)\)\s*$')

for line in lines:
    m = pat.match(line)
    if not m:
        out.append(line)
        continue
    indent, key, expr = m.groups()
    out.append(f"{indent}if hasattr(self, 'system_vars') and {key} in self.system_vars:")
    out.append(f"{indent}    self.system_vars[{key}].set({expr})")
    changed += 1

if changed == 0:
    # Idempotency: if already patched, accept it; otherwise stop instead of
    # silently modifying an unexpected file version.
    if "hasattr(self, 'system_vars')" in text:
        print('PPH 6 system_vars Hotfix ist bereits aktiv.')
        raise SystemExit(0)
    raise SystemExit('Keine erwarteten system_vars-Zugriffe gefunden; Datei wurde nicht verändert.')

new = '\n'.join(out) + ('\n' if text.endswith('\n') else '')
p.write_text(new, encoding='utf-8')
print(f'{changed} system_vars-Zugriffe abgesichert.')
PY

python3 -m py_compile "$FILE"

echo "Backup: $BACKUP"
echo "Hotfix erfolgreich installiert."
echo "Jetzt: cd $ROOT && ./start_pph_hub.sh"
