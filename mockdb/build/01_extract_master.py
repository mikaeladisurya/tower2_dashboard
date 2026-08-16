"""Ekstrak master data struktural dari DAPEG (Sample-03 sheet 'Sheet1') + FTK unit holding.

PENTING soal PII: file sumber berisi nama pegawai & NIP asli. Skrip ini SENGAJA
hanya mengeluarkan agregat struktural (daftar unit, katalog posisi, jumlah pegawai
per posisi per unit). Tidak ada satu pun kolom identitas orang yang ditulis ke output.

Kunci yang dipakai (hasil verifikasi granularitas):
    unit induk     -> 'Organisasi 2' (nama org), BUKAN CoCd.
                      CoCd 5200 dipakai bersama UID Jateng & UID Yogyakarta (unit baru).
    unit pelaksana -> 'BusA' (Business Area). 'Organisasi 3' TIDAK dipakai sebagai kunci
                      karena untuk pegawai kantor induk isinya BIDANG/DIREKTORAT,
                      bukan unit pelaksana. Nama panjang diambil dari Organisasi 3
                      hanya bila diawali 'UNIT '.

Output -> mockdb/out/master/
    unit_induk.csv            unit induk (+ Kantor Pusat) + FTK & realisasi
    unit_pelaksana.csv        unit pelaksana beserta induknya
    jabatan_katalog.csv       katalog nama posisi unik + jenjang
    posisi_unit_induk.csv     jumlah pegawai per (unit induk x posisi x jenjang)
    posisi_unit_pelaksana.csv jumlah pegawai per (unit pelaksana x posisi x jenjang)

Jalankan: python mockdb/build/01_extract_master.py
"""
from __future__ import annotations

import csv
import re
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data sintetis" / "Sample-03-Realisasi Pemenuhan FTK_April 2026.xlsx"
OUT = ROOT / "mockdb" / "out" / "master"

NS_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
SHEET_DAPEG = "xl/worksheets/sheet4.xml"
SHEET_FTK = "xl/worksheets/sheet3.xml"

# Prefix nama unit induk -> jenis unit. Diurutkan: yang lebih panjang dicek duluan.
JENIS_UNIT_INDUK = [
    ("UNIT INDUK PENYALURAN DAN PUSAT PENGATUR BEBAN", "UIP3B"),
    ("UNIT INDUK PUSAT PENGATUR BEBAN", "UIP2B"),
    ("UNIT INDUK PEMBANGKITAN", "UIK"),
    ("UNIT INDUK PEMBANGUNAN", "UIP"),
    ("UNIT INDUK DISTRIBUSI", "UID"),
    ("UNIT INDUK TRANSMISI", "UIT"),
    ("UNIT INDUK WILAYAH", "UIW"),
    ("PUSAT", "PUSAT"),
]


def col_index(ref: str) -> int:
    """'BC12' -> 54 (0-based kolom)."""
    letters = re.match(r"([A-Z]+)", ref or "A").group(1)
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def load_shared_strings(z: zipfile.ZipFile) -> list[str]:
    out: list[str] = []
    if "xl/sharedStrings.xml" not in z.namelist():
        return out
    with z.open("xl/sharedStrings.xml") as fh:
        for _, el in ET.iterparse(fh, events=("end",)):
            if el.tag == NS_MAIN + "si":
                out.append("".join(t.text or "" for t in el.iter(NS_MAIN + "t")))
                el.clear()
    return out


def iter_rows(z: zipfile.ZipFile, sheet: str, shared: list[str]):
    """Yield dict {col_index: value} per baris, streaming (hemat memori)."""
    with z.open(sheet) as fh:
        for _, el in ET.iterparse(fh, events=("end",)):
            if el.tag != NS_MAIN + "row":
                continue
            row: dict[int, str] = {}
            for cell in el:
                v = cell.find(NS_MAIN + "v")
                if v is None or v.text is None:
                    text = ""
                elif cell.get("t") == "s":
                    i = int(v.text)
                    text = shared[i] if i < len(shared) else ""
                else:
                    text = v.text
                row[col_index(cell.get("r"))] = text.strip()
            yield row
            el.clear()


