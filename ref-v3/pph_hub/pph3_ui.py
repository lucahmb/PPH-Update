#!/usr/bin/env python3
from __future__ import annotations

import tkinter as tk
from typing import Any, Callable


def install(cls: type, ns: dict[str, Any]) -> None:
    """Install the PPH 3.0 shell on top of the proven 2.9 backend/UI methods."""
    BG = ns["BG"]
    SURFACE = ns["SURFACE"]
    SURFACE2 = ns["SURFACE2"]
    SURFACE3 = ns["SURFACE3"]
    BORDER = ns["BORDER"]
    TEXT = ns["TEXT"]
    MUTED = ns["MUTED"]
    CYAN = ns["CYAN"]
    GREEN = ns["GREEN"]
    YELLOW = ns["YELLOW"]
    RED = ns["RED"]
    BLUE = ns["BLUE"]
    PURPLE = ns["PURPLE"]
    ORANGE = ns["ORANGE"]

    events = ns["_pph28_events"]
    health = ns["_pph28_health"]
    jobs = ns["_pph28_jobs"]
    services = ns["_pph28_services"]
    updates = ns["_pph28_updates"]
    messagebox = ns["messagebox"]
    threading = ns["_pph28_threading"]
    from hardware_roles import adapter_overview

    import pph_snapshot
    import pph_version

    original_build_pages = cls._build_pages
    original_show_page = cls.show_page
    original_go_home = cls.go_home

    def nav_button(self, parent: tk.Misc, label: str, target: str) -> tk.Button:
        button = tk.Button(
            parent,
            text=label,
            command=lambda page=target: self.show_page(page),
            bg=SURFACE2,
            fg=TEXT,
            activebackground=CYAN,
            activeforeground=BG,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=BORDER,
            font=self._font(8, "bold"),
            padx=4,
            pady=7,
            cursor="hand2",
        )
        return button

    def info_card(
        self,
        parent: tk.Misc,
        title: str,
        value_var: tk.StringVar,
        detail_var: tk.StringVar,
        accent: str,
    ) -> tk.Frame:
        card = tk.Frame(parent, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
        tk.Frame(card, bg=accent, height=4).pack(fill="x")
        body = tk.Frame(card, bg=SURFACE)
        body.pack(fill="both", expand=True, padx=10, pady=7)
        tk.Label(body, text=title, bg=SURFACE, fg=MUTED, font=self._font(8, "bold"), anchor="w").pack(fill="x")
        tk.Label(body, textvariable=value_var, bg=SURFACE, fg=accent, font=self._font(17, "bold"), anchor="w").pack(fill="x", pady=(2, 0))
        tk.Label(body, textvariable=detail_var, bg=SURFACE, fg=TEXT, font=self._font(8), anchor="w", justify="left", wraplength=165).pack(fill="x", pady=(2, 0))
        return card

    def build_shell(self) -> None:
        self.root.configure(bg=BG)

        header = tk.Frame(self.root, bg=SURFACE, height=62)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)

        brand = tk.Frame(header, bg=SURFACE)
        brand.pack(side="left", padx=(10, 6), pady=8)
        tk.Label(brand, text="PPH", bg=CYAN, fg=BG, font=self._font(13, "bold"), padx=10, pady=6).pack(side="left")
        brand_text = tk.Frame(brand, bg=SURFACE)
        brand_text.pack(side="left", padx=(7, 0))
        tk.Label(brand_text, text="3.0", bg=SURFACE, fg=TEXT, font=self._font(15, "bold")).pack(anchor="w")
        tk.Label(brand_text, text="CONTROL CENTER", bg=SURFACE, fg=MUTED, font=self._font(7, "bold")).pack(anchor="w")

        self.back_button = tk.Button(
            header,
            text="←",
            command=self.go_back,
            bg=SURFACE2,
            fg=TEXT,
            activebackground=CYAN,
            activeforeground=BG,
            disabledforeground="#485a6d",
            relief="flat",
            bd=0,
            font=self._font(14, "bold"),
            width=3,
            pady=3,
            cursor="hand2",
        )
        self.back_button.pack(side="left", padx=(4, 7), pady=9)

        title = tk.Frame(header, bg=SURFACE)
        title.pack(side="left", fill="y", pady=8)
        tk.Label(title, textvariable=self.page_title, bg=SURFACE, fg=TEXT, font=self._font(13, "bold")).pack(anchor="w")
        tk.Label(title, textvariable=self.footer_var, bg=SURFACE, fg=MUTED, font=self._font(7)).pack(anchor="w", pady=(2, 0))

        controls = tk.Frame(header, bg=SURFACE)
        controls.pack(side="right", padx=(0, 8), pady=7)

        self.pph_update_badge_var = tk.StringVar(value="")
        self.pph_update_badge = tk.Button(
            controls,
            textvariable=self.pph_update_badge_var,
            command=lambda: self._pph28_open_update(),
            bg=YELLOW,
            fg=BG,
            activebackground=CYAN,
            activeforeground=BG,
            relief="flat",
            bd=0,
            font=self._font(8, "bold"),
            padx=6,
            pady=5,
            cursor="hand2",
        )

        self.pph_check_updates_button = tk.Button(
            controls,
            text="CHECK UPDATES",
            command=lambda: self._pph28_open_update(),
            bg=PURPLE,
            fg=TEXT,
            activebackground=CYAN,
            activeforeground=BG,
            relief="flat",
            bd=0,
            font=self._font(8, "bold"),
            padx=8,
            pady=6,
            cursor="hand2",
        )
        self.pph_check_updates_button.pack(side="left", padx=3)

        self.clock_var.set("--:--")
        tk.Label(controls, textvariable=self.clock_var, bg=SURFACE, fg=CYAN, font=self._font(9, "bold")).pack(side="left", padx=5)
        self.settings_button = self._header_button(controls, "⚙", lambda: self.show_page("settings3"))
        self.home_button = self._header_button(controls, "⌂", self.go_home)
        self.fullscreen_button = self._header_button(controls, "⛶", self.toggle_fullscreen)
        self.close_button = self._header_button(controls, "×", self.request_close)
        self.minimize_button = None
        self.window_button = None

        self.content = tk.Frame(self.root, bg=BG)
        self.content.pack(fill="both", expand=True)

        nav = tk.Frame(self.root, bg=SURFACE, height=50)
        nav.pack(side="bottom", fill="x")
        nav.pack_propagate(False)
        self.pph30_nav_buttons: dict[str, tk.Button] = {}
        items = [
            ("HOME", "home3"),
            ("MEASURE", "measure3"),
            ("WIFI", "wifi3"),
            ("SYSTEM", "system3"),
            ("JOBS", "jobs3"),
            ("EVENTS", "events3"),
            ("SETTINGS", "settings3"),
        ]
        for column, (label, target) in enumerate(items):
            nav.grid_columnconfigure(column, weight=1, uniform="pph30nav")
            button = nav_button(self, nav, label, target)
            button.grid(row=0, column=column, sticky="nsew", padx=3, pady=6)
            self.pph30_nav_buttons[target] = button

    def build_home(self) -> None:
        page = self._new_page("home3", "HOME")
        top = tk.Frame(page, bg=BG)
        top.pack(fill="x", padx=12, pady=(8, 4))
        tk.Label(top, text="PPH Control Center", bg=BG, fg=TEXT, font=self._font(16, "bold")).pack(side="left")
        tk.Label(top, text=f"v{pph_version.VERSION}", bg=SURFACE2, fg=CYAN, font=self._font(8, "bold"), padx=8, pady=4).pack(side="right")

        self.pph30_home = {
            key: tk.StringVar(value="—")
            for key in (
                "health_v", "health_d", "measure_v", "measure_d",
                "wifi_v", "wifi_d", "jobs_v", "jobs_d",
            )
        }
        self.pph30_home_event = tk.StringVar(value="Noch keine Events")
        self.pph30_home_update = tk.StringVar(value="Update-Status wird geladen …")

        cards = tk.Frame(page, bg=BG)
        cards.pack(fill="x", padx=8, pady=(0, 4))
        for col in range(4):
            cards.grid_columnconfigure(col, weight=1, uniform="homecards")
        defs = [
            ("HEALTH", "health_v", "health_d", GREEN),
            ("MEASUREMENT", "measure_v", "measure_d", CYAN),
            ("WIFI", "wifi_v", "wifi_d", ORANGE),
            ("JOBS", "jobs_v", "jobs_d", PURPLE),
        ]
        for index, (title_text, value, detail, accent) in enumerate(defs):
            info_card(self, cards, title_text, self.pph30_home[value], self.pph30_home[detail], accent).grid(row=0, column=index, sticky="nsew", padx=3, pady=3)

        strip = tk.Frame(page, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
        strip.pack(fill="x", padx=11, pady=4)
        tk.Label(strip, text="UPDATE", bg=SURFACE2, fg=PURPLE, font=self._font(7, "bold"), padx=7, pady=5).pack(side="left")
        tk.Label(strip, textvariable=self.pph30_home_update, bg=SURFACE, fg=TEXT, font=self._font(8), anchor="w").pack(side="left", fill="x", expand=True, padx=8)
        tk.Label(strip, text="EVENT", bg=SURFACE2, fg=BLUE, font=self._font(7, "bold"), padx=7, pady=5).pack(side="left")
        tk.Label(strip, textvariable=self.pph30_home_event, bg=SURFACE, fg=MUTED, font=self._font(8), anchor="w", width=34).pack(side="left", padx=8)

        actions = tk.Frame(page, bg=BG)
        actions.pack(fill="both", expand=True, padx=8, pady=(1, 8))
        for col in range(3):
            actions.grid_columnconfigure(col, weight=1, uniform="homeactions")
        for row in range(2):
            actions.grid_rowconfigure(row, weight=1, uniform="homeactions")
        defs = [
            ("START ANALYZER", self.launch_funktest, CYAN),
            ("WIFI OVERVIEW", lambda: self.show_page("wifi3"), SURFACE2),
            ("CHECK UPDATES", self._pph28_open_update, PURPLE),
            ("SERVICE CENTER", lambda: self.show_page("services"), SURFACE2),
            ("DIAGNOSTIC SNAPSHOT", self.pph30_create_snapshot, SURFACE2),
            ("EVENT CENTER", lambda: self.show_page("events3"), SURFACE2),
        ]
        for index, (label, command, accent) in enumerate(defs):
            self._button(actions, label, command, bg=accent, active=CYAN, size=9, pady=7).grid(row=index // 3, column=index % 3, sticky="nsew", padx=4, pady=4)

    def build_measure(self) -> None:
        page = self._new_page("measure3", "MEASURE")
        self.pph30_measure = {key: tk.StringVar(value="—") for key in ("status", "phase", "progress", "speed", "latency", "detail")}
        top = tk.Frame(page, bg=BG)
        top.pack(fill="x", padx=10, pady=(8, 4))
        for col in range(4):
            top.grid_columnconfigure(col, weight=1, uniform="measure")
        defs = [
            ("STATUS", "status", "phase", CYAN),
            ("PROGRESS", "progress", "detail", GREEN),
            ("THROUGHPUT", "speed", "detail", PURPLE),
            ("LATENCY", "latency", "detail", YELLOW),
        ]
        for index, (title_text, value, detail, accent) in enumerate(defs):
            info_card(self, top, title_text, self.pph30_measure[value], self.pph30_measure[detail], accent).grid(row=0, column=index, sticky="nsew", padx=3, pady=3)
        actions = tk.Frame(page, bg=BG)
        actions.pack(fill="x", padx=10, pady=4)
        for col in range(4):
            actions.grid_columnconfigure(col, weight=1, uniform="measureactions")
        defs = [
            ("OPEN ANALYZER", self.launch_funktest, CYAN),
            ("JOBS", lambda: self.show_page("jobs3"), SURFACE2),
            ("REPORTS", lambda: original_show_page(self, "reports"), SURFACE2),
            ("SNAPSHOT", self.pph30_create_snapshot, SURFACE2),
        ]
        for index, (label, command, accent) in enumerate(defs):
            self._button(actions, label, command, bg=accent, active=CYAN, size=9, pady=7).grid(row=0, column=index, sticky="ew", padx=3)
        self.pph30_measure_text = tk.Text(page, bg=SURFACE, fg=TEXT, relief="flat", bd=0, highlightthickness=1, highlightbackground=BORDER, font=self._font(9), wrap="word", padx=10, pady=8)
        self.pph30_measure_text.pack(fill="both", expand=True, padx=13, pady=(4, 9))
        self.pph30_measure_text.configure(state="disabled")

    def build_wifi(self) -> None:
        page = self._new_page("wifi3", "WIFI")
        self.pph30_wifi_title = tk.StringVar(value="WLAN-Hardware wird geprüft …")
        self.pph30_wifi_detail = tk.StringVar(value="")
        head = tk.Frame(page, bg=BG)
        head.pack(fill="x", padx=13, pady=(8, 3))
        tk.Label(head, textvariable=self.pph30_wifi_title, bg=BG, fg=TEXT, font=self._font(14, "bold")).pack(anchor="w")
        tk.Label(head, textvariable=self.pph30_wifi_detail, bg=BG, fg=MUTED, font=self._font(8), justify="left", wraplength=760).pack(anchor="w", pady=(2, 0))
        actions = tk.Frame(page, bg=BG)
        actions.pack(fill="x", padx=9, pady=3)
        defs = [
            ("NETWORK DOCTOR", self.open_network_doctor, CYAN),
            ("LAN MAPPER", self.open_lan_mapper, SURFACE2),
            ("DIAGNOSE", lambda: original_show_page(self, "tools"), SURFACE2),
            ("DFS", self._pph28_show_dfs, SURFACE2),
        ]
        for col, (label, command, accent) in enumerate(defs):
            actions.grid_columnconfigure(col, weight=1, uniform="wifiactions")
            self._button(actions, label, command, bg=accent, active=CYAN, size=8, pady=6).grid(row=0, column=col, sticky="ew", padx=3)
        self.pph30_wifi_rows = tk.Frame(page, bg=BG)
        self.pph30_wifi_rows.pack(fill="both", expand=True, padx=13, pady=(3, 9))

    def build_system(self) -> None:
        page = self._new_page("system3", "SYSTEM")
        self.pph30_system = {key: tk.StringVar(value="—") for key in ("health", "health_d", "temp", "temp_d", "disk", "disk_d", "services", "services_d")}
        cards = tk.Frame(page, bg=BG)
        cards.pack(fill="x", padx=9, pady=(8, 4))
        for col in range(4):
            cards.grid_columnconfigure(col, weight=1, uniform="system")
        defs = [
            ("HEALTH", "health", "health_d", GREEN),
            ("CPU / RAM", "temp", "temp_d", YELLOW),
            ("STORAGE", "disk", "disk_d", PURPLE),
            ("SERVICES", "services", "services_d", CYAN),
        ]
        for index, (title_text, value, detail, accent) in enumerate(defs):
            info_card(self, cards, title_text, self.pph30_system[value], self.pph30_system[detail], accent).grid(row=0, column=index, sticky="nsew", padx=3, pady=3)
        actions = tk.Frame(page, bg=BG)
        actions.pack(fill="both", expand=True, padx=9, pady=(4, 9))
        defs = [
            ("HEALTH DETAILS", self._pph28_show_health, CYAN),
            ("SERVICE CENTER", lambda: self.show_page("services"), SURFACE2),
            ("STORAGE", lambda: original_show_page(self, "storage"), SURFACE2),
            ("HARDWARE", lambda: original_show_page(self, "hardware"), SURFACE2),
            ("SNAPSHOT", self.pph30_create_snapshot, SURFACE2),
            ("REBOOT PI", lambda: self.confirm_control("reboot", "Pi wirklich neu starten?"), SURFACE2),
        ]
        for col in range(3):
            actions.grid_columnconfigure(col, weight=1, uniform="systemactions")
        for row in range(2):
            actions.grid_rowconfigure(row, weight=1, uniform="systemactions")
        for index, (label, command, accent) in enumerate(defs):
            self._button(actions, label, command, bg=accent, active=CYAN, size=9, pady=7).grid(row=index // 3, column=index % 3, sticky="nsew", padx=4, pady=4)

    def build_jobs(self) -> None:
        page = self._new_page("jobs3", "JOBS")
        self.pph30_jobs_header = tk.StringVar(value="Job Engine wird geladen …")
        tk.Label(page, textvariable=self.pph30_jobs_header, bg=BG, fg=CYAN, font=self._font(11, "bold")).pack(anchor="w", padx=13, pady=(8, 3))
        actions = tk.Frame(page, bg=BG)
        actions.pack(fill="x", padx=10, pady=2)
        self._button(actions, "REFRESH", self.pph30_refresh_jobs, bg=CYAN, active=CYAN, size=8, pady=5).pack(side="left", padx=3)
        self._button(actions, "SNAPSHOT", self.pph30_create_snapshot, size=8, pady=5).pack(side="left", padx=3)
        self._button(actions, "EVENTS", lambda: self.show_page("events3"), size=8, pady=5).pack(side="left", padx=3)
        self.pph30_jobs_rows = tk.Frame(page, bg=BG)
        self.pph30_jobs_rows.pack(fill="both", expand=True, padx=13, pady=(3, 9))

    def build_events(self) -> None:
        page = self._new_page("events3", "EVENTS")
        self.pph30_event_filter = "all"
        self.pph30_events_header = tk.StringVar(value="Event Center")
        tk.Label(page, textvariable=self.pph30_events_header, bg=BG, fg=TEXT, font=self._font(12, "bold")).pack(anchor="w", padx=13, pady=(8, 3))
        filters = tk.Frame(page, bg=BG)
        filters.pack(fill="x", padx=9, pady=2)
        defs = [("ALL", "all"), ("WARN", "warning"), ("ERROR", "error"), ("UPDATE", "update"), ("JOBS", "jobs")]
        for col, (label, mode) in enumerate(defs):
            filters.grid_columnconfigure(col, weight=1, uniform="events")
            self._button(filters, label, lambda value=mode: self.pph30_set_event_filter(value), bg=CYAN if col == 0 else SURFACE2, active=CYAN, size=8, pady=5).grid(row=0, column=col, sticky="ew", padx=3)
        self.pph30_events_rows = tk.Frame(page, bg=BG)
        self.pph30_events_rows.pack(fill="both", expand=True, padx=13, pady=(3, 9))

    def build_settings(self) -> None:
        page = self._new_page("settings3", "SETTINGS")
        self.pph30_settings_info = tk.StringVar(value=f"PPH {pph_version.VERSION} · {pph_version.CHANNEL}")
        card = tk.Frame(page, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="both", expand=True, padx=13, pady=9)
        tk.Label(card, text="PPH 3.0 SETTINGS", bg=SURFACE, fg=TEXT, font=self._font(13, "bold")).pack(anchor="w", padx=13, pady=(10, 2))
        tk.Label(card, textvariable=self.pph30_settings_info, bg=SURFACE, fg=CYAN, font=self._font(8)).pack(anchor="w", padx=13)
        tk.Label(card, text="DISPLAY TIMEOUT", bg=SURFACE, fg=MUTED, font=self._font(8, "bold")).pack(anchor="w", padx=13, pady=(10, 3))
        row = tk.Frame(card, bg=SURFACE)
        row.pack(fill="x", padx=9)
        for seconds, label in [(30, "30 S"), (60, "60 S"), (120, "2 MIN"), (300, "5 MIN"), (0, "NIE")]:
            self._button(row, label, lambda value=seconds: self.set_timeout(value), size=8, padx=3, pady=5).pack(side="left", fill="x", expand=True, padx=2)
        tk.Label(card, text="BRIGHTNESS", bg=SURFACE, fg=MUTED, font=self._font(8, "bold")).pack(anchor="w", padx=13, pady=(9, 3))
        row2 = tk.Frame(card, bg=SURFACE)
        row2.pack(fill="x", padx=9)
        for percent in (25, 50, 75, 100):
            self._button(row2, f"{percent}%", lambda value=percent: self.set_brightness(value), size=8, padx=3, pady=5).pack(side="left", fill="x", expand=True, padx=2)
        actions = tk.Frame(card, bg=SURFACE)
        actions.pack(side="bottom", fill="x", padx=9, pady=10)
        defs = [
            ("CHECK UPDATES", self._pph28_open_update, PURPLE),
            ("SERVICE CENTER", lambda: self.show_page("services"), SURFACE2),
            ("DISPLAY OFF", self.sleep_display, SURFACE2),
            ("WINDOW", self.window_mode, SURFACE2),
        ]
        for label, command, accent in defs:
            self._button(actions, label, command, bg=accent, active=CYAN, size=8, pady=5).pack(side="left", fill="x", expand=True, padx=2)

    def build_pages(self) -> None:
        # Keep all mature 2.9 pages in memory so existing refresh loops and tools
        # remain fully compatible. PPH 3.0 adds a new primary navigation layer.
        original_build_pages(self)
        build_home(self)
        build_measure(self)
        build_wifi(self)
        build_system(self)
        build_jobs(self)
        build_events(self)
        build_settings(self)

    def update_nav(self) -> None:
        active = self.current_page
        aliases = {
            "services": "system3",
            "storage": "system3",
            "hardware": "system3",
            "network_doctor": "wifi3",
            "lan_mapper": "wifi3",
            "tools": "wifi3",
            "reports": "measure3",
        }
        active = aliases.get(active, active)
        for target, button in getattr(self, "pph30_nav_buttons", {}).items():
            selected = target == active
            button.configure(bg=CYAN if selected else SURFACE2, fg=BG if selected else TEXT)
        can_back = bool(self.navigation_stack) and self.current_page != "home3"
        self.back_button.configure(state="normal" if can_back else "disabled")

    def show_page(self, name: str, title: str | None = None, *, push: bool = True) -> None:
        if name == "dashboard":
            name = "home3"
        if name not in self.frames:
            return
        if name != self.current_page and push and self.current_page in self.frames:
            if not self.navigation_stack or self.navigation_stack[-1] != self.current_page:
                self.navigation_stack.append(self.current_page)
        for frame in self.frames.values():
            frame.pack_forget()
        self.frames[name].pack(fill="both", expand=True)
        self.current_page = name
        self.page_title.set(title or self.page_titles.get(name, name.upper()))
        update_nav(self)

        if name == "home3":
            self.pph30_refresh_home()
        elif name == "measure3":
            self.pph30_refresh_measure()
        elif name == "wifi3":
            self.pph30_refresh_wifi()
        elif name == "system3":
            self.pph30_refresh_system()
        elif name == "jobs3":
            self.pph30_refresh_jobs()
        elif name == "events3":
            self.pph30_refresh_events()
        elif name == "settings3":
            self.pph30_refresh_settings()
        elif name == "storage":
            self.refresh_storage()
        elif name == "hardware":
            self.refresh_hardware()
        elif name == "reports":
            self.refresh_reports()
        elif name == "services":
            try:
                self._pph_sc_active_check()
            except Exception:
                pass
        elif name == "network":
            self.refresh_network_text()
        self._reset_idle_timer()
        try:
            self._pph29_trigger_update_check(False, f"page:{name}")
        except Exception:
            pass

    def go_home(self) -> None:
        self.navigation_stack.clear()
        self.show_page("home3", "HOME", push=False)

    def refresh_home(self) -> None:
        try:
            payload = health.collect_health(include_kernel=False)
            self.pph30_home["health_v"].set(f"{payload.get('score', '—')}/100")
            self.pph30_home["health_d"].set(str(payload.get("grade") or "—"))
        except Exception as exc:
            self.pph30_home["health_v"].set("—")
            self.pph30_home["health_d"].set(f"Health: {exc}")

        running = self._measurement_running() or self._funktest_running()
        state = self._read_measurement_state()
        self.pph30_home["measure_v"].set("ACTIVE" if running else "READY")
        self.pph30_home["measure_d"].set(str(state.get("phase") or state.get("subtitle") or "Analyzer bereit"))

        try:
            overview = adapter_overview()
            roles = overview.get("roles") or {}
            present = sum(1 for item in roles.values() if item)
            self.pph30_home["wifi_v"].set(f"{present}/3")
            self.pph30_home["wifi_d"].set(str(overview.get("active_source") or overview.get("title") or "WLAN"))
        except Exception as exc:
            self.pph30_home["wifi_v"].set("—")
            self.pph30_home["wifi_d"].set(str(exc))

        summary = jobs.summary()
        self.pph30_home["jobs_v"].set(str(summary.get("active_count") or 0))
        recent = summary.get("recent") or []
        self.pph30_home["jobs_d"].set(str(recent[0].get("title") if recent else "Keine aktiven Jobs"))

        recent_events = events.read_events(limit=1)
        if recent_events:
            item = recent_events[-1]
            self.pph30_home_event.set(str(item.get("message") or item.get("type") or "Event")[:48])
        else:
            self.pph30_home_event.set("Noch keine Events")
        try:
            cache = updates._read_remote_cache()
            manifest = cache.get("manifest") if isinstance(cache.get("manifest"), dict) else {}
            remote_version = str(manifest.get("version") or "—")
            self.pph30_home_update.set(f"Stable {remote_version} · installiert {updates.installed_version()}")
        except Exception:
            self.pph30_home_update.set(f"Installiert {updates.installed_version()}")

    def refresh_measure(self) -> None:
        state = self._read_measurement_state()
        running = self._measurement_running() or self._funktest_running()
        progress = int(float(state.get("progress") or 0)) if running else 0
        self.pph30_measure["status"].set("ACTIVE" if running else "READY")
        self.pph30_measure["phase"].set(str(state.get("phase") or state.get("subtitle") or "Keine Messung aktiv"))
        self.pph30_measure["progress"].set(f"{progress}%")
        dl = state.get("download_mbps")
        ul = state.get("upload_mbps")
        if isinstance(dl, (int, float)):
            self.pph30_measure["speed"].set(f"{float(dl):.1f} M")
        elif isinstance(ul, (int, float)):
            self.pph30_measure["speed"].set(f"{float(ul):.1f} M")
        else:
            self.pph30_measure["speed"].set("—")
        ping = state.get("latency_ms") or state.get("ping_ms")
        self.pph30_measure["latency"].set(f"{float(ping):.1f} ms" if isinstance(ping, (int, float)) else "—")
        self.pph30_measure["detail"].set(str(state.get("updated_at") or "Keine Live-Daten")[-8:])
        lines = [f"Status: {'Messung läuft' if running else 'Bereit'}"]
        for key, label in (("project", "Projekt"), ("room", "Raum"), ("phase", "Phase"), ("server", "Server"), ("updated_at", "Aktualisiert")):
            value = state.get(key)
            if value not in (None, ""):
                lines.append(f"{label}: {value}")
        if dl is not None or ul is not None:
            lines.append(f"Download: {dl if dl is not None else '—'} Mbps · Upload: {ul if ul is not None else '—'} Mbps")
        self.pph30_measure_text.configure(state="normal")
        self.pph30_measure_text.delete("1.0", "end")
        self.pph30_measure_text.insert("1.0", "\n".join(lines))
        self.pph30_measure_text.configure(state="disabled")

    def refresh_wifi(self) -> None:
        for child in self.pph30_wifi_rows.winfo_children():
            child.destroy()
        try:
            overview = adapter_overview()
        except Exception as exc:
            overview = {"title": "WLAN Fehler", "detail": str(exc), "roles": {}}
        self.pph30_wifi_title.set(str(overview.get("title") or "WLAN"))
        self.pph30_wifi_detail.set(str(overview.get("detail") or ""))
        roles = overview.get("roles") or {}
        defs = [
            ("measurement", "BROSTREND · MESSUNG", CYAN),
            ("scan", "ALFA AWUS · SCAN / ANALYSE", ORANGE),
            ("control", "PI WLAN · STEUERUNG", GREEN),
        ]
        for key, title_text, accent in defs:
            item = roles.get(key) or {}
            row = tk.Frame(self.pph30_wifi_rows, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
            row.pack(fill="x", pady=3)
            tk.Frame(row, bg=accent, width=6).pack(side="left", fill="y")
            body = tk.Frame(row, bg=SURFACE)
            body.pack(side="left", fill="both", expand=True, padx=10, pady=7)
            tk.Label(body, text=title_text, bg=SURFACE, fg=TEXT, font=self._font(9, "bold"), anchor="w").pack(fill="x")
            if item:
                primary = f"{item.get('interface') or '—'} · {item.get('driver') or '—'} · {item.get('model') or 'Adapter'}"
                secondary = f"{item.get('iftype') or 'managed'} · {item.get('operstate') or '—'}"
                if item.get("connected"):
                    secondary += f" · {item.get('ssid') or 'verbunden'}"
            else:
                primary = "Nicht erkannt"
                secondary = "Kein passender Adapter vorhanden"
            tk.Label(body, text=primary, bg=SURFACE, fg=accent, font=self._font(9, "bold"), anchor="w").pack(fill="x", pady=(2, 0))
            tk.Label(body, text=secondary, bg=SURFACE, fg=MUTED, font=self._font(8), anchor="w").pack(fill="x", pady=(2, 0))

    def refresh_system(self) -> None:
        try:
            payload = health.collect_health(include_kernel=True)
            self.pph30_system["health"].set(f"{payload.get('score', '—')}/100")
            self.pph30_system["health_d"].set(str(payload.get("grade") or "—"))
            temp = payload.get("temperature_c")
            self.pph30_system["temp"].set(f"{temp:.1f} °C" if isinstance(temp, (int, float)) else "—")
            self.pph30_system["temp_d"].set(f"RAM {payload.get('memory_percent', '—')} %")
            root = payload.get("root_disk") or {}
            self.pph30_system["disk"].set(f"{root.get('percent', '—')} %")
            findings = payload.get("findings") or []
            self.pph30_system["disk_d"].set(f"{len(findings)} Findings")
        except Exception as exc:
            self.pph30_system["health"].set("—")
            self.pph30_system["health_d"].set(str(exc))
            self.pph30_system["temp"].set("—")
            self.pph30_system["temp_d"].set("—")
            self.pph30_system["disk"].set("—")
            self.pph30_system["disk_d"].set("—")
        service_summary = services.summary()
        self.pph30_system["services"].set(f"{service_summary.get('active', 0)}/{service_summary.get('total', 0)}")
        self.pph30_system["services_d"].set("PPH Services aktiv")

    def render_jobs(self, rows: list[dict[str, Any]]) -> None:
        for child in self.pph30_jobs_rows.winfo_children():
            child.destroy()
        if not rows:
            tk.Label(self.pph30_jobs_rows, text="Keine Jobs vorhanden.", bg=BG, fg=MUTED, font=self._font(10)).pack(pady=20)
            return
        for item in rows[:8]:
            status = str(item.get("status") or "unknown")
            accent = GREEN if status == "completed" else CYAN if status == "running" else YELLOW if status in {"queued", "cancelling"} else RED if status == "failed" else MUTED
            row = tk.Frame(self.pph30_jobs_rows, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
            row.pack(fill="x", pady=2)
            body = tk.Frame(row, bg=SURFACE)
            body.pack(side="left", fill="both", expand=True, padx=9, pady=6)
            tk.Label(body, text=str(item.get("title") or "PPH Job"), bg=SURFACE, fg=TEXT, font=self._font(9, "bold"), anchor="w").pack(fill="x")
            tk.Label(body, text=str(item.get("message") or ""), bg=SURFACE, fg=MUTED, font=self._font(8), anchor="w").pack(fill="x")
            tk.Label(row, text=f"{status.upper()} · {int(item.get('progress') or 0)}%", bg=SURFACE2, fg=accent, font=self._font(8, "bold"), padx=8, pady=7).pack(side="right", padx=7)

    def refresh_jobs(self) -> None:
        rows = jobs.list_jobs(limit=12)
        active = sum(1 for item in rows if str(item.get("status")) in {"queued", "running", "cancelling"})
        self.pph30_jobs_header.set(f"{active} aktive Jobs · {len(rows)} zuletzt gespeichert")
        render_jobs(self, rows)

    def set_event_filter(self, mode: str) -> None:
        self.pph30_event_filter = mode
        self.pph30_refresh_events()

    def refresh_events(self) -> None:
        for child in self.pph30_events_rows.winfo_children():
            child.destroy()
        rows = events.read_events(limit=50)
        mode = getattr(self, "pph30_event_filter", "all")
        if mode == "warning":
            rows = [item for item in rows if str(item.get("severity")) == "warning"]
        elif mode == "error":
            rows = [item for item in rows if str(item.get("severity")) in {"error", "critical"}]
        elif mode == "update":
            rows = [item for item in rows if str(item.get("category")) == "update"]
        elif mode == "jobs":
            rows = [item for item in rows if str(item.get("category")) == "jobs"]
        self.pph30_events_header.set(f"Event Center · {mode.upper()} · {len(rows)} Treffer")
        if not rows:
            tk.Label(self.pph30_events_rows, text="Keine Events im aktuellen Filter.", bg=BG, fg=MUTED, font=self._font(10)).pack(pady=20)
            return
        for item in rows[-10:][::-1]:
            severity = str(item.get("severity") or "info")
            accent = RED if severity in {"error", "critical"} else YELLOW if severity == "warning" else PURPLE if str(item.get("category")) == "update" else CYAN
            row = tk.Frame(self.pph30_events_rows, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=severity.upper(), bg=SURFACE2, fg=accent, font=self._font(7, "bold"), width=9, padx=5, pady=6).pack(side="left")
            body = tk.Frame(row, bg=SURFACE)
            body.pack(side="left", fill="both", expand=True, padx=8, pady=5)
            tk.Label(body, text=str(item.get("message") or item.get("type") or "Event"), bg=SURFACE, fg=TEXT, font=self._font(8, "bold"), anchor="w").pack(fill="x")
            meta = f"{item.get('category') or 'system'} · {str(item.get('timestamp') or '')[-8:]}"
            tk.Label(body, text=meta, bg=SURFACE, fg=MUTED, font=self._font(7), anchor="w").pack(fill="x")

    def refresh_settings(self) -> None:
        try:
            cache = updates._read_remote_cache()
            checked = str(cache.get("checked_at") or "noch nie")
            manifest = cache.get("manifest") if isinstance(cache.get("manifest"), dict) else {}
            remote = str(manifest.get("version") or "—")
        except Exception:
            checked, remote = "—", "—"
        self.pph30_settings_info.set(
            f"PPH {pph_version.VERSION} · {pph_version.BUILD_NAME}\n"
            f"Channel {pph_version.CHANNEL} · Remote Stable {remote} · Last Check {checked}"
        )

    def create_snapshot(self) -> None:
        self.footer_var.set("Diagnostic Snapshot wird erstellt …")

        def worker() -> None:
            try:
                path = pph_snapshot.create_snapshot()
                error = None
            except Exception as exc:
                path, error = None, exc

            def apply() -> None:
                if error:
                    self.footer_var.set(f"Snapshot fehlgeschlagen: {error}")
                    messagebox.showwarning("PPH Snapshot", str(error), parent=self.root)
                else:
                    self.footer_var.set("Snapshot erstellt")
                    messagebox.showinfo("PPH Snapshot", f"Gespeichert:\n{path}", parent=self.root)
                    if self.current_page == "jobs3":
                        self.pph30_refresh_jobs()
            try:
                self.root.after(0, apply)
            except tk.TclError:
                pass

        threading.Thread(target=worker, daemon=True).start()

    cls._build_shell = build_shell
    cls._build_pages = build_pages
    cls.show_page = show_page
    cls.go_home = go_home
    cls.pph30_refresh_home = refresh_home
    cls.pph30_refresh_measure = refresh_measure
    cls.pph30_refresh_wifi = refresh_wifi
    cls.pph30_refresh_system = refresh_system
    cls.pph30_refresh_jobs = refresh_jobs
    cls.pph30_render_jobs = render_jobs
    cls.pph30_set_event_filter = set_event_filter
    cls.pph30_refresh_events = refresh_events
    cls.pph30_refresh_settings = refresh_settings
    cls.pph30_create_snapshot = create_snapshot
    cls._pph30_original_show_page = original_show_page
    cls._pph30_original_go_home = original_go_home
