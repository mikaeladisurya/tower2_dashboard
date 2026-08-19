# Kamus Metrik — Dashboard Rekrutmen PLN v2

Kontrak bersama antara halaman dashboard dan chatbot. **Setiap angka yang tampil di
dashboard harus berasal dari salah satu metrik di sini**, diimplementasikan sekali di
`core/metrics.py`. Kalau halaman butuh angka baru, tambahkan metriknya di sini dulu.

Semua SQL di dokumen ini **sudah dijalankan dan diverifikasi** terhadap
`mockdb/out/rekrutmen.duckdb` pada 19 Agustus 2026. Kolom "Hasil" adalah keluaran nyata.

---

## Konvensi

| Hal | Aturan |
|---|---|
| Tanggal potong | **15 September 2026** — semua status relatif ke tanggal ini |
| Kunci waktu | `tahun_program` (tahun gelombang dibuka), **bukan** tahun masuk kerja |
| Jalur | `sumber_rekrutmen` ∈ {`mandiri`, `rbb`} — atribut, bukan tabel terpisah |
| "Diterima" | `pendaftaran.hasil_akhir = 'DITERIMA'` — **bukan** berarti sudah ber-SK |
| "Sudah SK" | `penempatan.status_sk = 'SUDAH'` |
| Badge sumber | `NYATA` · `DIMODELKAN` · `AGREGAT` (FHCI, tanpa identitas) |

### Tiga angka yang sering tertukar

```
7.711  DITERIMA        lulus seluruh tahap seleksi
5.711  SUDAH BER-SK    sudah SK pengangkatan
2.000  SEDANG OJT      kohort 2025, SK menyusul
```

Selisih 7.711 − 5.711 = 2.000 **bukan kebocoran data** — itu pipeline yang memang sedang
berjalan pada tanggal potong. Ini kesalahan interpretasi paling mudah terjadi; label di
UI harus selalu eksplisit.

---

## A. Metrik ringkasan (Halaman 1)

### M01 · Total pendaftaran — `NYATA` — **218.928**
```sql
SELECT count(*) AS pendaftaran FROM pendaftaran
```

### M02 · Pelamar unik — `NYATA` — **172.389**
```sql
SELECT count(DISTINCT kandidat_id) AS pelamar FROM pendaftaran
```

### M03 · Total akun — `NYATA` — **368.912 akun, 172.389 pernah melamar**
```sql
SELECT count(*) AS akun,
       sum(CASE WHEN pernah_melamar THEN 1 ELSE 0 END) AS pernah_melamar
FROM kandidat
```
> 196.523 akun tidak pernah mengirim satu lamaran pun — bahan cerita tentang funnel
> paling atas yang biasanya tidak terlihat.

### M04 · Diterima — `NYATA` — **7.711**
```sql
SELECT count(*) AS diterima FROM pendaftaran WHERE hasil_akhir = 'DITERIMA'
```

### M05 · Rasio seleksi — `NYATA` — **28,4 pendaftaran per 1 diterima**
```sql
SELECT round(count(*)*1.0 / nullif(sum(CASE WHEN hasil_akhir='DITERIMA' THEN 1 END),0),1)
       AS pelamar_per_diterima
FROM pendaftaran
```
> Tampilkan sebagai **1 : 28**. Catatan: riset menyebut 1:49 (mandiri) dan 1:186 (RBB
> nasional) — angka database lebih rendah karena pendaftaran RBB yang tercatat di PLN hanya
> yang sudah lolos FHCI (lihat M29).

### M06 · Sudah ber-SK — `NYATA` — **5.711**
```sql
SELECT count(*) AS sudah_sk FROM penempatan WHERE status_sk = 'SUDAH'
```

### M07 · Sedang OJT — `NYATA` — **2.000**
```sql
SELECT count(*) AS sedang_ojt FROM pasca_tahap WHERE tahap_kode='ojt' AND status='BERJALAN'
```

