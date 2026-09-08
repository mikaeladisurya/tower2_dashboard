# Skema mockdbv3 — Section 6: PENEMPATAN

Status: **draft, menunggu review user.** Belum ada data, belum ada DDL final.

Prinsip yang dipakai di seluruh skema ini:

1. Setiap tabel entitas punya **primary key surrogate** (`id`), bukan nama/teks bisnis.
2. **Tidak ada nilai agregat/turunan** yang disimpan (mis. realisasi pagu, jumlah terisi) —
   dihitung saat query.
3. **Tidak ada kolom "untuk generator/analis"**. Tabel berbentuk seperti database produksi.
4. Apa pun yang **berubah menurut waktu** disimpan sebagai baris ber-periode, bukan kolom
   "current" yang ditimpa terus.
5. Kosakata yang **dipakai untuk join/filter lintas tabel** diberi tabel lookup sendiri.
6. **Usulan dan keputusan adalah dua kejadian berbeda** → dua tabel berbeda.
7. Atribut milik induk tidak disalin ke anak.

---

## Batas section ini

Baris tahap pasca-seleksi — samapta, pembidangan, OJT, ujian OJT, SK penempatan — sudah ada
di `pendaftaran_tahap` (section PENDAFTARAN). Section ini **tidak mengulanginya**. Yang
ditambahkan di sini hanya **isi keputusannya**: bidang apa, unit OJT mana, unit dan jabatan
di SK, grade berapa, profesi_rekrutmen apa.

Pembagiannya begini:

| pertanyaan | dijawab oleh |
|---|---|
| dia sampai tahap mana, kapan, lolos atau tidak | `pendaftaran_tahap` |
| dia dibidangkan ke sub bidang apa | `pembidangan` |
| dia OJT di unit mana | `penempatan_ojt` |
| dia jadi calon pegawai kapan, diangkat kapan, NIP berapa | `pegawai` |
| dia akhirnya ditempatkan di posisi mana, grade berapa | `sk_penempatan` |

Section ini juga tempat keluhan BPO akhirnya bisa dihitung, dan itu dibahas di bagian
tersendiri di bawah.

---

## A. Pembidangan

### `pembidangan`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `pendaftaran_tahap_id` | INTEGER FK → `pendaftaran_tahap.id` | baris tahap `pembidangan` |
| `sub_bidang_id` | INTEGER FK → `sub_bidang.id` | |

UNIQUE (`pendaftaran_tahap_id`)

Contoh isi:

```
 id  pendaftaran_tahap  sub_bidang
  1        110          Distribusi
  2        126          Transmisi
  3        134          Keuangan
```

Kolom `tanggal` dibuang: tanggalnya sudah ada di `pendaftaran_tahap.tanggal` milik baris yang
ditunjuk. Menyimpannya dua kali melanggar prinsip 7 dan membuka peluang dua tanggal berbeda
untuk satu kejadian yang sama.

**Beberapa profesi_rekrutmen bisa berbagi satu bidang** — dikonfirmasi. Analyst Keuangan dan Officer
Akuntansi dua profesi_rekrutmen berbeda, tapi pembidangannya sama: KEUANGAN. Itu sebabnya yang disimpan
di sini `sub_bidang_id`, bukan profesi_rekrutmen.

Dan karena `profesi_rekrutmen` di MASTER juga menunjuk `sub_bidang_id`, konsistensinya jadi bisa diuji:
sub bidang hasil pembidangan seseorang harus sama dengan sub bidang profesi_rekrutmen yang akhirnya
ditulis di SK-nya. Orang yang dibidangkan ke KEUANGAN tidak masuk akal berakhir sebagai
Technician Distribusi.

**Bidang bukan pilihan peserta dan bukan salinan dari apa pun.** Ia keputusan tersendiri yang
diambil setelah TTD kontrak dan samapta, dan sangat mengikuti komposisi jurusan yang dibuka
program_rekrutmen itu: angkatan berjurusan teknik dibagi ke sub bidang teknis, angkatan non-teknik ke
sub bidang non-teknis seperti Niaga.

