#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v5.2.1/pph-update-5.2.1-startup-crash-fix.tar.gz'
WORK=Path('/tmp/pph522'); EXTRACT=WORK/'extract'; PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v5.2.2'; OUT=OUT_DIR/'pph-update-5.2.2-deep-page-redesign.tar.gz'

def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if WORK.exists(): shutil.rmtree(WORK)
EXTRACT.mkdir(parents=True); PAYLOAD.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(EXTRACT)
source=EXTRACT/'payload'
if not source.is_dir(): raise SystemExit('5.2.1 payload directory missing')
for item in source.iterdir():
    dest=PAYLOAD/item.name
    if item.is_dir(): shutil.copytree(item,dest)
    else: shutil.copy2(item,dest)

ui=PAYLOAD/'pph_hub/pph51_ui.py'
shutil.copy2(ROOT/'src/v5.2.0/pph52_ui.py',ui)

(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\nVERSION="5.2.2"\nCHANNEL="stable"\nBUILD_NAME="PPH 5.2.2 · Deep Page Redesign"\nSCHEMA_VERSION=5\n',encoding='utf-8')

test_file=PAYLOAD/'test_ui_522.py'
test_file.write_text("""from pathlib import Path
import py_compile
R=Path(__file__).resolve().parent
ui=R/'pph_hub/pph51_ui.py'
py_compile.compile(str(ui), doraise=True)
t=ui.read_text(encoding='utf-8')
assert \"left.grid(row=0,column=0\" not in t, 'two_cards() must not grid the card frames into an unrelated container'
assert \"left.pack(side='left'\" in t and \"right.pack(side='left'\" in t
for marker in ('visual_page','scanline','p51_visual','HARDWARE','STORAGE','SERVICES','NETWORK DOCTOR','LAN MAPPER','Visuelle PPH 5.2 Detailseite'):
    assert marker in t
assert 'def _release_reset' in t and 'except Exception:pass' in t
print('PPH 5.2.2 deep page redesign tests OK')
""",encoding='utf-8')

subprocess.run(['python3','-m','py_compile',str(ui),str(PAYLOAD/'pph_version.py')],check=True)
subprocess.run(['python3',str(test_file)],cwd=PAYLOAD,check=True)
for c in PAYLOAD.rglob('__pycache__'): shutil.rmtree(c)

files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
    rel=p.relative_to(PAYLOAD).as_posix(); mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','fieldctl.py','fielddctl.py','install_field_mode.sh'} else '0644'
    files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'5.2.2','min_version':'5.2.0','max_version':'5.2.1','channel':'stable','build_name':'PPH 5.2.2 · Deep Page Redesign','released':'2026-08-10','features':['Deep redesign for the pages behind the home screen','Hardware, Storage, Services, Events, Jobs, Reports, Tools, Network Doctor, LAN Mapper and Field detail pages now use visual status layouts instead of plain text pages','Animated scanline on detail pages','Live status hero plus two mini status tiles per detail page','Keeps the 5.2.1 startup crash fix and button hardening'],'files':files}
OUT_DIR.mkdir(parents=True,exist_ok=True)
mp=WORK/'manifest.json'; mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
with tarfile.open(OUT,'w:gz') as tf:
    tf.add(mp,arcname='manifest.json')
    for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
        tf.add(p,arcname='payload/'+p.relative_to(PAYLOAD).as_posix())
with tarfile.open(OUT,'r:gz') as tf:
    names=set(tf.getnames())
    req={'manifest.json','payload/pph_hub/pph51_ui.py','payload/pph_version.py'}
    miss=sorted(req-names)
    if miss: raise SystemExit('Archive invalid: '+', '.join(miss))
(OUT_DIR/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
channel={'product':'pph-funktest','channel':'stable','version':'5.2.2','released':'2026-08-10','build_name':'PPH 5.2.2 · Deep Page Redesign','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v5.2.2/pph-update-5.2.2-deep-page-redesign.tar.gz','sha256':sha256(OUT),'min_version':'5.2.0','max_version':'5.2.1','notes':['Redesigns the boring pages behind Home: System, Hardware, Storage, Services, Events, Jobs, Reports, Tools, Network Doctor, LAN Mapper and Field detail pages','Adds animated scanlines, status heroes and mini status tiles to detail pages','Keeps the 5.2.1 startup crash fix']}
(ROOT/'channels/stable.json').write_text(json.dumps(channel,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(OUT)
