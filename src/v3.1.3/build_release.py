#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v3.1.1/pph-update-3.1.1-access-point-fix.tar.gz'
WORK=Path('/tmp/pph313'); PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v3.1.3'; OUT=OUT_DIR/'pph-update-3.1.3-current-ip-control.tar.gz'
def sha256(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def rep(t,o,n,l):
    if o not in t: raise SystemExit(f'missing patch anchor: {l}')
    return t.replace(o,n,1)
if WORK.exists():shutil.rmtree(WORK)
WORK.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf:tf.extractall(WORK)

ap=PAYLOAD/'pph_hub/access_point.py'
t=ap.read_text(encoding='utf-8')
t=rep(t,'if token and token.isdigit() and len(token) == 12:','if token and token.isdigit() and len(token) == 4:','token validation')
t=rep(t,'token = _digits(12)\n        TOKEN_FILE.write_text(token, encoding="utf-8")','token = _digits(4)\n        TOKEN_FILE.write_text(token, encoding="utf-8")','token generation')
t=t.replace('12 numeric digits.','4 numeric digits.',1)
t=rep(t,'if self.path == "/start": controller.start(); return self.send_json(200,{"ok":True})','if self.path == "/start":\n                        threading.Thread(target=controller.start, daemon=True, name="pph-ap-start").start(); return self.send_json(202,{"accepted":True})','api async start')
insert='''\ndef _ipv4(interface: str | None) -> str:\n    if not interface:\n        return ""\n    result = _run(["ip", "-4", "-o", "addr", "show", "dev", interface])\n    for line in result.stdout.splitlines():\n        parts = line.split()\n        if "inet" in parts:\n            return parts[parts.index("inet") + 1].split("/", 1)[0]\n    return ""\n\n'''
t=rep(t,'def _carrier(interface: str | None) -> bool:\n',insert+'def _carrier(interface: str | None) -> bool:\n','ipv4 helper')
t=rep(t,'"lan_iface": lan, "lan_connected": _carrier(lan),','"lan_iface": lan, "lan_ip": _ipv4(lan), "lan_connected": _carrier(lan),','lan ip status')
ap.write_text(t,encoding='utf-8')

ui=PAYLOAD/'pph_hub/access_ui.py'
t=ui.read_text(encoding='utf-8')
t=rep(t,'import tkinter as tk\n','import tkinter as tk\nimport threading\n','threading import')
old='''    def start_access(self)->None:\n        try:self.pph31_ap.start(); self.footer_var.set("Access Point gestartet"); self.pph31_refresh_access()\n        except Exception as exc:messagebox.showerror("PPH Access Point",str(exc),parent=self.root)'''
new='''    def start_access(self)->None:\n        self.footer_var.set("Access Point startet …")\n        self.pph31_ap_vars["detail"].set("STARTET · BrosTrend wird konfiguriert · bitte kurz warten")\n        def worker():\n            try:\n                self.pph31_ap.start(); error=None\n            except Exception as exc:\n                error=exc\n            def done():\n                if error:\n                    self.footer_var.set("Access Point Start fehlgeschlagen")\n                    self.pph31_ap_vars["detail"].set(f"STARTFEHLER · {error}")\n                    messagebox.showerror("PPH Access Point",str(error),parent=self.root)\n                else:\n                    self.footer_var.set("Access Point gestartet")\n                self.pph31_refresh_access()\n            self.root.after(0,done)\n        threading.Thread(target=worker,daemon=True,name="pph-ap-ui-start").start()'''
t=rep(t,old,new,'ui async start')
old_dialog='''    def show_token(self)->None:messagebox.showinfo("PPH Laptop Token",f"Host: homelab.local:8788\\n\\nToken:\\n{self.pph31_ap.token}",parent=self.root)'''
new_dialog='''    def show_token(self)->None:\n        status=self.pph31_ap.status()\n        lan_ip=status.get("lan_ip") or "noch keine LAN-IP"\n        messagebox.showinfo("PPH Laptop Control",f"AKTUELLE PI-IP: {lan_ip}\\nAP-IP: 10.42.0.1\\nPORT: 8788\\n\\n4-STELLIGER CODE:\\n{self.pph31_ap.token}\\n\\nIm gleichen LAN: aktuelle Pi-IP verwenden.\\nIm PPH-WLAN: 10.42.0.1 verwenden.",parent=self.root)'''
t=rep(t,old_dialog,new_dialog,'control dialog')
ui.write_text(t,encoding='utf-8')

(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\n\nVERSION = "3.1.3"\nCHANNEL = "stable"\nBUILD_NAME = "PPH 3.1.3 · Current IP Control"\nSCHEMA_VERSION = 3\n',encoding='utf-8')
test=PAYLOAD/'test_access_point_313.py'
test.write_text('''from pathlib import Path\nimport sys\nROOT=Path(__file__).resolve().parent; HUB=ROOT/"pph_hub"; sys.path.insert(0,str(HUB))\nfrom access_point import _digits\nfor _ in range(20):\n    x=_digits(4); assert len(x)==4 and x.isdigit()\nap=(HUB/"access_point.py").read_text(); ui=(HUB/"access_ui.py").read_text()\nassert '"lan_ip": _ipv4(lan)' in ap\nassert 'accepted' in ap\nassert 'AKTUELLE PI-IP' in ui\nassert 'AP-IP: 10.42.0.1' in ui\nassert 'pph-ap-ui-start' in ui\nprint("PPH 3.1.3 tests OK")\n''',encoding='utf-8')
for p in (ap,ui):subprocess.run(['python3','-m','py_compile',str(p)],check=True)
subprocess.run(['python3',str(test)],cwd=PAYLOAD,check=True)
for c in PAYLOAD.rglob('__pycache__'):shutil.rmtree(c)
files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
    rel=p.relative_to(PAYLOAD).as_posix(); mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py'} else '0644'
    files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'3.1.3','min_version':'3.1.2','max_version':'3.1.2','channel':'stable','build_name':'PPH 3.1.3 · Current IP Control','released':'2026-08-10','tests':['test_access_point_313.py'],'features':['CONTROL zeigt aktuelle LAN-IP des Pi','CONTROL zeigt zusätzlich feste AP-IP 10.42.0.1','4-stelliger Code','asynchroner AP-Start','Laptop kann je nach Netz aktuelle LAN-IP oder AP-IP verwenden'],'files':files}
(WORK/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
OUT_DIR.mkdir(parents=True,exist_ok=True)
with tarfile.open(OUT,'w:gz') as tf:tf.add(WORK/'manifest.json',arcname='manifest.json');tf.add(PAYLOAD,arcname='payload')
package_sha=sha256(OUT)
(OUT_DIR/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT_DIR/'sha256.txt').write_text(f'{package_sha}  {OUT.name}\n',encoding='utf-8')
stable={'product':'pph-funktest','channel':'stable','version':'3.1.3','released':'2026-08-10','build_name':'PPH 3.1.3 · Current IP Control','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v3.1.3/pph-update-3.1.3-current-ip-control.tar.gz','sha256':package_sha,'min_version':'3.1.2','max_version':'3.1.2','notes':['aktuelle LAN-IP im CONTROL-Fenster','AP-IP 10.42.0.1 separat','4-stelliger Code','asynchroner AP-Start']}
(ROOT/'channels/stable.json').write_text(json.dumps(stable,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Built {OUT} sha256={package_sha}')