Karena itu ia tabel sendiri, bukan kolom di `pendaftaran`. Sub bidang seseorang ditetapkan
**setelah** dia diterima, dan tidak dijamin sama dengan sub bidang yang tersirat dari
jurusannya lewat `pemetaan_jurusan_sub_bidang`. Selisih keduanya justru salah satu angka yang
menarik: berapa persen peserta berakhir di sub bidang yang bukan pasangan alami jurusannya.

Tidak ada `profesi_rekrutmen_id` di sini. Pembidangan menetapkan sub bidang; profesi_rekrutmen baru ditetapkan
di SK penempatan, setelah OJT.

---

## B. OJT

### `penempatan_ojt`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `pendaftaran_tahap_id` | INTEGER FK → `pendaftaran_tahap.id` | baris tahap `ojt` |
| `unit_id` | INTEGER FK → `unit.id` | unit tempat OJT dijalani |
| `tanggal_mulai` | DATE | |
| `tanggal_selesai` | DATE, NULL | NULL = masih berjalan |

UNIQUE (`pendaftaran_tahap_id`)

`tanggal_mulai` dan `tanggal_selesai` tetap ada dan **bukan** duplikat: `pendaftaran_tahap`
menyimpan satu tanggal kejadian, sedangkan OJT adalah rentang berbulan-bulan.

Contoh isi:

```
 id  pendaftaran_tahap  unit                                   tanggal_mulai  tanggal_selesai
  1        111          PLN Unit Induk Distribusi Jawa Barat   2024-07-01     2024-11-14
  2        127          PLN Unit Induk Transmisi Jawa Bagian…  2024-07-01     2024-11-14
  3        135          PLN Pusat Sertifikasi                  2024-07-01     2025-02-13
```

OJT mulai 1 Juli, ujian OJT digelar 3-4 bulan kemudian (sekitar pertengahan Oktober), SK
terbit November. Baris 3 selesainya Februari karena peserta itu belum lulus ujian pertama dan
tetap menjalani OJT sampai jadwal ujian berikutnya, sekitar tiga bulan sesudahnya.

**Grain-nya unit induk, bukan unit pelaksana** — dikonfirmasi. HTD menempatkan peserta OJT
sampai tingkat unit induk saja; unit induk itu sendiri yang memutuskan orangnya ditaruh di
kantor induk atau di salah satu unit pelaksananya, dan keputusan internal itu tidak sampai ke
sistem rekrutmen.

Kolomnya tetap `unit_id` biasa, bukan `unit_induk_id`, karena tabel `unit` sudah berjenjang
lewat `unit_atasan_id` — dan karena ada peserta yang OJT di unit pusat (Pusdiklat, Pusertif,
Pusmanpro) yang setara unit induk tapi bukan unit induk. Aturan "harus unit ber-level 1" tidak
bisa dijamin FK; ia dijaga saat populasi.

---

## C. Pegawai

### `pegawai`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `kandidat_id` | INTEGER FK → `kandidat.id` | |
| `nomor_pegawai` | VARCHAR UNIQUE | NIP; terbit saat TTD kontrak, sebelum samapta |
| `tanggal_mulai_calon` | DATE | tanggal TTD kontrak — mulai jadi **calon pegawai** |
| `tanggal_diangkat` | DATE, NULL | tanggal SK penempatan; NULL = masih calon pegawai |
| `tanggal_berhenti` | DATE, NULL | NULL = masih aktif |
| `alasan_berhenti_id` | INTEGER FK → `alasan_berhenti.id`, NULL | |

### `alasan_berhenti`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `nama` | VARCHAR | |

Contoh isi:

```
 id  nama
  1  Mengundurkan diri
  2  Pensiun
  3  Meninggal dunia
  4  Pemutusan hubungan kerja
  5  Tidak lulus masa percobaan
```

