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

## C. Seleksi Berjalan (halaman 3, G12)

Berbeda dari M01–M04 (Beranda), yang melintasi seluruh gelombang: metrik di bawah selalu
dipersempit ke satu `gelombang_id` — pertanyaannya "gelombang yang sedang jalan sudah sampai
mana?", bukan potret nasional. `seleksi_tahap` sudah terbatas ke `kategori='seleksi'` (enam
tahap, urutan 1–6) — baris `fhci_agregat` dan `pasca` tidak pernah masuk tabel ini, jadi tidak
perlu filter kategori tambahan.

Dua tanggal acuan dipakai konsisten di seluruh bagian ini:

- **2026-08-23** (hari ini) — tidak ada gelombang terbuka, jalur keadaan kosong.
- **2025-10-03** — `G2025-092` terbuka (`tgl_buka=2025-10-01`, `tgl_tutup=2025-10-05`), jalur
  gelombang aktif.

## M12 · `gelombang_terbuka(acuan=None) -> DataFrame`

**Definisi bisnis:** gelombang yang pendaftarannya sedang terbuka pada tanggal acuan.

### SQL

```sql
SELECT gelombang_id, nama_gelombang, tgl_buka, tgl_tutup,
       date_diff('day', CAST(? AS DATE), tgl_tutup) AS hari_tersisa,
       n_profesi, diterima_target
FROM gelombang
WHERE tgl_buka <= ? AND tgl_tutup >= ?
ORDER BY tgl_tutup
```

### Keluaran nyata

**acuan=2026-08-23** (0 baris — tidak ada gelombang terbuka, benar per P3: gelombang terakhir
`G2025-092` tutup 2025-10-05, jauh sebelum hari ini):

```
Empty DataFrame
Columns: [gelombang_id, nama_gelombang, tgl_buka, tgl_tutup, hari_tersisa, n_profesi, diterima_target]
```

**acuan=2025-10-03** (1 baris):

```
  gelombang_id                                        nama_gelombang   tgl_buka  tgl_tutup  hari_tersisa  n_profesi  diterima_target
0    G2025-092  REKRUTMEN PLN GROUP TINGKAT S1/D4 DAN D3 TAHUN 2025 2025-10-01 2025-10-05             2         12             1021
```

---

## M13 · `profesi_gelombang(gelombang_id) -> DataFrame`

**Definisi bisnis:** profesi yang dibuka pada satu gelombang.

### SQL

```sql
SELECT nama_profesi, jenjang, kota_rekrutmen, kuota
FROM profesi
WHERE gelombang_id = ?
ORDER BY nama_profesi
```

### Keluaran nyata

`profesi_gelombang('G2025-092')` → **12 baris**, kolom `nama_profesi, jenjang,
kota_rekrutmen, kuota`. Seluruh 12 baris `kota_rekrutmen = 'Seluruh Indonesia'` (bukan salah
satu dari lima kolom acak seragam J1 — `kota_rekrutmen` bukan `kota_domisili`/`kota_asal`,
nilainya memang seragam untuk gelombang rekrutmen nasional, bukan bug generator). Contoh dua
baris pertama:

```
                                          nama_profesi  jenjang     kota_rekrutmen  kuota
0  Proyeksi PLN GROUP - S1 Hukum - Lokasi Penempatan...  S1/D-IV  Seluruh Indonesia     39
1  Proyeksi PLN GROUP - S2 Hukum/Non Hukum dengan La...       S2  Seluruh Indonesia     16
```

---

## M14 · `posisi_tahap_seleksi(gelombang_id, acuan=None) -> DataFrame`

**Definisi bisnis:** berapa peserta menunggu di tiap tahap seleksi, berapa yang tahapnya
sudah lewat — dihitung dari `seleksi_tahap.tanggal_tahap` terhadap acuan, bukan dari kolom
status beku manapun.

### SQL

```sql
SELECT r.urutan, st.tahap_kode, r.nama,
       count(*) AS jumlah,
       CAST(sum(CASE WHEN st.tanggal_tahap > ? THEN 1 ELSE 0 END) AS BIGINT) AS menunggu,
       CAST(sum(CASE WHEN st.tanggal_tahap <= ? THEN 1 ELSE 0 END) AS BIGINT) AS sudah_lewat
FROM seleksi_tahap st
JOIN tahap_ref r USING (tahap_kode)
WHERE st.gelombang_id = ?
GROUP BY 1, 2, 3
ORDER BY 1
```

