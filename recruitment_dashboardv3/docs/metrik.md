# Kamus metrik — Dashboard Rekrutmen PLN v3

Kontrak bersama antara halaman dashboard dan chatbot. **Setiap angka yang tampil harus
berasal dari salah satu fungsi di sini**, diimplementasikan sekali di `core/metrics.py`.
Kalau halaman butuh angka baru, metriknya ditambahkan di dokumen ini dulu.

Isi berkas ini **tidak pernah tampil di UI** (P2). `help=` di halaman boleh mengutip baris
"Definisi bisnis" saja — bukan SQL-nya, bukan catatannya.

Semua keluaran di bawah **dijalankan sungguhan** terhadap `mockdb/out/rekrutmen.duckdb`
(dibuka read-only) lewat `../.venv/Scripts/python.exe`, bukan diperkirakan. Yang tidak
dijalankan disebut tidak dijalankan.

---

## Konvensi

| Hal | Aturan |
|---|---|
| Jangkar waktu | **`acuan`** — parameter tiap fungsi, jatuh ke `db.hari_ini()` kalau kosong |
| `hari_ini()` | tanggal berjalan sungguhan, dapat ditimpa pemilih tanggal lewat `session_state` |
| `TANGGAL_POTONG` | **tidak dipakai di modul ini sama sekali** — perannya hanya penanda horison data |
| Status | selalu **dihitung dari perbandingan tanggal terhadap `acuan`**; kolom `pasca_tahap.status` tidak pernah dibaca |
| Tanggal ke SQL | selalu sebagai **parameter** (`db.query(SQL, [acuan, …])`), tidak pernah dirangkai ke string |
| Jendela waktu | selalu **parameter berdefault** (`hari: int = 30`), tidak pernah angka terkubur di SQL |
| Bentuk modul | datar, satu fungsi per metrik, tanpa cache sendiri — `core.db` sudah `@st.cache_data(ttl=3600)` |
| Angka 0 | dikembalikan apa adanya sebagai fakta, tidak pernah diganti angka lama yang tampak terkini (P3) |

### Dua jebakan skema yang wajib diingat saat menambah metrik

1. **`pasca_tahap.urutan` bernilai 7–13, `tahap_ref.urutan` untuk tahap yang sama bernilai
   100–106.** Menjoin lewat `urutan` akan mencampur tahap pasca dengan tahap seleksi
   (urutan 1–6). Join **selalu lewat `tahap_kode`**, dan urutan tampilan **selalu** diambil
   dari `tahap_ref.urutan`.
2. **`pendaftaran.status_lamaran` hanya bernilai `SELESAI`** untuk seluruh 218.928 baris —
   tidak berguna sebagai penyaring. `hasil_akhir` hanya `DITERIMA` / `GAGAL`.

### Angka jangkar — dieksekusi ulang di goal ini

```
pendaftaran : 218928
diterima    : 7711
sudah_sk    : 5711
TANGGAL_POTONG: 2026-09-15   (dibaca dari _meta_generator, bukan diketik)
hari_ini()  : 2026-08-22
```

---

## Helper bersama

### `_acuan(acuan)`

Satu baris: `return acuan or db.hari_ini()`. Dipanggil di baris pertama setiap fungsi
metrik. Inilah yang membuat pemilih tanggal berlaku seragam di seluruh halaman, dan yang
membuat tiap fungsi bisa diuji pada tanggal sembarang di G9.

### `_PERISTIWA_SQL`

Aliran peristiwa bertanggal, disatukan dari **lima** sumber. Dipakai bersama oleh
`tenggat_terdekat()` dan `aktivitas_sekitar()` supaya keduanya tidak pernah punya
definisi "peristiwa" yang berbeda.

| `jenis` | Sumber | Kolom tanggal | `jumlah` |
|---|---|---|---|
| `Selesai tahap pasca-seleksi` | `pasca_tahap` × `tahap_ref` | `tanggal_selesai` | peserta di tahap itu |
| `Mulai tahap pasca-seleksi` | `pasca_tahap` × `tahap_ref` | `tanggal_mulai` | peserta di tahap itu |
| `Tahap seleksi` | `seleksi_tahap` × `tahap_ref` | `tanggal_tahap` | peserta terjadwal hari itu |
| `Gelombang dibuka` | `gelombang` | `tgl_buka` | 0 |
| `Gelombang ditutup` | `gelombang` | `tgl_tutup` | pelamar masuk sampai `acuan` |

Baris "Mulai" disaring `tanggal_mulai <> tanggal_selesai`. Enam dari tujuh tahap pasca
adalah peristiwa titik (durasi 0 hari, lihat J6), jadi tanpa saringan itu semuanya muncul
dua kali di daftar tenggat. Yang lolos saringan hanya `ojt` — satu-satunya tahap pasca
yang punya rentang (180 hari).

```sql
    SELECT 'Selesai tahap pasca-seleksi' AS jenis,
           pt.gelombang_id               AS gelombang,
           r.nama                        AS tahap,
           pt.tanggal_selesai            AS tanggal,
           count(*)                      AS jumlah
    FROM pasca_tahap pt
    JOIN tahap_ref r USING (tahap_kode)
    GROUP BY 1, 2, 3, 4

    UNION ALL

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
```

