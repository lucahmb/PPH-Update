#!/usr/bin/env python3
from __future__ import annotations
import json,time,tkinter as tk
from pathlib import Path
from typing import Any
BG='#03070c'; PANEL='#0a111a'; PANEL2='#101b28'; BORDER='#21354a'; TEXT='#f4f8fb'; MUTED='#7891a6'; CYAN='#42dcff'; GREEN='#45e39a'; ORANGE='#ff9f68'; PURPLE='#bd8cff'; RED='#ff6475'; BLUE='#6f8cff'
STATE=Path.home()/'.local/share/pph5'; SESSIONS=STATE/'sessions'

def install(cls:type,ns:dict[str,Any])->None:
    prev_build=cls._build_pages; prev_show=cls.show_page

    def widget_texts(w):
        out=[]
        stack=[w]
        while stack:
            x=stack.pop()
            try:
                txt=str(x.cget('text') or '')
                if txt: out.append(txt.upper())
            except Exception: pass
            try: stack.extend(x.winfo_children())
            except Exception: pass
        return out

    def cleanup(self):
        # Remove legacy root-level navigation/overlay widgets from 3.x/4.x.
        for w in list(self.root.winfo_children()):
            if w is getattr(self,'content',None):
                continue
            remove=False
            texts=' '.join(widget_texts(w))
            if 'FIELD INTERFACE' in texts or 'PPH 4.0' in texts or 'PPH 4 · FIELD INTERFACE' in texts:
                remove=True
            try:
                info=w.pack_info()
                remove = remove or (info.get('side')=='bottom' and w is not getattr(self,'content',None))
            except Exception: pass
            try:
                pl=w.place_info()
                if pl:
                    rely=str(pl.get('rely',''))
                    y=str(pl.get('y',''))
                    remove = remove or rely in ('1','1.0') or y in ('430','440','450','460')
            except Exception: pass
            if remove:
                try:w.destroy()
                except Exception:pass
        for b in getattr(self,'pph30_nav_buttons',{}).values():
            try:b.destroy()
            except Exception:pass
        # Current page, including its 5.0 bottom nav, must be above surviving root widgets.
        try:
            frame=self.frames.get(self.current_page)
            if frame is not None:
                frame.lift()
                frame.update_idletasks()
        except Exception: pass

    def replace(self,name,title):
        old=self.frames.get(name)
        if old is not None:
            try:old.destroy()
            except Exception:pass
            self.frames.pop(name,None)
        return self._new_page(name,title)
    def button(self,p,text,cmd,accent=CYAN):
        return tk.Button(p,text=text,command=cmd,bg=PANEL2,fg=TEXT,activebackground=accent,activeforeground=BG,relief='flat',bd=0,highlightthickness=1,highlightbackground=BORDER,font=self._font(11,'bold'),pady=11,padx=7)
    def header(self,p,title):
        h=tk.Frame(p,bg=BG,height=52);h.pack(fill='x',padx=11,pady=(6,3));h.pack_propagate(False)
        tk.Label(h,text='PPH 5 · FIELD PLATFORM',bg=BG,fg=CYAN,font=self._font(7,'bold')).pack(anchor='w')
        tk.Label(h,text=title,bg=BG,fg=TEXT,font=self._font(17,'bold')).pack(anchor='w')
    def nav(self,p,active):
        n=tk.Frame(p,bg='#050a10',height=66,highlightthickness=1,highlightbackground=BORDER)
        n.pack(side='bottom',fill='x');n.pack_propagate(False)
        n._pph50_nav=True
        for i,(lab,target) in enumerate([('HOME','home3'),('WLAN','measure3'),('NETZ','network'),('FIELD','field50'),('SYSTEM','system3')]):
            n.grid_columnconfigure(i,weight=1,uniform='n50')
            b=button(self,n,lab,lambda t=target:self.show_page(t),CYAN)
            b.configure(font=self._font(9,'bold'),pady=10,bg=CYAN if target==active else PANEL2,fg=BG if target==active else TEXT)
            b.grid(row=0,column=i,sticky='nsew',padx=2,pady=5)
        try:n.lift()
        except Exception:pass
    def hero(self,p,title,var,detail,accent=GREEN):
        f=tk.Frame(p,bg=PANEL,highlightthickness=1,highlightbackground=BORDER);tk.Frame(f,bg=accent,height=5).pack(fill='x');tk.Label(f,text=title,bg=PANEL,fg=MUTED,font=self._font(8,'bold')).pack(anchor='w',padx=14,pady=(10,0));tk.Label(f,textvariable=var,bg=PANEL,fg=accent,font=self._font(26,'bold')).pack(anchor='w',padx=14);tk.Label(f,textvariable=detail,bg=PANEL,fg=TEXT,font=self._font(9),wraplength=700,justify='left').pack(anchor='w',padx=14,pady=(0,8));return f
    def textpanel(self,p): return tk.Text(p,bg=PANEL,fg=TEXT,relief='flat',bd=0,highlightthickness=1,highlightbackground=BORDER,font=self._font(9),wrap='word',padx=10,pady=8)
    def settext(w,s):
        w.configure(state='normal');w.delete('1.0','end');w.insert('end',s);w.configure(state='disabled')
    def field(self):
        p=replace(self,'field50','FIELD MODE');header(self,p,'FIELD MODE');nav(self,p,'field50');self.f50v=tk.StringVar(value='READY');self.f50d=tk.StringVar(value='Customer mode · AP · Self-Healing · Diagnostics');hero(self,p,'CUSTOMER MODE',self.f50v,self.f50d).pack(fill='both',expand=True,padx=11,pady=6);r=tk.Frame(p,bg=BG);r.pack(fill='x',padx=8,pady=(0,6));
        for lab,t,a in [('FLOW','flow50',CYAN),('BEFORE/AFTER','compare50',ORANGE),('SESSION','session50',PURPLE)]:button(self,r,lab,lambda x=t:self.show_page(x),a).pack(side='left',fill='x',expand=True,padx=3)
    def flow(self):
        p=replace(self,'flow50','CONNECTION FLOW');header(self,p,'CONNECTION FLOW');nav(self,p,'field50');self.flow50={k:tk.StringVar(value='—') for k in ('internet','uplink','pi','ap','clients')};r=tk.Frame(p,bg=BG);r.pack(fill='both',expand=True,padx=9,pady=7)
        for i,(lab,key,a) in enumerate([('INTERNET','internet',GREEN),('UPLINK','uplink',CYAN),('PI','pi',PURPLE),('PPH-WIFI','ap',ORANGE),('CLIENTS','clients',BLUE)]):r.grid_columnconfigure(i,weight=1,uniform='flow');c=tk.Frame(r,bg=PANEL,highlightthickness=1,highlightbackground=BORDER);c.grid(row=0,column=i,sticky='nsew',padx=3);tk.Label(c,text=lab,bg=PANEL,fg=MUTED,font=self._font(7,'bold')).pack(pady=(18,3));tk.Label(c,textvariable=self.flow50[key],bg=PANEL,fg=a,font=self._font(13,'bold'),wraplength=120).pack(padx=4,pady=6)
    def compare(self):
        p=replace(self,'compare50','BEFORE / AFTER');header(self,p,'BEFORE / AFTER');nav(self,p,'field50');self.before50=tk.StringVar(value='NOT SET');self.after50=tk.StringVar(value='NOT SET');self.delta50=tk.StringVar(value='Take two measurements');g=tk.Frame(p,bg=BG);g.pack(fill='both',expand=True,padx=9,pady=6);g.grid_columnconfigure(0,weight=1);g.grid_columnconfigure(1,weight=1);hero(self,g,'BEFORE',self.before50,self.delta50,ORANGE).grid(row=0,column=0,sticky='nsew',padx=4);hero(self,g,'AFTER',self.after50,self.delta50,GREEN).grid(row=0,column=1,sticky='nsew',padx=4);r=tk.Frame(p,bg=BG);r.pack(fill='x',padx=9,pady=(0,7));button(self,r,'SAVE BEFORE',lambda:self.capture50('before'),ORANGE).pack(side='left',fill='x',expand=True,padx=3);button(self,r,'SAVE AFTER',lambda:self.capture50('after'),GREEN).pack(side='left',fill='x',expand=True,padx=3)
    def session(self):
        p=replace(self,'session50','SESSION');header(self,p,'SESSION RECORDER');nav(self,p,'field50');self.session50v=tk.StringVar(value='STOPPED');self.session50d=tk.StringVar(value='Record a customer visit');hero(self,p,'RECORDER',self.session50v,self.session50d,RED).pack(fill='both',expand=True,padx=11,pady=6);r=tk.Frame(p,bg=BG);r.pack(fill='x',padx=9,pady=(0,7));button(self,r,'START',self.session_start50,GREEN).pack(side='left',fill='x',expand=True,padx=3);button(self,r,'STOP + SAVE',self.session_stop50,RED).pack(side='left',fill='x',expand=True,padx=3)
    def notifications(self):
        p=replace(self,'notify50','NOTIFICATIONS');header(self,p,'NOTIFICATIONS');nav(self,p,'system3');self.notify50=textpanel(self,p);self.notify50.pack(fill='both',expand=True,padx=11,pady=7)
    def build_pages(self):
        prev_build(self);cleanup(self);field(self);flow(self);compare(self);session(self);notifications(self)
        for d in (0,40,120,300,800): self.root.after(d,lambda s=self:cleanup(s))
    def show_page(self,name,title=None,*,push=True):
        prev_show(self,name,title,push=push);cleanup(self)
        for d in (0,30,100): self.root.after(d,lambda s=self:cleanup(s))
        if name=='flow50':self.refresh_flow50()
        elif name=='notify50':self.refresh_notify50()
    def refresh_flow50(self):
        self.flow50['pi'].set('READY')
        try:s=self.pph31_ap.status();self.flow50['ap'].set('ACTIVE' if s.get('active') else 'OFF');self.flow50['clients'].set(str(s.get('clients',0)));self.flow50['internet'].set('ONLINE' if s.get('internet_ok',True) else 'OFFLINE');self.flow50['uplink'].set(str(s.get('lan_iface') or 'eth0'))
        except Exception:self.flow50['ap'].set('—')
    def capture50(self,which):
        try:st=self._read_measurement_state()
        except Exception:st={}
        val=st.get('download_mbps') or st.get('throughput_mbps');snap={'download':val,'signal':st.get('signal_dbm') or st.get('rssi'),'time':time.time()};setattr(self,'_'+which+'50',snap);getattr(self,which+'50').set(f'{float(val):.1f} Mbit/s' if isinstance(val,(int,float)) else 'SAVED');b=getattr(self,'_before50',None);a=getattr(self,'_after50',None)
        if b and a and isinstance(b.get('download'),(int,float)) and isinstance(a.get('download'),(int,float)):self.delta50.set(f"{float(a['download'])-float(b['download']):+.1f} Mbit/s")
    def session_start50(self):
        STATE.mkdir(parents=True,exist_ok=True);SESSIONS.mkdir(parents=True,exist_ok=True);self._session50={'started':time.time(),'samples':[]};self.session50v.set('RECORDING');self.session50d.set(time.strftime('Started %H:%M:%S'));self.sample50()
    def sample50(self):
        if not getattr(self,'_session50',None):return
        try:st=self._read_measurement_state()
        except Exception:st={}
        self._session50['samples'].append({'t':time.time(),'state':st});self.root.after(5000,self.sample50)
    def session_stop50(self):
        if not getattr(self,'_session50',None):return
        SESSIONS.mkdir(parents=True,exist_ok=True);p=SESSIONS/(time.strftime('%Y%m%d-%H%M%S')+'.json');p.write_text(json.dumps(self._session50,indent=2,default=str));self._session50=None;self.session50v.set('SAVED');self.session50d.set(p.name)
    def refresh_notify50(self):
        try:ev=ns['_pph28_events'].read_events(limit=15);settext(self.notify50,'\n\n'.join(str(x.get('message') or x) for x in reversed(ev)) if ev else 'No notifications')
        except Exception:settext(self.notify50,'No notifications')
    cls._build_pages=build_pages;cls.show_page=show_page;cls.refresh_flow50=refresh_flow50;cls.capture50=capture50;cls.session_start50=session_start50;cls.session_stop50=session_stop50;cls.sample50=sample50;cls.refresh_notify50=refresh_notify50
