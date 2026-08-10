#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v4.1.0/pph-update-4.1.0-visual-relaunch.tar.gz'
WORK=Path('/tmp/pph411'); PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v4.1.1'; OUT=OUT_DIR/'pph-update-4.1.1-5inch-touch.tar.gz'
def sha256(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
if WORK.exists(): shutil.rmtree(WORK)
WORK.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(WORK)

ui=r'''#!/usr/bin/env python3
from __future__ import annotations
import tkinter as tk
from typing import Any

BG='#03070c'; PANEL='#0a111a'; PANEL2='#101b28'; BORDER='#21354a'
TEXT='#f1f7fb'; MUTED='#7690a6'; CYAN='#42dcff'; GREEN='#45e39a'; YELLOW='#ffd166'; ORANGE='#ff9f68'; PURPLE='#bd8cff'; RED='#ff6475'

# 800x480 / 5-inch touch layout: fewer controls per page, larger touch targets.
def install(cls:type, ns:dict[str,Any])->None:
    prev_build=cls._build_pages; prev_show=cls.show_page

    def touch_button(self,parent,text,cmd,accent=CYAN):
        b=tk.Button(parent,text=text,command=cmd,bg=PANEL2,fg=TEXT,activebackground=accent,activeforeground=BG,
                    relief='flat',bd=0,highlightthickness=1,highlightbackground=BORDER,
                    font=self._font(11,'bold'),pady=11,padx=8,cursor='hand2')
        b.bind('<ButtonPress-1>',lambda e,w=b,a=accent:w.configure(bg=a,fg=BG),add='+')
        b.bind('<ButtonRelease-1>',lambda e,w=b:w.configure(bg=PANEL2,fg=TEXT),add='+')
        return b

    def header(self,page,title,kicker='PPH 4.1.1'):
        h=tk.Frame(page,bg=BG,height=52); h.pack(fill='x',padx=12,pady=(7,4)); h.pack_propagate(False)
        left=tk.Frame(h,bg=BG); left.pack(side='left',fill='y')
        tk.Label(left,text=kicker,bg=BG,fg=CYAN,font=self._font(7,'bold')).pack(anchor='w')
        tk.Label(left,text=title,bg=BG,fg=TEXT,font=self._font(15,'bold')).pack(anchor='w')
        tk.Label(h,text='800×480 TOUCH',bg=PANEL2,fg=MUTED,font=self._font(7,'bold'),padx=8,pady=5).pack(side='right',pady=6)

    def metric(self,parent,title,var,accent=CYAN,detail=None):
        f=tk.Frame(parent,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
        tk.Frame(f,bg=accent,height=4).pack(fill='x')
        body=tk.Frame(f,bg=PANEL); body.pack(fill='both',expand=True,padx=11,pady=8)
        tk.Label(body,text=title,bg=PANEL,fg=MUTED,font=self._font(8,'bold')).pack(anchor='w')
        tk.Label(body,textvariable=var,bg=PANEL,fg=accent,font=self._font(21,'bold')).pack(anchor='w',pady=(1,0))
        if detail is not None:
            tk.Label(body,textvariable=detail,bg=PANEL,fg=TEXT,font=self._font(8),wraplength=270,justify='left').pack(anchor='w',pady=(2,0))
        return f

    def bottom_nav(self,page,active):
        nav=tk.Frame(page,bg='#050a10',height=58,highlightthickness=1,highlightbackground=BORDER)
        nav.pack(side='bottom',fill='x'); nav.pack_propagate(False)
        items=[('HOME','home411'),('WLAN','wireless411'),('NETZ','network411'),('ACCESS','access411'),('SYSTEM','system411')]
        for i,(label,target) in enumerate(items):
            nav.grid_columnconfigure(i,weight=1,uniform='nav411')
            b=touch_button(self,nav,label,lambda t=target:self.show_page(t),CYAN if target==active else PURPLE)
            b.configure(font=self._font(9,'bold'),pady=8,bg=CYAN if target==active else PANEL2,fg=BG if target==active else TEXT)
            b.grid(row=0,column=i,sticky='nsew',padx=2,pady=5)

    def build_home(self):
        p=self._new_page('home411','HOME'); header(self,p,'FIELD CENTER'); bottom_nav(self,p,'home411')
        self.p411h={k:tk.StringVar(value='—') for k in ('net','netd','ap','apd','radio','radiod','sys','sysd')}
        grid=tk.Frame(p,bg=BG); grid.pack(fill='both',expand=True,padx=9,pady=(1,5))
        for c in range(2): grid.grid_columnconfigure(c,weight=1,uniform='home411')
        for r in range(2): grid.grid_rowconfigure(r,weight=1,uniform='home411')
        defs=[('NETWORK','net','netd',CYAN),('ACCESS POINT','ap','apd',GREEN),('RADIOS','radio','radiod',ORANGE),('SYSTEM','sys','sysd',PURPLE)]
        for i,(t,v,d,a) in enumerate(defs): metric(self,grid,t,self.p411h[v],a,self.p411h[d]).grid(row=i//2,column=i%2,sticky='nsew',padx=4,pady=4)

    def build_wireless(self):
        p=self._new_page('wireless411','WIRELESS'); header(self,p,'WIRELESS ANALYZER','RF / WLAN'); bottom_nav(self,p,'wireless411')
        self.p411w={k:tk.StringVar(value='—') for k in ('signal','speed','quality','latency','radio','phase')}
        main=tk.Frame(p,bg=BG); main.pack(fill='both',expand=True,padx=9,pady=(0,5))
        top=tk.Frame(main,bg=BG); top.pack(fill='both',expand=True)
        for c in range(2): top.grid_columnconfigure(c,weight=1,uniform='w411'); top.grid_rowconfigure(c,weight=1,uniform='w411r')
        defs=[('SIGNAL','signal',CYAN),('THROUGHPUT','speed',PURPLE),('QUALITY','quality',GREEN),('LATENCY','latency',YELLOW)]
        for i,(t,k,a) in enumerate(defs): metric(self,top,t,self.p411w[k],a).grid(row=i//2,column=i%2,sticky='nsew',padx=4,pady=4)
        foot=tk.Frame(main,bg=BG); foot.pack(fill='x',pady=(2,0))
        touch_button(self,foot,'START',self.p41_start_wireless,CYAN).pack(side='left',fill='x',expand=True,padx=3)
        touch_button(self,foot,'RADIOS',lambda:self.show_page('wifi32'),ORANGE).pack(side='left',fill='x',expand=True,padx=3)
        touch_button(self,foot,'DETAILS',lambda:prev_show(self,'measure3'),PURPLE).pack(side='left',fill='x',expand=True,padx=3)

    def build_network(self):
        p=self._new_page('network411','NETWORK'); header(self,p,'NETWORK ANALYZER','ETHERNET / IP'); bottom_nav(self,p,'network411')
        self.p411n={k:tk.StringVar(value='—') for k in ('dl','ul','ping','loss','phase')}
        main=tk.Frame(p,bg=BG); main.pack(fill='both',expand=True,padx=9,pady=(0,5))
        grid=tk.Frame(main,bg=BG); grid.pack(fill='both',expand=True)
        for c in range(2): grid.grid_columnconfigure(c,weight=1,uniform='n411'); grid.grid_rowconfigure(c,weight=1,uniform='n411r')
        defs=[('DOWNLOAD','dl',CYAN),('UPLOAD','ul',PURPLE),('PING','ping',YELLOW),('LOSS','loss',GREEN)]
        for i,(t,k,a) in enumerate(defs): metric(self,grid,t,self.p411n[k],a).grid(row=i//2,column=i%2,sticky='nsew',padx=4,pady=4)
        row=tk.Frame(main,bg=BG); row.pack(fill='x',pady=(2,0))
        touch_button(self,row,'START TEST',self.launch_funktest,CYAN).pack(side='left',fill='x',expand=True,padx=3)
        touch_button(self,row,'DOCTOR',lambda:self.show_page('doctor32'),GREEN).pack(side='left',fill='x',expand=True,padx=3)
        touch_button(self,row,'REPORTS',lambda:prev_show(self,'reports'),PURPLE).pack(side='left',fill='x',expand=True,padx=3)

    def build_simple(self,name,title,kicker,active,actions):
        p=self._new_page(name,title); header(self,p,title,kicker); bottom_nav(self,p,active)
        area=tk.Frame(p,bg=BG); area.pack(fill='both',expand=True,padx=10,pady=(2,7))
        hero=tk.Frame(area,bg=PANEL,highlightthickness=1,highlightbackground=BORDER); hero.pack(fill='both',expand=True)
        tk.Label(hero,text=title,bg=PANEL,fg=TEXT,font=self._font(22,'bold')).pack(anchor='w',padx=16,pady=(18,4))
        tk.Label(hero,text='Touch-optimierte Steuerung für das 5-Zoll-Display',bg=PANEL,fg=MUTED,font=self._font(9)).pack(anchor='w',padx=16)
        buttons=tk.Frame(hero,bg=PANEL); buttons.pack(fill='x',padx=12,pady=18)
        for i,(lab,cmd,a) in enumerate(actions):
            buttons.grid_columnconfigure(i,weight=1,uniform='simple411')
            touch_button(self,buttons,lab,cmd,a).grid(row=0,column=i,sticky='ew',padx=4)

    def build_pages(self):
        prev_build(self)
        build_home(self); build_wireless(self); build_network(self)
        build_simple(self,'access411','ACCESS POINT','FIELD ROUTER','access411',[
            ('CONTROL',lambda:prev_show(self,'access3'),GREEN),('TOKEN',lambda:prev_show(self,'access3'),CYAN),('DOCTOR',lambda:self.show_page('doctor32'),PURPLE)])
        build_simple(self,'system411','SYSTEM','DEVICE HEALTH','system411',[
            ('STATUS',lambda:prev_show(self,'system3'),CYAN),('EVENTS',lambda:prev_show(self,'events3'),ORANGE),('SETTINGS',lambda:self.show_page('settings411'),PURPLE)])
        build_simple(self,'settings411','SETTINGS','CONFIGURATION','system411',[
            ('SETTINGS',lambda:prev_show(self,'settings3'),CYAN),('HARDWARE',lambda:prev_show(self,'hardware'),ORANGE),('STORAGE',lambda:prev_show(self,'storage'),PURPLE)])

    def show_page(self,name,title=None,*,push=True):
        aliases={'dashboard':'home411','home41':'home411','home3':'home411','home32':'home411','wireless41':'wireless411','wireless4':'wireless411','funktest':'wireless411','site_analyzer':'wireless411','analyzer41':'network411','analyzer32':'network411','measure3':'network411','access41':'access411','system41':'system411','settings41':'settings411'}
        name=aliases.get(name,name); prev_show(self,name,title,push=push)
        if name=='home411': self.p411_refresh_home()
        elif name=='wireless411': self.p411_refresh_wireless()
        elif name=='network411': self.p411_refresh_network()

    def refresh_home(self):
        try:
            route=__import__('subprocess').run(['ip','route','show','default'],capture_output=True,text=True,timeout=2).stdout
            self.p411h['net'].set('ONLINE' if route else 'OFFLINE'); self.p411h['netd'].set('LAN aktiv' if 'eth0' in route else 'Route aktiv' if route else 'Kein Uplink')
        except Exception: pass
        try:
            s=self.pph31_ap.status(); self.p411h['ap'].set('ACTIVE' if s.get('active') else 'OFF'); self.p411h['apd'].set(f"{s.get('clients',0)} Geräte · {float(s.get('total_mbps') or 0):.1f} Mbit/s")
        except Exception: pass
        self.p411h['radio'].set('3/3'); self.p411h['radiod'].set('Onboard · BrosTrend · ALFA'); self.p411h['sys'].set('READY'); self.p411h['sysd'].set('Field Mode bereit')

    def refresh_wireless(self):
        try: st=self._read_measurement_state()
        except Exception: st={}
        sig=st.get('signal_dbm') or st.get('rssi'); dl=st.get('download_mbps') or st.get('throughput_mbps'); ping=st.get('ping_ms') or st.get('latency_ms')
        self.p411w['signal'].set(f'{float(sig):.0f} dBm' if isinstance(sig,(int,float)) else '—')
        self.p411w['speed'].set(f'{float(dl):.1f} Mbit/s' if isinstance(dl,(int,float)) else '—')
        self.p411w['quality'].set(f'{max(0,min(100,int((float(sig)+95)*2)))}%' if isinstance(sig,(int,float)) else '—')
        self.p411w['latency'].set(f'{float(ping):.1f} ms' if isinstance(ping,(int,float)) else '—')
        self.p411w['radio'].set(str(st.get('radio') or st.get('adapter') or 'BrosTrend · mt7921u'))
        self.p411w['phase'].set(str(st.get('phase') or 'READY'))
        if self.current_page=='wireless411':
            try:self.root.after(900,self.p411_refresh_wireless)
            except Exception:pass

    def refresh_network(self):
        try: st=self._read_measurement_state()
        except Exception: st={}
        def f(k,s):
            v=st.get(k); return f'{float(v):.1f}{s}' if isinstance(v,(int,float)) else '—'
        self.p411n['dl'].set(f('download_mbps',' Mbit/s')); self.p411n['ul'].set(f('upload_mbps',' Mbit/s')); self.p411n['ping'].set(f('ping_ms',' ms')); self.p411n['loss'].set(f('loss_pct',' %')); self.p411n['phase'].set(str(st.get('phase') or 'READY'))
        if self.current_page=='network411':
            try:self.root.after(900,self.p411_refresh_network)
            except Exception:pass

    cls._build_pages=build_pages; cls.show_page=show_page
    cls.p411_refresh_home=refresh_home; cls.p411_refresh_wireless=refresh_wireless; cls.p411_refresh_network=refresh_network
'''
(PAYLOAD/'pph_hub/pph411_touch.py').write_text(ui,encoding='utf-8')
launcher=PAYLOAD/'pph_hub/pph3_app.py'
t=launcher.read_text(encoding='utf-8')
if 'from pph411_touch import install as install411' not in t:
    t=t.replace('if __name__ == "__main__":','from pph411_touch import install as install411\ninstall411(hub.PolishedPPHApp, vars(hub))\n\nif __name__ == "__main__":',1)
launcher.write_text(t,encoding='utf-8')
(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\n\nVERSION = "4.1.1"\nCHANNEL = "stable"\nBUILD_NAME = "PPH 4.1.1 · 5-inch Touch Layout"\nSCHEMA_VERSION = 4\n',encoding='utf-8')

test=PAYLOAD/'test_ui_411.py'
test.write_text('''from pathlib import Path\nR=Path(__file__).resolve().parent\nt=(R/'pph_hub/pph411_touch.py').read_text(encoding='utf-8')\na=(R/'pph_hub/pph3_app.py').read_text(encoding='utf-8')\nfor x in ('800×480 TOUCH','WIRELESS ANALYZER','NETWORK ANALYZER','Touch-optimierte Steuerung','pady=11'):\n    assert x in t\nassert 'install411(hub.PolishedPPHApp, vars(hub))' in a\nprint('PPH 4.1.1 5-inch tests OK')\n''',encoding='utf-8')
subprocess.run(['python3','-m','py_compile',str(PAYLOAD/'pph_hub/pph411_touch.py'),str(launcher)],check=True)
subprocess.run(['python3',str(test)],cwd=PAYLOAD,check=True)
for c in PAYLOAD.rglob('__pycache__'): shutil.rmtree(c)
files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
    rel=p.relative_to(PAYLOAD).as_posix(); mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','fieldctl.py','install_field_mode.sh'} else '0644'
    files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'4.1.1','min_version':'4.1.0','max_version':'4.1.0','channel':'stable','build_name':'PPH 4.1.1 · 5-inch Touch Layout','released':'2026-08-10','tests':['test_ui_411.py'],'features':['800x480/5-Zoll Layout','größere Touch-Ziele','maximal vier Hauptmetriken pro Seite','Bottom-Navigation statt enger Sidebar','größere Typografie und Abstände','Backend unverändert'],'files':files}
(WORK/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
OUT_DIR.mkdir(parents=True,exist_ok=True)
with tarfile.open(OUT,'w:gz') as tf: tf.add(WORK/'manifest.json',arcname='manifest.json'); tf.add(PAYLOAD,arcname='payload')
package_sha=sha256(OUT)
(OUT_DIR/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT_DIR/'sha256.txt').write_text(f'{package_sha}  {OUT.name}\n',encoding='utf-8')
stable={'product':'pph-funktest','channel':'stable','version':'4.1.1','released':'2026-08-10','build_name':'PPH 4.1.1 · 5-inch Touch Layout','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v4.1.1/pph-update-4.1.1-5inch-touch.tar.gz','sha256':package_sha,'min_version':'4.1.0','max_version':'4.1.0','notes':['5-inch/800x480 touch layout','larger controls','bottom navigation','less dense pages','backend unchanged']}
(ROOT/'channels/stable.json').write_text(json.dumps(stable,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Built {OUT} sha256={package_sha}')
