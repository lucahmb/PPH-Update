#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="${PPH_PROJECT_ROOT:-$HOME/pph-funktest}"
PPH3_APP="$PROJECT_ROOT/pph_hub/pph3_app.py"
POLISHED_APP="$PROJECT_ROOT/pph_hub/polished_hub.py"
LEGACY_APP="$PROJECT_ROOT/pph_hub/pph_hub.py"
USER_UID="$(id -u)"
STATE_DIR="$HOME/.local/state/pph-hub"

mkdir -p "$STATE_DIR"

if [[ -f "$PPH3_APP" ]]; then
    APP="$PPH3_APP"
elif [[ -f "$POLISHED_APP" ]]; then
    APP="$POLISHED_APP"
elif [[ -f "$LEGACY_APP" ]]; then
    APP="$LEGACY_APP"
else
    echo "FEHLER: Keine PPH-Hub-Anwendung gefunden." >&2
    exit 1
fi

hub_running() {
    python3 - "$APP" "$USER_UID" <<'PYPROC'
import os
import sys
from pathlib import Path

target = str(Path(sys.argv[1]).resolve())
uid = int(sys.argv[2])
self_pid = os.getpid()
ancestors = {self_pid}
pid = os.getppid()

while pid > 1 and pid not in ancestors:
    ancestors.add(pid)
    try:
        fields = Path(f"/proc/{pid}/stat").read_text().split()
        pid = int(fields[3])
    except (OSError, ValueError, IndexError):
        break

for entry in Path("/proc").iterdir():
    if not entry.name.isdigit() or int(entry.name) in ancestors:
        continue
    try:
        if entry.stat().st_uid != uid:
            continue
        argv = (entry / "cmdline").read_bytes().split(b"\0")
        args = [item.decode(errors="replace") for item in argv if item]
        for arg in args[1:]:
            try:
                if str(Path(arg).resolve()) == target:
                    raise SystemExit(0)
            except OSError:
                continue
    except (OSError, PermissionError):
        continue

raise SystemExit(1)
PYPROC
}

if hub_running; then
    echo "PPH Hub läuft bereits."
    exit 0
fi

import_gui_environment() {
    local pid environment key value

    while read -r pid; do
        [[ -r "/proc/$pid/environ" ]] || continue
        environment="$(tr '\0' '\n' < "/proc/$pid/environ" 2>/dev/null || true)"
        [[ -n "$environment" ]] || continue

        while IFS='=' read -r key value; do
            case "$key" in
                DISPLAY|WAYLAND_DISPLAY|XDG_RUNTIME_DIR|DBUS_SESSION_BUS_ADDRESS|XAUTHORITY)
                    export "$key=$value"
                    ;;
            esac
        done <<< "$environment"

        if [[ -n "${DISPLAY:-}" || -n "${WAYLAND_DISPLAY:-}" ]]; then
            return 0
        fi
    done < <(
        pgrep -u "$USER_UID" -f \
            'labwc|wayfire|lxsession|Xwayland|weston|wf-panel-pi|pcmanfm|xfce4-session|gnome-shell' \
            2>/dev/null || true
    )

    return 1
}

if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
    import_gui_environment || true
fi

export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$USER_UID}"

if [[ -z "${DBUS_SESSION_BUS_ADDRESS:-}" && -S "$XDG_RUNTIME_DIR/bus" ]]; then
    export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
fi

if [[ -z "${DISPLAY:-}" ]]; then
    if [[ -S /tmp/.X11-unix/X0 ]]; then
        export DISPLAY=":0"
    elif [[ -S /tmp/.X11-unix/X1 ]]; then
        export DISPLAY=":1"
    fi
fi

if [[ -z "${XAUTHORITY:-}" && -f "$HOME/.Xauthority" ]]; then
    export XAUTHORITY="$HOME/.Xauthority"
fi

if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
    echo "Keine grafische Desktop-Sitzung gefunden. Nach einem Desktop-Login oder Reboot erneut starten." >&2
    exit 1
fi

# Gemeinsame Projektmodule liegen in $PROJECT_ROOT, Hub-Module in pph_hub/.
export PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/pph_hub${PYTHONPATH:+:$PYTHONPATH}"

cd "$PROJECT_ROOT"
exec /usr/bin/python3 "$APP"
