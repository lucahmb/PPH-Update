#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, shutil, subprocess, tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'packages/v3.1.7/pph-update-3.1.7-display-layer-fix.tar.gz'
WORK = Path('/tmp/pph320')
PAYLOAD = WORK / 'payload'
OUT_DIR = ROOT / 'packages/v3.2.0'
OUT = OUT_DIR / 'pph-update-3.2.0-field-analyzer.tar.gz'

def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f'missing patch anchor: {label}')
    return text.replace(old, new, 1)

if WORK.exists():
    shutil.rmtree(WORK)
WORK.mkdir(parents=True)
with tarfile.open(BASE, 'r:gz') as tf:
    tf.extractall(WORK)

ui32 = r'''#!/usr/bin/env python3
from __future__ import annotations

import socket
import subprocess
import threading
import time
import tkinter as tk
from typing import Any


def install(cls: type, ns: dict[str, Any]) -> None:
    BG=ns['BG']; SURFACE=ns['SURFACE']; SURFACE2=ns['SURFACE2']; SURFACE3=ns['SURFACE3']; BORDER=ns['BORDER']
    TEXT=ns['TEXT']; MUTED=ns['MUTED']; CYAN=ns['CYAN']; GREEN=ns['GREEN']; YELLOW=ns['YELLOW']; RED=ns['RED']; PURPLE=ns['PURPLE']; ORANGE=ns['ORANGE']
    from hardware_roles import adapter_overview

    previous_build_pages = cls._build_pages
    previous_show_page = cls.show_page

    def card(self, parent, title, value_var, detail_var, accent, value_size=18):
        frame=tk.Frame(parent,bg=SURFACE,highlightthickness=1,highlightbackground=BORDER)
        tk.Frame(frame,bg=accent,height=4).pack(fill='x')
        body=tk.Frame(frame,bg=SURFACE); body.pack(fill='both',expand=True,padx=10,pady=7)
        tk.Label(body,text=title,bg=SURFACE,fg=MUTED,font=self._font(7,'bold'),anchor='w').pack(fill='x')
        tk.Label(body,textvariable=value_var,bg=SURFACE,fg=accent,font=self._font(value_size,'bold'),anchor='w').pack(fill='x')
        tk.Label(body,textvariable=detail_var,bg=SURFACE,fg=TEXT,font=self._font(7),anchor='w',justify='left',wraplength=170).pack(fill='x')
        return frame

    def build_home32(self):
        page=self._new_page('home32','PPH FIELD CENTER')
        head=tk.Frame(page,bg=BG); head.pack(fill='x',padx=12,pady=(7,3))
        tk.Label(head,text='PPH FIELD CENTER',bg=BG,fg=TEXT,font=self._font(15,'bold')).pack(side='left')
        self.pph32_top_status=tk.StringVar(value='LAN —   AP —   RADIO —')
        tk.Label(head,textvariable=self.pph32_top_status,bg=BG,fg=CYAN,font=self._font(8,'bold')).pack(side='right')
        self.pph32_home={k:tk.StringVar(value='—') for k in ('net','netd','wifi','wifid','ap','apd','sys','sysd')}
        cards=tk.Frame(page,bg=BG); cards.pack(fill='x',padx=8,pady=3)
        defs=[('NETWORK','net','netd',CYAN),('RADIOS','wifi','wifid',ORANGE),('ACCESS POINT','ap','apd',GREEN),('SYSTEM','sys','sysd',PURPLE)]
        for c,(title,v,d,a) in enumerate(defs):
            cards.grid_columnconfigure(c,weight=1,uniform='pph32home')
            card(self,cards,title,self.pph32_home[v],self.pph32_home[d],a,15).grid(row=0,column=c,sticky='nsew',padx=3)
        actions=tk.Frame(page,bg=BG); actions.pack(fill='both',expand=True,padx=8,pady=5)
        for c in range(3): actions.grid_columnconfigure(c,weight=1,uniform='pph32actions')
        for r in range(2): actions.grid_rowconfigure(r,weight=1,uniform='pph32actions')
        defs=[
            ('QUICK TEST',lambda:self.show_page('quick32'),CYAN),
            ('NETWORK ANALYZER',lambda:self.show_page('analyzer32'),PURPLE),
            ('RADIO CENTER',lambda:self.show_page('wifi32'),ORANGE),
            ('NETWORK DOCTOR',lambda:self.show_page('doctor32'),GREEN),
            ('ACCESS POINT',lambda:self.show_page('access3'),SURFACE2),
            ('SYSTEM / EVENTS',lambda:self.show_page('system3'),SURFACE2),
        ]
        for i,(label,cmd,a) in enumerate(defs):
            self._button(actions,label,cmd,bg=a,active=CYAN,size=9,pady=8).grid(row=i//3,column=i%3,sticky='nsew',padx=4,pady=4)

    def build_analyzer32(self):
        page=self._new_page('analyzer32','NETWORK ANALYZER')
        self.pph32_an={k:tk.StringVar(value='—') for k in ('status','phase','dl','ul','ping','jitter','loss','radio','detail')}
        head=tk.Frame(page,bg=BG); head.pack(fill='x',padx=12,pady=(7,2))
        tk.Label(head,text='PPH NETWORK ANALYZER',bg=BG,fg=TEXT,font=self._font(14,'bold')).pack(side='left')
        tk.Label(head,textvariable=self.pph32_an['status'],bg=SURFACE2,fg=CYAN,font=self._font(8,'bold'),padx=8,pady=4).pack(side='right')
        metrics=tk.Frame(page,bg=BG); metrics.pack(fill='x',padx=8,pady=3)
        defs=[('DOWNLOAD','dl',CYAN),('UPLOAD','ul',PURPLE),('PING','ping',YELLOW),('JITTER','jitter',ORANGE),('LOSS','loss',GREEN)]
        for c,(title,key,a) in enumerate(defs):
            metrics.grid_columnconfigure(c,weight=1,uniform='anmetrics')
            d=tk.StringVar(value='LIVE')
            card(self,metrics,title,self.pph32_an[key],d,a,14).grid(row=0,column=c,sticky='nsew',padx=2)
        strip=tk.Frame(page,bg=SURFACE,highlightthickness=1,highlightbackground=BORDER); strip.pack(fill='x',padx=11,pady=4)
        tk.Label(strip,text='PHASE',bg=SURFACE2,fg=MUTED,font=self._font(7,'bold'),padx=7,pady=5).pack(side='left')
        tk.Label(strip,textvariable=self.pph32_an['phase'],bg=SURFACE,fg=TEXT,font=self._font(8,'bold')).pack(side='left',padx=8)
        tk.Label(strip,text='RADIO',bg=SURFACE2,fg=MUTED,font=self._font(7,'bold'),padx=7,pady=5).pack(side='left')
        tk.Label(strip,textvariable=self.pph32_an['radio'],bg=SURFACE,fg=ORANGE,font=self._font(8,'bold')).pack(side='left',padx=8)
        tk.Label(strip,textvariable=self.pph32_an['detail'],bg=SURFACE,fg=MUTED,font=self._font(7),anchor='e').pack(side='right',fill='x',expand=True,padx=8)
        actions=tk.Frame(page,bg=BG); actions.pack(fill='both',expand=True,padx=8,pady=4)
        for c in range(4): actions.grid_columnconfigure(c,weight=1,uniform='anact')
        defs=[('START ANALYZER',self.launch_funktest,CYAN),('QUICK TEST',lambda:self.show_page('quick32'),GREEN),('REPORTS',lambda:previous_show_page(self,'reports'),SURFACE2),('RADIO CENTER',lambda:self.show_page('wifi32'),SURFACE2)]
        for c,(label,cmd,a) in enumerate(defs): self._button(actions,label,cmd,bg=a,active=CYAN,size=9,pady=8).grid(row=0,column=c,sticky='nsew',padx=3,pady=4)

    def build_wifi32(self):
        page=self._new_page('wifi32','RADIO CENTER')
        head=tk.Frame(page,bg=BG); head.pack(fill='x',padx=12,pady=(7,3))
        tk.Label(head,text='RADIO CENTER',bg=BG,fg=TEXT,font=self._font(14,'bold')).pack(side='left')
        self.pph32_wifi_summary=tk.StringVar(value='Adapter werden geprüft …')
        tk.Label(head,textvariable=self.pph32_wifi_summary,bg=BG,fg=MUTED,font=self._font(8)).pack(side='right')
        self.pph32_wifi_rows=tk.Frame(page,bg=BG); self.pph32_wifi_rows.pack(fill='both',expand=True,padx=11,pady=3)
        actions=tk.Frame(page,bg=BG); actions.pack(fill='x',padx=9,pady=(2,8))
        defs=[('START FUNKSCAN',self.launch_funktest,CYAN),('NETWORK DOCTOR',lambda:self.show_page('doctor32'),GREEN),('DFS / CHANNELS',self._pph28_show_dfs,ORANGE),('ACCESS POINT',lambda:self.show_page('access3'),PURPLE)]
        for c,(label,cmd,a) in enumerate(defs):
            actions.grid_columnconfigure(c,weight=1,uniform='wifi32a')
            self._button(actions,label,cmd,bg=a,active=CYAN,size=8,pady=6).grid(row=0,column=c,sticky='ew',padx=3)

    def build_quick32(self):
        page=self._new_page('quick32','QUICK TEST')
        self.pph32_quick_score=tk.StringVar(value='READY')
        self.pph32_quick_result=tk.StringVar(value='Ein Test prüft Uplink, Gateway, DNS, Internet, Radios und Access Point.')
        tk.Label(page,text='PPH QUICK TEST',bg=BG,fg=TEXT,font=self._font(15,'bold')).pack(anchor='w',padx=13,pady=(9,2))
        tk.Label(page,textvariable=self.pph32_quick_score,bg=BG,fg=GREEN,font=self._font(26,'bold')).pack(anchor='w',padx=13)
        tk.Label(page,textvariable=self.pph32_quick_result,bg=SURFACE,fg=TEXT,font=self._font(9),justify='left',anchor='nw',wraplength=740,padx=12,pady=10,highlightthickness=1,highlightbackground=BORDER).pack(fill='both',expand=True,padx=13,pady=5)
        row=tk.Frame(page,bg=BG); row.pack(fill='x',padx=10,pady=(0,9))
        self._button(row,'TEST STARTEN',self.pph32_run_quick,bg=CYAN,active=CYAN,size=9,pady=7).pack(side='left',fill='x',expand=True,padx=3)
        self._button(row,'NETWORK DOCTOR',lambda:self.show_page('doctor32'),bg=SURFACE2,active=CYAN,size=9,pady=7).pack(side='left',fill='x',expand=True,padx=3)

    def build_doctor32(self):
        page=self._new_page('doctor32','NETWORK DOCTOR')
        tk.Label(page,text='NETWORK DOCTOR',bg=BG,fg=TEXT,font=self._font(15,'bold')).pack(anchor='w',padx=13,pady=(9,2))
        self.pph32_doctor_status=tk.StringVar(value='Bereit')
        tk.Label(page,textvariable=self.pph32_doctor_status,bg=BG,fg=CYAN,font=self._font(8,'bold')).pack(anchor='w',padx=13)
        self.pph32_doctor_text=tk.Text(page,bg=SURFACE,fg=TEXT,relief='flat',bd=0,highlightthickness=1,highlightbackground=BORDER,font=self._font(9),wrap='word',padx=10,pady=8)
        self.pph32_doctor_text.pack(fill='both',expand=True,padx=13,pady=5); self.pph32_doctor_text.configure(state='disabled')
        row=tk.Frame(page,bg=BG); row.pack(fill='x',padx=10,pady=(0,9))
        self._button(row,'DIAGNOSE STARTEN',self.pph32_run_doctor,bg=CYAN,active=CYAN,size=9,pady=7).pack(side='left',fill='x',expand=True,padx=3)
        self.pph32_heal_button=self._button(row,'SELF-HEAL: AUS',self.pph32_toggle_heal,bg=SURFACE2,active=GREEN,size=9,pady=7)
        self.pph32_heal_button.pack(side='left',fill='x',expand=True,padx=3)

    def build_pages(self):
        previous_build_pages(self)
        build_home32(self); build_analyzer32(self); build_wifi32(self); build_quick32(self); build_doctor32(self)
        self.pph32_self_heal=False

    def show_page(self,name,title=None,*,push=True):
        aliases={'dashboard':'home32','home3':'home32','measure3':'analyzer32','wifi3':'wifi32'}
        name=aliases.get(name,name)
        previous_show_page(self,name,title,push=push)
        if name=='home32': self.pph32_refresh_home()
        elif name=='analyzer32': self.pph32_refresh_analyzer()
        elif name=='wifi32': self.pph32_refresh_wifi()

    def cmd(args,timeout=4):
        try:
            p=subprocess.run(args,text=True,capture_output=True,timeout=timeout,check=False)
            return p.returncode,(p.stdout or '').strip(),(p.stderr or '').strip()
        except Exception as exc: return 99,'',str(exc)

    def refresh_home(self):
        route=cmd(['ip','route','show','default'])[1]
        lan='eth0' in route
        try: ov=adapter_overview(); roles=ov.get('roles') or {}; radios=sum(1 for v in roles.values() if v)
        except Exception: radios=0
        ap={}
        try: ap=self.pph31_ap.status() if hasattr(self,'pph31_ap') else {}
        except Exception: pass
        self.pph32_home['net'].set('ONLINE' if route else 'OFFLINE'); self.pph32_home['netd'].set('eth0 Uplink' if lan else 'Default Route aktiv' if route else 'Kein Uplink')
        self.pph32_home['wifi'].set(f'{radios}/3'); self.pph32_home['wifid'].set('Onboard · BrosTrend · ALFA')
        self.pph32_home['ap'].set('ACTIVE' if ap.get('active') else 'OFF'); self.pph32_home['apd'].set(f"{ap.get('clients',0)} Clients · {float(ap.get('total_mbps') or 0):.1f} Mbit/s")
        temp=cmd(['bash','-lc',"cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || echo 0"])[1]
        try: tc=float(temp)/1000
        except Exception: tc=0
        self.pph32_home['sys'].set(f'{tc:.0f}°C' if tc else 'READY'); self.pph32_home['sysd'].set('Field services aktiv')
        self.pph32_top_status.set(f"LAN {'●' if lan else '○'}   AP {'●' if ap.get('active') else '○'}   RADIO {radios}/3")

    def refresh_analyzer(self):
        state=self._read_measurement_state(); running=self._measurement_running() or self._funktest_running()
        self.pph32_an['status'].set('● MEASURING' if running else 'READY')
        self.pph32_an['phase'].set(str(state.get('phase') or state.get('subtitle') or 'Bereit'))
        def fmt(key,suffix=' Mbit/s'):
            v=state.get(key); return f'{float(v):.1f}{suffix}' if isinstance(v,(int,float)) else '—'
        self.pph32_an['dl'].set(fmt('download_mbps')); self.pph32_an['ul'].set(fmt('upload_mbps'))
        ping=state.get('latency_ms',state.get('ping_ms')); self.pph32_an['ping'].set(f'{float(ping):.1f} ms' if isinstance(ping,(int,float)) else '—')
        jit=state.get('jitter_ms'); self.pph32_an['jitter'].set(f'{float(jit):.1f} ms' if isinstance(jit,(int,float)) else '—')
        loss=state.get('packet_loss_percent',state.get('loss_percent')); self.pph32_an['loss'].set(f'{float(loss):.1f} %' if isinstance(loss,(int,float)) else '—')
        try:
            ov=adapter_overview(); r=(ov.get('roles') or {}).get('measurement') or {}; self.pph32_an['radio'].set(f"{r.get('interface','—')} · {r.get('driver','—')}")
        except Exception: self.pph32_an['radio'].set('—')
        self.pph32_an['detail'].set(str(state.get('updated_at') or 'Keine Live-Messung'))
        if self.current_page=='analyzer32': self.root.after(1000,self.pph32_refresh_analyzer)

    def refresh_wifi(self):
        for w in self.pph32_wifi_rows.winfo_children(): w.destroy()
        try: ov=adapter_overview(); roles=ov.get('roles') or {}
        except Exception as exc: ov={'detail':str(exc)}; roles={}
        defs=[('control','ONBOARD · CONTROL',GREEN),('measurement','BROSTREND · FIELD / AP',CYAN),('scan','ALFA AWUS · ANALYSIS',ORANGE)]
        present=0
        for key,title,a in defs:
            r=roles.get(key) or {}; present+=bool(r)
            row=tk.Frame(self.pph32_wifi_rows,bg=SURFACE,highlightthickness=1,highlightbackground=BORDER); row.pack(fill='x',pady=3)
            tk.Frame(row,bg=a,width=6).pack(side='left',fill='y')
            body=tk.Frame(row,bg=SURFACE); body.pack(side='left',fill='both',expand=True,padx=10,pady=7)
            tk.Label(body,text=title,bg=SURFACE,fg=TEXT,font=self._font(9,'bold'),anchor='w').pack(fill='x')
            if r:
                main=f"{r.get('interface','—')} · {r.get('driver','—')} · {r.get('model','Adapter')}"
                sub=f"{r.get('iftype','managed')} · {r.get('operstate','—')}"
            else: main='NICHT ERKANNT'; sub='Adapter fehlt oder Treiber nicht aktiv'
            tk.Label(body,text=main,bg=SURFACE,fg=a,font=self._font(10,'bold'),anchor='w').pack(fill='x')
            tk.Label(body,text=sub,bg=SURFACE,fg=MUTED,font=self._font(8),anchor='w').pack(fill='x')
        self.pph32_wifi_summary.set(f'{present}/3 Radios erkannt')

    def run_quick(self):
        self.pph32_quick_score.set('TESTING …'); self.pph32_quick_result.set('Prüfung läuft …')
        def work():
            checks=[]; score=0
            route=cmd(['ip','route','show','default'])[1]; checks.append(('Uplink / Route',bool(route),route.splitlines()[0] if route else 'keine Default Route')); score+=20 if route else 0
            gateway=''
            parts=route.split()
            if 'via' in parts:
                try: gateway=parts[parts.index('via')+1]
                except Exception: pass
            okgw=bool(gateway and cmd(['ping','-c','1','-W','2',gateway],3)[0]==0); checks.append(('Gateway',okgw,gateway or 'nicht gefunden')); score+=20 if okgw else 0
            try: socket.gethostbyname('github.com'); dns=True
            except Exception: dns=False
            checks.append(('DNS',dns,'Namensauflösung')); score+=20 if dns else 0
            inet=cmd(['ping','-c','1','-W','2','1.1.1.1'],3)[0]==0; checks.append(('Internet IPv4',inet,'1.1.1.1')); score+=20 if inet else 0
            try: ov=adapter_overview(); radios=sum(1 for v in (ov.get('roles') or {}).values() if v)
            except Exception: radios=0
            radio_ok=radios>=2; checks.append(('WLAN Hardware',radio_ok,f'{radios}/3 Radios erkannt')); score+=20 if radio_ok else 10 if radios else 0
            lines=[f"{'✓' if ok else '✕'} {name}: {detail}" for name,ok,detail in checks]
            grade='SEHR GUT' if score>=90 else 'GUT' if score>=70 else 'PRÜFEN' if score>=50 else 'FEHLER'
            self.root.after(0,lambda:(self.pph32_quick_score.set(f'{score}/100 · {grade}'),self.pph32_quick_result.set('\n'.join(lines))))
        threading.Thread(target=work,daemon=True).start()

    def run_doctor(self):
        self.pph32_doctor_status.set('Diagnose läuft …')
        def work():
            lines=[]
            for title,args in [
                ('ROUTING',['ip','route']),('LINK',['ip','-br','link']),('ADDRESSES',['ip','-br','addr']),('NETWORKMANAGER',['nmcli','-f','DEVICE,TYPE,STATE,CONNECTION','device']),('DNS',['resolvectl','status'])]:
                rc,out,err=cmd(args,6); lines.append(f'[{title}]\n{out or err or "—"}')
            rc,_,_=cmd(['ping','-c','2','-W','2','1.1.1.1'],5); lines.append(f"[INTERNET]\n{'✓ erreichbar' if rc==0 else '✕ nicht erreichbar'}")
            try:
                ov=adapter_overview(); roles=ov.get('roles') or {}; lines.append('[RADIOS]\n'+ '\n'.join(f"{k}: {(v or {}).get('interface','—')} / {(v or {}).get('driver','—')}" for k,v in roles.items()))
            except Exception as exc: lines.append(f'[RADIOS]\n{exc}')
            text='\n\n'.join(lines)
            def done():
                self.pph32_doctor_text.configure(state='normal'); self.pph32_doctor_text.delete('1.0','end'); self.pph32_doctor_text.insert('1.0',text); self.pph32_doctor_text.configure(state='disabled'); self.pph32_doctor_status.set('Diagnose abgeschlossen')
            self.root.after(0,done)
        threading.Thread(target=work,daemon=True).start()

    def toggle_heal(self):
        self.pph32_self_heal=not getattr(self,'pph32_self_heal',False)
        self.pph32_heal_button.configure(text=f"SELF-HEAL: {'AN' if self.pph32_self_heal else 'AUS'}",bg=GREEN if self.pph32_self_heal else SURFACE2)
        if self.pph32_self_heal: self.pph32_self_heal_tick()

    def heal_tick(self):
        if not getattr(self,'pph32_self_heal',False): return
        # Field Mode already owns privileged repair. This trigger only asks the installed helper to reconcile state.
        route=cmd(['ip','route','show','default'])[1]
        if 'eth0' in route:
            rc,out,_=cmd(['nmcli','-t','-f','NAME,DEVICE','connection','show','--active'])
            if 'PPH-AccessPoint:wlan' not in out:
                cmd(['sudo','-n','/usr/local/sbin/pph-fieldctl','start'],12)
        try: self.root.after(10000,self.pph32_self_heal_tick)
        except tk.TclError: pass

    cls._build_pages=build_pages; cls.show_page=show_page
    cls.pph32_refresh_home=refresh_home; cls.pph32_refresh_analyzer=refresh_analyzer; cls.pph32_refresh_wifi=refresh_wifi
    cls.pph32_run_quick=run_quick; cls.pph32_run_doctor=run_doctor; cls.pph32_toggle_heal=toggle_heal; cls.pph32_self_heal_tick=heal_tick
'''
(PAYLOAD/'pph_hub/pph32_ui.py').write_text(ui32,encoding='utf-8')

