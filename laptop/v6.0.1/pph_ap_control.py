#!/usr/bin/env python3
from __future__ import annotations
import json, threading, time, tkinter as tk
from tkinter import messagebox
from urllib import request, error

VERSION='6.0.1'
DEFAULT_PORT=8765
BG='#03070C'; PANEL='#0A111A'; PANEL2='#101B28'; BORDER='#21354A'; TEXT='#F4F8FB'; MUTED='#7891A6'
CYAN='#42DCFF'; GREEN='#45E39A'; RED='#FF6475'; ORANGE='#FF9F68'; PURPLE='#BD8CFF'

STATUS_PATHS=['/api/ap/status','/ap/status','/api/status','/status']
START_PATHS=['/api/ap/start','/ap/start','/api/start','/start']
STOP_PATHS=['/api/ap/stop','/ap/stop','/api/stop','/stop']

class API:
    def __init__(self):
        self.host='10.42.0.1'; self.port=DEFAULT_PORT; self.code=''; self.status_path=None; self.start_path=None; self.stop_path=None
    def base(self): return f'http://{self.host}:{self.port}'
    def call(self,path,method='GET',payload=None,timeout=3):
        data=None; headers={'User-Agent':f'PPH-App-Control/{VERSION}','Accept':'application/json'}
        if self.code:
            headers['X-PPH-Code']=self.code; headers['Authorization']=f'Bearer {self.code}'
        if payload is not None:
            data=json.dumps(payload).encode(); headers['Content-Type']='application/json'
        req=request.Request(self.base()+path,data=data,headers=headers,method=method)
        with request.urlopen(req,timeout=timeout) as r:
            raw=r.read().decode(errors='replace')
            try:return json.loads(raw) if raw else {}
            except Exception:return {'raw':raw,'http_status':r.status}
    def probe(self):
        last=None
        for p in STATUS_PATHS:
            try:
                d=self.call(p); self.status_path=p; return d
            except Exception as e:last=e
        raise last or RuntimeError('Keine Status-API gefunden')
    def command(self,kind):
        paths=START_PATHS if kind=='start' else STOP_PATHS
        remembered=self.start_path if kind=='start' else self.stop_path
        ordered=([remembered] if remembered else [])+[p for p in paths if p!=remembered]
        last=None
        for p in ordered:
            if not p: continue
            for method,payload in [('POST',{}),('GET',None)]:
                try:
                    d=self.call(p,method,payload)
                    if kind=='start': self.start_path=p
                    else:self.stop_path=p
                    return d
                except error.HTTPError as e:
                    last=e
                    if e.code in (404,405): continue
                    raise
                except Exception as e:last=e
        raise last or RuntimeError(f'{kind} fehlgeschlagen')

