"""R1 — Scrape katalog program dari rekrutmen.pln.co.id (data publik).

Sopan: User-Agent deskriptif, jeda antar request, cache ke disk (skip kalau sudah
ada -> resumable & tidak membebani server). robots.txt dicek 404 (tak ada batasan).

Output -> knowledge/sources/rekrutmen_pln/
    raw/list/page_<n>.html         cache HTML listing
    raw/detail/<id>.html           cache HTML tiap program
    pdf/<file>.pdf                 brosur program (dedup per URL)
    programs.csv                   1 baris per program (field listing + detail)
    programs.json                  versi lengkap (termasuk semua pasangan label)

Jalankan: recruitment_dashboard/.venv/Scripts/python.exe knowledge/build/r1_scrape_rekrutmen.py
"""
from __future__ import annotations

import csv
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import unquote, urljoin

import httpx
from bs4 import BeautifulSoup

BASE = "https://rekrutmen.pln.co.id"
INDEX = f"{BASE}/vacancy/site/index"
UA = "Mozilla/5.0 (compatible; PLN-Tower2-Research/1.0; internal recruitment analytics)"
DELAY = 1.3  # detik antar request
MAX_PAGES = 25  # pengaman kalau deteksi paginasi gagal

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "knowledge" / "sources" / "rekrutmen_pln"
RAW_LIST = OUT / "raw" / "list"
RAW_DETAIL = OUT / "raw" / "detail"
PDF_DIR = OUT / "pdf"

MONTHS = ("januari|februari|maret|april|mei|juni|juli|agustus|"
          "september|oktober|november|desember")
DATE_RE = re.compile(rf"(\d{{1,2}})\s+({MONTHS})\s+(\d{{4}})", re.I)

# label listing -> nama kolom
LABEL_MAP = {
    "minat profesi": "minat_profesi",
    "jenjang pendidikan": "jenjang",
    "program studi": "program_studi",
    "unit": "unit",
    "bidang": "bidang",
}


def fetch(client: httpx.Client, url: str, cache: Path, *, binary: bool = False):
    """GET dengan cache disk + jeda sopan. Return teks (atau bytes kalau binary)."""
    if cache.exists() and cache.stat().st_size > 0:
        return cache.read_bytes() if binary else cache.read_text(encoding="utf-8", errors="replace")
    time.sleep(DELAY)
    r = client.get(url)
    r.raise_for_status()
    cache.parent.mkdir(parents=True, exist_ok=True)
    if binary:
        cache.write_bytes(r.content)
        print(f"    unduh {cache.name}  ({len(r.content)//1024} KB)")
        return r.content
    cache.write_text(r.text, encoding="utf-8")
    return r.text


def detect_last_page(soup: BeautifulSoup) -> int:
    nums = [int(m.group(1)) for a in soup.select("a[href]")
            if (m := re.search(r"CcnEmployerVacancy_page/(\d+)", a.get("href", "")))]
    return max(nums) if nums else 1


def parse_listing(html: str, page: int) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    out = []
    for a in soup.select("a.title[href*='/vacancy/site/view/id/']"):
        card = a.find_parent("div", class_="box") or a.parent
        pid = re.search(r"/view/id/([\w-]+)", a["href"]).group(1)
        rec = {
            "program_id": pid,
            "title": a.get_text(strip=True),
            "detail_url": urljoin(BASE, a["href"]),
            "listing_page": page,
        }
        loc = card.find("span", class_="location")
        if loc:
            rec["lokasi_tes"] = re.sub(r"^\s*Lokasi Tes\s*", "", loc.get_text(" ", strip=True))
        extra = {}
        for desc in card.select("div.desc"):
            lab = desc.find("label")
            if not lab:
                continue
            key = lab.get_text(strip=True)
            val = desc.get_text(" ", strip=True)
            val = re.sub(rf"^\s*{re.escape(key)}\s*", "", val).strip()
            col = LABEL_MAP.get(key.lower())
            (rec if col else extra)[col or key] = val
        if extra:
            rec["_extra_listing"] = extra
        out.append(rec)
    return out


# label yang diambil dari tiap blok "Minat Profesi" di halaman detail
PROFESI_LABELS = {
    "Dibuka": "tgl_buka", "Ditutup": "tgl_tutup", "Jenjang": "jenjang",
    "Nama Profesi": "nama_profesi", "Kota Rekrutmen": "kota_rekrutmen",
    "Kode Profesi": "kode_profesi", "Angkatan": "angkatan",
    "Minimal IPK": "minimal_ipk", "Program Studi": "program_studi",
}


def _value_after(label) -> str:
    """Teks sesudah <label> di dalam parent-nya, berhenti di <label> berikutnya."""
    parts = []
    for sib in label.next_siblings:
        if getattr(sib, "name", None) == "label":
            break
        t = sib.get_text(" ", strip=True) if hasattr(sib, "get_text") else str(sib).strip()
        if t:
            parts.append(t)
    return re.sub(r"\s+", " ", " ".join(parts)).strip(" :")


