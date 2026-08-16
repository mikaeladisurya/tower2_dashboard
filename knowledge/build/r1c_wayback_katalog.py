"""R1c — Pulihkan katalog program historis dari Wayback Machine.

Latar: sistem HTD mencatat 222 rekrutmen, tapi web publik hanya menampilkan 31
(F-021). Sisanya diarsip/dihapus. Snapshot web.archive.org 2017-2026 bisa
memulihkan judul-judul program yang sudah hilang.

Sopan: jeda antar request + cache ke disk (resumable, tidak membebani archive.org).

Output -> knowledge/sources/rekrutmen_pln/wayback/
    raw/<timestamp>.html          cache snapshot
    programs_historis.csv         judul program unik + kapan terlihat
Jalankan: recruitment_dashboard/.venv/Scripts/python.exe knowledge/build/r1c_wayback_katalog.py
"""
from __future__ import annotations

import csv
import json
import re
import time
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

CDX = "http://web.archive.org/cdx/search/cdx"
TARGET = "rekrutmen.pln.co.id/vacancy/site/index*"
UA = {"User-Agent": "Mozilla/5.0 (compatible; PLN-Tower2-Research/1.0; internal analytics)"}
DELAY = 1.5

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "knowledge" / "sources" / "rekrutmen_pln" / "wayback"
RAW = OUT / "raw"


def list_snapshots(client: httpx.Client) -> list[tuple[str, str]]:
    r = client.get(CDX, params={"url": TARGET, "output": "json",
                                "collapse": "digest", "filter": "statuscode:200"}, timeout=90)
    rows = json.loads(r.text)
    hdr = rows[0]
    ts_i, orig_i = hdr.index("timestamp"), hdr.index("original")
    return [(row[ts_i], row[orig_i]) for row in rows[1:]]


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    seen: dict[str, dict] = {}          # judul -> info
    per_snapshot: list[tuple[str, int]] = []

    with httpx.Client(headers=UA, timeout=90, follow_redirects=True) as client:
        snaps = list_snapshots(client)
        print(f"{len(snaps)} snapshot ditemukan (2017-2026)\n")

        for i, (ts, orig) in enumerate(snaps, 1):
            cache = RAW / f"{ts}.html"
            if cache.exists() and cache.stat().st_size > 0:
                html = cache.read_text(encoding="utf-8", errors="replace")
            else:
                time.sleep(DELAY)
                url = f"https://web.archive.org/web/{ts}/{orig}"
                try:
                    r = client.get(url)
                    if r.status_code != 200:
                        print(f"  [{i}/{len(snaps)}] {ts} -> HTTP {r.status_code}, lewati")
                        continue
                    html = r.text
                    cache.write_text(html, encoding="utf-8")
                except Exception as e:  # noqa: BLE001
                    print(f"  [{i}/{len(snaps)}] {ts} -> ERR {e}")
                    continue

            soup = BeautifulSoup(html, "lxml")
            titles = []
            for a in soup.select("a.title"):
                t = re.sub(r"\s+", " ", a.get_text(strip=True)).strip()
                if not t:
                    continue
                titles.append(t)
                rec = seen.setdefault(t, {"judul": t, "pertama": ts, "terakhir": ts, "n": 0})
                rec["n"] += 1
                rec["pertama"] = min(rec["pertama"], ts)
                rec["terakhir"] = max(rec["terakhir"], ts)
            per_snapshot.append((ts, len(titles)))
            if i % 20 == 0 or i == len(snaps):
                print(f"  [{i}/{len(snaps)}] {ts[:6]} — kumulatif judul unik: {len(seen)}")

    rows = sorted(seen.values(), key=lambda r: r["pertama"])
    for r in rows:
        r["pertama_terlihat"] = f"{r['pertama'][:4]}-{r['pertama'][4:6]}"
        r["terakhir_terlihat"] = f"{r['terakhir'][:4]}-{r['terakhir'][4:6]}"
        m = re.search(r"\b(20\d\d)\b", r["judul"])
        r["tahun_di_judul"] = m.group(1) if m else ""
    with (OUT / "programs_historis.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=["judul", "tahun_di_judul", "pertama_terlihat",
                                           "terakhir_terlihat", "n"], extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(f"\nselesai -> {OUT}")
    print(f"  snapshot terbaca : {len(per_snapshot)}")
    print(f"  judul unik       : {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