### Keluaran nyata

**acuan=2025-10-03** (2025-10-03 jatuh sebelum tahap seleksi manapun mulai — administrasi
baru mulai 2025-10-08 — jadi seluruhnya masih "menunggu"):

```
   urutan        tahap_kode                                 nama  jumlah  menunggu  sudah_lewat
0       1      administrasi                 Seleksi Administrasi   49801     49801            0
1       2           adaptif                Tes Adaptif PLN (TAP)   31178     31178            0
2       3  akademik_inggris  Tes Akademik (TKB) & Bahasa Inggris    9418      9418            0
3       4         psikologi                        Tes Psikologi    3406      3406            0
4       5         fisik_mcu         Tes Fisik & Medical Check-Up    1658      1658            0
5       6         wawancara                  Wawancara User & HR    1259      1259            0
```

**acuan=2026-01-01** (administrasi s.d. psikologi sudah lewat; fisik_mcu mulai 2026-01-05,
wawancara mulai 2026-01-31 — keduanya masih menunggu):

```
administrasi : sudah_lewat = 49801
psikologi    : sudah_lewat = 3406
fisik_mcu    : sudah_lewat = 0, menunggu = 1658
```

---

## M15 · `jadwal_tahap_berikutnya(gelombang_id, acuan=None) -> DataFrame`

**Definisi bisnis:** tahap seleksi terdekat berikutnya sesudah acuan pada satu gelombang —
tahap apa, tanggal berapa, di kota mana, vendor siapa. Satu baris per kombinasi kota/vendor
pada tanggal terdekat itu, karena satu tahap bisa dijalankan serentak di beberapa kota dengan
vendor berbeda.

### SQL

```sql
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
```

### Keluaran nyata

**acuan=2025-10-03** (1 baris — administrasi tidak punya `lokasi_kota`/`vendor_id` terisi,
diproses terpusat, bukan bug):

```
   tahap_kode            nama_tahap tanggal_tahap lokasi_kota vendor  jumlah
0  administrasi  Seleksi Administrasi    2025-10-08        None   None    2644
```

**acuan=2026-03-01** (sesudah jadwal terakhir gelombang ini — wawancara berakhir
2026-02-16): kosong. Jawaban yang benar, bukan galat.

---

## M16 · `kehadiran_tahap_terakhir(gelombang_id, acuan=None) -> dict | None`

**Definisi bisnis:** kehadiran pada tahap seleksi terakhir yang sudah lewat, untuk satu
gelombang — sinyal paling dini kalau ada yang tidak beres. Hanya menghitung tahap yang
memang punya konsep kehadiran (`tahap_ref.ada_kehadiran`); Seleksi Administrasi berbasis
dokumen, tidak ada sesi hadir/tidak hadir. `None` kalau belum ada satu pun tahap
berkehadiran yang lewat.

### SQL

```sql
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
```

### Keluaran nyata

**acuan=2025-10-03** → `None`. Belum ada tahap berkehadiran yang lewat (administrasi, satu-
satunya tahap yang sudah lewat pada tanggal ini, `ada_kehadiran=False`).

**acuan=2026-01-01** (membuktikan jalur berisi benar-benar berjalan, bukan cuma jalur
`None`): psikologi berakhir 2025-12-26, jadi itulah tahap berkehadiran terakhir yang lewat:

```python
{'tahap_kode': 'psikologi', 'nama': 'Tes Psikologi',
 'tanggal_tahap': Timestamp('2025-12-26'), 'hadir': 268, 'tidak_hadir': 33, 'total': 301}
```

---

## M17 · `gelombang_terakhir_selesai(acuan=None) -> dict | None`

**Definisi bisnis:** gelombang paling baru yang pendaftarannya sudah tutup sebelum acuan,
beserta hasil akhirnya — dipakai keadaan kosong Halaman 3 supaya halaman tetap berguna saat
tidak ada gelombang terbuka.

