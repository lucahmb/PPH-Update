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
