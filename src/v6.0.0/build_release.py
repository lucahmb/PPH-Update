#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v5.2.2/pph-update-5.2.2-deep-page-redesign.tar.gz'
WORK=Path('/tmp/pph600'); EXTRACT=WORK/'extract'; PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v6.0.0'; OUT=OUT_DIR/'pph-update-6.0.0-field-instrument-redesign.tar.gz'

def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if WORK.exists(): shutil.rmtree(WORK)
EXTRACT.mkdir(parents=True); PAYLOAD.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(EXTRACT)
source=EXTRACT/'payload'
if not source.is_dir(): raise SystemExit('5.2.2 payload directory missing')
for item in source.iterdir():
    dest=PAYLOAD/item.name
    if item.is_dir(): shutil.copytree(item,dest)
    else: shutil.copy2(item,dest)

# PPH 6.0: one authoritative UI layer. pph6_ui.py is installed LAST and never
# calls into the previous _build_shell/_build_pages/show_page chain, so none
# of pph3_ui/pph32_ui/pph4_theme/pph41_ui/pph411_touch/pph412_paged/
# pph42_full_ui/pph50_platform/pph51_ui ever build a single widget anymore -
# their install() functions still run (harmless: they only patch cls methods
# pph6_ui immediately overrides again) so any backend side effects they may
# have relied on stay intact. Backend modules (access_point.py, fieldctl.py,
# hardware_roles, the measurement engine, update checker) are used directly
# by pph6_ui.py exactly as before.
ui=PAYLOAD/'pph_hub/pph6_ui.py'
shutil.copy2(ROOT/'src/v6.0.0/pph6_ui.py', ui)

launcher=PAYLOAD/'pph_hub/pph3_app.py'
txt=launcher.read_text(encoding='utf-8')
if 'install6' not in txt:
    marker='if __name__ == "__main__":'
    if marker not in txt: raise SystemExit('pph3_app.py: __main__ marker not found')
    txt=txt.replace(marker,'from pph6_ui import install as install6\ninstall6(hub.PolishedPPHApp, vars(hub))\n\n'+marker,1)
launcher.write_text(txt,encoding='utf-8')

(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\nVERSION="6.0.0"\nCHANNEL="stable"\nBUILD_NAME="PPH 6.0.0 · Field Instrument Redesign"\nSCHEMA_VERSION=6\n',encoding='utf-8')

subprocess.run(['python3','-m','py_compile',str(ui),str(launcher),str(PAYLOAD/'pph_version.py')],check=True)
for c in PAYLOAD.rglob('__pycache__'): shutil.rmtree(c)

# Hard gate: actually build every page with real Tkinter under Xvfb before
# this package is allowed to exist. String-matching tests missed the exact
# class of pack/grid and call-argument bugs that shipped in 5.1.0, 5.2.0 and
# 5.2.2 - this is the same tool used in CI (tools/ui_smoke_test.py), run here
# too so a broken build never even gets this far.
smoke=ROOT/'tools/ui_smoke_test.py'
result=subprocess.run(['xvfb-run','-a','python3',str(smoke),str(PAYLOAD),'pph_hub/pph6_ui.py'])
if result.returncode!=0:
    raise SystemExit('ui_smoke_test failed - refusing to package a UI that does not render. Install xvfb+python3-tk if this failed because no display tooling is available.')

files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
    rel=p.relative_to(PAYLOAD).as_posix(); mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','fieldctl.py','fielddctl.py','install_field_mode.sh'} else '0644'
    files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'6.0.0','min_version':'5.1.0','max_version':'5.2.2','channel':'stable','build_name':'PPH 6.0.0 · Field Instrument Redesign','released':'2026-08-10','ui_module':'pph_hub/pph6_ui.py','features':['Complete UI/UX overhaul for the 800x480 5-inch touch display, designed as a dedicated field instrument rather than a scaled-down desktop app','One authoritative UI layer (pph6_ui.py): older UI modules no longer build any page, own navigation, or draw any widget - backend hooks (measurement engine, access point controller, update checker) are used directly','Reusable component system: header/status chip, metric cards, action buttons, persistent bottom nav, list rows, progress bars, page indicator, modal overlay, notification toasts','Centralized animation manager with FULL/REDUCED/OFF levels, per-page cancellation, slide page transitions, animated boot sequence, animated connection flow, value interpolation','Access Point pairing code, SSID, password and LAN IP all directly visible with no submenu','Fixes a live production crash in 5.2.2 (scanline() called without self, binding a color string as the Tk parent) by fully replacing the affected UI layer','Verified end-to-end with tools/ui_smoke_test.py plus manual Xvfb screenshot review of all 28 pages, including a caught-and-fixed card-visibility z-order bug, three self.X() AttributeError bugs, a falsy-zero bug hiding valid 0% packet loss, a German-locale free(1) parsing bug, and a sliding-bottom-nav violation of the spec'],'files':files}
OUT_DIR.mkdir(parents=True,exist_ok=True)
mp=WORK/'manifest.json'; mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
with tarfile.open(OUT,'w:gz') as tf:
    tf.add(mp,arcname='manifest.json')
    for p in sorted(PAYLOAD.rglob('*')): tf.add(p,arcname='payload/'+p.relative_to(PAYLOAD).as_posix())
with tarfile.open(OUT,'r:gz') as tf:
    names=set(tf.getnames())
    req={'manifest.json','payload/pph_hub/pph6_ui.py','payload/pph_hub/pph3_app.py','payload/pph_version.py'}
    miss=sorted(req-names)
    if miss: raise SystemExit('Archive invalid: '+', '.join(miss))
(OUT_DIR/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
channel={'product':'pph-funktest','channel':'stable','version':'6.0.0','released':'2026-08-10','build_name':'PPH 6.0.0 · Field Instrument Redesign','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v6.0.0/pph-update-6.0.0-field-instrument-redesign.tar.gz','sha256':sha256(OUT),'min_version':'5.1.0','max_version':'5.2.2','notes':['Complete field-instrument UI/UX redesign for the 800x480 touch display','One authoritative UI layer - no more theme-on-theme stacking','Also fixes the 5.2.2 scanline() crash by replacing the whole UI layer','Covers every device currently on 5.1.x or 5.2.x']}
(ROOT/'channels/stable.json').write_text(json.dumps(channel,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(OUT)