### M11 · Tren tahunan — `NYATA`
```sql
SELECT g.tahun_program, g.sumber_rekrutmen, count(*) AS pendaftaran,
       sum(CASE WHEN p.hasil_akhir='DITERIMA' THEN 1 ELSE 0 END) AS diterima
FROM pendaftaran p JOIN gelombang g USING (gelombang_id)
GROUP BY 1,2 ORDER BY 1
```

| tahun | jalur | pendaftaran | diterima |
|---|---|---:|---:|
| 2019 | mandiri | 66.014 | 1.353 |
| 2020 | rbb | 455 | 125 |
| 2021 | rbb | 179 | 49 |
| 2022 | mandiri | 54.100 | 1.109 |
| 2023 | mandiri | 38.538 | 1.797 |
| 2024 | rbb | 4.646 | 1.278 |
| 2025 | mandiri | 54.996 | 2.000 |

> ⚠️ Tahun RBB (2020, 2021, 2024) **tidak boleh dibandingkan langsung** dengan tahun
> mandiri pada sumbu pendaftaran — yang tercatat hanya sisa setelah saringan FHCI.
> Chart harus memberi penanda jalur, bukan satu garis mulus.

---

## B. Metrik corong seleksi (Halaman 3)

### M08 · Funnel 6 tahap — `NYATA`
```sql
SELECT r.urutan, r.tahap_kode, r.nama,
       count(*) AS masuk,
       sum(CASE WHEN t.status_hadir='HADIR' THEN 1 ELSE 0 END) AS hadir,
       sum(CASE WHEN t.hasil='LULUS' THEN 1 ELSE 0 END) AS lulus,
       round(100.0*sum(CASE WHEN t.hasil='LULUS' THEN 1 ELSE 0 END)/count(*),1) AS pct_lulus,
       round(100.0*sum(CASE WHEN t.status_hadir='TIDAK_HADIR' THEN 1 ELSE 0 END)
             / nullif(sum(CASE WHEN t.status_hadir IS NOT NULL THEN 1 END),0),1) AS pct_no_show
FROM seleksi_tahap t JOIN tahap_ref r USING (tahap_kode)
GROUP BY 1,2,3 ORDER BY 1
```

| # | Tahap | Masuk | Hadir | Lulus | % Lulus | % No-show |
|---|---|---:|---:|---:|---:|---:|
| 1 | Seleksi Administrasi | 213.648 | — | 143.831 | 67,3% | — |
| 2 | Tes Adaptif (TAP) | 143.831 | 68.896 | 48.627 | 33,8% | **52,1%** |
| 3 | Tes Akademik & Inggris | 53.907 | 44.358 | 24.699 | 45,8% | 17,7% |
| 4 | Tes Psikologi | 24.699 | 22.651 | 15.980 | 64,7% | 8,3% |
| 5 | Tes Fisik & MCU | 15.980 | 14.826 | 12.623 | 79,0% | 7,2% |
| 6 | Wawancara User & HR | 12.623 | 11.859 | 7.711 | 61,1% | 6,1% |

**Dua hal yang wajib benar di UI:**
1. Administrasi tidak punya kehadiran (seleksi dokumen) — kolom no-show harus kosong,
   **bukan 0%**.
2. Tahap 3 masuk 53.907 padahal tahap 2 meluluskan 48.627. Selisih **5.280** adalah
   kandidat RBB yang masuk di tahap ini (titik serah-terima FHCI→PLN). Funnel harus
   menggambarkannya sebagai aliran masuk, bukan anomali.

### M09 · No-show keseluruhan — `NYATA` — **35,2%**
```sql
SELECT round(100.0*sum(CASE WHEN status_hadir='TIDAK_HADIR' THEN 1 ELSE 0 END)
       / nullif(count(status_hadir),0),1) AS pct_no_show
FROM seleksi_tahap
```

### M10 · Gugur per tahap — `NYATA`
```sql
SELECT tahap_gugur, count(*) AS gugur
FROM pendaftaran WHERE hasil_akhir='GAGAL' GROUP BY 1 ORDER BY 2 DESC
```
adaptif **95.204** · administrasi 69.817 · akademik_inggris 29.208 · psikologi 8.719 ·
wawancara 4.912 · fisik_mcu 3.357