### `_URUTAN_PENDAFTARAN = 0`

Tahap semu "Pendaftaran" yang tidak ada di `tahap_ref`: pelamar yang lamarannya sudah masuk
tapi belum menjalani satu tahap pun. Tanpa tahap ini, denyut pipeline kehilangan seluruh
pelamar selama masa pendaftaran masih terbuka — pada 2019-09-10 itu 14.348 orang.

---

# A · Metrik Halaman 1 — Beranda

Empat fungsi, semuanya dihitung ulang terhadap `acuan`.

---

## M01 · `keadaan_sekarang(acuan=None) -> dict`

**Definisi bisnis:** empat angka keadaan proses rekrutmen pada tanggal acuan — gelombang
yang sedang dibuka, pelamar yang sedang diseleksi, peserta yang sedang diklat prajabatan,
dan peserta yang sudah selesai diklat tapi SK-nya belum terbit.

Definisi per kunci, layak dipakai sebagai `help=` di halaman:

| Kunci | Definisi bisnis satu kalimat |
|---|---|
| `gelombang_dibuka` | Gelombang yang pendaftarannya sedang terbuka. |
| `sedang_diseleksi` | Pelamar yang tahapan seleksinya sudah dimulai dan hasil akhirnya belum diumumkan. |
| `sedang_ojt` | Peserta yang sedang menjalani diklat prajabatan. |
| `menunggu_sk` | Peserta yang sudah selesai diklat prajabatan tapi SK pengangkatannya belum terbit. |

### SQL

```sql
-- gelombang_dibuka
SELECT count(*) FROM gelombang
WHERE tgl_buka <= ? AND tgl_tutup >= ?

-- sedang_diseleksi
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

-- sedang_ojt
SELECT count(*) FROM pasca_tahap
WHERE tahap_kode = 'ojt'
  AND tanggal_mulai <= ? AND tanggal_selesai > ?

-- menunggu_sk
SELECT count(*) FROM pasca_tahap o
WHERE o.tahap_kode = 'ojt' AND o.tanggal_selesai <= ?
  AND NOT EXISTS (SELECT 1 FROM pasca_tahap s
                  WHERE s.pendaftaran_id = o.pendaftaran_id
                    AND s.tahap_kode = 'sk_penempatan'
                    AND s.tanggal_selesai <= ?)
```

### Keluaran nyata

| `acuan` | `gelombang_dibuka` | `sedang_diseleksi` | `sedang_ojt` | `menunggu_sk` |
|---|---|---|---|---|
| **2026-08-22** | 0 | 0 | **2.000** | 0 |
| **2026-10-05** | 0 | 0 | **1.021** | **979** |
| **2027-01-06** | 0 | 0 | **0** | **2.000** |

Keluaran mentah, apa adanya:

```
{'acuan': datetime.date(2026, 8, 22), 'gelombang_dibuka': 0, 'sedang_diseleksi': 0, 'sedang_ojt': 2000, 'menunggu_sk': 0}
{'acuan': datetime.date(2026, 10, 5), 'gelombang_dibuka': 0, 'sedang_diseleksi': 0, 'sedang_ojt': 1021, 'menunggu_sk': 979}
{'acuan': datetime.date(2027, 1, 6), 'gelombang_dibuka': 0, 'sedang_diseleksi': 0, 'sedang_ojt': 0, 'menunggu_sk': 2000}
```

Tiga tanggal tambahan, untuk membuktikan angkanya juga hidup di masa data ramai:

```
{'acuan': datetime.date(2019, 9, 10), 'gelombang_dibuka': 1, 'sedang_diseleksi': 16661, 'sedang_ojt': 0, 'menunggu_sk': 0}
{'acuan': datetime.date(2025, 10, 15), 'gelombang_dibuka': 0, 'sedang_diseleksi': 17766, 'sedang_ojt': 0, 'menunggu_sk': 0}
{'acuan': datetime.date(2026, 2, 20), 'gelombang_dibuka': 0, 'sedang_diseleksi': 1021, 'sedang_ojt': 0, 'menunggu_sk': 0}
```

### Kenapa `sedang_diseleksi` tidak memakai `min(tanggal_tahap) <= acuan < max(tanggal_tahap)`

Usulan awal G6 adalah definisi rentang itu. Kedua definisi dijalankan berdampingan terhadap
database dan hasilnya beda di satu titik yang menentukan:

| `acuan` | rentang `min … max` | dipakai: sudah mulai, belum gugur, belum diumumkan |
|---|---|---|
| 2019-09-10 | 16.661 | 16.661 |
| 2025-10-15 | 17.766 | 17.766 |
| 2026-01-15 | 4.321 | 4.321 |
| **2026-02-20** | **0** | **1.021** |
| 2026-08-22 | 0 | 0 |

Pada 2026-02-20, seluruh 1.021 pelamar G2025-092 sudah tuntas wawancara (tahap terakhir
2026-02-16) tapi pengumuman hasilnya baru 2026-02-27. Definisi rentang menyatakan mereka
**bukan** sedang diseleksi — padahal justru itu momen paling menegangkan bagi mereka dan
paling perlu terlihat oleh tim rekrutmen. Definisi yang dipakai menutup celah itu.

