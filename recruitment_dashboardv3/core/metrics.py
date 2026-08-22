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