> **Insight utama halaman 3:** titik gugur terbesar bukan seleksi administrasi, tapi Tes
> Adaptif — dan lebih dari separuhnya karena **tidak hadir**, bukan karena gagal tes.

### M12 · Funnel FHCI — `AGREGAT`
```sql
SELECT tahun_program, urutan, nama, jumlah_masuk, jumlah_lulus,
       round(100.0*jumlah_lulus/jumlah_masuk,1) AS pct_lulus
FROM seleksi_tahap_agregat ORDER BY tahun_program, urutan
```
Laju identik tiap tahun (40% → 28% → 17,5%) karena dimodelkan dari satu set aturan.
**Tanpa `kandidat_id`** — tidak bisa di-drill-down, dan itu memang faktanya.

### M29 · Jejak RBB di sistem PLN — `NYATA` + `AGREGAT` — **1,96%**
```sql
WITH fhci AS (
  SELECT tahun_program, max(CASE WHEN urutan=-3 THEN jumlah_masuk END) AS pelamar_fhci
  FROM seleksi_tahap_agregat GROUP BY 1
), pln AS (
  SELECT g.tahun_program, count(*) AS masuk_pln
  FROM pendaftaran p JOIN gelombang g USING (gelombang_id) GROUP BY 1
)
SELECT f.tahun_program, f.pelamar_fhci, p.masuk_pln,
       round(100.0*p.masuk_pln/f.pelamar_fhci,2) AS pct_terlihat
FROM fhci f LEFT JOIN pln p USING (tahun_program) ORDER BY 1
```

| tahun | pelamar FHCI | tercatat di PLN | terlihat |
|---|---:|---:|---:|
| 2020 | 23.215 | 455 | 1,96% |
| 2021 | 9.135 | 179 | 1,96% |
| 2024 | 237.045 | 4.646 | 1,96% |

> ⚠️ **Jangan pakai JOIN langsung** antara `seleksi_tahap_agregat` dan `pendaftaran` —
> tabel agregat punya 3 baris per tahun, hasilnya akan tiga kali lipat. Versi CTE di atas
> yang benar.

---

## C. Metrik perencanaan (Halaman 2) — seluruhnya `DIMODELKAN`

### M13 · Gap FTK nasional — `NYATA` — **701**
```sql
SELECT sum(ftk_2025) AS ftk, sum(realisasi_mar_2026) AS realisasi,
       sum(ftk_2025) - sum(realisasi_mar_2026) AS gap
FROM unit_induk
```
37.854 formasi − 37.153 realisasi = **701**.

> **Wajib pakai `realisasi_mar_2026`.** Kolom `realisasi_apr_2026` hanya terisi di 1 dari
> 48 unit; memakainya menghasilkan gap palsu 33.934.

### M14 · Gap FTK per unit — `NYATA` (dengan pengecualian)
```sql
SELECT nama_pendek, jenis_unit, ftk_2025, realisasi_mar_2026,
       ftk_2025 - realisasi_mar_2026 AS gap
FROM unit_induk
WHERE jumlah_pegawai > 50          -- buang unit anomali, lihat catatan
ORDER BY gap DESC
```
> ⚠️ **Anomali data master:** `UID Jawa Tengah & DIY` tercatat `jumlah_pegawai` = 4 dan
> `realisasi_mar_2026` = 4, tapi `ftk_2025` = 144 — jelas gagal *match* saat ekstraksi
> DAPEG (baris duplikat; unit yang sama juga punya baris benar dengan `jumlah_pegawai`
> 1.643 — detail penuh di `mockdb/ISSUES_MASTER_DATA.md`). Tanpa filter, unit ini menempati
> peringkat 1 gap (140) secara palsu. Filter `jumlah_pegawai > 50` mengeluarkannya, dan
> anomalinya **dilaporkan di halaman Kualitas Data**, tidak dihapus diam-diam.
>
> Setelah filter, tiga teratas: UID Jawa Barat 59 · Kantor Pusat 55 · P3B Sumatera 50.

