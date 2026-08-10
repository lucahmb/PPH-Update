#!/usr/bin/env python3
from __future__ import annotations
import subprocess, tkinter as tk
from typing import Any

BG='#05080b'; PANEL='#101820'; PANEL2='#172330'; PANEL3='#0c1319'; BORDER='#2b3f51'; TEXT='#f7fbfd'; MUTED='#8da2b3'
CYAN='#4bd7e8'; GREEN='#74d680'; ORANGE='#f4a259'; PURPLE='#b58cff'; RED='#f26d6d'; BLUE='#7da2ff'; YELLOW='#f3cf65'

CORE=('home3','measure3','wifi3','network','access3','system3','settings3','hardware','storage','services','events3','jobs3','reports','tools','network_doctor','lan_mapper','field50','flow50','compare50','session50','notify50','more52')

def install(cls:type, ns:dict[str,Any])->None:
    prev_build=cls._build_pages
    prev_show=cls.show_page

    def run(args, timeout=3):
        try:
            p=subprocess.run(args,text=True,capture_output=True,timeout=timeout,check=False)
            return (p.stdout or p.stderr or '').strip()
        except Exception:
            return ''

    def replace(self,name,title):
        old=getattr(self,'frames',{}).get(name)
        if old is not None:
            try: old.destroy()
            except Exception: pass
            self.frames.pop(name,None)
        return self._new_page(name,title)

    def button(self,p,text,cmd,accent=CYAN):
        b=tk.Button(p,text=text,command=cmd,bg=PANEL2,fg=TEXT,activebackground=accent,activeforeground=BG,
                    relief='flat',bd=0,highlightthickness=1,highlightbackground=BORDER,
                    font=self._font(12,'bold'),pady=13,padx=8,cursor='hand2')
        b.bind('<ButtonPress-1>',lambda e,w=b,a=accent:w.configure(bg=a,fg=BG,highlightbackground=a),add='+')
        b.bind('<ButtonRelease-1>',lambda e,w=b:w.after(90,lambda:w.configure(bg=PANEL2,fg=TEXT,highlightbackground=BORDER)),add='+')
        return b

    def header(self,p,kicker,title,status='READY'):
        h=tk.Frame(p,bg=BG,height=58); h.pack(fill='x',padx=12,pady=(7,2)); h.pack_propagate(False)
        l=tk.Frame(h,bg=BG); l.pack(side='left',fill='y')
        tk.Label(l,text=kicker,bg=BG,fg=CYAN,font=self._font(8,'bold')).pack(anchor='w')
        tk.Label(l,text=title,bg=BG,fg=TEXT,font=self._font(18,'bold')).pack(anchor='w')
        badge=tk.Label(h,text=status,bg=PANEL2,fg=GREEN,font=self._font(9,'bold'),padx=10,pady=7)
        badge.pack(side='right',pady=9)
        def pulse(on=False):
            try:
                badge.configure(fg=GREEN if on else CYAN)
                badge.after(850,lambda:pulse(not on))
            except Exception:
                pass
        pulse()

    def nav(self,p,active):
        n=tk.Frame(p,bg=PANEL3,height=74,highlightthickness=1,highlightbackground=BORDER)
        n.pack(side='bottom',fill='x'); n.pack_propagate(False); n._pph51_nav=True
        items=[('HOME','home3'),('FUNK','measure3'),('NETZ','network'),('AP','access3'),('GERAET','system3'),('MEHR','more52')]
        for i,(lab,target) in enumerate(items):
            n.grid_columnconfigure(i,weight=1,uniform='n51')
            active_state = target==active or (target=='more52' and active not in {'home3','measure3','network','access3','system3'})
            b=button(self,n,lab,lambda t=target:self.show_page(t),CYAN if target!='access3' else GREEN)
            b.configure(font=self._font(9,'bold'),pady=12,bg=CYAN if active_state else PANEL2,fg=BG if active_state else TEXT)
            b.grid(row=0,column=i,sticky='nsew',padx=3,pady=7)
        try:n.lift()
        except Exception:pass

    def card(self,p,title,var,accent=CYAN,detail=None):
        f=tk.Frame(p,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
        tk.Frame(f,bg=accent,height=5).pack(fill='x')
        tk.Label(f,text=title,bg=PANEL,fg=MUTED,font=self._font(8,'bold')).pack(anchor='w',padx=14,pady=(10,0))
        tk.Label(f,textvariable=var,bg=PANEL,fg=accent,font=self._font(24,'bold')).pack(anchor='w',padx=14,pady=(2,0))
        if detail is not None:
            tk.Label(f,textvariable=detail,bg=PANEL,fg=TEXT,font=self._font(9),wraplength=330,justify='left').pack(anchor='w',padx=14,pady=(2,10))
        f.bind('<Enter>',lambda e,w=f,a=accent:w.configure(highlightbackground=a),add='+')
        f.bind('<Leave>',lambda e,w=f:w.configure(highlightbackground=BORDER),add='+')
        return f

    def two_cards(self,p,left,right):
        g=tk.Frame(p,bg=BG); g.pack(fill='both',expand=True,padx=10,pady=6)
        g.grid_columnconfigure(0,weight=1,uniform='c51'); g.grid_columnconfigure(1,weight=1,uniform='c51'); g.grid_rowconfigure(0,weight=1)
        left.grid(row=0,column=0,sticky='nsew',padx=4); right.grid(row=0,column=1,sticky='nsew',padx=4)

    def actions(self,p,items):
        r=tk.Frame(p,bg=BG); r.pack(fill='x',padx=9,pady=(0,7))
        for lab,cmd,a in items:
            button(self,r,lab,cmd,a).pack(side='left',fill='x',expand=True,padx=3)

    def menu_tile(self,p,title,detail,target,accent=CYAN):
        f=tk.Frame(p,bg=PANEL,highlightthickness=1,highlightbackground=BORDER,cursor='hand2')
        tk.Frame(f,bg=accent,height=4).pack(fill='x')
        tk.Label(f,text=title,bg=PANEL,fg=TEXT,font=self._font(12,'bold')).pack(anchor='w',padx=12,pady=(8,0))
        tk.Label(f,text=detail,bg=PANEL,fg=MUTED,font=self._font(8),wraplength=220,justify='left').pack(anchor='w',padx=12,pady=(2,8))
        def go(_=None,t=target):
            try:f.configure(bg=accent)
            except Exception:pass
            self.root.after(80,lambda:self.show_page(t))
        for w in (f,)+tuple(f.winfo_children()):
            w.bind('<Button-1>',go,add='+')
        f.bind('<Enter>',lambda e,w=f,a=accent:w.configure(highlightbackground=a),add='+')
        f.bind('<Leave>',lambda e,w=f:w.configure(highlightbackground=BORDER),add='+')
        return f

    def text_page(self,name,title,kicker,active,refresh=None):
        p=replace(self,name,title); header(self,p,kicker,title); nav(self,p,active)
        t=tk.Text(p,bg=PANEL,fg=TEXT,insertbackground=TEXT,relief='flat',bd=0,highlightthickness=1,highlightbackground=BORDER,font=self._font(11),wrap='word',padx=12,pady=10)
        t.pack(fill='both',expand=True,padx=12,pady=7); setattr(self,'p51_'+name.replace('-','_'),t)
        if refresh: actions(self,p,[('REFRESH',refresh,CYAN)])
        return p

    def settext(w,s):
        try:
            w.configure(state='normal'); w.delete('1.0','end'); w.insert('end',s); w.configure(state='disabled')
        except Exception: pass

    def build_home(self):
        p=replace(self,'home3','HOME'); header(self,p,'PPH 5.2 · TOUCH HUB','FIELD CENTER'); nav(self,p,'home3')
        self.p51_home_net=tk.StringVar(value='—'); self.p51_home_field=tk.StringVar(value='READY')
        self.p51_home_net_d=tk.StringVar(value='Uplink wird geprüft'); self.p51_home_field_d=tk.StringVar(value='Field Platform bereit')
        two_cards(self,p,card(self,p,'NETWORK',self.p51_home_net,CYAN,self.p51_home_net_d),card(self,p,'FIELD',self.p51_home_field,GREEN,self.p51_home_field_d))
        actions(self,p,[('MESSUNG STARTEN',lambda:self.show_page('measure3'),ORANGE),('QUICK DIAG',lambda:self.show_page('network_doctor'),CYAN),('ALLE KATEGORIEN',lambda:self.show_page('more52'),PURPLE)])

    def build_wireless(self):
        p=replace(self,'measure3','WIRELESS'); header(self,p,'RF / WLAN','WIRELESS SITE ANALYZER','LIVE'); nav(self,p,'measure3')
        self.p51_sig=tk.StringVar(value='—'); self.p51_thr=tk.StringVar(value='—'); self.p51_sig_d=tk.StringVar(value='RSSI'); self.p51_thr_d=tk.StringVar(value='Live throughput')
        two_cards(self,p,card(self,p,'SIGNAL',self.p51_sig,CYAN,self.p51_sig_d),card(self,p,'THROUGHPUT',self.p51_thr,PURPLE,self.p51_thr_d))
        actions(self,p,[('START',self.launch_funktest,CYAN),('RADIOS',lambda:self.show_page('wifi3'),ORANGE),('REPORTS',lambda:self.show_page('reports'),PURPLE)])

    def build_network(self):
        p=replace(self,'network','NETWORK'); header(self,p,'LAN / WAN','NETWORK ANALYZER'); nav(self,p,'network')
        self.p51_net=tk.StringVar(value='—'); self.p51_ping=tk.StringVar(value='—'); self.p51_net_d=tk.StringVar(value='Uplink'); self.p51_ping_d=tk.StringVar(value='Gateway')
        two_cards(self,p,card(self,p,'UPLINK',self.p51_net,CYAN,self.p51_net_d),card(self,p,'LATENCY',self.p51_ping,GREEN,self.p51_ping_d))
        actions(self,p,[('NETWORK DOCTOR',lambda:self.show_page('network_doctor'),GREEN),('LAN MAP',lambda:self.show_page('lan_mapper'),ORANGE),('TOOLS',lambda:self.show_page('tools'),PURPLE)])

    def build_access(self):
        p=replace(self,'access3','ACCESS POINT'); header(self,p,'FIELD ROUTER','ACCESS POINT'); nav(self,p,'access3')
        self.p51_ap=tk.StringVar(value='—'); self.p51_token=tk.StringVar(value='—'); self.p51_ap_d=tk.StringVar(value='PPH-WIFI'); self.p51_token_d=tk.StringVar(value='AP-IP 10.42.0.1')
        two_cards(self,p,card(self,p,'ACCESS POINT',self.p51_ap,GREEN,self.p51_ap_d),card(self,p,'PAIRING CODE',self.p51_token,PURPLE,self.p51_token_d))
        actions(self,p,[('START',lambda:self.ap42('start'),GREEN),('STOP',lambda:self.ap42('stop'),RED),('REFRESH',lambda:self.refresh51('access3'),CYAN)])

    def build_system(self):
        p=replace(self,'system3','SYSTEM'); header(self,p,'DEVICE','GERAET STATUS'); nav(self,p,'system3')
        self.p51_cpu=tk.StringVar(value='—'); self.p51_mem=tk.StringVar(value='—'); self.p51_cpu_d=tk.StringVar(value='Temperature'); self.p51_mem_d=tk.StringVar(value='Memory')
        two_cards(self,p,card(self,p,'CPU',self.p51_cpu,ORANGE,self.p51_cpu_d),card(self,p,'RAM',self.p51_mem,BLUE,self.p51_mem_d))
        actions(self,p,[('HARDWARE',lambda:self.show_page('hardware'),ORANGE),('STORAGE',lambda:self.show_page('storage'),PURPLE),('SETTINGS',lambda:self.show_page('settings3'),CYAN)])

    def build_settings(self):
        p=replace(self,'settings3','SETTINGS'); header(self,p,'DEVICE','SETTINGS'); nav(self,p,'system3')
        box=tk.Frame(p,bg=PANEL,highlightthickness=1,highlightbackground=BORDER); box.pack(fill='both',expand=True,padx=12,pady=7)
        tk.Label(box,text='DISPLAY BRIGHTNESS',bg=PANEL,fg=MUTED,font=self._font(9,'bold')).pack(anchor='w',padx=12,pady=(12,5))
        r=tk.Frame(box,bg=PANEL); r.pack(fill='x',padx=9)
        for pct in (25,50,75,100): button(self,r,f'{pct}%',lambda v=pct:self.set_brightness(v),YELLOW).pack(side='left',fill='x',expand=True,padx=3)
        tk.Label(box,text='DISPLAY TIMEOUT',bg=PANEL,fg=MUTED,font=self._font(9,'bold')).pack(anchor='w',padx=12,pady=(14,5))
        r2=tk.Frame(box,bg=PANEL); r2.pack(fill='x',padx=9)
        for sec,lab in ((30,'30 S'),(60,'1 MIN'),(120,'2 MIN'),(0,'NIE')): button(self,r2,lab,lambda v=sec:self.set_timeout(v),CYAN).pack(side='left',fill='x',expand=True,padx=3)
        actions(self,p,[('CHECK UPDATES',self._pph28_open_update,PURPLE),('DISPLAY OFF',self.sleep_display,BLUE)])

    def build_more(self):
        p=replace(self,'more52','KATEGORIEN'); header(self,p,'PPH HUB','ALLE KATEGORIEN'); nav(self,p,'more52')
        g=tk.Frame(p,bg=BG); g.pack(fill='both',expand=True,padx=10,pady=5)
        for c in range(3): g.grid_columnconfigure(c,weight=1,uniform='m52')
        for r in range(2): g.grid_rowconfigure(r,weight=1,uniform='m52')
        tiles=[
            ('RADIOS','Adapter, DFS, Kanaele','wifi3',ORANGE),
            ('REPORTS','Messungen und Export','reports',PURPLE),
            ('TOOLS','Netzwerk-Werkzeuge','tools',CYAN),
            ('VERLAUF','Events und Jobs','events3',YELLOW),
            ('SYSTEM','Hardware, Speicher, Dienste','hardware',BLUE),
            ('FIELD','Flow, Vergleich, Session','field50',GREEN),
        ]
        for i,(title,detail,target,accent) in enumerate(tiles):
            menu_tile(self,g,title,detail,target,accent).grid(row=i//3,column=i%3,sticky='nsew',padx=4,pady=4)

    def build_generic(self,name,title,kicker='PPH 5.1',active='system3'):
        text_page(self,name,title,kicker,active,lambda n=name:self.refresh51(n))

    def build_field(self):
        p=replace(self,'field50','FIELD MODE'); header(self,p,'CUSTOMER MODE','FIELD MODE'); nav(self,p,'field50')
        self.p51_field=tk.StringVar(value='READY'); self.p51_field_d=tk.StringVar(value='AP · Diagnostics · Session tools')
        card(self,p,'FIELD STATUS',self.p51_field,GREEN,self.p51_field_d).pack(fill='both',expand=True,padx=12,pady=7)
        actions(self,p,[('CONNECTION FLOW',lambda:self.show_page('flow50'),CYAN),('BEFORE / AFTER',lambda:self.show_page('compare50'),ORANGE),('SESSION',lambda:self.show_page('session50'),PURPLE)])

    def build_pages(self):
        prev_build(self)
        # Legacy nav/sidebar references are no longer used by 5.1.
        try:self.pph30_nav_buttons={}
        except Exception:pass
        build_home(self); build_wireless(self); build_network(self); build_access(self); build_system(self); build_settings(self); build_field(self); build_more(self)
        for name,title,kicker,active in [
            ('wifi3','RADIO CENTER','RF / WLAN','measure3'),('hardware','HARDWARE','DEVICE','system3'),('storage','STORAGE','DEVICE','system3'),
            ('services','SERVICES','SYSTEM','system3'),('events3','EVENTS','SYSTEM','system3'),('jobs3','JOBS','SYSTEM','system3'),('reports','REPORTS','MEASUREMENTS','measure3'),
            ('tools','TOOLS','NETWORK','network'),('network_doctor','NETWORK DOCTOR','DIAGNOSTICS','network'),('lan_mapper','LAN MAPPER','NETWORK','network'),
            ('flow50','CONNECTION FLOW','FIELD','field50'),('compare50','BEFORE / AFTER','FIELD','field50'),('session50','SESSION RECORDER','FIELD','field50'),('notify50','NOTIFICATIONS','SYSTEM','system3')]:
            build_generic(self,name,title,kicker,active)

    def show_page(self,name,title=None,*,push=True):
        aliases={'dashboard':'home3','home412':'home3','home411':'home3','home41':'home3','home32':'home3','access41':'access3','access411':'access3','access412':'access3','analyzer41':'network','analyzer32':'network','network412':'network','network412b':'network','wireless4':'measure3','wireless41':'measure3','wireless411':'measure3','wireless412':'measure3','wireless412b':'measure3'}
        name=aliases.get(name,name)
        prev_show(self,name,title,push=push)
        if name in CORE:self.refresh51(name)
        try:
            self.pph30_nav_buttons={}
            frame=self.frames.get(name)
            if frame is not None: frame.lift()
        except Exception:pass

    def refresh51(self,name):
        if name=='home3':
            route=run(['ip','route','show','default']); self.p51_home_net.set('ONLINE' if route else 'OFFLINE'); self.p51_home_net_d.set(route.splitlines()[0][:48] if route else 'Kein Uplink')
        elif name=='measure3':
            try:st=self._read_measurement_state()
            except Exception:st={}
            s=st.get('signal_dbm') or st.get('rssi'); d=st.get('download_mbps') or st.get('throughput_mbps')
            self.p51_sig.set(f'{float(s):.0f} dBm' if isinstance(s,(int,float)) else '—'); self.p51_thr.set(f'{float(d):.1f} Mbit/s' if isinstance(d,(int,float)) else '—')
        elif name=='network':
            route=run(['ip','route','show','default']); self.p51_net.set('ONLINE' if route else 'OFFLINE'); self.p51_net_d.set(route.splitlines()[0][:42] if route else 'No route')
            gw='';
            try: gw=route.split('via ',1)[1].split()[0] if 'via ' in route else ''
            except Exception: gw=''
            if gw:
                out=run(['ping','-c','1','-W','1',gw]); import re; m=re.search(r'time=([0-9.]+)',out); self.p51_ping.set((m.group(1)+' ms') if m else '—'); self.p51_ping_d.set('Gateway '+gw)
        elif name=='access3':
            try:
                s=self.pph31_ap.status() or {}
            except Exception:s={}
            self.p51_ap.set('ACTIVE' if s.get('active') else 'OFF')
            ssid=s.get('ssid') or 'PPH-WIFI'; clients=s.get('clients',0); self.p51_ap_d.set(f'{ssid} · {clients} Clients')
            code=s.get('pairing_code') or s.get('token') or s.get('code') or s.get('access_code') or '—'
            self.p51_token.set(str(code))
            ip=s.get('ap_ip') or s.get('control_ip') or '10.42.0.1'; lan=s.get('lan_ip') or ''
            self.p51_token_d.set(f'AP-IP {ip}' + (f' · LAN {lan}' if lan else ''))
        elif name=='system3':
            temp=run(['bash','-lc',"cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || true"])
            try:self.p51_cpu.set(f'{int(temp)/1000:.0f}°C')
            except Exception:self.p51_cpu.set('—')
            mem=run(['bash','-lc',"free -m | awk '/Mem:/ {printf \"%d%%\", $3*100/$2}'"]); self.p51_mem.set(mem or '—')
        elif name in ('wifi3','hardware','storage','services','events3','jobs3','reports','tools','network_doctor','lan_mapper','flow50','compare50','session50','notify50'):
            w=getattr(self,'p51_'+name.replace('-','_'),None)
            if w is None:return
            if name=='wifi3': txt=run(['bash','-lc',"for i in /sys/class/net/wlan*; do [ -e \"$i\" ] || continue; n=$(basename \"$i\"); d=$(basename \"$(readlink -f \"$i/device/driver\" 2>/dev/null)\"); echo \"$n  $d\"; done"])
            elif name=='hardware': txt=run(['bash','-lc',"uname -a; echo; lsusb 2>/dev/null | head -12"])
            elif name=='storage': txt=run(['df','-h'])
            elif name=='services': txt=run(['bash','-lc',"systemctl --user --no-pager --type=service --state=running 2>/dev/null | head -18"])
            elif name=='network_doctor': txt=run(['bash','-lc',"ip -br addr; echo; ip route; echo; ping -c 1 -W 1 1.1.1.1 2>&1 | tail -2"])
            elif name=='lan_mapper': txt=run(['ip','neigh'])
            else: txt=f'{name.replace("3","").upper()}\n\nPPH 5.1 Wireless-style interface\nBackend-Funktionen bleiben erhalten.'
            settext(w,txt or 'Keine Daten')

    cls._build_pages=build_pages
    cls.show_page=show_page
    cls.refresh51=refresh51