`hasil_akhir` di `pendaftaran` adalah keputusan final per pelamar (`DITERIMA`/`GAGAL`),
bukan status berjalan yang beku — aman dibaca apa adanya, beda dengan `pasca_tahap.status`
(§4.1 ATURAN_TAMPILAN.md) yang menyatakan status sesaat generate dan bisa salah di masa depan.

### SQL

```sql
-- gelombang
SELECT gelombang_id, nama_gelombang, tgl_tutup
FROM gelombang
WHERE tgl_tutup < ?
ORDER BY tgl_tutup DESC
LIMIT 1

-- hasil, dipanggil dengan gelombang_id hasil query di atas
SELECT count(*) AS pendaftar,
       CAST(sum(CASE WHEN hasil_akhir = 'DITERIMA' THEN 1 ELSE 0 END) AS BIGINT) AS diterima,
       CAST(sum(CASE WHEN hasil_akhir = 'GAGAL' THEN 1 ELSE 0 END) AS BIGINT) AS gagal
FROM pendaftaran
WHERE gelombang_id = ?
```

### Keluaran nyata

**acuan=2026-08-23:**

```python
{'gelombang_id': 'G2025-092', 'nama_gelombang': 'REKRUTMEN PLN GROUP TINGKAT S1/D4 DAN D3 TAHUN 2025',
 'tgl_tutup': Timestamp('2025-10-05'), 'pendaftar': 49801, 'diterima': 1021, 'gagal': 48780}
```

**acuan=2025-10-03** (pada tanggal ini `G2025-092` sendiri masih terbuka, belum "selesai" —
gelombang terakhir yang sudah tutup adalah gelombang sebelumnya):

```python
{'gelombang_id': 'G2025-091', ...}
```

---

## M18 · `gugur_per_tahap_gelombang(gelombang_id) -> DataFrame`

**Definisi bisnis:** sebaran pelamar gugur per tahap, untuk satu gelombang yang sudah selesai
diproses — melengkapi M17 untuk menjawab "lolos/gugur sampai tahap mana". Hanya pelamar
dengan `hasil_akhir = 'GAGAL'` — keputusan final, bukan snapshot berjalan.

### SQL

```sql
SELECT r.urutan, p.tahap_gugur AS tahap_kode, r.nama, count(*) AS jumlah
FROM pendaftaran p
JOIN tahap_ref r ON r.tahap_kode = p.tahap_gugur
WHERE p.gelombang_id = ? AND p.hasil_akhir = 'GAGAL'
GROUP BY 1, 2, 3
ORDER BY 1
```

### Keluaran nyata

`gugur_per_tahap_gelombang('G2025-092')` → 6 baris, jumlah totalnya **48.780** — cocok persis
dengan `gagal` di M17:

```
   urutan        tahap_kode                                 nama  jumlah
0       1      administrasi                 Seleksi Administrasi   18623
1       2           adaptif                Tes Adaptif PLN (TAP)   21760
2       3  akademik_inggris  Tes Akademik (TKB) & Bahasa Inggris    6012
3       4         psikologi                        Tes Psikologi    1748
4       5         fisik_mcu         Tes Fisik & Medical Check-Up     399
5       6         wawancara                  Wawancara User & HR     238
```

---

## D. Corong Seleksi (halaman 4, G13)

Analisis **lintas gelombang** — beda dari M12–M18 (halaman 3), yang membaca satu gelombang
yang sedang berjalan pada tanggal acuan. Di sini pertanyaannya "di tahap mana orang hilang,
dan kenapa?" atas riwayat yang sudah tuntas, jadi tidak terikat `hari_ini()`.

---

## M19 · `corong_tahap_seleksi(gelombang_id=None) -> DataFrame`

**Definisi bisnis:** corong enam tahap seleksi mandiri (Administrasi → Wawancara), seluruh
gelombang atau satu gelombang terpilih. Memisahkan `hadir`/`tidak_hadir` dari `lulus`/`gagal`
supaya UI bisa memisahkan "gugur karena gagal" dari "gugur karena tidak hadir".

### SQL

```sql
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
```

### Keluaran nyata