### M15 · Rantai perencanaan — `DIMODELKAN`
```sql
SELECT tahun_program, round(sum(kekosongan)) AS kekosongan,
       round(sum(gap_ftk)) AS gap_ftk, round(sum(usulan)) AS usulan
FROM usulan_kebutuhan GROUP BY 1 ORDER BY 1
```
`usulan = kekosongan + gap_ftk`. 2025: 906 + 333 = 1.238.

### M16 · Pagu vs usulan — `DIMODELKAN`
```sql
SELECT p.tahun_program, sum(p.jumlah) AS pagu, round(u.usulan) AS usulan,
       round(100.0*sum(p.jumlah)/u.usulan,1) AS pct_disetujui
FROM pagu_rekrutmen p
JOIN (SELECT tahun_program, sum(usulan) AS usulan FROM usulan_kebutuhan GROUP BY 1) u
  USING (tahun_program)
GROUP BY 1, u.usulan ORDER BY 1
```

| tahun | usulan | pagu | disetujui |
|---|---:|---:|---:|
| 2019 | 3.099 | 1.093 | 35,3% |
| 2020 | 2.528 | 325 | 12,9% |
| 2021 | 2.313 | 689 | 29,8% |
| 2022 | 2.023 | 689 | 34,1% |
| 2023 | 1.816 | 1.277 | 70,3% |
| 2024 | 1.741 | 1.098 | 63,1% |
| 2025 | 1.238 | 1.050 | 84,8% |

> Cerita halaman 2: **persetujuan pagu naik dari 13% (2020) ke 85% (2025)** — jarak antara
> apa yang diminta unit dan apa yang disetujui pusat menyempit tajam.

### M17 · Proyeksi kekosongan per sebab — `DIMODELKAN`
```sql
SELECT tahun, round(sum(pensiun)) AS pensiun, round(sum(mengundurkan_diri)) AS aps,
       round(sum(meninggal_dunia)) AS meninggal, round(sum(phk)) AS phk,
       round(sum(kekosongan)) AS total
FROM proyeksi_kekosongan GROUP BY 1 ORDER BY 1
```
2019 total 2.357 → 2026 total **919**. Pensiun mendominasi (2026: 780 dari 919 = 85%).
Satu-satunya tabel yang punya **tahun 2026** — inilah isi "tahun berjalan".

---

## D. Metrik kandidat (Halaman 4)

### M18 · Jenjang pendidikan pelamar — `NYATA`
```sql
SELECT degree, count(*) AS n
FROM kandidat_pendidikan WHERE pendidikan_terakhir GROUP BY 1 ORDER BY 2 DESC
```
S1/D-IV 245.553 · D-III 98.161 · SMK 11.696 · S2 11.631

> Filter `pendidikan_terakhir` **wajib** — tanpa itu ikut terhitung baris SD/SMP/SMA yang
> memang disimpan (±4 baris per kandidat, total 1.071.976).

### M19 · Komposisi gender per kohort — `NYATA`
```sql
SELECT tahun_kohort, count(*) AS n,
       round(100.0*sum(CASE WHEN jenis_kelamin='P' THEN 1 ELSE 0 END)/count(*),1) AS pct_pria
FROM kandidat WHERE pernah_melamar GROUP BY 1 ORDER BY 1
```
> Kode gender adalah **`P` = Pria** dan **`W` = Wanita** — bukan `L`/`P`. Salah baca di
> sini membalik seluruh grafik.
>
> 2019 63,4% · 2020 74,0% · 2021 61,7% · 2022 68,3% · 2023 64,5% · 2024 64,4% · 2025 64,2%

### M20 · Asal kandidat per provinsi — `NYATA`
```sql
SELECT coalesce(propinsi_domisili,'(tidak diisi)') AS provinsi, count(*) AS n
FROM kandidat GROUP BY 1 ORDER BY 2 DESC
```
Jawa Barat 50.806 · Jawa Timur 47.701 · Jawa Tengah 40.956 · DKI Jakarta 28.707 ·
Banten 19.092. **13.788 tidak mengisi** — jangan dibuang diam-diam, tampilkan.

### M21 · Lamaran per akun — `NYATA` — **1,27**
```sql
SELECT count(*)*1.0/count(DISTINCT kandidat_id) AS rata2 FROM pendaftaran
```

