"""Muat seluruh out/master/*.csv ke satu berkas DuckDB (out/rekrutmen.duckdb).

Langkah TERAKHIR pipeline generator (rules/README.md urutan kausal sudah tuntas
di langkah 11). Tidak ada logika baru di sini -- CSV di out/master/ adalah SUMBER
KEBENARAN yang sudah lolos `00_verifikasi_rules.py` + `00b_verifikasi_keluaran.py`;
langkah ini murni memindahkannya ke bentuk satu-berkas yang dipakai dashboard
(keputusan user, README §Penyimpanan), plus verifikasi bahwa pemindahannya tidak
mengubah satu baris pun (row count CSV == row count tabel).

Berkas `.duckdb` DIGITIGNORE (HANDOFF §1: "Distribusi ke tim: REGENERATE, bukan
salin file") -- siapa pun bisa membangunnya ulang dari `rules/` + `out/master/`
tanpa perlu file besar/PII lewat git.

Input  : seluruh out/master/*.csv
Output : out/rekrutmen.duckdb

Jalankan: python mockdb/build/12_load_duckdb.py
"""
from __future__ import annotations

import csv
from pathlib import Path

import duckdb
import yaml

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "mockdb" / "out" / "master"
RULES = ROOT / "mockdb" / "rules"
DB_PATH = ROOT / "mockdb" / "out" / "rekrutmen.duckdb"

print("Langkah 12: muat ke DuckDB\n")

kohort_yaml = yaml.safe_load((RULES / "kohort.yaml").read_text(encoding="utf-8"))
meta = kohort_yaml["meta"]

if DB_PATH.exists():
    DB_PATH.unlink()  # selalu bangun ulang dari nol -- deterministik, bukan diff/append

con = duckdb.connect(str(DB_PATH))

csv_files = sorted(MASTER.glob("*.csv"))
print(f"  {len(csv_files)} berkas CSV ditemukan di {MASTER.relative_to(ROOT)}\n")

ringkasan: list[tuple[str, int, int]] = []  # (nama_tabel, baris_csv, baris_tabel)
for path in csv_files:
    nama_tabel = path.stem
    with path.open(encoding="utf-8-sig", newline="") as f:
        baris_csv = sum(1 for _ in f) - 1  # minus header

    con.execute(
        f"CREATE TABLE {nama_tabel} AS SELECT * FROM read_csv_auto(?, all_varchar=false, "
        f"header=true, sample_size=-1)",
        [str(path)],
    )
    baris_tabel = con.execute(f"SELECT count(*) FROM {nama_tabel}").fetchone()[0]
    ringkasan.append((nama_tabel, baris_csv, baris_tabel))

# ---------------------------------------------------------------------------
# Tabel metadata provenance -- seed, horison, tanggal potong, jumlah tabel/baris
# ---------------------------------------------------------------------------
con.execute("""
    CREATE TABLE _meta_generator (
        kunci VARCHAR PRIMARY KEY,
        nilai VARCHAR
    )
""")
total_baris = sum(t[2] for t in ringkasan)
meta_rows = [
    ("seed", str(meta["seed"])),
    ("tanggal_sekarang", str(meta["tanggal_sekarang"])),
    ("horison_gelombang", f"{meta['horison_gelombang'][0]}-{meta['horison_gelombang'][1]}"),
    ("cakupan", meta["cakupan"]),
    ("jumlah_tabel", str(len(ringkasan))),
    ("jumlah_baris_total", str(total_baris)),
    ("dibangun_dari", "mockdb/rules/*.yaml + mockdb/build/01-12 (REGENERATE, bukan disalin)"),
]
con.executemany("INSERT INTO _meta_generator VALUES (?, ?)", meta_rows)

con.close()

# ---------------------------------------------------------------------------
# Verifikasi: pemindahan CSV -> DuckDB tidak boleh mengubah jumlah baris
# ---------------------------------------------------------------------------
print("  cek jumlah baris CSV vs tabel DuckDB:")
meleset = [t for t in ringkasan if t[1] != t[2]]
for nama, c, d in ringkasan:
    tanda = "OK  " if c == d else "BEDA"
    print(f"    {tanda}  {nama:<28} csv={c:>8,}  tabel={d:>8,}")

ukuran_mb = DB_PATH.stat().st_size / (1024 * 1024)
print(f"\n  {len(ringkasan)} tabel, {total_baris:,} baris total, {ukuran_mb:,.1f} MB -> {DB_PATH.relative_to(ROOT)}")

if meleset:
    print(f"\n  GAGAL: {len(meleset)} tabel jumlah barisnya beda dari CSV sumber: {[t[0] for t in meleset]}")
    raise SystemExit(1)

print("\nSelesai langkah 12. Semua tabel cocok persis dgn CSV sumber.")
