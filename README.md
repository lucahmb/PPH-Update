# PPH Update Repository

Offizielle öffentliche Updatequelle für die PPH Network Suite.

## Struktur

- `channels/stable.json` – aktuell veröffentlichte Stable-Version
- `packages/vX.Y.Z/` – unveränderliche Update-Pakete
- `bootstrap.sh` – manueller Fallback zum Abrufen und Installieren des aktuellen Stable-Pakets

Der Raspberry Pi benötigt keinen GitHub-Token. Er liest nur den öffentlichen Stable-Channel, verifiziert die SHA-256-Prüfsumme und übergibt das Paket anschließend an den lokalen PPH-Updater mit Backup, Migrationen, Tests und Rollback.

## Versionsschema

PPH verwendet `MAJOR.MINOR.PATCH`, z. B. `2.9.0`.

Neue Stable-Versionen werden veröffentlicht, indem zuerst das Paket unter `packages/vX.Y.Z/` abgelegt und danach `channels/stable.json` auf diese Version aktualisiert wird. Dadurch zeigt der Stable-Channel nie auf ein Paket, das noch nicht vorhanden ist.

## UI-Architektur ab 6.0.0: eine einzige autoritative Schicht

Bis 5.2.x wurde jedes Redesign als weiterer Theme-Layer auf die vorherigen gestapelt (`pph3_ui` → `pph32_ui` → `pph4_theme` → … → `pph51_ui`), wobei jeder neue Layer `_build_pages`/`show_page` der vorherigen Version umschloss. Das führte wiederholt zu Bugs, weil neue Redesigns von einer älteren, teils schon gepatchten Kopie kopiert wurden.

Seit **PPH 6.0.0** gibt es nur noch eine autoritative UI-Datei: `pph_hub/pph6_ui.py`. Sie wird in `pph3_app.py` als letzter Layer installiert und ruft die vorherige `_build_shell`/`_build_pages`/`show_page`-Kette **nicht** mehr auf – die älteren Layer laufen zwar noch (harmlos, sie patchen nur Methoden, die pph6_ui sofort wieder überschreibt), bauen aber keine einzige Seite mehr. Backend-Hooks (Messengine, `AccessPointController`, Update-Checker, `hardware_roles`) werden direkt aus `pph6_ui.py` heraus genutzt.

**Für zukünftige Redesigns:** Als Ausgangsbasis immer die aktuell verpackte `pph_hub/pph6_ui.py` (bzw. deren Nachfolgeversion) nehmen, nie eine ältere `src/vX.Y.Z/`-Kopie – sonst schleichen sich bereits gefixte Bugs wieder ein, wie es zwischen 5.1.2 und 5.2.0 passiert ist. `manifest.json` jedes Pakets ab 6.0.0 enthält ein `ui_module`-Feld, das die aktuell aktive Datei benennt.

## UI-Layer testen, bevor released wird

Ein reiner String-Vergleich im Test ("kommt der Text X in der Datei vor?") merkt **nicht**, wenn ein Redesign einen Tkinter-Fehler wie einen `pack`/`grid`-Konflikt oder einen falschen Funktionsaufruf (fehlendes `self`) einbaut – genau das ist in 5.1.0, 5.2.0 und 5.2.2 passiert und hat PPH bei jedem Start abstürzen lassen (das Fenster flackerte nur auf und zu, oder die Seite baute sich gar nicht erst auf).

Deshalb: vor jedem Release, das die aktuelle UI-Datei verändert, `tools/ui_smoke_test.py` laufen lassen. Das baut die Datei mit echtem Tkinter (nicht nur String-Checks) gegen ein minimales Fake-App-Grundgerüst auf und rendert jede Seite:

```bash
sudo pacman -S tk xorg-server-xvfb   # einmalig, falls noch nicht installiert (Arch/CachyOS)
# bzw. sudo apt-get install -y python3-tk xvfb   # Debian/Ubuntu

xvfb-run -a python3 tools/ui_smoke_test.py <extrahiertes-payload-verzeichnis> pph_hub/pph6_ui.py
```

Exit-Code 0 heißt: jede Seite wurde tatsächlich mit Tk gebaut und angezeigt, ohne `TclError`. Ab `src/v6.0.0/build_release.py` ist dieser Check **fester Bestandteil des Build-Skripts selbst** (nicht nur der CI) – ein Build, der nicht rendert, erzeugt kein Paket. Der Workflow `.github/workflows/verify-stable-channel.yml` führt den Check zusätzlich bei jedem Push gegen das Paket aus, auf das `channels/stable.json` gerade zeigt, und liest dafür das `ui_module`-Feld aus `manifest.json` (Fallback: `pph_hub/pph51_ui.py` für ältere Pakete ohne dieses Feld).
