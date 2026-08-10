#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v4.1.2/pph-update-4.1.2-paged-touch.tar.gz'
WORK=Path('/tmp/pph420'); PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v4.2.0'; OUT=OUT_DIR/'pph-update-4.2.0-full-ui-rewrite.tar.gz'
def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if WORK.exists(): shutil.rmtree(WORK)
WORK.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(WORK)

ui=r'''#!/usr/bin/env python3
from __future__ import annotations
import os,subprocess,tkinter as tk
from typing import Any
BG='#03070c'; PANEL='#0a111a'; PANEL2='#101b28'; BORDER='#21354a'; TEXT='#f4f8fb'; MUTED='#7891a6'; CYAN='#42dcff'; GREEN='#45e39a'; YELLOW='#ffd166'; ORANGE='#ff9f68'; PURPLE='#bd8cff'; RED='#ff6475'; BLUE='#6f8cff'

PAGES=('home3','measure3','wifi3','system3','jobs3','events3','settings3','services','storage','hardware','reports','network','tools','network_doctor','lan_mapper','access3')

def install(cls:type,ns:dict[str,Any])->None:
    prev_build=cls._build_pages; prev_show=cls.show_page

    def run(args,timeout=3):
        try:
            p=subprocess.run(args,text=True,capture_output=True,timeout=timeout,check=False)
            return (p.stdout or p.stderr or '').strip()
        except Exception as e:return str(e)
    def replace(self,name,title):
        old=getattr(self,'frames',{}).get(name)
        if old is not None:
            try: old.destroy()
            except Exception: pass
            self.frames.pop(name,None)
        return self._new_page(name,title)
    def btn(self,p,text,cmd,accent=CYAN):
        b=tk.Button(p,text=text,command=cmd,bg=PANEL2,fg=TEXT,activebackground=accent,activeforeground=BG,relief='flat',bd=0,highlightthickness=1,highlightbackground=BORDER,font=self._font(12,'bold'),pady=12,padx=8,cursor='hand2')
        b.bind('<ButtonPress-1>',lambda e,w=b,a=accent:w.configure(bg=a,fg=BG),add='+')
        b.bind('<ButtonRelease-1>',lambda e,w=b:w.configure(bg=PANEL2,fg=TEXT),add='+')
        return b
    def head(self,p,title,kicker='PPH 4.2 · FULL UI'):
        h=tk.Frame(p,bg=BG,height=54);h.pack(fill='x',padx=12,pady=(7,3));h.pack_propagate(False)
        left=tk.Frame(h,bg=BG);left.pack(side='left')
        tk.Label(left,text=kicker,bg=BG,fg=CYAN,font=self._font(7,'bold')).pack(anchor='w')
        tk.Label(left,text=title,bg=BG,fg=TEXT,font=self._font(18,'bold')).pack(anchor='w')
        tk.Label(h,text='800×480',bg=PANEL2,fg=MUTED,font=self._font(7,'bold'),padx=8,pady=5).pack(side='right',pady=8)
    def nav(self,p,active):
        n=tk.Frame(p,bg='#050a10',height=64,highlightthickness=1,highlightbackground=BORDER);n.pack(side='bottom',fill='x');n.pack_propagate(False)
        items=[('HOME','home3'),('WLAN','measure3'),('NETZ','network'),('ACCESS','access3'),('SYSTEM','system3')]
        for i,(lab,target) in enumerate(items):
            n.grid_columnconfigure(i,weight=1,uniform='n42')
            b=btn(self,n,lab,lambda t=target:self.show_page(t),CYAN)
            b.configure(font=self._font(9,'bold'),pady=10,bg=CYAN if target==active else PANEL2,fg=BG if target==active else TEXT)
            b.grid(row=0,column=i,sticky='nsew',padx=2,pady=5)
    def giant(self,p,title,var,accent=CYAN,detail=None):
        f=tk.Frame(p,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
        tk.Frame(f,bg=accent,height=5).pack(fill='x')
        tk.Label(f,text=title,bg=PANEL,fg=MUTED,font=self._font(8,'bold')).pack(anchor='w',padx=14,pady=(10,0))
        tk.Label(f,textvariable=var,bg=PANEL,fg=accent,font=self._font(27,'bold')).pack(anchor='w',padx=14,pady=(1,1))
        if detail is not None:tk.Label(f,textvariable=detail,bg=PANEL,fg=TEXT,font=self._font(9),wraplength=700,justify='left').pack(anchor='w',padx=14,pady=(0,9))
        return f
    def textpanel(self,p):
        t=tk.Text(p,bg=PANEL,fg=TEXT,insertbackground=TEXT,relief='flat',bd=0,highlightthickness=1,highlightbackground=BORDER,font=self._font(9),wrap='word',padx=10,pady=8)
        return t
    def settext(w,s):
        try:w.configure(state='normal');w.delete('1.0','end');w.insert('end',s);w.configure(state='disabled')
        except Exception:pass

    def build_home(self):
        p=replace(self,'home3','HOME');head(self,p,'FIELD CENTER');nav(self,p,'home3')
        self.v42_home=tk.StringVar(value='READY');self.d42_home=tk.StringVar(value='PPH vollständig einsatzbereit')
        giant(self,p,'FIELD STATUS',self.v42_home,GREEN,self.d42_home).pack(fill='both',expand=True,padx=12,pady=7)
        r=tk.Frame(p,bg=BG);r.pack(fill='x',padx=9,pady=(0,7))
        for lab,cmd,a in [('QUICK TEST',lambda:self.show_page('network_doctor'),CYAN),('WIRELESS',lambda:self.show_page('measure3'),ORANGE),('EVENTS',lambda:self.show_page('events3'),PURPLE)]:btn(self,r,lab,cmd,a).pack(side='left',fill='x',expand=True,padx=3)
    def build_measure(self):
        p=replace(self,'measure3','WIRELESS');head(self,p,'WIRELESS SITE ANALYZER','RF / WLAN');nav(self,p,'measure3')
        self.v42_sig=tk.StringVar(value='—');self.v42_thr=tk.StringVar(value='—')
        g=tk.Frame(p,bg=BG);g.pack(fill='both',expand=True,padx=9,pady=5);g.grid_columnconfigure(0,weight=1);g.grid_columnconfigure(1,weight=1);g.grid_rowconfigure(0,weight=1)
        giant(self,g,'SIGNAL',self.v42_sig,CYAN).grid(row=0,column=0,sticky='nsew',padx=4);giant(self,g,'THROUGHPUT',self.v42_thr,PURPLE).grid(row=0,column=1,sticky='nsew',padx=4)
        r=tk.Frame(p,bg=BG);r.pack(fill='x',padx=9,pady=(0,7));btn(self,r,'START',self.launch_funktest,CYAN).pack(side='left',fill='x',expand=True,padx=3);btn(self,r,'RADIOS',lambda:self.show_page('wifi3'),ORANGE).pack(side='left',fill='x',expand=True,padx=3);btn(self,r,'REPORTS',lambda:self.show_page('reports'),PURPLE).pack(side='left',fill='x',expand=True,padx=3)
    def build_wifi(self):
        p=replace(self,'wifi3','RADIOS');head(self,p,'RADIO CENTER');nav(self,p,'measure3');self.t42_wifi=textpanel(self,p);self.t42_wifi.pack(fill='both',expand=True,padx=12,pady=7)
        r=tk.Frame(p,bg=BG);r.pack(fill='x',padx=9,pady=(0,7));btn(self,r,'REFRESH',lambda:self.r42('wifi3'),CYAN).pack(side='left',fill='x',expand=True,padx=3);btn(self,r,'DFS / CHANNELS',self._pph28_show_dfs,ORANGE).pack(side='left',fill='x',expand=True,padx=3);btn(self,r,'DOCTOR',lambda:self.show_page('network_doctor'),GREEN).pack(side='left',fill='x',expand=True,padx=3)
    def build_system(self):
        p=replace(self,'system3','SYSTEM');head(self,p,'SYSTEM');nav(self,p,'system3');self.v42_sys=tk.StringVar(value='READY');self.d42_sys=tk.StringVar(value='');giant(self,p,'DEVICE HEALTH',self.v42_sys,GREEN,self.d42_sys).pack(fill='both',expand=True,padx=12,pady=7)
        r=tk.Frame(p,bg=BG);r.pack(fill='x',padx=9,pady=(0,7));
        for lab,t,a in [('HARDWARE','hardware',ORANGE),('STORAGE','storage',PURPLE),('SERVICES','services',CYAN),('SETTINGS','settings3',BLUE)]:btn(self,r,lab,lambda x=t:self.show_page(x),a).pack(side='left',fill='x',expand=True,padx=3)
    def build_list(self,name,title,active='system3'):
        p=replace(self,name,title);head(self,p,title);nav(self,p,active);t=textpanel(self,p);t.pack(fill='both',expand=True,padx=12,pady=7);setattr(self,'t42_'+name.replace('-','_'),t);r=tk.Frame(p,bg=BG);r.pack(fill='x',padx=9,pady=(0,7));btn(self,r,'REFRESH',lambda n=name:self.r42(n),CYAN).pack(fill='x',expand=True,padx=3)
    def build_settings(self):
        p=replace(self,'settings3','SETTINGS');head(self,p,'SETTINGS');nav(self,p,'system3')
        box=tk.Frame(p,bg=PANEL,highlightthickness=1,highlightbackground=BORDER);box.pack(fill='both',expand=True,padx=12,pady=7)
        tk.Label(box,text='DISPLAY TIMEOUT',bg=PANEL,fg=MUTED,font=self._font(9,'bold')).pack(anchor='w',padx=12,pady=(12,4));r=tk.Frame(box,bg=PANEL);r.pack(fill='x',padx=8)
        for sec,lab in [(30,'30 S'),(60,'1 MIN'),(120,'2 MIN'),(300,'5 MIN'),(0,'NIE')]:btn(self,r,lab,lambda v=sec:self.set_timeout(v),CYAN).pack(side='left',fill='x',expand=True,padx=2)
        tk.Label(box,text='HELLIGKEIT',bg=PANEL,fg=MUTED,font=self._font(9,'bold')).pack(anchor='w',padx=12,pady=(14,4));r2=tk.Frame(box,bg=PANEL);r2.pack(fill='x',padx=8)
        for pct in (25,50,75,100):btn(self,r2,f'{pct}%',lambda v=pct:self.set_brightness(v),YELLOW).pack(side='left',fill='x',expand=True,padx=2)
        r3=tk.Frame(box,bg=PANEL);r3.pack(fill='x',padx=8,pady=14);btn(self,r3,'CHECK UPDATES',self._pph28_open_update,PURPLE).pack(side='left',fill='x',expand=True,padx=3);btn(self,r3,'DISPLAY OFF',self.sleep_display,BLUE).pack(side='left',fill='x',expand=True,padx=3)
    def build_access(self):
        p=replace(self,'access3','ACCESS POINT');head(self,p,'ACCESS POINT');nav(self,p,'access3');self.v42_ap=tk.StringVar(value='—');self.d42_ap=tk.StringVar(value='');giant(self,p,'PPH-WIFI',self.v42_ap,GREEN,self.d42_ap).pack(fill='both',expand=True,padx=12,pady=7)
        r=tk.Frame(p,bg=BG);r.pack(fill='x',padx=9,pady=(0,7));btn(self,r,'START',lambda:self.ap42('start'),GREEN).pack(side='left',fill='x',expand=True,padx=3);btn(self,r,'STOP',lambda:self.ap42('stop'),RED).pack(side='left',fill='x',expand=True,padx=3);btn(self,r,'DOCTOR',lambda:self.show_page('network_doctor'),CYAN).pack(side='left',fill='x',expand=True,padx=3)
    def build_doctor(self):
        p=replace(self,'network_doctor','NETWORK DOCTOR');head(self,p,'NETWORK DOCTOR');nav(self,p,'network');self.t42_doctor=textpanel(self,p);self.t42_doctor.pack(fill='both',expand=True,padx=12,pady=7);r=tk.Frame(p,bg=BG);r.pack(fill='x',padx=9,pady=(0,7));btn(self,r,'DIAGNOSE',self.doctor42,CYAN).pack(fill='x',expand=True,padx=3)
    def build_network(self):
        p=replace(self,'network','NETWORK');head(self,p,'NETWORK ANALYZER');nav(self,p,'network');self.v42_net=tk.StringVar(value='—');self.d42_net=tk.StringVar(value='');giant(self,p,'UPLINK',self.v42_net,CYAN,self.d42_net).pack(fill='both',expand=True,padx=12,pady=7);r=tk.Frame(p,bg=BG);r.pack(fill='x',padx=9,pady=(0,7));btn(self,r,'DOCTOR',lambda:self.show_page('network_doctor'),GREEN).pack(side='left',fill='x',expand=True,padx=3);btn(self,r,'LAN MAP',lambda:self.show_page('lan_mapper'),ORANGE).pack(side='left',fill='x',expand=True,padx=3);btn(self,r,'TOOLS',lambda:self.show_page('tools'),PURPLE).pack(side='left',fill='x',expand=True,padx=3)
    def build_pages(self):
        prev_build(self)
        build_home(self);build_measure(self);build_wifi(self);build_system(self);build_settings(self);build_access(self);build_doctor(self);build_network(self)
        for n,t,a in [('jobs3','JOBS','system3'),('events3','EVENTS','system3'),('services','SERVICES','system3'),('storage','STORAGE','system3'),('hardware','HARDWARE','system3'),('reports','REPORTS','measure3'),('tools','TOOLS','network'),('lan_mapper','LAN MAPPER','network')]:build_list(self,n,t,a)
    def show_page(self,name,title=None,*,push=True):
        aliases={'dashboard':'home3','home412':'home3','home411':'home3','home41':'home3','home32':'home3','wireless412':'measure3','wireless412b':'measure3','wireless411':'measure3','wireless41':'measure3','wireless4':'measure3','site_analyzer':'measure3','analyzer32':'network','analyzer41':'network','network412':'network','network412b':'network','doctor32':'network_doctor','quick32':'network_doctor','wifi32':'wifi3','access412':'access3','access411':'access3','system412':'system3','system411':'system3','settings412':'settings3','settings411':'settings3'}
        name=aliases.get(name,name);prev_show(self,name,title,push=push)
        if name in PAGES:self.r42(name)
    def r42(self,name):
        if name=='home3':
            route=run(['ip','route','show','default']);self.v42_home.set('READY' if route else 'OFFLINE');self.d42_home.set('Uplink aktiv · Field Mode bereit' if route else 'Kein Default-Uplink erkannt')
        elif name=='measure3':
            try:st=self._read_measurement_state()
            except Exception:st={}
            s=st.get('signal_dbm') or st.get('rssi');d=st.get('download_mbps') or st.get('throughput_mbps');self.v42_sig.set(f'{float(s):.0f} dBm' if isinstance(s,(int,float)) else '—');self.v42_thr.set(f'{float(d):.1f} Mbit/s' if isinstance(d,(int,float)) else '—')
        elif name=='wifi3':
            out=run(['bash','-lc',"for i in /sys/class/net/wlan*; do [ -e \"$i\" ] || continue; n=$(basename \"$i\"); d=$(basename \"$(readlink -f \"$i/device/driver\" 2>/dev/null)\"); echo \"$n   $d\"; done"]);settext(self.t42_wifi,out or 'Keine WLAN-Adapter erkannt')
        elif name=='system3':
            temp=run(['bash','-lc','cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || echo 0']);mem=run(['bash','-lc',"free -m | awk '/Mem:/{print $3\"/\"$2\" MB\"}'"]);self.v42_sys.set(f'{float(temp)/1000:.0f}°C' if temp.isdigit() else 'READY');self.d42_sys.set('RAM '+mem)
        elif name=='access3':
            try:s=self.pph31_ap.status();self.v42_ap.set('ACTIVE' if s.get('active') else 'OFF');self.d42_ap.set(f"{s.get('clients',0)} Geräte · {float(s.get('total_mbps') or 0):.1f} Mbit/s · 10.42.0.1")
            except Exception as e:self.v42_ap.set('CHECK');self.d42_ap.set(str(e))
        elif name=='network':
            route=run(['ip','route','show','default']);self.v42_net.set('ONLINE' if route else 'OFFLINE');self.d42_net.set(route[:180] or 'Keine Route')
        elif name=='storage':settext(self.t42_storage,run(['df','-h','/','/mnt/storage']))
        elif name=='hardware':settext(self.t42_hardware,run(['bash','-lc','uname -a; echo; lscpu | head -12; echo; lsusb']))
        elif name=='services':settext(self.t42_services,run(['bash','-lc',"systemctl --no-pager --type=service --state=running | head -18"]))
        elif name=='events3':settext(self.t42_events3,run(['bash','-lc','journalctl -n 16 --no-pager 2>/dev/null']))
        elif name=='jobs3':settext(self.t42_jobs3,run(['bash','-lc',"ps -eo pid,comm,%cpu,%mem --sort=-%cpu | head -16"]))
        elif name=='reports':
            try:st=self._read_measurement_state();settext(self.t42_reports,'LETZTER MESSSTATUS\n\n'+json.dumps(st,ensure_ascii=False,indent=2))
            except Exception as e:settext(self.t42_reports,str(e))
        elif name=='lan_mapper':settext(self.t42_lan_mapper,run(['ip','neigh']))
        elif name=='tools':settext(self.t42_tools,'NETWORK DOCTOR\nLAN MAPPER\nDFS / CHANNELS\nDIAGNOSTIC SNAPSHOT\n\nAlle Tools nutzen weiterhin die bestehende Backend-Logik.')
    def doctor42(self):
        rows=[]
        rows.append('DEFAULT ROUTE\n'+run(['ip','route','show','default']))
        rows.append('\nETH0\n'+run(['ip','-br','addr','show','eth0']))
        rows.append('\nFORWARDING\n'+run(['sysctl','net.ipv4.ip_forward']))
        rows.append('\nDNS\n'+run(['getent','hosts','github.com']))
        rows.append('\nINTERNET\n'+run(['ping','-c','2','1.1.1.1'],4))
        settext(self.t42_doctor,'\n'.join(rows))
    def ap42(self,action):
        run(['sudo','-n','/usr/local/sbin/pph-fieldctl',action],12);self.root.after(700,lambda:self.r42('access3'))
    cls._build_pages=build_pages;cls.show_page=show_page;cls.r42=r42;cls.doctor42=doctor42;cls.ap42=ap42
'''
(PAYLOAD/'pph_hub/pph42_full_ui.py').write_text(ui,encoding='utf-8')
launcher=PAYLOAD/'pph_hub/pph3_app.py';t=launcher.read_text(encoding='utf-8')
if 'from pph42_full_ui import install as install42' not in t:t=t.replace('if __name__ == "__main__":','from pph42_full_ui import install as install42\ninstall42(hub.PolishedPPHApp, vars(hub))\n\nif __name__ == "__main__":',1)
launcher.write_text(t,encoding='utf-8')
(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\n\nVERSION = "4.2.0"\nCHANNEL = "stable"\nBUILD_NAME = "PPH 4.2.0 · Full UI Rewrite"\nSCHEMA_VERSION = 4\n',encoding='utf-8')
test=PAYLOAD/'test_ui_420.py';test.write_text("from pathlib import Path\nR=Path(__file__).resolve().parent\nt=(R/'pph_hub/pph42_full_ui.py').read_text()\na=(R/'pph_hub/pph3_app.py').read_text()\nfor x in ('home3','measure3','wifi3','system3','jobs3','events3','settings3','services','storage','hardware','reports','network','tools','network_doctor','lan_mapper','access3'): assert x in t\nassert 'old.destroy()' in t\nassert 'install42(hub.PolishedPPHApp, vars(hub))' in a\nprint('PPH 4.2.0 full UI tests OK')\n")
subprocess.run(['python3','-m','py_compile',str(PAYLOAD/'pph_hub/pph42_full_ui.py'),str(launcher)],check=True);subprocess.run(['python3',str(test)],cwd=PAYLOAD,check=True)
for c in PAYLOAD.rglob('__pycache__'):shutil.rmtree(c)
files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
    rel=p.relative_to(PAYLOAD).as_posix();mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','fieldctl.py','install_field_mode.sh'} else '0644';files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'4.2.0','min_version':'4.1.2','max_version':'4.1.2','channel':'stable','build_name':'PPH 4.2.0 · Full UI Rewrite','released':'2026-08-10','tests':['test_ui_420.py'],'features':['Jede bestehende Haupt- und Unterseite wird ersetzt','Keine Wrapper vor Legacy-Seiten','800x480 5-inch Touch Design systemweit','Home, Wireless, Radio, Network, Access, System, Jobs, Events, Settings, Services, Storage, Hardware, Reports, Tools, Doctor und LAN Mapper neu','Backend bleibt erhalten'],'files':files}
(WORK/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');OUT_DIR.mkdir(parents=True,exist_ok=True)
with tarfile.open(OUT,'w:gz') as tf:tf.add(WORK/'manifest.json',arcname='manifest.json');tf.add(PAYLOAD,arcname='payload')
sh=sha256(OUT);(OUT_DIR/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');(OUT_DIR/'sha256.txt').write_text(f'{sh}  {OUT.name}\n')
stable={'product':'pph-funktest','channel':'stable','version':'4.2.0','released':'2026-08-10','build_name':'PPH 4.2.0 · Full UI Rewrite','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v4.2.0/pph-update-4.2.0-full-ui-rewrite.tar.gz','sha256':sh,'min_version':'4.1.2','max_version':'4.1.2','notes':['Every page replaced','No legacy wrapper pages','5-inch touch layouts systemwide','Backend unchanged']}
(ROOT/'channels/stable.json').write_text(json.dumps(stable,ensure_ascii=False,indent=2)+'\n');print(OUT,sh)