def parse_jenjang(raw: str) -> tuple[str, str]:
    """'Generalist 1 (G1) - 10' -> ('G1', '10'). 'Manajemen Dasar (MD) - 16' -> ('MD','16').

    Kode jenjang boleh mengandung angka (G1/G2/G3) -- kalau kelasnya cuma [A-Z]+,
    seluruh jenjang generalist (34rb dari 37rb pegawai) diam-diam jadi kosong.
    """
    m = re.search(r"\(([A-Z0-9]+)\)\s*-\s*(\d+)", raw or "")
    return (m.group(1), m.group(2)) if m else ("", "")


def jenis_unit_induk(nama: str) -> str:
    up = (nama or "").upper()
    if "KANTOR PUSAT" in up or up.strip() == "PT PLN (PERSERO)":
        return "KP"
    for prefix, kode in JENIS_UNIT_INDUK:
        if prefix in up:
            return kode
    return "LAIN"


def jenis_unit_pelaksana(nama: str) -> str:
    up = (nama or "").upper()
    table = [
        ("UNIT PELAKSANA PELAYANAN PELANGGAN", "UP3"),
        ("UNIT PELAKSANA PENGATUR DISTRIBUSI", "UP2D"),
        ("UNIT PELAKSANA PENYALURAN DAN PENGATUR BEBAN", "UP3B"),
        ("UNIT PELAKSANA PENGATUR BEBAN", "UP2B"),
        ("UNIT PELAKSANA PENGATUR TRANSMISI", "UPTS"),
        ("UNIT PELAKSANA TRANSMISI", "UPT"),
        ("UNIT PELAKSANA PROYEK", "UPP"),
        ("UNIT PELAKSANA KONSTRUKSI", "UPK"),
        ("UNIT PELAKSANA MANAJEMEN KONSTRUKSI", "UPMK"),
        ("UNIT PELAKSANA PEMBANGKITAN", "UPKIT"),
        ("UNIT PELAKSANA PENDIDIKAN DAN PELATIHAN", "UPDL"),
        ("UNIT PELAKSANA PRODUKSI DAN WORKSHOP", "UP2W"),
        ("UNIT PELAKSANA ASSESSMENT CENTER", "UPAC"),
        ("UNIT PELAKSANA SERTIFIKASI", "UPS"),
        ("UNIT PELAKSANA MUSEUM", "UPMLEB"),
        ("UNIT PELAKSANA", "UP"),
        ("UNIT LAYANAN", "UL"),
    ]
    for prefix, kode in table:
        if prefix in up:
            return kode
    return "LAIN"


def extract_ftk(z: zipfile.ZipFile, shared: list[str]) -> dict[str, dict[str, str]]:
    """Sheet ' FTK Unit Holding' -> {nama_unit_upper: {ftk_2024, ftk_2025, real_des_2025, real_apr_2026}}."""
    out: dict[str, dict[str, str]] = {}
    for i, row in enumerate(iter_rows(z, SHEET_FTK, shared)):
        if i == 0:
            continue
        nama = row.get(3, "").strip()
        if not nama or nama.upper().startswith(("JUMLAH", "TOTAL")):
            continue
        clean = lambda v: "" if v.startswith("#") else v
        out[nama.upper()] = {
            "nama_amor": row.get(1, "").strip(),
            "ftk_2024": clean(row.get(4, "")),
            "ftk_2025": clean(row.get(5, "")),
            "realisasi_des_2025": clean(row.get(16, "")),
            "realisasi_apr_2026": clean(row.get(20, "")),
        }
    return out


def normalize_for_match(nama: str) -> str:
    """'Unit Induk Distribusi (UID) Jawa Barat' <-> 'PT PLN (PERSERO) UNIT INDUK DISTRIBUSI JAWA BARAT'."""
    up = (nama or "").upper()
    up = up.replace("PT PLN (PERSERO)", "")
    up = re.sub(r"\((UID|UIW|UIT|UIP|UIP3B|UIP2B|UIK|UP2B)\)", "", up)
    up = re.sub(r"[^A-Z0-9]+", " ", up)
    up = " ".join(up.split())
    return up[4:] if up.startswith("PLN ") else up  # 'PLN Kantor Pusat' == 'PT PLN (PERSERO) KANTOR PUSAT'