---

## E. Metrik pasca-seleksi (Halaman 5)

### M22 · Posisi pipeline — `NYATA`
```sql
SELECT tahap_kode, status, count(*) AS n
FROM pasca_tahap GROUP BY 1,2 ORDER BY min(urutan), 2
```
pengumuman 7.711 · kontrak 7.711 · SAMAPTA 7.711 · pembidangan 7.711 ·
OJT **2.000 berjalan / 5.711 selesai** · ujian OJT 5.711 · SK 5.711

### M23 · Pembidangan — `NYATA`
```sql
SELECT bidang_pembidangan, count(*) AS n FROM penempatan GROUP BY 1 ORDER BY 2 DESC
```
Distribusi 1.499 · SDM 1.464 · Pembangkitan 871 · Niaga 820 · Transmisi & GI 741 ·
Konstruksi & Pengadaan 737 · Keuangan 625 · Manajemen Digital 482 · Perencanaan Sistem 340 ·
Proteksi & Kontrol 132

> ❌ **Metrik yang sengaja TIDAK dibuat: durasi antar tahap.** Jarak tutup gelombang → SK
> konstan **400 hari** untuk semua kohort, dan semua tahap pasca punya
> `tanggal_mulai = tanggal_selesai` kecuali OJT (180 hari). Tidak ada variasi, jadi analisis
> bottleneck/SLA di area ini akan menyesatkan. Jangan dibuat.

---

## F. Metrik penempatan (Halaman 6)

### M24 · Jenis penempatan — `NYATA`
```sql
SELECT jenis_penempatan, count(*) AS n FROM penempatan GROUP BY 1 ORDER BY 2 DESC
```
INDUK 5.171 · SUBHOLDING 2.540

### M25 · Grade masuk — `NYATA`
```sql
SELECT kode_grade, count(*) AS n FROM penempatan GROUP BY 1 ORDER BY 2 DESC
```
G2 5.423 · G1 2.020 · G3 268 — sesuai aturan SMK/D3→G1, S1/D4→G2, S2→G3.

### M26 · Rencana vs realisasi — `NYATA`
```sql
SELECT k.tahun_program, k.kuota, coalesce(r.realisasi,0) AS realisasi,
       round(100.0*coalesce(r.realisasi,0)/k.kuota,1) AS pct
FROM (SELECT tahun_program, sum(kuota) AS kuota FROM profesi GROUP BY 1) k
LEFT JOIN (SELECT tahun_program, count(*) AS realisasi FROM penempatan GROUP BY 1) r
  USING (tahun_program)
ORDER BY 1
```

| tahun | kuota | realisasi | % | catatan |
|---|---:|---:|---:|---|
| 2019 | 1.353 | 1.353 | 100% | mandiri |
| 2020 | 325 | 125 | 38,5% | ⚠️ RBB |
| 2021 | 689 | 49 | 7,1% | ⚠️ RBB |
| 2022 | 1.109 | 1.109 | 100% | mandiri |
| 2023 | 1.797 | 1.797 | 100% | mandiri |
| 2024 | 1.578 | 1.278 | 81,0% | ⚠️ RBB |
| 2025 | 2.000 | 2.000 | 100% | mandiri |

> ⚠️ **Tahun RBB tidak boleh disajikan sebagai "gagal memenuhi target".** Kuota di
> `profesi` untuk tahun RBB adalah kohort penuh, sedangkan yang tercatat di PLN hanya hasil
> serah-terima FHCI. Di UI, tiga tahun ini diberi penanda dan **dikeluarkan dari rata-rata
> pemenuhan**, dengan catatan kaki yang menjelaskan sebabnya.

---

## G. Metrik kualitas data (Halaman 7)

### M27 · Volume per sistem sumber — `NYATA`
```sql
SELECT sistem_sumber, count(*) AS n FROM seleksi_tahap GROUP BY 1 ORDER BY 2 DESC
```
rekrutmen.pln.co.id 370.102 · seleksi.pln.co.id 53.907 · hasil vendor di-upload 40.679

