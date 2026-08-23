"""Data sintetis untuk halaman Eksplorasi.

Semua angka di modul ini **bukan** hasil kueri ke database sungguhan --
dibangun dengan `numpy` memakai benih (seed) tetap supaya bentuknya stabil
antar pemuatan, untuk delapan fitur yang jelas berguna bagi tim rekrutmen
tapi belum punya sumber data nyata (lihat `docs/USULAN_DATABASE.md`).

Dipisah dari `app_pages/eksplorasi.py` supaya halaman itu sendiri tetap
berupa pemanggilan fungsi + penyajian, sejalan dengan pola "halaman tidak
menghitung, hanya menyajikan" yang dipakai `core/metrics.py` untuk data
sungguhan -- meski di sini yang dipanggil bukan kueri, melainkan angka
sintetis.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

_BENIH = 20260823


def pemenuhan_wilayah_3t() -> pd.DataFrame:
    """Rencana vs realisasi penempatan OJT per wilayah, sintetis."""
    return pd.DataFrame(
        {
            "wilayah": ["Wilayah 3T", "Wilayah Lainnya"],
            "rencana": [210, 1020],
            "realisasi": [96, 987],
        }
    )


def proyeksi_lanjutan(dasar: pd.DataFrame, tahun_tambahan: int = 3) -> pd.DataFrame:
    """Perpanjang deret tahun x kekosongan nyata dengan tahun sintetis.

    `dasar` adalah keluaran nyata `metrics.kekosongan_nasional_per_tahun()`
    (2019-2026). Tahun tambahan diekstrapolasi dari laju perubahan tiga tahun
    terakhir data nyata, ditambah derau kecil supaya tidak berupa garis lurus
    sempurna. Kolom `sumber` membedakan baris nyata dari baris sintetis --
    dipakai halaman untuk memberi tanda visual berbeda.
    """
    rng = np.random.default_rng(_BENIH)
    nyata = dasar.copy()
    nyata["sumber"] = "Realisasi"

    laju = (nyata["kekosongan"].iloc[-1] / nyata["kekosongan"].iloc[-4]) ** (1 / 3) - 1
    laju = float(np.clip(laju, -0.15, 0.05))

    tahun_awal = int(nyata["tahun"].iloc[-1])
    nilai_awal = float(nyata["kekosongan"].iloc[-1])
    baris_baru = []
    nilai = nilai_awal
    for i in range(1, tahun_tambahan + 1):
        derau = rng.normal(loc=0, scale=0.03)
        nilai = max(nilai * (1 + laju + derau), 0)
        baris_baru.append({"tahun": tahun_awal + i, "kekosongan": round(nilai), "sumber": "Proyeksi"})

    return pd.concat([nyata, pd.DataFrame(baris_baru)], ignore_index=True)


def faktor_pertumbuhan(n: int) -> np.ndarray:
    """Faktor pengali sintetis, satu per baris, untuk mengekstrapolasi
    kekosongan tahun berikutnya dari baseline nyata terakhir yang tersedia."""
    rng = np.random.default_rng(_BENIH + 1)
    faktor = rng.normal(loc=0.94, scale=0.08, size=n)
    return np.clip(faktor, 0.7, 1.2)


def pencocokan_kompetensi() -> pd.DataFrame:
    """Standar jabatan vs capaian pelamar per dimensi kompetensi, sintetis."""
    return pd.DataFrame(
        {
            "kompetensi": [
                "Teknis Kelistrikan",
                "Kepemimpinan",
                "Komunikasi",
                "Analitis",
                "Integritas",
                "Adaptabilitas",
            ],
            "standar_jabatan": [85, 75, 78, 80, 90, 76],
            "capaian_pelamar": [71, 68, 74, 77, 88, 73],
        }
    )


def sebaran_skor_tes() -> tuple[pd.DataFrame, float]:
    """Sebaran skor tes akademik sintetis (0-100) & ambang kelulusan."""
    rng = np.random.default_rng(_BENIH + 2)
    skor = rng.normal(loc=68, scale=12, size=4000)
    skor = np.clip(skor, 0, 100)
    ambang = 65.0
    return pd.DataFrame({"skor": skor}), ambang


def peristiwa_karier() -> pd.DataFrame:
    """Peristiwa karier pasca-penempatan per pegawai (APS/rotasi/mutasi/tugas
    karya), sintetis. Tanpa PII -- identitas pegawai memakai kode urut."""
    rng = np.random.default_rng(_BENIH + 3)
    jenis_peristiwa = ["APS", "Rotasi", "Mutasi", "Tugas Karya"]
    tahun_rentang = list(range(2020, 2027))
    n = 220
    return pd.DataFrame(
        {
            "id_pegawai": [f"PLN-{i:05d}" for i in rng.integers(10000, 99999, size=n)],
            "jenis": rng.choice(jenis_peristiwa, size=n, p=[0.30, 0.35, 0.20, 0.15]),
            "tahun": rng.choice(tahun_rentang, size=n),
        }
    )


def efektivitas_sumber_rekrutmen() -> pd.DataFrame:
    """Volume pelamar & tingkat konversi per jalur perekrutan, sintetis."""
    return pd.DataFrame(
        {
            "sumber": ["Kampus", "Job Fair", "Media Sosial", "Rujukan Pegawai", "Jalur RBB"],
            "jumlah_pelamar": [48200, 21500, 63400, 8600, 12100],
            "konversi_persen": [4.1, 2.8, 1.6, 7.9, 5.2],
        }
    )


def kapasitas_samapta_updl() -> pd.DataFrame:
    """Kapasitas & keterpakaian lokasi SAMAPTA per UPDL, sintetis."""
    rng = np.random.default_rng(_BENIH + 4)
    updl = [
        "UPDL Jakarta", "UPDL Bandung", "UPDL Semarang", "UPDL Surabaya",
        "UPDL Padang", "UPDL Palembang", "UPDL Medan", "UPDL Makassar",
        "UPDL Pandaan", "UPDL Suralaya", "UPDL Tuntungan",
    ]
    kapasitas = rng.integers(120, 320, size=len(updl))
    terpakai = np.round(kapasitas * rng.uniform(0.55, 0.98, size=len(updl)))
    return pd.DataFrame({"updl": updl, "kapasitas": kapasitas, "terpakai": terpakai})


def komponen_biaya_rekrutmen() -> pd.DataFrame:
    """Komponen biaya rekrutmen per tahun program, sintetis (dalam juta rupiah)."""
    rng = np.random.default_rng(_BENIH + 5)
    tahun = list(range(2022, 2027))
    komponen = ["Iklan & Publikasi", "Psikotes", "Tes Kesehatan", "SAMAPTA", "Administrasi"]
    baris = []
    dasar = {"Iklan & Publikasi": 1800, "Psikotes": 2600, "Tes Kesehatan": 1400, "SAMAPTA": 900, "Administrasi": 700}
    for t in tahun:
        for k in komponen:
            derau = rng.uniform(0.9, 1.15)
            baris.append({"tahun": t, "komponen": k, "biaya_juta_rupiah": round(dasar[k] * derau)})
    return pd.DataFrame(baris)


def biaya_per_pegawai_diterima(total_diterima: int = 7711) -> float:
    """Rasio biaya per pegawai diterima, sintetis -- total biaya lima tahun
    dibagi jumlah pegawai diterima (angka nyata terverifikasi `metrics`)."""
    biaya = komponen_biaya_rekrutmen()["biaya_juta_rupiah"].sum()
    return float(biaya) * 1_000_000 / total_diterima