`corong_tahap_seleksi()` (seluruh gelombang) — cocok persis dengan angka anchor rancangan:

```
   urutan        tahap_kode                                 nama   masuk  hadir  tidak_hadir   lulus  gagal
0       1      administrasi                 Seleksi Administrasi  213648      0            0  143831  69817
1       2           adaptif                Tes Adaptif PLN (TAP)  143831  68896        74935   48627  95204
2       3  akademik_inggris  Tes Akademik (TKB) & Bahasa Inggris   53907  44358         9549   24699  29208
3       4         psikologi                        Tes Psikologi   24699  22651         2048   15980   8719
4       5         fisik_mcu         Tes Fisik & Medical Check-Up   15980  14826         1154   12623   3357
5       6         wawancara                  Wawancara User & HR   12623  11859          764    7711   4912
```

`corong_tahap_seleksi('G2025-092')` — total gagal 48.780, cocok persis M18:

```
   urutan        tahap_kode                                 nama  masuk  hadir  tidak_hadir  lulus  gagal
0       1      administrasi                 Seleksi Administrasi  49801      0            0  31178  18623
1       2           adaptif                Tes Adaptif PLN (TAP)  31178  14102        17076   9418  21760
2       3  akademik_inggris  Tes Akademik (TKB) & Bahasa Inggris   9418   7494         1924   3406   6012
3       4         psikologi                        Tes Psikologi   3406   2977          429   1658   1748
4       5         fisik_mcu         Tes Fisik & Medical Check-Up   1658   1535          123   1259    399
5       6         wawancara                  Wawancara User & HR   1259   1190           69   1021    238
```

`administrasi` tidak punya kehadiran — `hadir`/`tidak_hadir` selalu 0, bukan `NULL`; UI wajib
membedakan ini dari "0% tidak hadir" (tahap itu memang tidak punya konsep kehadiran sama
sekali, seleksi berbasis dokumen).

---

## M20 · `no_show_per_tahap_mode() -> DataFrame`

**Definisi bisnis:** persentase tidak hadir per tahap seleksi × mode pelaksanaan, seluruh
gelombang — temuan inti halaman ini. Seleksi Administrasi tidak muncul (tidak berkehadiran).

### SQL

```sql
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
```

### Keluaran nyata

```
   urutan        tahap_kode                                 nama     mode  tidak_hadir   total  pct_no_show
0       2           adaptif                Tes Adaptif PLN (TAP)   online        74935  143831         52.1
1       3  akademik_inggris  Tes Akademik (TKB) & Bahasa Inggris   online         9549   53907         17.7
2       4         psikologi                        Tes Psikologi  offline         2048   24699          8.3
3       5         fisik_mcu         Tes Fisik & Medical Check-Up  offline         1154   15980          7.2
4       6         wawancara                  Wawancara User & HR  offline          764   12623          6.1
```

Cocok persis dengan angka anchor rancangan: Tes Adaptif online **52,1%** tidak hadir, jauh di
atas seluruh tahap offline (6,1–8,3%). `mode` berpola benar (CATATAN_DATA.md §5), jadi temuan
ini kokoh meski `kota_domisili` cacat.

---

## M21 · `rbb_masuk_akademik_inggris(gelombang_id=None) -> int`

**Definisi bisnis:** jumlah pelamar yang masuk sistem PLN langsung di tahap Akademik &
Inggris — titik serah-terima dari jalur RBB (FHCI), yang sudah disaring FHCI sebelum
diserahkan ke PLN.

### SQL

```sql
SELECT count(*) FROM pendaftaran
WHERE titik_masuk = 'akademik_inggris'
  AND (CAST(? AS VARCHAR) IS NULL OR gelombang_id = ?)
```

### Keluaran nyata

`rbb_masuk_akademik_inggris()` (seluruh gelombang) → **5.280** — persis sama dengan selisih
`masuk` tahap Akademik & Inggris (53.907) dikurangi `lulus` Tes Adaptif (48.627) di M19.
`pendaftaran.titik_masuk` adalah penanda langsung untuk aliran ini, dipakai alih-alih
menghitung selisih dua angka funnel yang terpisah.

Per gelombang, hanya empat gelombang RBB yang punya nilai bukan nol:

```
gelombang_id  jumlah
G2020-074        455
G2021-075        179
G2024-087       3599
G2024-088       1047
```

Gelombang mandiri lain (mis. `G2025-092`) mengembalikan **0** — jawaban yang benar, bukan
galat; gelombang itu tidak punya jalur RBB.

---

## M22 · `corong_fhci() -> DataFrame`

**Definisi bisnis:** corong agregat tiga tahap FHCI, dijumlah lintas tahun program (2020,
2021, 2024) — fakta struktural terpisah dari corong jalur mandiri, karena
`seleksi_tahap_agregat` **tidak punya `kandidat_id`/`pendaftaran_id`** (CATATAN_DATA.md J7).
JOIN langsung ke `pendaftaran` melipatgandakan hasil 3× — tidak pernah dilakukan di sini.

### SQL

```sql
SELECT urutan, tahap_kode, nama,
       CAST(sum(jumlah_masuk) AS BIGINT) AS masuk,
       CAST(sum(jumlah_lulus) AS BIGINT) AS lulus,
       round(100.0 * sum(jumlah_lulus) / sum(jumlah_masuk), 1) AS pct_lulus
FROM seleksi_tahap_agregat
GROUP BY 1, 2, 3
ORDER BY 1
```

### Keluaran nyata

```
   urutan         tahap_kode                                     nama   masuk   lulus  pct_lulus
0      -3  fhci_administrasi              Seleksi Administrasi (FHCI)  269395  107758       40.0
1      -2  fhci_tes_online_1           Tes Online 1: TKD, AKHLAK, TWK  107758   30172       28.0
2      -1  fhci_tes_online_2  Tes Online 2: Inggris, Learning Agility   30172    5280       17.5
```

`lulus` tahap terakhir (5.280) sama persis dengan M21 — dua sumber independen menyatakan
angka yang sama, titik serah-terima ini konsisten dari kedua sisi.

---

## M23 · `daftar_gelombang() -> DataFrame`

**Definisi bisnis:** seluruh gelombang 2019–2025, untuk pemilih pembanding corong antar
gelombang. Beda dari `gelombang_terbuka()` (M12, halaman 3) yang hanya gelombang yang sedang
buka — di sini seluruh 19 gelombang historis boleh dipilih, karena halaman ini analisis
lintas gelombang, bukan snapshot hari ini.

### SQL

```sql
SELECT gelombang_id, nama_gelombang, tgl_tutup
FROM gelombang
ORDER BY tgl_tutup DESC
```

### Keluaran nyata

19 baris, dari `G2025-092` (tutup 2025-10-05) sampai `G2019-070` (tutup 2019-07-25).

---

## M24 · `daftar_kohort_pasca() -> DataFrame`

**Definisi bisnis:** seluruh kohort (satu kohort = satu gelombang) yang punya jejak
pasca-seleksi, terbaru dulu — sumber pemilih kohort di Halaman 5.

### SQL

```sql
SELECT pt.gelombang_id, g.nama_gelombang,
       CAST(count(DISTINCT pt.pendaftaran_id) AS BIGINT) AS peserta,
       min(pt.tanggal_mulai) AS tanggal_mulai,
       max(pt.tanggal_selesai) AS tanggal_terakhir
FROM pasca_tahap pt
JOIN gelombang g USING (gelombang_id)
GROUP BY 1, 2
ORDER BY tanggal_mulai DESC
```

### Keluaran nyata

17 kohort, dari `G2025-092` (mulai 2026-02-27, terakhir 2026-10-15, 1.021 orang) sampai
`G2019-070` (mulai 2019-12-17, terakhir 2020-08-28, 267 orang). Dua kohort terbaru:

```
gelombang_id  nama_gelombang                                              peserta  tanggal_mulai  tanggal_terakhir
G2025-092     REKRUTMEN PLN GROUP TINGKAT S1/D4 DAN D3 TAHUN 2025            1021     2026-02-27        2026-10-15
G2025-091     REKRUTMEN PUTRA-PUTRI ASLI PAPUA PLN GROUP TAHUN 2025           979     2026-02-13        2026-10-01
```