Contoh isi `pegawai`:

```
 id  kandidat  nomor_pegawai  tanggal_mulai_calon  tanggal_diangkat  tanggal_berhenti  alasan_berhenti
  1      2      9224001       2024-05-24           2024-11-15        NULL              NULL
  2     14      9224002       2024-05-24           2024-11-15        2026-03-31        Mengundurkan diri
  3     41      9224088       2025-05-24           NULL              NULL              NULL
```

Baris 3 masih **calon pegawai**: dia sudah TTD kontrak, sedang menjalani pasca-seleksi, dan
SK-nya belum terbit karena ujian OJT pertamanya belum lulus.

**Status calon pegawai vs pegawai adalah turunan, bukan kolom.** Tidak ada
`status_kepegawaian` di sini:

```
tanggal_diangkat IS NULL   → calon pegawai (masih di samapta/pembidangan/OJT)
tanggal_diangkat IS NOT NULL AND tanggal_berhenti IS NULL  → pegawai aktif
tanggal_berhenti IS NOT NULL → sudah keluar
```

Kolom status akan bertentangan dengan ketiga tanggal itu begitu ada satu update yang lupa —
persis pola yang dihindari di seluruh skema ini.

Tabel ini yang membuat pertanyaan-pertanyaan berikut bisa dijawab tanpa kolom penanda apa pun:

- **Pelamar yang pernah jadi pegawai** — ada baris `pegawai` untuk `kandidat_id` ini yang
  tanggal mulainya mendahului `pendaftaran.tanggal_daftar` lamaran barunya. Ini rumah untuk
  kasus "masuk lewat SMA lalu melamar bukaan S1", di bawah 50 kasus dalam 10 tahun, dengan
  lima aturan logika yang sudah ditulis di `04_kandidat.md`.
- **Pegawai baru yang keluar cepat** — `tanggal_berhenti` dikurangi `tanggal_diangkat`.
  Angka yang sangat berarti untuk menilai program_rekrutmen rekrutmen: merekrut 500 orang lalu 60 keluar
  dalam dua tahun bukan rekrutmen yang berhasil.

**Dikoreksi:** rancangan sebelumnya menyebut orang yang TTD kontrak sudah jadi **pegawai**.
Itu keliru — dia **calon pegawai**, karena masih ada sisa tahapan pasca-seleksi yang harus
dilalui: samapta, pembidangan, OJT, ujian OJT. Pengangkatan jadi pegawai terjadi di SK
penempatan.

Karena itu dua tanggal, bukan satu: `tanggal_mulai_calon` (TTD kontrak) dan `tanggal_diangkat`
(SK penempatan). Jarak keduanya sekitar 5-7 bulan, dan lebih panjang untuk yang ujian OJT-nya
harus diulang.

Baris `pegawai` tetap dibuat sejak TTD kontrak, bukan menunggu SK. Kalau menunggu, orang yang
gagal di tengah pasca-seleksi tidak akan punya jejak sama sekali padahal dia sudah terikat
kontrak dengan PLN.

Tidak ada kolom `unit_id`, `posisi_id`, atau `grade_id` di sini. Ketiganya berubah sepanjang
karier dan tempatnya di `sk_penempatan` yang bertanggal.

---

## D. SK penempatan

### `sk_penempatan`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `pegawai_id` | INTEGER FK → `pegawai.id` | |
| `pendaftaran_tahap_id` | INTEGER FK → `pendaftaran_tahap.id`, NULL | baris tahap `sk_penempatan`; NULL untuk SK di luar rekrutmen (mutasi) |
| `nomor_sk` | VARCHAR | |
| `tanggal_sk` | DATE | |
| `tanggal_berlaku` | DATE | |
| `posisi_id` | INTEGER FK → `posisi.id`, NULL | unit × jabatan; NULL untuk penempatan ke SH/AP |
| `perusahaan_id` | INTEGER FK → `perusahaan.id`, NULL | diisi hanya untuk penempatan ke SH/AP |
| `profesi_rekrutmen_id` | INTEGER FK → `profesi_rekrutmen.id` | profesi_rekrutmen yang akhirnya ditetapkan HTD |
| `grade_id` | INTEGER FK → `grade.id` | grade saat diangkat |

