"""Pasca-seleksi: pengumuman -> kontrak -> SAMAPTA -> pembidangan -> OJT -> SK.

Urutan kausal (rules/README.md): pendaftaran.csv (langkah 08, `hasil_akhir` sudah
final) + seleksi_tahap.csv (langkah 09, wawancara LULUS = jangkar DITERIMA) ->
tahapan.yaml.tahap_pasca (perjalanan SETELAH lulus seleksi). Langkah ini hanya
berlaku untuk pendaftaran `hasil_akhir == "DITERIMA"` -- kedua jalur (mandiri/rbb)
memakai kosakata pasca yang SAMA (HANDOFF butir 4b, poin 2), jadi tidak ada
percabangan jalur di sini seperti langkah 09.

Titik penting (F-018/kohort.yaml §2b): "diterima" != "sudah jadi pegawai". Tanggal
tiap tahap dihitung sbg offset dari `tgl_tutup` profesi (TURUNAN, kohort.yaml
durasi_hari_setelah_tutup), lalu dipotong di `tanggal_sekarang` (2026-09-15):
  - Tahap bertitik-tunggal (pengumuman_akhir, ttd_kontrak, samapta, pembidangan,
    ujian_ojt, sk_penempatan): kalau tanggal hasil > tanggal_sekarang, tahap itu
    (dan seluruh tahap SESUDAHNYA) belum terjadi -- tidak ditulis baris apapun.
  - OJT beda: `durasi.ojt.mulai`/`selesai` (195/375 hari) BUKAN rentang acak
    sekali-titik seperti tahap lain, melainkan tanggal MULAI & SELESAI program itu
    sendiri (kelas prajabatan berjalan sbg kohort, bukan per-orang) -- lih. contoh
    persis di kohort.yaml (gelombang 2025: tutup 2025-10-05 -> ojt_mulai 2026-04-18,
    ojt_selesai 2026-10-15, keduanya = tgl_tutup + offset tetap, TANPA acak).
    Kalau tanggal_sekarang jatuh di antara mulai & selesai -> status BERJALAN dengan
    `progres` (persis mereproduksi kohort.yaml: gelombang 2025 progres_ojt 0.83).

`urutan` melanjutkan tahap_seleksi (1-6 di seleksi_tahap.csv) jadi 7-13, supaya
satu kandidat py11 punya SATU deret urutan lintas dua tabel.

Input  : rules/{tahapan,kohort}.yaml, out/master/{profesi,pendaftaran}.csv
Output : out/master/pasca_tahap.csv

Jalankan: python mockdb/build/10_pasca_seleksi.py
"""
from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "mockdb" / "out" / "master"
RULES = ROOT / "mockdb" / "rules"

SEED = 20260915
rng = np.random.default_rng(SEED)


def baca_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def muat_yaml(nama: str) -> dict:
    return yaml.safe_load((RULES / nama).read_text(encoding="utf-8"))


print("Langkah 10: pasca-seleksi (kontrak/SAMAPTA/pembidangan/OJT/SK)\n")

tahapan = muat_yaml("tahapan.yaml")
kohort_yaml = muat_yaml("kohort.yaml")

profesi = {r["profesi_id"]: r for r in baca_csv(MASTER / "profesi.csv")}
pendaftaran = baca_csv(MASTER / "pendaftaran.csv")

TANGGAL_SEKARANG = dt.date.fromisoformat(str(kohort_yaml["meta"]["tanggal_sekarang"]))
DURASI = kohort_yaml["durasi_hari_setelah_tutup"]

# tahap_pasca: urutan tetap sesuai daftar di yaml, melanjutkan dari tahap_seleksi (1-6)
PASCA = tahapan["tahap_pasca"]
URUTAN_AWAL = 7
PASCA_URUTAN = {t["kode"]: URUTAN_AWAL + i for i, t in enumerate(PASCA)}
PASCA_REF = {t["kode"]: t for t in PASCA}
ORDER = [t["kode"] for t in PASCA]

diterima = [r for r in pendaftaran if r["hasil_akhir"] == "DITERIMA"]

print(f"  {len(diterima):,} pendaftaran DITERIMA (jangkar dari langkah 08/09)")
print("  menulis pasca_tahap.csv ...")

n_baris = 0
n_selesai_semua = 0  # sudah ber-SK
n_sedang_ojt = 0
pasca_id = 0

with (MASTER / "pasca_tahap.csv").open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["pasca_id", "pendaftaran_id", "kandidat_id", "profesi_id", "gelombang_id",
                "tahap_kode", "urutan", "tanggal_mulai", "tanggal_selesai", "status", "progres",
                "pemilik_proses", "sistem_sumber"])

    for row in diterima:
        prow = profesi[row["profesi_id"]]
        tgl_tutup = prow["tgl_tutup"] or f"{prow['tahun_program']}-12-31"
        d_tutup = dt.date.fromisoformat(tgl_tutup)

        sudah_ber_sk = False
        sedang_ojt = False

        for kode in ORDER:
            tref = PASCA_REF[kode]
            durasi = DURASI[kode]

            if kode == "ojt":
                d_mulai = d_tutup + dt.timedelta(days=durasi["mulai"])
                d_selesai = d_tutup + dt.timedelta(days=durasi["selesai"])
                if d_mulai > TANGGAL_SEKARANG:
                    break
                if TANGGAL_SEKARANG >= d_selesai:
                    status, progres = "SELESAI", 1.0
                else:
                    status = "BERJALAN"
                    progres = round(
                        (TANGGAL_SEKARANG - d_mulai).days / (d_selesai - d_mulai).days, 4
                    )
                    sedang_ojt = True
                tanggal_mulai, tanggal_selesai = d_mulai.isoformat(), d_selesai.isoformat()
            else:
                off = int(rng.integers(durasi["mulai"], durasi["selesai"] + 1))
                d_tahap = d_tutup + dt.timedelta(days=off)
                if d_tahap > TANGGAL_SEKARANG:
                    break
                status, progres = "SELESAI", 1.0
                tanggal_mulai = tanggal_selesai = d_tahap.isoformat()

            pasca_id += 1
            w.writerow([
                pasca_id, row["pendaftaran_id"], row["kandidat_id"], row["profesi_id"],
                row["gelombang_id"], kode, PASCA_URUTAN[kode], tanggal_mulai, tanggal_selesai,
                status, progres, tref["pemilik_proses"], tref["sistem_sumber"],
            ])
            n_baris += 1

            if kode == "sk_penempatan":
                sudah_ber_sk = True
            if kode == "ojt" and status == "BERJALAN":
                # sudah dihitung di atas, tapi hentikan loop sebelum ujian_ojt/sk_penempatan
                break

        if sudah_ber_sk:
            n_selesai_semua += 1
        elif sedang_ojt:
            n_sedang_ojt += 1

print(f"  tulis pasca_tahap.csv  ({n_baris:,} baris utk {len(diterima):,} pendaftaran diterima)")
print(f"  sudah ber-SK (pegawai penuh): {n_selesai_semua:,}")
print(f"  sedang OJT (kontrak, belum SK): {n_sedang_ojt:,}")
print(f"  belum sampai kontrak/lebih awal dari OJT: "
      f"{len(diterima) - n_selesai_semua - n_sedang_ojt:,}")

print("\nSelesai langkah 10.")
print(f"  pasca_tahap: {n_baris:,} baris")
