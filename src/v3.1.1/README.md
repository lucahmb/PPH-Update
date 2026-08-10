# PPH 3.1.1 · Access Point Fix

Patch release for the PPH 3 Access Point module.

- Random WLAN password: exactly 12 numeric digits.
- Random laptop pairing token: exactly 12 numeric digits.
- Existing long tokens are replaced automatically on first start after update.
- The old `ChangeMe123!` default is replaced automatically.
- ACCESS UI shows and validates the 12-digit WLAN password.
- Laptop control v3.1.1 adds IP auto-discovery so it no longer depends on `homelab.local` resolving correctly.