CHECK: tepat satu dari `posisi_id` dan `perusahaan_id` terisi.

Contoh isi:

```
 id  pegawai  tahap  nomor_sk         tanggal_sk  posisi                                 perusahaan  profesi_rekrutmen              grade
  1     1      113   0421.P/DIR/2024  2024-11-15  Engineer Distribusi @ PLN UP3 Bandung  NULL        Engineer Distribusi  G2
  2     2      129   0421.P/DIR/2024  2024-11-15  Engineer Transmisi @ PLN UPT Cirebon   NULL        Engineer Transmisi   G2
  3     3      137   0455.P/DIR/2025  2025-02-20  NULL                                   PLN Icon+   Analyst Niaga        G2
```

**Grain-nya unit pelaksana** — dikonfirmasi. `posisi_id` menunjuk pasangan unit × jabatan,
dan unit yang dituju adalah unit ber-level 2. Ini berbeda dari OJT yang hanya sampai unit
induk, dan perbedaan itu memang nyata: HTD mereview ulang setelah OJT selesai, lalu
menerbitkan SK sampai tingkat unit pelaksana.

**Satu FK, bukan pasangan `unit_id` + `jabatan_id`.** Konsekuensinya: SK tidak bisa menunjuk
jabatan yang tidak pernah ada di unit itu. Kalau ditulis dua kolom terpisah, kombinasi
"Manager Distribusi di UPT Cirebon" bisa lolos padahal jabatannya tidak ada di sana.

**`perusahaan_id` untuk penempatan ke SubHolding / Anak Perusahaan.** Sesuai kesepakatan,
mock ini berhenti di tingkat perusahaan untuk SH/AP — kita tahu orangnya ditempatkan di PLN
Icon+, tapi tidak tahu di unit apa di dalamnya. Karena `posisi` selalu milik sebuah unit di
struktur holding, baris SH/AP tidak punya `posisi_id`. CHECK di atas yang menjaga supaya
tidak ada baris berisi dua-duanya atau kosong dua-duanya.

**`profesi_rekrutmen_id` muncul pertama kali di sini.** Sepanjang pendaftaran sampai OJT, tidak ada satu
pun baris yang menyebut profesi_rekrutmen peserta — sesuai koreksi bahwa pelamar mendaftar ke program_rekrutmen
lewat daftar prodi, bukan ke profesi_rekrutmen. Profesi ditetapkan HTD di ujung, berdasarkan hasil tes,
wawancara, pembidangan, dan OJT.

**`grade_id` disimpan, walau bisa dihitung dari `aturan_grade_masuk`.** Ini pengecualian yang
disengaja: aturan grade masuk berubah antar tahun, dan yang mengikat orang adalah angka yang
tertulis di SK-nya — bukan aturan yang berlaku saat kita bertanya. Menghitung ulang berarti
grade seseorang bisa berubah surut saat aturan diperbarui.

**Tidak ada FK ke `pagu_rekrutmen`.** Ini keputusan yang paling sengaja di seluruh skema, dan
alasannya di bagian berikut.

**Beberapa SK per pegawai dimungkinkan** oleh bentuk tabel ini (mutasi, promosi), tapi mock
ini hanya membangkitkan SK pertama dari proses rekrutmen. Kolom `pendaftaran_tahap_id` boleh
NULL justru untuk itu — SK mutasi tidak lahir dari lamaran mana pun.

---

## Benang merah: satu orang dari akun sampai NIP

