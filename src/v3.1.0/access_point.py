#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import secrets
import string
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

DRIVER = "mt7921u"
CONNECTION = "PPH-AccessPoint"
CONFIG_DIR = Path.home() / ".config" / "pph-ap"
CONFIG_FILE = CONFIG_DIR / "config.json"
TOKEN_FILE = CONFIG_DIR / "token"
DEFAULT = {"ssid": "PPH-WIFI", "band": "a", "api_port": 8788}


def _digits(length: int = 12) -> str:
    return "".join(secrets.choice(string.digits) for _ in range(length))


def _run(args: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Befehl fehlgeschlagen")
    return result


def _driver_of(interface: str) -> str:
    for path in (Path("/sys/class/net") / interface / "device/driver/module", Path("/sys/class/net") / interface / "device/driver"):
        try:
            return Path(os.path.realpath(path)).name
        except OSError:
            pass
    return ""


def find_brostrend() -> str | None:
    try:
        for item in Path("/sys/class/net").iterdir():
            if _driver_of(item.name) == DRIVER:
                return item.name
    except OSError:
        pass
    return None


def _counter(interface: str | None, name: str) -> int:
    if not interface:
        return 0
    try:
        return int((Path("/sys/class/net") / interface / "statistics" / name).read_text().strip())
    except (OSError, ValueError):
        return 0


def _lan_interface() -> str | None:
    result = _run(["ip", "route", "show", "default"])
    for line in result.stdout.splitlines():
        parts = line.split()
        if "dev" in parts:
            iface = parts[parts.index("dev") + 1]
            if iface.startswith(("eth", "en")):
                return iface
    try:
        for item in Path("/sys/class/net").iterdir():
            if item.name.startswith(("eth", "en")):
                return item.name
    except OSError:
        pass
    return None


def _carrier(interface: str | None) -> bool:
    if not interface:
        return False
    try:
        return (Path("/sys/class/net") / interface / "carrier").read_text().strip() == "1"
    except OSError:
        return False


def _clients(interface: str | None) -> int:
    if not interface:
        return 0
    result = _run(["iw", "dev", interface, "station", "dump"])
    if result.returncode:
        return 0
    return sum(1 for line in result.stdout.splitlines() if line.lstrip().startswith("Station "))


class AccessPointController:
    def __init__(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config()
        self.token = self._load_token()
        self.lock = threading.Lock()
        self._status: dict[str, Any] = {}
        self._previous: tuple[str | None, float, int, int] | None = None
        self._server: ThreadingHTTPServer | None = None
        threading.Thread(target=self._monitor_loop, daemon=True, name="pph-ap-monitor").start()
        self._start_api()

    def _load_config(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
        merged = dict(DEFAULT)
        merged.update(data)
        # First install gets a simple random 12-digit WLAN password.
        if not str(merged.get("password") or "").strip() or merged.get("password") == "ChangeMe123!":
            merged["password"] = _digits(12)
        self._save_config(merged)
        return merged

    def _save_config(self, config: dict[str, Any]) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        tmp = CONFIG_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(config, indent=2), encoding="utf-8")
        os.chmod(tmp, 0o600)
        tmp.replace(CONFIG_FILE)

    def _load_token(self) -> str:
        try:
            token = TOKEN_FILE.read_text(encoding="utf-8").strip()
            if token and token.isdigit() and len(token) == 12:
                return token
        except OSError:
            pass
        # Keep laptop pairing easy to type on the Pi: 12 numeric digits.
        token = _digits(12)
        TOKEN_FILE.write_text(token, encoding="utf-8")
        os.chmod(TOKEN_FILE, 0o600)
        return token

    def active(self) -> bool:
        result = _run(["nmcli", "-t", "-f", "NAME,TYPE,DEVICE", "connection", "show", "--active"])
        return any(line.startswith(CONNECTION + ":") for line in result.stdout.splitlines())

    def start(self) -> None:
        iface = find_brostrend()
        if not iface:
            raise RuntimeError("BrosTrend mt7921u wurde nicht gefunden.")
        config = dict(self.config)
        password = str(config.get("password") or "")
        ssid = str(config.get("ssid") or "PPH-WIFI").strip()
        if not ssid:
            raise RuntimeError("SSID darf nicht leer sein.")
        if len(password) < 8:
            raise RuntimeError("WLAN-Passwort muss mindestens 8 Zeichen haben.")
        _run(["nmcli", "connection", "delete", CONNECTION])
        _run(["nmcli", "connection", "add", "type", "wifi", "ifname", iface, "con-name", CONNECTION, "ssid", ssid], check=True)
        _run(["nmcli", "connection", "modify", CONNECTION, "802-11-wireless.mode", "ap", "802-11-wireless.band", str(config.get("band") or "a"), "wifi-sec.key-mgmt", "wpa-psk", "wifi-sec.psk", password, "ipv4.method", "shared", "ipv4.addresses", "10.42.0.1/24", "ipv6.method", "disabled", "connection.autoconnect", "yes"], check=True)
        _run(["nmcli", "connection", "up", CONNECTION], check=True)

    def stop(self) -> None:
        _run(["nmcli", "connection", "down", CONNECTION])

    def update_config(self, *, ssid: str | None = None, password: str | None = None, band: str | None = None) -> None:
        config = dict(self.config)
        if ssid is not None:
            ssid = ssid.strip()
            if not ssid:
                raise RuntimeError("SSID darf nicht leer sein.")
            config["ssid"] = ssid
        if password:
            if len(password) < 8:
                raise RuntimeError("Passwort muss mindestens 8 Zeichen haben.")
            config["password"] = password
        if band is not None:
            if band not in {"a", "bg"}:
                raise RuntimeError("Ungültiges WLAN-Band.")
            config["band"] = band
        self.config = config
        self._save_config(config)
        if self.active():
            self.start()

    def status(self) -> dict[str, Any]:
        with self.lock:
            return dict(self._status)

    def _monitor_loop(self) -> None:
        while True:
            iface = find_brostrend(); lan = _lan_interface(); now = time.monotonic()
            rx = _counter(iface, "rx_bytes"); tx = _counter(iface, "tx_bytes"); rx_mbps = tx_mbps = 0.0
            if self._previous and self._previous[0] == iface:
                dt = max(now - self._previous[1], 0.2)
                rx_mbps = max(0.0, (rx - self._previous[2]) * 8 / dt / 1_000_000)
                tx_mbps = max(0.0, (tx - self._previous[3]) * 8 / dt / 1_000_000)
            self._previous = (iface, now, rx, tx); active = self.active()
            status = {"active": active, "wifi_iface": iface, "driver": DRIVER, "lan_iface": lan, "lan_connected": _carrier(lan), "clients": _clients(iface) if active else 0, "rx_mbps": round(rx_mbps, 2), "tx_mbps": round(tx_mbps, 2), "total_mbps": round(rx_mbps + tx_mbps, 2), "ssid": str(self.config.get("ssid") or "PPH-WIFI"), "band": "5 GHz" if self.config.get("band") == "a" else "2.4 GHz"}
            with self.lock: self._status = status
            time.sleep(1.0)

    def _start_api(self) -> None:
        controller = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args: Any) -> None: return
            def send_json(self, code: int, payload: dict[str, Any]) -> None:
                body=json.dumps(payload).encode("utf-8"); self.send_response(code); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
            def authorized(self) -> bool: return self.headers.get("X-PPH-Token", "") == controller.token
            def body(self) -> dict[str, Any]:
                try:
                    length=int(self.headers.get("Content-Length","0")); return json.loads(self.rfile.read(length) or b"{}")
                except Exception: return {}
            def do_GET(self) -> None:
                if self.path == "/health": return self.send_json(200,{"ok":True})
                if not self.authorized(): return self.send_json(401,{"error":"unauthorized"})
                if self.path == "/status": return self.send_json(200,controller.status())
                if self.path == "/config": return self.send_json(200,{"ssid":controller.config.get("ssid"),"band":controller.config.get("band"),"password_set":bool(controller.config.get("password"))})
                self.send_json(404,{"error":"not found"})
            def do_POST(self) -> None:
                if not self.authorized(): return self.send_json(401,{"error":"unauthorized"})
                try:
                    if self.path == "/start": controller.start(); return self.send_json(200,{"ok":True})
                    if self.path == "/stop": controller.stop(); return self.send_json(200,{"ok":True})
                    if self.path == "/config":
                        data=self.body(); controller.update_config(ssid=data.get("ssid"),password=data.get("password"),band=data.get("band")); return self.send_json(200,{"ok":True})
                except Exception as exc: return self.send_json(500,{"error":str(exc)})
                self.send_json(404,{"error":"not found"})
        try:
            self._server=ThreadingHTTPServer(("0.0.0.0",int(self.config.get("api_port") or 8788)),Handler); threading.Thread(target=self._server.serve_forever,daemon=True,name="pph-ap-api").start()
        except OSError: self._server=None


def bars_for_speed(value: float) -> int:
    if value < 0.1: return 0
    if value < 5: return 1
    if value < 25: return 2
    if value < 75: return 3
    return 4
