from __future__ import annotations

from pathlib import Path

import pph_version


def test_version_300():
    assert pph_version.VERSION == "3.0.0"
    assert pph_version.CHANNEL == "stable"


def test_pph3_launcher_installs_overlay_before_main():
    launcher = (Path(__file__).parent / "pph_hub" / "pph3_app.py").read_text(encoding="utf-8")
    assert "install(hub.PolishedPPHApp, vars(hub))" in launcher
    assert "hub.main()" in launcher


def test_start_script_prefers_pph3_launcher():
    text = (Path(__file__).parent / "start_pph_hub.sh").read_text(encoding="utf-8")
    assert 'PPH3_APP="$PROJECT_ROOT/pph_hub/pph3_app.py"' in text
    assert 'APP="$PPH3_APP"' in text


def test_pph3_has_primary_navigation_and_update_button():
    text = (Path(__file__).parent / "pph_hub" / "pph3_ui.py").read_text(encoding="utf-8")
    for label in ("HOME", "MEASURE", "WIFI", "SYSTEM", "JOBS", "EVENTS", "SETTINGS"):
        assert f'("{label}"' in text
    assert 'text="CHECK UPDATES"' in text
