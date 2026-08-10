from pathlib import Path
import py_compile, sys
ROOT = Path(__file__).resolve().parent
HUB = ROOT / "pph_hub"
for p in (HUB / "access_point.py", HUB / "pph50_platform.py", HUB / "pph42_full_ui.py"):
    py_compile.compile(str(p), doraise=True)
ap = (HUB / "access_point.py").read_text()
platform = (HUB / "pph50_platform.py").read_text()
full_ui = (HUB / "pph42_full_ui.py").read_text()
assert '"pairing_code":self.token' in ap, "Access Point status() must expose the pairing code"
assert "s.get('internet',False)" in platform, "Connection Flow must read the real 'internet' status key"
assert "s.get('internet_ok'" not in platform, "stale 'internet_ok' key must not be read anymore"
assert "import json" in full_ui.splitlines()[2], "pph42_full_ui.py must import json for the REPORTS panel"
print("PPH 5.1.1 Access Point + Connection Flow fix tests OK")
