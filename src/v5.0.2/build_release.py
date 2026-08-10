#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, shutil, subprocess, tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'packages/v5.0.0/pph-update-5.0.0-field-platform.tar.gz'
WORK = Path('/tmp/pph502')
EXTRACT = WORK / 'extract'
PAYLOAD = WORK / 'payload'
OUT_DIR = ROOT / 'packages/v5.0.2'
OUT = OUT_DIR / 'pph-update-5.0.2-archive-layout-hotfix.tar.gz'

def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

if WORK.exists():
    shutil.rmtree(WORK)
EXTRACT.mkdir(parents=True)
PAYLOAD.mkdir(parents=True)

with tarfile.open(BASE, 'r:gz') as tf:
    tf.extractall(EXTRACT)

# 5.0.0 was packaged flat. Locate its actual payload root robustly.
candidates = [p.parent for p in EXTRACT.rglob('pph_version.py') if (p.parent / 'pph_hub').is_dir()]
if not candidates:
    raise SystemExit('Could not locate PPH payload root in 5.0.0 package')
src = candidates[0]
for item in src.iterdir():
    if item.name == 'manifest.json':
        continue
    dest = PAYLOAD / item.name
    if item.is_dir():
        shutil.copytree(item, dest)
    else:
        shutil.copy2(item, dest)

fieldctl = PAYLOAD / 'fieldctl.py'
if not fieldctl.exists():
    raise SystemExit('fieldctl.py missing from recovered 5.0.0 payload')

# Compatibility alias for the typo seen in some old paths.
(PAYLOAD / 'fielddctl.py').write_text(
    "#!/usr/bin/env python3\nfrom pathlib import Path\nimport runpy\nrunpy.run_path(str(Path(__file__).with_name('fieldctl.py')), run_name='__main__')\n",
    encoding='utf-8',
)

(PAYLOAD / 'pph_version.py').write_text(
    'from __future__ import annotations\nVERSION="5.0.2"\nCHANNEL="stable"\nBUILD_NAME="PPH 5.0.2 · Archive Layout Hotfix"\nSCHEMA_VERSION=5\n',
    encoding='utf-8',
)

subprocess.run(['python3', '-m', 'py_compile', str(PAYLOAD / 'fielddctl.py'), str(PAYLOAD / 'pph_hub/pph3_app.py')], check=True)
for c in PAYLOAD.rglob('__pycache__'):
    shutil.rmtree(c)

files = []
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
    rel = p.relative_to(PAYLOAD).as_posix()
    mode = '0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','fieldctl.py','fielddctl.py','install_field_mode.sh'} else '0644'
    files.append({'path': rel, 'sha256': sha256(p), 'mode': mode})

manifest = {
    'format': 1,
    'product': 'pph-funktest',
    'version': '5.0.2',
    'min_version': '4.2.0',
    'max_version': '5.0.1',
    'channel': 'stable',
    'build_name': 'PPH 5.0.2 · Archive Layout Hotfix',
    'released': '2026-08-10',
    'features': [
        'Full PPH 5.0 Field Platform',
        'Updater-compatible payload/ archive layout',
        'fieldctl.py guaranteed under payload/',
        'fielddctl.py compatibility alias',
        'Tar member validation before publish',
    ],
    'files': files,
}

OUT_DIR.mkdir(parents=True, exist_ok=True)
manifest_path = WORK / 'manifest.json'
manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

# IMPORTANT: updater expects manifest.json at root and every file under payload/.
with tarfile.open(OUT, 'w:gz') as tf:
    tf.add(manifest_path, arcname='manifest.json')
    for p in sorted(PAYLOAD.rglob('*')):
        tf.add(p, arcname='payload/' + p.relative_to(PAYLOAD).as_posix())

with tarfile.open(OUT, 'r:gz') as tf:
    names = set(tf.getnames())
    required = {
        'manifest.json',
        'payload/fieldctl.py',
        'payload/fielddctl.py',
        'payload/pph_version.py',
        'payload/pph_hub/pph3_app.py',
        'payload/pph_hub/pph50_platform.py',
    }
    missing = sorted(required - names)
    if missing:
        raise SystemExit('Archive layout invalid, missing: ' + ', '.join(missing))

(OUT_DIR / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
channel = {
    'product': 'pph-funktest',
    'channel': 'stable',
    'version': '5.0.2',
    'released': '2026-08-10',
    'build_name': 'PPH 5.0.2 · Archive Layout Hotfix',
    'repository': 'lucahmb/PPH-Update',
    'package_url': 'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v5.0.2/pph-update-5.0.2-archive-layout-hotfix.tar.gz',
    'sha256': sha256(OUT),
    'min_version': '4.2.0',
    'max_version': '5.0.1',
    'notes': [
        'Fix updater archive layout: payload/...',
        'Fix missing payload/fieldctl.py error',
        'Full PPH 5.0 Field Platform retained',
    ],
}
(ROOT / 'channels/stable.json').write_text(json.dumps(channel, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(OUT)
