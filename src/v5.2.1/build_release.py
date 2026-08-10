#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v5.2.0/pph-update-5.2.0-touch-hub-redesign.tar.gz'
WORK=Path('/tmp/pph521'); EXTRACT=WORK/'extract'; PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v5.2.1'; OUT=OUT_DIR/'pph-update-5.2.1-startup-crash-fix.tar.gz'

def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if WORK.exists(): shutil.rmtree(WORK)
EXTRACT.mkdir(parents=True); PAYLOAD.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(EXTRACT)
source=EXTRACT/'payload'
if not source.is_dir(): raise SystemExit('5.2.0 payload directory missing')
for item in source.iterdir():
    dest=PAYLOAD/item.name
    if item.is_dir(): shutil.copytree(item,dest)
    else: shutil.copy2(item,dest)

# Critical fix (regression of the 5.1.2 bug): the 5.2.0 rewrite of pph51_ui.py was
# authored from the ORIGINAL, pre-5.1.2 two_cards()/card() pair instead of the fixed
# one, so it shipped with the exact same defect: card() parents its returned frame on
# the page (p), but two_cards() then tried to .grid() that frame into an unrelated
# throwaway container while p's other children (header, nav) are pack-managed.
# Mixing pack and grid on the same master raises _tkinter.TclError on the very first
# page built (build_home), so the app crashed on every single startup again - same
# "window flickers open/closed, never renders" symptom as before.
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

    # Secondary hardening: button() schedules a delayed configure() via w.after(90, ...)
    # on release, but never guards against the widget being destroyed in the meantime
    # (e.g. tapping a nav button immediately navigates away, destroying the old page's
    # buttons). That raises an unhandled TclError inside the Tk callback on every such
    # tap. header()'s own pulse() already guards the same pattern with try/except; do
    # the same here for consistency and a quieter run.
    old_release=(
        "        b.bind('<ButtonRelease-1>',lambda e,w=b:w.after(90,lambda:w.configure(bg=PANEL2,fg=TEXT,highlightbackground=BORDER)),add='+')\n"
    )
    new_release=(
        "        def _release_reset(w=b):\n"
        "            try:w.configure(bg=PANEL2,fg=TEXT,highlightbackground=BORDER)\n"
        "            except Exception:pass\n"
        "        b.bind('<ButtonRelease-1>',lambda e,w=b:w.after(90,_release_reset),add='+')\n"
    )
    if old_release not in t: raise SystemExit('pph51_ui.py: button release anchor not found')
    t=t.replace(old_release,new_release,1)

    ui.write_text(t,encoding='utf-8')

(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\nVERSION="5.2.1"\nCHANNEL="stable"\nBUILD_NAME="PPH 5.2.1 · Startup Crash Fix"\nSCHEMA_VERSION=5\n',encoding='utf-8')

test_file=PAYLOAD/'test_ui_521.py'
test_file.write_text("""from pathlib import Path
import py_compile
R=Path(__file__).resolve().parent
ui=R/'pph_hub/pph51_ui.py'
py_compile.compile(str(ui), doraise=True)
t=ui.read_text(encoding='utf-8')
assert \"left.grid(row=0,column=0\" not in t, 'two_cards() must not grid the card frames into an unrelated container'
assert \"left.pack(side='left'\" in t and \"right.pack(side='left'\" in t
assert 'def _release_reset' in t and 'except Exception:pass' in t
print('PPH 5.2.1 startup crash fix tests OK')
""",encoding='utf-8')

subprocess.run(['python3','-m','py_compile',str(ui),str(PAYLOAD/'pph_version.py')],check=True)
subprocess.run(['python3',str(test_file)],cwd=PAYLOAD,check=True)
for c in PAYLOAD.rglob('__pycache__'): shutil.rmtree(c)

files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
    rel=p.relative_to(PAYLOAD).as_posix(); mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','fieldctl.py','fielddctl.py','install_field_mode.sh'} else '0644'
    files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'5.2.1','min_version':'5.2.0','max_version':'5.2.0','channel':'stable','build_name':'PPH 5.2.1 · Startup Crash Fix','released':'2026-08-10','features':['Fix: 5.2.0 reintroduced the 5.1.2 pack/grid startup crash in two_cards() (HOME, WIRELESS, NETWORK, ACCESS POINT, SYSTEM never rendered)','Hardening: button release callback no longer raises TclError when its widget was destroyed by a navigation that happened within 90ms'],'files':files}
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
channel={'product':'pph-funktest','channel':'stable','version':'5.2.1','released':'2026-08-10','build_name':'PPH 5.2.1 · Startup Crash Fix','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v5.2.1/pph-update-5.2.1-startup-crash-fix.tar.gz','sha256':sha256(OUT),'min_version':'5.2.0','max_version':'5.2.0','notes':['Fixes a regression of the 5.1.2 startup crash: two_cards() mixed pack and grid again and crashed on every launch','PPH never rendered a page on 5.2.0 - this restores it']}
(ROOT/'channels/stable.json').write_text(json.dumps(channel,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(OUT)
