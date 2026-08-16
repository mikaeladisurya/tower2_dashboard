"""Klasifikasi 6.148 nama posisi -> kelompok jabatan + bidang + sub bidang + bidang pembidangan.

Input  : out/master/jabatan_katalog.csv
         rules/bidang_jabatan.csv   (tabel kata kunci berurutan, first-match-wins; boleh diedit tangan)
Output : out/master/jabatan_klasifikasi.csv
         + ringkasan cakupan & daftar posisi yang belum tertangkap aturan

Catatan kosakata jabatan PLN Holding (hasil verifikasi dari DAPEG):
    tidak ada judul ANALYST, dan ENGINEER cuma 2 posisi. Kosakata aslinya
    OFFICER / TECHNICIAN / SPECIALIST / TEAM LEADER / MANAGER / VICE PRESIDENT.

Jalankan: python mockdb/build/02_klasifikasi_jabatan.py
"""
from __future__ import annotations

import csv
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "mockdb" / "out" / "master"
RULES = ROOT / "mockdb" / "rules" / "bidang_jabatan.csv"

# Prefix kelompok jabatan, dicek berurutan (yang lebih panjang duluan).
KELOMPOK_JABATAN = [
    "SENIOR EXECUTIVE VICE PRESIDENT", "EXECUTIVE VICE PRESIDENT", "VICE PRESIDENT",
    "GENERAL MANAGER", "SENIOR MANAGER", "ASSISTANT MANAGER", "DEPUTY MANAGER", "MANAGER",
    "TEAM LEADER",
    "SENIOR SPECIALIST", "JUNIOR SPECIALIST", "SPECIALIST",
    "SENIOR EXPERT", "JUNIOR EXPERT", "EXPERT",
    "SENIOR ENGINEER", "JUNIOR ENGINEER", "ENGINEER",
    "SENIOR OFFICER", "JUNIOR OFFICER", "OFFICER",
    "SENIOR TECHNICIAN", "JUNIOR TECHNICIAN", "TECHNICIAN",
    "KEPALA SATUAN", "KEPALA DIVISI", "SEKRETARIS PERUSAHAAN", "SPECIAL ASSISTANT",
]

# Salah ketik di sumber -> bentuk baku.
TYPO = {
    "SENOR OFFICER": "SENIOR OFFICER",
    "SPESIALIST": "SPECIALIST",
    "TC ": "TECHNICIAN ",
}

# Jenjang yang jadi sasaran rekrutmen fresh graduate.
JENJANG_ENTRY = {"G1"}


def normalize(nama: str) -> str:
    s = " ".join((nama or "").upper().split())
    for salah, benar in TYPO.items():
        if s.startswith(salah):
            s = benar + s[len(salah):]
    return s


def split_kelompok(nama: str) -> tuple[str, str]:
    """'JUNIOR TECHNICIAN PDKB GI/GITET' -> ('JUNIOR TECHNICIAN', 'PDKB GI/GITET')."""
    for pref in KELOMPOK_JABATAN:
        if nama == pref:
            return pref, ""
        if nama.startswith(pref + " "):
            return pref, nama[len(pref) + 1:]
    return "", nama


