"""R7 — Panen lowongan PLN dari Rekrutmen Bersama BUMN (RBB) via arsip Wayback.

Latar: 2021 & 2024 kosong di katalog rekrutmen.pln.co.id karena tahun itu PLN
merekrut lewat jalur PPB/RBB yang diumumkan di situs FHCI (F-041). Situs RBB
sudah mati (SSL error), tapi Wayback mengarsipkan endpoint data `/job/loadRecord/`
yang mengembalikan JSON berisi seluruh daftar lowongan.

Output -> knowledge/sources/rbb_fhci/
    raw_loadRecord_<tahun>.json     cache JSON mentah
    lowongan_pln_rbb.csv            baris lowongan milik PLN Group saja

Jalankan: recruitment_dashboard/.venv/Scripts/python.exe knowledge/build/r7_rbb_fhci.py
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import httpx

UA = {"User-Agent": "Mozilla/5.0 (compatible; PLN-Tower2-Research/1.0)"}
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "knowledge" / "sources" / "rbb_fhci"

# (tahun, timestamp snapshot, url endpoint)
SNAPSHOTS = [
    ("2024", "20240327", "https://rekrutmenbersama2024.fhcibumn.id/job/loadRecord/"),
]

# Kolom bermakna dari tiap record lowongan.
# CATATAN: `total_job_available` SENGAJA TIDAK dipakai sebagai kuota. Jumlahnya
# 1.777.000 untuk seluruh BUMN (RBB 2024 nyatanya merekrut ~5.900 orang) dan semua
# nilainya kelipatan 1.000 -> kemungkinan bobot tampilan internal, bukan formasi.
COLS = ["vacancy_name", "tenant_name", "vacancy_type", "stream_name",
        "allow_sma", "allow_d3", "allow_s1", "allow_s2",
        "highest_age_sma", "highest_age_d3", "highest_age_s1", "highest_age_s2",
        "lowest_ipk_sma", "lowest_ipk_d3", "lowest_ipk_s1", "lowest_ipk_s2",
        "check_certificate", "major_non_sma_custom", "major_sma_custom", "vacancy_id"]


def harvest(tahun: str, ts: str, url: str) -> list[dict]:
    OUT.mkdir(parents=True, exist_ok=True)
    cache = OUT / f"raw_loadRecord_{tahun}.json"
    if cache.exists() and cache.stat().st_size > 0:
        payload = cache.read_text(encoding="utf-8", errors="replace")
    else:
        r = httpx.get(f"https://web.archive.org/web/{ts}/{url}",
                      headers=UA, timeout=120, follow_redirects=True)
        r.raise_for_status()
        payload = r.text
        cache.write_text(payload, encoding="utf-8")
    data = json.loads(payload)
    result = data.get("data", {}).get("result", []) or []
    print(f"  {tahun}: {len(result):,} lowongan total (semua BUMN)")
    return result


def main() -> int:
    rows: list[dict] = []
    for tahun, ts, url in SNAPSHOTS:
        try:
            records = harvest(tahun, ts, url)
        except Exception as e:  # noqa: BLE001
            print(f"  {tahun}: GAGAL — {e}")
            continue
        # kunci semua nama field yang tersedia (buat dokumentasi skema)
        if records:
            print(f"     field tersedia: {', '.join(sorted(records[0].keys()))}")
        pln = [r for r in records
               if re.search(r"\bPLN\b|Perusahaan Listrik Negara", str(r.get("tenant_name", "")), re.I)]
        print(f"     -> milik PLN Group: {len(pln)}")
        for r in pln:
            rec = {"tahun": tahun}
            for c in COLS:
                if c in r:
                    v = r[c]
                    rec[c] = re.sub(r"\s+", " ", str(v)).strip() if v is not None else ""
            # simpan sisa field yang belum tertangkap
            extra = {k: v for k, v in r.items() if k not in COLS and v not in (None, "")}
            rec["_lain"] = json.dumps(extra, ensure_ascii=False)[:400]
            rows.append(rec)

    if not rows:
        print("\nTidak ada baris PLN yang terpanen.")
        return 1

    cols = ["tahun"] + [c for c in COLS if any(c in r for r in rows)] + ["_lain"]
    with (OUT / "lowongan_pln_rbb.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"\nselesai -> {OUT / 'lowongan_pln_rbb.csv'} ({len(rows)} baris)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
