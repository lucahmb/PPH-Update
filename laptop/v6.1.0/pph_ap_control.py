#!/usr/bin/env python3
from __future__ import annotations
import json, socket, threading, time, tkinter as tk
from tkinter import messagebox
from urllib import request, error

VERSION='6.1.0'
DEFAULT_PORT=8788
DEFAULT_SSID='Hotspot'
DEFAULT_PASSWORD='Keller 098!'
BG='#03070C'; PANEL='#0A111A'; PANEL2='#101B28'; BORDER='#21354A'; TEXT='#F4F8FB'; MUTED='#7891A6'
CYAN='#42DCFF'; GREEN='#45E39A'; RED='#FF6475'; ORANGE='#FF9F68'; PURPLE='#BD8CFF'; YELLOW='#FFD166'
STATUS_PATH='/status'; START_PATH='/start'; STOP_PATH='/stop'; CONFIG_PATH='/config'; HEALTH_PATH='/health'

class API:
    def __init__(self): self.host='10.42.0.1'; self.port=DEFAULT_PORT; self.code=''
    def base(self): return f'http://{self.host}:{self.port}'
    def call(self,path,method='GET',payload=None,timeout=5,auth=True):
        data=None; headers={'User-Agent':f'PPH-App-Control/{VERSION}','Accept':'application/json','Connection':'close'}
        if auth and self.code: headers['X-PPH-Token']=self.code
        if payload is not None:
            data=json.dumps(payload).encode(); headers['Content-Type']='application/json'
        req=request.Request(self.base()+path,data=data,headers=headers,method=method)
        with request.urlopen(req,timeout=timeout) as r:
            raw=r.read().decode(errors='replace')
            try:return json.loads(raw) if raw else {}
            except Exception:return {'raw':raw,'http_status':r.status}
    def health(self,timeout=2): return self.call(HEALTH_PATH,timeout=timeout,auth=False)
    def status(self,timeout=5): return self.call(STATUS_PATH,timeout=timeout)
    def config(self,timeout=5): return self.call(CONFIG_PATH,timeout=timeout)
    def probe(self): self.health(); return self.status()
    def save_config(self,ssid,password,band,timeout=12):
        payload={'ssid':ssid or None,'band':band or None}
        if password: payload['password']=password
        return self.call(CONFIG_PATH,method='POST',payload=payload,timeout=timeout)
    def command(self,kind): return self.call(START_PATH if kind=='start' else STOP_PATH,method='POST',payload={},timeout=8)