class App:
    def __init__(self,root):
        self.root=root; self.api=API(); self.busy=False
        root.title(f'PPH App Control {VERSION}'); root.geometry('760x520'); root.minsize(680,460); root.configure(bg=BG)
        top=tk.Frame(root,bg=BG); top.pack(fill='x',padx=18,pady=(16,8))
        tk.Label(top,text='PPH APP CONTROL',bg=BG,fg=CYAN,font=('TkDefaultFont',10,'bold')).pack(anchor='w')
        tk.Label(top,text=f'FIELD ROUTER CONTROL · v{VERSION}',bg=BG,fg=TEXT,font=('TkDefaultFont',20,'bold')).pack(anchor='w')
        conn=tk.Frame(root,bg=PANEL,highlightthickness=1,highlightbackground=BORDER); conn.pack(fill='x',padx=18,pady=6)
        tk.Label(conn,text='PI IP',bg=PANEL,fg=MUTED).grid(row=0,column=0,padx=10,pady=10,sticky='w')
        self.host=tk.StringVar(value='10.42.0.1'); tk.Entry(conn,textvariable=self.host,bg=PANEL2,fg=TEXT,insertbackground=TEXT,relief='flat',width=18).grid(row=0,column=1,padx=6)
        tk.Label(conn,text='CODE',bg=PANEL,fg=MUTED).grid(row=0,column=2,padx=10,sticky='w')
        self.code=tk.StringVar(); tk.Entry(conn,textvariable=self.code,bg=PANEL2,fg=TEXT,insertbackground=TEXT,relief='flat',width=8,show='•').grid(row=0,column=3,padx=6)
        self.connect_btn=self.btn(conn,'CONNECT',self.connect,CYAN); self.connect_btn.grid(row=0,column=4,padx=10,pady=8)
        self.connection=tk.StringVar(value='DISCONNECTED'); tk.Label(conn,textvariable=self.connection,bg=PANEL,fg=ORANGE,font=('TkDefaultFont',10,'bold')).grid(row=0,column=5,padx=10)
        main=tk.Frame(root,bg=BG); main.pack(fill='both',expand=True,padx=18,pady=8); main.grid_columnconfigure((0,1),weight=1); main.grid_rowconfigure((0,1),weight=1)
        self.ap=tk.StringVar(value='—'); self.clients=tk.StringVar(value='—'); self.pairing=tk.StringVar(value='—'); self.ipinfo=tk.StringVar(value='—')
        self.card(main,0,0,'ACCESS POINT',self.ap,GREEN); self.card(main,0,1,'CLIENTS',self.clients,CYAN); self.card(main,1,0,'PAIRING CODE',self.pairing,PURPLE); self.card(main,1,1,'ADDRESS',self.ipinfo,ORANGE)
        actions=tk.Frame(root,bg=BG); actions.pack(fill='x',padx=14,pady=(4,14))
        self.start_btn=self.btn(actions,'START',lambda:self.command('start'),GREEN); self.start_btn.pack(side='left',fill='x',expand=True,padx=4)
        self.stop_btn=self.btn(actions,'STOP',lambda:self.command('stop'),RED); self.stop_btn.pack(side='left',fill='x',expand=True,padx=4)
        self.refresh_btn=self.btn(actions,'REFRESH',self.refresh,CYAN); self.refresh_btn.pack(side='left',fill='x',expand=True,padx=4)
        self.after_id=None
    def btn(self,p,text,cmd,accent):
        return tk.Button(p,text=text,command=cmd,bg=PANEL2,fg=TEXT,activebackground=accent,activeforeground=BG,relief='flat',bd=0,highlightthickness=1,highlightbackground=BORDER,font=('TkDefaultFont',11,'bold'),pady=12,padx=12)
    def card(self,p,r,c,title,var,accent):
        f=tk.Frame(p,bg=PANEL,highlightthickness=1,highlightbackground=BORDER); f.grid(row=r,column=c,sticky='nsew',padx=5,pady=5)
        tk.Frame(f,bg=accent,height=5).pack(fill='x'); tk.Label(f,text=title,bg=PANEL,fg=MUTED,font=('TkDefaultFont',9,'bold')).pack(anchor='w',padx=14,pady=(12,0)); tk.Label(f,textvariable=var,bg=PANEL,fg=accent,font=('TkDefaultFont',24,'bold'),wraplength=310,justify='left').pack(anchor='w',padx=14,pady=(4,12))
    def bg(self,fn):
        if self.busy:return
        self.busy=True
        def run():
            try:fn()
            except Exception as e:
                msg=str(e)
                self.root.after(0,lambda m=msg: messagebox.showerror('PPH App Control',m))
            finally:self.root.after(0,self._idle)
        threading.Thread(target=run,daemon=True).start()
    def _idle(self):self.busy=False
    def configure_api(self):
        self.api.host=self.host.get().strip() or '10.42.0.1'; self.api.code=self.code.get().strip()
    def connect(self):
        def work():
            self.configure_api(); d=self.api.probe(); self.root.after(0,lambda:self.apply(d,True)); self.root.after(0,self.schedule)
        self.bg(work)
    def refresh(self):
        def work():
            self.configure_api(); d=self.api.call(self.api.status_path) if self.api.status_path else self.api.probe(); self.root.after(0,lambda:self.apply(d,True))
        self.bg(work)
    def command(self,kind):
        def work():
            self.configure_api(); self.api.command(kind); time.sleep(.7); d=self.api.call(self.api.status_path) if self.api.status_path else self.api.probe(); self.root.after(0,lambda:self.apply(d,True))
        self.bg(work)
    def schedule(self):
        if self.after_id:
            try:self.root.after_cancel(self.after_id)
            except Exception:pass
        self.after_id=self.root.after(2000,self.poll)
    def poll(self):
        def work():
            try:
                self.configure_api(); d=self.api.call(self.api.status_path) if self.api.status_path else self.api.probe(); self.root.after(0,lambda:self.apply(d,True))
            except Exception:self.root.after(0,lambda:self.connection.set('OFFLINE'))
            finally:self.root.after(0,self.schedule)
        threading.Thread(target=work,daemon=True).start()
    def apply(self,d,connected=False):
        if not isinstance(d,dict): d={}
        src=d.get('access_point') if isinstance(d.get('access_point'),dict) else d.get('ap') if isinstance(d.get('ap'),dict) else d
        active=src.get('active'); active=src.get('running',active); active=src.get('enabled',active)
        if isinstance(active,str): active=active.lower() in ('1','true','on','active','running','yes')
        self.ap.set('ACTIVE' if active else 'OFF')
        clients=src.get('clients',src.get('client_count',src.get('connected_clients','—')))
        if isinstance(clients,list):clients=len(clients)
        self.clients.set(str(clients))
        code=src.get('pairing_code') or src.get('token') or src.get('code') or src.get('access_code') or '—'; self.pairing.set(str(code))
        apip=src.get('ap_ip') or src.get('control_ip') or '10.42.0.1'; lan=src.get('lan_ip') or src.get('uplink_ip') or ''
        self.ipinfo.set(str(apip)+(f'\nLAN {lan}' if lan else ''))
        if connected:self.connection.set('CONNECTED')

if __name__=='__main__':
    root=tk.Tk(); App(root); root.mainloop()
