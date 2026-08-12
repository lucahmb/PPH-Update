#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v7.1.3/pph-update-7.1.3-boot-intro-orientation-fix.tar.gz'
WORK=Path('/tmp/pph714'); EXTRACT=WORK/'extract'; PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v7.1.4'; OUT=OUT_DIR/'pph-update-7.1.4-boot-intro-portrait.tar.gz'

def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if WORK.exists(): shutil.rmtree(WORK)
EXTRACT.mkdir(parents=True); PAYLOAD.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(EXTRACT)
source=EXTRACT/'payload'
if not source.is_dir(): raise SystemExit('7.1.3 payload directory missing')
for item in source.iterdir():
    dest=PAYLOAD/item.name
    if item.is_dir(): shutil.copytree(item,dest)
    else: shutil.copy2(item,dest)

# 7.1.4: `mpv --vo=drm --drm-mode=help` on the device revealed the real
# panel - a 720x1280 DSI display (card2-DSI-2), not an 800x480 HDMI screen.
# No amount of --video-rotate fixes that: it rotates the decoded video
# frame, not the output surface, so an 800x480 clip was always going to
# get letterboxed into a 720x1280 target no matter the rotation value
# (that's also why 7.1.2/7.1.3 both still looked "vertical" and the
# content looked small/boring - most of the panel was black bars).
# render_frames.py is rewritten natively for 720x1280 portrait: bigger
# grid, repositioned wordmark/status/dot layout, ~2.4x more ambient
# particles for the larger area, and tighter per-phase easing (faster
# wipe/stagger/shrink) so transitions read snappier. mpv now targets the
# confirmed connector directly (--drm-connector=0.DSI-2) with no rotate
# flag at all.
BOOT_INTRO_SRC=ROOT/'boot-intro'
boot_intro_dest=PAYLOAD/'boot_intro'
shutil.copy2(BOOT_INTRO_SRC/'build/intro.mp4', boot_intro_dest/'intro.mp4')
shutil.copy2(BOOT_INTRO_SRC/'pph-boot-intro.service', boot_intro_dest/'pph-boot-intro.service')
shutil.copy2(BOOT_INTRO_SRC/'install.sh', boot_intro_dest/'install.sh')

(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\nVERSION="7.1.4"\nCHANNEL="stable"\nBUILD_NAME="PPH 7.1.4 · Boot Intro Portrait Rebuild"\nSCHEMA_VERSION=7\n',encoding='utf-8')

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
manifest={'format':1,'product':'pph-funktest','version':'7.1.4','min_version':'7.1.0','max_version':'7.1.3','channel':'stable','build_name':'PPH 7.1.4 · Boot Intro Portrait Rebuild','released':'2026-08-12','ui_module':'pph_hub/pph71_ui.py','features':[
    'Fix: boot intro is now natively 720x1280 for the real DSI panel (confirmed via `mpv --drm-mode=help`) instead of an 800x480 clip getting letterboxed - this is what actually caused the "vertical/boring" look, not the rotation flag',
    'mpv now targets --drm-connector=0.DSI-2 directly, no rotate flag',
    'Livelier + snappier: bigger grid and ~2.4x the ambient particles for the larger panel, faster wordmark wipe/status stagger/handoff shrink',
    'Re-run sudo <app-dir>/boot_intro/install.sh after this update to pick up the new video and service',
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
channel={'product':'pph-funktest','channel':'stable','version':'7.1.4','released':'2026-08-12','build_name':'PPH 7.1.4 · Boot Intro Portrait Rebuild','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v7.1.4/pph-update-7.1.4-boot-intro-portrait.tar.gz','sha256':sha256(OUT),'min_version':'7.1.0','max_version':'7.1.3','notes':['Fix: boot intro rebuilt natively for the real 720x1280 DSI panel - fixes the vertical/boring look at the source instead of rotating a landscape clip','Livelier and snappier transitions on the larger panel','After check update, re-run: sudo <app-dir>/boot_intro/install.sh','No other changes']}
(ROOT/'channels/stable.json').write_text(json.dumps(channel,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(OUT)