### M28 · Kelengkapan per kualitas kohort — `NYATA`
```sql
SELECT kualitas_kohort, count(*) AS n,
       round(100.0*count(body_height)/count(*),1) AS pct_blok_fisik,
       round(100.0*count(kota_domisili)/count(*),1) AS pct_domisili
FROM kandidat GROUP BY 1 ORDER BY 1
```

| kohort | n | blok fisik | kota domisili |
|---|---:|---:|---:|
| RENDAH | 101.829 | **0,0%** | 90,0% |
| SEDANG | 106.415 | 33,1% | 97,3% |
| BAIK | 160.668 | 70,6% | 99,6% |

> Kelengkapan data membaik tiap tahun — kohort lama tidak punya blok fisik sama sekali.
> Ini bukan bug, ini kurva kematangan sistem yang justru layak dipamerkan.

### M30 · Selisih dua angka rencana — `DIMODELKAN`
```sql
SELECT g.tahun_program, sum(g.diterima_target) AS target_gelombang, p.pagu,
       sum(g.diterima_target) - p.pagu AS selisih
FROM gelombang g
LEFT JOIN (SELECT tahun_program, sum(jumlah) AS pagu FROM pagu_rekrutmen GROUP BY 1) p
  USING (tahun_program)
GROUP BY 1, p.pagu ORDER BY 1
```

| tahun | target gelombang | pagu | selisih |
|---|---:|---:|---:|
| 2019 | 1.353 | 1.093 | +260 |
| 2020 | 325 | 325 | 0 |
| 2021 | 689 | 689 | 0 |
| 2022 | 1.109 | 689 | +420 |
| 2023 | 1.797 | 1.277 | +520 |
| 2024 | 1.578 | 1.098 | +480 |
| 2025 | 2.000 | 1.050 | +950 |

> **Temuan yang ditampilkan, bukan disembunyikan.** Dua angka rencana untuk tahun yang sama
> tidak pernah didamaikan: pagu (sisi anggaran) dan target gelombang (sisi program).
> Selisihnya melebar dari 0 (2020–2021) ke 950 (2025). Di sistem nyata, ketidaksinkronan
> seperti ini persis yang bikin "berapa sebenarnya target kita?" tidak punya jawaban tunggal.

---

## H. Metrik tambahan halaman 2, 3, 5, 6, 7 (ditambahkan 2026-08-19)

Semua di bawah **sudah dijalankan dan diverifikasi** terhadap `rekrutmen.duckdb`. Kode M31+
melanjutkan penomoran M01–M30 di atas.

### M31 · Heatmap unit × sub-bidang — `DIMODELKAN`
```sql
SELECT unit_induk, sub_bidang, round(sum(usulan)) AS usulan
FROM usulan_kebutuhan WHERE tahun_program = 2025
GROUP BY 1, 2 ORDER BY 3 DESC
```
Kantor Pusat/Komunikasi & Umum 46 · Kantor Pusat/SDM 45 · UID Jabar/Distribusi 34 ·
UID Jatim/Distribusi 30 · UIP2B Sumatera/Transmisi 24 — dipakai halaman Perencanaan
(lapis analis, dipindah dari lapis eksekutif supaya tidak melanggar batas 4 blok D5).

### M32 · No-show per tahap × mode — `NYATA`
```sql
SELECT tahap_kode, mode,
       round(100.0 * sum(CASE WHEN status_hadir='TIDAK_HADIR' THEN 1 ELSE 0 END)
             / count(*), 1) AS pct_no_show
FROM seleksi_tahap WHERE status_hadir IS NOT NULL GROUP BY 1, 2 ORDER BY 3 DESC
```

| tahap | mode | % no-show |
|---|---|---:|
| adaptif | online | **52,1** |
| akademik_inggris | online | 17,7 |
| psikologi | offline | 8,3 |
| fisik_mcu | offline | 7,2 |
| wawancara | offline | 6,1 |

