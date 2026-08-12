#!/usr/bin/env python3
from __future__ import annotations
import math, subprocess, time, tkinter as tk
from typing import Any

# ---------------------------------------------------------------------------
# PPH 7.1 - "Pulse Deck" UI/UX for the 800x480 / 5-inch Pi touch UI.
# Same authoritative-single-layer architecture as 6.x (older UI modules still
# get installed for their backend side effects but never build a page), same
# backend hooks (measurement engine, AccessPointController, hardware_roles,
# update checker). Everything about how it LOOKS and MOVES is new: canvas-
# drawn glyph icons and nav, glowing rounded "holo" cards, animated signal
# bars, live sparkline graphs, a sliding nav indicator, a radar-sweep boot
# sequence, and richer per-widget motion - all built from primitives
# (rectangles/arcs/lines/polygons/color-lerp) that stay cheap to redraw, per
# the same performance discipline 6.x settled on: draw static art once, only
# animate StringVars/color and cancel every loop the instant a page is left.
# ---------------------------------------------------------------------------

BG = '#07100E'; SURFACE = '#111A17'; SURFACE2 = '#1A2521'; BORDER = '#314139'
TEXT = '#F7FAF5'; MUTED = '#9AA79E'
CYAN = '#4FE3C1'; GREEN = '#A6F06A'; YELLOW = '#F6D55C'; ORANGE = '#FF8A4C'
RED = '#FF5B66'; PURPLE = '#CE87FF'; BLUE = '#62B6FF'
INK = '#030706'; RAIL = '#0B1310'

CHIP = {
    'ready': (SURFACE2, GREEN), 'live': (SURFACE2, CYAN), 'offline': (SURFACE2, MUTED),
    'warn': (SURFACE2, YELLOW), 'error': (SURFACE2, RED), 'active': (SURFACE2, GREEN),
}

W, H = 800, 480
HEADER_H = 56
NAV_H = 80
ACTION_H = 62

LIVE_PAGES = {
    'home3': 2000, 'measure3': 1000, 'measure3_detail': 1200,
    'wifi3': 3000, 'radio_detail': 2000,
    'network': 1200, 'network_detail': 1200,
    'access3': 1000, 'access_detail': 1200, 'access_detail2': 1200,
    'system3': 2000, 'system_detail': 3000,
    'hardware': 4000, 'storage': 5000,
    'events3': 4000,
}


def run(args: list[str], timeout: float = 3) -> str:
    try:
        p = subprocess.run(args, text=True, capture_output=True, timeout=timeout, check=False)
        return (p.stdout or p.stderr or '').strip()
    except Exception:
        return ''


def _first(*vals):
    for v in vals:
        if v is not None:
            return v
    return None


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


def _lerp_color(a: str, b: str, t: float) -> str:
    t = max(0.0, min(1.0, t))
    a = a.lstrip('#'); b = b.lstrip('#')
    ar, ag, ab = int(a[0:2], 16), int(a[2:4], 16), int(a[4:6], 16)
    br, bg, bb = int(b[0:2], 16), int(b[2:4], 16), int(b[4:6], 16)
    r = int(ar + (br - ar) * t); g = int(ag + (bg - ag) * t); c = int(ab + (bb - ab) * t)
    return f'#{max(0,min(255,r)):02x}{max(0,min(255,g)):02x}{max(0,min(255,c)):02x}'


# =========================================================================
# Canvas drawing primitives - static art, drawn once per widget build.
# =========================================================================

def rounded_rect(canvas, x1, y1, x2, y2, r, **kw):
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(pts, smooth=True, **kw)


def deck_background(canvas, w, h):
    canvas.delete('deckbg')
    canvas.create_rectangle(0, 0, w, h, fill=BG, outline='', tags='deckbg')
    for x in range(-40, w + 80, 80):
        canvas.create_line(x, 0, x + 130, h, fill='#102019', width=1, tags='deckbg')
    for y in range(42, h, 58):
        canvas.create_line(0, y, w, y, fill='#0E1B17', width=1, tags='deckbg')
    canvas.create_rectangle(0, 0, w, 7, fill=CYAN, outline='', tags='deckbg')
    canvas.create_rectangle(0, h - 7, w, h, fill=GREEN, outline='', tags='deckbg')


def glyph_home(canvas, cx, cy, s, color):
    canvas.create_polygon(cx - s, cy, cx, cy - s * 0.9, cx + s, cy, fill=color, outline='')
    canvas.create_rectangle(cx - s * 0.62, cy, cx + s * 0.62, cy + s * 0.78, fill=color, outline='')
    canvas.create_rectangle(cx - s * 0.62, cy, cx + s * 0.62, cy + s * 0.78, fill=BG, outline='', width=0) if False else None
    canvas.create_rectangle(cx - s * 0.2, cy + s * 0.24, cx + s * 0.2, cy + s * 0.78, fill=BG, outline='')


def glyph_wifi(canvas, cx, cy, s, color, level=3):
    canvas.create_oval(cx - s * 0.14, cy + s * 0.5, cx + s * 0.14, cy + s * 0.78, fill=color, outline='')
    for i in range(3):
        rad = s * (0.35 + i * 0.32)
        w = max(1, int(s * 0.14))
        fill = color if level > i else BORDER
        canvas.create_arc(cx - rad, cy - rad * 0.2, cx + rad, cy + rad * 1.5,
                           start=35, extent=110, style='arc', outline=fill, width=w)


def glyph_network(canvas, cx, cy, s, color):
    pts = [(cx, cy - s * 0.75), (cx - s * 0.75, cy + s * 0.5), (cx + s * 0.75, cy + s * 0.5)]
    for x1, y1 in pts:
        for x2, y2 in pts:
            if (x1, y1) < (x2, y2):
                canvas.create_line(x1, y1, x2, y2, fill=color, width=max(1, int(s * 0.1)))
    for x, y in pts:
        r = s * 0.16
        canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline=BG, width=1)


def glyph_access(canvas, cx, cy, s, color):
    canvas.create_rectangle(cx - s * 0.7, cy + s * 0.25, cx + s * 0.7, cy + s * 0.6, fill=color, outline='')
    canvas.create_line(cx - s * 0.25, cy + s * 0.25, cx - s * 0.5, cy - s * 0.7, fill=color, width=max(1, int(s * 0.12)))
    canvas.create_line(cx + s * 0.25, cy + s * 0.25, cx + s * 0.5, cy - s * 0.7, fill=color, width=max(1, int(s * 0.12)))
    for dx in (-0.5, 0.5):
        canvas.create_oval(cx + dx * s - s * 0.09, cy - s * 0.7 - s * 0.09, cx + dx * s + s * 0.09, cy - s * 0.7 + s * 0.09, fill=color, outline='')


def glyph_system(canvas, cx, cy, s, color):
    rounded_rect(canvas, cx - s * 0.55, cy - s * 0.55, cx + s * 0.55, cy + s * 0.55, s * 0.14, fill='', outline=color, width=max(1, int(s * 0.12)))
    canvas.create_rectangle(cx - s * 0.2, cy - s * 0.2, cx + s * 0.2, cy + s * 0.2, fill=color, outline='')
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        x1 = cx + dx * s * 0.55; y1 = cy + dy * s * 0.55
        x2 = cx + dx * s * 0.85; y2 = cy + dy * s * 0.85
        canvas.create_line(x1, y1, x2, y2, fill=color, width=max(1, int(s * 0.12)))


NAV_GLYPHS = {'home3': glyph_home, 'measure3': glyph_wifi, 'network': glyph_network,
              'access3': glyph_access, 'system3': glyph_system}


def signal_bars(canvas, x, y, color, filled=3, count=4, bw=7, gap=3, h=20, muted=BORDER):
    for i in range(count):
        bh = h * (i + 1) / count
        bx = x + i * (bw + gap)
        by = y + h - bh
        fill = color if i < filled else muted
        canvas.create_rectangle(bx, by, bx + bw, y + h, fill=fill, outline='')


def glyph_check(canvas, cx, cy, s, color):
    canvas.create_line(cx - s * 0.5, cy, cx - s * 0.12, cy + s * 0.4, cx + s * 0.55, cy - s * 0.45,
                        fill=color, width=max(2, int(s * 0.22)), capstyle='round', joinstyle='round')


def glyph_cross(canvas, cx, cy, s, color):
    canvas.create_line(cx - s * 0.4, cy - s * 0.4, cx + s * 0.4, cy + s * 0.4, fill=color, width=max(2, int(s * 0.2)), capstyle='round')
    canvas.create_line(cx - s * 0.4, cy + s * 0.4, cx + s * 0.4, cy - s * 0.4, fill=color, width=max(2, int(s * 0.2)), capstyle='round')


def sparkline(canvas, values, color, pad=4):
    # place()'d canvases resolve their real width/height asynchronously via
    # idle tasks, so a draw triggered synchronously from refresh() can still
    # see stale (near-zero) geometry. Store the latest values on the canvas
    # and also redraw on <Configure>, so once Tk actually resolves the real
    # size the graph redraws correctly - same fix as progress_bar's _set().
    canvas._pph7_values = values
    def redraw(_e=None):
        canvas.delete('spark')
        w = max(1, canvas.winfo_width()); h = max(1, canvas.winfo_height())
        vals = [v for v in canvas._pph7_values if isinstance(v, (int, float))]
        if len(vals) < 2:
            return
        lo, hi = min(vals), max(vals)
        if hi - lo < 1e-6: hi = lo + 1
        n = len(canvas._pph7_values)
        pts = []
        for i, v in enumerate(canvas._pph7_values):
            vv = v if isinstance(v, (int, float)) else lo
            x = pad + (w - 2 * pad) * i / max(1, n - 1)
            y = h - pad - (h - 2 * pad) * (vv - lo) / (hi - lo)
            pts.extend((x, y))
        if len(pts) >= 4:
            fill_pts = [pad, h - pad] + pts + [w - pad, h - pad]
            canvas.create_polygon(fill_pts, fill=_lerp_color(BG, color, 0.18), outline='', tags='spark')
            canvas.create_line(*pts, fill=color, width=2, smooth=True, tags='spark')
    if not getattr(canvas, '_pph7_spark_bound', False):
        canvas.bind('<Configure>', redraw, add='+')
        canvas._pph7_spark_bound = True
    redraw()