Ketiga syaratnya bisa dipakai karena sudah diverifikasi: **211.217 pendaftaran `GAGAL`
seluruhnya punya baris `seleksi_tahap` ber-`hasil = 'GAGAL'`** dan **7.711 pendaftaran
`DITERIMA` tidak satu pun punya baris `GAGAL`** — jadi "belum pernah gugur sampai `acuan`"
adalah penanda yang bersih, dan tidak sekali pun membaca kolom `hasil_akhir` yang beku.

Cek silang: pada tiap tanggal, `sedang_diseleksi` **selalu sama persis** dengan jumlah orang
di tahap 1–6 pada `denyut_pipeline()` — diuji pada lima tanggal, cocok semuanya.

### Catatan angka yang terlihat aneh

- **`gelombang_dibuka` = 0 di ketiga tanggal jangkar.** Gelombang terakhir tutup 2025-10-05
  (J10); tidak ada gelombang 2026. Nol adalah jawaban yang benar. Halaman menampilkannya
  sebagai fakta keadaan, bukan sebagai galat, dan **tanpa menerangkan sebabnya** (P2).
- **`menunggu_sk` = 0 pada 2026-08-22, lalu 979, lalu 2.000.** Ini J9 yang sedang bekerja:
  kohort 2025 sama sekali tidak punya baris `ujian_ojt` maupun `sk_penempatan`, jadi begitu
  OJT-nya selesai (G2025-091 pada 2026-10-01, G2025-092 pada 2026-10-15) mereka menggantung
  permanen. Angka 2.000 di 2027 **bukan bug metrik** — itu cacat generator yang memang harus
  terlihat. **Jangan ditambal di SQL.**
- **`sedang_diseleksi` = 0 sejak 2026-02-27.** Aktivitas `seleksi_tahap` terakhir di seluruh
  database 2026-02-16 (J10).

### Biaya

Diukur pada 2019-09-10 (tanggal tersibuk, seleksi hidup di tiga gelombang):
**69,2 ms dingin · 0,5 ms saat kena cache `@st.cache_data`.**

---

## M02 · `tenggat_terdekat(hari=30, acuan=None) -> DataFrame`

**Definisi bisnis:** peristiwa rekrutmen yang jatuh tempo dalam sekian hari ke depan dari
tanggal acuan, diurutkan dari yang paling dekat.

Kolom: `jenis` · `gelombang` · `tahap` · `tanggal` · `hari_tersisa` · `jumlah`.
`hari_tersisa` **dihitung** dengan `date_diff` terhadap `acuan`, tidak pernah diketik —
jadi tidak pernah basi (§4.4).

Jendela waktunya **parameter berdefault**, bukan konstanta di SQL: halaman boleh melebarkan
ke 90 hari tanpa menyentuh `metrics.py`.

### SQL

```sql
WITH peristiwa AS ( … _PERISTIWA_SQL … )
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
```

### Keluaran nyata

**`acuan = 2026-08-22`, `hari = 30`** — kosong, dan itu jawaban yang benar:

```
Empty DataFrame
Columns: [jenis, gelombang, tahap, tanggal, hari_tersisa, jumlah]
Index: []
```

**`acuan = 2026-08-22`, `hari = 90`** — dua tenggat OJT muncul, membuktikan jendelanya
memang parameter:

```
                      jenis gelombang                         tahap    tanggal  hari_tersisa  jumlah
Selesai tahap pasca-seleksi G2025-091 Diklat Prajabatan / First OJT 2026-10-01            40     979
Selesai tahap pasca-seleksi G2025-092 Diklat Prajabatan / First OJT 2026-10-15            54    1021
```

**`acuan = 2026-10-05`, `hari = 30`:**

```
                      jenis gelombang                         tahap    tanggal  hari_tersisa  jumlah
Selesai tahap pasca-seleksi G2025-092 Diklat Prajabatan / First OJT 2026-10-15            10    1021
```

**`acuan = 2027-01-06`, `hari = 30` dan `hari = 90`** — kosong di kedua jendela:

```
Empty DataFrame
Columns: [jenis, gelombang, tahap, tanggal, hari_tersisa, jumlah]
Index: []
```

**`acuan = 2019-09-10`, `hari = 30`** — **59 baris**. Sepuluh baris teratas, ditambah satu
baris `Gelombang ditutup` yang letaknya lebih ke bawah (bukan baris ke-11), untuk menunjukkan
bahwa jenis peristiwa lain memang ikut terjaring:

