#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; BASE=ROOT/'packages/v4.2.0/pph-update-4.2.0-full-ui-rewrite.tar.gz'; WORK=Path('/tmp/pph500'); PAYLOAD=WORK/'payload'; OUT_DIR=ROOT/'packages/v5.0.0'; OUT=OUT_DIR/'pph-update-5.0.0-field-platform.tar.gz'
def sha256(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if WORK.exists():shutil.rmtree(WORK)
WORK.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf:tf.extractall(WORK)
shutil.copy2(ROOT/'src/v5.0.0/pph50_platform.py',PAYLOAD/'pph_hub/pph50_platform.py')
launcher=PAYLOAD/'pph_hub/pph3_app.py';t=launcher.read_text()
if 'install50' not in t:t=t.replace('if __name__ == "__main__":','from pph50_platform import install as install50\ninstall50(hub.PolishedPPHApp, vars(hub))\n\nif __name__ == "__main__":',1)
launcher.write_text(t)
(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\nVERSION="5.0.0"\nCHANNEL="stable"\nBUILD_NAME="PPH 5.0.0 · Field Platform"\nSCHEMA_VERSION=5\n')
subprocess.run(['python3','-m','py_compile',str(PAYLOAD/'pph_hub/pph50_platform.py'),str(launcher)],check=True)
for c in PAYLOAD.rglob('__pycache__'):shutil.rmtree(c)
files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
 rel=p.relative_to(PAYLOAD).as_posix();files.append({'path':rel,'sha256':sha256(p),'mode':'0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','fieldctl.py','install_field_mode.sh'} else '0644'})
manifest={'format':1,'product':'pph-funktest','version':'5.0.0','min_version':'4.2.0','max_version':'4.2.0','channel':'stable','build_name':'PPH 5.0.0 · Field Platform','released':'2026-08-10','features':['Legacy bottom navigation cleanup','Field Mode','Connection Flow','Before/After measurement','Session Recorder','Notification Center','PPH 4.2 full UI retained'],'files':files}
(PAYLOAD/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n');OUT_DIR.mkdir(parents=True,exist_ok=True)
with tarfile.open(OUT,'w:gz') as tf:
 for p in sorted(PAYLOAD.rglob('*')):tf.add(p,arcname=p.relative_to(PAYLOAD))
channel={'product':'pph-funktest','channel':'stable','version':'5.0.0','released':'2026-08-10','build_name':'PPH 5.0.0 · Field Platform','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v5.0.0/pph-update-5.0.0-field-platform.tar.gz','sha256':sha256(OUT),'min_version':'4.2.0','max_version':'4.2.0','notes':['Legacy bottom cards removed','Field Mode + Connection Flow','Before/After measurement','Session Recorder + Notifications']}
(OUT_DIR/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n');(ROOT/'channels/stable.json').write_text(json.dumps(channel,indent=2,ensure_ascii=False)+'\n');print(OUT)
