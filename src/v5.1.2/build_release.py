#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v5.1.1/pph-update-5.1.1-access-point-flow-fix.tar.gz'
WORK=Path('/tmp/pph512'); EXTRACT=WORK/'extract'; PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v5.1.2'; OUT=OUT_DIR/'pph-update-5.1.2-startup-crash-fix.tar.gz'

def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if WORK.exists(): shutil.rmtree(WORK)
EXTRACT.mkdir(parents=True); PAYLOAD.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(EXTRACT)
source=EXTRACT/'payload'
if not source.is_dir(): raise SystemExit('5.1.1 payload directory missing')
for item in source.iterdir():
    dest=PAYLOAD/item.name
    if item.is_dir(): shutil.copytree(item,dest)
    else: shutil.copy2(item,dest)

# Critical fix: two_cards() tried to .grid() the frames returned by card() into a
# throwaway container `g`, but card() actually parents those frames on the page
# itself (`p`), which already has pack-managed children (header/nav). Mixing pack
# and grid inside the same master raises _tkinter.TclError immediately on the very
# first page built (build_home), so the app crashed on every single startup and a
# Restart=always systemd unit kept relaunching it -> the window "flickered" open and
# closed in a loop and never actually rendered. This affects every 5.1.x page that
# uses two_cards(): HOME, WIRELESS, NETWORK, ACCESS POINT and SYSTEM.
ui=PAYLOAD/'pph_hub/pph51_ui.py'
if ui.exists():
    t=ui.read_text(encoding='utf-8')
    old=(
        "    def two_cards(self,p,left,right):\n"
        "        g=tk.Frame(p,bg=BG); g.pack(fill='both',expand=True,padx=10,pady=6)\n"
        "        g.grid_columnconfigure(0,weight=1,uniform='c51'); g.grid_columnconfigure(1,weight=1,uniform='c51'); g.grid_rowconfigure(0,weight=1)\n"
        "        left.grid(row=0,column=0,sticky='nsew',padx=4); right.grid(row=0,column=1,sticky='nsew',padx=4)\n"
    )
    new=(
        "    def two_cards(self,p,left,right):\n"
        "        left.pack(side='left',fill='both',expand=True,padx=(10,4),pady=6); right.pack(side='left',fill='both',expand=True,padx=(4,10),pady=6)\n"
    )
    if old not in t: raise SystemExit('pph51_ui.py: two_cards anchor not found')
    t=t.replace(old,new,1)
    ui.write_text(t,encoding='utf-8')

(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\nVERSION="5.1.2"\nCHANNEL="stable"\nBUILD_NAME="PPH 5.1.2 · Startup Crash Fix"\nSCHEMA_VERSION=5\n',encoding='utf-8')

test_file=PAYLOAD/'test_ui_512.py'
shutil.copy2(ROOT/'src/v5.1.2/test_ui_512.py',test_file)

subprocess.run(['python3','-m','py_compile',str(ui),str(PAYLOAD/'pph_version.py')],check=True)
subprocess.run(['python3',str(test_file)],cwd=PAYLOAD,check=True)
for c in PAYLOAD.rglob('__pycache__'): shutil.rmtree(c)

files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
    rel=p.relative_to(PAYLOAD).as_posix(); mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','fieldctl.py','fielddctl.py','install_field_mode.sh'} else '0644'
    files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'5.1.2','min_version':'5.1.0','max_version':'5.1.1','channel':'stable','build_name':'PPH 5.1.2 · Startup Crash Fix','released':'2026-08-10','features':['Fix: two_cards() mixed pack and grid geometry managers on the same page frame, crashing PPH on every startup (build_home ran first, so the hub never rendered a single page and kept restart-looping under systemd)','Affects HOME, WIRELESS, NETWORK, ACCESS POINT and SYSTEM pages'],'files':files}
OUT_DIR.mkdir(parents=True,exist_ok=True)
mp=WORK/'manifest.json'; mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
with tarfile.open(OUT,'w:gz') as tf:
    tf.add(mp,arcname='manifest.json')
    for p in sorted(PAYLOAD.rglob('*')): tf.add(p,arcname='payload/'+p.relative_to(PAYLOAD).as_posix())
with tarfile.open(OUT,'r:gz') as tf:
    names=set(tf.getnames())
    req={'manifest.json','payload/pph_hub/pph51_ui.py','payload/pph_version.py'}
    miss=sorted(req-names)
    if miss: raise SystemExit('Archive invalid: '+', '.join(miss))
(OUT_DIR/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
channel={'product':'pph-funktest','channel':'stable','version':'5.1.2','released':'2026-08-10','build_name':'PPH 5.1.2 · Startup Crash Fix','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v5.1.2/pph-update-5.1.2-startup-crash-fix.tar.gz','sha256':sha256(OUT),'min_version':'5.1.0','max_version':'5.1.1','notes':['Fixes a startup crash (pack/grid geometry manager conflict in two_cards()) that made PPH restart-loop and appear to flicker without ever opening','Works whether the device is currently on 5.1.0 or 5.1.1']}
(ROOT/'channels/stable.json').write_text(json.dumps(channel,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(OUT)