`tanggal_terakhir` kohort 2025 berhenti di selesainya OJT (2026-10-01 / 2026-10-15) — bukan
di SK penempatan, karena `ujian_ojt` dan `sk_penempatan` belum punya satu baris pun untuk
kedua kohort ini (J9).

---

## M25 · `kohort_relevan(acuan=None) -> str`

**Definisi bisnis:** kohort paling relevan untuk dibuka pertama kali pada tanggal acuan —
default pemilih kohort di Halaman 5. Prioritas: kohort yang jendela pasca-nya mencakup
acuan, dipilih yang paling baru mulai; kalau tidak ada yang sedang berjalan, kohort terakhir
yang jendelanya sudah lewat sebelum acuan; kalau acuan lebih awal dari kohort mana pun,
kohort paling awal.

### Implementasi

Dibangun di atas `daftar_kohort_pasca()` (M24), disaring lewat pandas — bukan SQL baru;
tabelnya sudah teragregasi jadi 17 baris, aman dinalar di memori.

### Keluaran nyata

```python
kohort_relevan(date(2026, 8, 23))  # -> 'G2025-092' (kedua kohort 2025 sedang OJT)
kohort_relevan(date(2027, 1, 6))   # -> 'G2025-092' (masih dalam jendela sampai 2026-10-15)
kohort_relevan(date(2025, 3, 1))   # -> 'G2024-088' (satu-satunya yang sedang berjalan)
kohort_relevan(date(2019, 1, 1))   # -> 'G2019-070' (sebelum kohort mana pun mulai)
```

---

## M26 · `lini_masa_pasca_kohort(gelombang_id, acuan=None) -> DataFrame`

**Definisi bisnis:** posisi satu kohort di ketujuh tahap pasca-seleksi pada tanggal acuan —
jawaban langsung "sekarang prosesnya di mana?". `selesai`/`berjalan`/`belum_mulai` dihitung
dari tanggal, bukan dari `pasca_tahap.status` yang beku (ATURAN_TAMPILAN.md §4.1). LEFT JOIN
dari `tahap_ref` membuat tahap yang belum punya baris sama sekali tetap tampil dengan
`peserta = 0`, alih-alih hilang dari tabel — ini mekanisme rekonsiliasi J9.

### SQL

```sql
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
```

### Keluaran nyata

`lini_masa_pasca_kohort('G2025-091', acuan=date(2026, 8, 23))`:

```
urutan  tahap_kode         nama                            peserta  tanggal_mulai  tanggal_selesai  selesai  berjalan  belum_mulai
   100  pengumuman_akhir   Pengumuman Hasil Seleksi             979     2026-02-13       2026-02-13      979         0            0
   101  ttd_kontrak        Penandatanganan Perjanjian           979     2026-02-23       2026-03-08      979         0            0
   102  samapta            SAMAPTA                               979     2026-03-15       2026-03-29      979         0            0
   103  pembidangan        Penetapan Pembidangan                979     2026-03-30       2026-03-30      979         0            0
   104  ojt                Diklat Prajabatan / First OJT        979     2026-04-04       2026-10-01        0       979            0
   105  ujian_ojt          Ujian Akhir OJT                         0            NaT              NaT        0         0            0
   106  sk_penempatan      SK Pengangkatan & Penempatan            0            NaT              NaT        0         0            0
```

Baris `ojt` tuntas (`selesai` akan jadi 979 begitu acuan lewat 2026-10-01), sementara
`ujian_ojt` dan `sk_penempatan` tetap `peserta = 0` **berapa pun acuan yang dicoba** — selisih
979 yang menggantung terlihat langsung di tabel, tanpa fungsi tambahan.

Sebagai pembanding, kohort lama `G2024-088` (acuan 2025-03-01, SAMAPTA masih berjalan) punya
ketujuh baris terisi penuh, termasuk `ujian_ojt`/`sk_penempatan` — bukti bahwa J9 memang
spesifik pada kohort 2025, bukan cacat query:

```
urutan  tahap_kode      peserta  selesai  berjalan  belum_mulai
   102  samapta             288      268         0           20
   103  pembidangan         288        0         0          288
   104  ojt                 288        0         0          288
   105  ujian_ojt           288        0         0          288
   106  sk_penempatan       288        0         0          288
```

