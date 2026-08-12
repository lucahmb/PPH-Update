#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v7.0.0/pph-update-7.0.0-motion-redesign.tar.gz'
WORK=Path('/tmp/pph710'); EXTRACT=WORK/'extract'; PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v7.1.0'; OUT=OUT_DIR/'pph-update-7.1.0-pulse-deck-ui.tar.gz'

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

# PPH 7.1: Pulse Deck replaces the previous visible layer with a compact,
# high-contrast 5-inch instrument UI while keeping the 7.0 backend hooks.
ui=PAYLOAD/'pph_hub/pph71_ui.py'
shutil.copy2(ROOT/'src/v7.1.0/pph71_ui.py', ui)

launcher=PAYLOAD/'pph_hub/pph3_app.py'
txt=launcher.read_text(encoding='utf-8')
if 'from pph6_ui import install as install6' in txt:
    txt=txt.replace(
        'from pph6_ui import install as install6\ninstall6(hub.PolishedPPHApp, vars(hub))\n\n',
        '', 1,
    )
if 'from pph7_ui import install as install7' in txt:
    txt=txt.replace(
        'from pph7_ui import install as install7\ninstall7(hub.PolishedPPHApp, vars(hub))\n\n',
        '', 1,
    )
if 'install71' not in txt:
    marker='if __name__ == "__main__":'
    if marker not in txt: raise SystemExit('pph3_app.py: __main__ marker not found')
    txt=txt.replace(marker,'from pph71_ui import install as install71\ninstall71(hub.PolishedPPHApp, vars(hub))\n\n'+marker,1)
launcher.write_text(txt,encoding='utf-8')

(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\nVERSION="7.1.0"\nCHANNEL="stable"\nBUILD_NAME="PPH 7.1.0 · Pulse Deck UI"\nSCHEMA_VERSION=7\n',encoding='utf-8')

subprocess.run(['python3','-m','py_compile',str(ui),str(launcher),str(PAYLOAD/'pph_version.py')],check=True)
for c in PAYLOAD.rglob('__pycache__'): shutil.rmtree(c)

smoke=ROOT/'tools/ui_smoke_test.py'
result=subprocess.run(['xvfb-run','-a','python3',str(smoke),str(PAYLOAD),'pph_hub/pph71_ui.py'])
if result.returncode!=0:
    raise SystemExit('ui_smoke_test failed - refusing to package a UI that does not render.')
for c in PAYLOAD.rglob('__pycache__'): shutil.rmtree(c)

files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
    rel=p.relative_to(PAYLOAD).as_posix(); mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','fieldctl.py','fielddctl.py','install_field_mode.sh'} else '0644'
    files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'7.1.0','min_version':'7.0.0','max_version':'7.0.0','channel':'stable','build_name':'PPH 7.1.0 · Pulse Deck UI','released':'2026-08-12','ui_module':'pph_hub/pph71_ui.py','features':[
    'New Pulse Deck UI/UX tuned for the 800x480 5-inch Raspberry Pi display',
    'High-contrast petrol/graphite instrument surface with lime/cyan live states and warning-only orange/red accents',
    'Animated deck grid background, stronger boot identity, thicker touch navigation and clearer active-state motion',
    'Reworked cards and action buttons with compact 8px geometry, top accent rails and stable touch-friendly sizing',
    'Carries forward the 7.0 backend hooks, live-polling pages, Access Point details/config, update control and diagnostics',
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
channel={'product':'pph-funktest','channel':'stable','version':'7.1.0','released':'2026-08-12','build_name':'PPH 7.1.0 · Pulse Deck UI','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v7.1.0/pph-update-7.1.0-pulse-deck-ui.tar.gz','sha256':sha256(OUT),'min_version':'7.0.0','max_version':'7.0.0','notes':['New Pulse Deck UI/UX for the 800x480 / 5-inch Pi display: high contrast, larger touch nav, animated deck background, compact cards and clearer action states','Carries forward 7.0 behavior and all backend hooks']}
(ROOT/'channels/stable.json').write_text(json.dumps(channel,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(OUT)