Diputuskan: seluruh tabel keputusan di section ini menunjuk **`pendaftaran_tahap_id`**, sama
persis dengan pola yang sudah dipakai `pendaftaran_nilai` dan `pemeriksaan_kesehatan` di
section PENDAFTARAN. Satu pola untuk seluruh skema, tanpa pengecualian.

```
kandidat (akun)                       id 2, Anisa, NIK 3273…
  └─ pendaftaran                      id 2, PLN-2024-0005190, program_rekrutmen 7
       └─ pendaftaran_tahap × 13      administrasi … sk_penempatan
            ├─ 102 adaptif            → pendaftaran_nilai
            ├─ 103 akademik_inggris   → pendaftaran_nilai (TPA, Bahasa Inggris)
            ├─ 105 fisik_mcu          → pemeriksaan_kesehatan
            ├─ 110 pembidangan        → pembidangan        (Distribusi)
            ├─ 111 ojt                → penempatan_ojt     (PLN UID Jawa Barat)
            └─ 113 sk_penempatan      → sk_penempatan      (Engineer Distribusi @ UP3 Bandung)
                                           └─ pegawai      NIP 9224001
```

Rantainya tetap terbaca: **akun id berapa → nomor pendaftaran berapa → sampai tahap mana →
NIP berapa.** Bedanya hanya satu lompatan tambahan lewat baris tahap, dan lompatan itu yang
memberi dua hal:

- Tanggal tiap kejadian hanya ada di satu tempat, yaitu `pendaftaran_tahap.tanggal`. Itu
  sebabnya `pembidangan` tidak punya kolom `tanggal`.
- Baris keputusan tidak bisa ada untuk orang yang tidak pernah menjalani tahapnya. Tidak ada
  baris pembidangan untuk peserta yang gugur di psikologi.

`pegawai` menempel ke `kandidat`, bukan ke lamaran, karena orangnya bisa punya lebih dari satu
lamaran sepanjang hidup tapi hanya satu identitas pegawai. Jembatan dari lamaran ke NIP lewat
`sk_penempatan.pendaftaran_tahap_id` → `pendaftaran_tahap.pendaftaran_id`.

**Konsekuensi kolom `kesempatan_ke`:** karena ujian OJT bisa diulang, satu lamaran bisa punya
beberapa baris `ujian_ojt`. Tabel di section ini tidak terpengaruh — tidak ada satu pun yang
menunjuk baris ujian OJT. Yang menunjuk baris `sk_penempatan` cuma satu, dan SK memang hanya
terbit sekali.

---

## Di sinilah keluhan BPO bisa dihitung

Keluhan yang muncul di requirement gathering: **perencanaan dan penempatan akhir di lapangan
sebagian tidak sesuai.** Seluruh rangkaian keputusan desain sejak section PERENCANAAN dibuat
supaya selisih itu tidak hilang, dan di sini titik ukurnya.

Rantai rencananya:

```
usulan_kebutuhan (unit)  →  pagu_rekrutmen (HST, per posisi)
  →  bukaan_profesi + kuota (HTD, per profesi_rekrutmen)  →  ... proses seleksi ...
  →  sk_penempatan (per posisi, per profesi_rekrutmen)
```

Empat selisih yang sekarang bisa dihitung, semuanya tanpa kolom tambahan:

| selisih | dihitung dari |
|---|---|
| unit mengusulkan berapa vs pagu menetapkan berapa | `usulan_kebutuhan` vs `pagu_rekrutmen` |
| pagu menetapkan berapa vs kuota diumumkan berapa | `pagu_rekrutmen` vs `bukaan_profesi.kuota` |
| kuota diumumkan berapa vs berapa yang benar-benar diterima | `bukaan_profesi.kuota` vs hitung `sk_penempatan` per profesi_rekrutmen |
| **posisi mana yang direncanakan vs posisi mana yang benar-benar diisi** | `pagu_rekrutmen.posisi_id` vs `sk_penempatan.posisi_id` |

