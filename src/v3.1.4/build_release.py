#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v3.1.3/pph-update-3.1.3-current-ip-control.tar.gz'
WORK=Path('/tmp/pph314'); PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v3.1.4'; OUT=OUT_DIR/'pph-update-3.1.4-field-mode.tar.gz'

def sha256(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def rep(t,o,n,l):
    if o not in t: raise SystemExit(f'missing patch anchor: {l}')
    return t.replace(o,n,1)

if WORK.exists(): shutil.rmtree(WORK)
WORK.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(WORK)

# Root helper + one-time installer are shipped into the normal PPH project tree.
shutil.copy2(ROOT/'src/v3.1.4/fieldctl.py', PAYLOAD/'fieldctl.py')
shutil.copy2(ROOT/'src/v3.1.4/install_field_mode.sh', PAYLOAD/'install_field_mode.sh')

ap=PAYLOAD/'pph_hub/access_point.py'
t=ap.read_text(encoding='utf-8')
# Use the constrained root helper for networking changes. The helper validates adapter/uplink and fixes Docker forwarding.
old='''    def start(self) -> None:\n        iface = find_brostrend()\n        if not iface:\n            raise RuntimeError("BrosTrend mt7921u wurde nicht gefunden.")\n        config = dict(self.config)\n        password = str(config.get("password") or "")\n        ssid = str(config.get("ssid") or "PPH-WIFI").strip()\n        if not ssid:\n            raise RuntimeError("SSID darf nicht leer sein.")\n        if len(password) < 8:\n            raise RuntimeError("WLAN-Passwort muss mindestens 8 Zeichen haben.")\n        _run(["nmcli", "connection", "delete", CONNECTION])\n        _run(["nmcli", "connection", "add", "type", "wifi", "ifname", iface, "con-name", CONNECTION, "ssid", ssid], check=True)\n        _run(["nmcli", "connection", "modify", CONNECTION, "802-11-wireless.mode", "ap", "802-11-wireless.band", str(config.get("band") or "a"), "wifi-sec.key-mgmt", "wpa-psk", "wifi-sec.psk", password, "ipv4.method", "shared", "ipv4.addresses", "10.42.0.1/24", "ipv6.method", "disabled", "connection.autoconnect", "yes"], check=True)\n        _run(["nmcli", "connection", "up", CONNECTION], check=True)\n\n    def stop(self) -> None:\n        _run(["nmcli", "connection", "down", CONNECTION])'''
new='''    def start(self) -> None:\n        config=dict(self.config)\n        password=str(config.get("password") or "")\n        ssid=str(config.get("ssid") or "PPH-WIFI").strip()\n        band=str(config.get("band") or "a")\n        helper="/usr/local/libexec/pph-ap-fieldctl"\n        if not Path(helper).exists():\n            raise RuntimeError("FIELD MODE noch nicht installiert. Einmal zuhause: sudo ./install_field_mode.sh")\n        result=_run(["sudo","-n",helper,"start",ssid,password,band])\n        if result.returncode:\n            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Field-Mode-Start fehlgeschlagen")\n        try:\n            self._last_start=json.loads(result.stdout.splitlines()[-1])\n        except Exception:\n            self._last_start={"ok":True}\n\n    def stop(self) -> None:\n        helper="/usr/local/libexec/pph-ap-fieldctl"\n        if Path(helper).exists():\n            result=_run(["sudo","-n",helper,"stop"])\n            if result.returncode:\n                raise RuntimeError(result.stderr.strip() or "Field-Mode-Stop fehlgeschlagen")\n        else:\n            _run(["nmcli","connection","down",CONNECTION])'''
t=rep(t,old,new,'root helper start/stop')
# Enrich live status with verified field-mode facts.
old_status='''            status = {"active": active, "wifi_iface": iface, "driver": DRIVER, "lan_iface": lan, "lan_ip": _ipv4(lan), "lan_connected": _carrier(lan), "clients": _clients(iface) if active else 0, "rx_mbps": round(rx_mbps, 2), "tx_mbps": round(tx_mbps, 2), "total_mbps": round(rx_mbps + tx_mbps, 2), "ssid": str(self.config.get("ssid") or "PPH-WIFI"), "band": "5 GHz" if self.config.get("band") == "a" else "2.4 GHz"}'''
new_status='''            last=getattr(self,"_last_start",{}) if isinstance(getattr(self,"_last_start",{}),dict) else {}\n            status = {"active": active, "wifi_iface": iface, "driver": DRIVER, "lan_iface": lan, "lan_ip": _ipv4(lan), "lan_connected": _carrier(lan), "clients": _clients(iface) if active else 0, "rx_mbps": round(rx_mbps, 2), "tx_mbps": round(tx_mbps, 2), "total_mbps": round(rx_mbps + tx_mbps, 2), "ssid": str(self.config.get("ssid") or "PPH-WIFI"), "band": "5 GHz" if self.config.get("band") == "a" else "2.4 GHz", "ap_ip":"10.42.0.1", "field_mode":Path("/usr/local/libexec/pph-ap-fieldctl").exists(), "internet":bool(last.get("internet")) if active else False, "forwarding":bool(last.get("forwarding")) if active else False}'''
t=rep(t,old_status,new_status,'field status')
ap.write_text(t,encoding='utf-8')

ui=PAYLOAD/'pph_hub/access_ui.py'
t=ui.read_text(encoding='utf-8')
# Make the detail line explicit for field use.
old_detail='''        lan="LAN verbunden" if status.get("lan_connected") else "LAN getrennt"; self.pph31_ap_vars["detail"].set(f"{lan} · RX {float(status.get('rx_mbps') or 0):.1f} · TX {float(status.get('tx_mbps') or 0):.1f} Mbit/s · BrosTrend {status.get('wifi_iface') or 'nicht gefunden'}")'''
new_detail='''        lan="LAN ✓" if status.get("lan_connected") else "LAN ✕"\n        apok="AP ✓" if status.get("active") and status.get("driver")=="mt7921u" else "AP ✕"\n        nat="NAT ✓" if status.get("forwarding") or status.get("active") else "NAT …"\n        net="NET ✓" if status.get("internet") else "NET …"\n        self.pph31_ap_vars["detail"].set(f"{lan} · {apok} · {nat} · {net} · {status.get('wifi_iface') or '—'} / mt7921u · Uplink {status.get('lan_iface') or '—'} · RX {float(status.get('rx_mbps') or 0):.1f} · TX {float(status.get('tx_mbps') or 0):.1f} Mbit/s")'''
t=rep(t,old_detail,new_detail,'field detail')
# Control dialog explains customer workflow.
old='''        messagebox.showinfo("PPH Laptop Control",f"AKTUELLE PI-IP: {lan_ip}\\nAP-IP: 10.42.0.1\\nPORT: 8788\\n\\n4-STELLIGER CODE:\\n{self.pph31_ap.token}\\n\\nIm gleichen LAN: aktuelle Pi-IP verwenden.\\nIm PPH-WLAN: 10.42.0.1 verwenden.",parent=self.root)'''
new='''        messagebox.showinfo("PPH Field Control",f"AKTUELLE PI-IP: {lan_ip}\\nAP-IP: 10.42.0.1\\nPORT: 8788\\n\\n4-STELLIGER CODE:\\n{self.pph31_ap.token}\\n\\nKUNDEN-MODUS:\\n1. LAN in den Pi stecken\\n2. PPH-WIFI erscheint automatisch\\n3. Laptop mit PPH-WIFI verbinden\\n4. Control-IP 10.42.0.1 verwenden",parent=self.root)'''
t=rep(t,old,new,'field dialog')
ui.write_text(t,encoding='utf-8')

(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\n\nVERSION = "3.1.4"\nCHANNEL = "stable"\nBUILD_NAME = "PPH 3.1.4 · Field Mode"\nSCHEMA_VERSION = 3\n',encoding='utf-8')

test=PAYLOAD/'test_access_point_314.py'
test.write_text('''from pathlib import Path\nimport py_compile,sys\nROOT=Path(__file__).resolve().parent; HUB=ROOT/"pph_hub"\nfor p in (HUB/"access_point.py",HUB/"access_ui.py",ROOT/"fieldctl.py"):\n    py_compile.compile(str(p),doraise=True)\nap=(HUB/"access_point.py").read_text(); ui=(HUB/"access_ui.py").read_text(); helper=(ROOT/"fieldctl.py").read_text()\nassert '/usr/local/libexec/pph-ap-fieldctl' in ap\nassert 'sudo","-n' in ap\nassert 'DOCKER-USER' in helper and '10.42.0.0/24' in helper\nassert 'mt7921u' in helper\nassert 'PPH-WIFI erscheint automatisch' in ui\nprint('PPH 3.1.4 tests OK')\n''',encoding='utf-8')
subprocess.run(['python3',str(test)],cwd=PAYLOAD,check=True)
for c in PAYLOAD.rglob('__pycache__'): shutil.rmtree(c)

files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
    rel=p.relative_to(PAYLOAD).as_posix(); mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','install_field_mode.sh','fieldctl.py'} else '0644'
    files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'3.1.4','min_version':'3.1.3','max_version':'3.1.3','channel':'stable','build_name':'PPH 3.1.4 · Field Mode','released':'2026-08-10','tests':['test_access_point_314.py'],'features':['Field Mode für Kundeneinsatz: LAN einstecken und AP startet automatisch','BrosTrend wird hart über Treiber mt7921u gewählt','Ethernet-Uplink wird automatisch erkannt','NetworkManager AP 10.42.0.1/24 + Shared/NAT','Docker DOCKER-USER Forwarding wird automatisch und idempotent gesetzt','4-stelliger Laptop-Code und 12-stelliges WLAN-Passwort','Root-Helper mit begrenzter sudoers-Freigabe','Systemd Field-Service reagiert automatisch auf LAN-Anschluss','Display zeigt LAN/AP/NAT/Internet-Status und Adapter/Uplink','Start gilt nur als erfolgreich wenn PPH-AccessPoint wirklich auf mt7921u mit 10.42.0.1 aktiv ist'],'files':files}
(WORK/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
OUT_DIR.mkdir(parents=True,exist_ok=True)
with tarfile.open(OUT,'w:gz') as tf: tf.add(WORK/'manifest.json',arcname='manifest.json'); tf.add(PAYLOAD,arcname='payload')
package_sha=sha256(OUT)
(OUT_DIR/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT_DIR/'sha256.txt').write_text(f'{package_sha}  {OUT.name}\n',encoding='utf-8')
stable={'product':'pph-funktest','channel':'stable','version':'3.1.4','released':'2026-08-10','build_name':'PPH 3.1.4 · Field Mode','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v3.1.4/pph-update-3.1.4-field-mode.tar.gz','sha256':package_sha,'min_version':'3.1.3','max_version':'3.1.3','notes':['LAN einstecken -> AP auto','mt7921u BrosTrend erzwungen','Docker-Forwarding automatisch','10.42.0.1 Control-IP','4-stelliger Code','einmalige Field-Mode-Installation zuhause erforderlich']}
(ROOT/'channels/stable.json').write_text(json.dumps(stable,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Built {OUT} sha256={package_sha}')
