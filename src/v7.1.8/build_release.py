#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v7.1.7/pph-update-7.1.7-boot-intro-connector-fix.tar.gz'
WORK=Path('/tmp/pph718'); EXTRACT=WORK/'extract'; PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v7.1.8'; OUT=OUT_DIR/'pph-update-7.1.8-ap-progress-screen.tar.gz'

def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if WORK.exists(): shutil.rmtree(WORK)
EXTRACT.mkdir(parents=True); PAYLOAD.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(EXTRACT)
source=EXTRACT/'payload'
if not source.is_dir(): raise SystemExit('7.1.7 payload directory missing')
for item in source.iterdir():
    dest=PAYLOAD/item.name
    if item.is_dir(): shutil.copytree(item,dest)
    else: shutil.copy2(item,dest)

# 7.1.8: animated Access Point start/stop progress screen. ap_start()/
# ap_stop() previously just fired a toast and a background "refresh burst"
# (a few blind refreshes at fixed delays) - no feedback while the AP was
# actually coming up or down. New ap_progress() overlay shows a live
# progress bar + checklist (command sent / interface / network state)
# driven by AccessPointController.status() polled every 500ms, with real
# data (SSID, band, interface, AP IP) filled in as it becomes available -
# not a fixed-duration animation, it stays open exactly until the real
# state (active/inactive) is reached, with a ~20s timeout fallback.
# Verified with a dedicated Tk-mainloop test that fires the real START/STOP
# canvas-button callbacks against a fake AccessPointController and confirms
# the overlay opens, polls, and closes on both paths - ui_smoke_test.py
# alone doesn't exercise button callbacks so this needed its own check.
ui=PAYLOAD/'pph_hub/pph71_ui.py'
shutil.copy2(ROOT/'src/v7.1.8/pph71_ui.py', ui)

launcher=PAYLOAD/'pph_hub/pph3_app.py'
(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\nVERSION="7.1.8"\nCHANNEL="stable"\nBUILD_NAME="PPH 7.1.8 · Access Point Progress Screen"\nSCHEMA_VERSION=7\n',encoding='utf-8')

subprocess.run(['python3','-m','py_compile',str(ui),str(launcher),str(PAYLOAD/'pph_version.py')],check=True)
for c in PAYLOAD.rglob('__pycache__'): shutil.rmtree(c)

smoke=ROOT/'tools/ui_smoke_test.py'
result=subprocess.run(['xvfb-run','-a','python3',str(smoke),str(PAYLOAD),'pph_hub/pph71_ui.py'])
if result.returncode!=0:
    raise SystemExit('ui_smoke_test failed - refusing to package a UI that does not render.')
for c in PAYLOAD.rglob('__pycache__'): shutil.rmtree(c)

files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
    rel=p.relative_to(PAYLOAD).as_posix()
    mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','fieldctl.py','fielddctl.py','install_field_mode.sh','boot_intro/install.sh','boot_intro/test-rotation.sh'} else '0644'
    files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'7.1.8','min_version':'7.1.0','max_version':'7.1.7','channel':'stable','build_name':'PPH 7.1.8 · Access Point Progress Screen','released':'2026-08-12','ui_module':'pph_hub/pph71_ui.py','features':[
    'New: animated Access Point start/stop progress screen with live checklist (command sent / interface / network state) and progress bar',
    'Driven by real AccessPointController.status() polling every 500ms - shows real SSID/band/interface/AP-IP as they become available, not placeholder text',
    'Stays open exactly until the AP is actually active (start) or actually inactive (stop), not a fixed duration - ~20s timeout fallback shows a warning instead of hanging forever',
    'No boot-intro or backend changes - carries forward 7.1.7 unchanged otherwise',
], 'files':files}
OUT_DIR.mkdir(parents=True,exist_ok=True)
mp=WORK/'manifest.json'; mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
with tarfile.open(OUT,'w:gz') as tf:
    tf.add(mp,arcname='manifest.json')
    for p in sorted(PAYLOAD.rglob('*')): tf.add(p,arcname='payload/'+p.relative_to(PAYLOAD).as_posix())
with tarfile.open(OUT,'r:gz') as tf:
    names=set(tf.getnames())
    req={'manifest.json','payload/pph_hub/pph71_ui.py','payload/pph_hub/pph3_app.py','payload/pph_version.py'}
    miss=sorted(req-names)
    if miss: raise SystemExit('Archive invalid: '+', '.join(miss))
(OUT_DIR/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
channel={'product':'pph-funktest','channel':'stable','version':'7.1.8','released':'2026-08-12','build_name':'PPH 7.1.8 · Access Point Progress Screen','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v7.1.8/pph-update-7.1.8-ap-progress-screen.tar.gz','sha256':sha256(OUT),'min_version':'7.1.0','max_version':'7.1.7','notes':['New: animated Access Point start/stop screen with live real-data checklist and progress bar, stays open until the AP is actually up/down','No boot-intro changes in this release']}
(ROOT/'channels/stable.json').write_text(json.dumps(channel,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(OUT)
