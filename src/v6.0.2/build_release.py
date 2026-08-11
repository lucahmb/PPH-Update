#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v6.0.1/pph-update-6.0.1-topbar-version-control.tar.gz'
WORK=Path('/tmp/pph602'); EXTRACT=WORK/'extract'; PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v6.0.2'; OUT=OUT_DIR/'pph-update-6.0.2-access-point-live-data-fix.tar.gz'

def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if WORK.exists(): shutil.rmtree(WORK)
EXTRACT.mkdir(parents=True); PAYLOAD.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(EXTRACT)
source=EXTRACT/'payload'
if not source.is_dir(): raise SystemExit('6.0.1 payload directory missing')
for item in source.iterdir():
    dest=PAYLOAD/item.name
    if item.is_dir(): shutil.copytree(item,dest)
    else: shutil.copy2(item,dest)

# 6.0.0 shipped every page's refresh() as one-shot: it ran once on page entry
# and never again, so a "LIVE" status chip was purely decorative. Most
# visibly, the Access Point page kept showing ACTIVE with a stale client
# count after pressing STOP - the toast fired immediately, but
# AccessPointController.status() is served from a background monitor thread
# that only re-polls nmcli once a second, so the first refresh right after
# stop() returns could still read pre-change state, and nothing ever
# refreshed again afterward.
#
# This release was originally built directly against 6.0.0 (as "6.0.1"), but
# a separate session shipped its own, unrelated 6.0.1 (persistent topbar
# version control) in the meantime. Rebased on top of that: pph6_ui.py here
# is 6.0.1's file with this release's Access Point / live-refresh changes
# re-applied - both features are present and were verified together with
# tools/ui_smoke_test.py and manual Xvfb screenshot review.
ui=PAYLOAD/'pph_hub/pph6_ui.py'
shutil.copy2(ROOT/'src/v6.0.2/pph6_ui.py', ui)

(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\nVERSION="6.0.2"\nCHANNEL="stable"\nBUILD_NAME="PPH 6.0.2 · Access Point Live Data Fix"\nSCHEMA_VERSION=6\n',encoding='utf-8')

subprocess.run(['python3','-m','py_compile',str(ui),str(PAYLOAD/'pph_version.py')],check=True)
for c in PAYLOAD.rglob('__pycache__'): shutil.rmtree(c)

smoke=ROOT/'tools/ui_smoke_test.py'
result=subprocess.run(['xvfb-run','-a','python3',str(smoke),str(PAYLOAD),'pph_hub/pph6_ui.py'])
if result.returncode!=0:
    raise SystemExit('ui_smoke_test failed - refusing to package a UI that does not render.')

files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
    rel=p.relative_to(PAYLOAD).as_posix(); mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','fieldctl.py','fielddctl.py','install_field_mode.sh'} else '0644'
    files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'6.0.2','min_version':'6.0.0','max_version':'6.0.1','channel':'stable','build_name':'PPH 6.0.2 · Access Point Live Data Fix','released':'2026-08-10','ui_module':'pph_hub/pph6_ui.py','features':['Fix: every page with a LIVE status chip now actually re-polls while visible instead of only once on page entry (LIVE_PAGES + Anim.loop, cancelled the instant you navigate away)','Fix: Access Point START/STOP now shows the real state within ~1s instead of staying stale until you leave and return - stop()/start() also fire a burst of quick follow-up refreshes','Restores Access Point RX/TX breakdown, LAN uplink status and NAT-forwarding/internet status on a second details page (access_detail2), split from the first to fit the 480px screen','Restores SSID/password/band editing on a new ACCESS POINT CONFIG page, reachable from the details pages','Fixes a band-selector highlight bug caused by a fragile hasattr()-based lazy dict init','Carries forward 6.0.1 topbar version control unchanged'],'files':files}
OUT_DIR.mkdir(parents=True,exist_ok=True)
mp=WORK/'manifest.json'; mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
with tarfile.open(OUT,'w:gz') as tf:
    tf.add(mp,arcname='manifest.json')
    for p in sorted(PAYLOAD.rglob('*')): tf.add(p,arcname='payload/'+p.relative_to(PAYLOAD).as_posix())
with tarfile.open(OUT,'r:gz') as tf:
    names=set(tf.getnames())
    req={'manifest.json','payload/pph_hub/pph6_ui.py','payload/pph_version.py'}
    miss=sorted(req-names)
    if miss: raise SystemExit('Archive invalid: '+', '.join(miss))
(OUT_DIR/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
channel={'product':'pph-funktest','channel':'stable','version':'6.0.2','released':'2026-08-10','build_name':'PPH 6.0.2 · Access Point Live Data Fix','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v6.0.2/pph-update-6.0.2-access-point-live-data-fix.tar.gz','sha256':sha256(OUT),'min_version':'6.0.0','max_version':'6.0.1','notes':['Access Point (and every other LIVE page) now actually updates while visible instead of only once on entry','Restores RX/TX, LAN, NAT-forwarding/internet status and SSID/password/band editing on the Access Point pages','Includes 6.0.1 topbar version control']}
(ROOT/'channels/stable.json').write_text(json.dumps(channel,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(OUT)
