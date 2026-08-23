"""Kamus metrik — SATU definisi angka untuk seluruh aplikasi.

Aturan arsitektur: **halaman tidak menulis SQL.** Semua angka yang tampil di
dashboard, dan yang dirujuk chatbot, berasal dari modul ini — supaya angka di
halaman 1, halaman 5, dan jawaban chatbot tidak pernah berbeda.

Bentuk modul: datar, satu fungsi per metrik. Tanpa registry, tanpa dekorator,
**tanpa cache sendiri** — `core.db.query` dan `core.db.skalar` sudah
`@st.cache_data(ttl=3600)`.

Dua aturan yang mengikat seluruh berkas ini:

1. **Semua status dihitung dari perbandingan tanggal terhadap `acuan`**, tidak
   pernah dibaca dari kolom `pasca_tahap.status`. Kolom itu snapshot beku saat
   data digenerate; dibaca mentah ia menyatakan "2.000 sedang OJT" selamanya,
   termasuk di 2027.
2. Tiap fungsi menerima `acuan: date | None = None` dan jatuh ke
   `db.hari_ini()` kalau tidak diisi. Tanggal selalu masuk SQL sebagai
   **parameter**, tidak pernah dirangkai ke dalam string SQL.

Angka 0 dikembalikan apa adanya sebagai fakta. Agregat atas kolom bertanggal
tidak pernah dipakai sebagai pengganti hari ini.

Alasan "kenapa angkanya begini" ada di `docs/CATATAN_DATA.md`, keluaran nyata
tiap fungsi ada di `docs/metrik.md` — tidak pernah di UI.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from core import db

# ──────────────────────────────────────────────────────────────────────────────
# Helper bersama
# ──────────────────────────────────────────────────────────────────────────────

# Urutan tahap diambil dari `tahap_ref.urutan` (seleksi 1-6, pasca 100-106),
# BUKAN dari `pasca_tahap.urutan` yang bernilai 7-13 sehingga bertabrakan
# dengan urutan tahap seleksi. Join selalu lewat `tahap_kode`.
# Tahap semu untuk pelamar yang sudah mendaftar tapi belum menjalani tahap apa
# pun; tidak ada di `tahap_ref`.
_URUTAN_PENDAFTARAN = 0

# Aliran peristiwa bertanggal, disatukan dari lima sumber supaya "tenggat
# terdekat" dan "aktivitas terakhir/berikutnya" membaca definisi yang sama
# persis. Satu baris = satu peristiwa kolektif (gelombang x tahap x tanggal).
# Satu tanda tanya di dalamnya: parameter acuan, untuk menghitung pelamar yang
# sudah masuk sampai acuan pada peristiwa penutupan gelombang.
_PERISTIWA_SQL = """
    SELECT 'Selesai tahap pasca-seleksi' AS jenis,
           pt.gelombang_id               AS gelombang,
           r.nama                        AS tahap,
           pt.tanggal_selesai            AS tanggal,
           count(*)                      AS jumlah
    FROM pasca_tahap pt
    JOIN tahap_ref r USING (tahap_kode)
    GROUP BY 1, 2, 3, 4

    UNION ALL

    -- Hanya tahap pasca yang punya rentang. Enam dari tujuh tahap pasca adalah
    -- peristiwa titik (tanggal_mulai = tanggal_selesai); tanpa saringan ini
    -- semuanya tampil dua kali.
    SELECT 'Mulai tahap pasca-seleksi' AS jenis,
           pt.gelombang_id             AS gelombang,
           r.nama                      AS tahap,
           pt.tanggal_mulai            AS tanggal,
           count(*)                    AS jumlah
    FROM pasca_tahap pt
    JOIN tahap_ref r USING (tahap_kode)
    WHERE pt.tanggal_mulai <> pt.tanggal_selesai
    GROUP BY 1, 2, 3, 4

    UNION ALL

    SELECT 'Tahap seleksi'  AS jenis,
           st.gelombang_id  AS gelombang,
           r.nama           AS tahap,
           st.tanggal_tahap AS tanggal,
           count(*)         AS jumlah
    FROM seleksi_tahap st
    JOIN tahap_ref r USING (tahap_kode)
    GROUP BY 1, 2, 3, 4

    UNION ALL

    SELECT 'Gelombang dibuka'   AS jenis,
           g.gelombang_id       AS gelombang,
           'Pendaftaran dibuka' AS tahap,
           g.tgl_buka           AS tanggal,
           0                    AS jumlah
    FROM gelombang g

    UNION ALL

    SELECT 'Gelombang ditutup'   AS jenis,
           g.gelombang_id        AS gelombang,
           'Pendaftaran ditutup' AS tahap,
           g.tgl_tutup           AS tanggal,
           (SELECT count(*) FROM pendaftaran p
             WHERE p.gelombang_id = g.gelombang_id
               AND p.tanggal_lamar <= ?) AS jumlah
    FROM gelombang g
