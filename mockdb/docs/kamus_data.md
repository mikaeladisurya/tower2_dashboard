# Kamus data — database mock rekrutmen PLN Group

Horison gelombang **2019–2025**, tanggal potong **15 Sep 2026**.
Rincian kolom untuk tabel yang **baru atau berubah** dibanding mock lama. Tabel master
di `out/master/` sudah terdokumentasi di `mockdb/README.md`. Model besarnya di
[ERD.md](ERD.md).

## Legenda kolom `Sumber`

| Tanda | Arti | Boleh dipercaya sebagai fakta PLN? |
|---|---|---|
| 🟢 **NYATA** | dari sumber tersitasi (DAPEG, SR, scrape situs, perdir) | ya |
| 🔵 **TURUNAN** | dihitung dari angka nyata lewat penalaran tertulis | dengan catatan |
| 🟠 **DIMODELKAN** | **tidak ada di sistem asli sama sekali** | **tidak** — direka penuh |
| ⚪ **ASUMSI** | tidak ada sumber, tidak diturunkan | tidak |

Kolom 🟠 wajib diberi penanda visual di dashboard. Kalau tidak, orang akan mengira PLN
sudah punya data yang sebenarnya belum ada — dan itu menghapus seluruh nilai proyek ini.

---

## `kandidat` — akun *lifetime*

Skema mengikuti **halaman Pratayang CV asli** di area member (F-034), bukan tebakan.

| Kolom | Tipe | Sumber | Catatan |
|---|---|---|---|
| `kandidat_id` | BIGINT PK | 🟠 | = "ID Member" di sistem asli, numerik |
| `nama_lengkap` | VARCHAR | 🟠 | **100% sintetis.** Jangan pernah ambil dari DAPEG atau dump area member |
| `email` | VARCHAR | 🟠 | |
| `no_ktp` | VARCHAR(16) | 🟠 | NIK sintetis, checksum tidak valid **dengan sengaja** |
| `no_handphone` | VARCHAR | 🟠 | |
| `tempat_lahir` | VARCHAR | 🟠 | |
| `tanggal_lahir` | DATE | 🟠 | menentukan umur saat daftar → kriteria administrasi |
| `jenis_kelamin` | CHAR(1) | 🔵 | sebaran **per tahun** (F-048): berayun 65:35 → 86:14. **Jangan 50:50, dan jangan satu angka tetap** |
| `agama` | VARCHAR | ⚪ | sebaran nasional umum, tidak ada sumber PLN |
| `status_perkawinan` | VARCHAR | 🔵 | 94% belum menikah; sisanya gugur di administrasi |
| **Blok domisili** | | | |
| `alamat_domisili`, `kota_domisili`, `propinsi_domisili`, `kode_pos_domisili` | VARCHAR | 🟠 | |
| **Blok asal** *(terpisah — F-034)* | | | |
| `alamat_asal`, `kota_asal`, `propinsi_asal` | VARCHAR | 🟠 | **NULL untuk kohort 2019–2021** — field belum ada |
| **Blok fisik** *(temuan baru F-034)* | | | |
| `ukuran_baju`, `ukuran_celana`, `ukuran_sepatu` | VARCHAR | 🟠 | |
| `body_height` | SMALLINT | 🟠 | cm |
| `body_weight` | SMALLINT | 🟠 | kg |
| `bmi` | DECIMAL(4,1) | 🟠 | **dihitung** dari tinggi & berat — jangan dibangkitkan terpisah |
| `visus_kiri`, `visus_kanan` | VARCHAR | 🟠 | mis. `6/6`, `6/12` |
| `tingkat_ketajaman`, `silinder` | VARCHAR | 🟠 | |
| `abdominal_circumference` | SMALLINT | 🟠 | cm |
| `tatto` | BOOLEAN | 🟠 | |
| `buta_warna` | BOOLEAN | 🟠 | ±3,5% pria / 0,4% wanita; **UNFIT otomatis untuk profesi TEKNIK** |
| **Metadata** | | | |
| `tanggal_daftar_akun` | DATE | 🟠 | |
| `email_teraktivasi` | BOOLEAN | 🔵 | 7,5% akun tak pernah aktivasi (F-019/F-033) |
| `pernah_melamar` | BOOLEAN | 🔵 | 47% akun tidak pernah melamar sama sekali (F-019) |
| `kualitas_kohort` | VARCHAR | 🔵 | `RENDAH` (2019–2021) / `SEDANG` (2022, 2024) / `BAIK` (2023, 2025) / `PERENCANAAN` (2026) |

> **Konsistensi wajib:** hasil `fisik_mcu` harus cocok dengan blok fisik di sini. BMI di
> luar 18,5–25 harus muncul sebagai temuan MCU, bukan angka baru yang bertentangan.
> Untuk kohort ≤2022 blok fisik kosong — jadi MCU-nya **tidak bisa dijelaskan** dari
> biodata. Itu realistis dan memang tujuannya.