**Insight jangkar halaman Corong Seleksi (D1/D3):** tes online kehilangan jauh lebih banyak
peserta daripada tes offline — pola ini menggantikan hipotesis "jarak tempat tinggal" yang
gugur setelah diuji (lihat `docs/backlog.md` B6). Kolom `mode` di sini berpola benar,
independen dari cacat `kota_domisili` yang dicatat di `mockdb/ISSUES_SEBARAN.md`.

### M33 · Umur pelamar saat mendaftar akun — `NYATA`
```sql
SELECT date_diff('year', tanggal_lahir, tanggal_daftar_akun) AS umur, count(*) AS n
FROM kandidat WHERE pernah_melamar AND tanggal_lahir IS NOT NULL
GROUP BY 1 ORDER BY 1
```
Puncak di umur 21 (36.786), turun landai ke umur 30 (496) — berpola benar (bukan seragam),
aman dipakai di halaman Kandidat.

### M34 · Rumpun jurusan: melamar vs diterima — `NYATA`
```sql
WITH t AS (
  SELECT ps.rumpun, count(*) AS melamar,
         sum(CASE WHEN p.hasil_akhir='DITERIMA' THEN 1 ELSE 0 END) AS diterima
  FROM pendaftaran p
  JOIN kandidat_pendidikan kp ON kp.kandidat_id = p.kandidat_id AND kp.pendidikan_terakhir
  JOIN program_studi ps ON ps.program_studi = kp.program_studi
  GROUP BY 1
)
SELECT rumpun, melamar, diterima, round(100.0 * diterima / melamar, 2) AS pct
FROM t ORDER BY melamar DESC
```

| rumpun | melamar | diterima | % lolos |
|---|---:|---:|---:|
| Manajemen dan Bisnis | 36.073 | 1.206 | 3,34 |
| Informatika dan Data | 24.639 | 768 | 3,12 |
| Mesin dan Konversi Energi | 24.372 | 899 | 3,69 |
| Elektro dan Ketenagalistrikan | 23.440 | 1.062 | **4,53** |
| Akuntansi dan Perpajakan | 18.410 | 618 | 3,36 |

> ⚠️ **Join lewat tabel master `program_studi`** (kolom `rumpun`), **bukan** tabel
> `profesi_prodi` (yang hanya punya `min_ipk`, tidak ada kolom rumpun) dan **bukan** tabel
> `rumpun_jurusan` (agregat per rumpun, tanpa kolom penghubung ke `program_studi`
> perorangan). Salah pilih tabel di sini gagal dengan `Binder Error`.

Elektro & Ketenagalistrikan lolos paling tinggi (4,53%) — masuk akal untuk perusahaan
kelistrikan, dan rentang 2,82–4,53% cukup lebar untuk jadi insight (beda dengan almamater
di B7 yang rentangnya 3,10–3,76% dan terbukti tanpa sinyal).

### M35 · Volume tes per kota — `NYATA`
```sql
SELECT lokasi_kota, count(*) AS n FROM seleksi_tahap
WHERE mode = 'offline' GROUP BY 1 ORDER BY 2 DESC
```
Makassar 5.162 · Surabaya 5.160 · Palembang 5.115 · Balikpapan 5.083 · Jakarta 4.950 ·
Medan 4.912 · Merauke 2.596 · Nabire 2.522 · Sorong 2.512 · Wamena 1.886. Berpola benar
(rasio top/bawah 37,7×) — dipakai sebagai peta jangkar halaman Kandidat, **menggantikan**
peta "asal vs kota tes" yang datanya cacat (lihat §I di bawah).

### M36 · Sebaran per UPDL — `NYATA`
```sql
SELECT d.nama AS updl, count(*) AS n
FROM penempatan p JOIN updl d ON p.updl_id = d.updl_id
GROUP BY 1 ORDER BY 2 DESC
```
UPDL Semarang 953 · UPDL Pandaan 916 · UPDL Surabaya 890 · UPDL Palembang 771 ·
UPDL Tuntungan 710 · UPDL Padang 623 · UPDL Makassar 619 · UPDL Jakarta 580 ·
UPDL Suralaya 556 · UPDL Banjarbaru 550 (+1 lainnya, 11 UPDL total).

