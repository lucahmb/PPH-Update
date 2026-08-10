#!/usr/bin/env python3
"""Real-Tk smoke test for a PPH top-level UI layer's install(cls, ns) function.

String-matching tests (assert "some text" in source) cannot catch a Tk
geometry-manager conflict: PPH shipped with exactly that bug twice (5.1.0 and
again 5.2.0) because card()/two_cards() mixed pack() and grid() on the same
parent widget, and nothing ever actually built the widget tree to find out.

This tool does: it loads the given install(cls, ns) function against a
minimal fake host app backed by a REAL Tk root, calls _build_pages() (which
constructs every page) and then show_page() for every page the module
declares in its CORE tuple, under whatever real or virtual (Xvfb) X display
is available. Any pack/grid mix, bad font spec, missing widget option, etc.
surfaces as a real _tkinter.TclError - not a guess.

Only stdlib-only top-level UI modules (import subprocess/tkinter/typing, no
"from hardware_roles import ..." style dependencies on modules that live
outside this repo) can be smoke-tested this way; that has been true for
every pph5x_ui.py so far because it's the layer these UI-redesign sessions
actually rewrite.

Usage:
    python3 tools/ui_smoke_test.py <payload_dir> [module/relative/path.py]

    payload_dir            Directory containing pph_hub/... (an extracted
                            package's payload/ folder).
    module/relative/path    Defaults to pph_hub/pph51_ui.py - the stable slot
                            name every 5.1.x/5.2.x release installs its
                            top-level UI layer as, regardless of the source
                            file's own version-specific name.

Exit code 0 = every CORE page built and rendered without error.
Requires a real or Xvfb-backed DISPLAY (see: xvfb-run -a python3 ...).
"""
from __future__ import annotations

import importlib.util
import sys
import tkinter as tk
from pathlib import Path
from unittest.mock import MagicMock


class _FakeAccessPoint:
    """Stands in for access_point.AccessPointController so build_access()
    never constructs the real thing (which spawns background threads, binds
    a network port, and shells out to nmcli/iw)."""

    token = "0000"
    config = {"ssid": "PPH-WIFI", "band": "a", "password": "000000000000"}

    def status(self) -> dict:
        return {}


class FakeApp:
    """Minimal stand-in for the real PolishedPPHApp base class.

    Layout primitives (_new_page, _font, _button, _header_button, frames,
    StringVars, ...) are real, so real widgets get built and real Tk errors
    surface. Everything else (domain/business-logic methods the UI layer
    might reference as a button command, like launch_funktest or
    _pph28_open_update) falls back to a cached MagicMock via __getattr__, so
    a smoke test never fails on a missing unrelated method - only on an
    actual Tk construction error.
    """

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.content = tk.Frame(root)
        self.content.pack(fill="both", expand=True)
        self.frames: dict[str, tk.Widget] = {}
        self.pages = self.frames
        self.page_titles: dict[str, str] = {}
        self.navigation_stack: list[str] = []
        self.current_page = ""
        self.footer_var = tk.StringVar(value="")
        self.page_title = tk.StringVar(value="")
        self.clock_var = tk.StringVar(value="--:--")
        self.back_button = tk.Button(root)
        self.pph31_ap = _FakeAccessPoint()
        self._fake_cache: dict[str, MagicMock] = {}

    # --- required by every install(cls, ns): read via `cls.X` before being
    # wrapped, so these must exist as real callables ahead of time.
    def _build_pages(self) -> None:
        pass

    def show_page(self, name: str, title: str | None = None, *, push: bool = True) -> None:
        frame = self.frames.get(name)
        if frame is None:
            return
        for f in self.frames.values():
            f.pack_forget()
        frame.pack(fill="both", expand=True)
        self.current_page = name

    def go_home(self) -> None:
        self.show_page("home3", push=False)

    def toggle_fullscreen(self) -> None:
        pass

    # --- layout primitives every pph5x_ui.py install() calls directly.
    def _new_page(self, name: str, title: str) -> tk.Frame:
        frame = tk.Frame(self.content)
        self.frames[name] = frame
        self.page_titles[name] = title
        return frame

    def _font(self, size: int, weight: str = "normal"):
        return ("TkDefaultFont", size, weight)

    def _button(self, parent, text, command, bg=None, active=None, size=10, pady=6, padx=None):
        return tk.Button(parent, text=text, command=command)

    def _header_button(self, parent, text, command):
        return tk.Button(parent, text=text, command=command)

    # --- safe catch-all for every domain method this layer merely references.
    def __getattr__(self, name: str):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        if name not in self._fake_cache:
            self._fake_cache[name] = MagicMock(name=name)
        return self._fake_cache[name]


def _load_install(module_path: Path, payload_dir: Path):
    for extra in (str(module_path.parent), str(payload_dir)):
        if extra not in sys.path:
            sys.path.insert(0, extra)
    spec = importlib.util.spec_from_file_location("_pph_ui_under_test", module_path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"could not load module spec for {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "install"):
        raise SystemExit(f"{module_path} has no install(cls, ns) function")
    return module


def run(payload_dir: Path, module_rel_path: str) -> None:
    module_path = payload_dir / module_rel_path
    if not module_path.is_file():
        raise SystemExit(f"UI module not found: {module_path}")
    module = _load_install(module_path, payload_dir)

    module.install(FakeApp, {})

    root = tk.Tk()
    try:
        app = FakeApp(root)
        build_shell = getattr(type(app), "_build_shell", None)
        if build_shell is not None:
            try: app.content.destroy()
            except Exception: pass
            build_shell(app)
        app._build_pages()
        core = getattr(module, "CORE", tuple(app.frames.keys()))
        if not core:
            raise SystemExit("module exposes no CORE pages to exercise")
        built = set(app.frames.keys())
        missing = [name for name in core if name not in built]
        if missing:
            raise SystemExit(f"_build_pages() never created these CORE pages: {missing}")
        for name in core:
            app.show_page(name)
            root.update_idletasks()
    finally:
        root.destroy()

    print(f"ui_smoke_test OK: {module_rel_path} built and rendered {len(core)} CORE pages")


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        raise SystemExit(__doc__)
    payload_dir = Path(sys.argv[1]).resolve()
    module_rel_path = sys.argv[2] if len(sys.argv) == 3 else "pph_hub/pph51_ui.py"
    run(payload_dir, module_rel_path)