Baris terakhir itu inti keluhannya, dan ia bisa dijawab **justru karena** `sk_penempatan`
tidak punya FK ke `pagu_rekrutmen`. Kalau ada FK, tiap SK dipaksa menunjuk sebuah baris pagu,
dan penempatan yang tidak sesuai rencana jadi mustahil dimasukkan ke basis data — bukan karena
tidak terjadi, tapi karena skemanya melarang. Ketidaksesuaian yang jadi alasan dashboard ini
dibuat akan lenyap dari data.

Keduanya menunjuk `posisi_id` yang sama, jadi perbandingannya tetap tepat tanpa FK:

```sql
-- posisi yang dipagu tapi tidak pernah terisi, dan sebaliknya
SELECT p.posisi_id, SUM(p.jumlah_pagu) AS direncanakan, COUNT(sk.id) AS terisi
FROM pagu_rekrutmen p
FULL OUTER JOIN sk_penempatan sk ON sk.posisi_id = p.posisi_id
GROUP BY p.posisi_id
```

Aturan untuk generator: **jangan paksa SK cocok dengan pagu.** Sebagian memang harus tidak
cocok — itu fenomena yang sedang diukur, bukan cacat data. Angka berapa persennya perlu
dikalibrasi bersama saat populasi.

---

## Perpindahan antara OJT dan SK

Dikonfirmasi, dan ini aturan populasi yang penting karena menentukan apakah datanya terasa
nyata:

| kelompok | perilaku |
|---|---|
| umum | **5-10%** pindah unit induk antara OJT dan SK |
| jenjang S2 ke atas | **~90%** berpindah unit induk |
| yang OJT di Kantor Pusat / unit pusat | biasanya **tetap di situ** saat SK terbit |

Karena `penempatan_ojt.unit_id` menunjuk unit induk dan `sk_penempatan.posisi_id` menunjuk
unit pelaksana, membandingkan keduanya perlu naik satu lapis dulu lewat `unit_atasan_id`:

```sql
-- unit induk saat OJT vs unit induk dari posisi di SK
ojt.unit_id  vs  (SELECT unit_atasan_id FROM unit WHERE id = (
                    SELECT unit_id FROM posisi WHERE id = sk.posisi_id))
```

Angka 5-10% itu harus muncul dari perbandingan ini, bukan dipatok sebagai kolom.

---

## Flow section PENEMPATAN

```
[PENDAFTARAN] peserta lolos wawancara → pengumuman_akhir → ttd_kontrak
  → pegawai                 1 baris, tanggal_mulai_calon = tanggal TTD kontrak
                            status: CALON PEGAWAI, tanggal_diangkat masih NULL
  → [tahap samapta]         hanya baris pendaftaran_tahap, tidak ada tabel di sini
  → [tahap pembidangan]  → pembidangan        1 baris, menunjuk baris tahap itu
  → [tahap ojt]          → penempatan_ojt     1 baris, unit induk + rentang tanggal
  → [tahap ujian_ojt]       hanya baris pendaftaran_tahap + pendaftaran_nilai
  → [tahap sk_penempatan]→ sk_penempatan      1 baris, posisi/perusahaan + profesi_rekrutmen + grade
                            pegawai.tanggal_diangkat ← tanggal SK. Baru sekarang jadi PEGAWAI.
```

Empat jalur bertemu di sini tanpa perlakuan khusus sama sekali — Mandiri, Pro Hire, RBB, dan
Ikatan Dinas semuanya melewati lima langkah yang sama.

Dua hal yang tetap perlu kalibrasi terpisah saat populasi:

- **Ujian OJT peserta ikatan dinas formalitas** — tidak ada yang gagal.
- **Ujian OJT jalur lain jarang menggugurkan**, karena boleh diulang sampai tiga kali dengan
  jarak sekitar tiga bulan. Yang belum lulus tidak keluar, dia tetap OJT sampai jadwal ujian
  berikutnya. Jadi sebagian kecil peserta punya dua atau tiga baris `ujian_ojt` dengan
  `kesempatan_ke` berbeda, **dan SK-nya memang terbit belakangan** dari teman seangkatannya —
  dikonfirmasi. Selama itu dia masih berstatus calon pegawai.
