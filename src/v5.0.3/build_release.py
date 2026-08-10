#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v5.0.2/pph-update-5.0.2-archive-layout-hotfix.tar.gz'
WORK=Path('/tmp/pph503'); EXTRACT=WORK/'extract'; PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v5.0.3'; OUT=OUT_DIR/'pph-update-5.0.3-bottom-nav-fix.tar.gz'
def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if WORK.exists(): shutil.rmtree(WORK)
EXTRACT.mkdir(parents=True); PAYLOAD.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(EXTRACT)
src=EXTRACT/'payload'
if not src.is_dir(): raise SystemExit('payload/ missing in 5.0.2 base')
for item in src.iterdir():
    dest=PAYLOAD/item.name
    shutil.copytree(item,dest) if item.is_dir() else shutil.copy2(item,dest)
shutil.copy2(ROOT/'src/v5.0.3/pph50_platform.py',PAYLOAD/'pph_hub/pph50_platform.py')
(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\nVERSION="5.0.3"\nCHANNEL="stable"\nBUILD_NAME="PPH 5.0.3 · Bottom Navigation Fix"\nSCHEMA_VERSION=5\n',encoding='utf-8')
subprocess.run(['python3','-m','py_compile',str(PAYLOAD/'pph_hub/pph50_platform.py'),str(PAYLOAD/'pph_hub/pph3_app.py')],check=True)
for c in PAYLOAD.rglob('__pycache__'): shutil.rmtree(c)
files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
    rel=p.relative_to(PAYLOAD).as_posix(); mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','fieldctl.py','fielddctl.py','install_field_mode.sh'} else '0644'
    files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'5.0.3','min_version':'5.0.2','max_version':'5.0.2','channel':'stable','build_name':'PPH 5.0.3 · Bottom Navigation Fix','released':'2026-08-10','features':['Remove legacy FIELD INTERFACE overlay','Reserve bottom navigation area','Raise active page/navigation after page changes','Full PPH 5.0 Field Platform retained'],'files':files}
OUT_DIR.mkdir(parents=True,exist_ok=True)
mp=WORK/'manifest.json'; mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
with tarfile.open(OUT,'w:gz') as tf:
    tf.add(mp,arcname='manifest.json')
    for p in sorted(PAYLOAD.rglob('*')): tf.add(p,arcname='payload/'+p.relative_to(PAYLOAD).as_posix())
with tarfile.open(OUT,'r:gz') as tf:
    names=set(tf.getnames()); required={'manifest.json','payload/fieldctl.py','payload/pph_hub/pph50_platform.py','payload/pph_version.py'}
    missing=sorted(required-names)
    if missing: raise SystemExit('archive missing: '+', '.join(missing))
(OUT_DIR/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
channel={'product':'pph-funktest','channel':'stable','version':'5.0.3','released':'2026-08-10','build_name':'PPH 5.0.3 · Bottom Navigation Fix','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v5.0.3/pph-update-5.0.3-bottom-nav-fix.tar.gz','sha256':sha256(OUT),'min_version':'5.0.2','max_version':'5.0.2','notes':['Fix FIELD INTERFACE banner covering bottom buttons','Legacy overlay purge','Bottom navigation kept above overlays']}
(ROOT/'channels/stable.json').write_text(json.dumps(channel,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(OUT)
