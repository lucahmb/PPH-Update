# PPH AP Laptop Control 3.1.1

The downloadable laptop bundle no longer depends on `homelab.local`.

- Tries `homelab.local` and `homelab` first.
- If name resolution fails, scans the laptop's local `/24` for the PPH `/health` endpoint on TCP 8788.
- Saves the discovered host/IP in `~/.config/pph-ap-client.json`.
- Accepts the new 12-digit numeric PPH token.
- WLAN passwords entered through the client must be exactly 12 numeric digits.