class App:
    def __init__(self,root):
        self.root=root; self.api=API(); self.busy=False; self.after_id=None
        root.title(f'PPH App Control {VERSION}'); root.geometry('860x700'); root.minsize(780,620); root.configure(bg=BG)
        top=tk.Frame(root,bg=BG); top.pack(fill='x',padx=18,pady=(14,6))
        tk.Label(top,text='PPH APP CONTROL',bg=BG,fg=CYAN,font=('TkDefaultFont',10,'bold')).pack(anchor='w')
        title=tk.Frame(top,bg=BG); title.pack(fill='x')
        tk.Label(title,text=f'FIELD ROUTER CONTROL · v{VERSION}',bg=BG,fg=TEXT,font=('TkDefaultFont',20,'bold')).pack(side='left')
        self.operation=tk.StringVar(value='READY')
        tk.Label(title,textvariable=self.operation,bg=PANEL2,fg=CYAN,font=('TkDefaultFont',10,'bold'),padx=12,pady=6).pack(side='right')

        conn=tk.Frame(root,bg=PANEL,highlightthickness=1,highlightbackground=BORDER); conn.pack(fill='x',padx=18,pady=6)
        tk.Label(conn,text='PI IP',bg=PANEL,fg=MUTED).grid(row=0,column=0,padx=10,pady=10,sticky='w')
        self.host=tk.StringVar(value='10.42.0.1'); tk.Entry(conn,textvariable=self.host,bg=PANEL2,fg=TEXT,insertbackground=TEXT,relief='flat',width=18).grid(row=0,column=1,padx=6)
        tk.Label(conn,text='PAIR CODE',bg=PANEL,fg=MUTED).grid(row=0,column=2,padx=10,sticky='w')
        self.code=tk.StringVar(); tk.Entry(conn,textvariable=self.code,bg=PANEL2,fg=TEXT,insertbackground=TEXT,relief='flat',width=8,show='•').grid(row=0,column=3,padx=6)
        self.connect_btn=self.btn(conn,'CONNECT',self.connect,CYAN); self.connect_btn.grid(row=0,column=4,padx=10,pady=8)
        self.connection=tk.StringVar(value='DISCONNECTED'); tk.Label(conn,textvariable=self.connection,bg=PANEL,fg=ORANGE,font=('TkDefaultFont',10,'bold')).grid(row=0,column=5,padx=10)

        cfg=tk.Frame(root,bg=PANEL,highlightthickness=1,highlightbackground=BORDER); cfg.pack(fill='x',padx=18,pady=6)
        tk.Label(cfg,text='ACCESS POINT CONFIG',bg=PANEL,fg=PURPLE,font=('TkDefaultFont',9,'bold')).grid(row=0,column=0,columnspan=4,padx=10,pady=(10,4),sticky='w')
        tk.Label(cfg,text='WLAN NAME',bg=PANEL,fg=MUTED).grid(row=1,column=0,padx=10,pady=5,sticky='w')
        self.ssid=tk.StringVar(value=DEFAULT_SSID); tk.Entry(cfg,textvariable=self.ssid,bg=PANEL2,fg=TEXT,insertbackground=TEXT,relief='flat',width=24).grid(row=1,column=1,padx=6,pady=5,sticky='ew')
        tk.Label(cfg,text='PASSWORT',bg=PANEL,fg=MUTED).grid(row=1,column=2,padx=10,pady=5,sticky='w')
        self.password=tk.StringVar(value=DEFAULT_PASSWORD); tk.Entry(cfg,textvariable=self.password,bg=PANEL2,fg=TEXT,insertbackground=TEXT,relief='flat',width=20,show='•').grid(row=1,column=3,padx=6,pady=5,sticky='ew')
        tk.Label(cfg,text='BAND',bg=PANEL,fg=MUTED).grid(row=2,column=0,padx=10,pady=(5,10),sticky='w')
        self.band=tk.StringVar(value='a')
        bandf=tk.Frame(cfg,bg=PANEL); bandf.grid(row=2,column=1,padx=6,pady=(5,10),sticky='w')
        tk.Radiobutton(bandf,text='5 GHz',variable=self.band,value='a',bg=PANEL,fg=TEXT,selectcolor=PANEL2,activebackground=PANEL,activeforeground=TEXT).pack(side='left')
        tk.Radiobutton(bandf,text='2.4 GHz',variable=self.band,value='bg',bg=PANEL,fg=TEXT,selectcolor=PANEL2,activebackground=PANEL,activeforeground=TEXT).pack(side='left')
        self.save_btn=self.btn(cfg,'SAVE CONFIG',self.save_config,PURPLE); self.save_btn.grid(row=2,column=3,padx=6,pady=(5,10),sticky='ew')
        cfg.grid_columnconfigure(1,weight=1); cfg.grid_columnconfigure(3,weight=1)

        main=tk.Frame(root,bg=BG); main.pack(fill='both',expand=True,padx=18,pady=6); main.grid_columnconfigure((0,1),weight=1); main.grid_rowconfigure((0,1),weight=1)
        self.ap=tk.StringVar(value='—'); self.clients=tk.StringVar(value='—'); self.pairing=tk.StringVar(value='—'); self.ipinfo=tk.StringVar(value='—')
        self.card(main,0,0,'ACCESS POINT',self.ap,GREEN); self.card(main,0,1,'CLIENTS',self.clients,CYAN); self.card(main,1,0,'PAIRING CODE',self.pairing,PURPLE); self.card(main,1,1,'ADDRESS',self.ipinfo,ORANGE)
        actions=tk.Frame(root,bg=BG); actions.pack(fill='x',padx=14,pady=(4,14))
        self.start_btn=self.btn(actions,'START',lambda:self.command('start'),GREEN); self.start_btn.pack(side='left',fill='x',expand=True,padx=4)
        self.stop_btn=self.btn(actions,'STOP',lambda:self.command('stop'),RED); self.stop_btn.pack(side='left',fill='x',expand=True,padx=4)
        self.refresh_btn=self.btn(actions,'REFRESH',self.refresh,CYAN); self.refresh_btn.pack(side='left',fill='x',expand=True,padx=4)

    def btn(self,p,text,cmd,accent):
        return tk.Button(p,text=text,command=cmd,bg=PANEL2,fg=TEXT,activebackground=accent,activeforeground=BG,relief='flat',bd=0,highlightthickness=1,highlightbackground=BORDER,font=('TkDefaultFont',11,'bold'),pady=12,padx=12)
    def card(self,p,r,c,title,var,accent):
        f=tk.Frame(p,bg=PANEL,highlightthickness=1,highlightbackground=BORDER); f.grid(row=r,column=c,sticky='nsew',padx=5,pady=5)
        tk.Frame(f,bg=accent,height=5).pack(fill='x'); tk.Label(f,text=title,bg=PANEL,fg=MUTED,font=('TkDefaultFont',9,'bold')).pack(anchor='w',padx=14,pady=(10,0)); tk.Label(f,textvariable=var,bg=PANEL,fg=accent,font=('TkDefaultFont',22,'bold'),wraplength=350,justify='left').pack(anchor='w',padx=14,pady=(4,10))
    def set_op(self,text): self.root.after(0,lambda:self.operation.set(text))
    def bg(self,fn,op='WORKING'):
        if self.busy:return
        self.busy=True; self.set_op(op)
        def run():
            try:fn()
            except error.HTTPError as e:
                if e.code==401: msg='Pair-Code falsch oder abgelaufen.'
                elif e.code==404: msg=f'AP-API nicht gefunden: {self.api.base()}'
                else: msg=f'HTTP {e.code}: {e.reason}'
                self.root.after(0,lambda m=msg: messagebox.showerror('PPH App Control',m))
            except Exception as e:
                msg=str(e); self.root.after(0,lambda m=msg: messagebox.showerror('PPH App Control',m))
            finally:self.root.after(0,self._idle)
        threading.Thread(target=run,daemon=True).start()
    def _idle(self): self.busy=False; self.operation.set('READY')
    def configure_api(self): self.api.host=self.host.get().strip() or '10.42.0.1'; self.api.code=self.code.get().strip()
    def connect(self):
        def work():
            self.configure_api(); d=self.api.probe(); c=self.api.config(); self.root.after(0,lambda:self.apply(d,True)); self.root.after(0,lambda:self.apply_config(c)); self.root.after(0,self.schedule)
        self.bg(work,'CONNECTING')
    def apply_config(self,c):
        if not isinstance(c,dict): return
        if c.get('ssid'): self.ssid.set(str(c['ssid']))
        if c.get('band'): self.band.set(str(c['band']))
        # API intentionally does not return password. Keep user-entered value.
    def wait_api(self,deadline=15):
        end=time.time()+deadline; last=None
        while time.time()<end:
            try:
                self.api.health(timeout=2); return True
            except Exception as e: last=e; time.sleep(.8)
        if last: raise last
        return False
    def save_config(self):
        desired_ssid=self.ssid.get().strip() or DEFAULT_SSID
        desired_password=self.password.get()
        desired_band=self.band.get() or 'a'
        def work():
            self.configure_api(); timed_out=False
            try:
                self.api.save_config(desired_ssid,desired_password,desired_band,timeout=12)
            except (TimeoutError, socket.timeout):
                timed_out=True
            except error.URLError as e:
                if isinstance(getattr(e,'reason',None), socket.timeout): timed_out=True
                else: raise
            # Config changes may temporarily disrupt AP/network state. Reconnect instead of failing immediately.
            if timed_out:
                self.set_op('RECONNECTING')
            self.wait_api(18)
            self.set_op('VERIFYING')
            c=self.api.config(timeout=6)
            got_ssid=str(c.get('ssid') or '')
            got_band=str(c.get('band') or '')
            if got_ssid != desired_ssid or got_band != desired_band:
                raise RuntimeError(f'Config konnte nicht verifiziert werden. Pi meldet SSID={got_ssid!r}, Band={got_band!r}.')
            self.root.after(0,lambda:self.apply_config(c))
            self.root.after(0,lambda:messagebox.showinfo('PPH App Control','WLAN-Konfiguration gespeichert und verifiziert.'))
        self.bg(work,'SAVING CONFIG')
    def refresh(self):
        def work():
            self.configure_api(); d=self.api.status(); self.root.after(0,lambda:self.apply(d,True))
        self.bg(work,'REFRESHING')
    def command(self,kind):
        def work():
            self.configure_api(); self.api.command(kind)
            if kind=='start':
                self.set_op('STARTING AP'); deadline=time.time()+18; last={}
                while time.time()<deadline:
                    time.sleep(.8); last=self.api.status(timeout=5)
                    self.root.after(0,lambda d=last:self.apply(d,True))
                    if bool(last.get('active')): return
                details=[]
                for k in ('field_mode','lan_connected','internet','forwarding','wifi_iface','driver'):
                    if k in last: details.append(f'{k}={last.get(k)}')
                raise RuntimeError('START wurde angenommen, aber der Access Point wurde nicht aktiv.' + (f"\nStatus: {', '.join(details)}" if details else ''))
            else:
                self.set_op('STOPPING AP'); time.sleep(.8); d=self.api.status(); self.root.after(0,lambda:self.apply(d,True))
        self.bg(work,'STARTING AP' if kind=='start' else 'STOPPING AP')
    def schedule(self):
        if self.after_id:
            try:self.root.after_cancel(self.after_id)
            except Exception:pass
        self.after_id=self.root.after(2500,self.poll)
    def poll(self):
        def work():
            try:
                self.configure_api(); d=self.api.status(timeout=4); self.root.after(0,lambda:self.apply(d,True))
            except Exception:self.root.after(0,lambda:self.connection.set('OFFLINE'))
            finally:self.root.after(0,self.schedule)
        threading.Thread(target=work,daemon=True).start()
    def apply(self,d,connected=False):
        if not isinstance(d,dict): d={}
        active=d.get('active',False)
        if isinstance(active,str): active=active.lower() in ('1','true','on','active','running','yes')
        self.ap.set('ACTIVE' if active else 'OFF')
        clients=d.get('clients','—'); self.clients.set(str(len(clients) if isinstance(clients,list) else clients))
        self.pairing.set(str(d.get('pairing_code') or '—'))
        apip=d.get('ap_ip') or '10.42.0.1'; lan=d.get('lan_ip') or ''
        self.ipinfo.set(str(apip)+(f'\nLAN {lan}' if lan else ''))
        if connected:self.connection.set('CONNECTED')

if __name__=='__main__':
    root=tk.Tk(); App(root); root.mainloop()
