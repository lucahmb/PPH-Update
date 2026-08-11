#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v6.0.2/pph-update-6.0.2-access-point-live-data-fix.tar.gz'
WORK=Path('/tmp/pph700'); EXTRACT=WORK/'extract'; PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v7.0.0'; OUT=OUT_DIR/'pph-update-7.0.0-motion-redesign.tar.gz'

def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if WORK.exists(): shutil.rmtree(WORK)
EXTRACT.mkdir(parents=True); PAYLOAD.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(EXTRACT)
source=EXTRACT/'payload'
if not source.is_dir(): raise SystemExit('6.0.2 payload directory missing')
for item in source.iterdir():
    dest=PAYLOAD/item.name
    if item.is_dir(): shutil.copytree(item,dest)
    else: shutil.copy2(item,dest)

# PPH 7.0: a complete visual/motion reinvention of the touch UI, requested as
# a from-scratch redesign rather than an iteration on 6.x. Same authoritative
# single-layer architecture (older UI modules still installed for backend
# side effects, never build a page) and the same backend hooks. Everything
# about how it looks and moves is new: pph7_ui.py replaces pph6_ui.py as the
# active layer entirely.
ui=PAYLOAD/'pph_hub/pph7_ui.py'
shutil.copy2(ROOT/'src/v7.0.0/pph7_ui.py', ui)

launcher=PAYLOAD/'pph_hub/pph3_app.py'
txt=launcher.read_text(encoding='utf-8')
if 'from pph6_ui import install as install6' in txt:
    txt=txt.replace(
        'from pph6_ui import install as install6\ninstall6(hub.PolishedPPHApp, vars(hub))\n\n',
        '', 1,
    )
if 'install7' not in txt:
    marker='if __name__ == "__main__":'
    if marker not in txt: raise SystemExit('pph3_app.py: __main__ marker not found')
    txt=txt.replace(marker,'from pph7_ui import install as install7\ninstall7(hub.PolishedPPHApp, vars(hub))\n\n'+marker,1)
launcher.write_text(txt,encoding='utf-8')

(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\nVERSION="7.0.0"\nCHANNEL="stable"\nBUILD_NAME="PPH 7.0.0 · Motion Redesign"\nSCHEMA_VERSION=7\n',encoding='utf-8')

subprocess.run(['python3','-m','py_compile',str(ui),str(launcher),str(PAYLOAD/'pph_version.py')],check=True)
for c in PAYLOAD.rglob('__pycache__'): shutil.rmtree(c)

smoke=ROOT/'tools/ui_smoke_test.py'
result=subprocess.run(['xvfb-run','-a','python3',str(smoke),str(PAYLOAD),'pph_hub/pph7_ui.py'])
if result.returncode!=0:
    raise SystemExit('ui_smoke_test failed - refusing to package a UI that does not render.')

files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
    rel=p.relative_to(PAYLOAD).as_posix(); mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','fieldctl.py','fielddctl.py','install_field_mode.sh'} else '0644'
    files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'7.0.0','min_version':'6.0.0','max_version':'6.0.2','channel':'stable','build_name':'PPH 7.0.0 · Motion Redesign','released':'2026-08-11','ui_module':'pph_hub/pph7_ui.py','features':[
    'Complete visual and motion reinvention of the 800x480 touch UI, built from scratch (not an iteration on 6.x)',
    'Canvas-drawn glyph icon system throughout: bottom nav icons, card icons, animated signal bars, list-row status glyphs - no image assets',
    'Rounded "holo" cards with a glowing accent edge, replacing flat panels',
    'Live sparkline graphs on Wireless throughput and Network download, animated bottom-nav selection pill that slides between tabs instead of instantly recoloring',
    'Radar-sweep boot sequence replacing the plain checklist',
    'Ripple touch feedback on every button press, back-ease overlay entrance, refined page slide transitions',
    'Carries forward every 6.x fix: live-polling LIVE pages, Access Point RX/TX/LAN/NAT/internet detail pages and SSID/password/band config, topbar version control',
], 'files':files}
OUT_DIR.mkdir(parents=True,exist_ok=True)
mp=WORK/'manifest.json'; mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
with tarfile.open(OUT,'w:gz') as tf:
    tf.add(mp,arcname='manifest.json')
    for p in sorted(PAYLOAD.rglob('*')): tf.add(p,arcname='payload/'+p.relative_to(PAYLOAD).as_posix())
with tarfile.open(OUT,'r:gz') as tf:
    names=set(tf.getnames())
    req={'manifest.json','payload/pph_hub/pph7_ui.py','payload/pph_hub/pph3_app.py','payload/pph_version.py'}
    miss=sorted(req-names)
    if miss: raise SystemExit('Archive invalid: '+', '.join(miss))
(OUT_DIR/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
channel={'product':'pph-funktest','channel':'stable','version':'7.0.0','released':'2026-08-11','build_name':'PPH 7.0.0 · Motion Redesign','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v7.0.0/pph-update-7.0.0-motion-redesign.tar.gz','sha256':sha256(OUT),'min_version':'6.0.0','max_version':'6.0.2','notes':['Complete from-scratch UI/UX and motion redesign: rounded glowing cards, canvas icon system, animated signal bars, live sparklines, sliding nav indicator, radar-sweep boot','Carries forward all 6.x fixes (live-polling, Access Point detail/config pages, topbar version control)']}
(ROOT/'channels/stable.json').write_text(json.dumps(channel,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(OUT)
