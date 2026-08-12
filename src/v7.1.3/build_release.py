#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v7.1.2/pph-update-7.1.2-boot-intro-fix.tar.gz'
WORK=Path('/tmp/pph713'); EXTRACT=WORK/'extract'; PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v7.1.3'; OUT=OUT_DIR/'pph-update-7.1.3-boot-intro-orientation-fix.tar.gz'

def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if WORK.exists(): shutil.rmtree(WORK)
EXTRACT.mkdir(parents=True); PAYLOAD.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(EXTRACT)
source=EXTRACT/'payload'
if not source.is_dir(): raise SystemExit('7.1.2 payload directory missing')
for item in source.iterdir():
    dest=PAYLOAD/item.name
    if item.is_dir(): shutil.copytree(item,dest)
    else: shutil.copy2(item,dest)

# 7.1.3: the panel is a normal 800x480 landscape connector after all -
# --video-rotate=90 (added in 7.1.2 based on an early, since it turned out
# incorrect, guess) made the intro render as a pillarboxed portrait strip.
# Reverted to --video-rotate=0 (plain horizontal). No other changes.
BOOT_INTRO_SRC=ROOT/'boot-intro'
boot_intro_dest=PAYLOAD/'boot_intro'
shutil.copy2(BOOT_INTRO_SRC/'build/intro.mp4', boot_intro_dest/'intro.mp4')
shutil.copy2(BOOT_INTRO_SRC/'pph-boot-intro.service', boot_intro_dest/'pph-boot-intro.service')
shutil.copy2(BOOT_INTRO_SRC/'install.sh', boot_intro_dest/'install.sh')

(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\nVERSION="7.1.3"\nCHANNEL="stable"\nBUILD_NAME="PPH 7.1.3 · Boot Intro Orientation Fix"\nSCHEMA_VERSION=7\n',encoding='utf-8')

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
manifest={'format':1,'product':'pph-funktest','version':'7.1.3','min_version':'7.1.0','max_version':'7.1.2','channel':'stable','build_name':'PPH 7.1.3 · Boot Intro Orientation Fix','released':'2026-08-12','ui_module':'pph_hub/pph71_ui.py','features':[
    'Fix: boot intro rendered as a vertical pillarboxed strip - the panel is plain 800x480 landscape, --video-rotate=90 from 7.1.2 was wrong, reverted to horizontal',
    'Re-run sudo <app-dir>/boot_intro/install.sh after this update to pick up the fixed systemd unit',
    'No UI/backend/visual-content changes otherwise - carries forward 7.1.2 intro and 7.1.0 Pulse Deck UI unchanged',
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
channel={'product':'pph-funktest','channel':'stable','version':'7.1.3','released':'2026-08-12','build_name':'PPH 7.1.3 · Boot Intro Orientation Fix','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v7.1.3/pph-update-7.1.3-boot-intro-orientation-fix.tar.gz','sha256':sha256(OUT),'min_version':'7.1.0','max_version':'7.1.2','notes':['Fix: boot intro now plays horizontal (the panel was never actually rotated - 7.1.2 guessed wrong)','After check update, re-run: sudo <app-dir>/boot_intro/install.sh','No other changes']}
(ROOT/'channels/stable.json').write_text(json.dumps(channel,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(OUT)
