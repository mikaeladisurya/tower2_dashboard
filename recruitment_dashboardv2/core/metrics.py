"""Implementasi kamus metrik — SATU definisi untuk seluruh aplikasi.

Aturan arsitektur: **halaman tidak boleh menulis SQL agregat sendiri.** Semua angka
yang tampil di dashboard (dan yang dirujuk chatbot) berasal dari modul ini, supaya
halaman 1, halaman 6, dan jawaban chatbot tidak pernah berbeda.

Kode metrik (M01, M08, …) merujuk ke `docs/metrik.md`. Kalau butuh angka baru,
tambahkan metriknya di dokumen itu dulu, baru di sini.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from core.db import query, skalar

_KOORDINAT_PATH = Path(__file__).resolve().parents[1] / "data" / "koordinat.csv"

# ──────────────────────────────────────────────────────────────────────────────
# A. Ringkasan (halaman 1)
# ──────────────────────────────────────────────────────────────────────────────


def ringkasan() -> dict[str, float]:
    """M01–M07 sekaligus — dipakai baris KPI halaman 1."""
    return {
        "pendaftaran": skalar("SELECT count(*) FROM pendaftaran"),
        "pelamar": skalar("SELECT count(DISTINCT kandidat_id) FROM pendaftaran"),
        "akun": skalar("SELECT count(*) FROM kandidat"),
        "diterima": skalar(
            "SELECT count(*) FROM pendaftaran WHERE hasil_akhir = 'DITERIMA'"
        ),
        "rasio": skalar(
            "SELECT round(count(*)*1.0 / nullif(sum(CASE WHEN hasil_akhir='DITERIMA' "
            "THEN 1 END), 0), 1) FROM pendaftaran"
        ),
        "sudah_sk": skalar(
            "SELECT count(*) FROM penempatan WHERE status_sk = 'SUDAH'"
        ),
        "sedang_ojt": skalar(
            "SELECT count(*) FROM pasca_tahap "
            "WHERE tahap_kode = 'ojt' AND status = 'BERJALAN'"
        ),
    }


def tren_tahunan() -> pd.DataFrame:
    """M11 — pendaftaran & diterima per tahun program, dipisah jalur."""
    return query(
        """
        SELECT g.tahun_program AS tahun,
               g.sumber_rekrutmen AS jalur,
               count(*) AS pendaftaran,
               sum(CASE WHEN p.hasil_akhir = 'DITERIMA' THEN 1 ELSE 0 END) AS diterima
        FROM pendaftaran p
        JOIN gelombang g USING (gelombang_id)
        GROUP BY 1, 2
        ORDER BY 1
        """
    )


# ──────────────────────────────────────────────────────────────────────────────
# B. Corong seleksi (halaman 3)
# ──────────────────────────────────────────────────────────────────────────────


def funnel_seleksi() -> pd.DataFrame:
    """M08 — enam tahap seleksi PLN dengan konversi & no-show.

    Catatan: tahap `administrasi` tidak punya kehadiran (seleksi dokumen), jadi
    `pct_no_show`-nya NULL — bukan 0. Jangan diisi nol saat menampilkan.
    """
    return query(
        """
        SELECT r.urutan,
               r.tahap_kode,
               r.nama,
               count(*) AS masuk,
               sum(CASE WHEN t.status_hadir = 'HADIR' THEN 1 ELSE 0 END) AS hadir,
               sum(CASE WHEN t.hasil = 'LULUS' THEN 1 ELSE 0 END) AS lulus,
               round(100.0 * sum(CASE WHEN t.hasil = 'LULUS' THEN 1 ELSE 0 END)
                     / count(*), 1) AS pct_lulus,
               round(100.0 * sum(CASE WHEN t.status_hadir = 'TIDAK_HADIR' THEN 1 ELSE 0 END)
                     / nullif(sum(CASE WHEN t.status_hadir IS NOT NULL THEN 1 END), 0),
                     1) AS pct_no_show
        FROM seleksi_tahap t
        JOIN tahap_ref r USING (tahap_kode)
        GROUP BY 1, 2, 3
        ORDER BY 1
        """
    )


def gugur_per_tahap() -> pd.DataFrame:
    """M10 — di tahap mana pendaftaran berhenti."""
    return query(
        """
        SELECT tahap_gugur, count(*) AS gugur
        FROM pendaftaran
        WHERE hasil_akhir = 'GAGAL'
        GROUP BY 1
        ORDER BY 2 DESC
        """
    )


def no_show_keseluruhan() -> float:
    """M09 — persentase tidak hadir di seluruh tahap yang punya kehadiran."""
    return skalar(
        """
        SELECT round(100.0 * sum(CASE WHEN status_hadir = 'TIDAK_HADIR' THEN 1 ELSE 0 END)
               / nullif(count(status_hadir), 0), 1)
        FROM seleksi_tahap
        """
    )


def no_show_per_tahap_mode() -> pd.DataFrame:
    """M32 — no-show per tahap x mode online/offline.

    Jangkar temuan halaman Corong Seleksi: tes online kehilangan jauh lebih banyak
    peserta daripada offline. Menggantikan hipotesis jarak tempat tinggal, yang gugur
    setelah diuji (kota_domisili dibagikan acak seragam — lihat ISSUES_SEBARAN.md).
    """
    return query(
        """
        SELECT tahap_kode, mode,
               round(100.0 * sum(CASE WHEN status_hadir = 'TIDAK_HADIR' THEN 1 ELSE 0 END)
                     / count(*), 1) AS pct_no_show
        FROM seleksi_tahap
        WHERE status_hadir IS NOT NULL
        GROUP BY 1, 2
        ORDER BY 3 DESC
        """
    )


def funnel_fhci() -> pd.DataFrame:
    """M12 — corong FHCI (jalur RBB, sebelum masuk sistem PLN). AGREGAT, tanpa kandidat_id."""
    return query(
        """
        SELECT tahun_program, urutan, nama, jumlah_masuk, jumlah_lulus,
               round(100.0 * jumlah_lulus / jumlah_masuk, 1) AS pct_lulus
        FROM seleksi_tahap_agregat
        ORDER BY tahun_program, urutan
        """
    )


def jejak_rbb() -> pd.DataFrame:
    """M29 — berapa persen pelamar FHCI yang berjejak di sistem PLN.

    WAJIB pakai CTE, JANGAN JOIN langsung seleksi_tahap_agregat ke pendaftaran —
    tabel agregat punya 3 baris per tahun, join langsung menggandakan hasil 3x.
    """
    return query(
        """
        WITH fhci AS (
            SELECT tahun_program, max(CASE WHEN urutan = -3 THEN jumlah_masuk END) AS pelamar_fhci
            FROM seleksi_tahap_agregat GROUP BY 1
        ), pln AS (
            SELECT g.tahun_program, count(*) AS masuk_pln
            FROM pendaftaran p JOIN gelombang g USING (gelombang_id) GROUP BY 1
        )
        SELECT f.tahun_program AS tahun, f.pelamar_fhci, p.masuk_pln,
               round(100.0 * p.masuk_pln / f.pelamar_fhci, 2) AS pct_terlihat
        FROM fhci f LEFT JOIN pln p USING (tahun_program)
        ORDER BY 1
        """
    )


# ──────────────────────────────────────────────────────────────────────────────
# C. Perencanaan (halaman 2)
# ──────────────────────────────────────────────────────────────────────────────


def gap_ftk() -> dict[str, float]:
    """M13 — formasi vs realisasi.

    WAJIB memakai `realisasi_mar_2026`: kolom `realisasi_apr_2026` hanya terisi di
    1 dari 48 unit dan menghasilkan gap palsu 33.934.
    """
    df = query(
        """
        SELECT sum(ftk_2025) AS ftk,
               sum(realisasi_mar_2026) AS realisasi,
               sum(ftk_2025) - sum(realisasi_mar_2026) AS gap
        FROM unit_induk
        """
    )
    return df.iloc[0].to_dict()


def pagu_vs_usulan() -> pd.DataFrame:
    """M16 — berapa persen usulan unit yang disetujui jadi pagu. DIMODELKAN."""
    return query(
        """
        SELECT p.tahun_program AS tahun,
               sum(p.jumlah) AS pagu,
               round(u.usulan) AS usulan,
               round(100.0 * sum(p.jumlah) / u.usulan, 1) AS pct_disetujui
        FROM pagu_rekrutmen p
        JOIN (
            SELECT tahun_program, sum(usulan) AS usulan
            FROM usulan_kebutuhan GROUP BY 1
        ) u USING (tahun_program)
        GROUP BY 1, u.usulan
        ORDER BY 1
        """
    )


def gap_ftk_per_unit(minimal_pegawai: int = 50) -> pd.DataFrame:
    """M14 — gap FTK per unit induk.

    `unit_induk` punya baris duplikat/gagal-match untuk "UID Jawa Tengah & DIY"
    (jumlah_pegawai=4, ftk_2025=144 — lihat mockdb/ISSUES_MASTER_DATA.md). Filter
    `jumlah_pegawai > 50` menyingkirkannya tanpa perlu tahu penyebabnya lebih dulu.
    """
    return query(
        """
        SELECT nama_pendek, jenis_unit, ftk_2025, realisasi_mar_2026,
               ftk_2025 - realisasi_mar_2026 AS gap
        FROM unit_induk
        WHERE jumlah_pegawai > ?
        ORDER BY gap DESC
        """,
        [minimal_pegawai],
    )


def proyeksi_per_sebab() -> pd.DataFrame:
    """M17 — proyeksi kekosongan per sebab per tahun. DIMODELKAN.

    2019–2026 saja tabel ini yang punya tahun 2026 — isi "fase perencanaan".
    """
    return query(
        """
        SELECT tahun,
               round(sum(pensiun)) AS pensiun,
               round(sum(mengundurkan_diri)) AS aps,
               round(sum(meninggal_dunia)) AS meninggal,
               round(sum(phk)) AS phk,
               round(sum(kekosongan)) AS total
        FROM proyeksi_kekosongan
        GROUP BY 1
        ORDER BY 1
        """
    )


def heatmap_kebutuhan(tahun: int = 2025) -> pd.DataFrame:
    """M31 — usulan kebutuhan per unit induk × sub-bidang. DIMODELKAN. Lapis analis."""
    return query(
        """
        SELECT unit_induk, sub_bidang, round(sum(usulan)) AS usulan
        FROM usulan_kebutuhan
        WHERE tahun_program = ?
        GROUP BY 1, 2
        ORDER BY 3 DESC
        """,
        [tahun],
    )


# ──────────────────────────────────────────────────────────────────────────────
# D bis. Kandidat & pasar tenaga kerja (halaman 4)
# ──────────────────────────────────────────────────────────────────────────────
#
# Tiga metrik yang DIBATALKAN karena kolom sumbernya dibagikan acak seragam oleh
# generator (lihat mockdb/ISSUES_SEBARAN.md): sebaran asal per provinsi, peta asal
# vs kota tes, konversi per almamater. Tidak diimplementasikan di sini — halaman 4
# memakai volume_tes_per_kota() sebagai pengganti peta.


def akun_ringkas() -> dict[str, float]:
    """Bagian dari M03/M21 — baris KPI halaman Kandidat."""
    return {
        "akun": skalar("SELECT count(*) FROM kandidat"),
        "pelamar": skalar("SELECT count(DISTINCT kandidat_id) FROM pendaftaran"),
        "lamaran_per_akun": skalar(
            "SELECT count(*) * 1.0 / count(DISTINCT kandidat_id) FROM pendaftaran"
        ),
        "tidak_melamar": skalar(
            "SELECT count(*) FROM kandidat WHERE NOT pernah_melamar"
        ),
    }


def jenjang_pendidikan() -> pd.DataFrame:
    """M18 — jenjang pendidikan terakhir pelamar.

    Filter `pendidikan_terakhir` WAJIB — tanpa itu baris SD/SMP/SMA (±4 baris/kandidat)
    ikut terhitung.
    """
    return query(
        """
        SELECT degree, count(*) AS n
        FROM kandidat_pendidikan
        WHERE pendidikan_terakhir
        GROUP BY 1
        ORDER BY 2 DESC
        """
    )


def gender_per_kohort() -> pd.DataFrame:
    """M19 — proporsi pria per tahun kohort.

    Kode gender adalah P=Pria, W=Wanita — BUKAN L/P. Salah baca membalik chart.
    """
    return query(
        """
        SELECT tahun_kohort AS tahun, count(*) AS n,
               round(100.0 * sum(CASE WHEN jenis_kelamin = 'P' THEN 1 ELSE 0 END)
                     / count(*), 1) AS pct_pria
        FROM kandidat
        WHERE pernah_melamar
        GROUP BY 1
        ORDER BY 1
        """
    )


def umur_pelamar() -> pd.DataFrame:
    """M33 — sebaran umur pelamar saat mendaftar akun."""
    return query(
        """
        SELECT date_diff('year', tanggal_lahir, tanggal_daftar_akun) AS umur, count(*) AS n
        FROM kandidat
        WHERE pernah_melamar AND tanggal_lahir IS NOT NULL
        GROUP BY 1
        ORDER BY 1
        """
    )


def rumpun_melamar_vs_diterima() -> pd.DataFrame:
    """M34 — rumpun jurusan: melamar vs diterima.

    Join lewat tabel master `program_studi` (kolom `rumpun`) — BUKAN `profesi_prodi`
    (tidak ada kolom rumpun) dan BUKAN `rumpun_jurusan` (agregat, tanpa kolom
    penghubung ke program_studi perorangan).
    """
    return query(
        """
        WITH t AS (
            SELECT ps.rumpun, count(*) AS melamar,
                   sum(CASE WHEN p.hasil_akhir = 'DITERIMA' THEN 1 ELSE 0 END) AS diterima
            FROM pendaftaran p
            JOIN kandidat_pendidikan kp
                ON kp.kandidat_id = p.kandidat_id AND kp.pendidikan_terakhir
            JOIN program_studi ps ON ps.program_studi = kp.program_studi
            GROUP BY 1
        )
        SELECT rumpun, melamar, diterima, round(100.0 * diterima / melamar, 2) AS pct
        FROM t
        ORDER BY melamar DESC
        """
    )


def volume_tes_per_kota() -> pd.DataFrame:
    """M35 — volume tes offline per kota. Jangkar peta halaman Kandidat.

    Menggantikan peta "asal vs kota tes" yang dibatalkan (kota_domisili cacat).
    `lokasi_kota` berpola benar (rasio top/bawah 37,7x), aman dipakai.
    """
    return query(
        """
        SELECT lokasi_kota, count(*) AS n
        FROM seleksi_tahap
        WHERE mode = 'offline'
        GROUP BY 1
        ORDER BY 2 DESC
        """
    )


def volume_tes_per_kota_geo() -> pd.DataFrame:
    """M35 + koordinat statis (`data/koordinat.csv`) — jangkar peta halaman Kandidat.

    43 kota tes offline diketik tangan (lat/lon kota, bukan alamat lokasi tes persis)
    karena DuckDB tidak punya kolom geografis untuk `lokasi_kota`.
    """
    koordinat = pd.read_csv(_KOORDINAT_PATH)
    return volume_tes_per_kota().merge(
        koordinat, left_on="lokasi_kota", right_on="kota", how="inner"
    )


# ──────────────────────────────────────────────────────────────────────────────
# D. Pasca-seleksi & penempatan (halaman 5 & 6)
# ──────────────────────────────────────────────────────────────────────────────


def posisi_pipeline() -> pd.DataFrame:
    """M22 — berapa orang di tiap tahap pasca-seleksi pada tanggal potong."""
    return query(
        """
        SELECT p.tahap_kode,
               r.nama,
               min(p.urutan) AS urutan,
               sum(CASE WHEN p.status = 'SELESAI' THEN 1 ELSE 0 END) AS selesai,
               sum(CASE WHEN p.status = 'BERJALAN' THEN 1 ELSE 0 END) AS berjalan,
               count(*) AS total
        FROM pasca_tahap p
        JOIN tahap_ref r USING (tahap_kode)
        GROUP BY 1, 2
        ORDER BY 3
        """
    )


def penempatan_jenis() -> pd.DataFrame:
    """M24 — induk vs subholding."""
    return query(
        """
        SELECT jenis_penempatan, count(*) AS jumlah
        FROM penempatan
        GROUP BY 1
        ORDER BY 2 DESC
        """
    )


def pembidangan() -> pd.DataFrame:
    """M23 — pembidangan hasil penempatan."""
    return query(
        """
        SELECT bidang_pembidangan, count(*) AS n
        FROM penempatan
        GROUP BY 1
        ORDER BY 2 DESC
        """
    )


def sebaran_updl() -> pd.DataFrame:
    """M36 — sebaran penempatan per UPDL (11 lokasi)."""
    return query(
        """
        SELECT d.nama AS updl, count(*) AS n
        FROM penempatan p JOIN updl d ON p.updl_id = d.updl_id
        GROUP BY 1
        ORDER BY 2 DESC
        """
    )


def timeline_kohort() -> pd.DataFrame:
    """M37 — rentang tanggal gelombang per tahun, untuk sumbu Gantt."""
    return query(
        """
        SELECT tahun_program AS tahun, min(tgl_buka) AS mulai, max(tgl_tutup) AS selesai,
               count(*) AS n_gelombang
        FROM gelombang
        GROUP BY 1
        ORDER BY 1
        """
    )


def treemap_penempatan() -> pd.DataFrame:
    """M38 — penempatan per unit induk x bidang pembidangan. Jangkar treemap halaman 6.

    Dijoin ke `unit_induk.nama_pendek` — `penempatan.unit_induk` sendiri berisi nama
    resmi panjang ("PT PLN (PERSERO) UNIT INDUK DISTRIBUSI JAWA BARAT"), tidak layak
    jadi label sel treemap.
    """
    return query(
        """
        SELECT coalesce(u.nama_pendek, p.unit_induk) AS unit_induk,
               p.bidang_pembidangan, count(*) AS n
        FROM penempatan p
        LEFT JOIN unit_induk u ON u.unit_induk = p.unit_induk
        WHERE p.unit_induk IS NOT NULL
        GROUP BY 1, 2
        ORDER BY 3 DESC
        """
    )


def grade_masuk() -> pd.DataFrame:
    """M25 — grade masuk hasil penempatan (validasi aturan grade sesuai jenjang)."""
    return query(
        """
        SELECT kode_grade, count(*) AS n
        FROM penempatan
        GROUP BY 1
        ORDER BY 2 DESC
        """
    )


def rencana_vs_realisasi() -> pd.DataFrame:
    """M26 — kuota profesi vs penempatan nyata per tahun.

    Tiga tahun RBB (2020, 2021, 2024) ditandai: kuotanya kohort penuh sementara yang
    tercatat di PLN hanya hasil serah-terima FHCI. Membacanya sebagai "gagal memenuhi
    target" itu keliru — kolom `jalur` disediakan supaya UI bisa memberi penanda.
    """
    return query(
        """
        SELECT k.tahun_program AS tahun,
               k.kuota,
               coalesce(r.realisasi, 0) AS realisasi,
               round(100.0 * coalesce(r.realisasi, 0) / k.kuota, 1) AS pct,
               j.jalur
        FROM (SELECT tahun_program, sum(kuota) AS kuota FROM profesi GROUP BY 1) k
        LEFT JOIN (
            SELECT tahun_program, count(*) AS realisasi FROM penempatan GROUP BY 1
        ) r USING (tahun_program)
        LEFT JOIN (
            SELECT tahun_program, max(sumber_rekrutmen) AS jalur
            FROM gelombang GROUP BY 1
        ) j USING (tahun_program)
        ORDER BY 1
        """
    )


# ──────────────────────────────────────────────────────────────────────────────
# G. Kualitas data & sumber sistem (halaman 7)
# ──────────────────────────────────────────────────────────────────────────────


def volume_per_sistem() -> pd.DataFrame:
    """M27/M39 — volume baris seleksi_tahap per sistem sumber."""
    return query(
        """
        SELECT sistem_sumber, count(*) AS n
        FROM seleksi_tahap
        GROUP BY 1
        ORDER BY 2 DESC
        """
    )


def kelengkapan_per_kohort() -> pd.DataFrame:
    """M28 — kelengkapan kolom (blok fisik, domisili) per kualitas kohort."""
    return query(
        """
        SELECT kualitas_kohort, count(*) AS n,
               round(100.0 * count(body_height) / count(*), 1) AS pct_blok_fisik,
               round(100.0 * count(kota_domisili) / count(*), 1) AS pct_domisili
        FROM kandidat
        GROUP BY 1
        ORDER BY 1
        """
    )


def selisih_angka_rencana() -> pd.DataFrame:
    """M30 — selisih target gelombang vs pagu disetujui per tahun. DIMODELKAN."""
    return query(
        """
        SELECT g.tahun_program AS tahun, sum(g.diterima_target) AS target_gelombang, p.pagu,
               sum(g.diterima_target) - p.pagu AS selisih
        FROM gelombang g
        LEFT JOIN (SELECT tahun_program, sum(jumlah) AS pagu FROM pagu_rekrutmen GROUP BY 1) p
            USING (tahun_program)
        GROUP BY 1, p.pagu
        ORDER BY 1
        """
    )
