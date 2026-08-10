#!/usr/bin/env python3
from __future__ import annotations
import subprocess, time, tkinter as tk
from typing import Any

# ---------------------------------------------------------------------------
# PPH 6.0 — one authoritative UI layer for the 800x480 5-inch touch display.
# Older UI modules (pph3_ui / pph32_ui / pph4_theme / pph41_ui / pph411_touch /
# pph412_paged / pph42_full_ui / pph50_platform / pph51_ui) still get installed
# by pph3_app.py for their backend side effects, but none of their _build_shell,
# _build_pages or show_page ever run: this module overrides all three last and
# never calls the previous versions. Backend hooks (measurement engine, funktest
# launcher, brightness/timeout, update checker, access point controller) remain
# in use exactly as before.
# ---------------------------------------------------------------------------

BG = '#03070C'; PANEL = '#0A111A'; PANEL2 = '#101B28'; BORDER = '#21354A'
TEXT = '#F4F8FB'; MUTED = '#7891A6'
CYAN = '#42DCFF'; GREEN = '#45E39A'; YELLOW = '#FFD166'; ORANGE = '#FF9F68'
RED = '#FF6475'; PURPLE = '#BD8CFF'; BLUE = '#6F8CFF'

CHIP = {
    'ready': (PANEL2, GREEN), 'live': (PANEL2, CYAN), 'offline': (PANEL2, MUTED),
    'warn': (PANEL2, YELLOW), 'error': (PANEL2, RED), 'active': (PANEL2, GREEN),
}

W, H = 800, 480
HEADER_H = 58
NAV_H = 76
ACTION_H = 62


def run(args: list[str], timeout: float = 3) -> str:
    try:
        p = subprocess.run(args, text=True, capture_output=True, timeout=timeout, check=False)
        return (p.stdout or p.stderr or '').strip()
    except Exception:
        return ''


def _adapter_overview() -> dict:
    try:
        from hardware_roles import adapter_overview
        return adapter_overview() or {}
    except Exception:
        return {}


def _current_version() -> str:
    try:
        import pph_version
        return str(pph_version.VERSION)
    except Exception:
        return '—'


def _first(*vals):
    for v in vals:
        if v is not None:
            return v
    return None


def _lerp_color(a: str, b: str, t: float) -> str:
    a = a.lstrip('#'); b = b.lstrip('#')
    ar, ag, ab = int(a[0:2], 16), int(a[2:4], 16), int(a[4:6], 16)
    br, bg, bb = int(b[0:2], 16), int(b[2:4], 16), int(b[4:6], 16)
    r = int(ar + (br - ar) * t); g = int(ag + (bg - ag) * t); c = int(ab + (bb - ab) * t)
    return f'#{max(0,min(255,r)):02x}{max(0,min(255,g)):02x}{max(0,min(255,c)):02x}'


# =========================================================================
# Animation manager — centralized, tag-based, cancellable per page.
# =========================================================================
class Anim:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.level = 'FULL'
        self._tok: dict[str, str] = {}

    def set_level(self, level: str) -> None:
        self.level = level if level in ('FULL', 'REDUCED', 'OFF') else 'FULL'

    def enabled(self, tier: str = 'FULL') -> bool:
        if tier == 'ESSENTIAL':
            return True
        if self.level == 'OFF':
            return False
        if self.level == 'REDUCED':
            return tier == 'REDUCED'
        return True

    def cancel(self, tag: str) -> None:
        tok = self._tok.pop(tag, None)
        if tok is not None:
            try: self.root.after_cancel(tok)
            except Exception: pass

    def cancel_page(self, page: str) -> None:
        prefix = page + ':'
        for tag in [t for t in list(self._tok) if t.startswith(prefix)]:
            self.cancel(tag)

    def after(self, tag: str, ms: int, fn) -> None:
        self.cancel(tag)
        def run_once():
            self._tok.pop(tag, None)
            try: fn()
            except Exception: pass
        self._tok[tag] = self.root.after(ms, run_once)

    def loop(self, tag: str, ms: int, fn) -> None:
        self.cancel(tag)
        def tick():
            if tag not in self._tok:
                return
            try: fn()
            except Exception: pass
            if tag in self._tok:
                self._tok[tag] = self.root.after(ms, tick)
        self._tok[tag] = self.root.after(ms, tick)

    def tween(self, tag: str, ms: int, on_frame, on_done=None, tier: str = 'FULL', fps: int = 30) -> None:
        if not self.enabled(tier):
            try: on_frame(1.0)
            except Exception: pass
            if on_done:
                try: on_done()
                except Exception: pass
            return
        self.cancel(tag)
        start = time.monotonic()
        step = max(16, int(1000 / fps))
        def tick():
            t = min(1.0, (time.monotonic() - start) * 1000 / max(1, ms))
            eased = 1 - (1 - t) * (1 - t)
            try: on_frame(eased)
            except Exception: pass
            if t >= 1.0:
                self._tok.pop(tag, None)
                if on_done:
                    try: on_done()
                    except Exception: pass
                return
            self._tok[tag] = self.root.after(step, tick)
        self._tok[tag] = self.root.after(step, tick)


