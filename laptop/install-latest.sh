#!/usr/bin/env bash
set -euo pipefail
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
REPO="lucahmb/PPH-Update"
VER="v6.0.1"
fetch_api_raw() {
  local path="$1" out="$2"
  python3 - "$REPO" "$path" "$out" <<'PY'
import sys, urllib.request
repo, path, out = sys.argv[1:]
url=f"https://api.github.com/repos/{repo}/contents/{path}?ref=main"
req=urllib.request.Request(url,headers={
    'User-Agent':'PPH-App-Control-Installer/6.0.1',
    'Accept':'application/vnd.github.raw+json',
    'Cache-Control':'no-cache',
    'Pragma':'no-cache',
})
with urllib.request.urlopen(req,timeout=20) as r:
    data=r.read()
open(out,'wb').write(data)
PY
}
fetch_api_raw "laptop/$VER/pph_ap_control.py" "$TMP/pph_ap_control.py"
fetch_api_raw "laptop/$VER/install.sh" "$TMP/install.sh"
chmod +x "$TMP/install.sh"
"$TMP/install.sh"
