#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "packages/v3.0.0/pph-update-3.0.0-control-center.tar.gz"
WORK = Path("/tmp/pph310")
PAYLOAD = WORK / "payload"
OUT_DIR = ROOT / "packages/v3.1.0"
OUT = OUT_DIR / "pph-update-3.1.0-access-point.tar.gz"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"Patch anchor missing: {label}")
    return text.replace(old, new, 1)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if WORK.exists():
    shutil.rmtree(WORK)
WORK.mkdir(parents=True)
with tarfile.open(BASE, "r:gz") as tf:
    tf.extractall(WORK)

shutil.copy2(ROOT / "src/v3.1.0/access_point.py", PAYLOAD / "pph_hub/access_point.py")
shutil.copy2(ROOT / "src/v3.1.0/access_ui.py", PAYLOAD / "pph_hub/access_ui.py")

app = PAYLOAD / "pph_hub/pph3_app.py"
text = app.read_text(encoding="utf-8")
text = replace_once(text, "from pph3_ui import install\n", "from pph3_ui import install\nfrom access_ui import install_access\n", "app import")
text = replace_once(text, "install(hub.PolishedPPHApp, vars(hub))\n", "install(hub.PolishedPPHApp, vars(hub))\ninstall_access(hub.PolishedPPHApp, vars(hub))\n", "app installer")
app.write_text(text, encoding="utf-8")

ui = PAYLOAD / "pph_hub/pph3_ui.py"
text = ui.read_text(encoding="utf-8")
text = text.replace("PPH 3.0 shell", "PPH 3.1 shell", 1)
text = text.replace('text="3.0"', 'text="3.1"', 1)
text = text.replace('text="PPH 3.0 SETTINGS"', 'text="PPH 3.1 SETTINGS"', 1)
text = replace_once(
    text,
    '            ("WIFI", "wifi3"),\n            ("SYSTEM", "system3"),\n',
    '            ("WIFI", "wifi3"),\n            ("ACCESS", "access3"),\n            ("SYSTEM", "system3"),\n',
    "navigation",
)
text = replace_once(
    text,
    '("WIFI OVERVIEW", lambda: self.show_page("wifi3"), SURFACE2),',
    '("ACCESS POINT", lambda: self.show_page("access3"), ORANGE),',
    "home action",
)
text = replace_once(
    text,
    '        build_wifi(self)\n        build_system(self)\n',
    '        build_wifi(self)\n        self.pph31_build_access()\n        build_system(self)\n',
    "build pages",
)
text = replace_once(
    text,
    '        elif name == "system3":\n            self.pph30_refresh_system()\n',
    '        elif name == "access3":\n            self.pph31_refresh_access()\n        elif name == "system3":\n            self.pph30_refresh_system()\n',
    "show page",
)
ui.write_text(text, encoding="utf-8")

(PAYLOAD / "pph_version.py").write_text(
    'from __future__ import annotations\n\nVERSION = "3.1.0"\nCHANNEL = "stable"\nBUILD_NAME = "PPH 3.1.0 · Access Point"\nSCHEMA_VERSION = 3\n',
    encoding="utf-8",
)

test = PAYLOAD / "test_access_point_310.py"
test.write_text(
    '''from pathlib import Path\nimport sys\nROOT = Path(__file__).resolve().parent\nHUB = ROOT / "pph_hub"\nsys.path.insert(0, str(HUB))\nfrom access_point import bars_for_speed\nassert [bars_for_speed(x) for x in (0, 1, 10, 50, 100)] == [0, 1, 2, 3, 4]\nui=(HUB/"pph3_ui.py").read_text(encoding="utf-8")\napp=(HUB/"pph3_app.py").read_text(encoding="utf-8")\nassert '("ACCESS", "access3")' in ui\nassert 'self.pph31_build_access()' in ui\nassert 'install_access' in app\nprint("PPH 3.1 Access Point tests OK")\n''',
    encoding="utf-8",
)

for path in (PAYLOAD / "pph_hub/access_point.py", PAYLOAD / "pph_hub/access_ui.py", ui, app):
    subprocess.run(["python3", "-m", "py_compile", str(path)], check=True)
subprocess.run(["python3", str(test)], cwd=PAYLOAD, check=True)

for cache in PAYLOAD.rglob("__pycache__"):
    shutil.rmtree(cache)

files = []
for path in sorted(p for p in PAYLOAD.rglob("*") if p.is_file()):
    rel = path.relative_to(PAYLOAD).as_posix()
    mode = "0755" if rel in {"start_pph_hub.sh", "pph_hub/pph3_app.py"} else "0644"
    files.append({"path": rel, "sha256": sha256(path), "mode": mode})
manifest = {
    "format": 1,
    "product": "pph-funktest",
    "version": "3.1.0",
    "min_version": "3.0.0",
    "max_version": "3.0.99",
    "channel": "stable",
    "build_name": "PPH 3.1.0 · Access Point",
    "released": "2026-08-10",
    "tests": ["test_v2.py", "test_measurement_targets.py", "test_core_platform_28.py", "test_github_updates_29.py", "test_ui_300.py", "test_access_point_310.py"],
    "features": [
        "Neuer ACCESS-Point-Tab im PPH 3 Control Center",
        "LAN-Uplink über BrosTrend mt7921u als eigenes WLAN",
        "Eigene SSID und WPA2-Passwort direkt am Touchdisplay",
        "2.4-GHz- und 5-GHz-Modus",
        "Live-Gesamtgeschwindigkeit, RX, TX und verbundene Geräte",
        "Vier dynamische Geschwindigkeitsbalken",
        "Token-geschützte lokale Laptop-API auf TCP 8788",
        "Adapter-Erkennung über mt7921u statt feste wlanX-Namen",
        "Offline-Betrieb nach Installation"
    ],
    "files": files,
}
(WORK / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

OUT_DIR.mkdir(parents=True, exist_ok=True)
with tarfile.open(OUT, "w:gz") as tf:
    tf.add(WORK / "manifest.json", arcname="manifest.json")
    tf.add(PAYLOAD, arcname="payload")
package_sha = sha256(OUT)
(OUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(OUT_DIR / "sha256.txt").write_text(f"{package_sha}  {OUT.name}\n", encoding="utf-8")

stable = {
    "product": "pph-funktest",
    "channel": "stable",
    "version": "3.1.0",
    "released": "2026-08-10",
    "build_name": "PPH 3.1.0 · Access Point",
    "repository": "lucahmb/PPH-Update",
    "package_url": "https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v3.1.0/pph-update-3.1.0-access-point.tar.gz",
    "sha256": package_sha,
    "min_version": "3.0.0",
    "max_version": "3.0.99",
    "notes": [
        "ACCESS POINT direkt im PPH 3 Control Center",
        "LAN -> BrosTrend mt7921u -> eigenes WLAN mit eigener SSID und Passwort",
        "Live Mbit/s, RX/TX, Client-Anzahl und dynamische WLAN-Balken",
        "2.4/5 GHz Auswahl und Start/Stop am Touchdisplay",
        "Laptop-Steuerung lokal über Port 8788 und Token",
        "Keine feste wlanX-Bindung"
    ]
}
(ROOT / "channels/stable.json").write_text(json.dumps(stable, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Built {OUT} sha256={package_sha}")