```
            jenis gelombang                               tahap    tanggal  hari_tersisa  jumlah
    Tahap seleksi G2019-071                Seleksi Administrasi 2019-09-10             0    1490
    Tahap seleksi G2019-070 Tes Akademik (TKB) & Bahasa Inggris 2019-09-11             1     204
    Tahap seleksi G2019-071                Seleksi Administrasi 2019-09-11             1    1562
    Tahap seleksi G2019-070 Tes Akademik (TKB) & Bahasa Inggris 2019-09-12             2     190
    Tahap seleksi G2019-071                Seleksi Administrasi 2019-09-12             2    1610
    Tahap seleksi G2019-070 Tes Akademik (TKB) & Bahasa Inggris 2019-09-13             3     205
    Tahap seleksi G2019-071                Seleksi Administrasi 2019-09-13             3    1510
    Tahap seleksi G2019-070 Tes Akademik (TKB) & Bahasa Inggris 2019-09-14             4     200
    Tahap seleksi G2019-071                Seleksi Administrasi 2019-09-14             4    1558
    Tahap seleksi G2019-070 Tes Akademik (TKB) & Bahasa Inggris 2019-09-15             5     177
Gelombang ditutup G2019-072                 Pendaftaran ditutup 2019-09-20            10    6559
```

### Catatan

- Peristiwa yang jatuh **tepat pada `acuan`** ikut terhitung, `hari_tersisa = 0` — lihat
  baris pertama keluaran 2019-09-10.
- Pada masa seleksi ramai, tahap tes dijadwalkan **harian per gelombang**, jadi daftar ini
  bisa puluhan baris. Pemotongan tampilan adalah keputusan halaman (G10), bukan metrik —
  metrik tidak boleh diam-diam membuang baris.
- Kolom `jumlah` untuk `Gelombang dibuka` selalu 0: pada hari pembukaan belum ada pelamar.

### Biaya

**15,5 ms dingin · 0,5 ms saat kena cache**, diukur pada 2019-09-10 dengan 59 baris hasil.

---

## M03 · `denyut_pipeline(acuan=None) -> DataFrame`

**Definisi bisnis:** jumlah pelamar yang masih berproses di tiap tahap pada tanggal acuan,
dari pendaftaran sampai SK penempatan.

Kolom: `urutan` · `tahap_kode` · `nama` · `jumlah` · `sedang_berjalan` · `sudah_tuntas`.

Aturan penempatannya: **tiap pelamar yang masih berproses menempati tepat satu tahap** —
tahap terjauh yang sudah dimulai sampai `acuan`. Pelamar yang sudah gugur sampai `acuan`
keluar dari hitungan. Urutan dan label diambil dari `tahap_ref`; tahap yang kosong tetap
muncul dengan nilai 0 supaya bentuk pipeline-nya utuh.

### SQL

```sql
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
```

### Penyimpangan dari rancangan yang diusulkan, dan alasannya

Usulan G6 adalah satu kolom hitungan saja: tahap terjauh yang sudah dimulai. Dijalankan apa
adanya, hasilnya **identik di ketiga tanggal jangkar** — 2.000 di OJT dan 5.711 di SK pada
2026-08-22, 2026-10-05, **dan** 2027-01-06. Denyut yang tidak berdenyut.

Lebih buruk: pada 2027-01-06 kartu M01 berkata `sedang_ojt = 0` sementara pipeline berkata
"2.000 di Diklat Prajabatan". Dua angka bertentangan di satu halaman.

Sebabnya J9. Kohort 2025 tidak punya baris tahap sesudah OJT, jadi "tahap terjauh yang sudah
dimulai" mereka **selamanya** OJT. Karena itu hitungannya dipecah dua tanpa mengubah aturan
"tepat satu tahap":

- **`sedang_berjalan`** — tahapnya masih berlangsung pada `acuan`
- **`sudah_tuntas`** — tahapnya sudah rampung pada `acuan`, orangnya menunggu tahap berikutnya

`jumlah = sedang_berjalan + sudah_tuntas` selalu, diuji pada lima tanggal. Sekarang pipeline
bergerak (2.000 berjalan → 1.021 berjalan / 979 tuntas → 2.000 tuntas) dan tidak lagi
bertentangan dengan M01. Penyimpangan ini **menambah** kolom, tidak mengganti rancangan.

Pemilahan ketuntasan berbeda per kategori tahap, dan itu memang benar:
tahap **seleksi** adalah peristiwa satu hari, jadi begitu tanggalnya lewat tahapnya tuntas
dan pelamar menunggu tahap berikutnya (`sedang_berjalan` selalu 0 di tahap 1–6). Tahap
**pasca** punya `tanggal_selesai`, jadi dibandingkan ke sana. Tahap semu **Pendaftaran**
dihitung `sedang_berjalan`: pelamar memang masih duduk di tahap itu sampai tahap seleksi
pertamanya tiba.

### Keluaran nyata

**`acuan = 2026-08-22`:**

```
 urutan       tahap_kode                                nama  jumlah  sedang_berjalan  sudah_tuntas
      0      pendaftaran                         Pendaftaran       0                0             0
      1     administrasi                Seleksi Administrasi       0                0             0
      2          adaptif               Tes Adaptif PLN (TAP)       0                0             0
      3 akademik_inggris Tes Akademik (TKB) & Bahasa Inggris       0                0             0
      4        psikologi                       Tes Psikologi       0                0             0
      5        fisik_mcu        Tes Fisik & Medical Check-Up       0                0             0
      6        wawancara                 Wawancara User & HR       0                0             0
    100 pengumuman_akhir            Pengumuman Hasil Seleksi       0                0             0
    101      ttd_kontrak          Penandatanganan Perjanjian       0                0             0
    102          samapta                             SAMAPTA       0                0             0
    103      pembidangan               Penetapan Pembidangan       0                0             0
    104              ojt       Diklat Prajabatan / First OJT    2000             2000             0
    105        ujian_ojt                     Ujian Akhir OJT       0                0             0
    106    sk_penempatan        SK Pengangkatan & Penempatan    5711                0          5711
```

