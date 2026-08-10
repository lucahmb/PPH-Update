#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$HOME/pph-funktest}"
FILES=(
  "$ROOT/pph_hub/pph_hub.py"
  "$ROOT/pph_hub/polished_hub.py"
)

for f in "${FILES[@]}"; do
  [[ -f "$f" ]] || { echo "Datei fehlt: $f" >&2; exit 1; }
done

STAMP="$(date +%Y%m%d-%H%M%S)"
for f in "${FILES[@]}"; do
  cp -a "$f" "$f.bak-pph6-legacy-$STAMP"
done

python3 - "${FILES[@]}" <<'PY'
from pathlib import Path
import re, sys

# Guard direct legacy Tk variable writes such as:
# self.dashboard_overview_vars["measurement"].set(...)
# self.system_vars["cpu"].set(...)
# self.foo_vars["bar"].set(...)
pat = re.compile(
    r'^(\s*)self\.([A-Za-z_][A-Za-z0-9_]*_vars)\[(["\'][^"\']+["\'])\]\.set\((.*)\)\s*$'
)

for raw in sys.argv[1:]:
    p = Path(raw)
    text = p.read_text(encoding='utf-8')
    lines = text.splitlines()
    out = []
    changed = 0

    for line in lines:
        m = pat.match(line)
        if not m:
            out.append(line)
            continue
        indent, attr, key, expr = m.groups()
        # Avoid double-patching lines already nested under a guard by checking
        # only the current line; generated .set line itself still matches, so
        # inspect previous output line too.
        if out and f"hasattr(self, '{attr}')" in out[-1]:
            out.append(line)
            continue
        out.append(f"{indent}if hasattr(self, '{attr}') and {key} in getattr(self, '{attr}', {{}}):")
        out.append(f"{indent}    self.{attr}[{key}].set({expr})")
        changed += 1

    if changed:
        p.write_text('\n'.join(out) + ('\n' if text.endswith('\n') else ''), encoding='utf-8')
    print(f"{p.name}: {changed} Legacy-Var-Zugriffe abgesichert")
PY

python3 -m py_compile "${FILES[@]}"

echo "PPH 6 Legacy-Snapshot-Hotfix erfolgreich installiert."
echo "Backups: *.bak-pph6-legacy-$STAMP"
echo "Jetzt: cd $ROOT && ./start_pph_hub.sh"