### M37 · Rentang tanggal per kohort (untuk timeline) — `NYATA`
```sql
SELECT tahun_program, min(tgl_buka) AS mulai, max(tgl_tutup) AS selesai, count(*) AS n_gel
FROM gelombang GROUP BY 1 ORDER BY 1
```
2019: 15 Jul–25 Nov (5 gelombang) · 2020: 30 Des–9 Jan (1) · 2021: 23 Des–14 Jan (1) ·
2022: 30 Mar–25 Des (5) · 2023: 22 Mei–25 Okt (3) · 2024: 23 Mar–25 Agu (2) ·
2025: 8 Sep–5 Okt (2). Dipakai untuk sumbu Gantt timeline kohort di halaman Pasca-Seleksi.

### M38 · Treemap penempatan: unit × bidang — `NYATA`
```sql
SELECT unit_induk, bidang_pembidangan, count(*) AS n
FROM penempatan WHERE unit_induk IS NOT NULL
GROUP BY 1, 2 ORDER BY 3 DESC
```
Kantor Pusat/SDM 244 · UID Jabar/Distribusi 117 · UID Jatim/Distribusi 97 ·
UIP2B Sumatera/Transmisi 92 · UIT Jateng/Transmisi 87 — jangkar treemap halaman Penempatan.

### M39 · Volume baris per sistem sumber — `NYATA`
```sql
SELECT sistem_sumber, count(*) AS n FROM seleksi_tahap GROUP BY 1 ORDER BY 2 DESC
```
Sama dengan M27 (dipertahankan sebagai referensi silang) — rekrutmen.pln.co.id 370.102 ·
seleksi.pln.co.id 53.907 · hasil vendor di-upload 40.679.

### M40 · Sumber skor — `DIMODELKAN`
```sql
SELECT DISTINCT sumber_skor FROM seleksi_tahap
```
Satu nilai: `DIMODELKAN` di seluruh 464.688 baris — konfirmasi bahwa skor tes memang
tidak pernah ada di sumber nyata (F-017), bukan sebagian dimodelkan.

---

## I. Dampak cacat data ke metrik halaman 4 (lihat `mockdb/ISSUES_SEBARAN.md`)

Tiga metrik yang **direncanakan tapi dibatalkan** karena kolom sumbernya dibagikan acak
seragam oleh generator (rasio top/bawah 1,02–1,07, seharusnya jauh lebih tinggi):

| Metrik batal | Kolom bermasalah | Bukti |
|---|---|---|
| Sebaran asal kandidat per provinsi | `kandidat.kota_domisili` | 43 nilai, top/bawah 1,05 — provinsi tampak berpola hanya karena artefak jumlah kota per provinsi |
| Peta asal vs kota tes | `kandidat.kota_domisili`, `kota_asal` | `kota_asal` identik `kota_domisili` di 199.310/199.310 baris (bug generator) |
| Konversi per almamater | `kandidat_pendidikan.sekolah_universitas` | 15 nilai unik dari 68, top/bawah 1,02; konversi 3,10–3,76% (tanpa sinyal) |

Digantikan M35 (volume tes per kota, berpola benar) dan tidak diganti untuk almamater —
lihat `docs/backlog.md` B7 untuk rencana rebuild.

---

## Metrik yang sengaja tidak dibuat

| Metrik | Alasan |
|---|---|
| Durasi / SLA antar tahap pasca-seleksi | Konstan 400 hari, tidak ada variasi (lihat M23) |
| Skor rata-rata per tahap | `sumber_skor` seluruhnya `DIMODELKAN` (M40); sistem asli hanya simpan lulus/gagal |
| Biaya per rekrutmen | Tidak ada data biaya sama sekali |
| Rasio pelamar per lowongan tingkat ULP | Master DAPEG berhenti di unit pelaksana |
| Attrition / turnover pegawai | Tabel `headcount_tahunan` & `peristiwa_pegawai` tidak ada di DB ini |
| Sebaran asal kandidat per provinsi | Data cacat — lihat §I di atas dan `mockdb/ISSUES_SEBARAN.md` |
| Konversi per almamater | Data cacat — lihat §I di atas dan `docs/backlog.md` B7 |