### `kandidat_pendidikan`

| Kolom | Sumber | Catatan |
|---|---|---|
| `degree` | 🟠 | `SD`, `SMP`, `SMA/SMK`, `D-III`, `S1/D-IV`, `S2` |
| `sekolah_universitas`, `program_studi` | 🟠 | prodi dari daftar 49 asli (F-004) |
| `skhu_ipk` | 🟠 | IPK untuk pendidikan tinggi, NEM untuk SMA/SMK |
| `pendidikan_terakhir` | 🟠 | penanda baris mana yang jadi acuan seleksi |
| `tahun_masuk`, `tahun_lulus` | 🟠 | |

**±4 baris per kandidat.** Sistem asli mewajibkan SD, SMP, dan SMA/SMK diisi — bukan
cuma pendidikan tinggi (F-034). Untuk kohort 2019–2021 kewajiban itu belum ada, jadi
banyak yang hanya punya baris pendidikan tinggi.

### `kandidat_sertifikasi`

`kategori_sertifikasi` · `tahun` · `skor` — 🟠. Hanya 31% kandidat punya.

> **Jangan tertukar:** `skor` di tabel ini adalah **satu-satunya skor yang benar-benar
> ada di sistem asli**, karena diisi sendiri oleh kandidat. Skor **tes** tidak ada
> (F-017).

### `kandidat_keluarga`, `kandidat_berkas`

`kandidat_keluarga`: `hubungan_keluarga` · `alamat` · `no_telp` · `pekerjaan` — 🟠, 1–2 baris.

`kandidat_berkas`: 8 jenis wajib (F-034) — KTP, Akta Kelahiran, Surat Keterangan Belum
Menikah, Ijazah, Transkrip, Swafoto, Foto Full Body, Pasfoto. Kolom `terunggah`,
`tanggal_unggah`, `valid`. Swafoto & foto full body **belum ada** sebelum 2022.

---

## `gelombang` → `program` → `profesi`

### `gelombang`

| Kolom | Sumber | Catatan |
|---|---|---|
| `gelombang_id` | 🟠 | |
| `angkatan` | 🟢/🔵 | nomor **seri paralel asli** (F-008). Bukan tebakan "S1 70-an" |
| `sumber_nomor` | 🟢 | `nyata` (8 nomor tercatat di sumber) / `inferensi_kuat` / `inferensi` |
| `seri` | 🔵 | `utama` (70–92) / `khusus` (7–9, Pro Hire & subholding). SMK tidak dimodelkan di horison ini |
| `tahun_program` | 🟢 | **kunci waktu utama** |
| `tahun_masuk` | 🔵 | = `tahun_program + 1` (jeda pipeline; keyakinan **tinggi** sejak F-048) |
| `jenis_program` | 🟢 | REGULER / CAMPUS / AFIRMASI / PRO_HIRE / DIASPORA / BIDANG / S2 / RBB |
| `sumber_rekrutmen` | 🟢 | `mandiri` / `rbb` |
| `kualitas_kohort` | 🔵 | |

### `program` *(entri penempatan)*

`judul` 🟢 — **wajib** dari `programs.csv` / `programs_historis.csv` / `lowongan_pln_rbb.csv`.
**Tidak ada judul yang boleh dikarang.** Gelombang 2021 & 2024 tidak punya judul sama
sekali dan diberi penanda *"(tidak terekam di katalog PLN)"*.
`perusahaan_penempatan` 🟢 · `lokasi_tes` 🟢 · `pdf_brosur` 🟢 · `status` 🟢.

### `profesi` — ⭐ **unit granular pendaftaran**

| Kolom | Sumber | Catatan |
|---|---|---|
| `kode_profesi` | 🟢 | `{SUBHOLDING}.{TIPE}.{JENJANG}[.varian]` (2024+) atau `{n}.{m}` (2019–23) |
| `nama_profesi` | 🟢 | dari `profesi.csv` |
| `jenjang` | 🟢 | |
| `kota_rekrutmen` | 🟢 | **terkunci** saat daftar, tidak bisa diubah (F-024, F-033) |
| `tgl_buka`, `tgl_tutup` | 🟢 | jendela 5–14 hari (F-007) |
| `min_ipk` | 🟢 | per profesi; per-prodi ada di `profesi_prodi` |
| `umur_maks` | 🟢 | **berbeda per jalur** — mandiri S1 ≤27, RBB S1 ≤30 (F-022, F-043) |
| `bidang_pembidangan` | 🔵 | dipetakan dari minat profesi (F-005) |
| `kuota` | 🟠 | ⚠️ **tidak ada di sumber manapun** — F-017, F-027, F-043 |

