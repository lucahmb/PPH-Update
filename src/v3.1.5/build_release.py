#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v3.1.4/pph-update-3.1.4-field-mode.tar.gz'
WORK=Path('/tmp/pph315'); PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v3.1.5'; OUT=OUT_DIR/'pph-update-3.1.5-ui-update-fix.tar.gz'
def sha256(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def rep(t,o,n,l):
    if o not in t: raise SystemExit(f'missing patch anchor: {l}')
    return t.replace(o,n,1)
if WORK.exists(): shutil.rmtree(WORK)
WORK.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(WORK)
ui=PAYLOAD/'pph_hub/pph3_ui.py'
t=ui.read_text(encoding='utf-8')
t=rep(t,'import tkinter as tk\n','import tkinter as tk\nimport json\nimport time\nimport urllib.request\n','fresh update imports')
insert='''\n    def fresh_stable_version() -> str | None:\n        url = f"https://raw.githubusercontent.com/lucahmb/PPH-Update/main/channels/stable.json?_={int(time.time())}"\n        try:\n            req = urllib.request.Request(url, headers={"User-Agent":"PPH/3.1.5", "Cache-Control":"no-cache", "Pragma":"no-cache"})\n            with urllib.request.urlopen(req, timeout=5) as response:\n                data = json.load(response)\n            return str(data.get("version") or "") or None\n        except Exception:\n            return None\n\n    def force_open_update(self) -> None:\n        self.footer_var.set("Update-Status wird frisch geladen …")\n        try:\n            self._pph29_trigger_update_check(True, "manual-fresh")\n        except Exception:\n            pass\n        try:\n            self.root.after(900, self._pph28_open_update)\n        except tk.TclError:\n            pass\n\n'''
t=rep(t,'    def nav_button(self, parent: tk.Misc, label: str, target: str) -> tk.Button:\n',insert+'    def nav_button(self, parent: tk.Misc, label: str, target: str) -> tk.Button:\n','fresh helpers')
t=rep(t,'        controls.pack(side="right", padx=(0, 8), pady=7)\n','        controls.place(relx=1.0, x=-6, y=7, anchor="ne")\n','responsive top controls')
t=t.replace('text="CHECK UPDATES"','text="UPDATES"',1)
t=t.replace('command=lambda: self._pph28_open_update(),','command=lambda: force_open_update(self),',2)
t=t.replace('(\"CHECK UPDATES\", self._pph28_open_update, PURPLE),','(\"UPDATES\", lambda: force_open_update(self), PURPLE),',1)
old='''        try:\n            cache = updates._read_remote_cache()\n            manifest = cache.get("manifest") if isinstance(cache.get("manifest"), dict) else {}\n            remote_version = str(manifest.get("version") or "—")\n            self.pph30_home_update.set(f"Stable {remote_version} · installiert {updates.installed_version()}")\n        except Exception:\n            self.pph30_home_update.set(f"Installiert {updates.installed_version()}")'''
new='''        try:\n            remote_version = fresh_stable_version()\n            if not remote_version:\n                cache = updates._read_remote_cache()\n                manifest = cache.get("manifest") if isinstance(cache.get("manifest"), dict) else {}\n                remote_version = str(manifest.get("version") or "—")\n            self.pph30_home_update.set(f"Stable {remote_version} · installiert {updates.installed_version()}")\n        except Exception:\n            self.pph30_home_update.set(f"Installiert {updates.installed_version()}")'''
t=rep(t,old,new,'home fresh stable')
old2='''        try:\n            cache = updates._read_remote_cache()\n            checked = str(cache.get("checked_at") or "noch nie")\n            manifest = cache.get("manifest") if isinstance(cache.get("manifest"), dict) else {}\n            remote = str(manifest.get("version") or "—")\n        except Exception:\n            checked, remote = "—", "—"'''
new2='''        try:\n            cache = updates._read_remote_cache()\n            checked = str(cache.get("checked_at") or "noch nie")\n            manifest = cache.get("manifest") if isinstance(cache.get("manifest"), dict) else {}\n            remote = fresh_stable_version() or str(manifest.get("version") or "—")\n        except Exception:\n            checked, remote = "—", fresh_stable_version() or "—"'''
t=rep(t,old2,new2,'settings fresh stable')
ui.write_text(t,encoding='utf-8')
(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\n\nVERSION = "3.1.5"\nCHANNEL = "stable"\nBUILD_NAME = "PPH 3.1.5 · UI + Update Refresh Fix"\nSCHEMA_VERSION = 3\n',encoding='utf-8')
test=PAYLOAD/'test_ui_315.py'
test.write_text('''from pathlib import Path\nROOT=Path(__file__).resolve().parent\nui=(ROOT/"pph_hub/pph3_ui.py").read_text(encoding="utf-8")\nassert 'controls.place(relx=1.0' in ui\nassert 'fresh_stable_version' in ui\nassert 'manual-fresh' in ui\nassert 'Cache-Control' in ui\nassert 'text="UPDATES"' in ui\nprint("PPH 3.1.5 tests OK")\n''',encoding='utf-8')
subprocess.run(['python3','-m','py_compile',str(ui)],check=True)
subprocess.run(['python3',str(test)],cwd=PAYLOAD,check=True)
for c in PAYLOAD.rglob('__pycache__'): shutil.rmtree(c)
files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
    rel=p.relative_to(PAYLOAD).as_posix(); mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','fieldctl.py','install_field_mode.sh'} else '0644'
    files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'3.1.5','min_version':'3.1.4','max_version':'3.1.4','channel':'stable','build_name':'PPH 3.1.5 · UI + Update Refresh Fix','released':'2026-08-10','tests':['test_ui_315.py'],'features':['Topbar bleibt auf 800x480 im Vollbild sichtbar','UPDATES/Home/Fullscreen/Close werden rechts fest verankert','Manueller Update-Check erzwingt Fresh-Refresh statt altem Cache','Home und Settings lesen Stable-Version mit Cache-Buster','PPH 3.1.4 Field Mode bleibt vollständig enthalten'],'files':files}
(WORK/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
OUT_DIR.mkdir(parents=True,exist_ok=True)
with tarfile.open(OUT,'w:gz') as tf: tf.add(WORK/'manifest.json',arcname='manifest.json'); tf.add(PAYLOAD,arcname='payload')
package_sha=sha256(OUT)
(OUT_DIR/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT_DIR/'sha256.txt').write_text(f'{package_sha}  {OUT.name}\n',encoding='utf-8')
stable={'product':'pph-funktest','channel':'stable','version':'3.1.5','released':'2026-08-10','build_name':'PPH 3.1.5 · UI + Update Refresh Fix','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v3.1.5/pph-update-3.1.5-ui-update-fix.tar.gz','sha256':package_sha,'min_version':'3.1.4','max_version':'3.1.4','notes':['Fullscreen Topbar Fix','Fresh Update Check ohne alten Cache','Field Mode 3.1.4 enthalten']}
(ROOT/'channels/stable.json').write_text(json.dumps(stable,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Built {OUT} sha256={package_sha}')