"""


def _acuan(acuan: date | None) -> date:
    """Jangkar waktu satu pemanggilan metrik: tanggal yang diminta, atau hari ini."""
    return acuan or db.hari_ini()


# ──────────────────────────────────────────────────────────────────────────────
# A. Beranda (halaman 1)
# ──────────────────────────────────────────────────────────────────────────────


def keadaan_sekarang(acuan: date | None = None) -> dict[str, object]:
    """Empat angka keadaan proses rekrutmen pada tanggal acuan.

    `gelombang_dibuka` — gelombang yang pendaftarannya sedang terbuka.
    `sedang_diseleksi` — pelamar yang tahapan seleksinya sudah dimulai dan
    hasil akhirnya belum diumumkan.
    `sedang_ojt` — peserta yang sedang menjalani diklat prajabatan.
    `menunggu_sk` — peserta yang sudah selesai diklat prajabatan tapi SK
    pengangkatannya belum terbit.
    """
    acuan = _acuan(acuan)
    return {
        "acuan": acuan,
        "gelombang_dibuka": db.skalar(
            """
            SELECT count(*) FROM gelombang
            WHERE tgl_buka <= ? AND tgl_tutup >= ?
            """,
            [acuan, acuan],
        ),
        # "Sedang diseleksi" = sudah menjalani minimal satu tahap sampai acuan,
        # belum pernah gugur sampai acuan, dan pengumuman akhirnya belum keluar
        # sampai acuan. Dipilih daripada definisi "tahap pertamanya sudah lewat
        # tapi tahap terakhirnya belum", karena pelamar yang sudah tuntas
        # wawancara tapi masih menunggu pengumuman tetap sedang diseleksi --
        # lihat docs/metrik.md.
        "sedang_diseleksi": db.skalar(
            """
            SELECT count(*) FROM pendaftaran p
            WHERE EXISTS (SELECT 1 FROM seleksi_tahap t
                          WHERE t.pendaftaran_id = p.pendaftaran_id
                            AND t.tanggal_tahap <= ?)
              AND NOT EXISTS (SELECT 1 FROM seleksi_tahap t
                              WHERE t.pendaftaran_id = p.pendaftaran_id
                                AND t.hasil = 'GAGAL'
                                AND t.tanggal_tahap <= ?)
              AND NOT EXISTS (SELECT 1 FROM pasca_tahap x
                              WHERE x.pendaftaran_id = p.pendaftaran_id
                                AND x.tahap_kode = 'pengumuman_akhir'
                                AND x.tanggal_mulai <= ?)
            """,
            [acuan, acuan, acuan],
        ),
        "sedang_ojt": db.skalar(
            """
            SELECT count(*) FROM pasca_tahap
            WHERE tahap_kode = 'ojt'
              AND tanggal_mulai <= ? AND tanggal_selesai > ?
            """,
            [acuan, acuan],
        ),
        "menunggu_sk": db.skalar(
            """
            SELECT count(*) FROM pasca_tahap o
            WHERE o.tahap_kode = 'ojt' AND o.tanggal_selesai <= ?
              AND NOT EXISTS (SELECT 1 FROM pasca_tahap s
                              WHERE s.pendaftaran_id = o.pendaftaran_id
                                AND s.tahap_kode = 'sk_penempatan'
                                AND s.tanggal_selesai <= ?)
            """,
            [acuan, acuan],
        ),
    }


def tenggat_terdekat(hari: int = 30, acuan: date | None = None) -> pd.DataFrame:
    """Peristiwa rekrutmen yang jatuh tempo dalam `hari` ke depan dari acuan.

    Kolom: jenis, gelombang, tahap, tanggal, hari_tersisa, jumlah. Diurutkan
    dari yang paling dekat; hari_tersisa dihitung terhadap acuan.
    """
    acuan = _acuan(acuan)
    return db.query(
        f"""
        WITH peristiwa AS ({_PERISTIWA_SQL})
        SELECT jenis,
               gelombang,
               tahap,
               tanggal,
               date_diff('day', CAST(? AS DATE), tanggal) AS hari_tersisa,
               jumlah
        FROM peristiwa
        WHERE tanggal >= CAST(? AS DATE)
          AND tanggal <= CAST(? AS DATE) + CAST(? AS INTEGER)
        ORDER BY tanggal, jenis, gelombang
        """,
        [acuan, acuan, acuan, acuan, hari],
    )


def denyut_pipeline(acuan: date | None = None) -> pd.DataFrame:
    """Jumlah pelamar yang masih berproses di tiap tahap pada tanggal acuan.

    Kolom: urutan, tahap_kode, nama, jumlah, sedang_berjalan, sudah_tuntas.
    Tiap pelamar yang masih berproses menempati tepat satu tahap — tahap
    terjauh yang sudah dimulai sampai acuan; `sedang_berjalan` dan
    `sudah_tuntas` memilah apakah tahap itu masih berlangsung pada acuan.
    Pelamar yang sudah gugur tidak lagi terhitung.
    """
    acuan = _acuan(acuan)
    return db.query(
        """
        WITH gugur AS (
            SELECT pendaftaran_id, min(tanggal_tahap) AS tgl_gugur
            FROM seleksi_tahap
            WHERE hasil = 'GAGAL'
            GROUP BY 1
        ),
        seleksi_dimulai AS (
            SELECT pendaftaran_id, max(urutan) AS urutan
            FROM seleksi_tahap
            WHERE tanggal_tahap <= ?
            GROUP BY 1
        ),
        pasca_dimulai AS (
            SELECT pt.pendaftaran_id, max(r.urutan) AS urutan
            FROM pasca_tahap pt
            JOIN tahap_ref r USING (tahap_kode)
            WHERE pt.tanggal_mulai <= ?
            GROUP BY 1
        ),
        posisi AS (
            SELECT p.pendaftaran_id,
                   coalesce(pd.urutan, sd.urutan, ?) AS urutan
            FROM pendaftaran p
            LEFT JOIN gugur g USING (pendaftaran_id)
            LEFT JOIN seleksi_dimulai sd USING (pendaftaran_id)
            LEFT JOIN pasca_dimulai pd USING (pendaftaran_id)
            WHERE p.tanggal_lamar <= ?
              AND (g.tgl_gugur IS NULL OR g.tgl_gugur > ?)
        ),
        -- Tahap seleksi adalah peristiwa satu hari: begitu tanggalnya lewat,
        -- tahapnya tuntas dan pelamar menunggu tahap berikutnya. Tahap pasca
        -- punya rentang, jadi ketuntasannya dibandingkan ke tanggal_selesai.
        posisi_status AS (
            SELECT po.urutan,
                   CASE
                       WHEN r.kategori = 'pasca'
                           THEN CASE WHEN pt.tanggal_selesai <= ? THEN 1 ELSE 0 END
                       WHEN r.kategori = 'seleksi' THEN 1
                       ELSE 0
                   END AS tuntas
            FROM posisi po
            LEFT JOIN tahap_ref r ON r.urutan = po.urutan
            LEFT JOIN pasca_tahap pt
                   ON pt.pendaftaran_id = po.pendaftaran_id
                  AND pt.tahap_kode = r.tahap_kode
        ),
        tahap AS (
            SELECT ? AS urutan, 'pendaftaran' AS tahap_kode, 'Pendaftaran' AS nama
            UNION ALL
            SELECT urutan, tahap_kode, nama
            FROM tahap_ref
            WHERE kategori IN ('seleksi', 'pasca')
        )
        SELECT t.urutan,
               t.tahap_kode,
               t.nama,
               count(ps.urutan) AS jumlah,
               CAST(coalesce(sum(CASE WHEN ps.tuntas = 0 THEN 1 ELSE 0 END), 0)
                    AS BIGINT) AS sedang_berjalan,
               CAST(coalesce(sum(ps.tuntas), 0) AS BIGINT) AS sudah_tuntas
        FROM tahap t
        LEFT JOIN posisi_status ps ON ps.urutan = t.urutan
        GROUP BY 1, 2, 3
        ORDER BY 1
        """,
        [acuan, acuan, _URUTAN_PENDAFTARAN, acuan, acuan, acuan, _URUTAN_PENDAFTARAN],
    )


def aktivitas_sekitar(acuan: date | None = None) -> pd.DataFrame:
    """Peristiwa terakhir sebelum acuan dan peristiwa terjadwal sesudah acuan.

    Kolom: arah (terakhir / berikutnya), jenis, gelombang, tahap, tanggal,
    selisih_hari, jumlah. Sisi yang memang tidak punya peristiwa tidak
    menghasilkan baris.
    """
    acuan = _acuan(acuan)
    return db.query(
        f"""
        WITH peristiwa AS ({_PERISTIWA_SQL}),
        terakhir AS (
            SELECT 'terakhir' AS arah, jenis, gelombang, tahap, tanggal, jumlah
            FROM peristiwa
            WHERE tanggal < CAST(? AS DATE)
            ORDER BY tanggal DESC, jumlah DESC
            LIMIT 1
        ),
        berikutnya AS (
            SELECT 'berikutnya' AS arah, jenis, gelombang, tahap, tanggal, jumlah
            FROM peristiwa
            WHERE tanggal > CAST(? AS DATE)
            ORDER BY tanggal ASC, jumlah DESC
            LIMIT 1
        ),
        gabung AS (
            SELECT arah, jenis, gelombang, tahap, tanggal, jumlah FROM terakhir
            UNION ALL
            SELECT arah, jenis, gelombang, tahap, tanggal, jumlah FROM berikutnya
        )
        SELECT arah, jenis, gelombang, tahap, tanggal,
               date_diff('day', CAST(? AS DATE), tanggal) AS selisih_hari,
               jumlah
        FROM gabung
        ORDER BY tanggal
        """,
        [acuan, acuan, acuan, acuan],
    )


# ──────────────────────────────────────────────────────────────────────────────
# B. Perencanaan Formasi (halaman 2)
# ──────────────────────────────────────────────────────────────────────────────
#
# Rantai perencanaan yang ada di data: proyeksi_kekosongan (per unit x posisi,
# 2019-2026) -> usulan_kebutuhan (kekosongan + gap FTK, 2019-2025) ->
# pagu_rekrutmen (2019-2025). `proyeksi_kekosongan` berhenti di 2026 -- lihat
# `rentang_tahun_proyeksi()`, yang dipakai halaman untuk mendeteksi batas ini
# dan menampilkannya sebagai keadaan data, bukan galat.

# Anomali `unit_induk` sudah terverifikasi (CATATAN_DATA.md J4): baris duplikat
# "UID Jawa Tengah & DIY" berjumlah_pegawai=4 tersingkir dengan filter ini,
# tanpa perlu tahu penyebabnya lebih dulu.
_MINIMAL_PEGAWAI_UNIT = 50


def rentang_tahun_proyeksi() -> tuple[int, int]:
    """Tahun minimum & maksimum yang tersedia di `proyeksi_kekosongan`.

    Batas horison data proyeksi -- dipakai halaman untuk menawarkan tahun
    historis terakhir begitu `hari_ini()` melewati tahun maksimum ini.
    """
    df = db.query("SELECT min(tahun) AS mn, max(tahun) AS mx FROM proyeksi_kekosongan")
    baris = df.iloc[0]
    return int(baris["mn"]), int(baris["mx"])


def kekosongan_per_sebab(acuan: date | None = None) -> pd.DataFrame:
    """Proyeksi kekosongan per sebab, untuk tahun berjalan & tahun berikutnya.

    `sebab` satu dari: pensiun, mengundurkan diri, meninggal dunia, PHK.
    Tahun diturunkan dari `acuan` (tahun(acuan) dan tahun(acuan)+1) -- bukan
    di-hardcode. Kalau kedua tahun berada di luar rentang data (lihat
    `rentang_tahun_proyeksi()`), hasilnya kosong -- itu jawaban yang benar,
    bukan galat.
    """
    acuan = _acuan(acuan)
    return db.query(
        """
        SELECT tahun,
               round(sum(pensiun)) AS pensiun,
               round(sum(mengundurkan_diri)) AS mengundurkan_diri,
               round(sum(meninggal_dunia)) AS meninggal_dunia,
               round(sum(phk)) AS phk,
               round(sum(kekosongan)) AS total
        FROM proyeksi_kekosongan
        WHERE tahun IN (?, ?)
        GROUP BY 1
        ORDER BY 1
        """,
        [acuan.year, acuan.year + 1],
    )


def kekosongan_per_unit(tahun: int, minimal_pegawai: int = _MINIMAL_PEGAWAI_UNIT) -> pd.DataFrame:
    """Proyeksi kekosongan per unit induk (48 unit) pada satu tahun.

    Kolom: unit_induk, nama_pendek, jenis_unit, kekosongan. Diurutkan dari yang
    paling terancam. Kosong kalau `tahun` di luar rentang `proyeksi_kekosongan`.
    """
    return db.query(
        """
        SELECT pk.unit_induk, u.nama_pendek, u.jenis_unit,
               round(sum(pk.kekosongan)) AS kekosongan
        FROM proyeksi_kekosongan pk
        JOIN unit_induk u ON u.unit_induk = pk.unit_induk
        WHERE pk.tahun = ? AND u.jumlah_pegawai > ?
        GROUP BY 1, 2, 3
        ORDER BY 4 DESC
        """,
        [tahun, minimal_pegawai],
    )


def daftar_unit_induk(minimal_pegawai: int = _MINIMAL_PEGAWAI_UNIT) -> pd.DataFrame:
    """Daftar unit induk untuk filter halaman -- kode & nama pendek, disaring
    anomali J4.

    Kolom kembalian sengaja diberi alias `kode_unit` (bukan nama kolom asli
    `unit_induk`) supaya halaman yang memanggilnya tidak perlu menyebut nama
    tabel/kolom sumber sebagai literal string.
    """
    return db.query(
        """
        SELECT unit_induk AS kode_unit, nama_pendek
        FROM unit_induk
        WHERE jumlah_pegawai > ?
        ORDER BY nama_pendek
        """,
        [minimal_pegawai],
    )


def kekosongan_per_posisi(unit_induk: str, tahun: int) -> pd.DataFrame:
    """Proyeksi kekosongan per posisi & sub-bidang, untuk satu unit pada satu
    tahun.

    Kolom: nama_posisi, sub_bidang, jenjang, kekosongan. Baris dengan
    kekosongan 0 disaring supaya daftar tetap fokus pada yang benar-benar
    terancam -- unit apa pun bisa punya ratusan kombinasi posisi x jenjang.
    """
    return db.query(
        """
        SELECT nama_posisi, sub_bidang, jenjang, round(sum(kekosongan)) AS kekosongan
        FROM proyeksi_kekosongan
        WHERE unit_induk = ? AND tahun = ?
        GROUP BY 1, 2, 3
        HAVING round(sum(kekosongan)) > 0
        ORDER BY 4 DESC
        """,
        [unit_induk, tahun],
    )


def gap_ftk_nasional(minimal_pegawai: int = _MINIMAL_PEGAWAI_UNIT) -> dict[str, float]:
    """Gap FTK nasional -- formasi (`ftk_2025`) vs realisasi.

    WAJIB `realisasi_mar_2026`: kolom `realisasi_apr_2026` hanya terisi di 1
    dari 48 unit dan menghasilkan gap palsu 33.934 (CATATAN_DATA.md J8).

    Memakai filter anomali J4 yang sama dengan `gap_ftk_per_unit()` supaya
    kartu nasional dan tabel per-unit di halaman selalu bisa dijumlahkan
    saling cocok -- hasilnya **561**, bukan 701 (701 adalah seluruh 48 baris
    apa adanya, termasuk baris duplikat J4; lihat CATATAN_DATA.md J8).
    """
    df = db.query(
        """
        SELECT sum(ftk_2025) AS ftk,
               sum(realisasi_mar_2026) AS realisasi,
               sum(ftk_2025) - sum(realisasi_mar_2026) AS gap
        FROM unit_induk
        WHERE jumlah_pegawai > ?
        """,
        [minimal_pegawai],
    )
    return df.iloc[0].to_dict()


def gap_ftk_per_unit(minimal_pegawai: int = _MINIMAL_PEGAWAI_UNIT) -> pd.DataFrame:
    """Gap FTK per unit induk -- formasi (`ftk_2025`) vs realisasi
    (`realisasi_mar_2026`)."""
    return db.query(
        """
        SELECT nama_pendek, jenis_unit, ftk_2025, realisasi_mar_2026,
               ftk_2025 - realisasi_mar_2026 AS gap
        FROM unit_induk
        WHERE jumlah_pegawai > ?
        ORDER BY gap DESC
        """,
        [minimal_pegawai],
    )


def usulan_vs_pagu() -> pd.DataFrame:
    """Usulan unit vs pagu yang disetujui pusat, per tahun program (2019-2025).

    Kolom: tahun, pagu, usulan, pct_disetujui.
    """
    return db.query(
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


# ──────────────────────────────────────────────────────────────────────────────
# C. Seleksi Berjalan (halaman 3)
# ──────────────────────────────────────────────────────────────────────────────
#
# Berbeda dari denyut_pipeline() (Beranda), yang melintasi seluruh gelombang.
# Metrik di sini selalu dipersempit ke satu `gelombang_id` -- pertanyaannya
# "gelombang yang sedang jalan sudah sampai mana?", bukan potret nasional.
# Kategori tahap di `seleksi_tahap` sudah terbatas pada kategori='seleksi'
# (enam tahap, urutan 1-6) -- baris fhci_agregat dan pasca tidak pernah masuk
# tabel ini, jadi tidak perlu filter kategori tambahan di sini.


def gelombang_terbuka(acuan: date | None = None) -> pd.DataFrame:
    """Gelombang yang pendaftarannya sedang terbuka pada tanggal acuan.

    Kolom: gelombang_id, nama_gelombang, tgl_buka, tgl_tutup, hari_tersisa,
    n_profesi, diterima_target. `hari_tersisa` dihitung terhadap acuan, bukan
    disimpan sebagai kolom beku.
    """
    acuan = _acuan(acuan)
    return db.query(
        """
        SELECT gelombang_id, nama_gelombang, tgl_buka, tgl_tutup,
               date_diff('day', CAST(? AS DATE), tgl_tutup) AS hari_tersisa,
               n_profesi, diterima_target
        FROM gelombang
        WHERE tgl_buka <= ? AND tgl_tutup >= ?
        ORDER BY tgl_tutup
        """,
        [acuan, acuan, acuan],
    )


def profesi_gelombang(gelombang_id: str) -> pd.DataFrame:
    """Profesi yang dibuka pada satu gelombang.

    Kolom: nama_profesi, jenjang, kota_rekrutmen, kuota.
    """
    return db.query(
        """
        SELECT nama_profesi, jenjang, kota_rekrutmen, kuota
        FROM profesi
        WHERE gelombang_id = ?
        ORDER BY nama_profesi
        """,
        [gelombang_id],
    )


def posisi_tahap_seleksi(gelombang_id: str, acuan: date | None = None) -> pd.DataFrame:
    """Posisi peserta per tahap seleksi pada satu gelombang, pada tanggal acuan.

    Kolom: urutan, tahap_kode, nama, jumlah, menunggu, sudah_lewat.
    `menunggu` -- tahap terjadwal sesudah acuan, hasilnya belum keluar.
    `sudah_lewat` -- tahap yang tanggalnya sudah lewat acuan.
    """
    acuan = _acuan(acuan)
    return db.query(
        """
        SELECT r.urutan, st.tahap_kode, r.nama,
               count(*) AS jumlah,
               CAST(sum(CASE WHEN st.tanggal_tahap > ? THEN 1 ELSE 0 END) AS BIGINT) AS menunggu,
               CAST(sum(CASE WHEN st.tanggal_tahap <= ? THEN 1 ELSE 0 END) AS BIGINT) AS sudah_lewat
        FROM seleksi_tahap st
        JOIN tahap_ref r USING (tahap_kode)
        WHERE st.gelombang_id = ?
        GROUP BY 1, 2, 3
        ORDER BY 1
        """,
        [acuan, acuan, gelombang_id],
    )


def jadwal_tahap_berikutnya(gelombang_id: str, acuan: date | None = None) -> pd.DataFrame:
    """Jadwal tahap seleksi terdekat sesudah acuan, untuk satu gelombang.

    Kolom: tahap_kode, nama_tahap, tanggal_tahap, lokasi_kota, vendor, jumlah.
    Satu baris per kombinasi kota/vendor pada tanggal terdekat itu -- satu
    tahap bisa dijalankan serentak di beberapa kota dengan vendor berbeda.
    Kosong kalau tidak ada lagi tahap terjadwal sesudah acuan.
    """
    acuan = _acuan(acuan)
    return db.query(
        """
        WITH tanggal_terdekat AS (
            SELECT min(tanggal_tahap) AS tgl
            FROM seleksi_tahap
            WHERE gelombang_id = ? AND tanggal_tahap > ?
        )
        SELECT st.tahap_kode, r.nama AS nama_tahap, st.tanggal_tahap,
               st.lokasi_kota, v.nama AS vendor, count(*) AS jumlah
        FROM seleksi_tahap st
        JOIN tahap_ref r USING (tahap_kode)
        LEFT JOIN vendor v USING (vendor_id)
        CROSS JOIN tanggal_terdekat td
        WHERE st.gelombang_id = ? AND st.tanggal_tahap = td.tgl
        GROUP BY 1, 2, 3, 4, 5
        ORDER BY st.lokasi_kota NULLS FIRST
        """,
        [gelombang_id, acuan, gelombang_id],
    )


def kehadiran_tahap_terakhir(gelombang_id: str, acuan: date | None = None) -> dict[str, object] | None:
    """Kehadiran pada tahap seleksi terakhir yang sudah lewat, untuk satu
    gelombang, pada tanggal acuan.

    Kolom kembalian: tahap_kode, nama, tanggal_tahap, hadir, tidak_hadir,
    total. Hanya menghitung tahap yang memang punya konsep kehadiran
    (`tahap_ref.ada_kehadiran`) -- Seleksi Administrasi berbasis dokumen,
    tidak ada sesi hadir/tidak hadir. `None` kalau belum ada satu pun tahap
    berkehadiran yang lewat pada gelombang ini sampai acuan.
    """
    acuan = _acuan(acuan)
    df = db.query(
        """
        WITH terakhir AS (
            SELECT max(st.tanggal_tahap) AS tgl
            FROM seleksi_tahap st
            JOIN tahap_ref r USING (tahap_kode)
            WHERE st.gelombang_id = ? AND r.ada_kehadiran AND st.tanggal_tahap <= ?
        )
        SELECT st.tahap_kode, r.nama, t.tgl AS tanggal_tahap,
               CAST(sum(CASE WHEN st.status_hadir = 'HADIR' THEN 1 ELSE 0 END) AS BIGINT) AS hadir,
               CAST(sum(CASE WHEN st.status_hadir = 'TIDAK_HADIR' THEN 1 ELSE 0 END) AS BIGINT) AS tidak_hadir,
               count(*) AS total
        FROM seleksi_tahap st
        JOIN tahap_ref r USING (tahap_kode)
        JOIN terakhir t ON st.tanggal_tahap = t.tgl
        WHERE st.gelombang_id = ?
        GROUP BY 1, 2, 3
        """,
        [gelombang_id, acuan, gelombang_id],
    )
    if df.empty:
        return None
    return df.iloc[0].to_dict()


def gelombang_terakhir_selesai(acuan: date | None = None) -> dict[str, object] | None:
    """Gelombang paling baru yang pendaftarannya sudah tutup sebelum acuan.

    Kolom kembalian: gelombang_id, nama_gelombang, tgl_tutup, pendaftar,
    diterima, gagal. Dipakai untuk keadaan kosong Halaman 3 -- kalau tidak
    ada gelombang yang sedang terbuka, halaman tetap menunjukkan hasil akhir
    gelombang terakhir yang sudah selesai. `hasil_akhir` di `pendaftaran`
    adalah keputusan final per pelamar, bukan status berjalan yang beku --
    aman dibaca apa adanya (beda dengan `pasca_tahap.status`, lihat §4.1
    ATURAN_TAMPILAN.md). `None` kalau tidak ada gelombang yang sudah tutup
    sebelum acuan.
    """
    acuan = _acuan(acuan)
    gelombang = db.query(
        """
        SELECT gelombang_id, nama_gelombang, tgl_tutup
        FROM gelombang
        WHERE tgl_tutup < ?
        ORDER BY tgl_tutup DESC
        LIMIT 1
        """,
        [acuan],
    )
    if gelombang.empty:
        return None
    baris = gelombang.iloc[0]
    hasil = db.query(
        """
        SELECT count(*) AS pendaftar,
               CAST(sum(CASE WHEN hasil_akhir = 'DITERIMA' THEN 1 ELSE 0 END) AS BIGINT) AS diterima,
               CAST(sum(CASE WHEN hasil_akhir = 'GAGAL' THEN 1 ELSE 0 END) AS BIGINT) AS gagal
        FROM pendaftaran
        WHERE gelombang_id = ?
        """,
        [baris["gelombang_id"]],
    ).iloc[0]
    return {
        "gelombang_id": baris["gelombang_id"],
        "nama_gelombang": baris["nama_gelombang"],
        "tgl_tutup": baris["tgl_tutup"],
        "pendaftar": int(hasil["pendaftar"]),
        "diterima": int(hasil["diterima"]),
        "gagal": int(hasil["gagal"]),
    }


def gugur_per_tahap_gelombang(gelombang_id: str) -> pd.DataFrame:
    """Sebaran pelamar gugur per tahap, untuk satu gelombang yang sudah
    selesai diproses.

    Kolom: urutan, tahap_kode, nama, jumlah. Hanya pelamar dengan
    `hasil_akhir = 'GAGAL'` -- keputusan final, bukan snapshot berjalan.
    """
    return db.query(
        """
        SELECT r.urutan, p.tahap_gugur AS tahap_kode, r.nama,
               count(*) AS jumlah
        FROM pendaftaran p
        JOIN tahap_ref r ON r.tahap_kode = p.tahap_gugur
        WHERE p.gelombang_id = ? AND p.hasil_akhir = 'GAGAL'
        GROUP BY 1, 2, 3
        ORDER BY 1
        """,
        [gelombang_id],
    )


# ──────────────────────────────────────────────────────────────────────────────
# D. Corong Seleksi (halaman 4)
# ──────────────────────────────────────────────────────────────────────────────
#
# Analisis lintas gelombang -- beda dari posisi_tahap_seleksi() (halaman 3),
# yang membaca posisi peserta pada SATU gelombang yang sedang berjalan. Di sini
# pertanyaannya "di tahap mana orang hilang, dan kenapa?" atas riwayat yang
# sudah tuntas, jadi tidak terikat ke hari_ini() -- lihat
# docs/RANCANGAN_HALAMAN.md §6. Enam tahap seleksi mandiri (`kategori =
# 'seleksi'`), terpisah dari tiga tahap agregat FHCI (`kategori =
# 'fhci_agregat'`, hanya ada di `seleksi_tahap_agregat` -- CATATAN_DATA.md J7,
# jangan pernah JOIN tabel itu ke `pendaftaran`).


def corong_tahap_seleksi(gelombang_id: str | None = None) -> pd.DataFrame:
    """Corong enam tahap seleksi mandiri, seluruh gelombang atau satu gelombang.

    Kolom: urutan, tahap_kode, nama, masuk, hadir, tidak_hadir, lulus, gagal.
    `hadir`/`tidak_hadir` bernilai 0 untuk Seleksi Administrasi -- tahap itu
    berbasis dokumen, tidak ada sesi kehadiran (`tahap_ref.ada_kehadiran =
    False`). `gagal` adalah `masuk - lulus`, sudah mencakup yang tidak hadir.
    """
    return db.query(
        """
        SELECT r.urutan, r.tahap_kode, r.nama,
               count(*) AS masuk,
               CAST(sum(CASE WHEN t.status_hadir = 'HADIR' THEN 1 ELSE 0 END) AS BIGINT) AS hadir,
               CAST(sum(CASE WHEN t.status_hadir = 'TIDAK_HADIR' THEN 1 ELSE 0 END) AS BIGINT) AS tidak_hadir,
               CAST(sum(CASE WHEN t.hasil = 'LULUS' THEN 1 ELSE 0 END) AS BIGINT) AS lulus,
               CAST(count(*) - sum(CASE WHEN t.hasil = 'LULUS' THEN 1 ELSE 0 END) AS BIGINT) AS gagal
        FROM seleksi_tahap t
        JOIN tahap_ref r USING (tahap_kode)
        WHERE r.kategori = 'seleksi'
          AND (CAST(? AS VARCHAR) IS NULL OR t.gelombang_id = ?)
        GROUP BY 1, 2, 3
        ORDER BY 1
        """,
        [gelombang_id, gelombang_id],
    )


def no_show_per_tahap_mode() -> pd.DataFrame:
    """Persentase tidak hadir per tahap seleksi x mode pelaksanaan, seluruh
    gelombang.

    Kolom: urutan, tahap_kode, nama, mode, tidak_hadir, total, pct_no_show.
    Seleksi Administrasi tidak muncul -- tidak punya konsep kehadiran.
    """
    return db.query(
        """
        SELECT r.urutan, t.tahap_kode, r.nama, t.mode,
               CAST(sum(CASE WHEN t.status_hadir = 'TIDAK_HADIR' THEN 1 ELSE 0 END) AS BIGINT) AS tidak_hadir,
               CAST(count(t.status_hadir) AS BIGINT) AS total,
               round(
                   100.0 * sum(CASE WHEN t.status_hadir = 'TIDAK_HADIR' THEN 1 ELSE 0 END)
                   / nullif(count(t.status_hadir), 0), 1
               ) AS pct_no_show
        FROM seleksi_tahap t
        JOIN tahap_ref r USING (tahap_kode)
        WHERE r.kategori = 'seleksi' AND t.status_hadir IS NOT NULL
        GROUP BY 1, 2, 3, 4
        ORDER BY 1
        """
    )


def rbb_masuk_akademik_inggris(gelombang_id: str | None = None) -> int:
    """Jumlah pelamar yang masuk sistem PLN langsung di tahap Akademik &
    Inggris -- titik serah-terima dari jalur RBB (FHCI).

    `pendaftaran.titik_masuk = 'akademik_inggris'` menandai pelamar yang tidak
    pernah melalui Seleksi Administrasi maupun Tes Adaptif PLN sendiri; mereka
    sudah disaring FHCI sebelum diserahkan (CATATAN_DATA.md §7). Tanpa filter,
    selisih ini persis sama dengan selisih `masuk` tahap Akademik & Inggris
    dikurangi `lulus` Tes Adaptif pada `corong_tahap_seleksi()`. Hanya empat
    gelombang RBB (G2020-074, G2021-075, G2024-087, G2024-088) yang punya
    pelamar dengan titik masuk ini -- gelombang mandiri lain akan mengembalikan
    0, itu jawaban yang benar.
    """
    return db.skalar(
        """
        SELECT count(*) FROM pendaftaran
        WHERE titik_masuk = 'akademik_inggris'
          AND (CAST(? AS VARCHAR) IS NULL OR gelombang_id = ?)
        """,
        [gelombang_id, gelombang_id],
    )


def corong_fhci() -> pd.DataFrame:
    """Corong agregat tiga tahap FHCI, dijumlah lintas tahun program.

    Kolom: urutan, tahap_kode, nama, masuk, lulus, pct_lulus. Sumber
    `seleksi_tahap_agregat` tidak punya `kandidat_id`/`pendaftaran_id` --
    fakta struktural jalur ini (CATATAN_DATA.md J7), bukan JOIN ke
    `pendaftaran`.
    """
    return db.query(
        """
        SELECT urutan, tahap_kode, nama,
               CAST(sum(jumlah_masuk) AS BIGINT) AS masuk,
               CAST(sum(jumlah_lulus) AS BIGINT) AS lulus,
               round(100.0 * sum(jumlah_lulus) / sum(jumlah_masuk), 1) AS pct_lulus
        FROM seleksi_tahap_agregat
        GROUP BY 1, 2, 3
        ORDER BY 1
        """
    )


def daftar_gelombang() -> pd.DataFrame:
    """Seluruh gelombang (2019-2025), untuk pembanding corong antar gelombang.

    Kolom: gelombang_id, nama_gelombang, tgl_tutup. Diurutkan dari yang
    paling baru.
    """
    return db.query(
        """
        SELECT gelombang_id, nama_gelombang, tgl_tutup
        FROM gelombang
        ORDER BY tgl_tutup DESC
        """
    )


# ──────────────────────────────────────────────────────────────────────────────
# E. Pasca-Seleksi (halaman 5)
# ──────────────────────────────────────────────────────────────────────────────
#
# Beda dari Corong Seleksi (bagian D): pertanyaan halaman ini "yang sudah lulus
# sekarang prosesnya di mana?" -- posisi hari ini di masing-masing kohort, yang
# bergerak seiring tanggal. Terikat penuh ke `acuan`/`hari_ini()`, tidak seperti
# Corong Seleksi yang historis-tuntas. Satu "kohort" di sini = satu gelombang;
# dipilih halaman lewat `daftar_kohort_pasca()` / `kohort_relevan()`.
#
# Tujuh tahap pasca (`tahap_ref.kategori = 'pasca'`, urutan 100-106) dibaca lewat
# LEFT JOIN dari `tahap_ref` supaya tahap yang belum punya baris sama sekali
# (ujian_ojt, sk_penempatan untuk kohort 2025 -- CATATAN_DATA.md J9) tetap
# tampil dengan peserta=0, bukan hilang dari tabel. Itulah mekanisme
# rekonsiliasi J9: `lini_masa_pasca_kohort()` menaruh "OJT selesai=979" dan
# "Ujian OJT peserta=0" berdampingan di baris yang sama, tanpa perlu fungsi
# tambahan yang menjelaskan sebabnya (P2 -- itu ada di CATATAN_DATA.md).


def daftar_kohort_pasca() -> pd.DataFrame:
    """Seluruh kohort (gelombang) yang punya jejak pasca-seleksi, terbaru dulu.

    Kolom: gelombang_id, nama_gelombang, peserta, tanggal_mulai,
    tanggal_terakhir. `tanggal_mulai` -- awal pengumuman hasil seleksi;
    `tanggal_terakhir` -- tanggal selesai terjauh dari tahap yang memang
    sudah punya baris (kohort 2025 berhenti di selesainya OJT, karena
    ujian_ojt/sk_penempatan belum punya baris sama sekali).
    """
    return db.query(
        """
        SELECT pt.gelombang_id, g.nama_gelombang,
               CAST(count(DISTINCT pt.pendaftaran_id) AS BIGINT) AS peserta,
               min(pt.tanggal_mulai) AS tanggal_mulai,
               max(pt.tanggal_selesai) AS tanggal_terakhir
        FROM pasca_tahap pt
        JOIN gelombang g USING (gelombang_id)
        GROUP BY 1, 2
        ORDER BY tanggal_mulai DESC
        """
    )


def kohort_relevan(acuan: date | None = None) -> str:
    """Kohort paling relevan untuk dibuka pertama kali pada tanggal acuan.

    Prioritas: kohort yang jendela pasca-nya (`tanggal_mulai` s.d.
    `tanggal_terakhir`) mencakup acuan, yang paling baru mulai -- itu kohort
    yang sedang berproses sekarang. Kalau tidak ada yang sedang berjalan,
    kohort terakhir yang jendelanya sudah lewat sebelum acuan. Kalau acuan
    lebih awal dari kohort mana pun, kohort paling awal.
    """
    acuan = _acuan(acuan)
    daftar = daftar_kohort_pasca()
    ts = pd.Timestamp(acuan)
    aktif = daftar[(daftar["tanggal_mulai"] <= ts) & (daftar["tanggal_terakhir"] >= ts)]
    if not aktif.empty:
        return aktif.sort_values("tanggal_mulai", ascending=False).iloc[0]["gelombang_id"]
    lewat = daftar[daftar["tanggal_terakhir"] < ts]
    if not lewat.empty:
        return lewat.sort_values("tanggal_terakhir", ascending=False).iloc[0]["gelombang_id"]
    return daftar.sort_values("tanggal_mulai", ascending=True).iloc[0]["gelombang_id"]


def lini_masa_pasca_kohort(gelombang_id: str, acuan: date | None = None) -> pd.DataFrame:
    """Posisi satu kohort di ketujuh tahap pasca-seleksi, pada tanggal acuan.

    Kolom: urutan, tahap_kode, nama, peserta, tanggal_mulai, tanggal_selesai,
    selesai, berjalan, belum_mulai. `peserta` -- jumlah baris nyata yang ada
    untuk tahap itu pada kohort ini (bisa 0 -- lihat catatan bagian di atas).
    `selesai`/`berjalan`/`belum_mulai` dihitung dari perbandingan
    `tanggal_mulai`/`tanggal_selesai` terhadap acuan, bukan dari kolom
    `pasca_tahap.status` yang beku (ATURAN_TAMPILAN.md §4.1).
    """
    acuan = _acuan(acuan)
    return db.query(
        """
        SELECT r.urutan, r.tahap_kode, r.nama,
               CAST(count(pt.pendaftaran_id) AS BIGINT) AS peserta,
               min(pt.tanggal_mulai) AS tanggal_mulai,
               max(pt.tanggal_selesai) AS tanggal_selesai,
               CAST(sum(CASE WHEN pt.tanggal_selesai <= ? THEN 1 ELSE 0 END) AS BIGINT) AS selesai,
               CAST(sum(CASE WHEN pt.tanggal_mulai <= ? AND pt.tanggal_selesai > ?
                         THEN 1 ELSE 0 END) AS BIGINT) AS berjalan,
               CAST(sum(CASE WHEN pt.tanggal_mulai > ? THEN 1 ELSE 0 END) AS BIGINT) AS belum_mulai
        FROM tahap_ref r
        LEFT JOIN pasca_tahap pt ON pt.tahap_kode = r.tahap_kode AND pt.gelombang_id = ?
        WHERE r.kategori = 'pasca'
        GROUP BY 1, 2, 3
        ORDER BY 1
        """,
        [acuan, acuan, acuan, acuan, gelombang_id],
    )


def status_samapta_kohort(gelombang_id: str) -> dict[str, object] | None:
    """Jendela pelaksanaan SAMAPTA untuk satu kohort.

    Kolom kembalian: peserta, tanggal_mulai, tanggal_selesai, durasi_hari.
    Tidak ada kolom lokasi -- `pasca_tahap` tidak menyimpan lokasi
    pelaksanaan SAMAPTA (CATATAN_DATA.md). `None` kalau kohort ini belum
    punya satu baris SAMAPTA pun.
    """
    df = db.query(
        """
        SELECT CAST(count(*) AS BIGINT) AS peserta,
               min(pt.tanggal_mulai) AS tanggal_mulai,
               max(pt.tanggal_selesai) AS tanggal_selesai,
               date_diff('day', min(pt.tanggal_mulai), max(pt.tanggal_selesai)) AS durasi_hari
        FROM pasca_tahap pt
        WHERE pt.tahap_kode = 'samapta' AND pt.gelombang_id = ?
        """,
        [gelombang_id],
    )
    if df.empty or df.iloc[0]["peserta"] == 0:
        return None
    return df.iloc[0].to_dict()


def pembidangan_per_kohort(gelombang_id: str) -> pd.DataFrame:
    """Sebaran bidang pembidangan untuk satu kohort.

    Kolom: bidang_pembidangan, jumlah. Diurutkan dari yang terbanyak.
    """
    return db.query(
        """
        SELECT pe.bidang_pembidangan, CAST(count(*) AS BIGINT) AS jumlah
        FROM penempatan pe
        JOIN pendaftaran p USING (pendaftaran_id)
        WHERE p.gelombang_id = ?
        GROUP BY 1
        ORDER BY 2 DESC
        """,
        [gelombang_id],
    )


def ojt_per_updl_kohort(gelombang_id: str) -> pd.DataFrame:
    """Sebaran peserta OJT per UPDL untuk satu kohort.

    Kolom: nama_updl, jumlah. Seluruh 11 UPDL selalu tampil, termasuk yang
    bernilai 0 untuk kohort ini (P5 -- granularitas penuh).
    """
    return db.query(
        """
        SELECT u.nama AS nama_updl, CAST(coalesce(count(pe.penempatan_id), 0) AS BIGINT) AS jumlah
        FROM updl u
        LEFT JOIN (
            SELECT pe.* FROM penempatan pe
            JOIN pendaftaran p USING (pendaftaran_id)
            WHERE p.gelombang_id = ?
        ) pe ON pe.updl_id = u.updl_id
        GROUP BY 1
        ORDER BY 2 DESC
        """,
        [gelombang_id],
    )


def status_sk_kohort(gelombang_id: str, acuan: date | None = None) -> dict[str, int]:
    """Berapa SK penempatan sudah terbit vs masih menunggu, untuk satu kohort.

    Kolom kembalian: total, terbit, menunggu. `terbit` dihitung dari baris
    `pasca_tahap` tahap `sk_penempatan` yang `tanggal_selesai`-nya sudah lewat
    acuan -- bukan dari kolom `penempatan.status_sk` yang beku.
    """
    acuan = _acuan(acuan)
    df = db.query(
        """
        WITH total AS (
            SELECT count(DISTINCT pendaftaran_id) AS n FROM pasca_tahap WHERE gelombang_id = ?
        ),
        terbit AS (
            SELECT count(*) AS n FROM pasca_tahap
            WHERE gelombang_id = ? AND tahap_kode = 'sk_penempatan' AND tanggal_selesai <= ?
        )
        SELECT total.n AS total, terbit.n AS terbit, total.n - terbit.n AS menunggu
        FROM total, terbit
        """,
        [gelombang_id, gelombang_id, acuan],
    )
    baris = df.iloc[0]
    return {
        "total": int(baris["total"]),
        "terbit": int(baris["terbit"]),
        "menunggu": int(baris["menunggu"]),
    }


def unit_tujuan_sk_kohort(gelombang_id: str) -> pd.DataFrame:
    """Unit tujuan penempatan untuk satu kohort, hanya yang sudah punya unit.

    Kolom: nama_pendek, jumlah. Kosong kalau seluruh kohort ini belum
    memiliki unit tujuan -- keadaan nyata (belum diputuskan), bukan data
    hilang (CATATAN_DATA.md).
    """
    return db.query(
        """
        SELECT u.nama_pendek, CAST(count(*) AS BIGINT) AS jumlah
        FROM penempatan pe
        JOIN pendaftaran p USING (pendaftaran_id)
        JOIN unit_induk u ON u.unit_induk = pe.unit_induk
        WHERE p.gelombang_id = ?
        GROUP BY 1
        ORDER BY 2 DESC
        """,
        [gelombang_id],
    )


# ──────────────────────────────────────────────────────────────────────────────
# F. Rencana & Realisasi (halaman 6)
# ──────────────────────────────────────────────────────────────────────────────
#
# Pertanyaan harian: seberapa tepat perencanaan kami ternyata? Analisis
# lintas-tahun atas riwayat yang sudah tuntas (2019-2025) -- sama seperti
# Corong Seleksi (bagian D), fungsi-fungsi di bagian ini TIDAK terikat
# `hari_ini()`/`acuan` (penyimpangan disetujui ATURAN_TAMPILAN.md §4.5: nilai
# analitisnya historis, datanya tidak berubah lagi, dan tidak ada status yang
# bisa berubah terhadap tanggal berjalan).
#
# Dua angka rencana yang tidak pernah didamaikan (CATATAN_DATA.md §7):
# `pagu_rekrutmen.jumlah` (sisi anggaran) dan `gelombang.diterima_target`
# (sisi program). Realisasi (`penempatan`, dihitung per `tahun_program`)
# konsisten mengikuti target gelombang, bukan pagu -- ditampilkan
# berdampingan, tidak ditafsirkan di sini (penafsiran ada di halaman).
#
# Tahun RBB (2020, 2021, 2024): `usulan_kebutuhan`/`penempatan` tahun-tahun
# itu hanya menyimpan sisa pelamar yang lolos saringan FHCI, bukan seluruh
# kohort -- CATATAN_DATA.md §7 menyebut eksplisit "menyajikan 2021 sebagai
# pemenuhan 7,1% adalah salah baca". Ditandai lewat kolom `tahun_rbb`, bukan
# disembunyikan -- halaman yang memutuskan mengeluarkannya dari rata-rata.
_TAHUN_RBB = (2020, 2021, 2024)


def pagu_target_realisasi_tahunan() -> pd.DataFrame:
    """Tiga angka rencana & realisasi per tahun program, 2019-2025.

    Kolom: tahun, pagu, target_gelombang, ditempatkan, selisih_pagu_target.
    `pagu` -- jumlah disetujui pusat (`pagu_rekrutmen`). `target_gelombang`
    -- target penerimaan yang ditulis di gelombang pendaftaran
    (`gelombang.diterima_target`). `ditempatkan` -- jumlah baris penempatan
    nyata. `selisih_pagu_target` positif berarti target gelombang melebihi
    pagu yang disetujui -- dua angka rencana yang tidak pernah didamaikan
    (CATATAN_DATA.md §7), bukan galat penghitungan.
    """
    return db.query(
        """
        WITH pagu AS (
            SELECT tahun_program AS tahun, sum(jumlah) AS pagu
            FROM pagu_rekrutmen GROUP BY 1
        ),
        target AS (
            SELECT tahun_program AS tahun, sum(diterima_target) AS target_gelombang
            FROM gelombang GROUP BY 1
        ),
        ditempatkan AS (
            SELECT tahun_program AS tahun, count(*) AS ditempatkan
            FROM penempatan GROUP BY 1
        )
        SELECT p.tahun, p.pagu, t.target_gelombang, d.ditempatkan,
               t.target_gelombang - p.pagu AS selisih_pagu_target
        FROM pagu p
        JOIN target t USING (tahun)
        JOIN ditempatkan d USING (tahun)
        ORDER BY 1
        """
    )


def rencana_realisasi_per_unit(minimal_pegawai: int = _MINIMAL_PEGAWAI_UNIT) -> pd.DataFrame:
    """Rencana vs realisasi penempatan per unit induk, tahun program 2019-2024.

    Kolom: kode_unit, nama_pendek, rencana, realisasi, selisih. `rencana`
    dari `usulan_kebutuhan.usulan`, `realisasi` dari jumlah baris
    `penempatan`. Kohort 2025 (belum sepenuhnya ditempatkan) sengaja di luar
    rentang -- keadaan proses, bukan data hilang. Memakai filter anomali J4
    yang sama dengan bagian B (`jumlah_pegawai > 50`).
    """
    return db.query(
        """
        WITH rencana AS (
            SELECT unit_induk, round(sum(usulan)) AS rencana
            FROM usulan_kebutuhan
            WHERE tahun_program BETWEEN 2019 AND 2024
            GROUP BY 1
        ),
        realisasi AS (
            SELECT unit_induk, count(*) AS realisasi
            FROM penempatan
            WHERE tahun_program BETWEEN 2019 AND 2024 AND unit_induk IS NOT NULL
            GROUP BY 1
        )
        SELECT r.unit_induk AS kode_unit, iu.nama_pendek, r.rencana,
               CAST(coalesce(rl.realisasi, 0) AS BIGINT) AS realisasi,
               CAST(coalesce(rl.realisasi, 0) AS BIGINT) - r.rencana AS selisih
        FROM rencana r
        LEFT JOIN realisasi rl USING (unit_induk)
        JOIN unit_induk iu ON iu.unit_induk = r.unit_induk
        WHERE iu.jumlah_pegawai > ?
        ORDER BY 5 DESC
        """,
        [minimal_pegawai],
    )


def pemenuhan_per_tahun() -> pd.DataFrame:
    """Persentase pemenuhan target gelombang per tahun program, 2019-2025.

    Kolom: tahun, target_gelombang, ditempatkan, pct_pemenuhan, tahun_rbb.
    `tahun_rbb` menandai 2020/2021/2024 -- tahun-tahun itu tercatat cuma
    sisa setelah saringan FHCI, jadi `pct_pemenuhan`-nya bukan gambaran
    penuh kohort (CATATAN_DATA.md §7). Halaman yang memutuskan
    mengeluarkannya dari rata-rata; fungsi ini hanya menandai, tidak
    menghitung ulang rata-ratanya.
    """
    return db.query(
        f"""
        WITH target AS (
            SELECT tahun_program AS tahun, sum(diterima_target) AS target_gelombang
            FROM gelombang GROUP BY 1
        ),
        ditempatkan AS (
            SELECT tahun_program AS tahun, count(*) AS ditempatkan
            FROM penempatan GROUP BY 1
        )
        SELECT t.tahun, t.target_gelombang, d.ditempatkan,
               round(100.0 * d.ditempatkan / t.target_gelombang, 1) AS pct_pemenuhan,
               t.tahun IN ({",".join("?" * len(_TAHUN_RBB))}) AS tahun_rbb
        FROM target t
        JOIN ditempatkan d USING (tahun)
        ORDER BY 1
        """,
        list(_TAHUN_RBB),
    )


# ──────────────────────────────────────────────────────────────────────────────
# G. Profil Pelamar (halaman 7)
# ──────────────────────────────────────────────────────────────────────────────
#
# Pertanyaan harian: siapa yang melamar, dan cocok tidak dengan yang
# dibutuhkan? Seperti bagian D dan F, seluruh fungsi di bagian ini TIDAK
# terikat `hari_ini()`/`acuan` (penyimpangan disetujui ATURAN_TAMPILAN.md
# §4.5): profil demografis pelamar 2019-2025 adalah riwayat tuntas, tidak
# ada status yang bergerak terhadap tanggal berjalan.
#
# Kolom terlarang mutlak (J1, acak seragam di generator): `kota_domisili`,
# `kota_asal`, `tempat_lahir`, `ukuran_baju`, `sekolah_universitas`. Tidak
# satu pun dipakai di bagian ini -- tidak ada analisis almamater, tidak ada
# peta asal-vs-tes.


def umur_gender_pelamar() -> pd.DataFrame:
    """Umur (tahun genap) x jenis kelamin, dihitung pada tanggal MELAMAR --
    bukan tanggal daftar akun maupun hari ini.

    Kolom: umur, jenis_kelamin, jumlah. Kode gender P = Pria, W = Wanita (J5)
    -- membalik keduanya membalik seluruh piramida. Rentang nyata di data
    20-39 tahun, mayoritas 20-34; tidak dipotong (P5), granularitas per
    tahun umur.
    """
    return db.query(
        """
        SELECT date_diff('year', k.tanggal_lahir, p.tanggal_lamar) AS umur,
               k.jenis_kelamin,
               CAST(count(*) AS BIGINT) AS jumlah
        FROM pendaftaran p
        JOIN kandidat k USING (kandidat_id)
        GROUP BY 1, 2
        ORDER BY 1, 2
        """
    )


def jenjang_pendidikan_pelamar() -> pd.DataFrame:
    """Jenjang pendidikan pelamar, dihitung dari riwayat pendidikan TERAKHIR
    saja.

    Kolom: degree, jumlah. Wajib filter `pendidikan_terakhir` -- tanpa itu
    tiap kandidat menyumbang sampai 4 baris riwayat sekolah (SD/SMP/SMA/S1
    sekaligus) dan jumlahnya menggelembung 3x lipat.
    """
    return db.query(
        """
        SELECT degree, CAST(count(*) AS BIGINT) AS jumlah
        FROM kandidat_pendidikan
        WHERE pendidikan_terakhir
        GROUP BY 1
        ORDER BY 2 DESC
        """
    )


def rumpun_jurusan_konversi() -> pd.DataFrame:
    """Rumpun jurusan pendidikan terakhir: yang melamar vs yang diterima.

    Kolom: rumpun, melamar, diterima. Join lewat `program_studi.rumpun`
    (BUKAN `profesi_prodi`/`rumpun_jurusan` -- keduanya salah tabel untuk
    pertanyaan ini). Total `melamar` sedikit di bawah total pendaftaran --
    sebagian `program_studi` pelamar tidak punya padanan rumpun di kamus
    referensi (rumpun None), baris itu tersaring lewat INNER JOIN.
    """
    return db.query(
        """
        SELECT ps.rumpun,
               CAST(count(*) AS BIGINT) AS melamar,
               CAST(sum(CASE WHEN p.hasil_akhir = 'DITERIMA' THEN 1 ELSE 0 END) AS BIGINT) AS diterima
        FROM pendaftaran p
        JOIN kandidat_pendidikan kp
             ON kp.kandidat_id = p.kandidat_id AND kp.pendidikan_terakhir
        JOIN program_studi ps ON ps.program_studi = kp.program_studi
        GROUP BY 1
        ORDER BY 2 DESC
        """
    )


def provinsi_domisili_pelamar() -> pd.DataFrame:
    """Sebaran provinsi domisili kandidat, seluruh basis kandidat.

    Kolom: propinsi_domisili, jumlah. Kolom ini berpola benar (rasio
    16,4 -- CATATAN_DATA.md J1), aman dipakai. `propinsi_domisili` kosong
    untuk sebagian kandidat -- baris itu tetap tampil sebagai NULL, bukan
    disaring diam-diam.
    """
    return db.query(
        """
        SELECT propinsi_domisili, CAST(count(*) AS BIGINT) AS jumlah
        FROM kandidat
        GROUP BY 1
        ORDER BY 2 DESC
        """
    )


def volume_tes_per_kota() -> pd.DataFrame:
    """Volume pelaksanaan tes tatap muka per kota, seluruh tahap seleksi.

    Kolom: lokasi_kota, jumlah. Hanya `mode = 'offline'` -- tes online tidak
    terikat kota. 43 kota, berpola benar (rasio 37,7x -- CATATAN_DATA.md
    J1), aman dipakai.
    """
    return db.query(
        """
        SELECT lokasi_kota, CAST(count(*) AS BIGINT) AS jumlah
        FROM seleksi_tahap
        WHERE mode = 'offline'
        GROUP BY 1
        ORDER BY 2 DESC
        """
    )


def kelengkapan_akun_per_kohort() -> pd.DataFrame:
    """Kelengkapan & aktivasi akun kandidat, per tahun kohort (bukan
    `kualitas_kohort`).

    Kolom: tahun_kohort, total, lengkap, pct_lengkap. "Lengkap & aktif" =
    `email_teraktivasi AND alamat_domisili IS NOT NULL`, definisi yang sama
    dengan agregat nasional di `recruitment_dashboardv2` (M42) -- di sini
    dipecah per tahun untuk menunjukkan kurva kematangan sistem. Tren naik
    dengan dua penyimpangan (2020, 2024) -- lihat CATATAN_DATA.md, bukan
    kenaikan mulus tiap tahun.
    """
    return db.query(
        """
        SELECT tahun_kohort,
               CAST(count(*) AS BIGINT) AS total,
               CAST(sum(CASE WHEN email_teraktivasi AND alamat_domisili IS NOT NULL
                              THEN 1 ELSE 0 END) AS BIGINT) AS lengkap,
               round(100.0 * sum(CASE WHEN email_teraktivasi AND alamat_domisili IS NOT NULL
                                       THEN 1 ELSE 0 END) / count(*), 1) AS pct_lengkap
        FROM kandidat
        GROUP BY 1
        ORDER BY 1
        """
    )
