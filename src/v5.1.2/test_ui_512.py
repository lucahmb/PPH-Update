from pathlib import Path
import py_compile
ROOT = Path(__file__).resolve().parent
HUB = ROOT / "pph_hub"
ui = HUB / "pph51_ui.py"
py_compile.compile(str(ui), doraise=True)
text = ui.read_text()
assert "g.grid_columnconfigure" not in text, "two_cards() must not grid into a frame that card() never parented widgets on"
assert "left.pack(side='left'" in text and "right.pack(side='left'" in text, "two_cards() must place its cards with pack, matching the page's other pack-managed children"
print("PPH 5.1.2 startup crash fix tests OK")