def main() -> int:
    if not SRC.exists():
        print(f"ERROR: sumber tidak ditemukan: {SRC}", file=sys.stderr)
        return 1
    OUT.mkdir(parents=True, exist_ok=True)

    z = zipfile.ZipFile(SRC)
    print("membaca shared strings ...")
    shared = load_shared_strings(z)
    print(f"  {len(shared):,} string")

    print("membaca sheet FTK unit holding ...")
    ftk = extract_ftk(z, shared)
    ftk_by_norm = {normalize_for_match(k): v for k, v in ftk.items()}
    print(f"  {len(ftk)} unit induk dengan angka FTK")

    print("membaca DAPEG (streaming, ~88MB) ...")
    cols: dict[str, int] = {}
    induk: dict[str, dict] = {}                  # nama_org2 -> info
    pelaksana: dict[tuple[str, str], dict] = {}  # (nama_org2, busa) -> info
    pel_nama: dict[tuple[str, str], Counter] = defaultdict(Counter)  # kandidat nama panjang
    jabatan: dict[str, Counter] = defaultdict(Counter)   # posisi -> Counter(jenjang_kode)
    jabatan_level: dict[str, Counter] = defaultdict(Counter)
    pos_induk = Counter()      # (unit_induk, posisi, jenjang) -> n
    pos_pelaksana = Counter()  # (unit_induk, busa, posisi, jenjang) -> n
    total = skipped = 0

    for i, row in enumerate(iter_rows(z, SHEET_DAPEG, shared)):
        if i == 0:
            cols = {name.strip(): idx for idx, name in row.items() if name.strip()}
            missing = [c for c in ("CoCd", "Company Code", "BusA", "Business Area",
                                   "Nama Panjang Posisi", "Jenjang - Sub Grp Text",
                                   "Organisasi 2", "Organisasi 3") if c not in cols]
            if missing:
                print(f"ERROR: kolom hilang di DAPEG: {missing}", file=sys.stderr)
                return 1
            continue

        get = lambda name: row.get(cols[name], "").strip()
        nama_induk = get("Organisasi 2")
        if not nama_induk or nama_induk.startswith("#"):  # buang #N/A
            skipped += 1
            continue
        total += 1

        kode_pel, nama_pel_pendek = get("BusA"), get("Business Area")
        org3 = get("Organisasi 3")
        posisi = get("Nama Panjang Posisi")
        jenjang_kode, jenjang_level = parse_jenjang(get("Jenjang - Sub Grp Text"))

        rec = induk.setdefault(nama_induk, {
            "unit_induk": nama_induk,
            "kode_cocd": get("CoCd"),
            "nama_pendek": get("Company Code"),
            "jenis_unit": jenis_unit_induk(nama_induk),
            "jumlah_pegawai": 0,
        })
        rec["jumlah_pegawai"] += 1

        if kode_pel:
            key = (nama_induk, kode_pel)
            prec = pelaksana.setdefault(key, {
                "kode_unit_pelaksana": kode_pel,
                "unit_induk": nama_induk,
                "nama_pendek": nama_pel_pendek,
                "nama_lengkap": "",
                "jenis_unit": jenis_unit_pelaksana(nama_pel_pendek),
                "jumlah_pegawai": 0,
            })
            prec["jumlah_pegawai"] += 1
            # Nama panjang hanya valid kalau Organisasi 3 memang node unit,
            # bukan BIDANG/DIREKTORAT (itu struktur internal kantor induk).
            if org3.upper().startswith(("UNIT PELAKSANA", "UNIT LAYANAN", "UNIT INDUK")):
                pel_nama[key][org3] += 1

        if posisi:
            jabatan[posisi][jenjang_kode] += 1
            jabatan_level[posisi][jenjang_level] += 1
            pos_induk[(nama_induk, posisi, jenjang_kode)] += 1
            if kode_pel:
                pos_pelaksana[(nama_induk, kode_pel, posisi, jenjang_kode)] += 1

    print(f"  {total:,} baris pegawai diproses ({skipped} dibuang karena unit induk kosong/#N/A)")

    # --- unit_induk.csv: join ke angka FTK lewat nama pendek (kosakata sama dgn 'Nama Amor') ---
    # Urutan prioritas penting: nama organisasi lengkap dulu, baru nama pendek.
    # UID Jateng & UID Yogyakarta berbagi CoCd 5200 dan nama pendek yang sama,
    # jadi kalau nama pendek dipakai duluan, UID Yogyakarta ikut mewarisi FTK UID Jateng.
    ftk_by_amor = {v["nama_amor"].upper(): v for v in ftk.values() if v["nama_amor"]}
    matched = 0
    consumed: set[int] = set()
    rows = []
    for rec in sorted(induk.values(), key=lambda r: (r["jenis_unit"], r["nama_pendek"])):
        f = ftk_by_norm.get(normalize_for_match(rec["unit_induk"]))
        if f is None:
            for cand in (ftk_by_amor.get(rec["nama_pendek"].upper()),
                         ftk_by_norm.get(normalize_for_match(rec["nama_pendek"]))):
                if cand is not None and id(cand) not in consumed:
                    f = cand
                    break
        if f:
            consumed.add(id(f))
            matched += 1
        rows.append({
            **rec,
            "ftk_2024": (f or {}).get("ftk_2024", ""),
            "ftk_2025": (f or {}).get("ftk_2025", ""),
            "realisasi_des_2025": (f or {}).get("realisasi_des_2025", ""),
            "realisasi_apr_2026": (f or {}).get("realisasi_apr_2026", ""),
        })
    write_csv(OUT / "unit_induk.csv", rows)
    print(f"  unit_induk.csv           {len(rows):>7,} baris  ({matched} ter-match ke angka FTK)")

    for key, rec in pelaksana.items():
        if pel_nama[key]:
            rec["nama_lengkap"] = pel_nama[key].most_common(1)[0][0]
            rec["jenis_unit"] = jenis_unit_pelaksana(rec["nama_lengkap"])
        else:
            # tidak ada node 'UNIT ...' -> ini kantor induk itu sendiri
            rec["nama_lengkap"] = rec["nama_pendek"]
            rec["jenis_unit"] = "KANTOR INDUK"
    write_csv(OUT / "unit_pelaksana.csv",
              sorted(pelaksana.values(), key=lambda r: (r["unit_induk"], r["nama_pendek"])))
    print(f"  unit_pelaksana.csv       {len(pelaksana):>7,} baris")

    unit_per_posisi: dict[str, set[str]] = defaultdict(set)
    for (u, p, _j) in pos_induk:
        unit_per_posisi[p].add(u)

    kat = []
    for posisi, cnt in sorted(jabatan.items()):
        jenjang_utama = cnt.most_common(1)[0][0]
        kat.append({
            "nama_posisi": posisi,
            "jenjang_utama": jenjang_utama,
            "level_utama": jabatan_level[posisi].most_common(1)[0][0],
            "jenjang_lain": "|".join(k for k, _ in cnt.most_common() if k != jenjang_utama),
            "jumlah_pegawai": sum(cnt.values()),
            "jumlah_unit_induk": len(unit_per_posisi[posisi]),
        })
    write_csv(OUT / "jabatan_katalog.csv", kat)
    print(f"  jabatan_katalog.csv      {len(kat):>7,} baris")

    write_csv(OUT / "posisi_unit_induk.csv", [
        {"unit_induk": u, "nama_posisi": p, "jenjang": j, "jumlah_pegawai": n}
        for (u, p, j), n in sorted(pos_induk.items(), key=lambda kv: (-kv[1], kv[0]))
    ])
    print(f"  posisi_unit_induk.csv    {len(pos_induk):>7,} baris")

    write_csv(OUT / "posisi_unit_pelaksana.csv", [
        {"unit_induk": u, "kode_unit_pelaksana": up, "nama_posisi": p,
         "jenjang": j, "jumlah_pegawai": n}
        for (u, up, p, j), n in sorted(pos_pelaksana.items(), key=lambda kv: (-kv[1], kv[0]))
    ])
    print(f"  posisi_unit_pelaksana.csv{len(pos_pelaksana):>7,} baris")

    print(f"\nselesai -> {OUT}")
    return 0


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
