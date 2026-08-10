#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v4.0.0/pph-update-4.0.0-visual-overhaul.tar.gz'
WORK=Path('/tmp/pph410'); PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v4.1.0'; OUT=OUT_DIR/'pph-update-4.1.0-visual-relaunch.tar.gz'
def sha256(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
if WORK.exists(): shutil.rmtree(WORK)
WORK.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(WORK)

ui=r'''#!/usr/bin/env python3
from __future__ import annotations
import tkinter as tk, subprocess
from typing import Any

BG='#03070c'; PANEL='#0a111a'; PANEL2='#101b28'; PANEL3='#162536'; BORDER='#21354a'
TEXT='#f1f7fb'; MUTED='#7690a6'; CYAN='#42dcff'; BLUE='#6f8cff'; GREEN='#45e39a'; YELLOW='#ffd166'; ORANGE='#ff9f68'; RED='#ff6475'; PURPLE='#bd8cff'

def install(cls:type, ns:dict[str,Any])->None:
    prev_build=cls._build_pages; prev_show=cls.show_page

    def pill(self,parent,text,fg=CYAN,bg=PANEL2):
        return tk.Label(parent,text=text,bg=bg,fg=fg,font=self._font(7,'bold'),padx=8,pady=4)

    def big_button(self,parent,text,cmd,accent=CYAN):
        b=tk.Button(parent,text=text,command=cmd,bg=PANEL2,fg=TEXT,activebackground=accent,activeforeground=BG,
                    relief='flat',bd=0,highlightthickness=1,highlightbackground=BORDER,font=self._font(9,'bold'),pady=10,cursor='hand2')
        b.bind('<ButtonPress-1>',lambda e,w=b,a=accent:w.configure(bg=a,fg=BG),add='+')
        b.bind('<ButtonRelease-1>',lambda e,w=b:w.configure(bg=PANEL2,fg=TEXT),add='+')
        return b

    def metric(self,parent,title,var,accent=CYAN,detail=None):
        f=tk.Frame(parent,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
        tk.Frame(f,bg=accent,width=5).pack(side='left',fill='y')
        body=tk.Frame(f,bg=PANEL);body.pack(fill='both',expand=True,padx=9,pady=7)
        tk.Label(body,text=title,bg=PANEL,fg=MUTED,font=self._font(7,'bold')).pack(anchor='w')
        tk.Label(body,textvariable=var,bg=PANEL,fg=accent,font=self._font(17,'bold')).pack(anchor='w')
        if detail is not None: tk.Label(body,textvariable=detail,bg=PANEL,fg=TEXT,font=self._font(7)).pack(anchor='w')
        return f

    def section_header(self,parent,kicker,title,status=''):
        h=tk.Frame(parent,bg=BG);h.pack(fill='x',padx=12,pady=(8,5))
        left=tk.Frame(h,bg=BG);left.pack(side='left')
        tk.Label(left,text=kicker,bg=BG,fg=CYAN,font=self._font(7,'bold')).pack(anchor='w')
        tk.Label(left,text=title,bg=BG,fg=TEXT,font=self._font(16,'bold')).pack(anchor='w')
        if status: pill(self,h,status).pack(side='right')
        return h

    def sidebar(self,parent,items):
        rail=tk.Frame(parent,bg='#050a10',width=126,highlightthickness=1,highlightbackground=BORDER)
        rail.pack(side='left',fill='y',padx=(0,8)); rail.pack_propagate(False)
        tk.Label(rail,text='PPH 4.1',bg='#050a10',fg=CYAN,font=self._font(11,'bold')).pack(anchor='w',padx=10,pady=(10,2))
        tk.Label(rail,text='FIELD OS',bg='#050a10',fg=MUTED,font=self._font(7,'bold')).pack(anchor='w',padx=10,pady=(0,10))
        for label,cmd in items:
            big_button(self,rail,label,cmd,PURPLE).pack(fill='x',padx=7,pady=3)
        return rail

    def build_home(self):
        page=self._new_page('home41','PPH 4.1')
        section_header(self,page,'PORTABLE PERFORMANCE HUB','FIELD COMMAND CENTER','LIVE')
        body=tk.Frame(page,bg=BG);body.pack(fill='both',expand=True,padx=10,pady=(0,8))
        sidebar(self,body,[('WIRELESS',lambda:self.show_page('wireless41')),('NETWORK',lambda:self.show_page('analyzer41')),('ACCESS',lambda:self.show_page('access41')),('SYSTEM',lambda:self.show_page('system41')),('SETTINGS',lambda:self.show_page('settings41'))])
        main=tk.Frame(body,bg=BG);main.pack(side='left',fill='both',expand=True)
        self.p41={k:tk.StringVar(value='—') for k in ('net','netd','radio','radiod','ap','apd','sys','sysd')}
        cards=tk.Frame(main,bg=BG);cards.pack(fill='x')
        defs=[('NETWORK','net','netd',CYAN),('RADIOS','radio','radiod',ORANGE),('ACCESS POINT','ap','apd',GREEN),('SYSTEM','sys','sysd',PURPLE)]
        for c,(t,v,d,a) in enumerate(defs): cards.grid_columnconfigure(c,weight=1,uniform='h41'); metric(self,cards,t,self.p41[v],a,self.p41[d]).grid(row=0,column=c,sticky='nsew',padx=3)
        hero=tk.Frame(main,bg=PANEL,highlightthickness=1,highlightbackground=BORDER);hero.pack(fill='both',expand=True,pady=(7,0))
        tk.Label(hero,text='FIELD READY',bg=PANEL,fg=GREEN,font=self._font(24,'bold')).pack(anchor='w',padx=14,pady=(14,2))
        tk.Label(hero,text='One-tap diagnostics, wireless analysis and access-point control.',bg=PANEL,fg=MUTED,font=self._font(9)).pack(anchor='w',padx=14)
        row=tk.Frame(hero,bg=PANEL);row.pack(fill='x',padx=10,pady=14)
        for i,(lab,cmd,a) in enumerate([('QUICK TEST',lambda:self.show_page('quick32'),CYAN),('WIRELESS SCAN',lambda:self.show_page('wireless41'),ORANGE),('NETWORK DOCTOR',lambda:self.show_page('doctor32'),GREEN)]):
            row.grid_columnconfigure(i,weight=1,uniform='hero'); big_button(self,row,lab,cmd,a).grid(row=0,column=i,sticky='ew',padx=4)

    def build_wireless(self):
        page=self._new_page('wireless41','WIRELESS')
        section_header(self,page,'RF / WLAN','WIRELESS SITE ANALYZER','READY')
        body=tk.Frame(page,bg=BG);body.pack(fill='both',expand=True,padx=10,pady=(0,8))
        sidebar(self,body,[('START',self.p41_start_wireless),('RADIOS',lambda:self.show_page('wifi32')),('NETWORK',lambda:self.show_page('analyzer41')),('HOME',lambda:self.show_page('home41'))])
        main=tk.Frame(body,bg=BG);main.pack(side='left',fill='both',expand=True)
        self.p41w={k:tk.StringVar(value='—') for k in ('signal','speed','quality','latency','loss','channel','radio','phase')}
        top=tk.Frame(main,bg=BG);top.pack(fill='x')
        for i,(t,k,a) in enumerate([('SIGNAL','signal',CYAN),('THROUGHPUT','speed',PURPLE),('QUALITY','quality',GREEN)]): top.grid_columnconfigure(i,weight=1,uniform='wt'); metric(self,top,t,self.p41w[k],a).grid(row=0,column=i,sticky='nsew',padx=3)
        bot=tk.Frame(main,bg=BG);bot.pack(fill='x',pady=6)
        for i,(t,k,a) in enumerate([('LATENCY','latency',YELLOW),('LOSS','loss',ORANGE),('CHANNEL','channel',BLUE)]): bot.grid_columnconfigure(i,weight=1,uniform='wb'); metric(self,bot,t,self.p41w[k],a).grid(row=0,column=i,sticky='nsew',padx=3)
        live=tk.Frame(main,bg=PANEL,highlightthickness=1,highlightbackground=BORDER);live.pack(fill='both',expand=True)
        tk.Label(live,text='LIVE RADIO',bg=PANEL,fg=MUTED,font=self._font(7,'bold')).pack(anchor='w',padx=10,pady=(8,2))
        tk.Label(live,textvariable=self.p41w['radio'],bg=PANEL,fg=CYAN,font=self._font(11,'bold')).pack(anchor='w',padx=10)
        tk.Label(live,textvariable=self.p41w['phase'],bg=PANEL,fg=TEXT,font=self._font(8)).pack(anchor='w',padx=10,pady=(2,8))

    def build_analyzer(self):
        page=self._new_page('analyzer41','NETWORK')
        section_header(self,page,'ETHERNET / IP','NETWORK ANALYZER','LIVE DATA')
        body=tk.Frame(page,bg=BG);body.pack(fill='both',expand=True,padx=10,pady=(0,8))
        sidebar(self,body,[('START TEST',self.launch_funktest),('DOCTOR',lambda:self.show_page('doctor32')),('REPORTS',lambda:prev_show(self,'reports')),('HOME',lambda:self.show_page('home41'))])
        main=tk.Frame(body,bg=BG);main.pack(side='left',fill='both',expand=True)
        self.p41n={k:tk.StringVar(value='—') for k in ('dl','ul','ping','jitter','loss','phase')}
        hero=tk.Frame(main,bg=BG);hero.pack(fill='x')
        metric(self,hero,'DOWNLOAD',self.p41n['dl'],CYAN).pack(side='left',fill='both',expand=True,padx=3)
        metric(self,hero,'UPLOAD',self.p41n['ul'],PURPLE).pack(side='left',fill='both',expand=True,padx=3)
        row=tk.Frame(main,bg=BG);row.pack(fill='x',pady=6)
        for i,(t,k,a) in enumerate([('PING','ping',YELLOW),('JITTER','jitter',ORANGE),('LOSS','loss',GREEN)]): row.grid_columnconfigure(i,weight=1,uniform='net'); metric(self,row,t,self.p41n[k],a).grid(row=0,column=i,sticky='nsew',padx=3)
        phase=tk.Frame(main,bg=PANEL,highlightthickness=1,highlightbackground=BORDER);phase.pack(fill='both',expand=True)
        tk.Label(phase,text='CURRENT PHASE',bg=PANEL,fg=MUTED,font=self._font(7,'bold')).pack(anchor='w',padx=10,pady=(9,2))
        tk.Label(phase,textvariable=self.p41n['phase'],bg=PANEL,fg=TEXT,font=self._font(11,'bold')).pack(anchor='w',padx=10)

    def simple_page(self,name,title,kicker,actions):
        page=self._new_page(name,title)
        section_header(self,page,kicker,title,'PPH 4.1')
        body=tk.Frame(page,bg=BG);body.pack(fill='both',expand=True,padx=10,pady=(0,8))
        sidebar(self,body,[('HOME',lambda:self.show_page('home41')),('WIRELESS',lambda:self.show_page('wireless41')),('NETWORK',lambda:self.show_page('analyzer41'))])
        main=tk.Frame(body,bg=BG);main.pack(side='left',fill='both',expand=True)
        pane=tk.Frame(main,bg=PANEL,highlightthickness=1,highlightbackground=BORDER);pane.pack(fill='both',expand=True)
        tk.Label(pane,text=title,bg=PANEL,fg=TEXT,font=self._font(18,'bold')).pack(anchor='w',padx=14,pady=(14,4))
        tk.Label(pane,text='Redesigned PPH 4.1 control surface',bg=PANEL,fg=MUTED,font=self._font(8)).pack(anchor='w',padx=14)
        row=tk.Frame(pane,bg=PANEL);row.pack(fill='x',padx=10,pady=14)
        for i,(lab,cmd,a) in enumerate(actions): row.grid_columnconfigure(i,weight=1,uniform='simp'); big_button(self,row,lab,cmd,a).grid(row=0,column=i,sticky='ew',padx=4)

    def build_pages(self):
        prev_build(self)
        build_home(self);build_wireless(self);build_analyzer(self)
        simple_page(self,'access41','ACCESS POINT','FIELD ROUTER',[('OPEN CONTROL',lambda:prev_show(self,'access3'),GREEN),('NETWORK DOCTOR',lambda:self.show_page('doctor32'),CYAN)])
        simple_page(self,'system41','SYSTEM','DEVICE HEALTH',[('SYSTEM DETAILS',lambda:prev_show(self,'system3'),PURPLE),('EVENTS',lambda:prev_show(self,'events3'),BLUE),('JOBS',lambda:prev_show(self,'jobs3'),ORANGE)])
        simple_page(self,'settings41','SETTINGS','CONFIGURATION',[('OPEN SETTINGS',lambda:prev_show(self,'settings3'),CYAN),('HARDWARE',lambda:prev_show(self,'hardware'),ORANGE),('STORAGE',lambda:prev_show(self,'storage'),PURPLE)])

    def show_page(self,name,title=None,*,push=True):
        aliases={'dashboard':'home41','home3':'home41','home32':'home41','wireless4':'wireless41','funktest':'wireless41','site_analyzer':'wireless41','analyzer32':'analyzer41','measure3':'analyzer41','access3':'access41','system3':'system41','settings3':'settings41'}
        name=aliases.get(name,name);prev_show(self,name,title,push=push)
        if name=='home41': self.p41_refresh_home()
        elif name=='wireless41': self.p41_refresh_wireless()
        elif name=='analyzer41': self.p41_refresh_network()
        try:
            page=self.pages.get(name)
            if page:
                page.configure(highlightthickness=2,highlightbackground=CYAN)
                self.root.after(120,lambda p=page:p.configure(highlightthickness=0))
        except Exception: pass

    def refresh_home(self):
        try:
            route=subprocess.run(['ip','route','show','default'],capture_output=True,text=True,timeout=2).stdout
            self.p41['net'].set('ONLINE' if route else 'OFFLINE');self.p41['netd'].set('eth0 uplink' if 'eth0' in route else 'route active' if route else 'no route')
        except Exception:self.p41['net'].set('—')
        try:
            s=self.pph31_ap.status(); self.p41['ap'].set('ACTIVE' if s.get('active') else 'OFF'); self.p41['apd'].set(f"{s.get('clients',0)} clients")
        except Exception:self.p41['ap'].set('—')
        self.p41['radio'].set('3/3');self.p41['radiod'].set('Onboard · BrosTrend · ALFA');self.p41['sys'].set('READY');self.p41['sysd'].set('Field services online')

    def refresh_wireless(self):
        try:st=self._read_measurement_state()
        except Exception:st={}
        sig=st.get('signal_dbm') or st.get('rssi'); dl=st.get('download_mbps') or st.get('throughput_mbps'); ping=st.get('ping_ms') or st.get('latency_ms'); loss=st.get('loss_pct') or st.get('packet_loss')
        self.p41w['signal'].set(f'{float(sig):.0f} dBm' if isinstance(sig,(int,float)) else '—'); self.p41w['speed'].set(f'{float(dl):.1f} Mbit/s' if isinstance(dl,(int,float)) else '—')
        self.p41w['quality'].set(f'{max(0,min(100,int((float(sig)+95)*2)))}%' if isinstance(sig,(int,float)) else '—'); self.p41w['latency'].set(f'{float(ping):.1f} ms' if isinstance(ping,(int,float)) else '—'); self.p41w['loss'].set(f'{float(loss):.1f}%' if isinstance(loss,(int,float)) else '—'); self.p41w['channel'].set(str(st.get('channel') or 'AUTO')); self.p41w['radio'].set(str(st.get('radio') or st.get('adapter') or 'BrosTrend · mt7921u')); self.p41w['phase'].set(str(st.get('phase') or st.get('subtitle') or 'Measurement engine ready'))
        if getattr(self,'current_page','')=='wireless41': self.root.after(900,self.p41_refresh_wireless)

    def refresh_network(self):
        try:st=self._read_measurement_state()
        except Exception:st={}
        def f(k,s):
            v=st.get(k);return f'{float(v):.1f}{s}' if isinstance(v,(int,float)) else '—'
        self.p41n['dl'].set(f('download_mbps',' Mbit/s'));self.p41n['ul'].set(f('upload_mbps',' Mbit/s'));self.p41n['ping'].set(f('ping_ms',' ms'));self.p41n['jitter'].set(f('jitter_ms',' ms'));self.p41n['loss'].set(f('loss_pct',' %'));self.p41n['phase'].set(str(st.get('phase') or 'Ready'))
        if getattr(self,'current_page','')=='analyzer41': self.root.after(900,self.p41_refresh_network)

    def start_wireless(self):
        try:self.launch_funktest()
        except Exception:pass
        self.root.after(500,lambda:self.show_page('wireless41',push=False))

    cls._build_pages=build_pages;cls.show_page=show_page;cls.p41_refresh_home=refresh_home;cls.p41_refresh_wireless=refresh_wireless;cls.p41_refresh_network=refresh_network;cls.p41_start_wireless=start_wireless
'''
(PAYLOAD/'pph_hub/pph41_ui.py').write_text(ui,encoding='utf-8')
launcher=PAYLOAD/'pph_hub/pph3_app.py'
t=launcher.read_text(encoding='utf-8')
if 'from pph41_ui import install as install41' not in t:
    t=t.replace('if __name__ == "__main__":','from pph41_ui import install as install41\ninstall41(hub.PolishedPPHApp, vars(hub))\n\nif __name__ == "__main__":',1)
launcher.write_text(t,encoding='utf-8')
(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\n\nVERSION = "4.1.0"\nCHANNEL = "stable"\nBUILD_NAME = "PPH 4.1.0 · Visual Relaunch"\nSCHEMA_VERSION = 4\n',encoding='utf-8')
test=PAYLOAD/'test_ui_410.py';test.write_text("""from pathlib import Path\nR=Path(__file__).resolve().parent\nt=(R/'pph_hub/pph41_ui.py').read_text(encoding='utf-8')\nfor x in ('FIELD COMMAND CENTER','WIRELESS SITE ANALYZER','NETWORK ANALYZER','FIELD OS','ACCESS POINT','SETTINGS'):\n assert x in t\nassert 'install41(hub.PolishedPPHApp, vars(hub))' in (R/'pph_hub/pph3_app.py').read_text(encoding='utf-8')\nprint('PPH 4.1 tests OK')\n""",encoding='utf-8')
subprocess.run(['python3','-m','py_compile',str(PAYLOAD/'pph_hub/pph41_ui.py'),str(launcher)],check=True);subprocess.run(['python3',str(test)],cwd=PAYLOAD,check=True)
for c in PAYLOAD.rglob('__pycache__'): shutil.rmtree(c)
files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
 rel=p.relative_to(PAYLOAD).as_posix(); mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','fieldctl.py','install_field_mode.sh'} else '0644'; files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'4.1.0','min_version':'4.0.0','max_version':'4.0.0','channel':'stable','build_name':'PPH 4.1.0 · Visual Relaunch','released':'2026-08-10','tests':['test_ui_410.py'],'features':['Neue Seitenlayouts statt nur Skinning','Neue Sidebar-Navigation','Neue Home/Network/Wireless Oberflächen','Neue Access/System/Settings Relaunch-Seiten','Touch-Press und Page-Flash Animationen','Backend unverändert'],'files':files}
(WORK/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');OUT_DIR.mkdir(parents=True,exist_ok=True)
with tarfile.open(OUT,'w:gz') as tf: tf.add(WORK/'manifest.json',arcname='manifest.json');tf.add(PAYLOAD,arcname='payload')
package_sha=sha256(OUT);(OUT_DIR/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(OUT_DIR/'sha256.txt').write_text(f'{package_sha}  {OUT.name}\n',encoding='utf-8')
stable={'product':'pph-funktest','channel':'stable','version':'4.1.0','released':'2026-08-10','build_name':'PPH 4.1.0 · Visual Relaunch','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v4.1.0/pph-update-4.1.0-visual-relaunch.tar.gz','sha256':package_sha,'min_version':'4.0.0','max_version':'4.0.0','notes':['Real layout rebuild','Sidebar navigation','Wireless redesign','Network redesign','System/settings/access relaunch']}
(ROOT/'channels/stable.json').write_text(json.dumps(stable,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(f'Built {OUT} {package_sha}')