"""Jalankan SATU BERKAS ini utk membangun `out/rekrutmen.duckdb` dari nol.

Untuk siapa pun yang baru clone repo ini (dashboard, anggota tim baru, dst):

    python mockdb/build_all.py

Itu saja. Tidak perlu menjalankan skrip di `mockdb/build/` satu-satu.

Kenapa `rekrutmen.duckdb` tidak ikut di-commit: file itu (+ sebagian besar
`out/master/*.csv`) sengaja di-GITIGNORE karena besar (puluhan-ratusan MB) dan
100% BISA DIBANGKITKAN ULANG secara deterministik (satu seed tunggal di
`rules/kohort.yaml`) -- jadi lebih murah di-generate daripada disimpan di git.
Lihat `knowledge/HANDOFF.md` §1 ("Distribusi ke tim: REGENERATE, bukan salin file").

Dua langkah PERTAMA (01, 02) DIKECUALIKAN dari aturan itu: keduanya mengekstrak
data dari DAPEG asli (`data sintetis/`, berisi PII, sengaja TIDAK ikut git sama
sekali) dan hasilnya (7 berkas fondasi -- unit_induk.csv, unit_pelaksana.csv,
realisasi_bulanan.csv, jabatan_katalog.csv, jabatan_klasifikasi.csv,
posisi_unit_induk.csv, posisi_unit_pelaksana.csv) MASIH di-track di git karena
tim tanpa akses DAPEG tidak bisa membangkitkannya sendiri. Skrip ini otomatis
MELEWATI 01/02 kalau ketujuh berkas itu sudah ada (kondisi normal setelah clone),
dan baru mencoba menjalankannya kalau ada yang hilang.

Butuh Python dgn: numpy, pyyaml, duckdb (lihat requirements/environment proyek).
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent          # mockdb/
BUILD = ROOT / "build"
MASTER = ROOT / "out" / "master"

FONDASI = [
    "unit_induk.csv", "unit_pelaksana.csv", "realisasi_bulanan.csv",
    "jabatan_katalog.csv", "jabatan_klasifikasi.csv",
    "posisi_unit_induk.csv", "posisi_unit_pelaksana.csv",
]

LANGKAH_FONDASI = ["01_extract_master.py", "02_klasifikasi_jabatan.py"]
LANGKAH_GENERATOR = [
    "03_rumpun_jurusan.py", "04_attrition_proyeksi.py", "05_usulan_pagu.py",
    "06_gelombang_program_profesi.py", "07_vendor_lokasi.py",
    "08_kandidat_pendaftaran.py", "09_seleksi_tahap.py", "10_pasca_seleksi.py",
    "11_penempatan.py", "12_load_duckdb.py",
]


def jalankan(skrip: str) -> None:
    path = BUILD / skrip
    print(f"\n{'=' * 70}\n>> {skrip}\n{'=' * 70}")
    mulai = time.time()
    hasil = subprocess.run([sys.executable, str(path)])
    detik = time.time() - mulai
    if hasil.returncode != 0:
        print(f"\nGAGAL di {skrip} (exit {hasil.returncode}, {detik:.1f}s). Berhenti.")
        sys.exit(hasil.returncode)
    print(f"-- {skrip} selesai ({detik:.1f}s)")


def main() -> None:
    print("Membangun mockdb/out/rekrutmen.duckdb dari nol\n")

    hilang = [f for f in FONDASI if not (MASTER / f).exists()]
    if not hilang:
        print(f"  {len(FONDASI)} berkas fondasi (langkah 01/02) sudah ada di out/master/ "
              "(dari git) -- lewati 01/02.")
    else:
        print(f"  Berkas fondasi hilang: {hilang}")
        if not (ROOT.parent / "data sintetis").exists():
            print(
                "\n  'data sintetis/' (sumber DAPEG asli, berisi PII) tidak ditemukan di "
                "root repo.\n"
                "  Langkah 01/02 BUTUH folder ini dan TIDAK bisa dijalankan tanpanya.\n"
                "  Berkas fondasi seharusnya sudah ikut ter-clone dari git (di-track khusus\n"
                "  krn alasan ini) -- coba `git checkout -- mockdb/out/master/` dulu.\n"
                "  Kalau memang belum pernah ada, minta berkas itu ke rekan yang punya akses\n"
                "  DAPEG, bukan coba generate ulang tanpa sumbernya."
            )
            sys.exit(1)
        print("  'data sintetis/' ditemukan -- menjalankan 01/02 dulu.")
        for skrip in LANGKAH_FONDASI:
            jalankan(skrip)

    for skrip in LANGKAH_GENERATOR:
        jalankan(skrip)

    db = ROOT / "out" / "rekrutmen.duckdb"
    print(f"\n{'=' * 70}")
    if db.exists():
        print(f"SELESAI. {db} siap ({db.stat().st_size / (1024 * 1024):,.1f} MB).")
    else:
        print("SELESAI langkah generator, tapi rekrutmen.duckdb tidak ditemukan -- cek log di atas.")
        sys.exit(1)


if __name__ == "__main__":
    main()
