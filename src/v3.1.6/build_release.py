#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v3.1.5/pph-update-3.1.5-ui-update-fix.tar.gz'
WORK=Path('/tmp/pph316'); PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v3.1.6'; OUT=OUT_DIR/'pph-update-3.1.6-direct-from-313.tar.gz'
def sha256(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
if WORK.exists(): shutil.rmtree(WORK)
WORK.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(WORK)
(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\n\nVERSION = "3.1.6"\nCHANNEL = "stable"\nBUILD_NAME = "PPH 3.1.6 · Direct Upgrade Fix"\nSCHEMA_VERSION = 3\n',encoding='utf-8')
test=PAYLOAD/'test_upgrade_316.py'
test.write_text('''from pathlib import Path\nROOT=Path(__file__).resolve().parent\nui=(ROOT/"pph_hub/pph3_ui.py").read_text(encoding="utf-8")\nap=(ROOT/"pph_hub/access_point.py").read_text(encoding="utf-8")\nassert 'controls.place(relx=1.0' in ui\nassert 'fresh_stable_version' in ui\nassert 'mt7921u' in ap\nassert (ROOT/'fieldctl.py').exists()\nassert (ROOT/'install_field_mode.sh').exists()\nprint("PPH 3.1.6 tests OK")\n''',encoding='utf-8')
subprocess.run(['python3','-m','py_compile',str(PAYLOAD/'pph_hub/pph3_ui.py')],check=True)
subprocess.run(['python3',str(test)],cwd=PAYLOAD,check=True)
for c in PAYLOAD.rglob('__pycache__'): shutil.rmtree(c)
files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
    rel=p.relative_to(PAYLOAD).as_posix(); mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','fieldctl.py','install_field_mode.sh'} else '0644'
    files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'3.1.6','min_version':'3.1.3','max_version':'3.1.5','channel':'stable','build_name':'PPH 3.1.6 · Direct Upgrade Fix','released':'2026-08-10','tests':['test_upgrade_316.py'],'features':['Direktes Upgrade von 3.1.3/3.1.4/3.1.5','PPH 3.1.4 Field Mode vollständig enthalten','PPH 3.1.5 Fullscreen-Topbar-Fix enthalten','Fresh Update Check ohne alten Cache','Neuer eindeutiger Paketname verhindert alte 3.1.5-Datei'],'files':files}
(WORK/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
OUT_DIR.mkdir(parents=True,exist_ok=True)
with tarfile.open(OUT,'w:gz') as tf: tf.add(WORK/'manifest.json',arcname='manifest.json'); tf.add(PAYLOAD,arcname='payload')
package_sha=sha256(OUT)
(OUT_DIR/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT_DIR/'sha256.txt').write_text(f'{package_sha}  {OUT.name}\n',encoding='utf-8')
stable={'product':'pph-funktest','channel':'stable','version':'3.1.6','released':'2026-08-10','build_name':'PPH 3.1.6 · Direct Upgrade Fix','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v3.1.6/pph-update-3.1.6-direct-from-313.tar.gz','sha256':package_sha,'min_version':'3.1.3','max_version':'3.1.5','notes':['Direkt von 3.1.3 installierbar','Field Mode enthalten','Fullscreen/UI Fix enthalten','Fresh Update Check enthalten','neuer Paketname gegen stale cache']}
(ROOT/'channels/stable.json').write_text(json.dumps(stable,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Built {OUT} sha256={package_sha}')