---

## `pendaftaran`

| Kolom | Sumber | Catatan |
|---|---|---|
| `pendaftaran_id` | 🟠 | |
| `kandidat_id`, `profesi_id` | 🟠 | |
| `nomor_tes` | 🟢 | `{YYMM}/{SUBHOLDING}/{ANGKATAN}/{JENJANG-JURUSAN}/{URUT}` — mis. `2511/ES/92/D3-ELE/135615` |
| `tanggal_lamar` | 🟠 | |
| `status_lamaran` | 🟢 | `AKTIF` / `DIBATALKAN` / `SELESAI` — cancel diizinkan selama periode buka (F-033) |
| `sumber_rekrutmen` | 🟢 | `mandiri` / `rbb` |
| `titik_masuk` | 🔵 | `administrasi` (mandiri) / `akademik_inggris` (RBB) |
| `hasil_akhir` | 🟠 | `DITERIMA` / `GAGAL` / `MENGUNDURKAN_DIRI` / `DALAM_PROSES` |
| `tahap_gugur` | 🟠 | tahap tempat berhenti — kolom paling sering dipakai dashboard funnel |

Satu akun bisa punya banyak baris (rata-rata 1,35) — akun *lifetime*, boleh melamar
lintas tahun (F-025, F-033). Dalam **satu gelombang** dibatasi 1 profesi (tanggal tes
bentrok).

---

## `seleksi_tahap` — ⭐ satu tabel untuk kedua jalur

