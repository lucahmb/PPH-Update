#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v5.1.3/pph-update-5.1.3-launcher-false-positive-fix.tar.gz'
WORK=Path('/tmp/pph520'); EXTRACT=WORK/'extract'; PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v5.2.0'; OUT=OUT_DIR/'pph-update-5.2.0-touch-hub-redesign.tar.gz'

def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if WORK.exists(): shutil.rmtree(WORK)
EXTRACT.mkdir(parents=True); PAYLOAD.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(EXTRACT)
source=EXTRACT/'payload'
if not source.is_dir(): raise SystemExit('5.1.3 payload directory missing')
for item in source.iterdir():
    dest=PAYLOAD/item.name
    if item.is_dir(): shutil.copytree(item,dest)
    else: shutil.copy2(item,dest)

launcher=PAYLOAD/'start_pph_hub.sh'
ui=PAYLOAD/'pph_hub/pph51_ui.py'
shutil.copy2(ROOT/'src/v5.2.0/pph52_ui.py',ui)

(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\nVERSION="5.2.0"\nCHANNEL="stable"\nBUILD_NAME="PPH 5.2.0 · Touch Hub Redesign"\nSCHEMA_VERSION=5\n',encoding='utf-8')

test_file=PAYLOAD/'test_ui_520.py'
test_file.write_text("""from pathlib import Path
R=Path(__file__).resolve().parent
t=(R/'pph_hub/pph51_ui.py').read_text(encoding='utf-8')
v=(R/'pph_version.py').read_text(encoding='utf-8')
for x in ('PPH 5.2 · TOUCH HUB','more52','ALLE KATEGORIEN','MESSUNG STARTEN','GERAET','menu_tile','badge.after(850'):
    assert x in t
assert 'VERSION="5.2.0"' in v
print('PPH 5.2.0 touch hub tests OK')
""",encoding='utf-8')

subprocess.run(['bash','-n',str(launcher)],check=True)
subprocess.run(['python3','-m','py_compile',str(ui),str(PAYLOAD/'pph_version.py')],check=True)
subprocess.run(['python3',str(test_file)],cwd=PAYLOAD,check=True)
for c in PAYLOAD.rglob('__pycache__'): shutil.rmtree(c)

files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
    rel=p.relative_to(PAYLOAD).as_posix(); mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','fieldctl.py','fielddctl.py','install_field_mode.sh'} else '0644'
    files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'5.2.0','min_version':'5.1.3','max_version':'5.1.3','channel':'stable','build_name':'PPH 5.2.0 · Touch Hub Redesign','released':'2026-08-10','tests':['test_ui_520.py'],'features':['Redesigned 800x480 Raspberry Pi 5-inch Touch Hub','Six primary navigation areas: Home, Funk, Netz, AP, Geraet, Mehr','New category hub for radios, reports, tools, history, system and field workflows','Larger touch targets with press feedback and hover highlights','Animated live status badge in page headers','Backend and launcher behavior inherited from 5.1.3'],'files':files}
OUT_DIR.mkdir(parents=True,exist_ok=True)
mp=WORK/'manifest.json'; mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
with tarfile.open(OUT,'w:gz') as tf:
    tf.add(mp,arcname='manifest.json')
    for p in sorted(PAYLOAD.rglob('*')): tf.add(p,arcname='payload/'+p.relative_to(PAYLOAD).as_posix())
with tarfile.open(OUT,'r:gz') as tf:
    names=set(tf.getnames())
    req={'manifest.json','payload/start_pph_hub.sh','payload/pph_version.py','payload/pph_hub/pph51_ui.py','payload/test_ui_520.py'}
    miss=sorted(req-names)
    if miss: raise SystemExit('Archive invalid: '+', '.join(miss))
(OUT_DIR/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
channel={'product':'pph-funktest','channel':'stable','version':'5.2.0','released':'2026-08-10','build_name':'PPH 5.2.0 · Touch Hub Redesign','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v5.2.0/pph-update-5.2.0-touch-hub-redesign.tar.gz','sha256':sha256(OUT),'min_version':'5.1.3','max_version':'5.1.3','notes':['Redesigned 5-inch Raspberry Pi touch hub','Clear six-area navigation with a dedicated category hub','Larger touch controls and animated visual feedback','Keeps the 5.1.3 launcher fix and existing backend behavior']}
(ROOT/'channels/stable.json').write_text(json.dumps(channel,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(OUT)
