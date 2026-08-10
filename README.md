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

## UI-Layer testen, bevor released wird

Die aktuell aktive Bedienoberfläche (`pph_hub/pph51_ui.py` im Paket – der Dateiname bleibt über alle 5.1.x/5.2.x-Versionen hinweg gleich, auch wenn die Quelldatei unter `src/vX.Y.Z/` anders heißt, z. B. `pph52_ui.py`) wird bei jedem Redesign komplett neu geschrieben. Ein reiner String-Vergleich im Test ("kommt der Text X in der Datei vor?") merkt **nicht**, wenn dabei ein Tkinter-Fehler wie ein `pack`/`grid`-Konflikt eingebaut wird – genau das ist in 5.1.0 und danach nochmal in 5.2.0 passiert und hat PPH bei jedem Start abstürzen lassen (das Fenster flackerte nur noch auf und zu).

Deshalb: vor jedem Release, das `pph_hub/pph51_ui.py` verändert, `tools/ui_smoke_test.py` laufen lassen. Das baut die Datei mit echtem Tkinter (nicht nur String-Checks) gegen ein minimales Fake-App-Grundgerüst auf und rendert jede Seite aus dem `CORE`-Tupel:

```bash
sudo pacman -S tk xorg-server-xvfb   # einmalig, falls noch nicht installiert (Arch/CachyOS)
# bzw. sudo apt-get install -y python3-tk xvfb   # Debian/Ubuntu

xvfb-run -a python3 tools/ui_smoke_test.py <extrahiertes-payload-verzeichnis> pph_hub/pph51_ui.py
```

Exit-Code 0 heißt: jede Seite wurde tatsächlich mit Tk gebaut und angezeigt, ohne `TclError`. Der Workflow `.github/workflows/verify-stable-channel.yml` führt diesen Check zusätzlich automatisch bei jedem Push gegen das Paket aus, auf das `channels/stable.json` gerade zeigt – als Sicherheitsnetz, falls ein `build_release.py` den Aufruf vergisst.
