#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v7.1.0/pph-update-7.1.0-pulse-deck-ui.tar.gz'
WORK=Path('/tmp/pph711'); EXTRACT=WORK/'extract'; PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v7.1.1'; OUT=OUT_DIR/'pph-update-7.1.1-boot-intro.tar.gz'

def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if WORK.exists(): shutil.rmtree(WORK)
EXTRACT.mkdir(parents=True); PAYLOAD.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(EXTRACT)
source=EXTRACT/'payload'
if not source.is_dir(): raise SystemExit('7.1.0 payload directory missing')
for item in source.iterdir():
    dest=PAYLOAD/item.name
    if item.is_dir(): shutil.copytree(item,dest)
    else: shutil.copy2(item,dest)

# 7.1.1 carries the 7.1.0 Pulse Deck UI forward unchanged and adds the
# Raspberry-Pi boot intro (video splash + systemd unit + installer) under
# boot_intro/. Same pattern as fieldctl.py/install_field_mode.sh: shipped in
# the payload, applied with one manual `sudo ./boot_intro/install.sh` after
# the update lands, since installing a systemd unit needs root and the
# updater itself only syncs the app payload.
BOOT_INTRO_SRC=ROOT/'boot-intro'
boot_intro_dest=PAYLOAD/'boot_intro'
boot_intro_dest.mkdir(parents=True,exist_ok=True)
shutil.copy2(BOOT_INTRO_SRC/'build/intro.mp4', boot_intro_dest/'intro.mp4')
shutil.copy2(BOOT_INTRO_SRC/'pph-boot-intro.service', boot_intro_dest/'pph-boot-intro.service')
shutil.copy2(BOOT_INTRO_SRC/'install.sh', boot_intro_dest/'install.sh')

(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\nVERSION="7.1.1"\nCHANNEL="stable"\nBUILD_NAME="PPH 7.1.1 · Boot Intro"\nSCHEMA_VERSION=7\n',encoding='utf-8')

ui=PAYLOAD/'pph_hub/pph71_ui.py'
launcher=PAYLOAD/'pph_hub/pph3_app.py'
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
    mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','fieldctl.py','fielddctl.py','install_field_mode.sh','boot_intro/install.sh'} else '0644'
    files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'7.1.1','min_version':'7.0.0','max_version':'7.1.0','channel':'stable','build_name':'PPH 7.1.1 · Boot Intro','released':'2026-08-12','ui_module':'pph_hub/pph71_ui.py','features':[
    'Adds a ~22s branded boot intro (video splash) for the 800x480 Pi display: grid draw-in, "Luca\'s / Projects" wordmark, status handshake, handoff to the app background',
    'Ships as boot_intro/ in the payload: intro.mp4, a systemd unit playing it fullscreen via mpv/DRM before login, and install.sh',
    'Requires one manual step after this update installs: sudo <app-dir>/boot_intro/install.sh (installs the systemd unit, needs root - same pattern as install_field_mode.sh)',
    'No UI/backend changes - carries forward 7.1.0 Pulse Deck UI unchanged',
], 'files':files}
OUT_DIR.mkdir(parents=True,exist_ok=True)
mp=WORK/'manifest.json'; mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
with tarfile.open(OUT,'w:gz') as tf:
    tf.add(mp,arcname='manifest.json')
    for p in sorted(PAYLOAD.rglob('*')): tf.add(p,arcname='payload/'+p.relative_to(PAYLOAD).as_posix())
with tarfile.open(OUT,'r:gz') as tf:
    names=set(tf.getnames())
    req={'manifest.json','payload/pph_hub/pph71_ui.py','payload/pph_hub/pph3_app.py','payload/pph_version.py','payload/boot_intro/intro.mp4','payload/boot_intro/pph-boot-intro.service','payload/boot_intro/install.sh'}
    miss=sorted(req-names)
    if miss: raise SystemExit('Archive invalid: '+', '.join(miss))
(OUT_DIR/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
channel={'product':'pph-funktest','channel':'stable','version':'7.1.1','released':'2026-08-12','build_name':'PPH 7.1.1 · Boot Intro','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v7.1.1/pph-update-7.1.1-boot-intro.tar.gz','sha256':sha256(OUT),'min_version':'7.0.0','max_version':'7.1.0','notes':['New: branded ~22s boot intro video for the Pi display (Luca\'s / Projects)','After check update, run once: sudo <app-dir>/boot_intro/install.sh (needs sudo to install the systemd unit)','No UI/backend changes otherwise - Pulse Deck UI carried forward unchanged']}
(ROOT/'channels/stable.json').write_text(json.dumps(channel,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(OUT)
