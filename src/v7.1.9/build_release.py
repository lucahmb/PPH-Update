#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v7.1.8/pph-update-7.1.8-ap-progress-screen.tar.gz'
WORK=Path('/tmp/pph719'); EXTRACT=WORK/'extract'; PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v7.1.9'; OUT=OUT_DIR/'pph-update-7.1.9-cpu-power-menu.tar.gz'

def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if WORK.exists(): shutil.rmtree(WORK)
EXTRACT.mkdir(parents=True); PAYLOAD.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(EXTRACT)
source=EXTRACT/'payload'
if not source.is_dir(): raise SystemExit('7.1.8 payload directory missing')
for item in source.iterdir():
    dest=PAYLOAD/item.name
    if item.is_dir(): shutil.copytree(item,dest)
    else: shutil.copy2(item,dest)

# 7.1.9: two additions to the System pages.
#  - CPU AUSLASTUNG + UPTIME cards on system3 (the existing "CPU" card only
#    ever showed temperature). Usage is sampled without a blocking sleep():
#    each refresh() reads /proc/stat's aggregate cpu line and diffs it
#    against the previous refresh's reading (~2s apart, the page's own
#    LIVE_PAGES interval) instead of doing its own sleep-based measurement,
#    which would freeze the UI thread every refresh.
#  - A POWER section on SETTINGS > (details) with NEUSTART/HERUNTERFAHREN,
#    gated behind a confirm_power() overlay (touch screens have no "oops,
#    undo"), running `systemctl reboot`/`poweroff` in a background thread.
# ui_smoke_test.py only builds/shows pages, never fires button callbacks -
# verified separately with two Tk-mainloop tests: one confirms CPU
# load/uptime populate after two refresh() calls against real /proc/stat,
# the other clicks the real NEUSTART/HERUNTERFAHREN canvas buttons with
# subprocess.run mocked, confirming ABBRECHEN never calls it and
# confirming triggers exactly `systemctl reboot`/`poweroff`.
ui=PAYLOAD/'pph_hub/pph71_ui.py'
shutil.copy2(ROOT/'src/v7.1.9/pph71_ui.py', ui)

launcher=PAYLOAD/'pph_hub/pph3_app.py'
(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\nVERSION="7.1.9"\nCHANNEL="stable"\nBUILD_NAME="PPH 7.1.9 · CPU Load & Power Menu"\nSCHEMA_VERSION=7\n',encoding='utf-8')

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
manifest={'format':1,'product':'pph-funktest','version':'7.1.9','min_version':'7.1.0','max_version':'7.1.8','channel':'stable','build_name':'PPH 7.1.9 · CPU Load & Power Menu','released':'2026-08-12','ui_module':'pph_hub/pph71_ui.py','features':[
    'New: CPU AUSLASTUNG (utilization %) and UPTIME cards on the System page, alongside the existing CPU temperature/RAM cards',
    'New: POWER section under Settings with NEUSTART/HERUNTERFAHREN, gated behind a confirmation dialog - runs systemctl reboot/poweroff',
    'CPU usage is sampled diff-based across refresh cycles, no blocking sleep in the UI thread',
    'No boot-intro or Access Point changes - carries forward 7.1.8 unchanged otherwise',
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
channel={'product':'pph-funktest','channel':'stable','version':'7.1.9','released':'2026-08-12','build_name':'PPH 7.1.9 · CPU Load & Power Menu','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v7.1.9/pph-update-7.1.9-cpu-power-menu.tar.gz','sha256':sha256(OUT),'min_version':'7.1.0','max_version':'7.1.8','notes':['New: CPU-Auslastung + Uptime auf der System-Seite','New: Neustart/Herunterfahren-Menue unter Settings, mit Bestaetigungsdialog','Keine sonstigen Aenderungen']}
(ROOT/'channels/stable.json').write_text(json.dumps(channel,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(OUT)