---

## M27 · `status_samapta_kohort(gelombang_id) -> dict | None`

**Definisi bisnis:** jendela pelaksanaan SAMAPTA untuk satu kohort — jumlah peserta, kapan
mulai, kapan selesai, berapa lama. Tidak ada kolom lokasi di sumber data; halaman tidak
menampilkan/mengasumsikan lokasi pelaksanaan.

### SQL

```sql
SELECT CAST(count(*) AS BIGINT) AS peserta,
       min(tanggal_mulai) AS tanggal_mulai,
       max(tanggal_selesai) AS tanggal_selesai,
       date_diff('day', min(tanggal_mulai), max(tanggal_selesai)) AS durasi_hari
FROM pasca_tahap
WHERE tahap_kode = 'samapta' AND gelombang_id = ?
```

### Keluaran nyata

```python
status_samapta_kohort('G2025-091')
# {'peserta': 979, 'tanggal_mulai': 2026-03-15, 'tanggal_selesai': 2026-03-29, 'durasi_hari': 14}
status_samapta_kohort('G2025-092')
# {'peserta': 1021, 'tanggal_mulai': 2026-03-29, 'tanggal_selesai': 2026-04-12, 'durasi_hari': 14}
```

`durasi_hari` konstan 14 di kedua kohort — sesuai temuan rentang tahap yang konstan lintas
kohort (RANCANGAN_HALAMAN.md §7); tidak bermakna dibandingkan antar kohort, hanya
dilaporkan sebagai fakta jendela kohort yang sedang dilihat.

---

## M28 · `pembidangan_per_kohort(gelombang_id) -> DataFrame`

**Definisi bisnis:** sebaran bidang pembidangan untuk satu kohort.

### SQL

```sql
SELECT pe.bidang_pembidangan, CAST(count(*) AS BIGINT) AS jumlah
FROM penempatan pe
JOIN pendaftaran p USING (pendaftaran_id)
WHERE p.gelombang_id = ?
GROUP BY 1
ORDER BY 2 DESC
```

### Keluaran nyata

`pembidangan_per_kohort('G2025-091')` (979 orang, 9 bidang):

```
bidang_pembidangan                     jumlah
SDM                                       232
Distribusi                                179
Transmisi dan Gardu Induk                 131
Niaga                                     104
Manajemen Konstruksi dan Pengadaan         99
Keuangan                                   84
Pembangkitan                               78
Perencanaan Sistem                         41
Proteksi dan Kontrol                       31
```

Gabungan kedua kohort 2025 (091+092) sesuai anchor rancangan: Pembangkitan 481, SDM 362,
Distribusi 258, Transmisi & GI 215, Konstruksi 197, Keuangan 169, Niaga 165, Perencanaan
Sistem 91, Proteksi & Kontrol 62 — diverifikasi lewat penjumlahan manual kedua kohort di
`../.venv/Scripts/python.exe`, cocok persis dengan brief goal.

---

## M29 · `ojt_per_updl_kohort(gelombang_id) -> DataFrame`

**Definisi bisnis:** sebaran peserta OJT per UPDL untuk satu kohort — berguna untuk
pertanyaan kapasitas diklat.

### SQL

```sql
SELECT u.nama AS nama_updl, CAST(coalesce(count(pe.penempatan_id), 0) AS BIGINT) AS jumlah
FROM updl u
LEFT JOIN (
    SELECT pe.* FROM penempatan pe
    JOIN pendaftaran p USING (pendaftaran_id)
    WHERE p.gelombang_id = ?
) pe ON pe.updl_id = u.updl_id
GROUP BY 1
ORDER BY 2 DESC
```

### Keluaran nyata

`ojt_per_updl_kohort('G2025-091')` — 11 baris (seluruh UPDL selalu tampil, P5):

```
nama_updl        jumlah
UPDL Pandaan         122
UPDL Surabaya         122
UPDL Semarang         120
UPDL Palembang         97
UPDL Padang            84
UPDL Jakarta           81
UPDL Makassar          77
UPDL Tuntungan         75
UPDL Banjarbaru        69
UPDL Suralaya          66
UPDL Bogor             66
```

