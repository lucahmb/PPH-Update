#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v3.1.2/pph-update-3.1.2-simple-control.tar.gz'
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
insert='''\ndef _ipv4(interface: str | None) -> str:\n    if not interface:\n        return ""\n    result = _run(["ip", "-4", "-o", "addr", "show", "dev", interface])\n    for line in result.stdout.splitlines():\n        parts=line.split()\n        if "inet" in parts:\n            return parts[parts.index("inet")+1].split("/",1)[0]\n    return ""\n\n'''
t=rep(t,'def _carrier(interface: str | None) -> bool:\n',insert+'def _carrier(interface: str | None) -> bool:\n','ipv4 helper')
t=rep(t,'"lan_iface": lan, "lan_connected": _carrier(lan),','"lan_iface": lan, "lan_ip": _ipv4(lan), "lan_connected": _carrier(lan),','lan ip status')
ap.write_text(t,encoding='utf-8')
ui=PAYLOAD/'pph_hub/access_ui.py'
t=ui.read_text(encoding='utf-8')
old='messagebox.showinfo("PPH Laptop Control",f"CONTROL-IP: 10.42.0.1\\nPORT: 8788\\n\\n4-STELLIGER CODE:\\n{self.pph31_ap.token}\\n\\nLaptop zuerst mit dem PPH-WLAN verbinden.",parent=self.root)'
new='''status=self.pph31_ap.status(); lan_ip=status.get("lan_ip") or "noch keine LAN-IP"\n        messagebox.showinfo("PPH Laptop Control",f"AKTUELLE PI-IP: {lan_ip}\\nAP-IP: 10.42.0.1\\nPORT: 8788\\n\\n4-STELLIGER CODE:\\n{self.pph31_ap.token}\\n\\nIm gleichen LAN: aktuelle Pi-IP verwenden.\\nIm PPH-WLAN: 10.42.0.1 verwenden.",parent=self.root)'''
t=rep(t,old,new,'control dialog')
ui.write_text(t,encoding='utf-8')
(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\n\nVERSION = "3.1.3"\nCHANNEL = "stable"\nBUILD_NAME = "PPH 3.1.3 · Current IP Control"\nSCHEMA_VERSION = 3\n',encoding='utf-8')
test=PAYLOAD/'test_access_point_313.py'
test.write_text('''from pathlib import Path\nROOT=Path(__file__).resolve().parent; HUB=ROOT/"pph_hub"\nap=(HUB/"access_point.py").read_text(); ui=(HUB/"access_ui.py").read_text()\nassert '"lan_ip": _ipv4(lan)' in ap\nassert 'AKTUELLE PI-IP' in ui\nassert 'AP-IP: 10.42.0.1' in ui\nprint("PPH 3.1.3 tests OK")\n''',encoding='utf-8')
for p in (ap,ui):subprocess.run(['python3','-m','py_compile',str(p)],check=True)
subprocess.run(['python3',str(test)],cwd=PAYLOAD,check=True)
for c in PAYLOAD.rglob('__pycache__'):shutil.rmtree(c)
files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
    rel=p.relative_to(PAYLOAD).as_posix(); mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py'} else '0644'
    files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'3.1.3','min_version':'3.1.2','max_version':'3.1.2','channel':'stable','build_name':'PPH 3.1.3 · Current IP Control','released':'2026-08-10','tests':['test_access_point_313.py'],'features':['CONTROL zeigt aktuelle LAN-IP des Pi','CONTROL zeigt zusätzlich feste AP-IP 10.42.0.1','4-stelliger Code bleibt erhalten','Laptop kann je nach Netz aktuelle LAN-IP oder AP-IP verwenden'],'files':files}
(WORK/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
OUT_DIR.mkdir(parents=True,exist_ok=True)
with tarfile.open(OUT,'w:gz') as tf:tf.add(WORK/'manifest.json',arcname='manifest.json');tf.add(PAYLOAD,arcname='payload')
package_sha=sha256(OUT)
(OUT_DIR/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT_DIR/'sha256.txt').write_text(f'{package_sha}  {OUT.name}\n',encoding='utf-8')
stable={'product':'pph-funktest','channel':'stable','version':'3.1.3','released':'2026-08-10','build_name':'PPH 3.1.3 · Current IP Control','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v3.1.3/pph-update-3.1.3-current-ip-control.tar.gz','sha256':package_sha,'min_version':'3.1.2','max_version':'3.1.2','notes':['aktuelle LAN-IP im CONTROL-Fenster','AP-IP 10.42.0.1 separat','4-stelliger Code']}
(ROOT/'channels/stable.json').write_text(json.dumps(stable,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Built {OUT} sha256={package_sha}')
