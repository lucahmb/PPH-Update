#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, shutil, tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v5.0.3/pph-update-5.0.3-bottom-nav-fix.tar.gz'
WORK=Path('/tmp/pph504'); EXTRACT=WORK/'extract'; PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v5.0.4'; OUT=OUT_DIR/'pph-update-5.0.4-startup-nav-fix.tar.gz'

def sha256(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
if WORK.exists(): shutil.rmtree(WORK)
EXTRACT.mkdir(parents=True); PAYLOAD.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(EXTRACT)
# 5.0.3 uses updater-compatible root manifest + payload/ layout.
src=EXTRACT/'payload'
if not src.is_dir(): raise SystemExit('payload/ missing in 5.0.3')
for item in src.iterdir():
    dst=PAYLOAD/item.name
    shutil.copytree(item,dst) if item.is_dir() else shutil.copy2(item,dst)

# Guard legacy pph3 navigation against destroyed widgets.
p3=PAYLOAD/'pph_hub/pph3_ui.py'
t=p3.read_text(encoding='utf-8')
old='''        for target, button in getattr(self, "pph30_nav_buttons", {}).items():\n            selected = target == active\n            button.configure(bg=CYAN if selected else SURFACE2, fg=BG if selected else TEXT)'''
new='''        dead = []\n        for target, button in list(getattr(self, "pph30_nav_buttons", {}).items()):\n            try:\n                if not int(button.winfo_exists()):\n                    dead.append(target)\n                    continue\n                selected = target == active\n                button.configure(bg=CYAN if selected else SURFACE2, fg=BG if selected else TEXT)\n            except Exception:\n                dead.append(target)\n        for target in dead:\n            try:\n                self.pph30_nav_buttons.pop(target, None)\n            except Exception:\n                pass'''
if old not in t: raise SystemExit('pph3 update_nav block not found')
p3.write_text(t.replace(old,new,1),encoding='utf-8')

# Ensure 5.0 cleanup drops stale references before destroying old buttons.
p50=PAYLOAD/'pph_hub/pph50_platform.py'
s=p50.read_text(encoding='utf-8')
needle='''        for b in getattr(self,'pph30_nav_buttons',{}).values():\n            try:b.destroy()\n            except Exception:pass'''
replacement='''        old_nav = getattr(self, 'pph30_nav_buttons', {})\n        for b in list(old_nav.values()):\n            try:b.destroy()\n            except Exception:pass\n        try: old_nav.clear()\n        except Exception: pass'''
if needle in s: s=s.replace(needle,replacement,1)
p50.write_text(s,encoding='utf-8')

(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\nVERSION="5.0.4"\nCHANNEL="stable"\nBUILD_NAME="PPH 5.0.4 · Startup Navigation Fix"\nSCHEMA_VERSION=5\n',encoding='utf-8')
files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
    rel=p.relative_to(PAYLOAD).as_posix(); mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','fieldctl.py','fielddctl.py','install_field_mode.sh'} else '0644'
    files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'5.0.4','min_version':'5.0.3','max_version':'5.0.3','channel':'stable','build_name':'PPH 5.0.4 · Startup Navigation Fix','released':'2026-08-10','features':['Fix TclError from destroyed legacy nav buttons','Clear stale pph30_nav_buttons references','Retain bottom navigation overlay fix','Full PPH 5.0 Field Platform retained'],'files':files}
OUT_DIR.mkdir(parents=True,exist_ok=True)
mp=WORK/'manifest.json'; mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
with tarfile.open(OUT,'w:gz') as tf:
    tf.add(mp,arcname='manifest.json')
    for p in sorted(PAYLOAD.rglob('*')): tf.add(p,arcname='payload/'+p.relative_to(PAYLOAD).as_posix())
with tarfile.open(OUT,'r:gz') as tf:
    names=set(tf.getnames()); req={'manifest.json','payload/pph_hub/pph3_ui.py','payload/pph_hub/pph50_platform.py','payload/pph_version.py'}
    miss=req-names
    if miss: raise SystemExit('missing '+','.join(sorted(miss)))
(OUT_DIR/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
channel={'product':'pph-funktest','channel':'stable','version':'5.0.4','released':'2026-08-10','build_name':'PPH 5.0.4 · Startup Navigation Fix','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v5.0.4/pph-update-5.0.4-startup-nav-fix.tar.gz','sha256':sha256(OUT),'min_version':'5.0.3','max_version':'5.0.3','notes':['Fix startup TclError invalid command name','Clear destroyed legacy nav references','Keep FIELD INTERFACE bottom-nav fix']}
(ROOT/'channels/stable.json').write_text(json.dumps(channel,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(OUT)
