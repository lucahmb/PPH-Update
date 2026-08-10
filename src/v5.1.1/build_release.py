#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v5.1.0/pph-update-5.1.0-wireless-style-ui.tar.gz'
WORK=Path('/tmp/pph511'); EXTRACT=WORK/'extract'; PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v5.1.1'; OUT=OUT_DIR/'pph-update-5.1.1-access-point-flow-fix.tar.gz'

def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if WORK.exists(): shutil.rmtree(WORK)
EXTRACT.mkdir(parents=True); PAYLOAD.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(EXTRACT)
source=EXTRACT/'payload'
if not source.is_dir(): raise SystemExit('5.1.0 payload directory missing')
for item in source.iterdir():
    dest=PAYLOAD/item.name
    if item.is_dir(): shutil.copytree(item,dest)
    else: shutil.copy2(item,dest)

# Bug fix 1: the Access Point status dict never carried the pairing code, so the
# 5.1 UI's "PAIRING CODE" card always showed "-" (pph51_ui.py checks
# status()["pairing_code"]/["token"]/["code"]/["access_code"], none of which existed).
ap=PAYLOAD/'pph_hub/access_point.py'
if ap.exists():
    t=ap.read_text(encoding='utf-8')
    old='"ap_ip":"10.42.0.1", "field_mode":Path("/usr/local/libexec/pph-ap-fieldctl").exists()'
    new='"ap_ip":"10.42.0.1", "pairing_code":self.token, "field_mode":Path("/usr/local/libexec/pph-ap-fieldctl").exists()'
    if old not in t: raise SystemExit('access_point.py: status dict anchor not found')
    if new not in t: t=t.replace(old,new,1)
    ap.write_text(t,encoding='utf-8')

# Bug fix 2: Connection Flow read status["internet_ok"] (a key that never existed;
# AccessPointController.status() exposes "internet"), so the INTERNET tile always
# defaulted to True/"ONLINE" regardless of the real uplink state.
platform=PAYLOAD/'pph_hub/pph50_platform.py'
if platform.exists():
    t=platform.read_text(encoding='utf-8')
    old="s.get('internet_ok',True)"
    new="s.get('internet',False)"
    if old not in t: raise SystemExit('pph50_platform.py: internet_ok anchor not found')
    t=t.replace(old,new,1)
    platform.write_text(t,encoding='utf-8')

# Bug fix 3: the PPH 4.2 "REPORTS" text panel calls json.dumps() without importing
# json, raising a NameError that was silently swallowed and shown as an error string.
full_ui=PAYLOAD/'pph_hub/pph42_full_ui.py'
if full_ui.exists():
    t=full_ui.read_text(encoding='utf-8')
    old='import os,subprocess,tkinter as tk'
    new='import json,os,subprocess,tkinter as tk'
    if old not in t: raise SystemExit('pph42_full_ui.py: import anchor not found')
    if 'import json' not in t: t=t.replace(old,new,1)
    full_ui.write_text(t,encoding='utf-8')

(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\nVERSION="5.1.1"\nCHANNEL="stable"\nBUILD_NAME="PPH 5.1.1 · Access Point + Connection Flow Fix"\nSCHEMA_VERSION=5\n',encoding='utf-8')

test_file=PAYLOAD/'test_access_point_511.py'
shutil.copy2(ROOT/'src/v5.1.1/test_access_point_511.py',test_file)

subprocess.run(['python3','-m','py_compile',str(ap),str(platform),str(full_ui),str(PAYLOAD/'pph_version.py')],check=True)
subprocess.run(['python3',str(test_file)],cwd=PAYLOAD,check=True)
for c in PAYLOAD.rglob('__pycache__'): shutil.rmtree(c)

files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
    rel=p.relative_to(PAYLOAD).as_posix(); mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','fieldctl.py','fielddctl.py','install_field_mode.sh'} else '0644'
    files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'5.1.1','min_version':'5.1.0','max_version':'5.1.0','channel':'stable','build_name':'PPH 5.1.1 · Access Point + Connection Flow Fix','released':'2026-08-10','features':['Fix: Access Point pairing code now shown on the ACCESS card (status() was missing the pairing_code field)','Fix: Connection Flow INTERNET tile read a nonexistent internet_ok key and always showed ONLINE','Fix: PPH 4.2 REPORTS panel missing json import (NameError swallowed and shown as error text)'],'files':files}
OUT_DIR.mkdir(parents=True,exist_ok=True)
mp=WORK/'manifest.json'; mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
with tarfile.open(OUT,'w:gz') as tf:
    tf.add(mp,arcname='manifest.json')
    for p in sorted(PAYLOAD.rglob('*')): tf.add(p,arcname='payload/'+p.relative_to(PAYLOAD).as_posix())
with tarfile.open(OUT,'r:gz') as tf:
    names=set(tf.getnames())
    req={'manifest.json','payload/pph_hub/access_point.py','payload/pph_hub/pph50_platform.py','payload/pph_hub/pph42_full_ui.py','payload/pph_version.py'}
    miss=sorted(req-names)
    if miss: raise SystemExit('Archive invalid: '+', '.join(miss))
(OUT_DIR/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
channel={'product':'pph-funktest','channel':'stable','version':'5.1.1','released':'2026-08-10','build_name':'PPH 5.1.1 · Access Point + Connection Flow Fix','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v5.1.1/pph-update-5.1.1-access-point-flow-fix.tar.gz','sha256':sha256(OUT),'min_version':'5.1.0','max_version':'5.1.0','notes':['Access Point pairing code now populated on the ACCESS card','Connection Flow INTERNET tile reflects the real uplink state','PPH 4.2 legacy REPORTS panel no longer errors on missing json import']}
(ROOT/'channels/stable.json').write_text(json.dumps(channel,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(OUT)