**`acuan = 2026-10-05`** — baris yang berubah (sisanya nol, sama seperti di atas):

```
    104              ojt       Diklat Prajabatan / First OJT    2000             1021           979
    106    sk_penempatan        SK Pengangkatan & Penempatan    5711                0          5711
```

**`acuan = 2027-01-06`** — baris yang berubah:

```
    104              ojt       Diklat Prajabatan / First OJT    2000                0          2000
    106    sk_penempatan        SK Pengangkatan & Penempatan    5711                0          5711
```

Tiga tanggal tambahan, saat pipeline benar-benar ramai:

**`acuan = 2019-09-10`** — gelombang G2019-072 masih membuka pendaftaran:

```
 urutan       tahap_kode                                nama  jumlah  sedang_berjalan  sudah_tuntas
      0      pendaftaran                         Pendaftaran   14348            14348             0
      1     administrasi                Seleksi Administrasi   14117                0         14117
      2          adaptif               Tes Adaptif PLN (TAP)    2544                0          2544
      3 akademik_inggris Tes Akademik (TKB) & Bahasa Inggris       0                0             0
      4        psikologi                       Tes Psikologi       0                0             0
      5        fisik_mcu        Tes Fisik & Medical Check-Up       0                0             0
      6        wawancara                 Wawancara User & HR       0                0             0
    100 pengumuman_akhir            Pengumuman Hasil Seleksi       0                0             0
    101      ttd_kontrak          Penandatanganan Perjanjian       0                0             0
    102          samapta                             SAMAPTA       0                0             0
    103      pembidangan               Penetapan Pembidangan       0                0             0
    104              ojt       Diklat Prajabatan / First OJT       0                0             0
    105        ujian_ojt                     Ujian Akhir OJT       0                0             0
    106    sk_penempatan        SK Pengangkatan & Penempatan       0                0             0
```

**`acuan = 2025-10-15`** — baris tidak nol:

```
      0      pendaftaran                         Pendaftaran   28745            28745             0
      1     administrasi                Seleksi Administrasi   17766                0         17766
    106    sk_penempatan        SK Pengangkatan & Penempatan    5711                0          5711
```

**`acuan = 2026-02-20`** — baris tidak nol; 1.021 orang menunggu pengumuman, 979 sudah
diumumkan dan menunggu tanda tangan perjanjian:

```
      6        wawancara                 Wawancara User & HR    1021                0          1021
    100 pengumuman_akhir            Pengumuman Hasil Seleksi     979                0           979
    106    sk_penempatan        SK Pengangkatan & Penempatan    5711                0          5711
```

### Cek silang yang dijalankan

| Yang diperiksa | Hasil |
|---|---|
| `jumlah = sedang_berjalan + sudah_tuntas` di tiap baris | benar di 5 tanggal uji |
| jumlah tahap 1–6 = `keadaan_sekarang()['sedang_diseleksi']` | cocok di 5 tanggal uji |
| total pipeline saat tidak ada seleksi hidup | 7.711 = angka jangkar `diterima` |
| baris `sk_penempatan` | 5.711 = angka jangkar `sudah_sk` |
| total pipeline 2019-09-10 | 31.009 (lebih besar dari 7.711, karena seleksi sedang hidup) |

### Catatan angka yang terlihat aneh

- **`ujian_ojt` = 0 di semua tanggal.** J9: kohort 2025 tidak punya barisnya, dan kohort
  sebelumnya sudah lewat ke `sk_penempatan`. Bukan kesalahan query.
- **2.000 orang berhenti di baris `ojt` selamanya sesudah 2026-10-15.** Juga J9. Yang
  terlihat di kolom `sudah_tuntas`, bukan `sedang_berjalan` — jadi pembaca melihat "sudah
  rampung, menunggu tahap berikutnya", bukan "sedang OJT di tahun 2027". **Jangan ditambal.**
- **`sedang_berjalan` selalu 0 di tahap 1–6** — konsekuensi tahap seleksi berdurasi satu hari.

### Biaya

**36,4 ms dingin · 0,5 ms saat kena cache**, diukur pada 2019-09-10. Query menyentuh
`pendaftaran` (218.928), `seleksi_tahap` (464.688), dan `pasca_tahap` (49.977) hanya sebagai
agregat — tidak ada tabel yang dimuat penuh ke DataFrame; hasilnya selalu 14 baris.

---

## M04 · `aktivitas_sekitar(acuan=None) -> DataFrame`

**Definisi bisnis:** peristiwa rekrutmen terakhir sebelum tanggal acuan dan peristiwa
terjadwal berikutnya sesudahnya.

Kolom: `arah` (`terakhir` / `berikutnya`) · `jenis` · `gelombang` · `tahap` · `tanggal` ·
`selisih_hari` · `jumlah`. `selisih_hari` negatif untuk masa lalu, positif untuk masa depan,
dan **dihitung** terhadap `acuan`.

