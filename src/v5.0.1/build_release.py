#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v4.2.0/pph-update-4.2.0-full-ui-rewrite.tar.gz'
WORK=Path('/tmp/pph501'); EXTRACT=WORK/'extract'; PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v5.0.1'; OUT=OUT_DIR/'pph-update-5.0.1-fieldctl-hotfix.tar.gz'
def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if WORK.exists(): shutil.rmtree(WORK)
EXTRACT.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(EXTRACT)
# Detect the real payload root instead of assuming archive nesting.
roots=[]
for f in EXTRACT.rglob('fieldctl.py'):
    r=f.parent
    if (r/'pph_hub/pph3_app.py').exists(): roots.append(r)
if not roots:
    raise SystemExit('Could not locate payload root containing fieldctl.py + pph_hub/pph3_app.py')
SRC=min(roots,key=lambda p:len(p.parts))
shutil.copytree(SRC,PAYLOAD)
# Add the 5.0 platform layer to the known-good 4.2 payload.
shutil.copy2(ROOT/'src/v5.0.0/pph50_platform.py',PAYLOAD/'pph_hub/pph50_platform.py')
launcher=PAYLOAD/'pph_hub/pph3_app.py'
t=launcher.read_text(encoding='utf-8')
if 'install50' not in t:
    t=t.replace('if __name__ == "__main__":','from pph50_platform import install as install50\ninstall50(hub.PolishedPPHApp, vars(hub))\n\nif __name__ == "__main__":',1)
launcher.write_text(t,encoding='utf-8')
# Compatibility alias for the typo seen on field units.
alias=PAYLOAD/'fielddctl.py'
alias.write_text("#!/usr/bin/env python3\nfrom pathlib import Path\nimport runpy\nrunpy.run_path(str(Path(__file__).with_name('fieldctl.py')), run_name='__main__')\n",encoding='utf-8')
(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\nVERSION="5.0.1"\nCHANNEL="stable"\nBUILD_NAME="PPH 5.0.1 · Fieldctl Packaging Hotfix"\nSCHEMA_VERSION=5\n',encoding='utf-8')
subprocess.run(['python3','-m','py_compile',str(PAYLOAD/'pph_hub/pph50_platform.py'),str(launcher),str(alias)],check=True)
for c in PAYLOAD.rglob('__pycache__'): shutil.rmtree(c)
files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file() and x.name!='manifest.json'):
    rel=p.relative_to(PAYLOAD).as_posix()
    mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','fieldctl.py','fielddctl.py','install_field_mode.sh'} else '0644'
    files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'5.0.1','min_version':'4.2.0','max_version':'5.0.0','channel':'stable','build_name':'PPH 5.0.1 · Fieldctl Packaging Hotfix','released':'2026-08-10','features':['PPH 5.0 Field Platform','fieldctl.py guaranteed','fielddctl.py compatibility alias','canonical payload root','tarball content validation'],'files':files}
(PAYLOAD/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
OUT_DIR.mkdir(parents=True,exist_ok=True)
with tarfile.open(OUT,'w:gz') as tf:
    for p in sorted(PAYLOAD.rglob('*')): tf.add(p,arcname=p.relative_to(PAYLOAD))
with tarfile.open(OUT,'r:gz') as tf:
    names=set(tf.getnames())
required={'fieldctl.py','fielddctl.py','install_field_mode.sh','manifest.json','pph_hub/pph50_platform.py','pph_hub/pph3_app.py','pph_hub/pph42_full_ui.py'}
missing=sorted(required-names)
if missing: raise SystemExit('tarball missing: '+', '.join(missing))
channel={'product':'pph-funktest','channel':'stable','version':'5.0.1','released':'2026-08-10','build_name':'PPH 5.0.1 · Fieldctl Packaging Hotfix','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v5.0.1/pph-update-5.0.1-fieldctl-hotfix.tar.gz','sha256':sha256(OUT),'min_version':'4.2.0','max_version':'5.0.0','notes':['Fix fieldctl packaging','Compatibility alias fielddctl.py','Full PPH 5.0 Field Platform retained']}
(OUT_DIR/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
(ROOT/'channels/stable.json').write_text(json.dumps(channel,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(OUT)