# =========================================================================
# Animation manager
# =========================================================================
class Anim:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.level = 'FULL'
        self._tok: dict[str, str] = {}

    def set_level(self, level: str) -> None:
        self.level = level if level in ('FULL', 'REDUCED', 'OFF') else 'FULL'

    def enabled(self, tier: str = 'FULL') -> bool:
        if tier == 'ESSENTIAL': return True
        if self.level == 'OFF': return False
        if self.level == 'REDUCED': return tier == 'REDUCED'
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
            if tag not in self._tok: return
            try: fn()
            except Exception: pass
            if tag in self._tok:
                self._tok[tag] = self.root.after(ms, tick)
        self._tok[tag] = self.root.after(ms, tick)

    def tween(self, tag: str, ms: int, on_frame, on_done=None, tier: str = 'FULL', fps: int = 40, ease='out'):
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
        def curve(t):
            if ease == 'out': return 1 - (1 - t) * (1 - t)
            if ease == 'inout': return t * t * (3 - 2 * t)
            if ease == 'back':
                c = 1.70158
                return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2
            return t
        def tick():
            t = min(1.0, (time.monotonic() - start) * 1000 / max(1, ms))
            try: on_frame(curve(t))
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
    health = ns.get('_pph28_health'); jobs = ns.get('_pph28_jobs'); events = ns.get('_pph28_events')

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
        if not hasattr(self, 'back_button'): self.back_button = tk.Button(self.root)
        self.frames = {}; self.pages = self.frames; self.page_titles = {}
        self._pph7_anim = Anim(self.root)
        self._pph7_prev = {}
        self._pph7_refresh = {}
        self._pph7_notify_stack = []
        self._pph7_radio_sel = 'measurement'
        self._pph7_booted = False
        self._pph7_nav_map = {}
        self._pph7_history = {}

        self.pph7_bg = tk.Canvas(self.content, bg=BG, highlightthickness=0)
        self.pph7_bg.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.pph7_bg.bind('<Configure>', lambda e: deck_background(self.pph7_bg, e.width, e.height), add='+')

        nav = tk.Frame(self.content, bg=RAIL, height=NAV_H, highlightthickness=1, highlightbackground=BORDER)
        nav.pack(side='bottom', fill='x'); nav.pack_propagate(False)
        ind = tk.Canvas(nav, bg=RAIL, width=W, height=6, highlightthickness=0)
        ind.place(relx=0, rely=0, relwidth=1, height=6)
        self.pph7_nav_indicator = ind
        items = [('HOME', 'home3'), ('WLAN', 'measure3'), ('NETZ', 'network'), ('ACCESS', 'access3'), ('SYSTEM', 'system3')]
        self.pph7_nav_buttons = {}
        row = tk.Frame(nav, bg=RAIL); row.pack(fill='both', expand=True, pady=(8, 4))
        for i, (lab, target) in enumerate(items):
            row.grid_columnconfigure(i, weight=1, uniform='nav7')
            cell = tk.Frame(row, bg=RAIL, cursor='hand2')
            cell.grid(row=0, column=i, sticky='nsew')
            c = tk.Canvas(cell, bg=RAIL, width=34, height=34, highlightthickness=0)
            c.pack(pady=(2, 0))
            glyph = NAV_GLYPHS[target]
            glyph(c, 17, 17, 12, TEXT)
            lbl = tk.Label(cell, text=lab, bg=RAIL, fg=TEXT, font=font(self, 9, 'bold'))
            lbl.pack(pady=(2, 0))
            for w in (cell, c, lbl):
                w.bind('<Button-1>', lambda _e, t=target: self.show_page(t), add='+')
            self.pph7_nav_buttons[target] = (cell, c, lbl, glyph)
        self._pph7_nav_active_x = 0.0

        self.pph7_page_area = tk.Frame(self.content, bg=BG)
        self.pph7_page_area.pack(fill='both', expand=True)
        self.pph7_page_area.lift()
        nav.lift()

    def set_active_nav(self, key):
        items = ['home3', 'measure3', 'network', 'access3', 'system3']
        if key not in items:
            return
        idx = items.index(key)
        n = len(items)
        for i, target in enumerate(items):
            cell, c, lbl, glyph = self.pph7_nav_buttons[target]
            selected = (target == key)
            color = CYAN if selected else MUTED
            c.delete('all')
            glyph(c, 17, 17, 12, color)
            lbl.configure(fg=(TEXT if selected else MUTED), font=font(self, 9, 'bold' if selected else 'normal'))
        target_x = (idx + 0.5) / n
        def frame(t):
            cur = self._pph7_nav_active_x + (target_x - self._pph7_nav_active_x) * t
            self.pph7_nav_indicator.delete('all')
            w = max(1, self.pph7_nav_indicator.winfo_width())
            cx = cur * w
            pillw = w / n * 0.5
            rounded_rect(self.pph7_nav_indicator, cx - pillw / 2, 0, cx + pillw / 2, 6, 3, fill=CYAN, outline='')
            if t >= 0.999:
                self._pph7_nav_active_x = target_x
        self._pph7_anim.tween('nav:indicator', 220, frame, tier='REDUCED', ease='out')

    # --------------------------------------------------------- primitives --
    def font(self, size: int, weight: str = 'bold'):
        try: return self._font(size, weight)
        except Exception: return ('TkDefaultFont', size, weight)

    def new_page(self, name: str) -> tk.Frame:
        old = self.frames.get(name)
        if old is not None:
            try: old.destroy()
            except Exception: pass
        frame = tk.Frame(self.pph7_page_area, bg=BG)
        self.frames[name] = frame
        self.page_titles[name] = name
        return frame

    def header(self, page, kicker, title, status_text='READY', status_kind='ready', back_to=None):
        h = tk.Frame(page, bg=BG, height=HEADER_H); h.pack(fill='x', padx=14, pady=(8, 2)); h.pack_propagate(False)
        left = tk.Frame(h, bg=BG); left.pack(side='left', fill='y')
        if back_to:
            bc = tk.Canvas(left, width=34, height=34, bg=PANEL2 if False else SURFACE2, highlightthickness=1, highlightbackground=BORDER, cursor='hand2')
            bc.pack(side='left', padx=(0, 10))
            bc.create_line(20, 9, 12, 17, 20, 25, fill=TEXT, width=3, capstyle='round', joinstyle='round')
            bc.bind('<Button-1>', lambda _e, t=back_to: self.show_page(t), add='+')
        textcol = tk.Frame(left, bg=BG); textcol.pack(side='left', fill='y')
        tk.Label(textcol, text=kicker, bg=BG, fg=GREEN, font=font(self, 9, 'bold')).pack(anchor='w')
        tk.Label(textcol, text=title, bg=BG, fg=TEXT, font=font(self, 17, 'bold')).pack(anchor='w')
        right = tk.Frame(h, bg=BG); right.pack(side='right', fill='y', pady=4)
        svar = tk.StringVar(value=status_text)
        bg, fg = CHIP.get(status_kind, CHIP['ready'])
        badge = tk.Label(right, textvariable=svar, bg=bg, fg=fg, font=font(self, 9, 'bold'), padx=10, pady=6)
        badge.pack(side='right', padx=(6, 0))
        vc = tk.Button(right, text=f'v{_current_version()}', command=lambda: self._pph28_open_update(),
                        bg=SURFACE2, fg=CYAN, activebackground=CYAN, activeforeground=BG, relief='flat', bd=0,
                        highlightthickness=1, highlightbackground=BORDER, font=font(self, 8, 'bold'), padx=8, pady=6, cursor='hand2')
        vc.pack(side='right')
        return svar, badge

    def status_pulse(self, page_name, badge, base_kind):
        def tick():
            on = getattr(badge, '_pph7_on', False); badge._pph7_on = not on
            _, fg = CHIP[base_kind]
            try: badge.configure(fg=(CYAN if on else fg))
            except Exception: pass
        self._pph7_anim.loop(f'{page_name}:chip', 850, tick)

    def holo_card(self, parent, title, value_var, accent=CYAN, detail_var=None, glow=False, icon=None, w=360, h=150):
        outer = tk.Frame(parent, bg=BG)
        # Fixed width/height at construction time: without this, a canvas
        # that draws content sized from its own winfo_width()/height() (see
        # build() below) can feed back into its own geometry request under
        # pack(fill=both,expand=True), inflating it and starving sibling
        # widgets (e.g. the action row below it) of space they were promised.
        c = tk.Canvas(outer, bg=BG, highlightthickness=0, width=w, height=h)
        c.pack(fill='both', expand=True)
        state = {'built': False}
        def build(_e=None):
            c.delete('bg')
            cw = max(w, c.winfo_width()); ch = max(h, c.winfo_height())
            if glow:
                for i, t in enumerate((0.9, 0.72, 0.5, 0.22)):
                    pad = (4 - i) * 3
                    rounded_rect(c, 2 - pad, 2 - pad, cw - 2 + pad, ch - 2 + pad, 16 + pad,
                                 fill=_lerp_color(BG, accent, 1 - t), outline='', tags='bg')
            rounded_rect(c, 2, 2, cw - 2, ch - 2, 8, fill=SURFACE, outline=BORDER, width=1, tags='bg')
            c.create_rectangle(2, 2, cw - 2, 7, fill=accent, outline='', tags='bg')
            c.create_line(16, ch - 18, cw - 16, ch - 18, fill='#26352F', width=1, tags='bg')
            c.tag_lower('bg')
            if not state['built']:
                iy = 20
                if icon:
                    ic = tk.Canvas(outer, width=26, height=26, bg=SURFACE, highlightthickness=0)
                    ic_win = c.create_window(cw - 30, 26, window=ic)
                    icon(ic, 13, 13, 10, accent)
                tk.Label(outer, text=title, bg=SURFACE, fg=MUTED, font=font(self, 9, 'bold')).place(x=20, y=16)
                vlbl = tk.Label(outer, textvariable=value_var, bg=SURFACE, fg=accent, font=font(self, 25, 'bold'), wraplength=w - 40, justify='left')
                vlbl.place(x=18, y=42)
                if detail_var is not None:
                    tk.Label(outer, textvariable=detail_var, bg=SURFACE, fg=TEXT, font=font(self, 10), wraplength=w - 40, justify='left').place(x=20, y=ch - 34)
                state['built'] = True
        c.bind('<Configure>', build, add='+')
        outer._pph7_canvas = c
        return outer

    def two_cards(self, content, left, right):
        row = tk.Frame(content, bg=BG); row.pack(fill='both', expand=True, padx=12, pady=8)
        left.pack(in_=row, side='left', fill='both', expand=True, padx=(0, 6))
        right.pack(in_=row, side='left', fill='both', expand=True, padx=(6, 0))
        left.lift(); right.lift()
        return row

    def action_button(self, parent, text, command, accent=CYAN, danger=False):
        c = tk.Canvas(parent, bg=BG, highlightthickness=0, width=120, height=ACTION_H)
        state = {'w': 0, 'h': 0}
        def draw(pressed=False):
            c.delete('all')
            w = max(1, c.winfo_width()); h = max(1, c.winfo_height())
            col = (RED if danger else accent) if pressed else SURFACE2
            rounded_rect(c, 2, 2, w - 2, h - 2, 8, fill=col, outline=BORDER, width=1)
            c.create_rectangle(10, 7, w - 10, 10, fill=(BG if pressed else accent), outline='')
            c.create_text(w / 2, h / 2, text=text, fill=(BG if pressed else TEXT), font=font(self, 12, 'bold'))
        c.bind('<Configure>', lambda _e: draw(False), add='+')
        def ripple(x, y):
            if not self._pph7_anim.enabled('REDUCED'): return
            rid = c.create_oval(x, y, x, y, fill=_lerp_color(SURFACE2, (RED if danger else accent), 0.5), outline='')
            def frame(t):
                r = t * 70
                try: c.coords(rid, x - r, y - r, x + r, y + r)
                except Exception: pass
                try: c.itemconfigure(rid, stipple='gray50' if t > 0.5 else '')
                except Exception: pass
            def done():
                try: c.delete(rid)
                except Exception: pass
            self._pph7_anim.tween(f'ripple:{id(c)}', 260, frame, on_done=done, tier='REDUCED')
        def press(e):
            draw(True); ripple(e.x, e.y)
        def release(e):
            def reset(): draw(False)
            self._pph7_anim.after(f'btn:{id(c)}', 90, reset)
        def click(e):
            try: command()
            except Exception: pass
        c.bind('<ButtonPress-1>', press, add='+')
        c.bind('<ButtonRelease-1>', lambda e: (release(e), click(e)), add='+')
        return c

    def action_row(self, content, items):
        r = tk.Frame(content, bg=BG, height=ACTION_H); r.pack(side='bottom', fill='x', padx=12, pady=(0, 10)); r.pack_propagate(False)
        for label, cmd, accent in items[:3]:
            action_button(self, r, label, cmd, accent, danger=(label in ('STOP', 'RESET'))).pack(side='left', fill='both', expand=True, padx=4)
        return r

    def list_row(self, parent, label, status_var, kind='ready', on_tap=None):
        row = tk.Frame(parent, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER, cursor='hand2' if on_tap else 'arrow')
        c = tk.Canvas(row, width=26, height=26, bg=SURFACE, highlightthickness=0)
        c.pack(side='left', padx=(12, 6), pady=6)
        body = tk.Frame(row, bg=SURFACE); body.pack(side='left', fill='both', expand=True, padx=(0, 12), pady=6)
        tk.Label(body, text=label, bg=SURFACE, fg=TEXT, font=font(self, 11, 'bold'), anchor='w').pack(fill='x')
        _, fg0 = CHIP.get(kind, CHIP['ready'])
        status_lbl = tk.Label(body, textvariable=status_var, bg=SURFACE, fg=fg0, font=font(self, 9, 'bold'), anchor='w')
        status_lbl.pack(fill='x')
        def set_kind(k):
            _, kfg = CHIP.get(k, CHIP['ready'])
            c.delete('all')
            if k in ('ready', 'active'):
                glyph_check(c, 13, 13, 10, kfg)
            elif k == 'error':
                glyph_cross(c, 13, 13, 10, kfg)
            else:
                c.create_oval(7, 7, 19, 19, outline=kfg, width=2)
            try: status_lbl.configure(fg=kfg)
            except Exception: pass
        row._pph7_set_kind = set_kind
        set_kind(kind)
        if on_tap:
            for w in (row, body, c):
                w.bind('<Button-1>', lambda _e, f=on_tap: f(), add='+')
        return row

    def progress_bar(self, parent, accent=CYAN, height=14):
        c = tk.Canvas(parent, bg=SURFACE2, width=200, height=height, highlightthickness=0)
        state = {'pct': 0}
        def redraw(_e=None):
            c.delete('all')
            w = max(1, c.winfo_width())
            rounded_rect(c, 0, 0, w, height, height / 2, fill=SURFACE2, outline='')
            fw = w * max(0, min(100, state['pct'])) / 100
            if fw > 1:
                rounded_rect(c, 0, 0, fw, height, height / 2, fill=accent, outline='')
        def set_pct(pct):
            state['pct'] = pct; redraw()
        c._pph7_set = set_pct
        c.bind('<Configure>', redraw, add='+')
        return c

    def indeterminate(self, canvas, page_name, tag='scan'):
        state = {'x': 0.0}
        def tick():
            w = max(1, canvas.winfo_width()); seg = max(30, int(w * 0.22)); ht = int(canvas['height'])
            state['x'] = (state['x'] + w * 0.03) % (w + seg)
            canvas.delete('all')
            rounded_rect(canvas, 0, 0, w, ht, ht / 2, fill=SURFACE2, outline='')
            rounded_rect(canvas, state['x'] - seg, 0, state['x'], ht, ht / 2, fill=getattr(canvas, '_pph7_accent', CYAN), outline='')
        self._pph7_anim.loop(f'{page_name}:{tag}', 45, tick)

    def stop_indeterminate(self, page_name, tag='scan'):
        self._pph7_anim.cancel(f'{page_name}:{tag}')

    def page_indicator(self, parent, count, active):
        row = tk.Frame(parent, bg=BG); row.pack(pady=(2, 0))
        for i in range(count):
            c = tk.Canvas(row, width=16, height=16, bg=BG, highlightthickness=0); c.pack(side='left', padx=3)
            if i == active: c.create_oval(4, 4, 12, 12, fill=CYAN, outline='')
            else: c.create_oval(5, 5, 11, 11, outline=BORDER, width=2)
        return row

    def page_shell(self, name, kicker, title, active_nav, status_text='READY', status_kind='ready', back_to=None, actions=None):
        page = new_page(self, name)
        self._pph7_nav_map[name] = active_nav
        if actions:
            action_row(self, page, actions)
        svar, badge = header(self, page, kicker, title, status_text, status_kind, back_to)
        content = tk.Frame(page, bg=BG); content.pack(fill='both', expand=True)
        return page, content, svar, badge

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

    def overlay(self, title, message, rows=None, buttons=None):
        dim = tk.Frame(self.root, bg='#000000')
        dim.place(relx=0, rely=0, relwidth=1, relheight=1)
        panel = tk.Frame(dim, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
        panel.place(relx=0.5, rely=0.5, anchor='center', width=1, height=1)
        tk.Frame(panel, bg=RED, height=5).pack(fill='x')
        tk.Label(panel, text=title, bg=SURFACE, fg=TEXT, font=font(self, 16, 'bold')).pack(anchor='w', padx=20, pady=(14, 2))
        tk.Label(panel, text=message, bg=SURFACE, fg=MUTED, font=font(self, 10), wraplength=520, justify='left').pack(anchor='w', padx=20)
        if rows:
            rf = tk.Frame(panel, bg=SURFACE); rf.pack(fill='x', padx=20, pady=(10, 0))
            for label, ok in rows:
                r = tk.Frame(rf, bg=SURFACE); r.pack(fill='x', pady=2)
                tk.Label(r, text=label, bg=SURFACE, fg=TEXT, font=font(self, 9, 'bold'), anchor='w').pack(side='left')
                tk.Label(r, text=('OK' if ok else 'FAIL'), bg=SURFACE, fg=(GREEN if ok else RED), font=font(self, 9, 'bold')).pack(side='right')
        def close():
            try: dim.destroy()
            except Exception: pass
        br = tk.Frame(panel, bg=SURFACE); br.pack(side='bottom', fill='x', padx=16, pady=14)
        btns = list(buttons or []) or [('CLOSE', close, CYAN)]
        for label, cmd, accent in btns:
            def wrapped(c=cmd):
                try: c()
                finally: close()
            action_button(self, br, label, wrapped, accent).pack(side='left', fill='both', expand=True, padx=4)
        dim.lift()
        def frame(t):
            wpx = int(560 * (0.9 + 0.1 * t)); hpx = int(300 * (0.9 + 0.1 * t))
            panel.place_configure(width=wpx, height=hpx)
        self._pph7_anim.tween('overlay:open', 180, frame, tier='REDUCED', ease='back')
        return close

    def notify(self, text, kind='info'):
        kind_map = {'info': CYAN, 'ok': GREEN, 'warn': YELLOW, 'error': RED}
        accent = kind_map.get(kind, CYAN)
        while len(self._pph7_notify_stack) >= 2:
            old = self._pph7_notify_stack.pop(0)
            try: old.destroy()
            except Exception: pass
        n = tk.Frame(self.root, bg=SURFACE2, highlightthickness=1, highlightbackground=accent)
        tk.Label(n, text=text, bg=SURFACE2, fg=TEXT, font=font(self, 10, 'bold'), padx=14, pady=10).pack()
        idx = len(self._pph7_notify_stack); self._pph7_notify_stack.append(n)
        y_target = 10 + idx * 46
        n.place(relx=1.0, x=20, y=y_target, anchor='ne'); n.lift()
        def frame(t): n.place_configure(x=int(20 - 240 * (1 - t)))
        self._pph7_anim.tween(f'notify:{id(n)}:in', 180, frame, tier='REDUCED')
        def dismiss():
            def frame_out(t): n.place_configure(x=int(20 - 240 * t))
            def done():
                try: n.destroy()
                except Exception: pass
                if n in self._pph7_notify_stack: self._pph7_notify_stack.remove(n)
            self._pph7_anim.tween(f'notify:{id(n)}:out', 180, frame_out, on_done=done, tier='REDUCED')
        self._pph7_anim.after(f'notify:{id(n)}:life', 2600, dismiss)

    def animate_value(self, page, key, var, new_value, fmt, tier='FULL'):
        old = self._pph7_prev.get(key)
        self._pph7_prev[key] = new_value
        if old is None or not isinstance(new_value, (int, float)) or not isinstance(old, (int, float)):
            var.set(fmt(new_value)); return
        def frame(t): var.set(fmt(old + (new_value - old) * t))
        self._pph7_anim.tween(f'{page}:val:{key}', 320, frame, tier=tier)

    def push_history(self, key, value, cap=40):
        h = self._pph7_history.setdefault(key, [])
        h.append(value if isinstance(value, (int, float)) else None)
        del h[:-cap]
        return h

    # =====================================================================
    # PAGES
    # =====================================================================

    def build_home(self):
        page, content, svar, badge = page_shell(self, 'home3', 'PPH 7.1 · PULSE DECK', 'FIELD CENTER', 'home3', 'READY', 'ready')
        self.p7_net = tk.StringVar(value='—'); self.p7_net_d = tk.StringVar(value='Uplink wird geprüft')
        self.p7_field = tk.StringVar(value='READY'); self.p7_field_d = tk.StringVar(value='Alle Systeme OK')
        two_cards(self, content,
                  holo_card(self, content, 'NETWORK', self.p7_net, CYAN, self.p7_net_d, glow=True, icon=glyph_network),
                  holo_card(self, content, 'FIELD STATUS', self.p7_field, GREEN, self.p7_field_d, icon=glyph_home))
        action_row(self, page, [
            ('WIRELESS', lambda: self.show_page('measure3'), CYAN),
            ('QUICK TEST', lambda: self.show_page('network_doctor'), GREEN),
            ('FIELD', lambda: self.show_page('field50'), PURPLE),
        ])

        def refresh():
            route = run(['ip', 'route', 'show', 'default'])
            self.p7_net.set('ONLINE' if route else 'OFFLINE')
            self.p7_net_d.set(route.splitlines()[0][:44] if route else 'Kein Uplink')
            ap = _ensure_ap(self)
            try: s = ap.status() if ap else {}
            except Exception: s = {}
            self.p7_field.set('READY')
            self.p7_field_d.set(f"AP {'aktiv' if s.get('active') else 'aus'} · Messung bereit")
        self._pph7_refresh['home3'] = refresh

    def build_more(self):
        page, content, svar, badge = page_shell(self, 'more7', 'PULSE DECK', 'ALLE KATEGORIEN', 'system3', 'READY', 'ready')
        grid = tk.Frame(content, bg=BG); grid.pack(fill='both', expand=True, padx=10, pady=6)
        for c in range(3): grid.grid_columnconfigure(c, weight=1, uniform='more7')
        for r in range(2): grid.grid_rowconfigure(r, weight=1, uniform='more7')
        tiles = [('RADIOS', 'Adapter, DFS, Kanäle', 'wifi3', ORANGE), ('EVENTS', 'Verlauf und Meldungen', 'events3', BLUE),
                 ('SETTINGS', 'Anzeige, Updates, Field Mode', 'settings3', CYAN), ('CONNECTION FLOW', 'Internet bis Client', 'flow50', GREEN),
                 ('SESSION', 'Kunden-Session aufzeichnen', 'session50', PURPLE), ('TOOLS', 'Netzwerk-Werkzeuge', 'tools', YELLOW)]
        for i, (title, detail, target, accent) in enumerate(tiles):
            f = tk.Frame(grid, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER, cursor='hand2')
            tk.Frame(f, bg=accent, height=4).pack(fill='x')
            tk.Label(f, text=title, bg=SURFACE, fg=TEXT, font=font(self, 11, 'bold')).pack(anchor='w', padx=12, pady=(8, 0))
            tk.Label(f, text=detail, bg=SURFACE, fg=MUTED, font=font(self, 8), wraplength=200, justify='left').pack(anchor='w', padx=12, pady=(2, 8))
            for w in (f,) + tuple(f.winfo_children()):
                w.bind('<Button-1>', lambda _e, t=target: self.show_page(t), add='+')
            f.grid(row=i // 3, column=i % 3, sticky='nsew', padx=4, pady=4)

    def build_wireless(self):
        page, content, svar, badge = page_shell(self, 'measure3', 'RF / WLAN', 'WIRELESS SITE ANALYZER', 'measure3', 'READY', 'ready')
        self.p7_sig = tk.StringVar(value='—'); self.p7_sig_d = tk.StringVar(value='RSSI')
        self.p7_thr = tk.StringVar(value='—')
        sig_card = holo_card(self, content, 'SIGNAL', self.p7_sig, CYAN, self.p7_sig_d, glow=True)
        bars_c = tk.Canvas(sig_card, width=50, height=24, bg=SURFACE, highlightthickness=0)
        bars_c.place(relx=1.0, x=-18, y=52, anchor='ne')
        self.p7_sig_bars = bars_c
        thr_card = holo_card(self, content, 'THROUGHPUT', self.p7_thr, PURPLE)
        spark = tk.Canvas(thr_card, bg=SURFACE, highlightthickness=0, width=300, height=40)
        spark.place(relx=0, rely=1.0, x=16, y=-14, relwidth=1, width=-32, anchor='sw')
        self.p7_thr_spark = spark
        two_cards(self, content, sig_card, thr_card)
        action_row(self, page, [
            ('START', lambda: self.launch_funktest(), CYAN),
            ('DETAILS', lambda: self.show_page('measure3_detail'), ORANGE),
            ('RADIOS', lambda: self.show_page('wifi3'), PURPLE),
        ])
        wire_swipe(self, content, None, 'measure3_detail')
        status_pulse(self, 'measure3', badge, 'live')

        def refresh():
            try: st = self._read_measurement_state()
            except Exception: st = {}
            try: running = self._measurement_running() or self._funktest_running()
            except Exception: running = False
            svar.set('● LIVE' if running else 'READY')
            sig = st.get('signal_dbm') or st.get('rssi')
            if isinstance(sig, (int, float)):
                animate_value(self, 'measure3', 'sig', self.p7_sig, float(sig), lambda v: f'{v:.0f} dBm')
                q = max(0, min(100, int((sig + 95) * 2)))
                self.p7_sig_d.set('EXCELLENT' if q > 80 else 'GOOD' if q > 55 else 'FAIR' if q > 30 else 'WEAK')
                filled = 4 if q > 80 else 3 if q > 55 else 2 if q > 30 else 1
            else:
                self.p7_sig.set('—'); self.p7_sig_d.set('RSSI'); filled = 0
            bars_c.delete('all'); signal_bars(bars_c, 0, 2, CYAN, filled=filled, count=4, bw=7, gap=4, h=20)
            dl = st.get('download_mbps') or st.get('throughput_mbps')
            if isinstance(dl, (int, float)):
                animate_value(self, 'measure3', 'thr', self.p7_thr, float(dl), lambda v: f'{v:.1f} Mbit/s')
            else:
                self.p7_thr.set('—')
            push_history(self, 'thr', dl)
            sparkline(spark, self._pph7_history.get('thr', []), PURPLE)
        self._pph7_refresh['measure3'] = refresh

    def build_wireless_detail(self):
        page, content, svar, badge = page_shell(self, 'measure3_detail', 'RF / WLAN', 'WIRELESS DETAILS', 'measure3', '', 'ready', back_to='measure3')
        badge.pack_forget()
        page_indicator(self, content, 2, 1)
        grid = tk.Frame(content, bg=BG); grid.pack(fill='both', expand=True, padx=10, pady=4)
        for c in range(2): grid.grid_columnconfigure(c, weight=1, uniform='wd')
        for r in range(2): grid.grid_rowconfigure(r, weight=1, uniform='wd')
        self.p7_lat = tk.StringVar(value='—'); self.p7_qual = tk.StringVar(value='—')
        self.p7_loss = tk.StringVar(value='—'); self.p7_chan = tk.StringVar(value='—')
        defs = [('LATENCY', self.p7_lat, YELLOW), ('QUALITY', self.p7_qual, GREEN), ('LOSS', self.p7_loss, ORANGE), ('CHANNEL', self.p7_chan, BLUE)]
        for i, (title, var, accent) in enumerate(defs):
            holo_card(self, grid, title, var, accent, w=220, h=110).grid(row=i // 2, column=i % 2, sticky='nsew', padx=4, pady=4)
        wire_swipe(self, content, 'measure3', None)

        def refresh():
            try: st = self._read_measurement_state()
            except Exception: st = {}
            ping = _first(st.get('ping_ms'), st.get('latency_ms'))
            self.p7_lat.set(f'{float(ping):.1f} ms' if isinstance(ping, (int, float)) else '—')
            sig = st.get('signal_dbm') or st.get('rssi')
            self.p7_qual.set(f'{max(0, min(100, int((sig + 95) * 2)))}%' if isinstance(sig, (int, float)) else '—')
            loss = _first(st.get('loss_pct'), st.get('packet_loss'))
            self.p7_loss.set(f'{float(loss):.1f} %' if isinstance(loss, (int, float)) else '—')
            ch = st.get('channel'); self.p7_chan.set(str(ch) if ch else 'AUTO')
        self._pph7_refresh['measure3_detail'] = refresh

    def build_radio_center(self):
        page, content, svar, badge = page_shell(self, 'wifi3', 'RF / WLAN', 'RADIO CENTER', 'measure3', 'READY', 'ready')
        rows = tk.Frame(content, bg=BG); rows.pack(fill='both', expand=True, padx=14, pady=4)
        self.p7_radio_status = {}
        defs = [('control', 'ONBOARD', 'Broadcom / brcmfmac · CONTROL / CLIENT'),
                ('measurement', 'BROSTREND', 'mt7921u · ACCESS POINT / FIELD'),
                ('scan', 'ALFA AWUS', 'mt76x2u · RF ANALYSIS')]
        for key, label, sub in defs:
            v = tk.StringVar(value=sub); self.p7_radio_status[key] = v
            list_row(self, rows, label, v, 'offline', on_tap=lambda k=key: open_radio_detail(self, k)).pack(fill='x', pady=4)

        def refresh():
            ov = _adapter_overview(); roles = ov.get('roles') or {}
            for key, label, sub in defs:
                r = roles.get(key) or {}
                self.p7_radio_status[key].set(f"{r.get('interface','—')} · {r.get('driver','—')} · {r.get('operstate','—')}" if r else sub + ' · nicht erkannt')
        self._pph7_refresh['wifi3'] = refresh

    def open_radio_detail(self, key):
        self._pph7_radio_sel = key
        self.show_page('radio_detail')

    def build_radio_detail(self):
        page, content, svar, badge = page_shell(self, 'radio_detail', 'RF / WLAN', 'RADIO DETAILS', 'measure3', '', 'ready', back_to='wifi3')
        badge.pack_forget()
        self.p7_radio_title = tk.StringVar(value='—'); self.p7_radio_sub = tk.StringVar(value='—')
        holo_card(self, content, 'ADAPTER', self.p7_radio_title, ORANGE, self.p7_radio_sub, glow=True).pack(fill='both', expand=True, padx=10, pady=6)

        def refresh():
            key = getattr(self, '_pph7_radio_sel', 'measurement')
            labels = {'control': 'ONBOARD', 'measurement': 'BROSTREND', 'scan': 'ALFA AWUS'}
            self.p7_radio_title.set(labels.get(key, key.upper()))
            ov = _adapter_overview(); r = (ov.get('roles') or {}).get(key) or {}
            self.p7_radio_sub.set(f"{r.get('interface','—')} · {r.get('driver','—')} · {r.get('iftype','managed')} · {r.get('operstate','—')}" if r else 'Adapter nicht erkannt')
        self._pph7_refresh['radio_detail'] = refresh

    def build_network(self):
        page, content, svar, badge = page_shell(self, 'network', 'LAN / WAN', 'NETWORK ANALYZER', 'network', 'READY', 'ready')
        self.p7_dl = tk.StringVar(value='—'); self.p7_ul = tk.StringVar(value='—')
        dl_card = holo_card(self, content, 'DOWNLOAD', self.p7_dl, CYAN, glow=True)
        dl_spark = tk.Canvas(dl_card, bg=SURFACE, highlightthickness=0, width=300, height=40)
        dl_spark.place(relx=0, rely=1.0, x=16, y=-14, relwidth=1, width=-32, anchor='sw')
        ul_card = holo_card(self, content, 'UPLOAD', self.p7_ul, PURPLE)
        two_cards(self, content, dl_card, ul_card)
        action_row(self, page, [('TEST', lambda: self.launch_funktest(), CYAN), ('DOCTOR', lambda: self.show_page('network_doctor'), GREEN), ('DETAILS', lambda: self.show_page('network_detail'), ORANGE)])
        wire_swipe(self, content, None, 'network_detail')

        def refresh():
            try: st = self._read_measurement_state()
            except Exception: st = {}
            dl = st.get('download_mbps'); ul = st.get('upload_mbps')
            if isinstance(dl, (int, float)): animate_value(self, 'network', 'dl', self.p7_dl, float(dl), lambda v: f'{v:.0f} Mbit/s')
            else: self.p7_dl.set('—')
            if isinstance(ul, (int, float)): animate_value(self, 'network', 'ul', self.p7_ul, float(ul), lambda v: f'{v:.0f} Mbit/s')
            else: self.p7_ul.set('—')
            push_history(self, 'dl', dl)
            sparkline(dl_spark, self._pph7_history.get('dl', []), CYAN)
        self._pph7_refresh['network'] = refresh

    def build_network_detail(self):
        page, content, svar, badge = page_shell(self, 'network_detail', 'LAN / WAN', 'NETWORK DETAILS', 'network', '', 'ready', back_to='network')
        badge.pack_forget()
        grid = tk.Frame(content, bg=BG); grid.pack(fill='both', expand=True, padx=10, pady=4)
        for c in range(2): grid.grid_columnconfigure(c, weight=1, uniform='nd')
        for r in range(2): grid.grid_rowconfigure(r, weight=1, uniform='nd')
        self.p7_ping = tk.StringVar(value='—'); self.p7_jitter = tk.StringVar(value='—')
        self.p7_nloss = tk.StringVar(value='—'); self.p7_uplink = tk.StringVar(value='—')
        defs = [('PING', self.p7_ping, YELLOW), ('JITTER', self.p7_jitter, ORANGE), ('LOSS', self.p7_nloss, GREEN), ('UPLINK', self.p7_uplink, BLUE)]
        for i, (title, var, accent) in enumerate(defs):
            holo_card(self, grid, title, var, accent, w=220, h=110).grid(row=i // 2, column=i % 2, sticky='nsew', padx=4, pady=4)
        wire_swipe(self, content, 'network', None)

        def refresh():
            try: st = self._read_measurement_state()
            except Exception: st = {}
            ping = _first(st.get('ping_ms'), st.get('latency_ms'))
            self.p7_ping.set(f'{float(ping):.1f} ms' if isinstance(ping, (int, float)) else '—')
            jit = st.get('jitter_ms')
            self.p7_jitter.set(f'{float(jit):.1f} ms' if isinstance(jit, (int, float)) else '—')
            loss = _first(st.get('loss_pct'), st.get('packet_loss'))
            self.p7_nloss.set(f'{float(loss):.1f} %' if isinstance(loss, (int, float)) else '—')
            route = run(['ip', 'route', 'show', 'default'])
            iface = ''
            try: iface = route.split('dev ', 1)[1].split()[0] if 'dev ' in route else ''
            except Exception: pass
            self.p7_uplink.set((iface or 'eth0') + ' · 1 Gbit')
        self._pph7_refresh['network_detail'] = refresh

    def build_access(self):
        page, content, svar, badge = page_shell(self, 'access3', 'FIELD ROUTER', 'ACCESS POINT', 'access3', 'OFF', 'offline')
        self.p7_ap = tk.StringVar(value='—'); self.p7_ap_d = tk.StringVar(value='PPH-WIFI')
        self.p7_code = tk.StringVar(value='—'); self.p7_code_d = tk.StringVar(value='10.42.0.1')
        two_cards(self, content, holo_card(self, content, 'PPH-WIFI', self.p7_ap, GREEN, self.p7_ap_d, glow=True, icon=glyph_access),
                  holo_card(self, content, 'PAIRING CODE', self.p7_code, PURPLE, self.p7_code_d))
        info = tk.Frame(content, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
        info.pack(fill='x', padx=14, pady=(0, 4))
        row = tk.Frame(info, bg=SURFACE); row.pack(fill='x', padx=14, pady=8)
        self.p7_ssid = tk.StringVar(value='PPH-WIFI'); self.p7_lanip = tk.StringVar(value='—')
        for label, var, accent in (('SSID', self.p7_ssid, CYAN), ('LAN IP', self.p7_lanip, BLUE)):
            c = tk.Frame(row, bg=SURFACE); c.pack(side='left', fill='x', expand=True)
            tk.Label(c, text=label, bg=SURFACE, fg=MUTED, font=font(self, 8, 'bold')).pack(anchor='w')
            tk.Label(c, textvariable=var, bg=SURFACE, fg=accent, font=font(self, 13, 'bold')).pack(anchor='w')
        action_row(self, page, [('START', lambda: ap_start(self), GREEN), ('STOP', lambda: ap_stop(self), RED), ('DETAILS', lambda: self.show_page('access_detail'), CYAN)])

        def refresh():
            ap = _ensure_ap(self)
            try: s = ap.status() or {} if ap else {}
            except Exception: s = {}
            active = bool(s.get('active'))
            svar.set('● ACTIVE' if active else 'OFF')
            badge.configure(**dict(zip(('bg', 'fg'), CHIP['active' if active else 'offline'])))
            self.p7_ap.set('ACTIVE' if active else 'OFF')
            ssid = s.get('ssid') or 'PPH-WIFI'; clients = s.get('clients', 0)
            self.p7_ap_d.set(f'{clients} CLIENTS'); self.p7_ssid.set(ssid)
            code = _first(s.get('pairing_code'), s.get('token')) or '—'
            self.p7_code.set(str(code))
            ip = s.get('ap_ip') or '10.42.0.1'
            self.p7_code_d.set(str(ip)); self.p7_lanip.set(s.get('lan_ip') or '—')
        self._pph7_refresh['access3'] = refresh

    def build_access_detail(self):
        page, content, svar, badge = page_shell(self, 'access_detail', 'FIELD ROUTER', 'ACCESS POINT DETAILS', 'access3', '', 'ready', back_to='access3')
        badge.pack_forget()
        page_indicator(self, content, 2, 0)
        rows = tk.Frame(content, bg=BG); rows.pack(fill='both', expand=True, padx=14, pady=4)
        self.p7_ad = {}; self.p7_ad_row = {}
        for key, label in (('radio', 'RADIO'), ('band', 'BAND'), ('clients', 'CLIENTS'), ('throughput', 'THROUGHPUT')):
            v = tk.StringVar(value='—'); self.p7_ad[key] = v
            row = list_row(self, rows, label, v, 'ready'); row.pack(fill='x', pady=3); self.p7_ad_row[key] = row
        wire_swipe(self, content, None, 'access_detail2')
        action_row(self, page, [('WEITER', lambda: self.show_page('access_detail2'), CYAN)])

        def refresh():
            ap = _ensure_ap(self)
            try: s = ap.status() or {} if ap else {}
            except Exception: s = {}
            active = bool(s.get('active'))
            self.p7_ad['radio'].set(f"BrosTrend · {s.get('driver','mt7921u')}")
            band = s.get('band') or '—'
            self.p7_ad['band'].set(band if active else f'{band} (inaktiv)')
            self.p7_ad['clients'].set(str(s.get('clients', 0)))
            self.p7_ad['throughput'].set(f"{float(s.get('total_mbps') or 0):.1f} Mbit/s")
        self._pph7_refresh['access_detail'] = refresh

    def build_access_detail2(self):
        page, content, svar, badge = page_shell(self, 'access_detail2', 'FIELD ROUTER', 'ACCESS POINT DETAILS', 'access3', '', 'ready', back_to='access3')
        badge.pack_forget()
        page_indicator(self, content, 2, 1)
        rows = tk.Frame(content, bg=BG); rows.pack(fill='both', expand=True, padx=14, pady=4)
        self.p7_ad2 = {}; self.p7_ad2_row = {}
        for key, label in (('rxtx', 'RX / TX'), ('lan', 'LAN UPLINK'), ('forwarding', 'FORWARDING (NAT)'), ('internet', 'INTERNET')):
            v = tk.StringVar(value='—'); self.p7_ad2[key] = v
            row = list_row(self, rows, label, v, 'ready'); row.pack(fill='x', pady=3); self.p7_ad2_row[key] = row
        wire_swipe(self, content, 'access_detail', None)
        action_row(self, page, [('CONFIGURE', lambda: self.show_page('access_config'), PURPLE)])

        def refresh():
            ap = _ensure_ap(self)
            try: s = ap.status() or {} if ap else {}
            except Exception: s = {}
            active = bool(s.get('active'))
            self.p7_ad2['rxtx'].set(f"↓ {float(s.get('rx_mbps') or 0):.1f} · ↑ {float(s.get('tx_mbps') or 0):.1f} Mbit/s")
            lan_ok = bool(s.get('lan_connected'))
            self.p7_ad2['lan'].set(f"{s.get('lan_iface') or '—'} · {'VERBUNDEN' if lan_ok else 'GETRENNT'}")
            fwd_ok = bool(s.get('forwarding')) or active
            self.p7_ad2['forwarding'].set('AKTIV' if fwd_ok else 'INAKTIV')
            inet_ok = bool(s.get('internet'))
            self.p7_ad2['internet'].set('ONLINE' if inet_ok else 'OFFLINE')
            for key, ok in (('lan', lan_ok), ('forwarding', fwd_ok), ('internet', inet_ok)):
                row = self.p7_ad2_row.get(key)
                if row is not None:
                    try: row._pph7_set_kind('ready' if ok else 'offline')
                    except Exception: pass
        self._pph7_refresh['access_detail2'] = refresh

    def build_access_config(self):
        page, content, svar, badge = page_shell(self, 'access_config', 'FIELD ROUTER', 'ACCESS POINT CONFIG', 'access3', '', 'ready', back_to='access_detail')
        badge.pack_forget()
        box = tk.Frame(content, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
        box.pack(fill='both', expand=True, padx=14, pady=6)
        tk.Label(box, text='SSID', bg=SURFACE, fg=MUTED, font=font(self, 9, 'bold')).pack(anchor='w', padx=14, pady=(16, 4))
        self.p7_cfg_ssid = tk.Entry(box, bg=SURFACE2, fg=TEXT, insertbackground=TEXT, relief='flat', font=font(self, 13), highlightthickness=1, highlightbackground=BORDER)
        self.p7_cfg_ssid.pack(fill='x', padx=14, ipady=8)
        tk.Label(box, text='PASSWORT (MIND. 8 ZEICHEN)', bg=SURFACE, fg=MUTED, font=font(self, 9, 'bold')).pack(anchor='w', padx=14, pady=(14, 4))
        self.p7_cfg_pass = tk.Entry(box, bg=SURFACE2, fg=TEXT, insertbackground=TEXT, relief='flat', font=font(self, 13), highlightthickness=1, highlightbackground=BORDER, show='•')
        self.p7_cfg_pass.pack(fill='x', padx=14, ipady=8)
        tk.Label(box, text='LEER LASSEN, UM DAS AKTUELLE PASSWORT ZU BEHALTEN', bg=SURFACE, fg=MUTED, font=font(self, 7)).pack(anchor='w', padx=14, pady=(2, 0))
        tk.Label(box, text='BAND', bg=SURFACE, fg=MUTED, font=font(self, 9, 'bold')).pack(anchor='w', padx=14, pady=(14, 4))
        band_row = tk.Frame(box, bg=SURFACE); band_row.pack(fill='x', padx=10)
        self.p7_cfg_band = tk.StringVar(value='a')
        self.p7_cfg_band_buttons = {}
        for label, value in (('5 GHz', 'a'), ('2.4 GHz', 'bg')):
            def select(v=value):
                self.p7_cfg_band.set(v)
                for bv, b in self.p7_cfg_band_buttons.items():
                    sel = bv == self.p7_cfg_band.get()
                    b.configure(bg=(CYAN if sel else SURFACE2), fg=(BG if sel else TEXT))
            b = tk.Button(band_row, text=label, command=select, bg=SURFACE2, fg=TEXT, activebackground=CYAN, activeforeground=BG,
                          relief='flat', bd=0, highlightthickness=1, highlightbackground=BORDER, font=font(self, 11, 'bold'), pady=12, cursor='hand2')
            b.pack(side='left', fill='x', expand=True, padx=3)
            self.p7_cfg_band_buttons[value] = b
        action_row(self, page, [('SPEICHERN', lambda: ap_save_config(self), GREEN)])

        def refresh():
            ap = _ensure_ap(self)
            cfg = getattr(ap, 'config', {}) if ap else {}
            self.p7_cfg_ssid.delete(0, 'end'); self.p7_cfg_ssid.insert(0, str(cfg.get('ssid') or 'PPH-WIFI'))
            self.p7_cfg_pass.delete(0, 'end')
            band = str(cfg.get('band') or 'a'); self.p7_cfg_band.set(band)
            for bv, b in self.p7_cfg_band_buttons.items():
                sel = bv == band
                b.configure(bg=(CYAN if sel else SURFACE2), fg=(BG if sel else TEXT))
        self._pph7_refresh['access_config'] = refresh

    def build_connection_flow(self):
        page, content, svar, badge = page_shell(self, 'flow50', 'FIELD ROUTER', 'CONNECTION FLOW', 'access3', 'LIVE', 'live')
        wrap = tk.Frame(content, bg=BG); wrap.pack(fill='both', expand=True, padx=40, pady=4)
        steps = [('INTERNET', GREEN), ('ETHERNET', CYAN), ('RASPBERRY PI', BLUE), ('BROSTREND', ORANGE), ('PPH-WIFI', PURPLE), ('CLIENTS', GREEN)]
        self.p7_flow_boxes = []
        canvas = tk.Canvas(wrap, bg=BG, highlightthickness=0, width=400, height=280); canvas.pack(fill='both', expand=True)

        def draw():
            canvas.delete('static')
            cw = max(200, canvas.winfo_width()); ch = max(200, canvas.winfo_height()) - 12
            n = len(steps); box_h = 34; gap = (ch - n * box_h) / max(1, n - 1)
            self.p7_flow_boxes = []
            for i, (label, accent) in enumerate(steps):
                y = i * (box_h + gap)
                rounded_rect(canvas, cw * 0.15, y, cw * 0.85, y + box_h, 10, fill=SURFACE, outline=accent, width=2, tags='static')
                canvas.create_text(cw / 2, y + box_h / 2, text=label, fill=TEXT, font=font(self, 11, 'bold'), tags='static')
                self.p7_flow_boxes.append((cw / 2, y + box_h))
                if i < n - 1:
                    canvas.create_line(cw / 2, y + box_h, cw / 2, y + box_h + gap, fill=accent, width=2, tags='static')
            canvas.tag_lower('static')
        canvas.bind('<Configure>', lambda _e: draw())

        def pulse():
            if not self.p7_flow_boxes: return
            canvas.delete('pulse')
            t = (time.monotonic() * 0.4) % 1.0
            for i in range(len(self.p7_flow_boxes) - 1):
                x, y0 = self.p7_flow_boxes[i]; _x2, y1 = self.p7_flow_boxes[i + 1]
                y = y0 + (y1 - y0) * t
                canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill=CYAN, outline='', tags='pulse')
        self._pph7_anim.loop('flow50:pulse', 60, pulse)
        self._pph7_refresh['flow50'] = lambda: None

    def build_network_doctor(self):
        page, content, svar, badge = page_shell(self, 'network_doctor', 'DIAGNOSTICS', 'NETWORK DOCTOR', 'network', 'READY', 'ready')
        rows = tk.Frame(content, bg=BG); rows.pack(fill='both', expand=True, padx=14, pady=(4, 0))
        self.p7_doc = {}; self.p7_doc_row = {}
        for key, label in (('eth', 'ETHERNET'), ('gw', 'GATEWAY'), ('dns', 'DNS'), ('inet', 'INTERNET')):
            v = tk.StringVar(value='—'); self.p7_doc[key] = v
            row = list_row(self, rows, label, v, 'ready'); row.pack(fill='x', pady=3); self.p7_doc_row[key] = row
        self.p7_doc_result = tk.StringVar(value='TIPPE RUN AGAIN')
        self.p7_doc_result_lbl = tk.Label(content, textvariable=self.p7_doc_result, bg=BG, fg=YELLOW, font=font(self, 12, 'bold'))
        self.p7_doc_result_lbl.pack(pady=(6, 0))
        action_row(self, page, [('RUN AGAIN', lambda: run_doctor(self), CYAN), ('DETAILS', lambda: show_doctor_overlay(self), ORANGE)])
        self._pph7_refresh['network_doctor'] = lambda: run_doctor(self)

    def build_system(self):
        page, content, svar, badge = page_shell(self, 'system3', 'DEVICE', 'SYSTEM STATUS', 'system3', 'READY', 'ready')
        self.p7_cpu = tk.StringVar(value='—'); self.p7_cpu_d = tk.StringVar(value='Temperature')
        self.p7_ram = tk.StringVar(value='—'); self.p7_ram_d = tk.StringVar(value='Memory')
        two_cards(self, content, holo_card(self, content, 'CPU', self.p7_cpu, ORANGE, self.p7_cpu_d, glow=True, icon=glyph_system),
                  holo_card(self, content, 'RAM', self.p7_ram, BLUE, self.p7_ram_d))
        action_row(self, page, [('HARDWARE', lambda: self.show_page('hardware'), ORANGE), ('STORAGE', lambda: self.show_page('storage'), PURPLE), ('MORE', lambda: self.show_page('more7'), CYAN)])
        wire_swipe(self, content, None, 'system_detail')

        def refresh():
            temp = run(['bash', '-lc', "cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || true"])
            try:
                tc = int(temp) / 1000
                animate_value(self, 'system3', 'cpu', self.p7_cpu, tc, lambda v: f'{v:.0f}°C')
            except Exception:
                self.p7_cpu.set('—')
            mem = run(['bash', '-lc', "LC_ALL=C free -m | awk '/Mem:/ {printf \"%d\", $3*100/$2}'"])
            try:
                animate_value(self, 'system3', 'ram', self.p7_ram, float(mem), lambda v: f'{v:.0f}%')
            except Exception:
                self.p7_ram.set('—')
        self._pph7_refresh['system3'] = refresh

    def build_system_detail(self):
        page, content, svar, badge = page_shell(self, 'system_detail', 'DEVICE', 'SYSTEM DETAILS', 'system3', '', 'ready', back_to='system3')
        badge.pack_forget()
        self.p7_disk = tk.StringVar(value='—'); self.p7_power = tk.StringVar(value='NORMAL')
        two_cards(self, content, holo_card(self, content, 'STORAGE', self.p7_disk, PURPLE), holo_card(self, content, 'POWER', self.p7_power, GREEN))
        wire_swipe(self, content, 'system3', None)

        def refresh():
            out = run(['bash', '-lc', "df -h / | awk 'NR==2{print $5}'"])
            self.p7_disk.set(out or '—')
            volts = run(['bash', '-lc', 'vcgencmd get_throttled 2>/dev/null || true'])
            flagged = volts.strip().endswith('0x0') is False and volts != ''
            self.p7_power.set('THROTTLED' if flagged else 'NORMAL')
        self._pph7_refresh['system_detail'] = refresh

    def build_hardware(self):
        page, content, svar, badge = page_shell(self, 'hardware', 'DEVICE', 'HARDWARE', 'system3', 'READY', 'ready', back_to='system3')
        rows = tk.Frame(content, bg=BG); rows.pack(fill='both', expand=True, padx=14, pady=4)
        self.p7_hw = {}; self.p7_hw_row = {}
        for key, label in (('pi', 'RASPBERRY PI 5'), ('display', 'DISPLAY'), ('brostrend', 'BROSTREND'), ('alfa', 'ALFA AWUS'), ('storage', 'STORAGE')):
            v = tk.StringVar(value='—'); self.p7_hw[key] = v
            row = list_row(self, rows, label, v, 'ready'); row.pack(fill='x', pady=3); self.p7_hw_row[key] = row

        def refresh():
            self.p7_hw['pi'].set('ONLINE'); self.p7_hw['display'].set('800×480 DSI')
            ov = _adapter_overview(); roles = ov.get('roles') or {}
            for key, ok in (('brostrend', bool(roles.get('measurement'))), ('alfa', bool(roles.get('scan')))):
                self.p7_hw[key].set('DETECTED' if ok else 'NICHT ERKANNT')
                try: self.p7_hw_row[key]._pph7_set_kind('ready' if ok else 'offline')
                except Exception: pass
            self.p7_hw['storage'].set('ONLINE')
        self._pph7_refresh['hardware'] = refresh

    def build_storage(self):
        page, content, svar, badge = page_shell(self, 'storage', 'DEVICE', 'STORAGE', 'system3', 'READY', 'ready', back_to='system3')
        wrap = tk.Frame(content, bg=BG); wrap.pack(fill='both', expand=True, padx=16, pady=8)
        self.p7_store_bars = {}
        for key, label in (('root', 'SYSTEM'), ('data', 'DATEN')):
            box = tk.Frame(wrap, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER); box.pack(fill='x', pady=6)
            head = tk.Frame(box, bg=SURFACE); head.pack(fill='x', padx=14, pady=(10, 2))
            tk.Label(head, text=label, bg=SURFACE, fg=MUTED, font=font(self, 9, 'bold')).pack(side='left')
            v = tk.StringVar(value='—'); tk.Label(head, textvariable=v, bg=SURFACE, fg=CYAN, font=font(self, 9, 'bold')).pack(side='right')
            bar = progress_bar(self, box, CYAN); bar.pack(fill='x', padx=14, pady=(2, 12))
            self.p7_store_bars[key] = (v, bar)

        def refresh_mount(key, path):
            out = run(['bash', '-lc', f"df -h {path} 2>/dev/null | awk 'NR==2{{print $2, $4, $5}}'"])
            parts = out.split(); v, bar = self.p7_store_bars[key]
            if len(parts) == 3:
                total, free, pct = parts; v.set(f'{free} FREI')
                try: bar._pph7_set(100 - int(pct.strip('%')))
                except Exception: pass
            else:
                v.set('NICHT EINGEHÄNGT')
                try: bar._pph7_set(0)
                except Exception: pass

        def refresh():
            refresh_mount('root', '/'); refresh_mount('data', '/mnt/storage')
        self._pph7_refresh['storage'] = refresh

    def build_events(self):
        page, content, svar, badge = page_shell(self, 'events3', 'SYSTEM', 'EVENTS', 'system3', 'READY', 'ready', back_to='system3',
                                                  actions=[('RAW LOG', lambda: self.show_page('events_raw'), CYAN)])
        self.p7_events_wrap = tk.Frame(content, bg=BG); self.p7_events_wrap.pack(fill='both', expand=True, padx=12, pady=4)

        def refresh():
            for w in self.p7_events_wrap.winfo_children(): w.destroy()
            rows = []
            try:
                if events: rows = events.read_events(limit=6)
            except Exception: rows = []
            if not rows:
                tk.Label(self.p7_events_wrap, text='Keine Events', bg=BG, fg=MUTED, font=font(self, 10)).pack(pady=20)
                return
            for item in reversed(rows):
                sev = str(item.get('severity') or 'info')
                accent = RED if sev in ('error', 'critical') else YELLOW if sev == 'warning' else CYAN
                row = tk.Frame(self.p7_events_wrap, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER); row.pack(fill='x', pady=3)
                tk.Frame(row, bg=accent, width=6).pack(side='left', fill='y')
                body = tk.Frame(row, bg=SURFACE); body.pack(side='left', fill='both', expand=True, padx=10, pady=8)
                ts = str(item.get('timestamp') or '')[-8:-3]
                tk.Label(body, text=f"{ts}  {item.get('message') or item.get('type') or 'Event'}", bg=SURFACE, fg=TEXT, font=font(self, 10, 'bold'), anchor='w').pack(fill='x')
        self._pph7_refresh['events3'] = refresh

    def build_events_raw(self):
        page, content, svar, badge = page_shell(self, 'events_raw', 'SYSTEM', 'RAW LOG', 'system3', '', 'ready', back_to='events3')
        badge.pack_forget()
        t = tk.Text(content, bg=SURFACE, fg=TEXT, insertbackground=TEXT, relief='flat', bd=0, highlightthickness=1, highlightbackground=BORDER, font=font(self, 10), wrap='word', padx=12, pady=10)
        t.pack(fill='both', expand=True, padx=12, pady=6)
        self.p7_rawlog = t

        def refresh():
            out = run(['bash', '-lc', 'journalctl -n 30 --no-pager 2>/dev/null || true'])
            t.configure(state='normal'); t.delete('1.0', 'end'); t.insert('end', out or 'Keine Daten'); t.configure(state='disabled')
        self._pph7_refresh['events_raw'] = refresh

    def build_settings(self):
        page, content, svar, badge = page_shell(self, 'settings3', 'DEVICE', 'SETTINGS', 'system3', '', 'ready', back_to='system3')
        badge.pack_forget()
        page_indicator(self, content, 2, 0)
        box = tk.Frame(content, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER); box.pack(fill='both', expand=True, padx=14, pady=6)
        def row_label(text): tk.Label(box, text=text, bg=SURFACE, fg=MUTED, font=font(self, 9, 'bold')).pack(anchor='w', padx=14, pady=(16, 6))
        row_label('DISPLAY BRIGHTNESS')
        r1 = tk.Frame(box, bg=SURFACE); r1.pack(fill='x', padx=10)
        for pct in (25, 50, 75, 100):
            action_button(self, r1, f'{pct}%', lambda v=pct: self.set_brightness(v), YELLOW).pack(side='left', fill='x', expand=True, padx=3)
        row_label('DISPLAY TIMEOUT')
        r2 = tk.Frame(box, bg=SURFACE); r2.pack(fill='x', padx=10)
        for sec, lab in ((30, '30 S'), (60, '1 MIN'), (120, '2 MIN'), (0, 'NIE')):
            action_button(self, r2, lab, lambda v=sec: self.set_timeout(v), CYAN).pack(side='left', fill='x', expand=True, padx=3)
        wire_swipe(self, content, None, 'settings_detail')
        action_row(self, page, [('WEITER', lambda: self.show_page('settings_detail'), CYAN)])
        self._pph7_refresh['settings3'] = lambda: None

    def build_settings_detail(self):
        page, content, svar, badge = page_shell(self, 'settings_detail', 'DEVICE', 'SETTINGS', 'system3', '', 'ready', back_to='settings3')
        badge.pack_forget()
        page_indicator(self, content, 2, 1)
        box = tk.Frame(content, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER); box.pack(fill='both', expand=True, padx=14, pady=6)
        def row_label(text): tk.Label(box, text=text, bg=SURFACE, fg=MUTED, font=font(self, 9, 'bold')).pack(anchor='w', padx=14, pady=(16, 6))
        row_label('ANIMATIONEN')
        r3 = tk.Frame(box, bg=SURFACE); r3.pack(fill='x', padx=10)
        for level, lab in (('FULL', 'VOLL'), ('REDUCED', 'REDUZIERT'), ('OFF', 'AUS')):
            action_button(self, r3, lab, lambda v=level: self._pph7_anim.set_level(v), PURPLE).pack(side='left', fill='x', expand=True, padx=3)
        self.p7_ver = tk.StringVar(value=f'AKTUELL: {_current_version()}')
        row_label('UPDATES')
        r4 = tk.Frame(box, bg=SURFACE); r4.pack(fill='x', padx=14, pady=(0, 6))
        tk.Label(r4, textvariable=self.p7_ver, bg=SURFACE, fg=TEXT, font=font(self, 9)).pack(anchor='w')
        r5 = tk.Frame(box, bg=SURFACE); r5.pack(fill='x', padx=10, pady=(0, 12))
        action_button(self, r5, 'CHECK UPDATES', lambda: self._pph28_open_update(), CYAN).pack(side='left', fill='x', expand=True, padx=3)
        action_button(self, r5, 'DISPLAY OFF', lambda: self.sleep_display(), BLUE).pack(side='left', fill='x', expand=True, padx=3)
        wire_swipe(self, content, 'settings3', None)
        self._pph7_refresh['settings_detail'] = lambda: None

    def build_field(self):
        page, content, svar, badge = page_shell(self, 'field50', 'CUSTOMER MODE', 'FIELD MODE', 'access3', 'READY', 'ready')
        self.p7_field_state = tk.StringVar(value='FIELD READY')
        holo_card(self, content, 'STATUS', self.p7_field_state, GREEN, glow=True).pack(fill='both', expand=True, padx=14, pady=8)
        action_row(self, page, [('CONNECTION FLOW', lambda: self.show_page('flow50'), CYAN), ('BEFORE / AFTER', lambda: self.show_page('compare50'), ORANGE), ('SESSION', lambda: self.show_page('session50'), PURPLE)])
        self._pph7_refresh['field50'] = lambda: None

    def build_before_after(self):
        page, content, svar, badge = page_shell(self, 'compare50', 'CUSTOMER MODE', 'BEFORE / AFTER', 'access3', 'READY', 'ready', back_to='field50')
        self.p7_before = tk.StringVar(value='NOT SET'); self.p7_after = tk.StringVar(value='NOT SET')
        self.p7_delta = tk.StringVar(value='Zwei Messungen erforderlich')
        two_cards(self, content, holo_card(self, content, 'BEFORE', self.p7_before, ORANGE, self.p7_delta), holo_card(self, content, 'AFTER', self.p7_after, GREEN, self.p7_delta))
        action_row(self, page, [('SAVE BEFORE', lambda: capture(self, 'before'), ORANGE), ('SAVE AFTER', lambda: capture(self, 'after'), GREEN)])
        self._pph7_refresh['compare50'] = lambda: None

    def build_session(self):
        page, content, svar, badge = page_shell(self, 'session50', 'CUSTOMER MODE', 'SESSION RECORDER', 'access3', 'STOPPED', 'offline', back_to='field50')
        self.p7_sess_state = tk.StringVar(value='● STOPPED'); self.p7_sess_time = tk.StringVar(value='00:00:00')
        hero = tk.Frame(content, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER); hero.pack(fill='both', expand=True, padx=14, pady=8)
        tk.Label(hero, textvariable=self.p7_sess_state, bg=SURFACE, fg=RED, font=font(self, 16, 'bold')).pack(pady=(20, 4))
        tk.Label(hero, textvariable=self.p7_sess_time, bg=SURFACE, fg=TEXT, font=font(self, 30, 'bold')).pack()
        action_row(self, page, [('START', lambda: session_start(self), GREEN), ('STOP & SAVE', lambda: session_stop(self), RED)])
        self._pph7_refresh['session50'] = lambda: None

    def build_generic(self, name, title, kicker='PPH 7'):
        page, content, svar, badge = page_shell(self, name, kicker, title, 'system3', 'READY', 'ready', back_to='more7')
        t = tk.Text(content, bg=SURFACE, fg=TEXT, insertbackground=TEXT, relief='flat', bd=0, highlightthickness=1, highlightbackground=BORDER, font=font(self, 10), wrap='word', padx=12, pady=10)
        t.pack(fill='both', expand=True, padx=12, pady=6)
        setattr(self, 'p7_txt_' + name, t)

        def refresh():
            if name == 'tools': txt = 'NETWORK DOCTOR\nLAN MAPPER\nCONNECTION FLOW\nDIAGNOSTIC SNAPSHOT'
            elif name == 'lan_mapper': txt = run(['ip', 'neigh'])
            elif name == 'reports':
                try: st = self._read_measurement_state()
                except Exception: st = {}
                txt = 'LETZTER MESSSTATUS\n\n' + '\n'.join(f'{k}: {v}' for k, v in (st or {}).items())
            elif name == 'jobs3':
                try: rows = jobs.list_jobs(limit=10) if jobs else []
                except Exception: rows = []
                txt = '\n'.join(str(r.get('title') or r) for r in rows) or 'Keine Jobs'
            else: txt = f'{title}\n\nPPH 7.1 Pulse Deck'
            t.configure(state='normal'); t.delete('1.0', 'end'); t.insert('end', txt or 'Keine Daten'); t.configure(state='disabled')
        self._pph7_refresh[name] = refresh

    # =====================================================================
    # actions / helpers
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

    def _ap_refresh_burst(self):
        for name in ('access3', 'access_detail', 'access_detail2'):
            fn = self._pph7_refresh.get(name)
            if not fn: continue
            for delay in (300, 900, 1800, 3000):
                self._pph7_anim.after(f'{name}:burst:{delay}', delay, fn)

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
                self._pph7_refresh.get('access3', lambda: None)()
                _ap_refresh_burst(self)
            try: self.root.after(0, done)
            except Exception: pass
        threading.Thread(target=worker, daemon=True).start()

    def ap_stop(self):
        ap = _ensure_ap(self)
        import threading
        def worker():
            try:
                if ap: ap.stop()
                err = None
            except Exception as exc:
                err = exc
            def done():
                if err: notify(self, str(err), 'error')
                else: notify(self, 'Access Point gestoppt', 'warn')
                self._pph7_refresh.get('access3', lambda: None)()
                _ap_refresh_burst(self)
            try: self.root.after(0, done)
            except Exception: pass
        threading.Thread(target=worker, daemon=True).start()

    def ap_save_config(self):
        ap = _ensure_ap(self)
        ssid = self.p7_cfg_ssid.get().strip(); password = self.p7_cfg_pass.get().strip(); band = self.p7_cfg_band.get()
        if password and len(password) < 8:
            notify(self, 'Passwort muss mindestens 8 Zeichen haben.', 'error'); return
        import threading
        def worker():
            try:
                if ap: ap.update_config(ssid=ssid or None, password=password or None, band=band)
                err = None
            except Exception as exc:
                err = exc
            def done():
                if err: notify(self, str(err), 'error')
                else:
                    notify(self, 'Konfiguration gespeichert', 'ok')
                    self.show_page('access_detail')
                self._pph7_refresh.get('access3', lambda: None)()
                self._pph7_refresh.get('access_detail', lambda: None)()
                self._pph7_refresh.get('access_detail2', lambda: None)()
            try: self.root.after(0, done)
            except Exception: pass
        threading.Thread(target=worker, daemon=True).start()

    def run_doctor(self):
        route = run(['ip', 'route', 'show', 'default']); eth_ok = bool(route)
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
            self.p7_doc[key].set('OK' if ok else 'FAIL')
            row = self.p7_doc_row.get(key)
            if row is not None:
                try: row._pph7_set_kind('ready' if ok else 'error')
                except Exception: pass
        all_ok = eth_ok and gw_ok and dns_ok and inet_ok
        self.p7_doc_result.set('ALLE PRÜFUNGEN OK' if all_ok else 'PROBLEM ERKANNT')
        try: self.p7_doc_result_lbl.configure(fg=(GREEN if all_ok else YELLOW))
        except Exception: pass
        self._pph7_doctor_rows = [('ETHERNET', eth_ok), ('GATEWAY', gw_ok), ('DNS', dns_ok), ('INTERNET', inet_ok)]
        if not all_ok: notify(self, 'Netzwerkproblem erkannt', 'warn')

    def show_doctor_overlay(self):
        rows = getattr(self, '_pph7_doctor_rows', [])
        overlay(self, 'NETWORK ERROR', 'Ein oder mehrere Prüfungen sind fehlgeschlagen.', rows=rows,
                buttons=[('RETRY', lambda: run_doctor(self), CYAN), ('CLOSE', lambda: None, SURFACE2)])

    def capture(self, which):
        try: st = self._read_measurement_state()
        except Exception: st = {}
        val = st.get('download_mbps') or st.get('throughput_mbps')
        setattr(self, f'_pph7_{which}', val if isinstance(val, (int, float)) else None)
        var = self.p7_before if which == 'before' else self.p7_after
        var.set(f'{float(val):.0f} Mbit/s' if isinstance(val, (int, float)) else 'SAVED')
        b = getattr(self, '_pph7_before', None); a = getattr(self, '_pph7_after', None)
        if isinstance(b, (int, float)) and isinstance(a, (int, float)):
            self.p7_delta.set(f'{a - b:+.0f} Mbit/s')

    def session_start(self):
        import time as _t
        self._pph7_session = {'start': _t.time()}
        self.p7_sess_state.set('● RECORDING')
        def tick():
            elapsed = int(_t.time() - self._pph7_session['start'])
            self.p7_sess_time.set(f'{elapsed//3600:02d}:{(elapsed%3600)//60:02d}:{elapsed%60:02d}')
        self._pph7_anim.loop('session50:tick', 1000, tick)

    def session_stop(self):
        self._pph7_anim.cancel('session50:tick')
        self.p7_sess_state.set('SESSION SAVED')
        notify(self, 'Session gespeichert', 'ok')

    # =====================================================================
    # boot sequence - radar sweep
    # =====================================================================

    def play_boot(self, on_done):
        overlay = tk.Frame(self.root, bg=BG)
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        bgc = tk.Canvas(overlay, bg=BG, highlightthickness=0)
        bgc.place(relx=0, rely=0, relwidth=1, relheight=1)
        bgc.bind('<Configure>', lambda e: deck_background(bgc, e.width, e.height), add='+')
        radar = tk.Canvas(overlay, width=176, height=176, bg=BG, highlightthickness=0)
        radar.place(relx=0.5, rely=0.32, anchor='center')
        cx, cy, r = 88, 88, 74
        for rr in (r, r * 0.66, r * 0.33):
            radar.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, outline=BORDER, width=1)
        sweep = radar.create_line(cx, cy, cx, cy - r, fill=CYAN, width=2)
        dot = radar.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill=CYAN, outline='')
        state = {'angle': 0.0}
        def spin():
            state['angle'] = (state['angle'] + 8) % 360
            rad = math.radians(state['angle'] - 90)
            x = cx + r * math.cos(rad); y = cy + r * math.sin(rad)
            try: radar.coords(sweep, cx, cy, x, y)
            except Exception: pass
        self._pph7_anim.loop('boot:spin', 30, spin)
        tk.Label(overlay, text='PPH', bg=BG, fg=GREEN, font=font(self, 34, 'bold')).place(relx=0.5, rely=0.56, anchor='center')
        tk.Label(overlay, text='PULSE DECK', bg=BG, fg=CYAN, font=font(self, 11, 'bold')).place(relx=0.5, rely=0.63, anchor='center')
        rows = tk.Frame(overlay, bg=BG); rows.place(relx=0.5, rely=0.8, anchor='center')
        checks = ['DISPLAY', 'SYSTEM', 'NETWORK', 'RADIOS', 'FIELD SERVICES']
        labels = {}
        for c in checks:
            r2 = tk.Frame(rows, bg=BG); r2.pack(fill='x', pady=2)
            tk.Label(r2, text=c, bg=BG, fg=TEXT, font=font(self, 9, 'bold'), width=16, anchor='w').pack(side='left')
            v = tk.Label(r2, text='…', bg=BG, fg=MUTED, font=font(self, 9, 'bold')); v.pack(side='left')
            labels[c] = v
        state2 = {'i': 0}
        def step():
            if state2['i'] >= len(checks):
                self._pph7_anim.cancel('boot:spin')
                def finish():
                    try: overlay.destroy()
                    except Exception: pass
                    on_done()
                self._pph7_anim.after('boot:finish', 220, finish)
                return
            c = checks[state2['i']]; labels[c].configure(text='✓', fg=GREEN); state2['i'] += 1
            self._pph7_anim.after('boot:step', 170, step)
        self._pph7_anim.after('boot:step', 400, step)

    # =====================================================================
    # wiring
    # =====================================================================

    def build_pages(self):
        build_home(self); build_more(self)
        build_wireless(self); build_wireless_detail(self)
        build_radio_center(self); build_radio_detail(self)
        build_network(self); build_network_detail(self)
        build_access(self); build_access_detail(self); build_access_detail2(self); build_access_config(self)
        build_connection_flow(self)
        build_network_doctor(self)
        build_system(self); build_system_detail(self)
        build_hardware(self); build_storage(self)
        build_events(self); build_events_raw(self)
        build_settings(self); build_settings_detail(self)
        build_field(self); build_before_after(self); build_session(self)
        for name, title in (('tools', 'TOOLS'), ('lan_mapper', 'LAN MAPPER'), ('reports', 'REPORTS'), ('jobs3', 'JOBS'), ('notify50', 'NOTIFICATIONS')):
            build_generic(self, name, title)

        if not self._pph7_booted:
            self._pph7_booted = True
            def enter_home(): self.show_page('home3', push=False)
            play_boot(self, enter_home)

    def show_page(self, name, title=None, *, push=True):
        aliases = {'dashboard': 'home3', 'home412': 'home3', 'home411': 'home3', 'home41': 'home3', 'home32': 'home3', 'more6': 'more7',
                   'access41': 'access3', 'access411': 'access3', 'access412': 'access3',
                   'analyzer41': 'network', 'analyzer32': 'network', 'network412': 'network', 'network412b': 'network',
                   'wireless4': 'measure3', 'wireless41': 'measure3', 'wireless411': 'measure3', 'wireless412': 'measure3',
                   'wireless412b': 'measure3', 'doctor32': 'network_doctor', 'quick32': 'network_doctor', 'wifi32': 'wifi3'}
        name = aliases.get(name, name)
        old_name = getattr(self, 'current_page', None)
        new_frame = self.frames.get(name)
        if new_frame is None: return
        old_frame = self.frames.get(old_name) if old_name else None
        if old_name and old_name != name:
            self._pph7_anim.cancel_page(old_name)
        self.current_page = name
        self.page_title.set(self.page_titles.get(name, name.upper()))
        set_active_nav(self, self._pph7_nav_map.get(name, name))

        def finalize():
            for w in self.frames.values():
                if w is not new_frame: w.place_forget()
            new_frame.place(relx=0, rely=0, relwidth=1, relheight=1); new_frame.lift()

        if old_frame is None or old_frame is new_frame or not self.frames:
            finalize()
        else:
            def frame(t):
                try:
                    old_frame.place(relx=0, rely=0, relwidth=1, relheight=1, x=int(-W * t))
                    new_frame.place(relx=0, rely=0, relwidth=1, relheight=1, x=int(W * (1 - t)))
                    new_frame.lift()
                except Exception: pass
            self._pph7_anim.tween('nav:transition', 200, frame, on_done=finalize, tier='REDUCED', ease='out')

        refresher = self._pph7_refresh.get(name)
        if refresher:
            try: refresher()
            except Exception: pass
            interval = LIVE_PAGES.get(name)
            if interval:
                self._pph7_anim.loop(f'{name}:live', interval, refresher)
        try: self._pph29_trigger_update_check(False, f'page:{name}')
        except Exception: pass

    def go_home(self):
        self.show_page('home3', push=False)

    def toggle_fullscreen(self):
        pass

    cls._build_shell = build_shell
    cls._build_pages = build_pages
    cls.show_page = show_page
    cls.go_home = go_home
    cls.toggle_fullscreen = toggle_fullscreen
