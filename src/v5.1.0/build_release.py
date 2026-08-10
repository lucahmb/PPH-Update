#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v5.0.4/pph-update-5.0.4-startup-nav-fix.tar.gz'
WORK=Path('/tmp/pph510'); EXTRACT=WORK/'extract'; PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v5.1.0'; OUT=OUT_DIR/'pph-update-5.1.0-wireless-style-ui.tar.gz'

def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if WORK.exists(): shutil.rmtree(WORK)
EXTRACT.mkdir(parents=True); PAYLOAD.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(EXTRACT)
source=EXTRACT/'payload'
if not source.is_dir(): raise SystemExit('5.0.4 payload directory missing')
for item in source.iterdir():
    dest=PAYLOAD/item.name
    if item.is_dir(): shutil.copytree(item,dest)
    else: shutil.copy2(item,dest)

# New 5.1 UI layer.
shutil.copy2(ROOT/'src/v5.1.0/pph51_ui.py',PAYLOAD/'pph_hub/pph51_ui.py')
launcher=PAYLOAD/'pph_hub/pph3_app.py'; txt=launcher.read_text(encoding='utf-8')
if 'install51' not in txt:
    marker='if __name__ == "__main__":'
    txt=txt.replace(marker,'from pph51_ui import install as install51\ninstall51(hub.PolishedPPHApp, vars(hub))\n\n'+marker,1)
launcher.write_text(txt,encoding='utf-8')

# Python 3.13/Tk fix: Tcl_Obj values cannot always be int() directly.
theme=PAYLOAD/'pph_hub/pph4_theme.py'
if theme.exists():
    t=theme.read_text(encoding='utf-8')
    if 'def _pph_safe_int' not in t:
        insert="\ndef _pph_safe_int(value, default=0):\n    try:\n        return int(str(value))\n    except Exception:\n        try: return int(float(str(value)))\n        except Exception: return default\n\n"
        pos=t.find('\n', t.find('import '))
        t=t[:pos+1]+insert+t[pos+1:]
    t=t.replace("int(w.cget('padx') or 0)","_pph_safe_int(w.cget('padx'),0)")
    t=t.replace("int(w.cget('pady') or 0)","_pph_safe_int(w.cget('pady'),0)")
    theme.write_text(t,encoding='utf-8')

# Access UI guard: old refresh callbacks must not draw into destroyed canvases.
aui=PAYLOAD/'pph_hub/access_ui.py'
if aui.exists():
    a=aui.read_text(encoding='utf-8')
    old='canvas=self.pph31_ap_canvas; canvas.delete("all")'
    new='canvas=getattr(self,"pph31_ap_canvas",None)\n        if canvas is None or not int(canvas.winfo_exists()): return\n        canvas.delete("all")'
    if old in a: a=a.replace(old,new)
    aui.write_text(a,encoding='utf-8')

(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\nVERSION="5.1.0"\nCHANNEL="stable"\nBUILD_NAME="PPH 5.1.0 · Wireless Style System UI"\nSCHEMA_VERSION=5\n',encoding='utf-8')

subprocess.run(['python3','-m','py_compile',str(PAYLOAD/'pph_hub/pph51_ui.py'),str(launcher),str(theme),str(aui)],check=True)
for c in PAYLOAD.rglob('__pycache__'): shutil.rmtree(c)

files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
    rel=p.relative_to(PAYLOAD).as_posix(); mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','fieldctl.py','fielddctl.py','install_field_mode.sh'} else '0644'
    files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'5.1.0','min_version':'5.0.4','max_version':'5.0.4','channel':'stable','build_name':'PPH 5.1.0 · Wireless Style System UI','released':'2026-08-10','features':['Wireless Site Analyzer design language systemwide','Large 5-inch bottom navigation','Remove legacy sidebar use','Access Point pairing code + AP/LAN IP cards','Python 3.13 Tcl_Obj theme fix','Destroyed Access Point canvas guard'],'files':files}
OUT_DIR.mkdir(parents=True,exist_ok=True)
mp=WORK/'manifest.json'; mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
with tarfile.open(OUT,'w:gz') as tf:
    tf.add(mp,arcname='manifest.json')
    for p in sorted(PAYLOAD.rglob('*')): tf.add(p,arcname='payload/'+p.relative_to(PAYLOAD).as_posix())
with tarfile.open(OUT,'r:gz') as tf:
    names=set(tf.getnames())
    req={'manifest.json','payload/pph_hub/pph51_ui.py','payload/pph_hub/pph4_theme.py','payload/pph_hub/access_ui.py','payload/pph_hub/pph3_app.py','payload/pph_version.py'}
    miss=sorted(req-names)
    if miss: raise SystemExit('Archive invalid: '+', '.join(miss))
(OUT_DIR/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
channel={'product':'pph-funktest','channel':'stable','version':'5.1.0','released':'2026-08-10','build_name':'PPH 5.1.0 · Wireless Style System UI','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v5.1.0/pph-update-5.1.0-wireless-style-ui.tar.gz','sha256':sha256(OUT),'min_version':'5.0.4','max_version':'5.0.4','notes':['Systemwide Wireless Analyzer design','Large 5-inch nav and no legacy sidebar','Access Point pairing code/IP restored','Fix Tkinter Tcl_Obj and destroyed canvas callbacks']}
(ROOT/'channels/stable.json').write_text(json.dumps(channel,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(OUT)
