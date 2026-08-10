#!/usr/bin/env python3
from __future__ import annotations

import hashlib, json, shutil, subprocess, tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v3.1.1/pph-update-3.1.1-access-point-fix.tar.gz'
WORK=Path('/tmp/pph312'); PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v3.1.2'; OUT=OUT_DIR/'pph-update-3.1.2-simple-control.tar.gz'

def sha256(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()

def rep(text:str,old:str,new:str,label:str)->str:
    if old not in text: raise SystemExit(f'missing patch anchor: {label}')
    return text.replace(old,new,1)

if WORK.exists(): shutil.rmtree(WORK)
WORK.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(WORK)

ap=PAYLOAD/'pph_hub/access_point.py'
text=ap.read_text(encoding='utf-8')
text=rep(text,'if token and token.isdigit() and len(token) == 12:','if token and token.isdigit() and len(token) == 4:','token validation')
text=rep(text,'token = _digits(12)\n        TOKEN_FILE.write_text(token, encoding="utf-8")','token = _digits(4)\n        TOKEN_FILE.write_text(token, encoding="utf-8")','token generation')
text=text.replace('12 numeric digits.','4 numeric digits.',1)
text=rep(text,'if self.path == "/start": controller.start(); return self.send_json(200,{"ok":True})','if self.path == "/start":\n                        threading.Thread(target=controller.start, daemon=True, name="pph-ap-start").start(); return self.send_json(202,{"accepted":True})','api async start')
ap.write_text(text,encoding='utf-8')

ui=PAYLOAD/'pph_hub/access_ui.py'
text=ui.read_text(encoding='utf-8')
text=rep(text,'import tkinter as tk\n','import tkinter as tk\nimport threading\n','threading import')
old='''    def start_access(self)->None:\n        try:self.pph31_ap.start(); self.footer_var.set("Access Point gestartet"); self.pph31_refresh_access()\n        except Exception as exc:messagebox.showerror("PPH Access Point",str(exc),parent=self.root)'''
new='''    def start_access(self)->None:\n        self.footer_var.set("Access Point startet …")\n        self.pph31_ap_vars["detail"].set("STARTET · BrosTrend wird konfiguriert · bitte kurz warten")\n        def worker():\n            try:\n                self.pph31_ap.start(); error=None\n            except Exception as exc:\n                error=exc\n            def done():\n                if error:\n                    self.footer_var.set("Access Point Start fehlgeschlagen")\n                    self.pph31_ap_vars["detail"].set(f"STARTFEHLER · {error}")\n                    messagebox.showerror("PPH Access Point",str(error),parent=self.root)\n                else:\n                    self.footer_var.set("Access Point gestartet")\n                self.pph31_refresh_access()\n            self.root.after(0,done)\n        threading.Thread(target=worker,daemon=True,name="pph-ap-ui-start").start()'''
text=rep(text,old,new,'ui async start')
text=rep(text,'messagebox.showinfo("PPH Laptop Token",f"Host: homelab.local:8788\\n\\nToken:\\n{self.pph31_ap.token}",parent=self.root)','messagebox.showinfo("PPH Laptop Control",f"CONTROL-IP: 10.42.0.1\\nPORT: 8788\\n\\n4-STELLIGER CODE:\\n{self.pph31_ap.token}\\n\\nLaptop zuerst mit dem PPH-WLAN verbinden.",parent=self.root)','token dialog')
ui.write_text(text,encoding='utf-8')

(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\n\nVERSION = "3.1.2"\nCHANNEL = "stable"\nBUILD_NAME = "PPH 3.1.2 · Simple Access Control"\nSCHEMA_VERSION = 3\n',encoding='utf-8')

test=PAYLOAD/'test_access_point_312.py'
test.write_text('''from pathlib import Path\nimport sys\nROOT=Path(__file__).resolve().parent; HUB=ROOT/"pph_hub"; sys.path.insert(0,str(HUB))\nfrom access_point import _digits\nfor _ in range(20):\n    x=_digits(4); assert len(x)==4 and x.isdigit()\nap=(HUB/"access_point.py").read_text(); ui=(HUB/"access_ui.py").read_text()\nassert 'len(token) == 4' in ap\nassert 'accepted' in ap\nassert '10.42.0.1' in ui\nassert 'pph-ap-ui-start' in ui\nprint("PPH 3.1.2 tests OK")\n''',encoding='utf-8')

for p in (ap,ui): subprocess.run(['python3','-m','py_compile',str(p)],check=True)
subprocess.run(['python3',str(test)],cwd=PAYLOAD,check=True)
for cache in PAYLOAD.rglob('__pycache__'): shutil.rmtree(cache)

files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
    rel=p.relative_to(PAYLOAD).as_posix(); mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py'} else '0644'
    files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'3.1.2','min_version':'3.1.1','max_version':'3.1.1','channel':'stable','build_name':'PPH 3.1.2 · Simple Access Control','released':'2026-08-10','tests':['test_access_point_312.py'],'features':['Laptop-Control immer über 10.42.0.1:8788','Zufälliger 4-stelliger Laptop-Code','Kein homelab.local und kein Auto-Find nötig','STARTEN blockiert die Touch-Oberfläche nicht mehr','Startfehler werden im ACCESS-Menü angezeigt','12-stelliges numerisches WLAN-Passwort bleibt erhalten'],'files':files}
(WORK/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
OUT_DIR.mkdir(parents=True,exist_ok=True)
with tarfile.open(OUT,'w:gz') as tf: tf.add(WORK/'manifest.json',arcname='manifest.json'); tf.add(PAYLOAD,arcname='payload')
package_sha=sha256(OUT)
(OUT_DIR/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT_DIR/'sha256.txt').write_text(f'{package_sha}  {OUT.name}\n',encoding='utf-8')
stable={'product':'pph-funktest','channel':'stable','version':'3.1.2','released':'2026-08-10','build_name':'PPH 3.1.2 · Simple Access Control','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v3.1.2/pph-update-3.1.2-simple-control.tar.gz','sha256':package_sha,'min_version':'3.1.1','max_version':'3.1.1','notes':['Control-IP fest 10.42.0.1','4-stelliger Code','kein Auto-Find/.local','asynchroner AP-Start statt GUI-Timeout']}
(ROOT/'channels/stable.json').write_text(json.dumps(stable,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Built {OUT} sha256={package_sha}')
