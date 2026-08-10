#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
from pathlib import Path
import urllib.request, py_compile, os

VERSION = '6.0.1'
home = Path.home()
base = home / '.local/share/pph-ap-control'
bin_dir = home / '.local/bin'
apps = home / '.local/share/applications'
target = base / 'pph_ap_control.py'
launchers = [bin_dir / 'pph-ap-control', bin_dir / 'pph-app-control']

for p in (base, bin_dir, apps):
    p.mkdir(parents=True, exist_ok=True)

# Remove legacy symlink/hardlink launchers before touching the controller.
# Older installs could link ~/.local/bin/pph-ap-control directly to the Python file,
# which caused writing the launcher to overwrite the controller itself.
for p in launchers:
    try:
        if p.is_symlink() or p.exists():
            p.unlink()
    except FileNotFoundError:
        pass

# If the controller itself is a symlink, remove it too and recreate as a real file.
if target.is_symlink():
    target.unlink()

url = 'https://api.github.com/repos/lucahmb/PPH-Update/contents/laptop/v6.0.1/pph_ap_control.py?ref=main'
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
if "VERSION='6.0.1'" not in text:
    raise SystemExit('Downloadprüfung fehlgeschlagen: falsche Version')
if 'msg=str(e)' not in text:
    raise SystemExit('Downloadprüfung fehlgeschlagen: Python-3.13-Fix fehlt')

# Atomic write of the Python controller.
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

# Verify controller and launchers are physically distinct files.
final = target.read_text(encoding='utf-8')
if not final.startswith('#!/usr/bin/env python3') or "VERSION='6.0.1'" not in final or 'msg=str(e)' not in final:
    raise SystemExit('Installationsprüfung fehlgeschlagen: Zieldatei beschädigt')
for p in launchers:
    if os.path.samefile(target, p):
        raise SystemExit(f'Installationsprüfung fehlgeschlagen: {p} zeigt auf Controller-Datei')
    ltxt = p.read_text(encoding='utf-8')
    if not ltxt.startswith('#!/usr/bin/env bash') or 'exec python3' not in ltxt:
        raise SystemExit(f'Installationsprüfung fehlgeschlagen: Launcher beschädigt: {p}')

print('PPH App Control 6.0.1 installiert und verifiziert.')
print('Start: pph-ap-control oder pph-app-control')
print('Controller:', target)
print('Launcher:', launchers[0])
PY