- **Jarak mulai OJT ke ujian OJT pertama: 3-4 bulan** — dikonfirmasi untuk mockdbv3. Dihitung
  dari tanggal peserta mulai OJT di lokasi sampai tanggal ujian digelar.

---

## Yang sengaja tidak dibuat

**Tabel `realisasi_pagu`.** Realisasi adalah hitungan baris `sk_penempatan` per posisi. Kalau
disimpan, ia akan menyimpang dari detailnya — kesalahan yang persis terjadi di v1.

**Kolom `unit_id` / `posisi_id` / `grade_id` di `pegawai`.** Semuanya berubah sepanjang karier;
tempatnya di `sk_penempatan` yang bertanggal.

**FK dari `sk_penempatan` ke `pagu_rekrutmen`.** Lihat bagian keluhan BPO.

**Riwayat karier lengkap** (mutasi, promosi, rotasi, kenaikan grade). Bentuk tabelnya sudah
memungkinkan, tapi mock ini berhenti di SK pertama hasil rekrutmen.

**Struktur unit di dalam SubHolding / Anak Perusahaan.** Sesuai kesepakatan, penempatan SH/AP
berhenti di tingkat perusahaan.

---

## Yang perlu diputuskan

1. **Nama tabel dan kolom** — semua di atas usulan saya.
2. ~~Kapan profesi_rekrutmen ditetapkan~~ — pembidangan menetapkan **sub bidang** (beberapa profesi_rekrutmen bisa
   berbagi satu bidang: Analyst Keuangan dan Officer Akuntansi sama-sama KEUANGAN), profesi_rekrutmen
   sendiri baru ditulis di SK. Kolomnya tetap di tempat masing-masing.
3. ~~Nomor pegawai terbit kapan~~ — diputuskan: TTD kontrak terjadi **setelah lulus wawancara,
   sebelum samapta**, dan sejak itu orangnya sudah pegawai. `pegawai.nomor_pegawai` NOT NULL,
   `tanggal_mulai_kerja` = tanggal TTD kontrak.
4. ~~Peserta gagal di masa OJT~~ — diputuskan: **jarang gagal**, karena ujian OJT bisa diulang
   sampai tiga kali dengan jarak sekitar tiga bulan. Yang belum lulus tetap OJT sampai jadwal
   ujian berikutnya. Diterapkan lewat kolom `kesempatan_ke` di `pendaftaran_tahap`.
5. ~~Jabatan struktural~~ — diputuskan: tidak ada untuk mockdbv3. Populasi wajib memfilter
   `posisi` lewat `kelompok_jabatan.is_struktural = false`.
6. ~~Berapa lama OJT normalnya~~ — diputuskan: **3-4 bulan** dari mulai OJT di lokasi sampai
   ujian OJT digelar. Percobaan berikutnya sekitar tiga bulan sesudahnya.
7. ~~Nomor pegawai terbit kapan~~ — diputuskan: **saat TTD kontrak, sebelum samapta**. NIP
   sudah ada sejak masa calon pegawai, jadi `nomor_pegawai` NOT NULL.

---

## Daftar tabel section PENEMPATAN (5 tabel)

| # | tabel | fungsi |
|---|---|---|
| 1 | `pembidangan` | sub bidang yang ditetapkan setelah samapta |
| 2 | `penempatan_ojt` | unit induk tempat OJT dijalani |
| 3 | `pegawai` | orang yang sudah jadi pegawai, beserta akhir masa kerjanya |
| 4 | `alasan_berhenti` | lookup sebab berhenti |
| 5 | `sk_penempatan` | keputusan akhir: posisi, profesi_rekrutmen, grade |
