#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v3.1.6/pph-update-3.1.6-direct-from-313.tar.gz'
WORK=Path('/tmp/pph317'); PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v3.1.7'; OUT=OUT_DIR/'pph-update-3.1.7-display-layer-fix.tar.gz'
def sha256(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def rep(t,o,n,l):
    if o not in t: raise SystemExit(f'missing patch anchor: {l}')
    return t.replace(o,n,1)
if WORK.exists(): shutil.rmtree(WORK)
WORK.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(WORK)
ui=PAYLOAD/'pph_hub/pph3_ui.py'
t=ui.read_text(encoding='utf-8')
t=rep(t,'    original_go_home = cls.go_home\n','    original_go_home = cls.go_home\n    original_toggle_fullscreen = cls.toggle_fullscreen\n','fullscreen hook')
t=rep(t,'        controls = tk.Frame(header, bg=SURFACE)\n        controls.place(relx=1.0, x=-6, y=7, anchor="ne")\n','        controls = tk.Frame(header, bg=SURFACE)\n        controls.place(relx=1.0, x=-6, y=7, anchor="ne")\n        self.pph30_header = header\n        self.pph30_controls = controls\n','store header controls')
insert='''\n    def _pph317_raise_header(self) -> None:\n        try:\n            header=getattr(self,"pph30_header",None)\n            controls=getattr(self,"pph30_controls",None)\n            if header is not None:\n                header.lift()\n                header.configure(bg=SURFACE)\n            if controls is not None:\n                controls.lift()\n                controls.configure(bg=SURFACE)\n            for name in ("pph_check_updates_button","pph_update_badge","settings_button","home_button","fullscreen_button","close_button","back_button"):\n                widget=getattr(self,name,None)\n                if widget is not None:\n                    widget.lift()\n            self.root.update_idletasks()\n        except tk.TclError:\n            pass\n\n    def toggle_fullscreen(self) -> None:\n        original_toggle_fullscreen(self)\n        for delay in (0,40,120,300):\n            try:\n                self.root.after(delay, lambda s=self: _pph317_raise_header(s))\n            except tk.TclError:\n                pass\n\n'''
t=rep(t,'    def go_home(self) -> None:\n',insert+'    def go_home(self) -> None:\n','z-order methods')
t=rep(t,'    cls.go_home = go_home\n','    cls.go_home = go_home\n    cls.toggle_fullscreen = toggle_fullscreen\n    cls._pph317_raise_header = _pph317_raise_header\n','install fullscreen override')
ui.write_text(t,encoding='utf-8')
(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\n\nVERSION = "3.1.7"\nCHANNEL = "stable"\nBUILD_NAME = "PPH 3.1.7 · Display Layer Fix"\nSCHEMA_VERSION = 3\n',encoding='utf-8')
test=PAYLOAD/'test_ui_317.py'
test.write_text('''from pathlib import Path\nROOT=Path(__file__).resolve().parent\nui=(ROOT/"pph_hub/pph3_ui.py").read_text(encoding="utf-8")\nassert 'original_toggle_fullscreen = cls.toggle_fullscreen' in ui\nassert 'header.lift()' in ui\nassert 'controls.lift()' in ui\nassert 'self.root.update_idletasks()' in ui\nassert 'for delay in (0,40,120,300)' in ui\nassert 'cls.toggle_fullscreen = toggle_fullscreen' in ui\nprint("PPH 3.1.7 tests OK")\n''',encoding='utf-8')
subprocess.run(['python3','-m','py_compile',str(ui)],check=True)
subprocess.run(['python3',str(test)],cwd=PAYLOAD,check=True)
for c in PAYLOAD.rglob('__pycache__'): shutil.rmtree(c)
files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
    rel=p.relative_to(PAYLOAD).as_posix(); mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','fieldctl.py','install_field_mode.sh'} else '0644'
    files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'3.1.7','min_version':'3.1.3','max_version':'3.1.6','channel':'stable','build_name':'PPH 3.1.7 · Display Layer Fix','released':'2026-08-10','tests':['test_ui_317.py'],'features':['Fullscreen Z-Order Fix für unsichtbare aber klickbare Topbar-Buttons','Header/Controls werden nach Fullscreen mehrfach angehoben und neu gezeichnet','Field Mode und alle 3.1.6 Fixes enthalten','Direktes Upgrade ab 3.1.3 möglich'],'files':files}
(WORK/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
OUT_DIR.mkdir(parents=True,exist_ok=True)
with tarfile.open(OUT,'w:gz') as tf: tf.add(WORK/'manifest.json',arcname='manifest.json'); tf.add(PAYLOAD,arcname='payload')
package_sha=sha256(OUT)
(OUT_DIR/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT_DIR/'sha256.txt').write_text(f'{package_sha}  {OUT.name}\n',encoding='utf-8')
stable={'product':'pph-funktest','channel':'stable','version':'3.1.7','released':'2026-08-10','build_name':'PPH 3.1.7 · Display Layer Fix','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v3.1.7/pph-update-3.1.7-display-layer-fix.tar.gz','sha256':package_sha,'min_version':'3.1.3','max_version':'3.1.6','notes':['Fullscreen invisible-buttons Z-order fix','Field Mode enthalten','Direktes Upgrade ab 3.1.3']}
(ROOT/'channels/stable.json').write_text(json.dumps(stable,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Built {OUT} sha256={package_sha}')
