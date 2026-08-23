"""Lapis 1 -- angka jangkar terhadap DB nyata (tests/conftest.py sudah menaruh
root v3 di sys.path, tidak perlu sys.path.insert di sini).

`core/metrics.py` menerima `acuan: date | None` -- beda dari v2 yang jangkarnya
beku -- jadi tiap assert di sini memakai `acuan=date(...)` eksplisit, memakai
nilai yang sudah diverifikasi di `docs/metrik.md`. Dijalankan terhadap
`mockdb/out/rekrutmen.duckdb` sungguhan (read-only), tidak ada mock.
"""

from __future__ import annotations

from datetime import date

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
