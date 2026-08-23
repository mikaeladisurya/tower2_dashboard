"""Lapis 1 -- angka jangkar terhadap DB nyata (tests/conftest.py sudah menaruh
root v3 di sys.path, tidak perlu sys.path.insert di sini).

`core/metrics.py` menerima `acuan: date | None` -- beda dari v2 yang jangkarnya
beku -- jadi tiap assert di sini memakai `acuan=date(...)` eksplisit, memakai
nilai yang sudah diverifikasi di `docs/metrik.md`. Dijalankan terhadap
`mockdb/out/rekrutmen.duckdb` sungguhan (read-only), tidak ada mock.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from core import metrics

# ──────────────────────────────────────────────────────────────────────────────
# M01 -- keadaan_sekarang
# ──────────────────────────────────────────────────────────────────────────────


def test_keadaan_sekarang_2026_08_22():
    k = metrics.keadaan_sekarang(acuan=date(2026, 8, 22))
    assert k["gelombang_dibuka"] == 0
    assert k["sedang_diseleksi"] == 0
    assert k["sedang_ojt"] == 2000
    assert k["menunggu_sk"] == 0


def test_keadaan_sekarang_2026_10_05():
    k = metrics.keadaan_sekarang(acuan=date(2026, 10, 5))
    assert k["sedang_ojt"] == 1021
    assert k["menunggu_sk"] == 979


def test_keadaan_sekarang_2027_01_06():
    k = metrics.keadaan_sekarang(acuan=date(2027, 1, 6))
    assert k["sedang_ojt"] == 0
    assert k["menunggu_sk"] == 2000


def test_keadaan_sekarang_2019_09_10():
    k = metrics.keadaan_sekarang(acuan=date(2019, 9, 10))
    assert k["gelombang_dibuka"] == 1
    assert k["sedang_diseleksi"] == 16661


# ──────────────────────────────────────────────────────────────────────────────
# M02 -- tenggat_terdekat
# ──────────────────────────────────────────────────────────────────────────────


def test_tenggat_terdekat_bentuk_kolom():
    df = metrics.tenggat_terdekat(hari=30, acuan=date(2026, 8, 22))
    assert list(df.columns) == [
        "jenis",
        "gelombang",
        "tahap",
        "tanggal",
        "hari_tersisa",
        "jumlah",
    ]
    # Tipe bentuk: kolom jumlah/hari_tersisa numerik walau DataFrame kosong.
    assert df["hari_tersisa"].dtype.kind in "if"
    assert df["jumlah"].dtype.kind in "if"


def test_tenggat_terdekat_2026_08_22_hari_30_kosong():
    df = metrics.tenggat_terdekat(hari=30, acuan=date(2026, 8, 22))
    assert len(df) == 0


def test_tenggat_terdekat_2026_08_22_hari_90():
    df = metrics.tenggat_terdekat(hari=90, acuan=date(2026, 8, 22)).set_index("gelombang")
    assert int(df.loc["G2025-091", "hari_tersisa"]) == 40
    assert int(df.loc["G2025-091", "jumlah"]) == 979
    assert int(df.loc["G2025-092", "hari_tersisa"]) == 54
    assert int(df.loc["G2025-092", "jumlah"]) == 1021


def test_tenggat_terdekat_2019_09_10_hari_30():
    df = metrics.tenggat_terdekat(hari=30, acuan=date(2019, 9, 10))
    assert len(df) == 59
    baris_pertama = df.iloc[0]
    assert baris_pertama["jenis"] == "Tahap seleksi"
    assert baris_pertama["gelombang"] == "G2019-071"
    assert baris_pertama["tahap"] == "Seleksi Administrasi"
    assert int(baris_pertama["hari_tersisa"]) == 0
    assert int(baris_pertama["jumlah"]) == 1490


# ──────────────────────────────────────────────────────────────────────────────
# M03 -- denyut_pipeline
# ──────────────────────────────────────────────────────────────────────────────


def test_denyut_pipeline_bentuk_kolom():
    df = metrics.denyut_pipeline(acuan=date(2026, 8, 22))
    assert list(df.columns) == [
        "urutan",
        "tahap_kode",
        "nama",
        "jumlah",
        "sedang_berjalan",
        "sudah_tuntas",
    ]
    assert len(df) == 14


def test_denyut_pipeline_invarian_jumlah_2026_08_22():
    df = metrics.denyut_pipeline(acuan=date(2026, 8, 22))
    assert (df["jumlah"] == df["sedang_berjalan"] + df["sudah_tuntas"]).all()
    baris = df.set_index("tahap_kode")
    assert int(baris.loc["ojt", "jumlah"]) == 2000
    assert int(baris.loc["ojt", "sedang_berjalan"]) == 2000
    assert int(baris.loc["ojt", "sudah_tuntas"]) == 0
    assert int(baris.loc["sk_penempatan", "jumlah"]) == 5711
    assert int(baris.loc["sk_penempatan", "sudah_tuntas"]) == 5711


def test_denyut_pipeline_invarian_jumlah_2026_10_05():
    df = metrics.denyut_pipeline(acuan=date(2026, 10, 5))
    assert (df["jumlah"] == df["sedang_berjalan"] + df["sudah_tuntas"]).all()
    baris = df.set_index("tahap_kode")
    assert int(baris.loc["ojt", "sedang_berjalan"]) == 1021
    assert int(baris.loc["ojt", "sudah_tuntas"]) == 979


def test_denyut_pipeline_invarian_jumlah_2027_01_06():
    df = metrics.denyut_pipeline(acuan=date(2027, 1, 6))
    assert (df["jumlah"] == df["sedang_berjalan"] + df["sudah_tuntas"]).all()
    baris = df.set_index("tahap_kode")
    assert int(baris.loc["ojt", "sedang_berjalan"]) == 0
    assert int(baris.loc["ojt", "sudah_tuntas"]) == 2000


def test_denyut_pipeline_2019_09_10_pendaftaran_ramai():
    df = metrics.denyut_pipeline(acuan=date(2019, 9, 10))
    assert (df["jumlah"] == df["sedang_berjalan"] + df["sudah_tuntas"]).all()
    baris = df.set_index("tahap_kode")
    assert int(baris.loc["pendaftaran", "jumlah"]) == 14348
    assert int(baris.loc["pendaftaran", "sedang_berjalan"]) == 14348
    assert int(baris.loc["administrasi", "sudah_tuntas"]) == 14117


# ──────────────────────────────────────────────────────────────────────────────
# M04 -- aktivitas_sekitar
# ──────────────────────────────────────────────────────────────────────────────


def test_aktivitas_sekitar_bentuk_kolom():
    df = metrics.aktivitas_sekitar(acuan=date(2026, 8, 22))
    assert list(df.columns) == [
        "arah",
        "jenis",
        "gelombang",
        "tahap",
        "tanggal",
        "selisih_hari",
        "jumlah",
    ]
    assert set(df["arah"]) <= {"terakhir", "berikutnya"}


def test_aktivitas_sekitar_2026_08_22():
    df = metrics.aktivitas_sekitar(acuan=date(2026, 8, 22)).set_index("arah")
    assert df.loc["terakhir", "gelombang"] == "G2025-092"
    assert int(df.loc["terakhir", "selisih_hari"]) == -126
    assert int(df.loc["terakhir", "jumlah"]) == 1021
    assert df.loc["berikutnya", "gelombang"] == "G2025-091"
    assert int(df.loc["berikutnya", "selisih_hari"]) == 40
    assert int(df.loc["berikutnya", "jumlah"]) == 979


def test_aktivitas_sekitar_2027_01_06_hanya_satu_baris():
    """Sesudah 2026-10-15 tidak ada lagi peristiwa terjadwal di seluruh
    database (J10) -- hanya sisi 'terakhir' yang punya baris."""
    df = metrics.aktivitas_sekitar(acuan=date(2027, 1, 6))
    assert len(df) == 1
    assert df.iloc[0]["arah"] == "terakhir"
    assert df.iloc[0]["gelombang"] == "G2025-092"
    assert int(df.iloc[0]["selisih_hari"]) == -83


# ──────────────────────────────────────────────────────────────────────────────
# Tes bentuk tambahan disyaratkan G9 -- lihat catatan lewat/dilewati di laporan
# ──────────────────────────────────────────────────────────────────────────────

# 1. Filter anomali unit_induk (jumlah_pegawai > 50, J4/CATATAN_DATA.md): kini
#    relevan sejak G11 -- lihat test_gap_ftk_* dan test_kekosongan_per_unit_*
#    di bawah, yang membuktikan filter itu memindahkan baris duplikat dari
#    peringkat 1 dan mengubah total nasional 701 -> 561 (J8 versi G11).

# 2. Uji sebaran berpola untuk lima kolom acak seragam (kota_domisili, kota_asal,
#    tempat_lahir, ukuran_baju, sekolah_universitas): DILEWATI. Metrik G11 tidak
#    menyentuh satu pun dari kelima kolom itu -- seluruhnya soal proyeksi
#    kekosongan, gap FTK, dan usulan/pagu. Tidak ada yang perlu diuji sebarannya.


# ──────────────────────────────────────────────────────────────────────────────
# B -- Perencanaan Formasi (halaman 2, G11)
# ──────────────────────────────────────────────────────────────────────────────


def test_rentang_tahun_proyeksi():
    mn, mx = metrics.rentang_tahun_proyeksi()
    assert mn == 2019
    assert mx == 2026


def test_kekosongan_per_sebab_2026():
    df = metrics.kekosongan_per_sebab(acuan=date(2026, 8, 23))
    assert list(df.columns) == [
        "tahun",
        "pensiun",
        "mengundurkan_diri",
        "meninggal_dunia",
        "phk",
        "total",
    ]
    baris = df.set_index("tahun")
    assert int(baris.loc[2026, "pensiun"]) == 780
    assert int(baris.loc[2026, "total"]) == 919


def test_kekosongan_per_sebab_dua_tahun_saat_tersedia():
    """acuan di 2025-12-01 -> tahun(acuan)=2025 dan tahun(acuan)+1=2026,
    keduanya ada di data -- dua baris."""
    df = metrics.kekosongan_per_sebab(acuan=date(2025, 12, 1))
    assert len(df) == 2
    assert list(df["tahun"]) == [2025, 2026]


def test_kekosongan_per_sebab_2027_kosong_batas_jujur():
    """Batas jujur: proyeksi_kekosongan berhenti di 2026. acuan 2027-01-06 ->
    tahun(acuan)=2027 dan +1=2028, tidak satu pun ada di data -- kosong, dan
    itu jawaban yang benar (bukan galat, bukan data lama disamarkan)."""
    df = metrics.kekosongan_per_sebab(acuan=date(2027, 1, 6))
    assert df.empty
    assert list(df.columns) == [
        "tahun",
        "pensiun",
        "mengundurkan_diri",
        "meninggal_dunia",
        "phk",
        "total",
    ]


def test_kekosongan_per_unit_2026():
    df = metrics.kekosongan_per_unit(2026)
    assert len(df) == 47  # J4: baris duplikat tersaring oleh jumlah_pegawai > 50
    assert list(df.columns) == ["unit_induk", "nama_pendek", "jenis_unit", "kekosongan"]
    assert int(df.iloc[0]["kekosongan"]) == 153
    assert df.iloc[0]["nama_pendek"] == "Kantor Pusat"


def test_kekosongan_per_unit_2027_kosong_batas_jujur():
    """proyeksi_kekosongan tidak punya tahun 2027 -- kosong, bukan galat."""
    df = metrics.kekosongan_per_unit(2027)
    assert df.empty


def test_daftar_unit_induk_47_baris_setelah_filter():
    df = metrics.daftar_unit_induk()
    assert len(df) == 47
    assert list(df.columns) == ["kode_unit", "nama_pendek"]


def test_kekosongan_per_posisi_kantor_pusat_2026():
    daftar = metrics.daftar_unit_induk()
    kode_kp = daftar.set_index("nama_pendek").loc["Kantor Pusat", "kode_unit"]
    df = metrics.kekosongan_per_posisi(kode_kp, 2026)
    assert list(df.columns) == ["nama_posisi", "sub_bidang", "jenjang", "kekosongan"]
    assert len(df) > 0
    assert (df["kekosongan"] > 0).all()


def test_gap_ftk_nasional_filter_j4():
    """WAJIB realisasi_mar_2026 (J8). Dengan filter anomali J4
    (jumlah_pegawai > 50), total nasional 561 -- bukan 701 (701 adalah 48
    baris apa adanya, termasuk duplikat J4; lihat CATATAN_DATA.md J8)."""
    hasil = metrics.gap_ftk_nasional()
    assert int(hasil["ftk"]) == 37710
    assert int(hasil["realisasi"]) == 37149
    assert int(hasil["gap"]) == 561


def test_gap_ftk_per_unit_j4_tidak_di_peringkat_1():
    """Tanpa filter, baris duplikat J4 (pecahan Yogyakarta, jumlah_pegawai=4,
    gap=140) akan menempati peringkat 1 secara palsu. Dengan filter, baris
    itu tersaring (nama_pendek "UID Jawa Tengah & DIY" cuma tersisa sekali --
    unit sungguhannya, bukan pecahannya) dan peringkat 1 adalah unit lain."""
    df = metrics.gap_ftk_per_unit()
    assert len(df) == 47
    assert list(df["nama_pendek"]).count("UID Jawa Tengah & DIY") == 1
    assert int(df.iloc[0]["gap"]) == 59
    assert df.iloc[0]["nama_pendek"] == "UID Jawa Barat"


def test_usulan_vs_pagu_2019_2025():
    df = metrics.usulan_vs_pagu()
    assert list(df["tahun"]) == [2019, 2020, 2021, 2022, 2023, 2024, 2025]
    baris = df.set_index("tahun")
    assert int(baris.loc[2025, "pagu"]) == 1050
    assert int(baris.loc[2025, "usulan"]) == 1238


# ──────────────────────────────────────────────────────────────────────────────
# C -- Seleksi Berjalan (halaman 3, G12)
#
# Dua tanggal acuan WAJIB: 2026-08-23 (tidak ada gelombang terbuka -- jalur
# keadaan kosong) dan 2025-10-03 (G2025-092 terbuka tgl_buka=2025-10-01,
# tgl_tutup=2025-10-05 -- jalur gelombang aktif, supaya tidak hanya jalur
# kosong yang teruji).
# ──────────────────────────────────────────────────────────────────────────────


def test_gelombang_terbuka_2026_08_23_kosong():
    """Hari ini (jangkar suite) -- tidak ada gelombang terbuka, dan itu benar
    (P3): gelombang terakhir (G2025-092) tutup 2025-10-05, jauh sebelum acuan."""
    df = metrics.gelombang_terbuka(acuan=date(2026, 8, 23))
    assert df.empty
    assert list(df.columns) == [
        "gelombang_id",
        "nama_gelombang",
        "tgl_buka",
        "tgl_tutup",
        "hari_tersisa",
        "n_profesi",
        "diterima_target",
    ]


def test_gelombang_terbuka_2025_10_03_aktif():
    df = metrics.gelombang_terbuka(acuan=date(2025, 10, 3))
    assert len(df) == 1
    baris = df.iloc[0]
    assert baris["gelombang_id"] == "G2025-092"
    assert int(baris["hari_tersisa"]) == 2
    assert int(baris["n_profesi"]) == 12
    assert int(baris["diterima_target"]) == 1021


def test_profesi_gelombang_g2025_092():
    df = metrics.profesi_gelombang("G2025-092")
    assert len(df) == 12
    assert list(df.columns) == ["nama_profesi", "jenjang", "kota_rekrutmen", "kuota"]
    assert (df["kota_rekrutmen"] == "Seluruh Indonesia").all()


def test_posisi_tahap_seleksi_2025_10_03_semua_menunggu():
    """Pada 2025-10-03, Gelombang baru tutup pendaftaran -- seluruh tahap
    seleksi masih terjadwal di masa depan (administrasi mulai 2025-10-08)."""
    df = metrics.posisi_tahap_seleksi("G2025-092", acuan=date(2025, 10, 3))
    assert list(df.columns) == [
        "urutan",
        "tahap_kode",
        "nama",
        "jumlah",
        "menunggu",
        "sudah_lewat",
    ]
    assert len(df) == 6
    baris = df.set_index("tahap_kode")
    assert int(baris.loc["administrasi", "jumlah"]) == 49801
    assert int(baris.loc["administrasi", "menunggu"]) == 49801
    assert int(baris.loc["administrasi", "sudah_lewat"]) == 0
    assert int(baris.loc["wawancara", "jumlah"]) == 1259


def test_posisi_tahap_seleksi_2026_01_01_administrasi_sudah_lewat():
    """Pada 2026-01-01, administrasi s.d. psikologi sudah lewat; fisik_mcu &
    wawancara belum (mulai 2026-01-05 dan 2026-01-31)."""
    df = metrics.posisi_tahap_seleksi("G2025-092", acuan=date(2026, 1, 1)).set_index("tahap_kode")
    assert int(df.loc["administrasi", "sudah_lewat"]) == 49801
    assert int(df.loc["psikologi", "sudah_lewat"]) == 3406
    assert int(df.loc["fisik_mcu", "sudah_lewat"]) == 0
    assert int(df.loc["fisik_mcu", "menunggu"]) == 1658


def test_jadwal_tahap_berikutnya_2025_10_03():
    df = metrics.jadwal_tahap_berikutnya("G2025-092", acuan=date(2025, 10, 3))
    assert list(df.columns) == [
        "tahap_kode",
        "nama_tahap",
        "tanggal_tahap",
        "lokasi_kota",
        "vendor",
        "jumlah",
    ]
    assert len(df) == 1
    baris = df.iloc[0]
    assert baris["tahap_kode"] == "administrasi"
    assert baris["tanggal_tahap"] == pd.Timestamp("2025-10-08")
    assert int(baris["jumlah"]) == 2644


def test_jadwal_tahap_berikutnya_kosong_setelah_horison():
    """Sesudah jadwal terakhir gelombang (wawancara berakhir 2026-02-16),
    tidak ada lagi tahap terjadwal -- kosong, bukan galat."""
    df = metrics.jadwal_tahap_berikutnya("G2025-092", acuan=date(2026, 3, 1))
    assert df.empty


def test_kehadiran_tahap_terakhir_2025_10_03_belum_ada():
    """Pada 2025-10-03 belum ada satu pun tahap berkehadiran yang lewat
    (administrasi tidak punya konsep kehadiran) -- None, bukan galat."""
    assert metrics.kehadiran_tahap_terakhir("G2025-092", acuan=date(2025, 10, 3)) is None


def test_kehadiran_tahap_terakhir_2026_01_01_terisi():
    """Membuktikan jalur berisi benar-benar berjalan, bukan cuma jalur None:
    pada 2026-01-01, psikologi (berakhir 2025-12-26) adalah tahap
    berkehadiran terakhir yang lewat."""
    hasil = metrics.kehadiran_tahap_terakhir("G2025-092", acuan=date(2026, 1, 1))
    assert hasil is not None
    assert hasil["tahap_kode"] == "psikologi"
    assert hasil["tanggal_tahap"] == pd.Timestamp("2025-12-26")
    assert hasil["hadir"] == 268
    assert hasil["tidak_hadir"] == 33
    assert hasil["total"] == 301


def test_gelombang_terakhir_selesai_2026_08_23():
    hasil = metrics.gelombang_terakhir_selesai(acuan=date(2026, 8, 23))
    assert hasil is not None
    assert hasil["gelombang_id"] == "G2025-092"
    assert hasil["tgl_tutup"] == pd.Timestamp("2025-10-05")
    assert hasil["pendaftar"] == 49801
    assert hasil["diterima"] == 1021
    assert hasil["gagal"] == 48780


def test_gelombang_terakhir_selesai_2025_10_03_gelombang_sebelumnya():
    """Pada 2025-10-03, G2025-092 masih terbuka (belum 'selesai') -- gelombang
    terakhir yang sudah tutup adalah G2025-091."""
    hasil = metrics.gelombang_terakhir_selesai(acuan=date(2025, 10, 3))
    assert hasil is not None
    assert hasil["gelombang_id"] == "G2025-091"


def test_gugur_per_tahap_gelombang_g2025_092():
    df = metrics.gugur_per_tahap_gelombang("G2025-092")
    assert list(df.columns) == ["urutan", "tahap_kode", "nama", "jumlah"]
    assert len(df) == 6
    baris = df.set_index("tahap_kode")
    assert int(baris.loc["administrasi", "jumlah"]) == 18623
    assert int(baris.loc["adaptif", "jumlah"]) == 21760
    assert int(df["jumlah"].sum()) == 48780  # cocok dengan "gagal" di atas


# ──────────────────────────────────────────────────────────────────────────────
# D -- Corong Seleksi (halaman 4, G13)
#
# Analisis lintas gelombang -- tidak terikat `hari_ini()`, jadi tidak butuh
# dua tanggal acuan seperti bagian C. Dua ragam parameter WAJIB diuji:
# tanpa filter (seluruh gelombang, angka anchor rancangan) dan dengan filter
# satu gelombang (G2025-092, dibandingkan langsung ke M18/test C di atas).
# ──────────────────────────────────────────────────────────────────────────────


def test_corong_tahap_seleksi_seluruh_gelombang_angka_anchor():
    df = metrics.corong_tahap_seleksi()
    assert list(df.columns) == [
        "urutan",
        "tahap_kode",
        "nama",
        "masuk",
        "hadir",
        "tidak_hadir",
        "lulus",
        "gagal",
    ]
    assert len(df) == 6
    baris = df.set_index("tahap_kode")
    assert int(baris.loc["administrasi", "masuk"]) == 213648
    assert int(baris.loc["administrasi", "lulus"]) == 143831
    assert int(baris.loc["administrasi", "hadir"]) == 0
    assert int(baris.loc["administrasi", "tidak_hadir"]) == 0
    assert int(baris.loc["adaptif", "masuk"]) == 143831
    assert int(baris.loc["adaptif", "hadir"]) == 68896
    assert int(baris.loc["adaptif", "tidak_hadir"]) == 74935
    assert int(baris.loc["adaptif", "lulus"]) == 48627
    assert int(baris.loc["akademik_inggris", "masuk"]) == 53907
    assert int(baris.loc["akademik_inggris", "hadir"]) == 44358
    assert int(baris.loc["akademik_inggris", "lulus"]) == 24699
    assert int(baris.loc["akademik_inggris", "tidak_hadir"]) == 9549
    assert int(baris.loc["psikologi", "lulus"]) == 15980
    assert int(baris.loc["fisik_mcu", "lulus"]) == 12623
    assert int(baris.loc["wawancara", "masuk"]) == 12623
    assert int(baris.loc["wawancara", "lulus"]) == 7711
    assert int(baris.loc["wawancara", "tidak_hadir"]) == 764


def test_corong_tahap_seleksi_filter_gelombang_cocok_gugur_per_tahap():
    """Difilter satu gelombang, harus cocok persis dengan M18 (angka `gagal`
    == `gugur_per_tahap_gelombang`) dan dengan posisi_tahap_seleksi (`masuk`
    == `jumlah`)."""
    df = metrics.corong_tahap_seleksi("G2025-092").set_index("tahap_kode")
    gugur = metrics.gugur_per_tahap_gelombang("G2025-092").set_index("tahap_kode")
    assert int(df.loc["administrasi", "masuk"]) == 49801
    assert int(df.loc["administrasi", "gagal"]) == int(gugur.loc["administrasi", "jumlah"]) == 18623
    assert int(df.loc["adaptif", "gagal"]) == int(gugur.loc["adaptif", "jumlah"]) == 21760
    assert int(df.loc["wawancara", "lulus"]) == 1021  # diterima_target G2025-092


def test_corong_tahap_seleksi_gelombang_tanpa_data_kosong():
    """Gelombang yang tidak pernah ada -- kosong, bukan galat."""
    df = metrics.corong_tahap_seleksi("G0000-000")
    assert df.empty


def test_no_show_per_tahap_mode_anchor_tap_online():
    df = metrics.no_show_per_tahap_mode()
    assert list(df.columns) == [
        "urutan",
        "tahap_kode",
        "nama",
        "mode",
        "tidak_hadir",
        "total",
        "pct_no_show",
    ]
    assert len(df) == 5  # administrasi tidak berkehadiran, tidak muncul
    baris = df.set_index("tahap_kode")
    assert baris.loc["adaptif", "mode"] == "online"
    assert float(baris.loc["adaptif", "pct_no_show"]) == 52.1
    assert float(baris.loc["akademik_inggris", "pct_no_show"]) == 17.7
    assert baris.loc["wawancara", "mode"] == "offline"
    assert float(baris.loc["wawancara", "pct_no_show"]) == 6.1


# ──────────────────────────────────────────────────────────────────────────────
# E -- Pasca-Seleksi (halaman 5, G14)
#
# Terikat penuh ke `hari_ini()` -- beda dari bagian D. Angka jangkar utama:
# 2.000 orang kohort 2025 (G2025-091 979 + G2025-092 1.021) berhenti di OJT,
# ujian_ojt/sk_penempatan tidak punya baris sama sekali (J9) -- diuji di
# beberapa `acuan`, termasuk yang jauh melewati horison data, untuk
# membuktikan selisihnya tidak pernah bergerak.
# ──────────────────────────────────────────────────────────────────────────────


def test_daftar_kohort_pasca_bentuk_dan_anchor():
    df = metrics.daftar_kohort_pasca()
    assert list(df.columns) == [
        "gelombang_id",
        "nama_gelombang",
        "peserta",
        "tanggal_mulai",
        "tanggal_terakhir",
    ]
    assert len(df) == 17
    baris = df.set_index("gelombang_id")
    assert int(baris.loc["G2025-091", "peserta"]) == 979
    assert int(baris.loc["G2025-092", "peserta"]) == 1021
    assert int(baris.loc["G2024-088", "peserta"]) == 288


def test_kohort_relevan_mengikuti_acuan():
    assert metrics.kohort_relevan(date(2026, 8, 23)) == "G2025-092"
    assert metrics.kohort_relevan(date(2027, 1, 6)) == "G2025-092"
    assert metrics.kohort_relevan(date(2025, 3, 1)) == "G2024-088"
    assert metrics.kohort_relevan(date(2019, 1, 1)) == "G2019-070"


def test_lini_masa_pasca_kohort_2025_091_selisih_ojt_menggantung():
    """Kolom peserta ujian_ojt/sk_penempatan tetap 0 di kedua acuan -- J9."""
    for acuan in (date(2026, 8, 23), date(2027, 1, 6)):
        df = metrics.lini_masa_pasca_kohort("G2025-091", acuan=acuan)
        assert list(df.columns) == [
            "urutan",
            "tahap_kode",
            "nama",
            "peserta",
            "tanggal_mulai",
            "tanggal_selesai",
            "selesai",
            "berjalan",
            "belum_mulai",
        ]
        assert len(df) == 7
        baris = df.set_index("tahap_kode")
        assert int(baris.loc["pengumuman_akhir", "peserta"]) == 979
        assert int(baris.loc["ojt", "peserta"]) == 979
        assert int(baris.loc["ujian_ojt", "peserta"]) == 0
        assert int(baris.loc["sk_penempatan", "peserta"]) == 0

    tuntas = metrics.lini_masa_pasca_kohort("G2025-091", acuan=date(2026, 10, 20)).set_index(
        "tahap_kode"
    )
    assert int(tuntas.loc["ojt", "selesai"]) == 979
    assert int(tuntas.loc["ujian_ojt", "peserta"]) == 0


def test_lini_masa_pasca_kohort_lama_punya_ketujuh_tahap():
    """Kohort G2024-088 sudah tuntas -- ujian_ojt & sk_penempatan berisi
    penuh, pembanding bahwa J9 khusus kohort 2025."""
    df = metrics.lini_masa_pasca_kohort("G2024-088", acuan=date(2025, 3, 1)).set_index(
        "tahap_kode"
    )
    assert int(df.loc["samapta", "peserta"]) == 288
    assert int(df.loc["samapta", "selesai"]) == 268
    assert int(df.loc["samapta", "belum_mulai"]) == 20
    assert int(df.loc["ujian_ojt", "peserta"]) == 288
    assert int(df.loc["sk_penempatan", "peserta"]) == 288


def test_status_samapta_kohort_anchor():
    s91 = metrics.status_samapta_kohort("G2025-091")
    assert s91["peserta"] == 979
    assert s91["durasi_hari"] == 14
    s92 = metrics.status_samapta_kohort("G2025-092")
    assert s92["peserta"] == 1021
    assert s92["durasi_hari"] == 14


def test_status_samapta_kohort_tanpa_data_none():
    assert metrics.status_samapta_kohort("G0000-000") is None


def test_pembidangan_per_kohort_gabungan_2025_cocok_anchor_rancangan():
    a = metrics.pembidangan_per_kohort("G2025-091").set_index("bidang_pembidangan")["jumlah"]
    b = metrics.pembidangan_per_kohort("G2025-092").set_index("bidang_pembidangan")["jumlah"]
    total = a.add(b, fill_value=0)
    assert len(total) == 9
    assert int(total["Pembangkitan"]) == 481
    assert int(total["SDM"]) == 362
    assert int(total["Distribusi"]) == 258
    assert int(total["Transmisi dan Gardu Induk"]) == 215
    assert int(total["Manajemen Konstruksi dan Pengadaan"]) == 197
    assert int(total["Keuangan"]) == 169
    assert int(total["Niaga"]) == 165
    assert int(total["Perencanaan Sistem"]) == 91
    assert int(total["Proteksi dan Kontrol"]) == 62


def test_ojt_per_updl_kohort_selalu_11_baris_gabungan_cocok_anchor():
    df91 = metrics.ojt_per_updl_kohort("G2025-091")
    assert len(df91) == 11  # granularitas penuh (P5), termasuk yang bernilai 0
    u91 = df91.set_index("nama_updl")["jumlah"]
    u92 = metrics.ojt_per_updl_kohort("G2025-092").set_index("nama_updl")["jumlah"]
    total = u91.add(u92, fill_value=0)
    assert int(total["UPDL Semarang"]) == 257
    assert int(total["UPDL Pandaan"]) == 234
    assert int(total["UPDL Surabaya"]) == 228
    assert int(total["UPDL Tuntungan"]) == 201
    assert int(total["UPDL Palembang"]) == 195
    assert int(total["UPDL Padang"]) == 162
    assert int(total["UPDL Makassar"]) == 158
    assert int(total["UPDL Jakarta"]) == 152
    assert int(total["UPDL Bogor"]) == 141
    assert int(total["UPDL Suralaya"]) == 136
    assert int(total["UPDL Banjarbaru"]) == 136


def test_status_sk_kohort_2025_selalu_nol_terbit_berapa_pun_acuan():
    for acuan in (date(2026, 8, 23), date(2027, 1, 6)):
        s = metrics.status_sk_kohort("G2025-091", acuan=acuan)
        assert s == {"total": 979, "terbit": 0, "menunggu": 979}


def test_status_sk_kohort_lama_sudah_terbit_semua():
    s = metrics.status_sk_kohort("G2024-088", acuan=date(2026, 8, 23))
    assert s == {"total": 288, "terbit": 288, "menunggu": 0}


def test_unit_tujuan_sk_kohort_2025_kosong_lama_terisi():
    assert metrics.unit_tujuan_sk_kohort("G2025-091").empty
    df = metrics.unit_tujuan_sk_kohort("G2024-088")
    assert len(df) == 45
    assert int(df.set_index("nama_pendek").loc["Kantor Pusat", "jumlah"]) == 38


def test_rbb_masuk_akademik_inggris_nasional():
    assert metrics.rbb_masuk_akademik_inggris() == 5280


def test_rbb_masuk_akademik_inggris_per_gelombang():
    """Hanya gelombang RBB yang punya nilai bukan nol; gelombang mandiri 0 --
    jawaban yang benar, bukan galat."""
    assert metrics.rbb_masuk_akademik_inggris("G2020-074") == 455
    assert metrics.rbb_masuk_akademik_inggris("G2021-075") == 179
    assert metrics.rbb_masuk_akademik_inggris("G2024-087") == 3599
    assert metrics.rbb_masuk_akademik_inggris("G2024-088") == 1047
    assert metrics.rbb_masuk_akademik_inggris("G2025-092") == 0


def test_corong_fhci_tiga_tahap():
    df = metrics.corong_fhci()
    assert list(df.columns) == ["urutan", "tahap_kode", "nama", "masuk", "lulus", "pct_lulus"]
    assert len(df) == 3
    baris = df.set_index("tahap_kode")
    assert int(baris.loc["fhci_administrasi", "masuk"]) == 269395
    assert int(baris.loc["fhci_administrasi", "lulus"]) == 107758
    assert int(baris.loc["fhci_tes_online_2", "lulus"]) == 5280  # cocok M21


def test_daftar_gelombang_19_baris_terbaru_dulu():
    df = metrics.daftar_gelombang()
    assert list(df.columns) == ["gelombang_id", "nama_gelombang", "tgl_tutup"]
    assert len(df) == 19
    assert df.iloc[0]["gelombang_id"] == "G2025-092"
    assert df.iloc[-1]["gelombang_id"] == "G2019-070"


# ──────────────────────────────────────────────────────────────────────────────
# F -- Rencana & Realisasi (halaman 6, G15)
#
# Analisis lintas-tahun atas riwayat yang sudah tuntas (2019-2025) -- seperti
# bagian D, tidak terikat `hari_ini()`.
# ──────────────────────────────────────────────────────────────────────────────


def test_pagu_target_realisasi_tahunan_anchor_rancangan():
    """Cocok persis dengan tabel Temuan A di docs/RANCANGAN_HALAMAN.md §8."""
    df = metrics.pagu_target_realisasi_tahunan()
    assert list(df.columns) == [
        "tahun",
        "pagu",
        "target_gelombang",
        "ditempatkan",
        "selisih_pagu_target",
    ]
    assert list(df["tahun"]) == [2019, 2020, 2021, 2022, 2023, 2024, 2025]
    baris = df.set_index("tahun")
    assert int(baris.loc[2019, "pagu"]) == 1093
    assert int(baris.loc[2019, "target_gelombang"]) == 1353
    assert int(baris.loc[2019, "ditempatkan"]) == 1353
    assert int(baris.loc[2019, "selisih_pagu_target"]) == 260
    assert int(baris.loc[2020, "ditempatkan"]) == 125
    assert int(baris.loc[2020, "selisih_pagu_target"]) == 0
    assert int(baris.loc[2021, "ditempatkan"]) == 49
    assert int(baris.loc[2024, "pagu"]) == 1098
    assert int(baris.loc[2024, "target_gelombang"]) == 1578
    assert int(baris.loc[2024, "ditempatkan"]) == 1278
    assert int(baris.loc[2025, "pagu"]) == 1050
    assert int(baris.loc[2025, "target_gelombang"]) == 2000
    assert int(baris.loc[2025, "ditempatkan"]) == 2000
    assert int(baris.loc[2025, "selisih_pagu_target"]) == 950


def test_rencana_realisasi_per_unit_2019_2024_47_baris():
    """Filter anomali J4 (jumlah_pegawai > 50) -- konsisten dengan bagian B."""
    df = metrics.rencana_realisasi_per_unit()
    assert list(df.columns) == ["kode_unit", "nama_pendek", "rencana", "realisasi", "selisih"]
    assert len(df) == 47
    baris = df.set_index("nama_pendek")
    assert int(baris.loc["Kantor Pusat", "rencana"]) == 2056
    assert int(baris.loc["Kantor Pusat", "realisasi"]) == 447
    assert int(baris.loc["Kantor Pusat", "selisih"]) == -1609


def test_pemenuhan_per_tahun_anchor_tahun_rbb():
    df = metrics.pemenuhan_per_tahun()
    assert list(df.columns) == [
        "tahun",
        "target_gelombang",
        "ditempatkan",
        "pct_pemenuhan",
        "tahun_rbb",
    ]
    baris = df.set_index("tahun")
    assert bool(baris.loc[2020, "tahun_rbb"])
    assert bool(baris.loc[2021, "tahun_rbb"])
    assert bool(baris.loc[2024, "tahun_rbb"])
    assert not bool(baris.loc[2019, "tahun_rbb"])
    assert not bool(baris.loc[2022, "tahun_rbb"])
    assert not bool(baris.loc[2023, "tahun_rbb"])
    assert not bool(baris.loc[2025, "tahun_rbb"])
    assert float(baris.loc[2021, "pct_pemenuhan"]) == 7.1  # anchor CATATAN_DATA.md §7
    assert float(baris.loc[2020, "pct_pemenuhan"]) == 38.5
    assert float(baris.loc[2024, "pct_pemenuhan"]) == 81.0

    non_rbb = df[~df["tahun_rbb"]]
    assert round(float(non_rbb["pct_pemenuhan"].mean()), 1) == 100.0


# ──────────────────────────────────────────────────────────────────────────────
# G -- Profil Pelamar (halaman 7, G16)
#
# Tidak terikat hari_ini() -- riwayat pelamar 2019-2025 sudah tuntas, sama
# seperti bagian D dan F.
# ──────────────────────────────────────────────────────────────────────────────


def test_umur_gender_pelamar_anchor():
    df = metrics.umur_gender_pelamar()
    assert list(df.columns) == ["umur", "jenis_kelamin", "jumlah"]
    assert len(df) == 36
    assert df["umur"].min() == 20
    assert df["umur"].max() == 39
    total = df.groupby("jenis_kelamin")["jumlah"].sum()
    assert int(total["P"]) == 142465
    assert int(total["W"]) == 76463
    baris = df.set_index(["umur", "jenis_kelamin"])
    assert int(baris.loc[(20, "P"), "jumlah"]) == 7241
    assert int(baris.loc[(20, "W"), "jumlah"]) == 3999


def test_jenjang_pendidikan_pelamar_anchor():
    df = metrics.jenjang_pendidikan_pelamar()
    assert list(df.columns) == ["degree", "jumlah"]
    assert len(df) == 4
    baris = df.set_index("degree")
    assert int(baris.loc["S1/D-IV", "jumlah"]) == 245553
    assert int(baris.loc["D-III", "jumlah"]) == 98161
    assert int(baris.loc["SMK", "jumlah"]) == 11696
    assert int(baris.loc["S2", "jumlah"]) == 11631
    assert int(df["jumlah"].sum()) == 367041


def test_rumpun_jurusan_konversi_anchor():
    df = metrics.rumpun_jurusan_konversi()
    assert list(df.columns) == ["rumpun", "melamar", "diterima"]
    assert len(df) == 18
    assert int(df["melamar"].sum()) == 216958
    assert int(df["diterima"].sum()) == 7429
    baris = df.set_index("rumpun")
    assert int(baris.loc["Manajemen dan Bisnis", "melamar"]) == 36073
    assert int(baris.loc["Manajemen dan Bisnis", "diterima"]) == 1206
    assert int(baris.loc["Informatika dan Data", "melamar"]) == 24639


def test_provinsi_domisili_pelamar_anchor():
    """Rasio terbesar/terkecil 16,4x -- CATATAN_DATA.md J1 (kolom berpola benar)."""
    df = metrics.provinsi_domisili_pelamar()
    assert list(df.columns) == ["propinsi_domisili", "jumlah"]
    assert len(df) == 32  # 31 provinsi + 1 baris None
    baris = df.set_index("propinsi_domisili")
    assert int(baris.loc["Jawa Barat", "jumlah"]) == 50806
    assert int(baris.loc["Kepulauan Riau", "jumlah"]) == 3106
    assert round(df["jumlah"].max() / df["jumlah"].min(), 1) == 16.4
    assert int(baris.loc[None, "jumlah"]) == 13788


def test_volume_tes_per_kota_anchor():
    """43 kota, rasio 37,7x -- CATATAN_DATA.md J1 (kolom berpola benar)."""
    df = metrics.volume_tes_per_kota()
    assert list(df.columns) == ["lokasi_kota", "jumlah"]
    assert len(df) == 43
    baris = df.set_index("lokasi_kota")
    assert int(baris.loc["Makassar", "jumlah"]) == 5162
    assert round(df["jumlah"].max() / df["jumlah"].min(), 1) == 37.7


def test_kelengkapan_akun_per_kohort_anchor():
    df = metrics.kelengkapan_akun_per_kohort()
    assert list(df.columns) == ["tahun_kohort", "total", "lengkap", "pct_lengkap"]
    assert list(df["tahun_kohort"]) == [2019, 2020, 2021, 2022, 2023, 2024, 2025]
    baris = df.set_index("tahun_kohort")
    assert int(baris.loc[2019, "total"]) == 96875
    assert int(baris.loc[2019, "lengkap"]) == 84773
    assert float(baris.loc[2019, "pct_lengkap"]) == 87.5
    assert float(baris.loc[2020, "pct_lengkap"]) == 83.4  # penyimpangan tren, bukan monoton
    assert float(baris.loc[2025, "pct_lengkap"]) == 95.5