launcher=PAYLOAD/'pph_hub/pph3_app.py'
t=launcher.read_text(encoding='utf-8')
t=replace_once(t,'from pph3_ui import install\n','from pph3_ui import install\nfrom pph32_ui import install as install32\n','launcher import')
t=replace_once(t,'install(hub.PolishedPPHApp, vars(hub))\n','install(hub.PolishedPPHApp, vars(hub))\ninstall32(hub.PolishedPPHApp, vars(hub))\n','launcher install')
launcher.write_text(t,encoding='utf-8')

(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\n\nVERSION = "3.2.0"\nCHANNEL = "stable"\nBUILD_NAME = "PPH 3.2.0 · Field Analyzer"\nSCHEMA_VERSION = 3\n',encoding='utf-8')

test=PAYLOAD/'test_ui_320.py'
test.write_text('''from pathlib import Path\nR=Path(__file__).resolve().parent\nui=(R/'pph_hub/pph32_ui.py').read_text(encoding='utf-8')\nlaunch=(R/'pph_hub/pph3_app.py').read_text(encoding='utf-8')\nfor x in ('PPH FIELD CENTER','PPH NETWORK ANALYZER','RADIO CENTER','PPH QUICK TEST','NETWORK DOCTOR','SELF-HEAL'):\n    assert x in ui\nassert 'install32(hub.PolishedPPHApp, vars(hub))' in launch\nassert 'mt7921u' in (R/'pph_hub/access_point.py').read_text(encoding='utf-8')\nprint('PPH 3.2.0 tests OK')\n''',encoding='utf-8')
subprocess.run(['python3','-m','py_compile',str(PAYLOAD/'pph_hub/pph32_ui.py'),str(launcher)],check=True)
subprocess.run(['python3',str(test)],cwd=PAYLOAD,check=True)
for c in PAYLOAD.rglob('__pycache__'):
    shutil.rmtree(c)

files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
    rel=p.relative_to(PAYLOAD).as_posix()
    mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','fieldctl.py','install_field_mode.sh'} else '0644'
    files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={
    'format':1,'product':'pph-funktest','version':'3.2.0','min_version':'3.1.7','max_version':'3.1.7','channel':'stable',
    'build_name':'PPH 3.2.0 · Field Analyzer','released':'2026-08-10','tests':['test_ui_320.py'],
    'features':[
        'Neues PPH Field Center Dashboard für 800x480 Touchdisplay',
        'Network Analyzer Redesign mit Download/Upload/Ping/Jitter/Loss Live-Kacheln',
        'Radio Center Redesign für Onboard/BrosTrend/ALFA Rollen',
        'Quick Test mit Score für Uplink/Gateway/DNS/Internet/WLAN Hardware',
        'Network Doctor mit Routing/Link/IP/NetworkManager/DNS Diagnose',
        'Optionales Self-Healing über vorhandenen Field-Mode Root-Helper',
        'Bestehender Funktest, Access Point, Field Mode und Version Control bleiben erhalten'
    ],'files':files}
(WORK/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
OUT_DIR.mkdir(parents=True,exist_ok=True)
with tarfile.open(OUT,'w:gz') as tf:
    tf.add(WORK/'manifest.json',arcname='manifest.json'); tf.add(PAYLOAD,arcname='payload')
package_sha=sha256(OUT)
(OUT_DIR/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT_DIR/'sha256.txt').write_text(f'{package_sha}  {OUT.name}\n',encoding='utf-8')
stable={
    'product':'pph-funktest','channel':'stable','version':'3.2.0','released':'2026-08-10','build_name':'PPH 3.2.0 · Field Analyzer',
    'repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v3.2.0/pph-update-3.2.0-field-analyzer.tar.gz',
    'sha256':package_sha,'min_version':'3.1.7','max_version':'3.1.7',
    'notes':['Field Center Redesign','Network Analyzer Redesign','Radio Center','Quick Test','Network Doctor','Self-Healing']}
(ROOT/'channels/stable.json').write_text(json.dumps(stable,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Built {OUT} sha256={package_sha}')