Gabungan kedua kohort 2025 sesuai anchor rancangan: Semarang 257, Pandaan 234, Surabaya 228,
Tuntungan 201, Palembang 195, Padang 162, Makassar 158, Jakarta 152, Bogor 141, Suralaya
136, Banjarbaru 136 — diverifikasi lewat penjumlahan manual kedua kohort.

---

## M30 · `status_sk_kohort(gelombang_id, acuan=None) -> dict`

**Definisi bisnis:** berapa SK penempatan sudah terbit dan berapa masih menunggu, untuk satu
kohort. `terbit` dihitung dari baris `pasca_tahap` tahap `sk_penempatan` yang sudah lewat
acuan — bukan dari kolom `penempatan.status_sk` yang beku saat data digenerate, supaya
konsisten dengan aturan realtime §4.1 yang sama berlaku di seluruh halaman ini.

### SQL

```sql
WITH total AS (
    SELECT count(DISTINCT pendaftaran_id) AS n FROM pasca_tahap WHERE gelombang_id = ?
),
terbit AS (
    SELECT count(*) AS n FROM pasca_tahap
    WHERE gelombang_id = ? AND tahap_kode = 'sk_penempatan' AND tanggal_selesai <= ?
)
SELECT total.n AS total, terbit.n AS terbit, total.n - terbit.n AS menunggu
FROM total, terbit
```

### Keluaran nyata

```python
status_sk_kohort('G2025-091', acuan=date(2026, 8, 23))  # {'total': 979, 'terbit': 0, 'menunggu': 979}
status_sk_kohort('G2025-091', acuan=date(2027, 1, 6))   # {'total': 979, 'terbit': 0, 'menunggu': 979}
status_sk_kohort('G2024-088', acuan=date(2026, 8, 23))  # {'total': 288, 'terbit': 288, 'menunggu': 0}
```

Kohort 2025 tetap `terbit = 0` di kedua acuan yang dicoba, termasuk yang jauh melewati
horison data (2027-01-06) — konsisten dengan M26: tidak ada satu baris `sk_penempatan` pun
untuk kohort ini, jadi `terbit` tidak akan pernah bergerak berapa pun acuan dimajukan.

---

## M31 · `unit_tujuan_sk_kohort(gelombang_id) -> DataFrame`

**Definisi bisnis:** unit tujuan penempatan untuk satu kohort, hanya yang sudah punya unit.

### SQL

```sql
SELECT u.nama_pendek, CAST(count(*) AS BIGINT) AS jumlah
FROM penempatan pe
JOIN pendaftaran p USING (pendaftaran_id)
JOIN unit_induk u ON u.unit_induk = pe.unit_induk
WHERE p.gelombang_id = ?
GROUP BY 1
ORDER BY 2 DESC
```

### Keluaran nyata

`unit_tujuan_sk_kohort('G2025-091')` → **DataFrame kosong** — unit penempatan kohort 2025
memang belum diputuskan sama sekali (2.000 baris `unit_induk IS NULL` di `penempatan`),
keadaan proses nyata, bukan data hilang.

`unit_tujuan_sk_kohort('G2024-088')` → 45 unit terisi, lima teratas:

```
nama_pendek        jumlah
Kantor Pusat            38
UID Jawa Timur          17
UIW Maluku&Malut        16
UID Jawa Barat          15
UIT JBT                 14
```

---

## Yang belum ada di modul ini

Halaman 6–7 belum punya metrik sama sekali — itu lingkup G15–G16, tiap goal menambah
metriknya sendiri ke `core/metrics.py` dan bagian barunya ke dokumen ini.

Metrik Beranda (M01–M04) dipakai `app_pages/beranda.py`, dibangun di G10. Metrik Perencanaan
Formasi (M05–M11) dipakai `app_pages/perencanaan.py`, dibangun di G11. Metrik Seleksi
Berjalan (M12–M18) dipakai `app_pages/seleksi.py`, dibangun di G12. Metrik Corong Seleksi
(M19–M23) dipakai `app_pages/corong.py`, dibangun di G13. Metrik Pasca-Seleksi (M24–M31)
dipakai `app_pages/pasca.py`, dibangun di G14.
