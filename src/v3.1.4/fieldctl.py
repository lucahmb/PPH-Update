#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

CONNECTION = "PPH-AccessPoint"
DRIVER = "mt7921u"
AP_ADDR = "10.42.0.1/24"
SUBNET = "10.42.0.0/24"


def run(args: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    p = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and p.returncode:
        raise RuntimeError(p.stderr.strip() or p.stdout.strip() or f"Befehl fehlgeschlagen: {' '.join(args)}")
    return p


def driver_of(iface: str) -> str:
    for p in (Path('/sys/class/net')/iface/'device/driver/module', Path('/sys/class/net')/iface/'device/driver'):
        try:
            return Path(os.path.realpath(p)).name
        except OSError:
            pass
    return ''


def brostrend() -> str:
    for p in Path('/sys/class/net').iterdir():
        if driver_of(p.name) == DRIVER:
            return p.name
    raise RuntimeError('BrosTrend mt7921u nicht gefunden')


def carrier(iface: str) -> bool:
    try:
        return (Path('/sys/class/net')/iface/'carrier').read_text().strip() == '1'
    except OSError:
        return False


def uplink() -> str:
    # Prefer the active ethernet default route. Fall back to any ethernet interface with carrier.
    p = run(['ip','route','show','default'])
    for line in p.stdout.splitlines():
        parts = line.split()
        if 'dev' in parts:
            iface = parts[parts.index('dev')+1]
            if iface.startswith(('eth','en')) and carrier(iface):
                return iface
    for pth in Path('/sys/class/net').iterdir():
        if pth.name.startswith(('eth','en')) and carrier(pth.name):
            return pth.name
    raise RuntimeError('Kein aktiver LAN-Uplink gefunden')


def ipv4(iface: str) -> str:
    p=run(['ip','-4','-o','addr','show','dev',iface])
    for line in p.stdout.splitlines():
        parts=line.split()
        if 'inet' in parts:
            return parts[parts.index('inet')+1].split('/',1)[0]
    return ''


def rule_present(args: list[str]) -> bool:
    return run(['iptables','-C']+args).returncode == 0


def ensure_forward_rules(ap: str, up: str) -> None:
    # Docker installs a FORWARD policy DROP on this Pi. Allow only the PPH subnet through DOCKER-USER.
    out_rule=['DOCKER-USER','-i',ap,'-o',up,'-s',SUBNET,'-j','ACCEPT']
    back_rule=['DOCKER-USER','-i',up,'-o',ap,'-d',SUBNET,'-m','conntrack','--ctstate','ESTABLISHED,RELATED','-j','ACCEPT']
    if run(['iptables','-nL','DOCKER-USER']).returncode == 0:
        if not rule_present(out_rule):
            run(['iptables','-I']+out_rule+['-w'], check=True)
        if not rule_present(back_rule):
            run(['iptables','-I']+back_rule+['-w'], check=True)
    else:
        # Safe fallback if Docker is absent/disabled.
        fwd1=['FORWARD','-i',ap,'-o',up,'-s',SUBNET,'-j','ACCEPT']
        fwd2=['FORWARD','-i',up,'-o',ap,'-d',SUBNET,'-m','conntrack','--ctstate','ESTABLISHED,RELATED','-j','ACCEPT']
        if not rule_present(fwd1): run(['iptables','-I']+fwd1+['-w'],check=True)
        if not rule_present(fwd2): run(['iptables','-I']+fwd2+['-w'],check=True)


def remove_forward_rules(ap: str, up: str) -> None:
    rules=[
        ['DOCKER-USER','-i',ap,'-o',up,'-s',SUBNET,'-j','ACCEPT'],
        ['DOCKER-USER','-i',up,'-o',ap,'-d',SUBNET,'-m','conntrack','--ctstate','ESTABLISHED,RELATED','-j','ACCEPT'],
        ['FORWARD','-i',ap,'-o',up,'-s',SUBNET,'-j','ACCEPT'],
        ['FORWARD','-i',up,'-o',ap,'-d',SUBNET,'-m','conntrack','--ctstate','ESTABLISHED,RELATED','-j','ACCEPT'],
    ]
    for args in rules:
        while rule_present(args):
            run(['iptables','-D']+args+['-w'])


def active_on(iface: str) -> bool:
    p=run(['nmcli','-t','-f','NAME,DEVICE','connection','show','--active'])
    return any(line == f'{CONNECTION}:{iface}' for line in p.stdout.splitlines())


def wait_for_ap(iface: str, timeout: float = 20.0) -> None:
    deadline=time.monotonic()+timeout
    while time.monotonic() < deadline:
        if active_on(iface) and ipv4(iface) == '10.42.0.1':
            return
        time.sleep(.5)
    raise RuntimeError('PPH-AccessPoint wurde nicht auf der BrosTrend aktiv')


def start(ssid: str, password: str, band: str = 'a') -> dict:
    if not ssid or len(ssid) > 32:
        raise RuntimeError('Ungültige SSID')
    if len(password) < 8 or len(password) > 63:
        raise RuntimeError('Ungültiges WLAN-Passwort')
    if band not in {'a','bg'}:
        raise RuntimeError('Ungültiges Band')
    ap=brostrend(); up=uplink()
    run(['nmcli','radio','wifi','on'])
    run(['ip','link','set',ap,'up'])
    run(['nmcli','connection','delete',CONNECTION])
    run(['nmcli','connection','add','type','wifi','ifname',ap,'con-name',CONNECTION,'ssid',ssid],check=True)
    run(['nmcli','connection','modify',CONNECTION,
         '802-11-wireless.mode','ap','802-11-wireless.band',band,
         'wifi-sec.key-mgmt','wpa-psk','wifi-sec.psk',password,
         'ipv4.method','shared','ipv4.addresses',AP_ADDR,
         'ipv6.method','disabled','connection.autoconnect','yes'],check=True)
    run(['nmcli','connection','up',CONNECTION],check=True)
    wait_for_ap(ap)
    ensure_forward_rules(ap,up)
    # Verify the chosen wired uplink itself has internet. This does not depend on a client already being connected.
    internet = run(['ping','-I',up,'-c','1','-W','2','1.1.1.1']).returncode == 0
    result={'ok':True,'ap_iface':ap,'driver':DRIVER,'uplink':up,'uplink_ip':ipv4(up),'ap_ip':'10.42.0.1','internet':internet,'forwarding':True}
    print(json.dumps(result))
    return result


def stop() -> None:
    ap=brostrend()
    try: up=uplink()
    except Exception: up='eth0'
    remove_forward_rules(ap,up)
    run(['nmcli','connection','down',CONNECTION])


def config_for(user: str) -> tuple[str,str,str]:
    home=Path('/home')/user
    if user == 'root': home=Path('/root')
    cfg=home/'.config/pph-ap/config.json'
    data=json.loads(cfg.read_text(encoding='utf-8'))
    return str(data.get('ssid') or 'PPH-WIFI'), str(data.get('password') or ''), str(data.get('band') or 'a')


def watch(user: str) -> None:
    last=False
    first=True
    while True:
        try:
            up=uplink(); now=carrier(up)
        except Exception:
            now=False
        if now and (first or not last):
            try:
                ssid,password,band=config_for(user)
                start(ssid,password,band)
            except Exception as exc:
                print(f'PPH field auto-start failed: {exc}', file=sys.stderr, flush=True)
        last=now; first=False
        time.sleep(2)


def main() -> int:
    if os.geteuid() != 0:
        print('root required',file=sys.stderr); return 77
    if len(sys.argv) < 2:
        print('usage: fieldctl.py start SSID PASSWORD BAND | stop | watch USER',file=sys.stderr); return 2
    cmd=sys.argv[1]
    try:
        if cmd=='start':
            if len(sys.argv) != 5: raise RuntimeError('start benötigt SSID PASSWORT BAND')
            start(sys.argv[2],sys.argv[3],sys.argv[4]); return 0
        if cmd=='stop': stop(); return 0
        if cmd=='watch':
            if len(sys.argv)!=3: raise RuntimeError('watch benötigt USER')
            watch(sys.argv[2]); return 0
        raise RuntimeError('unbekannter Befehl')
    except Exception as exc:
        print(str(exc),file=sys.stderr); return 1

if __name__=='__main__':
    raise SystemExit(main())
