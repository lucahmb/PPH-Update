#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v7.1.4/pph-update-7.1.4-boot-intro-portrait.tar.gz'
WORK=Path('/tmp/pph715'); EXTRACT=WORK/'extract'; PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v7.1.5'; OUT=OUT_DIR/'pph-update-7.1.5-boot-intro-landscape-mount.tar.gz'

def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if WORK.exists(): shutil.rmtree(WORK)
EXTRACT.mkdir(parents=True); PAYLOAD.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(EXTRACT)
source=EXTRACT/'payload'
if not source.is_dir(): raise SystemExit('7.1.4 payload directory missing')
for item in source.iterdir():
    dest=PAYLOAD/item.name
    if item.is_dir(): shutil.copytree(item,dest)
    else: shutil.copy2(item,dest)

# 7.1.4 composed the intro natively in the DRM buffer's raw orientation
# (720x1280), assuming the buffer axis matched the viewer's axis. It
# doesn't: the panel is physically mounted landscape even though its raw
# DRM buffer is portrait, so 7.1.4 still displayed sideways. mpv
# --video-rotate was tried earlier (7.1.2/7.1.3) and turned out unreliable
# with the plain --vo=drm backend - both rotation values looked identical
# on device, meaning the flag was likely a no-op there.
#
# Fix this time at the file level instead of relying on any player flag:
# render_frames.py composes in the actual viewing orientation again
# (1280x720 landscape), and build.sh now bakes a `ffmpeg -vf transpose=1`
# into the encode step, permanently rotating the pixels into the panel's
# native 720x1280 buffer shape. No rotation flags needed at playback time
# at all - immune to whatever the vo backend does or doesn't support.
BOOT_INTRO_SRC=ROOT/'boot-intro'
boot_intro_dest=PAYLOAD/'boot_intro'
shutil.copy2(BOOT_INTRO_SRC/'build/intro.mp4', boot_intro_dest/'intro.mp4')
shutil.copy2(BOOT_INTRO_SRC/'pph-boot-intro.service', boot_intro_dest/'pph-boot-intro.service')
shutil.copy2(BOOT_INTRO_SRC/'install.sh', boot_intro_dest/'install.sh')

(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\nVERSION="7.1.5"\nCHANNEL="stable"\nBUILD_NAME="PPH 7.1.5 · Boot Intro Landscape Mount Fix"\nSCHEMA_VERSION=7\n',encoding='utf-8')

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
manifest={'format':1,'product':'pph-funktest','version':'7.1.5','min_version':'7.1.0','max_version':'7.1.4','channel':'stable','build_name':'PPH 7.1.5 · Boot Intro Landscape Mount Fix','released':'2026-08-12','ui_module':'pph_hub/pph71_ui.py','features':[
    'Fix: boot intro still displayed sideways in 7.1.4 - the panel is mounted landscape even though its raw DRM buffer is portrait (720x1280); mpv --video-rotate turned out unreliable with --vo=drm in earlier attempts',
    'Content is composed in the real viewing orientation again (1280x720) and the rotation into the 720x1280 buffer is now baked into the video file itself at build time (ffmpeg transpose), not left to a playback-time flag',
    'If this is rotated the wrong way (mirrored/upside-down) on your specific mount, it is a one-line fix (transpose=1 -> transpose=2) - let me know',
    'Re-run sudo <app-dir>/boot_intro/install.sh after this update to pick up the new video',
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
channel={'product':'pph-funktest','channel':'stable','version':'7.1.5','released':'2026-08-12','build_name':'PPH 7.1.5 · Boot Intro Landscape Mount Fix','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v7.1.5/pph-update-7.1.5-boot-intro-landscape-mount.tar.gz','sha256':sha256(OUT),'min_version':'7.1.0','max_version':'7.1.4','notes':['Fix: intro is composed landscape again and rotated into the panel buffer at build time (baked into the video file, not a playback flag)','If orientation is still off (mirrored/upside-down), tell me - one-line fix','After check update, re-run: sudo <app-dir>/boot_intro/install.sh']}
(ROOT/'channels/stable.json').write_text(json.dumps(channel,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(OUT)
