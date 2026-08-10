#!/usr/bin/env python3
from __future__ import annotations

import hashlib, json, shutil, subprocess, tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "packages/v3.1.0/pph-update-3.1.0-access-point.tar.gz"
WORK = Path("/tmp/pph311")
PAYLOAD = WORK / "payload"
OUT_DIR = ROOT / "packages/v3.1.1"
OUT = OUT_DIR / "pph-update-3.1.1-access-point-fix.tar.gz"

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

if WORK.exists(): shutil.rmtree(WORK)
WORK.mkdir(parents=True)
with tarfile.open(BASE, "r:gz") as tf: tf.extractall(WORK)

# Reuse the fixed 3.1 source modules: 12-digit numeric WLAN password/token + visible password UI.
shutil.copy2(ROOT / "src/v3.1.0/access_point.py", PAYLOAD / "pph_hub/access_point.py")
shutil.copy2(ROOT / "src/v3.1.0/access_ui.py", PAYLOAD / "pph_hub/access_ui.py")
(PAYLOAD / "pph_version.py").write_text(
    'from __future__ import annotations\n\nVERSION = "3.1.1"\nCHANNEL = "stable"\nBUILD_NAME = "PPH 3.1.1 · Access Point Fix"\nSCHEMA_VERSION = 3\n',
    encoding="utf-8",
)

test = PAYLOAD / "test_access_point_311.py"
test.write_text('''from pathlib import Path\nimport sys\nROOT=Path(__file__).resolve().parent\nHUB=ROOT/"pph_hub"\nsys.path.insert(0,str(HUB))\nfrom access_point import _digits,bars_for_speed\nfor _ in range(20):\n    x=_digits(12); assert len(x)==12 and x.isdigit()\nui=(HUB/"access_ui.py").read_text(encoding="utf-8")\nassert "WLAN-PASSWORT (12 ZIFFERN)" in ui\nassert "password.isdigit()" in ui\nprint("PPH 3.1.1 tests OK")\n''', encoding="utf-8")

for path in (PAYLOAD/"pph_hub/access_point.py", PAYLOAD/"pph_hub/access_ui.py"):
    subprocess.run(["python3","-m","py_compile",str(path)], check=True)
subprocess.run(["python3",str(test)], cwd=PAYLOAD, check=True)
for cache in PAYLOAD.rglob("__pycache__"): shutil.rmtree(cache)

files=[]
for path in sorted(p for p in PAYLOAD.rglob("*") if p.is_file()):
    rel=path.relative_to(PAYLOAD).as_posix()
    mode="0755" if rel in {"start_pph_hub.sh","pph_hub/pph3_app.py"} else "0644"
    files.append({"path":rel,"sha256":sha256(path),"mode":mode})
manifest={
    "format":1,"product":"pph-funktest","version":"3.1.1","min_version":"3.1.0","max_version":"3.1.0",
    "channel":"stable","build_name":"PPH 3.1.1 · Access Point Fix","released":"2026-08-10",
    "tests":["test_access_point_311.py"],
    "features":[
        "WLAN-Passwort wird automatisch als zufällige 12-stellige Zahl erzeugt",
        "Laptop-Pairing-Token wird automatisch als zufällige 12-stellige Zahl erzeugt",
        "Alte lange Tokens werden beim ersten Start automatisch ersetzt",
        "Standardpasswort ChangeMe123! wird automatisch ersetzt",
        "12-stelliges WLAN-Passwort wird im ACCESS-Menü sichtbar angezeigt und validiert"
    ],"files":files}
(WORK/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
OUT_DIR.mkdir(parents=True,exist_ok=True)
with tarfile.open(OUT,"w:gz") as tf:
    tf.add(WORK/"manifest.json",arcname="manifest.json"); tf.add(PAYLOAD,arcname="payload")
package_sha=sha256(OUT)
(OUT_DIR/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
(OUT_DIR/"sha256.txt").write_text(f"{package_sha}  {OUT.name}\n",encoding="utf-8")
stable={
    "product":"pph-funktest","channel":"stable","version":"3.1.1","released":"2026-08-10","build_name":"PPH 3.1.1 · Access Point Fix",
    "repository":"lucahmb/PPH-Update","package_url":"https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v3.1.1/pph-update-3.1.1-access-point-fix.tar.gz",
    "sha256":package_sha,"min_version":"3.1.0","max_version":"3.1.0",
    "notes":["12-stelliges numerisches WLAN-Passwort","12-stelliger numerischer Laptop-Token","ACCESS UI zeigt und validiert das Passwort"]}
(ROOT/"channels/stable.json").write_text(json.dumps(stable,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(f"Built {OUT} sha256={package_sha}")