Inilah yang menjaga Beranda tidak pernah kosong melompong ketika tidak ada apa pun yang
sedang berjalan.

### SQL

```sql
WITH peristiwa AS ( … _PERISTIWA_SQL … ),
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
```

Kalau beberapa peristiwa jatuh di tanggal yang sama, yang dipilih adalah yang **melibatkan
paling banyak orang** (`ORDER BY … jumlah DESC`).

### Keluaran nyata

**`acuan = 2026-08-22`:**

```
      arah                       jenis gelombang                         tahap    tanggal  selisih_hari  jumlah
  terakhir   Mulai tahap pasca-seleksi G2025-092 Diklat Prajabatan / First OJT 2026-04-18          -126    1021
berikutnya Selesai tahap pasca-seleksi G2025-091 Diklat Prajabatan / First OJT 2026-10-01            40     979
```

**`acuan = 2026-10-05`:**

```
      arah                       jenis gelombang                         tahap    tanggal  selisih_hari  jumlah
  terakhir Selesai tahap pasca-seleksi G2025-091 Diklat Prajabatan / First OJT 2026-10-01            -4     979
berikutnya Selesai tahap pasca-seleksi G2025-092 Diklat Prajabatan / First OJT 2026-10-15            10    1021
```

**`acuan = 2027-01-06`** — hanya satu baris, karena memang tidak ada lagi peristiwa
terjadwal di seluruh database sesudah 2026-10-15 (J10):

```
    arah                       jenis gelombang                         tahap    tanggal  selisih_hari  jumlah
terakhir Selesai tahap pasca-seleksi G2025-092 Diklat Prajabatan / First OJT 2026-10-15           -83    1021
```

Tiga tanggal tambahan:

```
acuan 2019-09-10
      arah         jenis gelombang                tahap    tanggal  selisih_hari  jumlah
  terakhir Tahap seleksi G2019-071 Seleksi Administrasi 2019-09-09            -1    1619
berikutnya Tahap seleksi G2019-071 Seleksi Administrasi 2019-09-11             1    1562

acuan 2025-10-15
      arah         jenis gelombang                tahap    tanggal  selisih_hari  jumlah
  terakhir Tahap seleksi G2025-092 Seleksi Administrasi 2025-10-14            -1    2653
berikutnya Tahap seleksi G2025-092 Seleksi Administrasi 2025-10-16             1    2607

acuan 2026-02-20
      arah                       jenis gelombang                      tahap    tanggal  selisih_hari  jumlah
  terakhir               Tahap seleksi G2025-092        Wawancara User & HR 2026-02-16            -4      82
berikutnya Selesai tahap pasca-seleksi G2025-091 Penandatanganan Perjanjian 2026-02-23             3      77
```

### Catatan

- Peristiwa yang jatuh **tepat pada `acuan`** tidak muncul di sini; ia muncul di
  `tenggat_terdekat()` dengan `hari_tersisa = 0`. Kedua fungsi membaca `_PERISTIWA_SQL` yang
  sama, jadi tidak ada peristiwa yang hilang di antara keduanya.
- Sisi yang memang tidak punya peristiwa **tidak menghasilkan baris**, bukan baris kosong —
  halaman yang memutuskan bagaimana menampilkannya (§4.3).

### Biaya

**32,3 ms dingin · 0,5 ms saat kena cache**, diukur pada 2019-09-10.

---

---

# B · Metrik Halaman 2 — Perencanaan Formasi (G11)

Rantai perencanaan yang ada di data:

```
proyeksi_kekosongan  →  usulan_kebutuhan  →  pagu_rekrutmen
 (per unit x posisi,     (kekosongan +         (2019-2025)
    2019-2026)            gap FTK, 2019-2025)
```

`proyeksi_kekosongan` **berhenti di 2026** — begitu `hari_ini()` melewatinya, fungsi yang
bergantung pada tahun berjalan mengembalikan DataFrame kosong (bukan galat, bukan data lama
disamarkan). Halaman menampilkan ini sebagai keadaan data lewat `keadaan_kosong()` lalu jatuh
ke tahun historis terakhir — lihat `rentang_tahun_proyeksi()` di bawah.

**Filter anomali J4 (`WHERE jumlah_pegawai > 50`)** dipakai konsisten di
`kekosongan_per_unit`, `daftar_unit_induk`, `gap_ftk_nasional`, dan `gap_ftk_per_unit` — bukan
cuma di tabel per-unit. Alasannya diuraikan di M08 di bawah: tanpa filter ini, KPI nasional
(701) dan jumlah baris di tabel per-unit (yang sudah tersaring, 561) akan terlihat tidak
cocok satu sama lain tanpa penjelasan apa pun di layar (P2 melarang menerangkan sebabnya di
UI) — jadi filter yang sama dipakai di kedua tempat.

---

## M05 · `rentang_tahun_proyeksi() -> tuple[int, int]`

**Definisi bisnis:** tahun minimum & maksimum yang tersedia di data proyeksi kekosongan —
batas horison proyeksi.

### SQL

```sql
SELECT min(tahun) AS mn, max(tahun) AS mx FROM proyeksi_kekosongan
```

