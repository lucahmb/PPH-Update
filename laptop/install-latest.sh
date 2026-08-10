#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
from pathlib import Path
import urllib.request, py_compile, os

VERSION = '6.0.2'
home = Path.home()
base = home / '.local/share/pph-ap-control'
bin_dir = home / '.local/bin'
apps = home / '.local/share/applications'
target = base / 'pph_ap_control.py'
launchers = [bin_dir / 'pph-ap-control', bin_dir / 'pph-app-control']

for p in (base, bin_dir, apps):
    p.mkdir(parents=True, exist_ok=True)

for p in launchers:
    try:
        if p.is_symlink() or p.exists():
            p.unlink()
    except FileNotFoundError:
        pass

if target.is_symlink():
    target.unlink()

url = 'https://api.github.com/repos/lucahmb/PPH-Update/contents/laptop/v6.0.2/pph_ap_control.py?ref=main'
req = urllib.request.Request(url, headers={
    'User-Agent': 'PPH-App-Control-Installer',
    'Accept': 'application/vnd.github.raw+json',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
})
with urllib.request.urlopen(req, timeout=20) as r:
    data = r.read()

text = data.decode('utf-8')
if not text.startswith('#!/usr/bin/env python3'):
    raise SystemExit('Download ungültig: keine Python-Datei erhalten')
if "VERSION='6.0.2'" not in text:
    raise SystemExit('Downloadprüfung fehlgeschlagen: falsche Version')
if 'X-PPH-Token' not in text or 'DEFAULT_PORT=8788' not in text:
    raise SystemExit('Downloadprüfung fehlgeschlagen: AP-API-Fix fehlt')

tmp = target.with_suffix('.py.tmp')
if tmp.exists() or tmp.is_symlink():
    tmp.unlink()
tmp.write_bytes(data)
tmp.chmod(0o755)
py_compile.compile(str(tmp), doraise=True)
os.replace(tmp, target)

launcher = f'#!/usr/bin/env bash\nexec python3 "{target}" "$@"\n'
for p in launchers:
    p.write_text(launcher, encoding='utf-8')
    p.chmod(0o755)

(apps / 'pph-ap-control.desktop').write_text(
    f'[Desktop Entry]\nName=PPH App Control {VERSION}\nComment=PPH Field Router Controller\nExec={launchers[0]}\nTerminal=false\nType=Application\nCategories=Network;Utility;\n',
    encoding='utf-8',
)

final = target.read_text(encoding='utf-8')
if not final.startswith('#!/usr/bin/env python3') or "VERSION='6.0.2'" not in final or 'X-PPH-Token' not in final or 'DEFAULT_PORT=8788' not in final:
    raise SystemExit('Installationsprüfung fehlgeschlagen: Zieldatei beschädigt')
for p in launchers:
    if os.path.samefile(target, p):
        raise SystemExit(f'Installationsprüfung fehlgeschlagen: {p} zeigt auf Controller-Datei')

print('PPH App Control 6.0.2 installiert und verifiziert.')
print('AP API: Port 8788 · X-PPH-Token · /status /start /stop')
print('Start: pph-ap-control oder pph-app-control')
PY
