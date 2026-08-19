"""Lapis 1 — nilai jangkar.

Membandingkan tiap metrik dengan nilai jangkar di docs/metrik.md (M01-M40). Kalau
mockdb diregenerasi atau sebuah query di core/metrics.py berubah, tes ini berteriak
sebelum angka salah sampai ke layar. Jalankan: `pytest tests/uji_metrik.py -v`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import metrics  # noqa: E402


def test_ringkasan():
    r = metrics.ringkasan()
    assert r["pendaftaran"] == 218_928
    assert r["diterima"] == 7_711
    assert r["sudah_sk"] == 5_711
    assert r["sedang_ojt"] == 2_000


def test_funnel_seleksi():
    f = metrics.funnel_seleksi().set_index("tahap_kode")
    assert int(f.loc["administrasi", "masuk"]) == 213_648
    assert int(f.loc["adaptif", "masuk"]) == 143_831
    assert f.loc["adaptif", "pct_no_show"] == 52.1
    assert int(f.loc["wawancara", "lulus"]) == 7_711


def test_gugur_per_tahap():
    g = metrics.gugur_per_tahap().set_index("tahap_gugur")["gugur"]
    assert int(g["adaptif"]) == 95_204
    assert int(g["administrasi"]) == 69_817


def test_no_show_per_tahap_mode():
    ns = metrics.no_show_per_tahap_mode().set_index("tahap_kode")
    assert ns.loc["adaptif", "mode"] == "online"
    assert ns.loc["adaptif", "pct_no_show"] == 52.1
    assert ns.loc["psikologi", "mode"] == "offline"


def test_jejak_rbb():
    rbb = metrics.jejak_rbb()
    # Tahun RBB (FHCI): 2020, 2021, 2024 — bukan seluruh rentang 2019-2025.
    assert set(rbb["tahun"]) == {2020, 2021, 2024}
    # M29: jalur RBB hampir tak berjejak di sistem PLN (< 2% pelamar FHCI 2024 terlihat)
    baris_2024 = rbb.loc[rbb["tahun"] == 2024].iloc[0]
    assert baris_2024["pct_terlihat"] < 2.0


def test_gap_ftk():
    gap = metrics.gap_ftk()
    assert gap["ftk"] == 37_854
    assert gap["realisasi"] == 37_153
    assert gap["gap"] == 701


def test_gap_ftk_per_unit_filters_anomali():
    unit = metrics.gap_ftk_per_unit()
    # UID Jawa Tengah & DIY punya baris master DUPLIKAT (satu anomali jumlah_pegawai=4,
    # satu benar jumlah_pegawai=1643, lihat ISSUES_MASTER_DATA.md) — filter
    # jumlah_pegawai > 50 harus menyisakan TEPAT SATU baris, bukan dua atau nol.
    baris_jateng = unit.loc[unit["nama_pendek"] == "UID Jawa Tengah & DIY"]
    assert len(baris_jateng) == 1
    assert int(baris_jateng.iloc[0]["ftk_2025"]) == 1516
    assert unit.iloc[0]["nama_pendek"] == "UID Jawa Barat"
    assert int(unit.iloc[0]["gap"]) == 59


def test_pagu_vs_usulan():
    pagu = metrics.pagu_vs_usulan().set_index("tahun")
    assert pagu.loc[2025, "usulan"] == 1_238
    assert pagu.loc[2025, "pct_disetujui"] == 84.8


def test_proyeksi_per_sebab():
    proyeksi = metrics.proyeksi_per_sebab().set_index("tahun")
    assert proyeksi.loc[2026, "total"] == 919


def test_akun_ringkas():
    akun = metrics.akun_ringkas()
    assert akun["akun"] == 368_912
    assert akun["pelamar"] == 172_389
    assert akun["tidak_melamar"] == 196_523


def test_jenjang_pendidikan():
    jenjang = metrics.jenjang_pendidikan().set_index("degree")["n"]
    assert int(jenjang["S1/D-IV"]) == 245_553


def test_rumpun_melamar_vs_diterima_berpola():
    rumpun = metrics.rumpun_melamar_vs_diterima()
    # Konversi antar rumpun HARUS bervariasi (bukti sebaran program_studi valid) —
    # beda dengan sekolah_universitas yang cacat (lihat ISSUES_SEBARAN.md).
    assert rumpun["pct"].max() - rumpun["pct"].min() > 1.0


def test_volume_tes_per_kota_berpola():
    kota = metrics.volume_tes_per_kota()
    assert len(kota) == 43
    # Rasio top/bawah harus jauh > 1 (kota berpola, bukan acak seragam).
    assert kota["n"].max() / kota["n"].min() > 10


def test_volume_tes_per_kota_geo_lengkap():
    geo = metrics.volume_tes_per_kota_geo()
    assert len(geo) == 43
    assert geo["lat"].notna().all()
    assert geo["lon"].notna().all()


def test_penempatan_jenis():
    jenis = metrics.penempatan_jenis().set_index("jenis_penempatan")["jumlah"]
    assert int(jenis["INDUK"]) == 5_171
    assert int(jenis["SUBHOLDING"]) == 2_540


def test_grade_masuk():
    grade = metrics.grade_masuk().set_index("kode_grade")["n"]
    assert int(grade["G2"]) == 5_423


def test_treemap_penempatan_pakai_nama_pendek():
    t = metrics.treemap_penempatan()
    assert "Kantor Pusat" in t["unit_induk"].tolist()
    # Nama resmi panjang tidak boleh lolos — kalau ini gagal, join nama_pendek putus.
    assert not t["unit_induk"].str.contains("PERSERO", na=False).any()


def test_volume_per_sistem():
    sistem = metrics.volume_per_sistem().set_index("sistem_sumber")["n"]
    assert int(sistem["rekrutmen.pln.co.id"]) == 370_102
    assert int(sistem["seleksi.pln.co.id"]) == 53_907


def test_kelengkapan_per_kohort():
    kelengkapan = metrics.kelengkapan_per_kohort().set_index("kualitas_kohort")
    assert kelengkapan.loc["RENDAH", "pct_blok_fisik"] == 0.0
    assert kelengkapan.loc["BAIK", "pct_blok_fisik"] == 70.6


def test_selisih_angka_rencana_melebar():
    selisih = metrics.selisih_angka_rencana().set_index("tahun")
    assert selisih.loc[2025, "selisih"] == 950