def load_rules(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        rules = list(csv.DictReader(fh))
    for r in rules:
        r["urutan"] = int(r["urutan"])
        r["kata_kunci"] = r["kata_kunci"].upper()
    rules.sort(key=lambda r: r["urutan"])
    return rules


def classify(fungsi: str, kelompok: str, rules: list[dict]) -> tuple[str, str, str, str]:
    """-> (bidang, sub_bidang, bidang_pembidangan, kata_kunci_pemicu)."""
    for r in rules:
        if r["kata_kunci"] in fungsi:
            return r["bidang"], r["sub_bidang"], r["bidang_pembidangan"], r["kata_kunci"]
    # Fallback: kosakata PLN konsisten -- TECHNICIAN selalu teknik, OFFICER selalu penunjang.
    if "TECHNICIAN" in kelompok:
        return "TEKNIK", "Distribusi", "Distribusi", "(fallback TECHNICIAN)"
    if kelompok:
        return "NON-TEKNIK", "Komunikasi dan Umum", "Sumber Daya Manusia", "(fallback OFFICER)"
    return "", "", "", ""


def main() -> int:
    src = MASTER / "jabatan_katalog.csv"
    if not src.exists():
        print(f"ERROR: jalankan 01_extract_master.py dulu ({src} belum ada)", file=sys.stderr)
        return 1
    rules = load_rules(RULES)
    print(f"aturan bidang: {len(rules)} kata kunci dari {RULES.name}")

    with src.open(encoding="utf-8") as fh:
        katalog = list(csv.DictReader(fh))

    out_rows = []
    stat_bidang, stat_sub, stat_kelompok = Counter(), Counter(), Counter()
    stat_pemicu = Counter()
    tanpa_kelompok, fallback = [], []

    for row in katalog:
        nama = normalize(row["nama_posisi"])
        kelompok, fungsi = split_kelompok(nama)
        # buang embel-embel lokasi/nomor supaya kata kunci lebih mudah kena
        fungsi_bersih = re.sub(r"\b(I{1,3}|IV|V|VI{1,3}|IX|X)\b", " ", fungsi)
        bidang, sub, pembidangan, pemicu = classify(fungsi_bersih, kelompok, rules)

        if not kelompok:
            tanpa_kelompok.append(nama)
        if pemicu.startswith("("):
            fallback.append(f"{kelompok} | {fungsi}")

        jenjang = row["jenjang_utama"]
        out_rows.append({
            "nama_posisi": row["nama_posisi"],
            "kelompok_jabatan": kelompok or "(lainnya)",
            "fungsi": fungsi,
            "jenjang_utama": jenjang,
            "level_utama": row["level_utama"],
            "bidang": bidang,
            "sub_bidang": sub,
            "bidang_pembidangan": pembidangan,
            "kata_kunci_pemicu": pemicu,
            "is_entry_level": "1" if jenjang in JENJANG_ENTRY else "0",
            "jumlah_pegawai": row["jumlah_pegawai"],
            "jumlah_unit_induk": row["jumlah_unit_induk"],
        })
        stat_bidang[bidang] += 1
        stat_sub[sub] += 1
        stat_kelompok[kelompok or "(lainnya)"] += 1
        stat_pemicu[pemicu] += 1

    dst = MASTER / "jabatan_klasifikasi.csv"
    with dst.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)

    n = len(out_rows)
    n_fb = len(fallback)
    print(f"\n{n:,} posisi diklasifikasi -> {dst.name}")
    print(f"  kena aturan kata kunci : {n - n_fb:,}  ({(n - n_fb) / n:.1%})")
    print(f"  jatuh ke fallback      : {n_fb:,}  ({n_fb / n:.1%})")
    print(f"  tanpa kelompok jabatan : {len(tanpa_kelompok)}")

    print("\n--- bidang ---")
    for k, v in stat_bidang.most_common():
        print(f"  {v:>6,}  {k or '(kosong)'}")
    print("\n--- sub bidang ---")
    for k, v in stat_sub.most_common():
        print(f"  {v:>6,}  {k or '(kosong)'}")
    print("\n--- kelompok jabatan (top 12) ---")
    for k, v in stat_kelompok.most_common(12):
        print(f"  {v:>6,}  {k}")

    entry = [r for r in out_rows if r["is_entry_level"] == "1"]
    print(f"\n--- posisi entry level (jenjang G1): {len(entry)} posisi, "
          f"{sum(int(r['jumlah_pegawai']) for r in entry):,} pegawai ---")
    eb = Counter(r["bidang_pembidangan"] for r in entry)
    for k, v in eb.most_common():
        print(f"  {v:>6,}  {k}")

    if fallback:
        print(f"\n--- contoh 15 posisi yang jatuh ke fallback (perlu kata kunci baru?) ---")
        for x in sorted(set(fallback))[:15]:
            print(f"  {x}")
    if tanpa_kelompok:
        print(f"\n--- posisi tanpa kelompok jabatan dikenali ---")
        for x in sorted(set(tanpa_kelompok)):
            print(f"  {x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
