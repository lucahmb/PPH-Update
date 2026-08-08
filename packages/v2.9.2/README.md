# PPH 2.9.2 Restart Fix

Fixes the display restart path after an update.

- installs `pph-hub.service`, `pph-status.service`, and `pph-monitor.service`
- adds a robust restart helper using `systemd-run`
- falls back to `start_pph_hub.sh` if the Hub service fails
- does not change measurement logic or hardware configuration

Package: `pph-update-2.9.2-restart-fix.tar.gz`
SHA-256: `abc4dc96514a0348ec04418c8c2e5febde9b3923d448202eaf84eb5339ac3cfb`
