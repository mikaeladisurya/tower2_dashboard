"""Konfigurasi pytest bersama untuk tests/.

Menaruh root v3 di sys.path sekali di sini, supaya tiap berkas tes (uji_*.py)
cukup `from core import metrics` tanpa mengulang
`sys.path.insert(0, str(Path(__file__).resolve().parents[1]))` di kepala
masing-masing berkas — pola yang dipakai recruitment_dashboardv2/tests/ dan
duplikatif di tiap berkas.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
