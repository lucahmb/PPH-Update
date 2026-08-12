#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v7.1.1/pph-update-7.1.1-boot-intro.tar.gz'
WORK=Path('/tmp/pph712'); EXTRACT=WORK/'extract'; PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v7.1.2'; OUT=OUT_DIR/'pph-update-7.1.2-boot-intro-fix.tar.gz'

def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if WORK.exists(): shutil.rmtree(WORK)
EXTRACT.mkdir(parents=True); PAYLOAD.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(EXTRACT)
source=EXTRACT/'payload'
if not source.is_dir(): raise SystemExit('7.1.1 payload directory missing')
for item in source.iterdir():
    dest=PAYLOAD/item.name
    if item.is_dir(): shutil.copytree(item,dest)
    else: shutil.copy2(item,dest)

# 7.1.2: fixes the boot intro itself, no UI/backend changes.
#  - mpv failed to become DRM master because Plymouth (quiet splash, still
#    active at that point in boot) already held it - ExecStartPre now runs
#    `plymouth quit` first, same as plymouth-quit.service itself does.
#  - the panel is mounted rotated - mpv now plays with --video-rotate=90.
#  - the intro itself was visually flat: added continuous ambient drifting
#    particles, a breathing glow behind the wordmark, a typewriter reveal
#    for the status log, a comet running along the finished progress bar,
#    periodic low-intensity scanline sweeps and a very slow Ken Burns zoom
#    over the whole 22s so nothing sits fully still.
BOOT_INTRO_SRC=ROOT/'boot-intro'
boot_intro_dest=PAYLOAD/'boot_intro'
shutil.copy2(BOOT_INTRO_SRC/'build/intro.mp4', boot_intro_dest/'intro.mp4')
shutil.copy2(BOOT_INTRO_SRC/'pph-boot-intro.service', boot_intro_dest/'pph-boot-intro.service')
shutil.copy2(BOOT_INTRO_SRC/'install.sh', boot_intro_dest/'install.sh')

(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\nVERSION="7.1.2"\nCHANNEL="stable"\nBUILD_NAME="PPH 7.1.2 · Boot Intro Fix"\nSCHEMA_VERSION=7\n',encoding='utf-8')

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
manifest={'format':1,'product':'pph-funktest','version':'7.1.2','min_version':'7.1.0','max_version':'7.1.1','channel':'stable','build_name':'PPH 7.1.2 · Boot Intro Fix','released':'2026-08-12','ui_module':'pph_hub/pph71_ui.py','features':[
    'Fix: boot intro mpv service failed to start (DRM master held by Plymouth) - now runs `plymouth quit` before playback, matching plymouth-quit.service',
    'Fix: intro played sideways on the rotated panel - mpv now plays with --video-rotate=90',
    'Livelier intro: continuous ambient particles, breathing wordmark glow, typewriter status log, progress-bar comet, periodic scanline sweeps and a slow Ken Burns zoom',
    'Re-run sudo <app-dir>/boot_intro/install.sh after this update to pick up the fixed systemd unit and video',
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
channel={'product':'pph-funktest','channel':'stable','version':'7.1.2','released':'2026-08-12','build_name':'PPH 7.1.2 · Boot Intro Fix','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v7.1.2/pph-update-7.1.2-boot-intro-fix.tar.gz','sha256':sha256(OUT),'min_version':'7.1.0','max_version':'7.1.1','notes':['Fix: boot intro now hands off from Plymouth correctly and plays rotated for the mounted panel','Intro is livelier now (ambient particles, breathing glow, typewriter log, comet, slow zoom)','After check update, re-run: sudo <app-dir>/boot_intro/install.sh','No UI/backend changes otherwise']}
(ROOT/'channels/stable.json').write_text(json.dumps(channel,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(OUT)