### Keluaran nyata

```
(2019, 2026)
```

---

## M06 · `kekosongan_per_sebab(acuan=None) -> DataFrame`

**Definisi bisnis:** proyeksi kekosongan per sebab (pensiun, mengundurkan diri, meninggal
dunia, PHK), untuk tahun berjalan dan tahun berikutnya dari `acuan`.

Tahun **diturunkan dari `acuan`** (`acuan.year` dan `acuan.year + 1`), tidak pernah
di-hardcode 2026/2027. Kalau kedua tahun di luar rentang `rentang_tahun_proyeksi()`,
hasilnya kosong — jawaban yang benar, bukan galat.

### SQL

```sql
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
```

### Keluaran nyata

**`acuan = 2026-08-23`** (satu baris — 2027 di luar rentang):

```
   tahun  pensiun  mengundurkan_diri  meninggal_dunia   phk  total
0   2026    780.0               78.0             39.0  22.0  919.0
```

**`acuan = 2025-12-01`** (dua baris — 2025 dan 2026 keduanya ada):

```
   tahun  pensiun  mengundurkan_diri  meninggal_dunia   phk   total
0   2025    864.0               85.0             43.0  23.0  1015.0
1   2026    780.0               78.0             39.0  22.0   919.0
```

**`acuan = 2019-01-01`:**

```
   tahun  pensiun  mengundurkan_diri  meninggal_dunia   phk   total
0   2019   2122.0              133.0             66.0  37.0  2357.0
1   2020   1656.0              107.0             53.0  29.0  1845.0
```

**Batas jujur — `acuan = 2027-01-06`** (kosong, kedua tahun 2027/2028 di luar data):

```
Empty DataFrame
Columns: [tahun, pensiun, mengundurkan_diri, meninggal_dunia, phk, total]
Index: []
```

2026: 919 kekosongan, 780 karena pensiun — **85%**, seperti dicatat di
`docs/RANCANGAN_HALAMAN.md` §4.

---

## M07 · `kekosongan_per_unit(tahun, minimal_pegawai=50) -> DataFrame`

**Definisi bisnis:** proyeksi kekosongan per unit induk pada satu tahun, diurutkan dari yang
paling terancam.

Filter anomali J4 (`jumlah_pegawai > 50`) menyingkirkan baris duplikat pecahan Yogyakarta.

### SQL

```sql
SELECT pk.unit_induk, u.nama_pendek, u.jenis_unit,
       round(sum(pk.kekosongan)) AS kekosongan
FROM proyeksi_kekosongan pk
JOIN unit_induk u ON u.unit_induk = pk.unit_induk
WHERE pk.tahun = ? AND u.jumlah_pegawai > ?
GROUP BY 1, 2, 3
ORDER BY 4 DESC
```

### Keluaran nyata

**`tahun = 2026`** — 47 baris (48 unit dikurangi 1 anomali J4). Sepuluh teratas:

```
Kantor Pusat            153
UID Jawa Timur           53
UID Jawa Barat           46
UID Jawa Tengah & DIY    40
UID Jakarta Raya         36
P3B Sumatera             32
UID Sumut                30
UIT JBT                  30
UID Sulselrabar          27
UID S2JB                 24
```

**Batas jujur — `tahun = 2027`:** kosong (di luar `rentang_tahun_proyeksi()`).

---

## M08 · `daftar_unit_induk(minimal_pegawai=50) -> DataFrame`

**Definisi bisnis:** daftar unit induk untuk filter halaman — kode dan nama pendek.

Kolom kembalian **`kode_unit`** (bukan `unit_induk`) — alias sengaja dipilih supaya halaman
yang memanggilnya tidak perlu menyebut nama kolom sumber sebagai string literal.

### SQL

```sql
SELECT unit_induk AS kode_unit, nama_pendek
FROM unit_induk
WHERE jumlah_pegawai > ?
ORDER BY nama_pendek
```

### Keluaran nyata

**47 baris** (48 dikurangi 1 anomali J4).

---

## M09 · `kekosongan_per_posisi(unit_induk, tahun) -> DataFrame`

**Definisi bisnis:** proyeksi kekosongan per posisi & sub-bidang, untuk satu unit pada satu
tahun. Baris dengan kekosongan 0 disaring — unit besar bisa punya ribuan kombinasi posisi
x jenjang, mayoritas tanpa kekosongan.

### SQL

```sql
SELECT nama_posisi, sub_bidang, jenjang, round(sum(kekosongan)) AS kekosongan
FROM proyeksi_kekosongan
WHERE unit_induk = ? AND tahun = ?
GROUP BY 1, 2, 3
HAVING round(sum(kekosongan)) > 0
ORDER BY 4 DESC
```

⚠️ **Jebakan ditemukan saat diuji:** `HAVING sum(kekosongan) > 0` (tanpa pembulatan) meloloskan
baris dengan kekosongan pecahan kecil (mis. 0,3) yang lalu **tampil sebagai 0** setelah
`round()` di `SELECT` — inkonsisten dan membingungkan. Diperbaiki dengan membulatkan di kedua
sisi: `HAVING round(sum(kekosongan)) > 0`.

### Keluaran nyata

