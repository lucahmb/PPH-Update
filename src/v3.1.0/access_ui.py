#!/usr/bin/env python3
from __future__ import annotations

import tkinter as tk
from typing import Any

from access_point import AccessPointController, bars_for_speed


def install_access(cls: type, ns: dict[str, Any]) -> None:
    BG = ns["BG"]
    SURFACE = ns["SURFACE"]
    SURFACE2 = ns["SURFACE2"]
    SURFACE3 = ns["SURFACE3"]
    BORDER = ns["BORDER"]
    TEXT = ns["TEXT"]
    MUTED = ns["MUTED"]
    CYAN = ns["CYAN"]
    GREEN = ns["GREEN"]
    RED = ns["RED"]
    PURPLE = ns["PURPLE"]
    ORANGE = ns["ORANGE"]
    messagebox = ns["messagebox"]

    def build_access(self) -> None:
        page = self._new_page("access3", "ACCESS POINT")
        if not hasattr(self, "pph31_ap"):
            self.pph31_ap = AccessPointController()
        self.pph31_ap_vars = {key: tk.StringVar(value="—") for key in ("status", "speed", "clients", "detail")}

        cards = tk.Frame(page, bg=BG)
        cards.pack(fill="x", padx=10, pady=(8, 4))
        for col in range(2):
            cards.grid_columnconfigure(col, weight=1, uniform="accesscards")

        speed_card = tk.Frame(cards, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
        speed_card.grid(row=0, column=0, sticky="nsew", padx=3)
        tk.Frame(speed_card, bg=ORANGE, height=4).pack(fill="x")
        body = tk.Frame(speed_card, bg=SURFACE)
        body.pack(fill="both", expand=True, padx=12, pady=7)
        tk.Label(body, text="AKTUELLE GESCHWINDIGKEIT", bg=SURFACE, fg=MUTED, font=self._font(8, "bold"), anchor="w").pack(fill="x")
        tk.Label(body, textvariable=self.pph31_ap_vars["speed"], bg=SURFACE, fg=ORANGE, font=self._font(19, "bold"), anchor="w").pack(side="left", fill="x", expand=True)
        self.pph31_ap_canvas = tk.Canvas(body, width=145, height=62, bg=SURFACE, highlightthickness=0)
        self.pph31_ap_canvas.pack(side="right", padx=(8, 0))

        client_card = tk.Frame(cards, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
        client_card.grid(row=0, column=1, sticky="nsew", padx=3)
        tk.Frame(client_card, bg=CYAN, height=4).pack(fill="x")
        body2 = tk.Frame(client_card, bg=SURFACE)
        body2.pack(fill="both", expand=True, padx=12, pady=7)
        tk.Label(body2, text="VERBUNDENE GERÄTE", bg=SURFACE, fg=MUTED, font=self._font(8, "bold"), anchor="w").pack(fill="x")
        tk.Label(body2, textvariable=self.pph31_ap_vars["clients"], bg=SURFACE, fg=CYAN, font=self._font(22, "bold"), anchor="w").pack(anchor="w")
        tk.Label(body2, textvariable=self.pph31_ap_vars["status"], bg=SURFACE, fg=TEXT, font=self._font(8, "bold"), anchor="w").pack(fill="x")

        config = tk.Frame(page, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
        config.pack(fill="x", padx=13, pady=4)
        row = tk.Frame(config, bg=SURFACE)
        row.pack(fill="x", padx=9, pady=7)
        tk.Label(row, text="SSID", bg=SURFACE, fg=MUTED, font=self._font(8, "bold")).grid(row=0, column=0, sticky="w")
        tk.Label(row, text="NEUES PASSWORT", bg=SURFACE, fg=MUTED, font=self._font(8, "bold")).grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.pph31_ap_ssid = tk.Entry(row, bg=SURFACE2, fg=TEXT, insertbackground=TEXT, relief="flat", font=self._font(10))
        self.pph31_ap_password = tk.Entry(row, bg=SURFACE2, fg=TEXT, insertbackground=TEXT, relief="flat", show="•", font=self._font(10))
        self.pph31_ap_ssid.grid(row=1, column=0, sticky="ew", ipady=6)
        self.pph31_ap_password.grid(row=1, column=1, sticky="ew", padx=(8, 0), ipady=6)
        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=1)
        self.pph31_ap_ssid.insert(0, str(self.pph31_ap.config.get("ssid") or "PPH-WIFI"))

        self.pph31_ap_band = tk.StringVar(value=str(self.pph31_ap.config.get("band") or "a"))
        bandrow = tk.Frame(config, bg=SURFACE)
        bandrow.pack(fill="x", padx=9, pady=(0, 7))
        for label, value in (("5 GHz", "a"), ("2.4 GHz", "bg")):
            tk.Radiobutton(bandrow, text=label, value=value, variable=self.pph31_ap_band, indicatoron=False, bg=SURFACE2, fg=TEXT, selectcolor=CYAN, activebackground=CYAN, relief="flat", font=self._font(8, "bold"), padx=10, pady=5).pack(side="left", padx=(0, 5))
        self._button(bandrow, "SPEICHERN", self.pph31_save_access, bg=PURPLE, active=CYAN, size=8, pady=5).pack(side="right")

        actions = tk.Frame(page, bg=BG)
        actions.pack(fill="x", padx=10, pady=3)
        for col in range(4):
            actions.grid_columnconfigure(col, weight=1, uniform="accessactions")
        for col, (label, command, accent) in enumerate((
            ("STARTEN", self.pph31_start_access, GREEN),
            ("STOPPEN", self.pph31_stop_access, RED),
            ("TOKEN", self.pph31_show_token, SURFACE2),
            ("WIFI", lambda: self.show_page("wifi3"), SURFACE2),
        )):
            self._button(actions, label, command, bg=accent, active=CYAN, size=8, pady=6).grid(row=0, column=col, sticky="ew", padx=3)
        tk.Label(page, textvariable=self.pph31_ap_vars["detail"], bg=BG, fg=MUTED, font=self._font(8), anchor="w").pack(fill="x", padx=14, pady=(2, 0))

    def draw_bars(self, count: int) -> None:
        canvas = self.pph31_ap_canvas
        canvas.delete("all")
        for index, height in enumerate((14, 27, 41, 56)):
            x = 10 + index * 31
            y = 59 - height
            fill = ORANGE if index < count else SURFACE3
            canvas.create_rectangle(x, y, x + 20, 59, fill=fill, outline=fill)

    def refresh_access(self) -> None:
        status = self.pph31_ap.status()
        speed = float(status.get("total_mbps") or 0.0)
        active = bool(status.get("active"))
        self.pph31_ap_vars["status"].set(("● AKTIV" if active else "○ AUS") + f" · {status.get('ssid') or 'PPH-WIFI'} · {status.get('band') or '—'}")
        self.pph31_ap_vars["speed"].set(f"{speed:.1f} Mbit/s")
        self.pph31_ap_vars["clients"].set(str(status.get("clients") or 0))
        lan = "LAN verbunden" if status.get("lan_connected") else "LAN getrennt"
        self.pph31_ap_vars["detail"].set(f"{lan} · RX {float(status.get('rx_mbps') or 0):.1f} · TX {float(status.get('tx_mbps') or 0):.1f} Mbit/s · BrosTrend {status.get('wifi_iface') or 'nicht gefunden'}")
        draw_bars(self, bars_for_speed(speed))
        if self.current_page == "access3":
            try:
                self.root.after(1000, self.pph31_refresh_access)
            except tk.TclError:
                pass

    def start_access(self) -> None:
        try:
            self.pph31_ap.start()
            self.footer_var.set("Access Point gestartet")
            self.pph31_refresh_access()
        except Exception as exc:
            messagebox.showerror("PPH Access Point", str(exc), parent=self.root)

    def stop_access(self) -> None:
        try:
            self.pph31_ap.stop()
            self.footer_var.set("Access Point gestoppt")
            self.pph31_refresh_access()
        except Exception as exc:
            messagebox.showerror("PPH Access Point", str(exc), parent=self.root)

    def save_access(self) -> None:
        try:
            password = self.pph31_ap_password.get()
            self.pph31_ap.update_config(
                ssid=self.pph31_ap_ssid.get(),
                password=password if password else None,
                band=self.pph31_ap_band.get(),
            )
            self.pph31_ap_password.delete(0, "end")
            self.footer_var.set("Access-Point-Konfiguration gespeichert")
            self.pph31_refresh_access()
        except Exception as exc:
            messagebox.showerror("PPH Access Point", str(exc), parent=self.root)

    def show_token(self) -> None:
        messagebox.showinfo("PPH Laptop Token", f"Host: homelab.local:8788\n\nToken:\n{self.pph31_ap.token}", parent=self.root)

    cls.pph31_build_access = build_access
    cls.pph31_refresh_access = refresh_access
    cls.pph31_draw_access_bars = draw_bars
    cls.pph31_start_access = start_access
    cls.pph31_stop_access = stop_access
    cls.pph31_save_access = save_access
    cls.pph31_show_token = show_token