| Kolom | Sumber | Catatan |
|---|---|---|
| `pendaftaran_id`, `tahap_kode` | 🟠 | PK gabungan |
| `urutan` | 🟢 | 1–6; kolom, bukan konstanta — urutan bisa beda per gelombang (ReqGathering#4) |
| `mode` | 🟢 | `online` / `offline` / `dokumen` (F-024, F-029) |
| `kota` | 🟢 | NULL untuk tahap online; **terkunci** untuk offline |
| `pemilik_proses` | 🟢 | `PLN_HTD` / `PLN_USER` / `VENDOR` / `FHCI` / `PUSDIKLAT` (F-018) |
| `sistem_sumber` | 🟢 | ⭐ `akademik_inggris` hidup di **`seleksi.pln.co.id`**, sisanya di `rekrutmen.pln.co.id` |
| `vendor_id` | ⚪ | psikologi & MCU |
| `tanggal_jadwal`, `tanggal_pelaksanaan` | 🟠 | |
| `hadir` | 🔵 | `HADIR` / `TIDAK_HADIR` / `TIDAK_DIUNDANG` — no-show ±44% (F-020) |
| `hasil` | 🟠 | `LULUS` / `GAGAL` / `TIDAK_HADIR` |
| `alasan_gagal` | 🔵 | **daftar**, bukan satu nilai — satu orang bisa gagal karena >1 sebab |

**Kandidat RBB tidak punya baris** untuk `administrasi` dan `adaptif` — itu ketiadaan
struktural, bukan data hilang. Titik masuknya `akademik_inggris` varian **TKB saja**
(komponen Inggris dikerjakan FHCI, tidak diulang PLN).

`sistem_sumber` menunjukkan titik rawan integrasi: hasil `seleksi.pln.co.id` di-**download
manual lalu di-upload** per angkatan ke `rekrutmen.pln.co.id` (F-018).

### `seleksi_skor` — ⚠️ **seluruhnya 🟠 DIMODELKAN**

`komponen` · `skor` · `skor_maks` · `passing_grade` · `lulus_komponen`.

**Tidak ada satu pun passing grade di regulasi PLN manapun** yang kita punya — Perdir
0056, 0050, dan Juknis 0048 sama-sama tidak memuatnya (F-028). Sistem asli hanya
menyimpan lulus/gagal tanpa skor (F-017). Seluruh isi tabel ini rekaan yang dikalibrasi
mundur dari laju lulus di `rules/funnel.yaml`.

Ada gunanya tetap dibangkitkan: dashboard bisa mendemokan **seperti apa jadinya kalau
skor ini dikumpulkan** — dan itu argumen konkret buat tim HTD.

### `tahap_agregat` — tahap FHCI, **tanpa `kandidat_id`**

`program_id` · `tahap_kode` · `tanggal_mulai` · `tanggal_selesai` · `jumlah_peserta` ·
`jumlah_lulus` · `pemilik_proses = FHCI`.

Sengaja **tidak punya foreign key ke kandidat**: PLN memang tidak memegang data
per-kandidat untuk tahap ini. Tapi PLN pasti tahu berapa orang yang diserahkan ke TKB,
jadi jumlahnya dicatat — tanpa angka ini funnel tahun RBB kosong dan tak bisa dibandingkan
antar-jalur.

Keyakinan volume di tabel ini **rendah** — porsi PLN dari ±1,1 juta pendaftar RBB 2024
adalah tebakan. Tandai kualitas rendah di dashboard.

---

## `prajabatan`, `penempatan`, `pegawai`

### `prajabatan`

`updl_id` 🔵 (11 UPDL) · `bidang_pembidangan` 🔵 · `kelas` 🟠 (30–60 orang) ·
`tanggal_mulai`/`selesai` 🟠 · `hasil_ujian_ojt` 🟠 · `sistem_sumber = "aplikasi Pusdiklat"` 🟢.

> **Pembidangan berat sebelah dan harus tetap begitu.** Pembangkitan tinggal 761 pegawai
> G1+G2 di holding (praktis cuma UIK Tanjung Jati B) karena sudah pindah ke subholding.
> Membagi rata 9 bidang akan membengkakkan porsi UPDL Suralaya ±10× dari semestinya.
> Bobot ada di `rules/jabatan.yaml`.

Istilah: Juknis 0048-2025 memakai **"OJT – First OJT"**, kata "Prajabatan" tidak muncul
sama sekali (F-028). Simpan kedua nama.

### `penempatan`

| Kolom | Sumber | Catatan |
|---|---|---|
| `unit_induk`, `kode_unit_pelaksana` | 🔵 | dipilih dari kebutuhan, bukan acak |
| `nama_posisi` | 🟢 | dari `jabatan_klasifikasi.csv` |
| `kelompok_jabatan` | 🟢 | ⚠️ **filter non-struktural pakai kolom ini, BUKAN `jenjang`** |
| `grade` | 🔵 | SMK/D3→G1 · S1/D4→G2 · S2→G3 (F-042, keyakinan **sedang**) |
| `tanggal_sk` | 🟠 | |

**Dua larangan keras** (F-042):
1. Tidak pernah ke jabatan struktural — Team Leader, Assistant Manager, Manager, Senior
   Manager, GM, VP, EVP. **Team Leader juga G2**, sama dengan Officer, jadi menyaring
   pakai `jenjang` akan meloloskannya.
2. Jangan tempatkan semua ke Junior — grade mengikuti jenjang pendidikan.

Nama posisi memakai konvensi DAPEG (**Officer / Technician / Specialist**), bukan
"Analyst"/"Engineer" — di DAPEG 37rb pegawai, "Analyst" nol.

### `peristiwa_pegawai`

| Kolom | Sumber | Catatan |
|---|---|---|
| `jenis_peristiwa` | 🟢 | Pensiun, Pensiun Dini, APS, Meninggal, PHK, Mutasi, Tugas Karya, Rotasi, Promosi, Demosi (F-015) |
| `turnover_sempit` | 🟢 | APS + PHK saja — definisi SR-2017/SR-2020 |
| `turnover_luas` | 🟢 | semua sebab termasuk pensiun — definisi SR-2021+ |
| `jenis_perubahan_headcount` | 🟢 | ⚠️ `ATTRITION` / `CARVE_OUT` / `REKRUTMEN` / `MUTASI_MASUK` |
| `menciptakan_kekosongan` | 🔵 | rotasi/promosi/demosi = `false` |

> **Carve-out wajib terpisah.** Penurunan 2022→2023 (−3.609 Induk / +3.377 Anak) adalah
> pemindahan ke subholding, bukan orang keluar (F-045). Kalau digabung, attrition 2023
> terbaca ±9,5% — 3,5× angka sebenarnya, dan seluruh proyeksi kebutuhan ikut ngawur.
>
> **Patahan definisi wajib ditandai.** SR-2017 & SR-2020 memakai turnover **sempit**
> (tanpa pensiun → 0,2%); SR-2021 ke atas memakai **luas** (2,7%). Satu garis turnover
> 2019–2025 tanpa penanda akan menampilkan lompatan 10× yang tidak pernah terjadi (F-049).
>
> Ketiganya — F-040, F-045, F-049 — satu keluarga masalah: **angka PLN tidak bisa
> dideretkan begitu saja lintas tahun.**

---

## Kolom lintas-tabel

| Kolom | Ada di | Guna |
|---|---|---|
| `sumber_sistem` | semua tabel fakta | memisahkan data nyata dari yang `DIMODELKAN` |
| `sumber_rekrutmen` | gelombang, pendaftaran, seleksi_tahap | perbandingan antar-jalur |
| `kualitas_kohort` | gelombang, kandidat, pendaftaran | peringatan saat membandingkan antar tahun |
| `tahun_program` | semua | kunci waktu utama — **bukan** tahun prajabatan |

Keempatnya yang memungkinkan dashboard menjawab pertanyaan inti proyek: **"mana yang
sudah kita punya, dan mana yang masih perlu ditambahkan?"**
