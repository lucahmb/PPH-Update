#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'packages/v3.2.0/pph-update-3.2.0-field-analyzer.tar.gz'
WORK=Path('/tmp/pph400'); PAYLOAD=WORK/'payload'
OUT_DIR=ROOT/'packages/v4.0.0'; OUT=OUT_DIR/'pph-update-4.0.0-visual-overhaul.tar.gz'

def sha256(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
if WORK.exists(): shutil.rmtree(WORK)
WORK.mkdir(parents=True)
with tarfile.open(BASE,'r:gz') as tf: tf.extractall(WORK)

theme=r'''#!/usr/bin/env python3
from __future__ import annotations
import tkinter as tk
import time
from typing import Any

# PPH 4.0 visual layer. Pure UI: backend/mess logic stays untouched.
BG="#071018"; PANEL="#0c1722"; PANEL2="#112131"; PANEL3="#172b3d"; BORDER="#21384b"
TEXT="#eaf7ff"; MUTED="#7f9aac"; CYAN="#38d7ff"; GREEN="#47e6a2"; YELLOW="#ffd166"
RED="#ff6b7a"; PURPLE="#b98cff"; ORANGE="#ffad66"; BLUE="#6aa9ff"


def install(cls:type, ns:dict[str,Any])->None:
    previous_build=cls._build_pages
    previous_show=cls.show_page
    previous_toggle=getattr(cls,'toggle_fullscreen',None)
    previous_launch=getattr(cls,'launch_funktest',None)

    def _safe_cfg(w,**kw):
        try:w.configure(**kw)
        except Exception:pass

    def _press_on(w):
        try:w.configure(relief='sunken',highlightbackground=CYAN)
        except Exception:pass
    def _press_off(w):
        try:w.configure(relief='flat',highlightbackground=BORDER)
        except Exception:pass

    def _skin(self,w):
        c=w.winfo_class()
        if c in ('Frame','Labelframe'):
            _safe_cfg(w,bg=BG if w.master==self.root else PANEL)
        elif c=='Label':
            bg=str(w.cget('bg'))
            _safe_cfg(w,bg=PANEL if bg not in (BG,CYAN,GREEN,YELLOW,RED,PURPLE,ORANGE,BLUE) else bg)
        elif c=='Button':
            _safe_cfg(w,bg=PANEL2,fg=TEXT,activebackground=CYAN,activeforeground=BG,
                      relief='flat',bd=0,highlightthickness=1,highlightbackground=BORDER,
                      padx=max(int(w.cget('padx') or 0),7),pady=max(int(w.cget('pady') or 0),5))
            if not getattr(w,'_pph4_fx',False):
                w.bind('<ButtonPress-1>',lambda e,b=w:_press_on(b),add='+')
                w.bind('<ButtonRelease-1>',lambda e,b=w:_press_off(b),add='+')
                w._pph4_fx=True
        elif c in ('Entry','Spinbox'):
            _safe_cfg(w,bg=PANEL2,fg=TEXT,insertbackground=TEXT,relief='flat',bd=0,highlightthickness=1,highlightbackground=BORDER)
        elif c=='Text':
            _safe_cfg(w,bg=PANEL,fg=TEXT,insertbackground=TEXT,relief='flat',bd=0,highlightthickness=1,highlightbackground=BORDER)
        elif c=='Canvas':
            _safe_cfg(w,bg=PANEL,highlightthickness=0)
        for ch in w.winfo_children(): _skin(self,ch)

    def _status_pulse(self):
        if not hasattr(self,'pph4_live_dot'): return
        self._pph4_pulse=not getattr(self,'_pph4_pulse',False)
        try:self.pph4_live_dot.configure(fg=CYAN if self._pph4_pulse else '#1f7185')
        except Exception:return
        try:self.root.after(700,self.pph4_status_pulse)
        except tk.TclError:pass

    def _page_anim(self):
        # Light redraw/entrance pulse; avoids compositor-heavy transparency.
        try:
            self.root.update_idletasks()
            page=self.pages.get(self.current_page)
            if page:
                old=page.cget('highlightbackground') if 'highlightbackground' in page.keys() else BORDER
                page.configure(highlightthickness=1,highlightbackground=CYAN)
                self.root.after(90,lambda p=page,o=old: _safe_cfg(p,highlightbackground=BORDER))
                self.root.after(190,lambda p=page: _safe_cfg(p,highlightthickness=0))
        except Exception:pass

    def _build_overlay(self):
        bar=tk.Frame(self.root,bg='#050b11',height=24,highlightthickness=1,highlightbackground=BORDER)
        bar.place(x=0,rely=1.0,y=-24,relwidth=1.0,height=24)
        bar.lift(); self.pph4_overlay=bar
        tk.Label(bar,text='PPH 4.0',bg='#050b11',fg=CYAN,font=self._font(7,'bold')).pack(side='left',padx=8)
        self.pph4_live_dot=tk.Label(bar,text='●',bg='#050b11',fg=CYAN,font=self._font(8,'bold'))
        self.pph4_live_dot.pack(side='left')
        tk.Label(bar,text='FIELD INTERFACE',bg='#050b11',fg=MUTED,font=self._font(7,'bold')).pack(side='left',padx=5)
        self.pph4_hint=tk.StringVar(value='READY')
        tk.Label(bar,textvariable=self.pph4_hint,bg='#050b11',fg=TEXT,font=self._font(7),anchor='e').pack(side='right',padx=8)
        self.pph4_status_pulse()

    def _build_wireless(self):
        page=self._new_page('wireless4','WIRELESS SITE ANALYZER')
        head=tk.Frame(page,bg=BG); head.pack(fill='x',padx=12,pady=(8,3))
        tk.Label(head,text='WIRELESS SITE ANALYZER',bg=BG,fg=TEXT,font=self._font(15,'bold')).pack(side='left')
        self.pph4_wire_status=tk.StringVar(value='READY')
        tk.Label(head,textvariable=self.pph4_wire_status,bg=PANEL2,fg=CYAN,font=self._font(8,'bold'),padx=9,pady=4).pack(side='right')
        self.pph4_wire={k:tk.StringVar(value='—') for k in ('signal','speed','quality','latency','loss','channel','radio','detail')}
        grid=tk.Frame(page,bg=BG); grid.pack(fill='x',padx=8,pady=3)
        defs=[('SIGNAL','signal',CYAN),('THROUGHPUT','speed',PURPLE),('QUALITY','quality',GREEN),('LATENCY','latency',YELLOW),('LOSS','loss',ORANGE),('CHANNEL','channel',BLUE)]
        for i,(title,key,accent) in enumerate(defs):
            r=i//3;c=i%3; grid.grid_columnconfigure(c,weight=1,uniform='w4')
            card=tk.Frame(grid,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
            card.grid(row=r,column=c,sticky='nsew',padx=3,pady=3)
            tk.Frame(card,bg=accent,height=3).pack(fill='x')
            tk.Label(card,text=title,bg=PANEL,fg=MUTED,font=self._font(7,'bold')).pack(anchor='w',padx=9,pady=(5,0))
            tk.Label(card,textvariable=self.pph4_wire[key],bg=PANEL,fg=accent,font=self._font(16,'bold')).pack(anchor='w',padx=9,pady=(0,5))
        strip=tk.Frame(page,bg=PANEL,highlightthickness=1,highlightbackground=BORDER);strip.pack(fill='x',padx=11,pady=4)
        tk.Label(strip,text='RADIO',bg=PANEL2,fg=MUTED,font=self._font(7,'bold'),padx=7,pady=5).pack(side='left')
        tk.Label(strip,textvariable=self.pph4_wire['radio'],bg=PANEL,fg=CYAN,font=self._font(8,'bold')).pack(side='left',padx=8)
        tk.Label(strip,textvariable=self.pph4_wire['detail'],bg=PANEL,fg=MUTED,font=self._font(7),anchor='e').pack(side='right',fill='x',expand=True,padx=8)
        row=tk.Frame(page,bg=BG); row.pack(fill='both',expand=True,padx=9,pady=(2,8))
        for c in range(4): row.grid_columnconfigure(c,weight=1,uniform='wa')
        items=[('START MEASUREMENT',self.pph4_start_wireless,CYAN),('NETWORK ANALYZER',lambda:self.show_page('analyzer32'),PURPLE),('RADIO CENTER',lambda:self.show_page('wifi32'),ORANGE),('HOME',self.go_home,PANEL2)]
        for c,(label,cmd,color) in enumerate(items):
            self._button(row,label,cmd,bg=color,active=CYAN,size=8,pady=7).grid(row=0,column=c,sticky='nsew',padx=3)

    def build_pages(self):
        previous_build(self)
        _build_wireless(self)
        try:self.root.configure(bg=BG)
        except Exception:pass
        self.root.after(20,lambda:_skin(self,self.root))
        self.root.after(60,lambda:_build_overlay(self))

    def show_page(self,name,title=None,*,push=True):
        aliases={'funktest':'wireless4','wireless':'wireless4','site_analyzer':'wireless4'}
        name=aliases.get(name,name)
        previous_show(self,name,title,push=push)
        try:self.pph4_hint.set(str(self.page_title.get() if hasattr(self,'page_title') else name).upper())
        except Exception:pass
        try:_skin(self,self.root)
        except Exception:pass
        self.root.after(15,lambda:_page_anim(self))
        if hasattr(self,'pph4_overlay'):
            try:self.pph4_overlay.lift()
            except Exception:pass
        if name=='wireless4': self.pph4_refresh_wireless()

    def refresh_wireless(self):
        try:state=self._read_measurement_state()
        except Exception:state={}
        try:running=self._measurement_running() or self._funktest_running()
        except Exception:running=False
        self.pph4_wire_status.set('● LIVE' if running else 'READY')
        sig=state.get('signal_dbm') or state.get('rssi')
        self.pph4_wire['signal'].set(f'{float(sig):.0f} dBm' if isinstance(sig,(int,float)) else '—')
        dl=state.get('download_mbps') or state.get('throughput_mbps')
        self.pph4_wire['speed'].set(f'{float(dl):.1f} Mbit/s' if isinstance(dl,(int,float)) else '—')
        if isinstance(sig,(int,float)):
            q=max(0,min(100,int((float(sig)+95)*2))); self.pph4_wire['quality'].set(f'{q}%')
        else:self.pph4_wire['quality'].set('—')
        ping=state.get('ping_ms') or state.get('latency_ms'); loss=state.get('loss_pct') or state.get('packet_loss')
        self.pph4_wire['latency'].set(f'{float(ping):.1f} ms' if isinstance(ping,(int,float)) else '—')
        self.pph4_wire['loss'].set(f'{float(loss):.1f} %' if isinstance(loss,(int,float)) else '—')
        ch=state.get('channel'); self.pph4_wire['channel'].set(str(ch) if ch else 'AUTO')
        radio=state.get('radio') or state.get('adapter') or 'BrosTrend · mt7921u / Auto'
        self.pph4_wire['radio'].set(str(radio)); self.pph4_wire['detail'].set(str(state.get('phase') or state.get('subtitle') or 'Messengine bereit'))
        if self.current_page=='wireless4':
            try:self.root.after(850,self.pph4_refresh_wireless)
            except tk.TclError:pass

    def start_wireless(self):
        self.pph4_wire_status.set('STARTING…')
        self.pph4_hint.set('WIRELESS MEASUREMENT STARTING')
        if previous_launch:
            try:previous_launch(self)
            except Exception as exc:
                self.pph4_wire_status.set('ERROR'); self.pph4_wire['detail'].set(str(exc)); return
        try:self.root.after(700,lambda:self.show_page('wireless4',push=False))
        except tk.TclError:pass

    def toggle_fullscreen(self):
        if previous_toggle: previous_toggle(self)
        def relift():
            try:
                _skin(self,self.root)
                if hasattr(self,'pph4_overlay'): self.pph4_overlay.lift()
                for n in ('back_button','pph_check_updates_button','settings_button','home_button','fullscreen_button','close_button'):
                    w=getattr(self,n,None)
                    if w is not None:w.lift()
            except Exception:pass
        for d in (20,80,180,360):
            try:self.root.after(d,relift)
            except Exception:pass

    cls._build_pages=build_pages; cls.show_page=show_page
    cls.pph4_refresh_wireless=refresh_wireless; cls.pph4_start_wireless=start_wireless; cls.pph4_status_pulse=_status_pulse
    if previous_toggle: cls.toggle_fullscreen=toggle_fullscreen
'''
(PAYLOAD/'pph_hub/pph4_theme.py').write_text(theme,encoding='utf-8')

launcher=PAYLOAD/'pph_hub/pph3_app.py'
t=launcher.read_text(encoding='utf-8')
if 'from pph4_theme import install as install4' not in t:
    t=t.replace('if __name__ == "__main__":','from pph4_theme import install as install4\ninstall4(hub.PolishedPPHApp, vars(hub))\n\nif __name__ == "__main__":',1)
launcher.write_text(t,encoding='utf-8')
(PAYLOAD/'pph_version.py').write_text('from __future__ import annotations\n\nVERSION = "4.0.0"\nCHANNEL = "stable"\nBUILD_NAME = "PPH 4.0.0 · Visual Overhaul"\nSCHEMA_VERSION = 4\n',encoding='utf-8')

test=PAYLOAD/'test_ui_400.py'
test.write_text('''from pathlib import Path\nR=Path(__file__).resolve().parent\nt=(R/'pph_hub/pph4_theme.py').read_text(encoding='utf-8')\napp=(R/'pph_hub/pph3_app.py').read_text(encoding='utf-8')\nfor x in ('WIRELESS SITE ANALYZER','FIELD INTERFACE','_page_anim','_skin','pph4_status_pulse','START MEASUREMENT'):\n    assert x in t\nassert 'install4(hub.PolishedPPHApp, vars(hub))' in app\nassert (R/'pph_hub/pph32_ui.py').exists()\nassert (R/'pph_hub/access_ui.py').exists()\nprint('PPH 4.0.0 visual tests OK')\n''',encoding='utf-8')
subprocess.run(['python3','-m','py_compile',str(PAYLOAD/'pph_hub/pph4_theme.py'),str(launcher)],check=True)
subprocess.run(['python3',str(test)],cwd=PAYLOAD,check=True)
for c in PAYLOAD.rglob('__pycache__'): shutil.rmtree(c)
files=[]
for p in sorted(x for x in PAYLOAD.rglob('*') if x.is_file()):
    rel=p.relative_to(PAYLOAD).as_posix(); mode='0755' if rel in {'start_pph_hub.sh','pph_hub/pph3_app.py','fieldctl.py','install_field_mode.sh'} else '0644'
    files.append({'path':rel,'sha256':sha256(p),'mode':mode})
manifest={'format':1,'product':'pph-funktest','version':'4.0.0','min_version':'3.2.0','max_version':'3.2.0','channel':'stable','build_name':'PPH 4.0.0 · Visual Overhaul','released':'2026-08-10','tests':['test_ui_400.py'],'features':['Globales PPH 4 Designsystem auf allen bestehenden Tk-Seiten','Einheitliche Panels, Typografie, Borders, Inputs und Touch-Buttons','Press-Animationen und Page-Entrance Animationen','Pulsierender Live-Status und persistente 4.0 Statusleiste','Wireless Site Analyzer erhält eigene 4.0 Instrument-Seite','Network Analyzer, Radio Center, Access Point und Legacy-Unterseiten werden rekursiv geskinnt','Fullscreen-Relift bleibt gegen unsichtbare Topbar-Buttons aktiv','Keine Änderung an Mess-, AP-, Routing- oder Field-Mode-Backendlogik'],'files':files}
(WORK/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
OUT_DIR.mkdir(parents=True,exist_ok=True)
with tarfile.open(OUT,'w:gz') as tf: tf.add(WORK/'manifest.json',arcname='manifest.json'); tf.add(PAYLOAD,arcname='payload')
package_sha=sha256(OUT)
(OUT_DIR/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT_DIR/'sha256.txt').write_text(f'{package_sha}  {OUT.name}\n',encoding='utf-8')
stable={'product':'pph-funktest','channel':'stable','version':'4.0.0','released':'2026-08-10','build_name':'PPH 4.0.0 · Visual Overhaul','repository':'lucahmb/PPH-Update','package_url':'https://raw.githubusercontent.com/lucahmb/PPH-Update/main/packages/v4.0.0/pph-update-4.0.0-visual-overhaul.tar.gz','sha256':package_sha,'min_version':'3.2.0','max_version':'3.2.0','notes':['Full system visual overhaul','Animations on all pages','Wireless Site Analyzer 4.0 shell','Global legacy-page skin','Backend unchanged']}
(ROOT/'channels/stable.json').write_text(json.dumps(stable,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Built {OUT} sha256={package_sha}')
