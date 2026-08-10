#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
from pathlib import Path
import urllib.request, py_compile

VERSION = '6.0.1'
home = Path.home()
base = home / '.local/share/pph-ap-control'
bin_dir = home / '.local/bin'
apps = home / '.local/share/applications'
target = base / 'pph_ap_control.py'

for p in (base, bin_dir, apps):
    p.mkdir(parents=True, exist_ok=True)

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
tmp.write_bytes(data)
tmp.chmod(0o755)
py_compile.compile(str(tmp), doraise=True)
tmp.replace(target)

launcher = f'''#!/usr/bin/env bash\nexec python3 "{target}" "$@"\n'''
for name in ('pph-ap-control', 'pph-app-control'):
    p = bin_dir / name
    p.write_text(launcher, encoding='utf-8')
    p.chmod(0o755)

(apps / 'pph-ap-control.desktop').write_text(
    f'''[Desktop Entry]\nName=PPH App Control {VERSION}\nComment=PPH Field Router Controller\nExec={bin_dir / 'pph-ap-control'}\nTerminal=false\nType=Application\nCategories=Network;Utility;\n''',
    encoding='utf-8',
)

final = target.read_text(encoding='utf-8')
if not final.startswith('#!/usr/bin/env python3') or "VERSION='6.0.1'" not in final or 'msg=str(e)' not in final:
    raise SystemExit('Installationsprüfung fehlgeschlagen: Zieldatei beschädigt')

print('PPH App Control 6.0.1 installiert und verifiziert.')
print('Start: pph-ap-control oder pph-app-control')
print('Controller:', target)
print('Launcher:', bin_dir / 'pph-ap-control')
PY