def install(cls: type, ns: dict[str, Any]) -> None:
    health = ns.get('_pph28_health')
    jobs = ns.get('_pph28_jobs')
    events = ns.get('_pph28_events')
    services = ns.get('_pph28_services')

    # ------------------------------------------------------------ shell --
    def build_shell(self) -> None:
        try: self.root.configure(bg=BG)
        except Exception: pass
        self.content = tk.Frame(self.root, bg=BG)
        self.content.pack(fill='both', expand=True)
        if not hasattr(self, 'footer_var'): self.footer_var = tk.StringVar(value='')
        if not hasattr(self, 'page_title'): self.page_title = tk.StringVar(value='')
        if not hasattr(self, 'clock_var'): self.clock_var = tk.StringVar(value='--:--')
        if not hasattr(self, 'navigation_stack'): self.navigation_stack = []
        if not hasattr(self, 'back_button'):
            self.back_button = tk.Button(self.root)
        self.frames = {}
        self.pages = self.frames
        self.page_titles = {}
        self._pph6_anim = Anim(self.root)
        self._pph6_prev = {}
        self._pph6_refresh = {}
        self._pph6_notify_stack = []
        self._pph6_radio_sel = 'measurement'
        self._pph6_booted = False
        self._pph6_nav_map = {}

        # Single persistent bottom nav, built once. It lives outside the page
        # frames so it never participates in page-slide transitions and its
        # position never changes - only the active button's colors update.
        nav = tk.Frame(self.content, bg='#050A10', height=NAV_H, highlightthickness=1, highlightbackground=BORDER)
        nav.pack(side='bottom', fill='x'); nav.pack_propagate(False)
        self.pph6_nav_buttons = {}
        nav_items = [('HOME', 'home3'), ('WLAN', 'measure3'), ('NETZ', 'network'), ('ACCESS', 'access3'), ('SYSTEM', 'system3')]
        for i, (lab, target) in enumerate(nav_items):
            nav.grid_columnconfigure(i, weight=1, uniform='nav6')
            b = tk.Button(nav, text=lab, command=lambda t=target: self.show_page(t),
                          bg=PANEL2, fg=TEXT, activebackground=CYAN, activeforeground=BG,
                          relief='flat', bd=0, highlightthickness=1, highlightbackground=BORDER,
                          font=font(self, 11, 'bold'), cursor='hand2')
            b.grid(row=0, column=i, sticky='nsew', padx=4, pady=8)
            self.pph6_nav_buttons[target] = b

        self.pph6_page_area = tk.Frame(self.content, bg=BG)
        self.pph6_page_area.pack(fill='both', expand=True)

    def set_active_nav(self, key):
        for target, b in self.pph6_nav_buttons.items():
            selected = (target == key)
            try: b.configure(bg=(CYAN if selected else PANEL2), fg=(BG if selected else TEXT))
            except Exception: pass

    # --------------------------------------------------------- primitives --
    def font(self, size: int, weight: str = 'bold'):
        try:
            return self._font(size, weight)
        except Exception:
            return ('TkDefaultFont', size, weight)

    def new_page(self, name: str) -> tk.Frame:
        old = self.frames.get(name)
        if old is not None:
            try: old.destroy()
            except Exception: pass
        frame = tk.Frame(self.pph6_page_area, bg=BG)
        self.frames[name] = frame
        self.page_titles[name] = name
        return frame

    def chip(self, parent, text_var, kind='ready'):
        bg, fg = CHIP.get(kind, CHIP['ready'])
        lbl = tk.Label(parent, textvariable=text_var, bg=bg, fg=fg, font=font(self, 9, 'bold'), padx=10, pady=7)
        return lbl

    def header(self, page, kicker, title, status_text='READY', status_kind='ready', back_to=None):
        h = tk.Frame(page, bg=BG, height=HEADER_H); h.pack(fill='x', padx=14, pady=(8, 2)); h.pack_propagate(False)
        left = tk.Frame(h, bg=BG); left.pack(side='left', fill='y')
        if back_to:
            b = tk.Button(left, text='←', command=lambda t=back_to: self.show_page(t), bg=PANEL2, fg=TEXT,
                           activebackground=CYAN, activeforeground=BG, relief='flat', bd=0,
                           highlightthickness=1, highlightbackground=BORDER, font=font(self, 12, 'bold'),
                           width=3, cursor='hand2')
            b.pack(side='left', padx=(0, 10), pady=4)
        textcol = tk.Frame(left, bg=BG); textcol.pack(side='left', fill='y')
        tk.Label(textcol, text=kicker, bg=BG, fg=CYAN, font=font(self, 9, 'bold')).pack(anchor='w')
        tk.Label(textcol, text=title, bg=BG, fg=TEXT, font=font(self, 19, 'bold')).pack(anchor='w')
        svar = tk.StringVar(value=status_text)
        badge = chip(self, h, svar, status_kind)
        badge.pack(side='right', pady=10)
        return svar, badge

    def status_pulse(self, page_name, var, badge, base_kind, on_text, off_text):
        def tick():
            state = getattr(badge, '_pph6_on', False)
            badge._pph6_on = not state
            bg, fg = CHIP[base_kind]
            badge.configure(fg=(CYAN if state else fg))
        self._pph6_anim.loop(f'{page_name}:chip', 900, tick)

    def card(self, parent, title, value_var, accent=CYAN, detail_var=None):
        f = tk.Frame(parent, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        tk.Frame(f, bg=accent, height=5).pack(fill='x')
        tk.Label(f, text=title, bg=PANEL, fg=MUTED, font=font(self, 9, 'bold')).pack(anchor='w', padx=16, pady=(12, 0))
        tk.Label(f, textvariable=value_var, bg=PANEL, fg=accent, font=font(self, 28, 'bold'), wraplength=330, justify='left').pack(anchor='w', padx=16, pady=(2, 0))
        if detail_var is not None:
            tk.Label(f, textvariable=detail_var, bg=PANEL, fg=TEXT, font=font(self, 10), wraplength=330, justify='left').pack(anchor='w', padx=16, pady=(2, 12))
        else:
            tk.Frame(f, bg=PANEL, height=10).pack()
        return f

    def two_cards(self, content, left, right):
        row = tk.Frame(content, bg=BG); row.pack(fill='both', expand=True, padx=10, pady=6)
        left.pack(in_=row, side='left', fill='both', expand=True, padx=(0, 5))
        right.pack(in_=row, side='left', fill='both', expand=True, padx=(5, 0))
        # left/right were created before row, so they stack below it by default;
        # row's own opaque background would otherwise cover both cards entirely.
        left.lift(); right.lift()
        return row

    def action_button(self, parent, text, command, accent=CYAN, danger=False):
        base_bg = PANEL2
        b = tk.Button(parent, text=text, command=command, bg=base_bg, fg=TEXT,
                      activebackground=accent, activeforeground=BG, relief='flat', bd=0,
                      highlightthickness=1, highlightbackground=BORDER,
                      font=font(self, 12, 'bold'), pady=15, cursor='hand2')
        def press(_e=None):
            try: b.configure(bg=(RED if danger else accent), fg=BG, highlightbackground=(RED if danger else accent))
            except Exception: pass
        def release(_e=None):
            def reset():
                try: b.configure(bg=base_bg, fg=TEXT, highlightbackground=BORDER)
                except Exception: pass
            try: self._pph6_anim.after(f'btn:{id(b)}', 90, reset)
            except Exception: reset()
        b.bind('<ButtonPress-1>', press, add='+')
        b.bind('<ButtonRelease-1>', release, add='+')
        return b

    def action_row(self, content, items):
        # side='bottom' makes stacking order independent of whether this is called
        # from page_shell (before header/content exist) or afterwards by a page
        # builder - it always ends up directly above bottom_nav either way.
        r = tk.Frame(content, bg=BG, height=ACTION_H); r.pack(side='bottom', fill='x', padx=10, pady=(0, 8)); r.pack_propagate(False)
        for label, cmd, accent in items[:3]:
            action_button(self, r, label, cmd, accent, danger=(label in ('STOP', 'RESET'))).pack(side='left', fill='both', expand=True, padx=4)
        return r

    def list_row(self, parent, label, status_var, kind='ready', on_tap=None):
        bg, fg = CHIP.get(kind, CHIP['ready'])
        row = tk.Frame(parent, bg=PANEL, highlightthickness=1, highlightbackground=BORDER, cursor='hand2' if on_tap else 'arrow')
        stripe = tk.Frame(row, bg=fg, width=6); stripe.pack(side='left', fill='y')
        body = tk.Frame(row, bg=PANEL); body.pack(side='left', fill='both', expand=True, padx=12, pady=11)
        tk.Label(body, text=label, bg=PANEL, fg=TEXT, font=font(self, 11, 'bold'), anchor='w').pack(fill='x')
        status_lbl = tk.Label(body, textvariable=status_var, bg=PANEL, fg=fg, font=font(self, 9, 'bold'), anchor='w')
        status_lbl.pack(fill='x')
        def set_kind(k):
            _, kfg = CHIP.get(k, CHIP['ready'])
            try:
                stripe.configure(bg=kfg); status_lbl.configure(fg=kfg)
            except Exception: pass
        row._pph6_set_kind = set_kind
        if on_tap:
            for w in (row, body):
                w.bind('<Button-1>', lambda _e, f=on_tap: f(), add='+')
        return row

    def progress_bar(self, parent, accent=CYAN, height=14):
        c = tk.Canvas(parent, bg=PANEL2, height=height, highlightthickness=0)
        c._pph6_accent = accent
        state = {'pct': 0}
        def redraw(_e=None):
            c.delete('all')
            w = max(1, c.winfo_width())
            c.create_rectangle(0, 0, w, height, fill=PANEL2, outline='')
            c.create_rectangle(0, 0, int(w * max(0, min(100, state['pct'])) / 100), height, fill=accent, outline='')
        def set_pct(pct):
            state['pct'] = pct
            redraw()
        c._pph6_set = set_pct
        # widths aren't known synchronously (Tk resolves geometry on idle), so redraw
        # again whenever the canvas actually gets/changes its real on-screen size.
        c.bind('<Configure>', redraw, add='+')
        return c

    def indeterminate(self, canvas, page_name, tag='scan'):
        state = {'x': 0.0}
        def tick():
            w = max(1, canvas.winfo_width()); seg = max(30, int(w * 0.22))
            state['x'] = (state['x'] + w * 0.03) % (w + seg)
            canvas.delete('all')
            canvas.create_rectangle(0, 0, w, int(canvas['height']), fill=PANEL2, outline='')
            canvas.create_rectangle(state['x'] - seg, 0, state['x'], int(canvas['height']), fill=getattr(canvas, '_pph6_accent', CYAN), outline='')
        self._pph6_anim.loop(f'{page_name}:{tag}', 45, tick)

    def stop_indeterminate(self, page_name, tag='scan'):
        self._pph6_anim.cancel(f'{page_name}:{tag}')

    def page_indicator(self, parent, count, active):
        row = tk.Frame(parent, bg=BG); row.pack(pady=(2, 0))
        for i in range(count):
            tk.Label(row, text='●' if i == active else '○', bg=BG, fg=(CYAN if i == active else BORDER), font=font(self, 10, 'bold')).pack(side='left', padx=3)
        return row

    def page_shell(self, name, kicker, title, active_nav, status_text='READY', status_kind='ready', back_to=None, actions=None):
        page = new_page(self, name)
        self._pph6_nav_map[name] = active_nav
        if actions:
            action_row(self, page, actions)
        svar, badge = header(self, page, kicker, title, status_text, status_kind, back_to)
        content = tk.Frame(page, bg=BG); content.pack(fill='both', expand=True, padx=0, pady=0)
        return page, content, svar, badge

    # ------------------------------------------------------------- swipe --
    def wire_swipe(self, frame, prev_name, next_name):
        state = {'x': None}
        def down(e): state['x'] = e.x_root
        def up(e):
            if state['x'] is None: return
            dx = e.x_root - state['x']; state['x'] = None
            if dx > 80 and prev_name: self.show_page(prev_name)
            elif dx < -80 and next_name: self.show_page(next_name)
        frame.bind('<ButtonPress-1>', down, add='+')
        frame.bind('<ButtonRelease-1>', up, add='+')

    # ----------------------------------------------------------- overlay --
    def overlay(self, title, message, rows=None, buttons=None):
        dim = tk.Frame(self.root, bg='#000000')
        dim.place(relx=0, rely=0, relwidth=1, relheight=1)
        try: dim.attributes
        except Exception: pass
        panel = tk.Frame(dim, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        panel.place(relx=0.5, rely=0.5, anchor='center', width=560, height=300)
        tk.Frame(panel, bg=RED, height=5).pack(fill='x')
        tk.Label(panel, text=title, bg=PANEL, fg=TEXT, font=font(self, 16, 'bold')).pack(anchor='w', padx=20, pady=(14, 2))
        tk.Label(panel, text=message, bg=PANEL, fg=MUTED, font=font(self, 10), wraplength=520, justify='left').pack(anchor='w', padx=20)
        if rows:
            rf = tk.Frame(panel, bg=PANEL); rf.pack(fill='x', padx=20, pady=(10, 0))
            for label, ok in rows:
                r = tk.Frame(rf, bg=PANEL); r.pack(fill='x', pady=2)
                tk.Label(r, text=label, bg=PANEL, fg=TEXT, font=font(self, 9, 'bold'), anchor='w').pack(side='left')
                tk.Label(r, text=('OK' if ok else 'FAIL'), bg=PANEL, fg=(GREEN if ok else RED), font=font(self, 9, 'bold')).pack(side='right')
        def close():
            try: dim.destroy()
            except Exception: pass
        br = tk.Frame(panel, bg=PANEL); br.pack(side='bottom', fill='x', padx=16, pady=14)
        btns = list(buttons or []) or [('CLOSE', close, CYAN)]
        for label, cmd, accent in btns:
            def wrapped(c=cmd):
                try: c()
                finally: close()
            action_button(self, br, label, wrapped, accent).pack(side='left', fill='both', expand=True, padx=4)
        dim.lift()
        panel.place_configure(width=1, height=1)
        def frame(t):
            wpx = int(560 * (0.92 + 0.08 * t)); hpx = int(300 * (0.92 + 0.08 * t))
            panel.place_configure(width=wpx, height=hpx)
        self._pph6_anim.tween('overlay:open', 150, frame, tier='REDUCED')
        return close

    # -------------------------------------------------------- notify toast --
    def notify(self, text, kind='info'):
        kind_map = {'info': CYAN, 'ok': GREEN, 'warn': YELLOW, 'error': RED}
        accent = kind_map.get(kind, CYAN)
        while len(self._pph6_notify_stack) >= 2:
            old = self._pph6_notify_stack.pop(0)
            try: old.destroy()
            except Exception: pass
        n = tk.Frame(self.root, bg=PANEL2, highlightthickness=1, highlightbackground=accent)
        tk.Label(n, text=text, bg=PANEL2, fg=TEXT, font=font(self, 10, 'bold'), padx=14, pady=10).pack()
        idx = len(self._pph6_notify_stack)
        self._pph6_notify_stack.append(n)
        y_target = 10 + idx * 46
        n.place(relx=1.0, x=20, y=y_target, anchor='ne')
        n.lift()
        def frame(t):
            n.place_configure(x=int(20 - 240 * (1 - t)))
        self._pph6_anim.tween(f'notify:{id(n)}:in', 160, frame, tier='REDUCED')
        def dismiss():
            def frame_out(t):
                n.place_configure(x=int(20 - 240 * t))
            def done():
                try: n.destroy()
                except Exception: pass
                if n in self._pph6_notify_stack: self._pph6_notify_stack.remove(n)
            self._pph6_anim.tween(f'notify:{id(n)}:out', 160, frame_out, on_done=done, tier='REDUCED')
        self._pph6_anim.after(f'notify:{id(n)}:life', 2600, dismiss)

    # -------------------------------------------------------- value anim --
    def animate_value(self, page, key, var, new_value, fmt, tier='FULL'):
        old = self._pph6_prev.get(key)
        self._pph6_prev[key] = new_value
        if old is None or old == new_value or not isinstance(new_value, (int, float)) or not isinstance(old, (int, float)):
            var.set(fmt(new_value)); return
        def frame(t):
            var.set(fmt(old + (new_value - old) * t))
        self._pph6_anim.tween(f'{page}:val:{key}', 320, frame, tier=tier)

    # =====================================================================
    # PAGES
    # =====================================================================

    def build_home(self):
        page, content, svar, badge = page_shell(self, 'home3', 'PPH 6 · FIELD SYSTEM', 'FIELD CENTER', 'home3', 'READY', 'ready',
                                                  actions=None)
        self.p6_net = tk.StringVar(value='—'); self.p6_net_d = tk.StringVar(value='Uplink wird geprüft')
        self.p6_field = tk.StringVar(value='READY'); self.p6_field_d = tk.StringVar(value='Alle Systeme OK')
        two_cards(self, content, card(self, content, 'NETWORK', self.p6_net, CYAN, self.p6_net_d),
                  card(self, content, 'FIELD STATUS', self.p6_field, GREEN, self.p6_field_d))
        action_row(self, page, [
            ('WIRELESS', lambda: self.show_page('measure3'), CYAN),
            ('QUICK TEST', lambda: self.show_page('network_doctor'), GREEN),
            ('FIELD', lambda: self.show_page('field50'), PURPLE),
        ])

        def refresh():
            route = run(['ip', 'route', 'show', 'default'])
            self.p6_net.set('ONLINE' if route else 'OFFLINE')
            self.p6_net_d.set(route.splitlines()[0][:44] if route else 'Kein Uplink')
            ap = _ensure_ap(self)
            try: s = ap.status() if ap else {}
            except Exception: s = {}
            self.p6_field.set('READY')
            self.p6_field_d.set(f"AP {'aktiv' if s.get('active') else 'aus'} · Messung bereit")
        self._pph6_refresh['home3'] = refresh

    def build_more(self):
        page, content, svar, badge = page_shell(self, 'more6', 'PPH HUB', 'ALLE KATEGORIEN', 'system3', 'READY', 'ready')
        grid = tk.Frame(content, bg=BG); grid.pack(fill='both', expand=True, padx=10, pady=6)
        for c in range(3): grid.grid_columnconfigure(c, weight=1, uniform='more6')
        for r in range(2): grid.grid_rowconfigure(r, weight=1, uniform='more6')
        tiles = [
            ('RADIOS', 'Adapter, DFS, Kanäle', 'wifi3', ORANGE),
            ('EVENTS', 'Verlauf und Meldungen', 'events3', BLUE),
            ('SETTINGS', 'Anzeige, Updates, Field Mode', 'settings3', CYAN),
            ('CONNECTION FLOW', 'Internet bis Client', 'flow50', GREEN),
            ('SESSION', 'Kunden-Session aufzeichnen', 'session50', PURPLE),
            ('TOOLS', 'Netzwerk-Werkzeuge', 'tools', YELLOW),
        ]
        for i, (title, detail, target, accent) in enumerate(tiles):
            f = tk.Frame(grid, bg=PANEL, highlightthickness=1, highlightbackground=BORDER, cursor='hand2')
            tk.Frame(f, bg=accent, height=4).pack(fill='x')
            tk.Label(f, text=title, bg=PANEL, fg=TEXT, font=font(self, 11, 'bold')).pack(anchor='w', padx=12, pady=(8, 0))
            tk.Label(f, text=detail, bg=PANEL, fg=MUTED, font=font(self, 8), wraplength=200, justify='left').pack(anchor='w', padx=12, pady=(2, 8))
            for w in (f,) + tuple(f.winfo_children()):
                w.bind('<Button-1>', lambda _e, t=target: self.show_page(t), add='+')
            f.grid(row=i // 3, column=i % 3, sticky='nsew', padx=4, pady=4)

    def build_wireless(self):
        page, content, svar, badge = page_shell(self, 'measure3', 'RF / WLAN', 'WIRELESS SITE ANALYZER', 'measure3', 'READY', 'ready',
                                                  actions=None)
        self.p6_sig = tk.StringVar(value='—'); self.p6_sig_d = tk.StringVar(value='RSSI')
        self.p6_thr = tk.StringVar(value='—'); self.p6_thr_d = tk.StringVar(value='Live throughput')
        two_cards(self, content, card(self, content, 'SIGNAL', self.p6_sig, CYAN, self.p6_sig_d),
                  card(self, content, 'THROUGHPUT', self.p6_thr, PURPLE, self.p6_thr_d))
        action_row(self, page, [
            ('START', lambda: self.launch_funktest(), CYAN),
            ('DETAILS', lambda: self.show_page('measure3_detail'), ORANGE),
            ('RADIOS', lambda: self.show_page('wifi3'), PURPLE),
        ])
        wire_swipe(self, content, None, 'measure3_detail')
        self._pph6_wire_status = (svar, badge)

        def refresh():
            try: st = self._read_measurement_state()
            except Exception: st = {}
            try: running = self._measurement_running() or self._funktest_running()
            except Exception: running = False
            svar.set('● LIVE' if running else 'READY')
            sig = _first(st.get('signal_dbm'), st.get('rssi'))
            if isinstance(sig, (int, float)):
                animate_value(self, 'measure3', 'sig', self.p6_sig, float(sig), lambda v: f'{v:.0f} dBm')
                q = max(0, min(100, int((sig + 95) * 2)))
                self.p6_sig_d.set('EXCELLENT' if q > 80 else 'GOOD' if q > 55 else 'FAIR' if q > 30 else 'WEAK')
            else:
                self.p6_sig.set('—'); self.p6_sig_d.set('RSSI')
            dl = _first(st.get('download_mbps'), st.get('throughput_mbps'))
            if isinstance(dl, (int, float)):
                animate_value(self, 'measure3', 'thr', self.p6_thr, float(dl), lambda v: f'{v:.1f} Mbit/s')
            else:
                self.p6_thr.set('—')
        self._pph6_refresh['measure3'] = refresh

    def build_wireless_detail(self):
        page, content, svar, badge = page_shell(self, 'measure3_detail', 'RF / WLAN', 'WIRELESS DETAILS', 'measure3', '', 'ready', back_to='measure3')
        badge.pack_forget()
        page_indicator(self, content, 2, 1)
        grid = tk.Frame(content, bg=BG); grid.pack(fill='both', expand=True, padx=10, pady=4)
        for c in range(2): grid.grid_columnconfigure(c, weight=1, uniform='wd')
        for r in range(2): grid.grid_rowconfigure(r, weight=1, uniform='wd')
        self.p6_lat = tk.StringVar(value='—'); self.p6_qual = tk.StringVar(value='—')
        self.p6_loss = tk.StringVar(value='—'); self.p6_chan = tk.StringVar(value='—')
        defs = [('LATENCY', self.p6_lat, YELLOW), ('QUALITY', self.p6_qual, GREEN),
                ('LOSS', self.p6_loss, ORANGE), ('CHANNEL', self.p6_chan, BLUE)]
        for i, (title, var, accent) in enumerate(defs):
            card(self, grid, title, var, accent).grid(row=i // 2, column=i % 2, sticky='nsew', padx=4, pady=4)
        wire_swipe(self, content, 'measure3', None)

        def refresh():
            try: st = self._read_measurement_state()
            except Exception: st = {}
            ping = _first(st.get('ping_ms'), st.get('latency_ms'))
            self.p6_lat.set(f'{float(ping):.1f} ms' if isinstance(ping, (int, float)) else '—')
            sig = _first(st.get('signal_dbm'), st.get('rssi'))
            self.p6_qual.set(f'{max(0, min(100, int((sig + 95) * 2)))}%' if isinstance(sig, (int, float)) else '—')
            loss = _first(st.get('loss_pct'), st.get('packet_loss'))
            self.p6_loss.set(f'{float(loss):.1f} %' if isinstance(loss, (int, float)) else '—')
            ch = st.get('channel'); self.p6_chan.set(str(ch) if ch else 'AUTO')
        self._pph6_refresh['measure3_detail'] = refresh

    def build_radio_center(self):
        page, content, svar, badge = page_shell(self, 'wifi3', 'RF / WLAN', 'RADIO CENTER', 'measure3', 'READY', 'ready')
        rows = tk.Frame(content, bg=BG); rows.pack(fill='both', expand=True, padx=14, pady=4)
        self.p6_radio_status = {}
        defs = [('control', 'ONBOARD', 'Broadcom / brcmfmac · CONTROL / CLIENT'),
                ('measurement', 'BROSTREND', 'mt7921u · ACCESS POINT / FIELD'),
                ('scan', 'ALFA AWUS', 'mt76x2u · RF ANALYSIS')]
        for key, label, sub in defs:
            v = tk.StringVar(value=sub)
            self.p6_radio_status[key] = v
            list_row(self, rows, label, v, 'offline', on_tap=lambda k=key: open_radio_detail(self, k)).pack(fill='x', pady=4)

        def refresh():
            ov = _adapter_overview(); roles = ov.get('roles') or {}
            for key, label, sub in defs:
                r = roles.get(key) or {}
                if r:
                    self.p6_radio_status[key].set(f"{r.get('interface','—')} · {r.get('driver','—')} · {r.get('operstate','—')}")
                else:
                    self.p6_radio_status[key].set(sub + ' · nicht erkannt')
        self._pph6_refresh['wifi3'] = refresh

    def open_radio_detail(self, key):
        self._pph6_radio_sel = key
        self.show_page('radio_detail')

    def build_radio_detail(self):
        page, content, svar, badge = page_shell(self, 'radio_detail', 'RF / WLAN', 'RADIO DETAILS', 'measure3', '', 'ready', back_to='wifi3')
        badge.pack_forget()
        self.p6_radio_title = tk.StringVar(value='—'); self.p6_radio_sub = tk.StringVar(value='—')
        hero = card(self, content, 'ADAPTER', self.p6_radio_title, ORANGE, self.p6_radio_sub)
        hero.pack(fill='both', expand=True, padx=10, pady=6)

        def refresh():
            key = getattr(self, '_pph6_radio_sel', 'measurement')
            labels = {'control': 'ONBOARD', 'measurement': 'BROSTREND', 'scan': 'ALFA AWUS'}
            self.p6_radio_title.set(labels.get(key, key.upper()))
            ov = _adapter_overview(); r = (ov.get('roles') or {}).get(key) or {}
            if r:
                self.p6_radio_sub.set(f"{r.get('interface','—')} · {r.get('driver','—')} · {r.get('iftype','managed')} · {r.get('operstate','—')}")
            else:
                self.p6_radio_sub.set('Adapter nicht erkannt')
        self._pph6_refresh['radio_detail'] = refresh

    def build_network(self):
        page, content, svar, badge = page_shell(self, 'network', 'LAN / WAN', 'NETWORK ANALYZER', 'network', 'READY', 'ready')
        self.p6_dl = tk.StringVar(value='—'); self.p6_ul = tk.StringVar(value='—')
        two_cards(self, content, card(self, content, 'DOWNLOAD', self.p6_dl, CYAN),
                  card(self, content, 'UPLOAD', self.p6_ul, PURPLE))
        action_row(self, page, [
            ('TEST', lambda: self.launch_funktest(), CYAN),
            ('DOCTOR', lambda: self.show_page('network_doctor'), GREEN),
            ('DETAILS', lambda: self.show_page('network_detail'), ORANGE),
        ])
        wire_swipe(self, content, None, 'network_detail')

        def refresh():
            try: st = self._read_measurement_state()
            except Exception: st = {}
            dl = st.get('download_mbps'); ul = st.get('upload_mbps')
            if isinstance(dl, (int, float)): animate_value(self, 'network', 'dl', self.p6_dl, float(dl), lambda v: f'{v:.0f} Mbit/s')
            else: self.p6_dl.set('—')
            if isinstance(ul, (int, float)): animate_value(self, 'network', 'ul', self.p6_ul, float(ul), lambda v: f'{v:.0f} Mbit/s')
            else: self.p6_ul.set('—')
        self._pph6_refresh['network'] = refresh

    def build_network_detail(self):
        page, content, svar, badge = page_shell(self, 'network_detail', 'LAN / WAN', 'NETWORK DETAILS', 'network', '', 'ready', back_to='network')
        badge.pack_forget()
        grid = tk.Frame(content, bg=BG); grid.pack(fill='both', expand=True, padx=10, pady=4)
        for c in range(2): grid.grid_columnconfigure(c, weight=1, uniform='nd')
        for r in range(2): grid.grid_rowconfigure(r, weight=1, uniform='nd')
        self.p6_ping = tk.StringVar(value='—'); self.p6_jitter = tk.StringVar(value='—')
        self.p6_nloss = tk.StringVar(value='—'); self.p6_uplink = tk.StringVar(value='—')
        defs = [('PING', self.p6_ping, YELLOW), ('JITTER', self.p6_jitter, ORANGE),
                ('LOSS', self.p6_nloss, GREEN), ('UPLINK', self.p6_uplink, BLUE)]
        for i, (title, var, accent) in enumerate(defs):
            card(self, grid, title, var, accent).grid(row=i // 2, column=i % 2, sticky='nsew', padx=4, pady=4)
        wire_swipe(self, content, 'network', None)

        def refresh():
            try: st = self._read_measurement_state()
            except Exception: st = {}
            ping = _first(st.get('ping_ms'), st.get('latency_ms'))
            self.p6_ping.set(f'{float(ping):.1f} ms' if isinstance(ping, (int, float)) else '—')
            jit = st.get('jitter_ms')
            self.p6_jitter.set(f'{float(jit):.1f} ms' if isinstance(jit, (int, float)) else '—')
            loss = _first(st.get('loss_pct'), st.get('packet_loss'))
            self.p6_nloss.set(f'{float(loss):.1f} %' if isinstance(loss, (int, float)) else '—')
            route = run(['ip', 'route', 'show', 'default'])
            iface = ''
            try: iface = route.split('dev ', 1)[1].split()[0] if 'dev ' in route else ''
            except Exception: pass
            self.p6_uplink.set((iface or 'eth0') + ' · 1 Gbit')
        self._pph6_refresh['network_detail'] = refresh

    def build_access(self):
        page, content, svar, badge = page_shell(self, 'access3', 'FIELD ROUTER', 'ACCESS POINT', 'access3', 'OFF', 'offline')
        self.p6_ap = tk.StringVar(value='—'); self.p6_ap_d = tk.StringVar(value='PPH-WIFI')
        self.p6_code = tk.StringVar(value='—'); self.p6_code_d = tk.StringVar(value='10.42.0.1')
        two_cards(self, content, card(self, content, 'PPH-WIFI', self.p6_ap, GREEN, self.p6_ap_d),
                  card(self, content, 'PAIRING CODE', self.p6_code, PURPLE, self.p6_code_d))
        info = tk.Frame(content, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        info.pack(fill='x', padx=14, pady=(0, 4))
        row = tk.Frame(info, bg=PANEL); row.pack(fill='x', padx=14, pady=8)
        self.p6_ssid = tk.StringVar(value='PPH-WIFI'); self.p6_lanip = tk.StringVar(value='—')
        for label, var, accent in (('SSID', self.p6_ssid, CYAN), ('LAN IP', self.p6_lanip, BLUE)):
            c = tk.Frame(row, bg=PANEL); c.pack(side='left', fill='x', expand=True)
            tk.Label(c, text=label, bg=PANEL, fg=MUTED, font=font(self, 8, 'bold')).pack(anchor='w')
            tk.Label(c, textvariable=var, bg=PANEL, fg=accent, font=font(self, 13, 'bold')).pack(anchor='w')
        action_row(self, page, [
            ('START', lambda: ap_start(self), GREEN),
            ('STOP', lambda: ap_stop(self), RED),
            ('DETAILS', lambda: self.show_page('access_detail'), CYAN),
        ])

        def refresh():
            ap = _ensure_ap(self)
            try: s = ap.status() or {} if ap else {}
            except Exception: s = {}
            active = bool(s.get('active'))
            svar.set('● ACTIVE' if active else 'OFF')
            badge.configure(**dict(zip(('bg', 'fg'), CHIP['active' if active else 'offline'])))
            self.p6_ap.set('ACTIVE' if active else 'OFF')
            ssid = s.get('ssid') or 'PPH-WIFI'; clients = s.get('clients', 0)
            self.p6_ap_d.set(f'{clients} CLIENTS'); self.p6_ssid.set(ssid)
            code = s.get('pairing_code') or s.get('token') or '—'
            self.p6_code.set(str(code))
            ip = s.get('ap_ip') or '10.42.0.1'
            self.p6_code_d.set(str(ip)); self.p6_lanip.set(s.get('lan_ip') or '—')
        self._pph6_refresh['access3'] = refresh

    def build_access_detail(self):
        page, content, svar, badge = page_shell(self, 'access_detail', 'FIELD ROUTER', 'ACCESS POINT DETAILS', 'access3', '', 'ready', back_to='access3')
        badge.pack_forget()
        rows = tk.Frame(content, bg=BG); rows.pack(fill='both', expand=True, padx=14, pady=4)
        self.p6_ad = {}
        for key, label in (('radio', 'RADIO'), ('band', 'BAND / CHANNEL'), ('clients', 'CLIENTS'),
                            ('throughput', 'THROUGHPUT'), ('internet', 'INTERNET')):
            v = tk.StringVar(value='—'); self.p6_ad[key] = v
            list_row(self, rows, label, v, 'ready').pack(fill='x', pady=3)

        def refresh():
            ap = _ensure_ap(self)
            try: s = ap.status() or {} if ap else {}
            except Exception: s = {}
            self.p6_ad['radio'].set(f"BrosTrend · {s.get('driver','mt7921u')}")
            self.p6_ad['band'].set(f"{s.get('band','—')}")
            self.p6_ad['clients'].set(str(s.get('clients', 0)))
            self.p6_ad['throughput'].set(f"{float(s.get('total_mbps') or 0):.1f} Mbit/s")
            self.p6_ad['internet'].set('ONLINE' if s.get('internet') else 'OFFLINE')
        self._pph6_refresh['access_detail'] = refresh

    def build_connection_flow(self):
        page, content, svar, badge = page_shell(self, 'flow50', 'FIELD ROUTER', 'CONNECTION FLOW', 'access3', 'LIVE', 'live')
        wrap = tk.Frame(content, bg=BG); wrap.pack(fill='both', expand=True, padx=40, pady=4)
        steps = [('INTERNET', GREEN), ('ETHERNET', CYAN), ('RASPBERRY PI', BLUE), ('BROSTREND', ORANGE), ('PPH-WIFI', PURPLE), ('CLIENTS', GREEN)]
        self.p6_flow_boxes = []
        canvas = tk.Canvas(wrap, bg=BG, highlightthickness=0)
        canvas.pack(fill='both', expand=True)

        def draw():
            canvas.delete('all')
            cw = max(200, canvas.winfo_width()); ch = max(200, canvas.winfo_height())
            n = len(steps); box_h = 34; gap = (ch - n * box_h) / max(1, n - 1)
            self.p6_flow_boxes = []
            for i, (label, accent) in enumerate(steps):
                y = i * (box_h + gap)
                canvas.create_rectangle(cw * 0.15, y, cw * 0.85, y + box_h, fill=PANEL, outline=accent, width=2)
                canvas.create_text(cw / 2, y + box_h / 2, text=label, fill=TEXT, font=font(self, 11, 'bold'))
                self.p6_flow_boxes.append((cw / 2, y + box_h))
                if i < n - 1:
                    canvas.create_line(cw / 2, y + box_h, cw / 2, y + box_h + gap, fill=accent, width=2, tags='flowline')
        canvas.bind('<Configure>', lambda _e: draw())

        def pulse():
            if not self.p6_flow_boxes: return
            canvas.delete('pulse')
            t = (time.monotonic() * 0.4) % 1.0
            for i in range(len(self.p6_flow_boxes) - 1):
                x, y0 = self.p6_flow_boxes[i]; _x2, y1 = self.p6_flow_boxes[i + 1]
                y = y0 + (y1 - y0) * t
                canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill=CYAN, outline='', tags='pulse')
        self._pph6_anim.loop('flow50:pulse', 60, pulse)
        self._pph6_refresh['flow50'] = lambda: None

    def build_network_doctor(self):
        page, content, svar, badge = page_shell(self, 'network_doctor', 'DIAGNOSTICS', 'NETWORK DOCTOR', 'network', 'READY', 'ready')
        rows = tk.Frame(content, bg=BG); rows.pack(fill='both', expand=True, padx=14, pady=(4, 0))
        self.p6_doc = {}
        checks = [('eth', 'ETHERNET'), ('gw', 'GATEWAY'), ('dns', 'DNS'), ('inet', 'INTERNET')]
        self.p6_doc_row = {}
        for key, label in checks:
            v = tk.StringVar(value='—'); self.p6_doc[key] = v
            row = list_row(self, rows, label, v, 'ready')
            row.pack(fill='x', pady=3)
            self.p6_doc_row[key] = row
        self.p6_doc_result = tk.StringVar(value='TIPPE RUN AGAIN')
        self.p6_doc_result_lbl = tk.Label(content, textvariable=self.p6_doc_result, bg=BG, fg=YELLOW, font=font(self, 12, 'bold'))
        self.p6_doc_result_lbl.pack(pady=(6, 0))
        action_row(self, page, [('RUN AGAIN', lambda: run_doctor(self), CYAN), ('DETAILS', lambda: show_doctor_overlay(self), ORANGE)])

        def refresh():
            run_doctor(self)
        self._pph6_refresh['network_doctor'] = refresh

    def build_system(self):
        page, content, svar, badge = page_shell(self, 'system3', 'DEVICE', 'SYSTEM STATUS', 'system3', 'READY', 'ready')
        self.p6_cpu = tk.StringVar(value='—'); self.p6_cpu_d = tk.StringVar(value='Temperature')
        self.p6_ram = tk.StringVar(value='—'); self.p6_ram_d = tk.StringVar(value='Memory')
        two_cards(self, content, card(self, content, 'CPU', self.p6_cpu, ORANGE, self.p6_cpu_d),
                  card(self, content, 'RAM', self.p6_ram, BLUE, self.p6_ram_d))
        action_row(self, page, [('HARDWARE', lambda: self.show_page('hardware'), ORANGE),
                                 ('STORAGE', lambda: self.show_page('storage'), PURPLE),
                                 ('MORE', lambda: self.show_page('more6'), CYAN)])
        wire_swipe(self, content, None, 'system_detail')

        def refresh():
            temp = run(['bash', '-lc', "cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || true"])
            try:
                tc = int(temp) / 1000
                animate_value(self, 'system3', 'cpu', self.p6_cpu, tc, lambda v: f'{v:.0f}°C')
            except Exception:
                self.p6_cpu.set('—')
            mem = run(['bash', '-lc', "LC_ALL=C free -m | awk '/Mem:/ {printf \"%d\", $3*100/$2}'"])
            try:
                animate_value(self, 'system3', 'ram', self.p6_ram, float(mem), lambda v: f'{v:.0f}%')
            except Exception:
                self.p6_ram.set('—')
        self._pph6_refresh['system3'] = refresh

    def build_system_detail(self):
        page, content, svar, badge = page_shell(self, 'system_detail', 'DEVICE', 'SYSTEM DETAILS', 'system3', '', 'ready', back_to='system3')
        badge.pack_forget()
        self.p6_disk = tk.StringVar(value='—'); self.p6_power = tk.StringVar(value='NORMAL')
        two_cards(self, content, card(self, content, 'STORAGE', self.p6_disk, PURPLE),
                  card(self, content, 'POWER', self.p6_power, GREEN))
        wire_swipe(self, content, 'system3', None)

        def refresh():
            out = run(['bash', '-lc', "df -h / | awk 'NR==2{print $5}'"])
            self.p6_disk.set(out or '—')
            volts = run(['bash', '-lc', 'vcgencmd get_throttled 2>/dev/null || true'])
            flagged = volts.strip().endswith('0x0') is False and volts != ''
            self.p6_power.set('THROTTLED' if flagged else 'NORMAL')
        self._pph6_refresh['system_detail'] = refresh

    def build_hardware(self):
        page, content, svar, badge = page_shell(self, 'hardware', 'DEVICE', 'HARDWARE', 'system3', 'READY', 'ready', back_to='system3')
        rows = tk.Frame(content, bg=BG); rows.pack(fill='both', expand=True, padx=14, pady=4)
        self.p6_hw = {}
        for key, label in (('pi', 'RASPBERRY PI 5'), ('display', 'DISPLAY'), ('brostrend', 'BROSTREND'),
                            ('alfa', 'ALFA AWUS'), ('storage', 'STORAGE')):
            v = tk.StringVar(value='—'); self.p6_hw[key] = v
            list_row(self, rows, label, v, 'ready').pack(fill='x', pady=3)

        def refresh():
            self.p6_hw['pi'].set('ONLINE')
            self.p6_hw['display'].set('800×480 DSI')
            ov = _adapter_overview(); roles = ov.get('roles') or {}
            self.p6_hw['brostrend'].set('DETECTED' if roles.get('measurement') else 'NICHT ERKANNT')
            self.p6_hw['alfa'].set('DETECTED' if roles.get('scan') else 'NICHT ERKANNT')
            self.p6_hw['storage'].set('ONLINE')
        self._pph6_refresh['hardware'] = refresh

    def build_storage(self):
        page, content, svar, badge = page_shell(self, 'storage', 'DEVICE', 'STORAGE', 'system3', 'READY', 'ready', back_to='system3')
        wrap = tk.Frame(content, bg=BG); wrap.pack(fill='both', expand=True, padx=16, pady=8)
        self.p6_store_bars = {}
        for key, label in (('root', 'SYSTEM'), ('data', 'DATEN')):
            box = tk.Frame(wrap, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
            box.pack(fill='x', pady=6)
            head = tk.Frame(box, bg=PANEL); head.pack(fill='x', padx=14, pady=(10, 2))
            tk.Label(head, text=label, bg=PANEL, fg=MUTED, font=font(self, 9, 'bold')).pack(side='left')
            v = tk.StringVar(value='—'); tk.Label(head, textvariable=v, bg=PANEL, fg=CYAN, font=font(self, 9, 'bold')).pack(side='right')
            bar = progress_bar(self, box, CYAN); bar.pack(fill='x', padx=14, pady=(2, 12))
            self.p6_store_bars[key] = (v, bar)

        def refresh_mount(key, path):
            out = run(['bash', '-lc', f"df -h {path} 2>/dev/null | awk 'NR==2{{print $2, $4, $5}}'"])
            parts = out.split()
            v, bar = self.p6_store_bars[key]
            if len(parts) == 3:
                total, free, pct = parts
                v.set(f'{free} FREI')
                try: bar._pph6_set(100 - int(pct.strip('%')))
                except Exception: pass
            else:
                v.set('NICHT EINGEHÄNGT')
                try: bar._pph6_set(0)
                except Exception: pass

        def refresh():
            refresh_mount('root', '/')
            refresh_mount('data', '/mnt/storage')
        self._pph6_refresh['storage'] = refresh

    def build_events(self):
        page, content, svar, badge = page_shell(self, 'events3', 'SYSTEM', 'EVENTS', 'system3', 'READY', 'ready', back_to='system3',
                                                  actions=[('RAW LOG', lambda: self.show_page('events_raw'), CYAN)])
        self.p6_events_wrap = tk.Frame(content, bg=BG); self.p6_events_wrap.pack(fill='both', expand=True, padx=12, pady=4)

        def refresh():
            for w in self.p6_events_wrap.winfo_children(): w.destroy()
            rows = []
            try:
                if events: rows = events.read_events(limit=6)
            except Exception: rows = []
            if not rows:
                tk.Label(self.p6_events_wrap, text='Keine Events', bg=BG, fg=MUTED, font=font(self, 10)).pack(pady=20)
                return
            for item in reversed(rows):
                sev = str(item.get('severity') or 'info')
                accent = RED if sev in ('error', 'critical') else YELLOW if sev == 'warning' else CYAN
                row = tk.Frame(self.p6_events_wrap, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
                row.pack(fill='x', pady=3)
                tk.Frame(row, bg=accent, width=6).pack(side='left', fill='y')
                body = tk.Frame(row, bg=PANEL); body.pack(side='left', fill='both', expand=True, padx=10, pady=8)
                ts = str(item.get('timestamp') or '')[-8:-3]
                tk.Label(body, text=f"{ts}  {item.get('message') or item.get('type') or 'Event'}", bg=PANEL, fg=TEXT, font=font(self, 10, 'bold'), anchor='w').pack(fill='x')
        self._pph6_refresh['events3'] = refresh

    def build_events_raw(self):
        page, content, svar, badge = page_shell(self, 'events_raw', 'SYSTEM', 'RAW LOG', 'system3', '', 'ready', back_to='events3')
        badge.pack_forget()
        t = tk.Text(content, bg=PANEL, fg=TEXT, insertbackground=TEXT, relief='flat', bd=0,
                    highlightthickness=1, highlightbackground=BORDER, font=font(self, 10), wrap='word', padx=12, pady=10)
        t.pack(fill='both', expand=True, padx=12, pady=6)
        self.p6_rawlog = t

        def refresh():
            out = run(['bash', '-lc', 'journalctl -n 30 --no-pager 2>/dev/null || true'])
            t.configure(state='normal'); t.delete('1.0', 'end'); t.insert('end', out or 'Keine Daten'); t.configure(state='disabled')
        self._pph6_refresh['events_raw'] = refresh

    def build_settings(self):
        page, content, svar, badge = page_shell(self, 'settings3', 'DEVICE', 'SETTINGS', 'system3', '', 'ready', back_to='system3')
        badge.pack_forget()
        page_indicator(self, content, 2, 0)
        box = tk.Frame(content, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        box.pack(fill='both', expand=True, padx=14, pady=6)

        def row_label(text):
            tk.Label(box, text=text, bg=PANEL, fg=MUTED, font=font(self, 9, 'bold')).pack(anchor='w', padx=14, pady=(16, 6))

        row_label('DISPLAY BRIGHTNESS')
        r1 = tk.Frame(box, bg=PANEL); r1.pack(fill='x', padx=10)
        for pct in (25, 50, 75, 100):
            action_button(self, r1, f'{pct}%', lambda v=pct: self.set_brightness(v), YELLOW).pack(side='left', fill='x', expand=True, padx=3)

        row_label('DISPLAY TIMEOUT')
        r2 = tk.Frame(box, bg=PANEL); r2.pack(fill='x', padx=10)
        for sec, lab in ((30, '30 S'), (60, '1 MIN'), (120, '2 MIN'), (0, 'NIE')):
            action_button(self, r2, lab, lambda v=sec: self.set_timeout(v), CYAN).pack(side='left', fill='x', expand=True, padx=3)
        wire_swipe(self, content, None, 'settings_detail')
        action_row(self, page, [('WEITER', lambda: self.show_page('settings_detail'), CYAN)])
        self._pph6_refresh['settings3'] = lambda: None

    def build_settings_detail(self):
        page, content, svar, badge = page_shell(self, 'settings_detail', 'DEVICE', 'SETTINGS', 'system3', '', 'ready', back_to='settings3')
        badge.pack_forget()
        page_indicator(self, content, 2, 1)
        box = tk.Frame(content, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        box.pack(fill='both', expand=True, padx=14, pady=6)

        def row_label(text):
            tk.Label(box, text=text, bg=PANEL, fg=MUTED, font=font(self, 9, 'bold')).pack(anchor='w', padx=14, pady=(16, 6))

        row_label('ANIMATIONEN')
        r3 = tk.Frame(box, bg=PANEL); r3.pack(fill='x', padx=10)
        for level, lab in (('FULL', 'VOLL'), ('REDUCED', 'REDUZIERT'), ('OFF', 'AUS')):
            action_button(self, r3, lab, lambda v=level: self._pph6_anim.set_level(v), PURPLE).pack(side='left', fill='x', expand=True, padx=3)

        self.p6_ver = tk.StringVar(value=f'AKTUELL: {_current_version()}')
        row_label('UPDATES')
        r4 = tk.Frame(box, bg=PANEL); r4.pack(fill='x', padx=14, pady=(0, 6))
        tk.Label(r4, textvariable=self.p6_ver, bg=PANEL, fg=TEXT, font=font(self, 9)).pack(anchor='w')
        r5 = tk.Frame(box, bg=PANEL); r5.pack(fill='x', padx=10, pady=(0, 12))
        action_button(self, r5, 'CHECK UPDATES', lambda: self._pph28_open_update(), CYAN).pack(side='left', fill='x', expand=True, padx=3)
        action_button(self, r5, 'DISPLAY OFF', lambda: self.sleep_display(), BLUE).pack(side='left', fill='x', expand=True, padx=3)
        wire_swipe(self, content, 'settings3', None)
        self._pph6_refresh['settings_detail'] = lambda: None

    def build_field(self):
        page, content, svar, badge = page_shell(self, 'field50', 'CUSTOMER MODE', 'FIELD MODE', 'access3', 'READY', 'ready')
        self.p6_field_state = tk.StringVar(value='FIELD READY')
        hero = card(self, content, 'STATUS', self.p6_field_state, GREEN)
        hero.pack(fill='both', expand=True, padx=14, pady=8)
        action_row(self, page, [
            ('CONNECTION FLOW', lambda: self.show_page('flow50'), CYAN),
            ('BEFORE / AFTER', lambda: self.show_page('compare50'), ORANGE),
            ('SESSION', lambda: self.show_page('session50'), PURPLE),
        ])
        self._pph6_refresh['field50'] = lambda: None

    def build_before_after(self):
        page, content, svar, badge = page_shell(self, 'compare50', 'CUSTOMER MODE', 'BEFORE / AFTER', 'access3', 'READY', 'ready', back_to='field50')
        self.p6_before = tk.StringVar(value='NOT SET'); self.p6_after = tk.StringVar(value='NOT SET')
        self.p6_delta = tk.StringVar(value='Zwei Messungen erforderlich')
        two_cards(self, content, card(self, content, 'BEFORE', self.p6_before, ORANGE, self.p6_delta),
                  card(self, content, 'AFTER', self.p6_after, GREEN, self.p6_delta))
        action_row(self, page, [('SAVE BEFORE', lambda: capture(self, 'before'), ORANGE), ('SAVE AFTER', lambda: capture(self, 'after'), GREEN)])
        self._pph6_refresh['compare50'] = lambda: None

    def build_session(self):
        page, content, svar, badge = page_shell(self, 'session50', 'CUSTOMER MODE', 'SESSION RECORDER', 'access3', 'STOPPED', 'offline', back_to='field50')
        self.p6_sess_state = tk.StringVar(value='● STOPPED'); self.p6_sess_time = tk.StringVar(value='00:00:00')
        hero = tk.Frame(content, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        hero.pack(fill='both', expand=True, padx=14, pady=8)
        tk.Label(hero, textvariable=self.p6_sess_state, bg=PANEL, fg=RED, font=font(self, 16, 'bold')).pack(pady=(20, 4))
        tk.Label(hero, textvariable=self.p6_sess_time, bg=PANEL, fg=TEXT, font=font(self, 30, 'bold')).pack()
        action_row(self, page, [('START', lambda: session_start(self), GREEN), ('STOP & SAVE', lambda: session_stop(self), RED)])
        self._pph6_refresh['session50'] = lambda: None

    def build_generic(self, name, title, kicker='PPH 6'):
        page, content, svar, badge = page_shell(self, name, kicker, title, 'system3', 'READY', 'ready', back_to='more6')
        t = tk.Text(content, bg=PANEL, fg=TEXT, insertbackground=TEXT, relief='flat', bd=0,
                    highlightthickness=1, highlightbackground=BORDER, font=font(self, 10), wrap='word', padx=12, pady=10)
        t.pack(fill='both', expand=True, padx=12, pady=6)
        setattr(self, 'p6_txt_' + name, t)

        def refresh():
            if name == 'tools':
                txt = 'NETWORK DOCTOR\nLAN MAPPER\nCONNECTION FLOW\nDIAGNOSTIC SNAPSHOT'
            elif name == 'lan_mapper':
                txt = run(['ip', 'neigh'])
            elif name == 'reports':
                try: st = self._read_measurement_state()
                except Exception: st = {}
                txt = 'LETZTER MESSSTATUS\n\n' + '\n'.join(f'{k}: {v}' for k, v in (st or {}).items())
            elif name == 'jobs3':
                try: rows = jobs.list_jobs(limit=10) if jobs else []
                except Exception: rows = []
                txt = '\n'.join(str(r.get('title') or r) for r in rows) or 'Keine Jobs'
            else:
                txt = f'{title}\n\nPPH 6 Field System'
            t.configure(state='normal'); t.delete('1.0', 'end'); t.insert('end', txt or 'Keine Daten'); t.configure(state='disabled')
        self._pph6_refresh[name] = refresh

    # =====================================================================
    # actions / helpers bound to pages
    # =====================================================================

    def _ensure_ap(self):
        if getattr(self, 'pph31_ap', None) is not None:
            return self.pph31_ap
        try:
            from access_point import AccessPointController
            self.pph31_ap = AccessPointController()
        except Exception:
            self.pph31_ap = None
        return self.pph31_ap

    def ap_start(self):
        notify(self, 'Access Point startet …', 'info')
        ap = _ensure_ap(self)
        import threading
        def worker():
            try:
                if ap: ap.start()
                err = None
            except Exception as exc:
                err = exc
            def done():
                if err: notify(self, f'Start fehlgeschlagen: {err}', 'error')
                else: notify(self, 'Access Point gestartet', 'ok')
                self._pph6_refresh.get('access3', lambda: None)()
            try: self.root.after(0, done)
            except Exception: pass
        threading.Thread(target=worker, daemon=True).start()

    def ap_stop(self):
        ap = _ensure_ap(self)
        try:
            if ap: ap.stop()
            notify(self, 'Access Point gestoppt', 'warn')
        except Exception as exc:
            notify(self, str(exc), 'error')
        self._pph6_refresh.get('access3', lambda: None)()

    def run_doctor(self):
        route = run(['ip', 'route', 'show', 'default'])
        eth_ok = bool(route)
        gw = ''
        try: gw = route.split('via ', 1)[1].split()[0] if 'via ' in route else ''
        except Exception: pass
        gw_ok = bool(gw) and run(['ping', '-c', '1', '-W', '1', gw]) != ''
        dns_ok = False
        try:
            import socket; socket.gethostbyname('github.com'); dns_ok = True
        except Exception: dns_ok = False
        inet_ok = run(['ping', '-c', '1', '-W', '1', '1.1.1.1']) != ''
        results = {'eth': eth_ok, 'gw': gw_ok, 'dns': dns_ok, 'inet': inet_ok}
        for key, ok in results.items():
            self.p6_doc[key].set('OK' if ok else 'FAIL')
            row = self.p6_doc_row.get(key)
            if row is not None:
                try: row._pph6_set_kind('ready' if ok else 'error')
                except Exception: pass
        all_ok = eth_ok and gw_ok and dns_ok and inet_ok
        self.p6_doc_result.set('ALLE PRÜFUNGEN OK' if all_ok else 'PROBLEM ERKANNT')
        try: self.p6_doc_result_lbl.configure(fg=(GREEN if all_ok else YELLOW))
        except Exception: pass
        self._pph6_doctor_rows = [('ETHERNET', eth_ok), ('GATEWAY', gw_ok), ('DNS', dns_ok), ('INTERNET', inet_ok)]
        if not all_ok:
            notify(self, 'Netzwerkproblem erkannt', 'warn')

    def show_doctor_overlay(self):
        rows = getattr(self, '_pph6_doctor_rows', [])
        overlay(self, 'NETWORK ERROR', 'Ein oder mehrere Prüfungen sind fehlgeschlagen.', rows=rows,
                      buttons=[('RETRY', lambda: run_doctor(self), CYAN), ('CLOSE', lambda: None, PANEL2)])

    def capture(self, which):
        try: st = self._read_measurement_state()
        except Exception: st = {}
        val = _first(st.get('download_mbps'), st.get('throughput_mbps'))
        setattr(self, f'_pph6_{which}', val if isinstance(val, (int, float)) else None)
        var = self.p6_before if which == 'before' else self.p6_after
        var.set(f'{float(val):.0f} Mbit/s' if isinstance(val, (int, float)) else 'SAVED')
        b = getattr(self, '_pph6_before', None); a = getattr(self, '_pph6_after', None)
        if isinstance(b, (int, float)) and isinstance(a, (int, float)):
            self.p6_delta.set(f'{a - b:+.0f} Mbit/s')

    def session_start(self):
        import time as _t
        self._pph6_session = {'start': _t.time()}
        self.p6_sess_state.set('● RECORDING')
        def tick():
            elapsed = int(_t.time() - self._pph6_session['start'])
            self.p6_sess_time.set(f'{elapsed//3600:02d}:{(elapsed%3600)//60:02d}:{elapsed%60:02d}')
        self._pph6_anim.loop('session50:tick', 1000, tick)

    def session_stop(self):
        self._pph6_anim.cancel('session50:tick')
        self.p6_sess_state.set('SESSION SAVED')
        notify(self, 'Session gespeichert', 'ok')

    # =====================================================================
    # boot sequence
    # =====================================================================

    def play_boot(self, on_done):
        overlay = tk.Frame(self.root, bg=BG)
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        tk.Label(overlay, text='PPH', bg=BG, fg=CYAN, font=font(self, 34, 'bold')).pack(pady=(90, 0))
        tk.Label(overlay, text='PORTABLE PERFORMANCE HUB', bg=BG, fg=MUTED, font=font(self, 10, 'bold')).pack()
        rows = tk.Frame(overlay, bg=BG); rows.pack(pady=30)
        checks = ['DISPLAY', 'SYSTEM', 'NETWORK', 'RADIOS', 'FIELD SERVICES']
        labels = {}
        for c in checks:
            r = tk.Frame(rows, bg=BG); r.pack(fill='x', pady=3)
            tk.Label(r, text=c, bg=BG, fg=TEXT, font=font(self, 10, 'bold'), width=18, anchor='w').pack(side='left')
            v = tk.Label(r, text='…', bg=BG, fg=MUTED, font=font(self, 10, 'bold')); v.pack(side='left')
            labels[c] = v
        state = {'i': 0}
        def step():
            if state['i'] >= len(checks):
                def finish():
                    try: overlay.destroy()
                    except Exception: pass
                    on_done()
                self._pph6_anim.after('boot:finish', 250, finish)
                return
            c = checks[state['i']]
            labels[c].configure(text='✓', fg=GREEN)
            state['i'] += 1
            self._pph6_anim.after('boot:step', 180, step)
        self._pph6_anim.after('boot:step', 180, step)

    # =====================================================================
    # wiring
    # =====================================================================

    def build_pages(self):
        build_home(self); build_more(self)
        build_wireless(self); build_wireless_detail(self)
        build_radio_center(self); build_radio_detail(self)
        build_network(self); build_network_detail(self)
        build_access(self); build_access_detail(self)
        build_connection_flow(self)
        build_network_doctor(self)
        build_system(self); build_system_detail(self)
        build_hardware(self); build_storage(self)
        build_events(self); build_events_raw(self)
        build_settings(self); build_settings_detail(self)
        build_field(self); build_before_after(self); build_session(self)
        for name, title in (('tools', 'TOOLS'), ('lan_mapper', 'LAN MAPPER'), ('reports', 'REPORTS'),
                             ('jobs3', 'JOBS'), ('notify50', 'NOTIFICATIONS')):
            build_generic(self, name, title)

        if not self._pph6_booted:
            self._pph6_booted = True
            def enter_home():
                self.show_page('home3', push=False)
            play_boot(self, enter_home)

    def show_page(self, name, title=None, *, push=True):
        aliases = {'dashboard': 'home3', 'home412': 'home3', 'home411': 'home3', 'home41': 'home3', 'home32': 'home3',
                   'access41': 'access3', 'access411': 'access3', 'access412': 'access3',
                   'analyzer41': 'network', 'analyzer32': 'network', 'network412': 'network', 'network412b': 'network',
                   'wireless4': 'measure3', 'wireless41': 'measure3', 'wireless411': 'measure3', 'wireless412': 'measure3',
                   'wireless412b': 'measure3', 'doctor32': 'network_doctor', 'quick32': 'network_doctor', 'wifi32': 'wifi3'}
        name = aliases.get(name, name)
        old_name = getattr(self, 'current_page', None)
        new_frame = self.frames.get(name)
        if new_frame is None:
            return
        old_frame = self.frames.get(old_name) if old_name else None
        if old_name and old_name != name:
            self._pph6_anim.cancel_page(old_name)
        self.current_page = name
        self.page_title.set(self.page_titles.get(name, name.upper()))
        set_active_nav(self, self._pph6_nav_map.get(name, name))

        def finalize():
            for w in self.frames.values():
                if w is not new_frame:
                    w.place_forget()
            new_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            new_frame.lift()

        if old_frame is None or old_frame is new_frame or not self.frames:
            finalize()
        else:
            direction = 1
            def frame(t):
                try:
                    old_frame.place(relx=0, rely=0, relwidth=1, relheight=1, x=int(-W * t * direction))
                    new_frame.place(relx=0, rely=0, relwidth=1, relheight=1, x=int(W * direction * (1 - t)))
                    new_frame.lift()
                except Exception:
                    pass
            self._pph6_anim.tween('nav:transition', 180, frame, on_done=finalize, tier='REDUCED')

        refresher = self._pph6_refresh.get(name)
        if refresher:
            try: refresher()
            except Exception: pass
        try:
            self._pph29_trigger_update_check(False, f'page:{name}')
        except Exception:
            pass

    def go_home(self):
        self.show_page('home3', push=False)

    def toggle_fullscreen(self):
        pass

    if not hasattr(cls, 'go_home'):
        pass

    cls._build_shell = build_shell
    cls._build_pages = build_pages
    cls.show_page = show_page
    cls.go_home = go_home
    cls.toggle_fullscreen = toggle_fullscreen
