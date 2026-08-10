#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v6.0.0/pph-update-6.0.0-field-instrument-redesign.tar.gz'
WORK=Path('/tmp/pph601'); EXTRACT=WORK/'extract'; PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v6.0.1'; OUT=OUT_DIR/'pph-update-6.0.1-topbar-version-control.tar.gz'

def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if WORK.exists(): shutil.rmtree(WORK)
EXTRACT.mkdir(parents=True); PAYLOAD.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(EXTRACT)
source=EXTRACT/'payload'
if not source.is_dir(): raise SystemExit('6.0.0 payload directory missing')
for item in source.iterdir():
    dest=PAYLOAD/item.name
    if item.is_dir(): shutil.copytree(item,dest)
    else: shutil.copy2(item,dest)

ui=PAYLOAD/'pph_hub/pph6_ui.py'
t=ui.read_text(encoding='utf-8')
old="""        svar = tk.StringVar(value=status_text)\n        badge = chip(self, h, svar, status_kind)\n        badge.pack(side='right', pady=10)\n        return svar, badge\n"""
new="""        # Persistent top-bar version control: available on every page without\n        # consuming additional vertical space on the 800x480 display.\n        right = tk.Frame(h, bg=BG)\n        right.pack(side='right', fill='y', pady=6)\n        svar = tk.StringVar(value=status_text)\n        badge = chip(self, right, svar, status_kind)\n        badge.pack(side='right', padx=(5, 0), pady=4)\n        vc = tk.Button(\n            right,\n            text=f'UPDATES · v{_current_version()}',\n            command=self._pph28_open_update,\n            bg=PANEL2, fg=CYAN, activebackground=CYAN, activeforeground=BG,\n            relief='flat', bd=0, highlightthickness=1, highlightbackground=BORDER,\n            font=font(self, 8, 'bold'), padx=9, pady=7, cursor='hand2'\n        )\n        vc.pack(side='right', pady=4)\n        return svar, badge\n"""
if old not in t: raise SystemExit('pph6 header block not found')
t=t.replace(old,new,1)
ui.write_text(t,encoding='utf-8')

(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\nVERSION="6.0.1"\nCHANNEL="stable"\nBUILD_NAME="PPH 6.0.1 · Topbar Version Control"\nSCHEMA_VERSION=6\n',encoding='utf-8')

subprocess.run(['python3','-m','py_compile',str(ui),str(PAYLOAD/'pph_hub/pph3_app.py'),str(PAYLOAD/'pph_version.py')],check=True)
for c in PAYLOAD.rglob('__pycache__'): shutil.rmtree(c)

smoke=ROOT/'tools/ui_smoke_test.py'
result=subprocess.run(['xvfb-run','-a','python3',str(smoke),str(PAYLOAD),'pph_hub/pph6_ui.py'])
if result.returncode!=0: raise SystemExit('ui_smoke_test failed')

files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
    rel=p.relative_to(PAYLOAD).as_posix(); mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','fieldctl.py','fielddctl.py','install_field_mode.sh'} else '0644'
    files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'6.0.1','min_version':'6.0.0','max_version':'6.0.0','channel':'stable','build_name':'PPH 6.0.1 · Topbar Version Control','released':'2026-08-10','ui_module':'pph_hub/pph6_ui.py','features':['Persistent version control in the topbar on every PPH 6 page','Topbar shows installed version and opens the existing update dialog with one tap','READY/LIVE status chip retained beside version control','No additional vertical space used on the 800x480 display','PPH 6 authoritative UI architecture retained'],'files':files}
OUT_DIR.mkdir(parents=True,exist_ok=True)
mp=WORK/'manifest.json'; mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
with tarfile.open(OUT,'w:gz') as tf:
    tf.add(mp,arcname='manifest.json')
    for p in sorted(PAYLOAD.rglob('*')): tf.add(p,arcname='payload/'+p.relative_to(PAYLOAD).as_posix())
with tarfile.open(OUT,'r:gz') as tf:
    names=set(tf.getnames()); req={'manifest.json','payload/pph_hub/pph6_ui.py','payload/pph_hub/pph3_app.py','payload/pph_version.py'}
    miss=sorted(req-names)
    if miss: raise SystemExit('Archive invalid: '+', '.join(miss))
(OUT_DIR/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
channel={'product':'pph-funktest','channel':'stable','version':'6.0.1','released':'2026-08-10','build_name':'PPH 6.0.1 · Topbar Version Control','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v6.0.1/pph-update-6.0.1-topbar-version-control.tar.gz','sha256':sha256(OUT),'min_version':'6.0.0','max_version':'6.0.0','notes':['Restore version control to the global PPH 6 topbar','Show installed version on every page','One-tap access to existing update checker','Status chip remains visible beside update control']}
(ROOT/'channels/stable.json').write_text(json.dumps(channel,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(OUT)
