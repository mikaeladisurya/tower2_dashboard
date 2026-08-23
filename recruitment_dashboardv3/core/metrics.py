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
