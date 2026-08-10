#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v5.1.2/pph-update-5.1.2-startup-crash-fix.tar.gz'
WORK=Path('/tmp/pph513'); EXTRACT=WORK/'extract'; PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v5.1.3'; OUT=OUT_DIR/'pph-update-5.1.3-launcher-false-positive-fix.tar.gz'

def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if WORK.exists(): shutil.rmtree(WORK)
EXTRACT.mkdir(parents=True); PAYLOAD.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(EXTRACT)
source=EXTRACT/'payload'
if not source.is_dir(): raise SystemExit('5.1.2 payload directory missing')
for item in source.iterdir():
    dest=PAYLOAD/item.name
    if item.is_dir(): shutil.copytree(item,dest)
    else: shutil.copy2(item,dest)

# Critical fix: start_pph_hub.sh's hub_running() scans every process's cmdline and
# calls Path(arg).resolve() to compare it against the hub's script path. For a
# RELATIVE argv entry, Path.resolve() resolves against the *checker's own* cwd, not
# the cwd of the process being inspected. Any unrelated process (e.g. a validation
# subprocess spawned by the updater, invoked with a relative argument like
# "pph_hub/pph3_app.py" from the same working directory) could therefore be
# misidentified as an already-running PPH Hub. When that happens, start_pph_hub.sh
# prints "PPH Hub läuft bereits." and exits 0 WITHOUT ever launching pph3_app.py -
# so the systemd user service just exits "successfully" over and over and the GUI
# never opens at all.
launcher=PAYLOAD/'start_pph_hub.sh'
if launcher.exists():
    t=launcher.read_text(encoding='utf-8')
    old=(
        "        for arg in args[1:]:\n"
        "            try:\n"
        "                if str(Path(arg).resolve()) == target:\n"
        "                    raise SystemExit(0)\n"
        "            except OSError:\n"
        "                continue\n"
    )
    new=(
        "        try:\n"
        "            proc_cwd = Path(f\"/proc/{entry.name}/cwd\").resolve()\n"
        "        except OSError:\n"
        "            proc_cwd = None\n"
        "        for arg in args[1:]:\n"
        "            try:\n"
        "                candidate = Path(arg)\n"
        "                if not candidate.is_absolute():\n"
        "                    if proc_cwd is None:\n"
        "                        continue\n"
        "                    candidate = proc_cwd / candidate\n"
        "                if str(candidate.resolve()) == target:\n"
        "                    raise SystemExit(0)\n"
        "            except OSError:\n"
        "                continue\n"
    )
    if old not in t: raise SystemExit('start_pph_hub.sh: hub_running() anchor not found')
    t=t.replace(old,new,1)
    launcher.write_text(t,encoding='utf-8')

(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\nVERSION="5.1.3"\nCHANNEL="stable"\nBUILD_NAME="PPH 5.1.3 · Launcher False-Positive Fix"\nSCHEMA_VERSION=5\n',encoding='utf-8')

test_file=PAYLOAD/'test_launcher_513.py'
shutil.copy2(ROOT/'src/v5.1.3/test_launcher_513.py',test_file)

subprocess.run(['bash','-n',str(launcher)],check=True)
subprocess.run(['python3','-m','py_compile',str(PAYLOAD/'pph_version.py')],check=True)
subprocess.run(['python3',str(test_file)],cwd=PAYLOAD,check=True)
for c in PAYLOAD.rglob('__pycache__'): shutil.rmtree(c)

files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
    rel=p.relative_to(PAYLOAD).as_posix(); mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','fieldctl.py','fielddctl.py','install_field_mode.sh'} else '0644'
    files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'5.1.3','min_version':'5.1.0','max_version':'5.1.2','channel':'stable','build_name':'PPH 5.1.3 · Launcher False-Positive Fix','released':'2026-08-10','features':['Fix: hub_running() resolved relative argv paths against its own cwd instead of the inspected process’s cwd, causing unrelated processes to be misdetected as an already-running PPH Hub - start_pph_hub.sh then exited 0 without ever launching the app, so the systemd user service silently gave up with no window at all'],'files':files}
OUT_DIR.mkdir(parents=True,exist_ok=True)
mp=WORK/'manifest.json'; mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
with tarfile.open(OUT,'w:gz') as tf:
    tf.add(mp,arcname='manifest.json')
    for p in sorted(PAYLOAD.rglob('*')): tf.add(p,arcname='payload/'+p.relative_to(PAYLOAD).as_posix())
with tarfile.open(OUT,'r:gz') as tf:
    names=set(tf.getnames())
    req={'manifest.json','payload/start_pph_hub.sh','payload/pph_version.py'}
    miss=sorted(req-names)
    if miss: raise SystemExit('Archive invalid: '+', '.join(miss))
(OUT_DIR/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
channel={'product':'pph-funktest','channel':'stable','version':'5.1.3','released':'2026-08-10','build_name':'PPH 5.1.3 · Launcher False-Positive Fix','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v5.1.3/pph-update-5.1.3-launcher-false-positive-fix.tar.gz','sha256':sha256(OUT),'min_version':'5.1.0','max_version':'5.1.2','notes':['Fixes a launcher bug where an unrelated process with a relative argv path could be mistaken for an already-running PPH Hub, silently preventing startup','Applies whether the device is currently on 5.1.0, 5.1.1 or 5.1.2']}
(ROOT/'channels/stable.json').write_text(json.dumps(channel,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(OUT)