**Kantor Pusat, 2026** — 14 baris (bukan 2.318 baris mentah posisi x jenjang unit ini;
setelah agregasi sub_bidang dan penyaringan kekosongan=0). Tiga teratas:

```
SENIOR OFFICER VERIFIKASI                    Keuangan dan Akuntansi   G3   2
SENIOR SPECIALIST KEUANGAN                   Keuangan dan Akuntansi  SSP   1
SENIOR SPECIALIST HUMAN CAPITAL MANAGEMENT   Sumber Daya Manusia     SSP   1
```

---

## M10 · `gap_ftk_nasional(minimal_pegawai=50) -> dict` · `gap_ftk_per_unit(minimal_pegawai=50) -> DataFrame`

**Definisi bisnis:** formasi tenaga kerja (FTK 2025) dikurangi realisasi pegawai (Maret
2026) — kekurangan pegawai terhadap formasi yang ditetapkan.

**WAJIB `realisasi_mar_2026`**: `realisasi_apr_2026` hanya terisi di 1 dari 48 unit dan
menghasilkan gap palsu 33.934 (CATATAN_DATA.md J8).

### SQL

```sql
-- nasional
SELECT sum(ftk_2025) AS ftk, sum(realisasi_mar_2026) AS realisasi,
       sum(ftk_2025) - sum(realisasi_mar_2026) AS gap
FROM unit_induk WHERE jumlah_pegawai > ?

-- per unit
SELECT nama_pendek, jenis_unit, ftk_2025, realisasi_mar_2026,
       ftk_2025 - realisasi_mar_2026 AS gap
FROM unit_induk WHERE jumlah_pegawai > ?
ORDER BY gap DESC
```

### Keluaran nyata

**Nasional (filter J4 diterapkan):**

```
{'ftk': 37710.0, 'realisasi': 37149.0, 'gap': 561.0}
```

**⚠️ Ini BUKAN 701.** 701 adalah jumlah seluruh **48 baris apa adanya**, termasuk baris
duplikat J4 ("UID Jawa Tengah & DIY" pecahan Yogyakarta, `jumlah_pegawai=4`, gap sendiri
140). `701 − 140 = 561`. Angka jangkar G6 (`gap_ftk = 701`, dikutip di `GOALS_V3.md`) dihitung
**tanpa** filter J4. Keputusan G11: **561** dipakai konsisten di kartu nasional maupun tabel
per-unit, supaya keduanya selalu bisa saling dijumlahkan cocok di halaman — kartu nasional
701 berdampingan dengan tabel yang cuma berjumlah 561 akan terlihat seperti galat tanpa
penjelasan apa pun yang boleh ditulis di UI (P2). Rinciannya di `docs/CATATAN_DATA.md` J8.

**Per unit — 47 baris.** Lima gap terbesar:

```
UID Jawa Barat            59
Kantor Pusat              55
P3B Sumatera              50
UIW Papua&Papua Barat     43
UID Jawa Timur            41
```

Lima terkecil (realisasi melebihi formasi — gap negatif):

```
UIW NusaTenggaraTimur     -5
UID Sumut                -13
UID Riau & Kepri         -21
UID Jawa Tengah & DIY   -138
```

**Cek silang J4:** tanpa filter, baris duplikat (gap=140) akan menempati **peringkat 1**
secara palsu. Dengan filter, peringkat 1 adalah UID Jawa Barat (gap=59) — unit sungguhan.

---

## M11 · `usulan_vs_pagu() -> DataFrame`

**Definisi bisnis:** berapa yang diusulkan unit (kekosongan + gap FTK) dibanding berapa yang
disetujui pusat sebagai pagu, per tahun program.

### SQL

```sql
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
```

### Keluaran nyata

**2019–2025** (7 baris, `usulan_kebutuhan` dan `pagu_rekrutmen` sama-sama berhenti di 2025):

```
   tahun    pagu  usulan  pct_disetujui
0   2019  1093.0  3099.0           35.3
1   2020   325.0  2528.0           12.9
2   2021   689.0  2313.0           29.8
3   2022   689.0  2023.0           34.1
4   2023  1277.0  1816.0           70.3
5   2024  1098.0  1741.0           63.1
6   2025  1050.0  1238.0           84.8
```

2025 cocok dengan angka `docs/RANCANGAN_HALAMAN.md` §4: 906 kekosongan + 333 gap FTK =
**1.238 usulan** → pagu **1.050**.

Persentase disetujui **naik** dari 2019 ke 2025 (35,3% → 84,8%) — dilaporkan apa adanya,
bukan ditafsirkan di dokumen ini (penafsiran ada di halaman/laporan, bukan di kamus metrik).

---

## Yang belum ada di modul ini

Halaman 3–7 belum punya metrik sama sekali — itu lingkup G12–G16, tiap goal menambah
metriknya sendiri ke `core/metrics.py` dan bagian barunya ke dokumen ini.

Metrik Beranda (M01–M04) **belum dipakai halaman mana pun saat ditulis** — sudah dipakai
sejak `app_pages/beranda.py` dibangun di G10. Metrik Perencanaan Formasi (M05–M11) dipakai
`app_pages/perencanaan.py`, dibangun di G11.