def parse_detail(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True)
    rec: dict = {}

    low = text.lower()
    if "sudah tutup" in low or "ditutup" in low:
        rec["status"] = "CLOSED"
    elif "masih dibuka" in low or "sedang dibuka" in low:
        rec["status"] = "OPEN"

    # --- blok profesi (granular: per jenjang x rumpun jurusan) ---
    profesi = []
    for head in soup.find_all(string=re.compile(r"Minat Profesi")):
        blk = head
        for _ in range(8):  # naik sampai container yang memuat 'Kode Profesi'
            blk = blk.parent
            if blk is None:
                break
            if blk.find("label", string=re.compile("Kode Profesi")):
                break
        if blk is None:
            continue
        p = {}
        for lab in blk.find_all("label"):
            col = PROFESI_LABELS.get(lab.get_text(strip=True))
            if col and col not in p:
                p[col] = _value_after(lab)
        if p.get("kode_profesi"):
            # IPK numerik representatif (nilai 'minimal X' yang paling sering)
            nums = re.findall(r"minimal\s*([\d.,]+)", p.get("minimal_ipk", ""), re.I)
            if nums:
                p["min_ipk"] = max(set(nums), key=nums.count).replace(",", ".")
            profesi.append(p)
    # dedup blok identik (kadang heading berulang)
    seen, uniq = set(), []
    for p in profesi:
        key = (p.get("kode_profesi"), p.get("jenjang"), p.get("nama_profesi"))
        if key not in seen:
            seen.add(key)
            uniq.append(p)
    rec["_profesi"] = uniq
    if uniq:  # promosikan tanggal & angkatan ke level program
        rec.setdefault("tgl_buka", uniq[0].get("tgl_buka"))
        rec.setdefault("tgl_tutup", uniq[0].get("tgl_tutup"))
        rec["angkatan"] = "; ".join(sorted({p["angkatan"] for p in uniq if p.get("angkatan")}))
        rec["kode_profesi"] = "; ".join(sorted({p["kode_profesi"] for p in uniq if p.get("kode_profesi")}))
    else:  # fallback tanggal dari regex kalau blok tak terbaca
        dates = [f"{d} {m.title()} {y}" for d, m, y in DATE_RE.findall(text)]
        if dates:
            rec["tgl_buka"] = dates[0]
        if len(dates) > 1:
            rec["tgl_tutup"] = dates[1]

    pdfs = []
    for a in soup.select("a[href]"):
        h = a["href"]
        if re.search(r"\.pdf(\?|$)", h, re.I) or re.search(r"/public/recruitment/", h, re.I):
            pdfs.append(urljoin(BASE, h))
    rec["_pdf_urls"] = sorted(set(pdfs))
    return rec


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": UA, "Accept-Language": "id-ID,id;q=0.9"}
    with httpx.Client(headers=headers, timeout=40, follow_redirects=True) as client:
        # 1) listing
        print("== LISTING ==")
        html1 = fetch(client, INDEX, RAW_LIST / "page_1.html")
        last = min(detect_last_page(BeautifulSoup(html1, "lxml")), MAX_PAGES)
        print(f"  total halaman: {last}")
        programs: list[dict] = []
        for p in range(1, last + 1):
            url = INDEX if p == 1 else f"{INDEX}/CcnEmployerVacancy_page/{p}"
            html = html1 if p == 1 else fetch(client, url, RAW_LIST / f"page_{p}.html")
            cards = parse_listing(html, p)
            print(f"  page {p}: {len(cards)} program")
            programs.extend(cards)
        # dedup by id (jaga2 kalau ada overlap antar halaman)
        uniq = {r["program_id"]: r for r in programs}
        programs = list(uniq.values())
        print(f"  total program unik: {len(programs)}")

        # 2) detail + PDF
        print("\n== DETAIL + PDF ==")
        pdf_seen: dict[str, str] = {}
        profesi_rows: list[dict] = []
        for i, rec in enumerate(programs, 1):
            html = fetch(client, rec["detail_url"], RAW_DETAIL / f"{rec['program_id']}.html")
            det = parse_detail(html)
            for p in det.pop("_profesi", []):
                profesi_rows.append({
                    "program_id": rec["program_id"],
                    "program_title": rec["title"],
                    **p,
                })
            local_pdfs = []
            for purl in det.pop("_pdf_urls", []):
                if purl not in pdf_seen:
                    fname = unquote(purl.rsplit("/", 1)[-1])
                    fname = re.sub(r"[^\w.\- ]+", "_", fname)[:120]
                    try:
                        fetch(client, purl, PDF_DIR / fname, binary=True)
                        pdf_seen[purl] = fname
                    except Exception as e:  # noqa: BLE001
                        print(f"    ! gagal unduh PDF {purl}: {e}")
                        continue
                local_pdfs.append(pdf_seen[purl])
            rec.update(det)
            rec["pdf_files"] = "; ".join(local_pdfs)
            if i % 10 == 0 or i == len(programs):
                print(f"  {i}/{len(programs)} program diproses")

    # 3) tulis output
    (OUT / "programs.json").write_text(
        json.dumps(programs, ensure_ascii=False, indent=2), encoding="utf-8")

    cols = ["program_id", "title", "status", "jenjang", "angkatan", "kode_profesi",
            "lokasi_tes", "tgl_buka", "tgl_tutup", "minat_profesi", "program_studi",
            "pdf_files", "detail_url", "listing_page"]
    with (OUT / "programs.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in programs:
            w.writerow(r)

    pcols = ["program_id", "kode_profesi", "angkatan", "jenjang", "nama_profesi",
             "kota_rekrutmen", "tgl_buka", "tgl_tutup", "min_ipk", "program_studi",
             "minimal_ipk", "program_title"]
    with (OUT / "profesi.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=pcols, extrasaction="ignore")
        w.writeheader()
        for r in profesi_rows:
            w.writerow(r)

    print(f"\nselesai -> {OUT}")
    print(f"  programs.csv/json : {len(programs)} program")
    print(f"  profesi.csv       : {len(profesi_rows)} profesi (granular)")
    print(f"  pdf/              : {len(list(PDF_DIR.glob('*.pdf'))) if PDF_DIR.exists() else 0} berkas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
