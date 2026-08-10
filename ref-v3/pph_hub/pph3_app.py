#!/usr/bin/env python3
from __future__ import annotations

import polished_hub as hub
from pph3_ui import install

install(hub.PolishedPPHApp, vars(hub))

if __name__ == "__main__":
    raise SystemExit(hub.main())
