#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v4.1.1/pph-update-4.1.1-5inch-touch.tar.gz'
WORK=Path('/tmp/pph412'); PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v4.1.2'; OUT=OUT_DIR/'pph-update-4.1.2-paged-touch.tar.gz'
def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if WORK.exists(): shutil.rmtree(WORK)
WORK.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(WORK)
ui=r'''#!/usr/bin/env python3
from __future__ import annotations
import tkinter as tk
from typing import Any
BG='#03070c'; PANEL='#0a111a'; PANEL2='#101b28'; BORDER='#21354a'; TEXT='#f1f7fb'; MUTED='#7690a6'; CYAN='#42dcff'; GREEN='#45e39a'; YELLOW='#ffd166'; ORANGE='#ff9f68'; PURPLE='#bd8cff'

def install(cls:type, ns:dict[str,Any])->None:
    prev_build=cls._build_pages; prev_show=cls.show_page
    def btn(self,p,t,c,a=CYAN):
        return tk.Button(p,text=t,command=c,bg=PANEL2,fg=TEXT,activebackground=a,activeforeground=BG,relief='flat',bd=0,highlightthickness=1,highlightbackground=BORDER,font=self._font(13,'bold'),pady=14,padx=10)
    def head(self,p,title,sub='PPH 4.1.2 · 5-INCH'):
        h=tk.Frame(p,bg=BG,height=56); h.pack(fill='x',padx=12,pady=(8,4)); h.pack_propagate(False)
        tk.Label(h,text=title,bg=BG,fg=TEXT,font=self._font(18,'bold')).pack(side='left')
        tk.Label(h,text=sub,bg=PANEL2,fg=CYAN,font=self._font(7,'bold'),padx=8,pady=5).pack(side='right',pady=8)
    def nav(self,p,active):
        n=tk.Frame(p,bg='#050a10',height=66,highlightthickness=1,highlightbackground=BORDER); n.pack(side='bottom',fill='x'); n.pack_propagate(False)
        items=[('HOME','home412'),('WLAN','wireless412'),('NETZ','network412'),('ACCESS','access412'),('SYSTEM','system412')]
        for i,(lab,target) in enumerate(items):
            n.grid_columnconfigure(i,weight=1,uniform='n412')
            b=btn(self,n,lab,lambda t=target:self.show_page(t),CYAN)
            b.configure(font=self._font(10,'bold'),pady=11,bg=CYAN if target==active else PANEL2,fg=BG if target==active else TEXT)
            b.grid(row=0,column=i,sticky='nsew',padx=2,pady=5)
    def giant(self,p,title,var,accent=CYAN,detail=None):
        f=tk.Frame(p,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
        tk.Frame(f,bg=accent,height=5).pack(fill='x')
        tk.Label(f,text=title,bg=PANEL,fg=MUTED,font=self._font(9,'bold')).pack(anchor='w',padx=16,pady=(12,0))
        tk.Label(f,textvariable=var,bg=PANEL,fg=accent,font=self._font(30,'bold')).pack(anchor='w',padx=16,pady=(2,2))
        if detail is not None: tk.Label(f,textvariable=detail,bg=PANEL,fg=TEXT,font=self._font(10),wraplength=320,justify='left').pack(anchor='w',padx=16,pady=(0,10))
        return f
    def build_home(self):
        p=self._new_page('home412','HOME'); head(self,p,'FIELD CENTER'); nav(self,p,'home412')
        self.p412h={k:tk.StringVar(value='—') for k in ('main','detail')}
        hero=giant(self,p,'FIELD STATUS',self.p412h['main'],GREEN,self.p412h['detail']); hero.pack(fill='both',expand=True,padx=12,pady=6)
        row=tk.Frame(p,bg=BG); row.pack(fill='x',padx=10,pady=(0,8))
        btn(self,row,'QUICK TEST',lambda:self.show_page('quick32'),CYAN).pack(side='left',fill='x',expand=True,padx=4)
        btn(self,row,'WIRELESS',lambda:self.show_page('wireless412'),ORANGE).pack(side='left',fill='x',expand=True,padx=4)
    def build_wireless(self):
        p=self._new_page('wireless412','WIRELESS'); head(self,p,'WIRELESS ANALYZER','RF / WLAN'); nav(self,p,'wireless412')
        self.p412w={k:tk.StringVar(value='—') for k in ('signal','speed','detail')}
        area=tk.Frame(p,bg=BG); area.pack(fill='both',expand=True,padx=10,pady=4)
        area.grid_columnconfigure(0,weight=1); area.grid_columnconfigure(1,weight=1); area.grid_rowconfigure(0,weight=1)
        giant(self,area,'SIGNAL',self.p412w['signal'],CYAN).grid(row=0,column=0,sticky='nsew',padx=4)
        giant(self,area,'THROUGHPUT',self.p412w['speed'],PURPLE).grid(row=0,column=1,sticky='nsew',padx=4)
        row=tk.Frame(p,bg=BG); row.pack(fill='x',padx=10,pady=(0,8))
        btn(self,row,'START',self.p41_start_wireless,CYAN).pack(side='left',fill='x',expand=True,padx=4)
        btn(self,row,'DETAILS',lambda:self.show_page('wireless412b'),ORANGE).pack(side='left',fill='x',expand=True,padx=4)
    def build_wireless_b(self):
        p=self._new_page('wireless412b','WIRELESS DETAILS'); head(self,p,'WIRELESS DETAILS','PAGE 2 / 2'); nav(self,p,'wireless412')
        self.p412wb={k:tk.StringVar(value='—') for k in ('quality','latency','loss','channel')}
        g=tk.Frame(p,bg=BG); g.pack(fill='both',expand=True,padx=10,pady=4)
        for c in range(2): g.grid_columnconfigure(c,weight=1,uniform='wb'); g.grid_rowconfigure(c,weight=1,uniform='wbr')
        defs=[('QUALITY','quality',GREEN),('LATENCY','latency',YELLOW),('LOSS','loss',ORANGE),('CHANNEL','channel',CYAN)]
        for i,(t,k,a) in enumerate(defs): giant(self,g,t,self.p412wb[k],a).grid(row=i//2,column=i%2,sticky='nsew',padx=4,pady=4)
    def build_network(self):
        p=self._new_page('network412','NETWORK'); head(self,p,'NETWORK ANALYZER','PAGE 1 / 2'); nav(self,p,'network412')
        self.p412n={k:tk.StringVar(value='—') for k in ('dl','ul')}
        g=tk.Frame(p,bg=BG); g.pack(fill='both',expand=True,padx=10,pady=4); g.grid_columnconfigure(0,weight=1); g.grid_columnconfigure(1,weight=1); g.grid_rowconfigure(0,weight=1)
        giant(self,g,'DOWNLOAD',self.p412n['dl'],CYAN).grid(row=0,column=0,sticky='nsew',padx=4)
        giant(self,g,'UPLOAD',self.p412n['ul'],PURPLE).grid(row=0,column=1,sticky='nsew',padx=4)
        row=tk.Frame(p,bg=BG); row.pack(fill='x',padx=10,pady=(0,8))
        btn(self,row,'START TEST',self.launch_funktest,CYAN).pack(side='left',fill='x',expand=True,padx=4)
        btn(self,row,'DETAILS',lambda:self.show_page('network412b'),GREEN).pack(side='left',fill='x',expand=True,padx=4)
    def build_network_b(self):
        p=self._new_page('network412b','NETWORK DETAILS'); head(self,p,'NETWORK DETAILS','PAGE 2 / 2'); nav(self,p,'network412')
        self.p412nb={k:tk.StringVar(value='—') for k in ('ping','jitter','loss')}
        g=tk.Frame(p,bg=BG); g.pack(fill='both',expand=True,padx=10,pady=5)
        for c in range(3): g.grid_columnconfigure(c,weight=1,uniform='nb')
        giant(self,g,'PING',self.p412nb['ping'],YELLOW).grid(row=0,column=0,sticky='nsew',padx=4)
        giant(self,g,'JITTER',self.p412nb['jitter'],ORANGE).grid(row=0,column=1,sticky='nsew',padx=4)
        giant(self,g,'LOSS',self.p412nb['loss'],GREEN).grid(row=0,column=2,sticky='nsew',padx=4)
        row=tk.Frame(p,bg=BG); row.pack(fill='x',padx=10,pady=(0,8)); btn(self,row,'NETWORK DOCTOR',lambda:self.show_page('doctor32'),CYAN).pack(fill='x',expand=True,padx=4)
    def build_simple(self,name,title,active,open_cmd,secondary):
        p=self._new_page(name,title); head(self,p,title); nav(self,p,active)
        v=tk.StringVar(value='READY'); d=tk.StringVar(value='Große Touch-Steuerung')
        giant(self,p,title,v,CYAN,d).pack(fill='both',expand=True,padx=12,pady=8)
        row=tk.Frame(p,bg=BG); row.pack(fill='x',padx=10,pady=(0,8))
        btn(self,row,'ÖFFNEN',open_cmd,CYAN).pack(side='left',fill='x',expand=True,padx=4)
        btn(self,row,secondary[0],secondary[1],PURPLE).pack(side='left',fill='x',expand=True,padx=4)
    def build_pages(self):
        prev_build(self); build_home(self); build_wireless(self); build_wireless_b(self); build_network(self); build_network_b(self)
        build_simple(self,'access412','ACCESS POINT','access412',lambda:prev_show(self,'access3'),('DOCTOR',lambda:self.show_page('doctor32')))
        build_simple(self,'system412','SYSTEM','system412',lambda:prev_show(self,'system3'),('SETTINGS',lambda:self.show_page('settings412')))
        build_simple(self,'settings412','SETTINGS','system412',lambda:prev_show(self,'settings3'),('HARDWARE',lambda:prev_show(self,'hardware')))
    def show_page(self,name,title=None,*,push=True):
        aliases={'dashboard':'home412','home411':'home412','home41':'home412','home3':'home412','home32':'home412','wireless411':'wireless412','wireless41':'wireless412','wireless4':'wireless412','funktest':'wireless412','site_analyzer':'wireless412','network411':'network412','analyzer41':'network412','analyzer32':'network412','measure3':'network412','access411':'access412','system411':'system412','settings411':'settings412'}
        name=aliases.get(name,name); prev_show(self,name,title,push=push)
        if name=='home412': self.p412_refresh_home()
        elif name in ('wireless412','wireless412b'): self.p412_refresh_wireless()
        elif name in ('network412','network412b'): self.p412_refresh_network()
    def refresh_home(self):
        try:
            import subprocess; route=subprocess.run(['ip','route','show','default'],capture_output=True,text=True,timeout=2).stdout
            s=self.pph31_ap.status(); ok=bool(route)
            self.p412h['main'].set('READY' if ok else 'OFFLINE'); self.p412h['detail'].set(f"Network {'online' if ok else 'offline'} · AP {'active' if s.get('active') else 'off'} · {s.get('clients',0)} clients")
        except Exception: self.p412h['main'].set('CHECK')
    def refresh_wireless(self):
        try: st=self._read_measurement_state()
        except Exception: st={}
        sig=st.get('signal_dbm') or st.get('rssi'); dl=st.get('download_mbps') or st.get('throughput_mbps'); ping=st.get('ping_ms') or st.get('latency_ms'); loss=st.get('loss_pct') or st.get('packet_loss')
        self.p412w['signal'].set(f'{float(sig):.0f} dBm' if isinstance(sig,(int,float)) else '—'); self.p412w['speed'].set(f'{float(dl):.1f} Mbit/s' if isinstance(dl,(int,float)) else '—')
        self.p412wb['quality'].set(f'{max(0,min(100,int((float(sig)+95)*2)))}%' if isinstance(sig,(int,float)) else '—'); self.p412wb['latency'].set(f'{float(ping):.1f} ms' if isinstance(ping,(int,float)) else '—'); self.p412wb['loss'].set(f'{float(loss):.1f} %' if isinstance(loss,(int,float)) else '—'); self.p412wb['channel'].set(str(st.get('channel') or 'AUTO'))
        if self.current_page in ('wireless412','wireless412b'):
            try:self.root.after(900,self.p412_refresh_wireless)
            except Exception:pass
    def refresh_network(self):
        try: st=self._read_measurement_state()
        except Exception: st={}
        def f(k,s):
            v=st.get(k); return f'{float(v):.1f}{s}' if isinstance(v,(int,float)) else '—'
        self.p412n['dl'].set(f('download_mbps',' Mbit/s')); self.p412n['ul'].set(f('upload_mbps',' Mbit/s')); self.p412nb['ping'].set(f('ping_ms',' ms')); self.p412nb['jitter'].set(f('jitter_ms',' ms')); self.p412nb['loss'].set(f('loss_pct',' %'))
        if self.current_page in ('network412','network412b'):
            try:self.root.after(900,self.p412_refresh_network)
            except Exception:pass
    cls._build_pages=build_pages; cls.show_page=show_page; cls.p412_refresh_home=refresh_home; cls.p412_refresh_wireless=refresh_wireless; cls.p412_refresh_network=refresh_network
'''
(PAYLOAD/'pph_hub/pph412_paged.py').write_text(ui,encoding='utf-8')
launcher=PAYLOAD/'pph_hub/pph3_app.py'; t=launcher.read_text(encoding='utf-8')
if 'from pph412_paged import install as install412' not in t: t=t.replace('if __name__ == "__main__":','from pph412_paged import install as install412\ninstall412(hub.PolishedPPHApp, vars(hub))\n\nif __name__ == "__main__":',1)
launcher.write_text(t,encoding='utf-8')
(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\n\nVERSION = "4.1.2"\nCHANNEL = "stable"\nBUILD_NAME = "PPH 4.1.2 · Paged 5-inch Touch UI"\nSCHEMA_VERSION = 4\n',encoding='utf-8')
test=PAYLOAD/'test_ui_412.py'; test.write_text("from pathlib import Path\nR=Path(__file__).resolve().parent\nt=(R/'pph_hub/pph412_paged.py').read_text()\nfor x in ('PAGE 1 / 2','PAGE 2 / 2','font=self._font(30','pady=14','wireless412b','network412b'): assert x in t\nprint('PPH 4.1.2 tests OK')\n")
subprocess.run(['python3','-m','py_compile',str(PAYLOAD/'pph_hub/pph412_paged.py'),str(launcher)],check=True); subprocess.run(['python3',str(test)],cwd=PAYLOAD,check=True)
for c in PAYLOAD.rglob('__pycache__'): shutil.rmtree(c)
files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
    rel=p.relative_to(PAYLOAD).as_posix(); mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','fieldctl.py','install_field_mode.sh'} else '0644'; files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'4.1.2','min_version':'4.1.1','max_version':'4.1.1','channel':'stable','build_name':'PPH 4.1.2 · Paged 5-inch Touch UI','released':'2026-08-10','tests':['test_ui_412.py'],'features':['Paged Touch UI für 5 Zoll','1–2 Hauptwerte pro Screen','30pt Hauptwerte','große 52–64px Touch-Ziele','Wireless und Network auf zwei Seiten verteilt','keine zusätzliche Overlay-Leiste'],'files':files}
(WORK/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n'); OUT_DIR.mkdir(parents=True,exist_ok=True)
with tarfile.open(OUT,'w:gz') as tf: tf.add(WORK/'manifest.json',arcname='manifest.json'); tf.add(PAYLOAD,arcname='payload')
package_sha=sha256(OUT); (OUT_DIR/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n'); (OUT_DIR/'sha256.txt').write_text(f'{package_sha}  {OUT.name}\n')
stable={'product':'pph-funktest','channel':'stable','version':'4.1.2','released':'2026-08-10','build_name':'PPH 4.1.2 · Paged 5-inch Touch UI','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v4.1.2/pph-update-4.1.2-paged-touch.tar.gz','sha256':package_sha,'min_version':'4.1.1','max_version':'4.1.1','notes':['Paged 5-inch UI','1-2 metrics per page','larger touch targets','wireless/network detail pages','backend unchanged']}
(ROOT/'channels/stable.json').write_text(json.dumps(stable,ensure_ascii=False,indent=2)+'\n')
print('Built',OUT,package_sha)
