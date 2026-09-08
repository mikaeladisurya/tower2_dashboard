# Skema mockdbv3 — Section 5: PENDAFTARAN

Status: **draft, menunggu review user.** Belum ada data, belum ada DDL final.

Prinsip yang dipakai di seluruh skema ini:

1. Setiap tabel entitas punya **primary key surrogate** (`id`), bukan nama/teks bisnis.
2. **Tidak ada nilai agregat/turunan** yang disimpan (mis. jumlah pelamar, tingkat kelulusan,
   status terakhir) — dihitung saat query.
3. **Tidak ada kolom "untuk generator/analis"**. Tabel berbentuk seperti database produksi.
4. Apa pun yang **berubah menurut waktu** disimpan sebagai baris ber-periode, bukan kolom
   "current" yang ditimpa terus.
5. Kosakata yang **dipakai untuk join/filter lintas tabel** diberi tabel lookup sendiri.
6. **Usulan dan keputusan adalah dua kejadian berbeda** → dua tabel berbeda.
7. Atribut milik induk tidak disalin ke anak.

---

## Batas section ini

Section ini menghubungkan **orang** (KANDIDAT) dengan **bukaan** (PROGRAM), lalu mencatat apa
yang terjadi pada orang itu di tiap tahap.

Grain lamaran: **satu kandidat × satu program_rekrutmen**. Bukan per profesi_rekrutmen, bukan per unit.

Ini koreksi dari rancangan sebelumnya, yang memasang `bukaan_profesi_id` di `pendaftaran`.
Dikonfirmasi user: yang dilihat pelamar adalah **daftar program_rekrutmen studi yang dibuka**, bukan
daftar profesi_rekrutmen. Profesi seseorang baru ditetapkan HTD di belakang, berdasarkan nilai tes,
wawancara, pembidangan, dan OJT.

| sisi | melihat apa |
|---|---|
| penyelenggara (HST/HTD) | profesi_rekrutmen + kuota tiap profesi_rekrutmen |
| pelamar | program_rekrutmen studi apa saja yang boleh mendaftar |

Prodi yang dipakai melamar tidak perlu kolom sendiri — sudah terkandung di ijazah yang
dipilih pelamar (`kandidat_pendidikan_id` → `institusi_jurusan` → `jurusan`).
Daftar prodi yang diumumkan juga tidak perlu tabel baru: ia DISTINCT prodi dari seluruh
`bukaan_profesi` milik program_rekrutmen itu.

Tahapnya berlanjut melewati titik seseorang jadi pegawai. Baris tahap untuk samapta,
pembidangan, OJT, ujian OJT, dan SK penempatan **tetap ditulis di sini**, di tabel yang sama,
karena bentuk kejadiannya identik: tanggal, hasil, kadang nilai. Yang pindah ke PENEMPATAN
bukan barisnya, melainkan **isi keputusannya** — bidang hasil pembidangan, unit OJT, unit di
SK. Kalau dipisah jadi dua tabel tahap, tiap pertanyaan "sampai tahap mana orang ini" harus
UNION dua tabel selamanya.

---

## A. Lamaran

### `pendaftaran`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `kandidat_id` | INTEGER FK → `kandidat.id` | |
| `program_rekrutmen_id` | INTEGER FK → `program_rekrutmen.id` | program_rekrutmen yang dilamar |
| `nomor_pendaftaran` | VARCHAR UNIQUE | nomor peserta di sistem PLN; tim HTD menyebutnya "NO TES" |
| `nomor_peserta_bumn` | VARCHAR, NULL | nomor peserta di sistem BUMN — hanya jalur RBB |
| `tanggal_daftar` | DATE | |
| `kandidat_pendidikan_id` | INTEGER FK → `kandidat_pendidikan.id` | ijazah yang dipakai melamar |
| `kandidat_data_fisik_id` | INTEGER FK → `kandidat_data_fisik.id`, NULL | data fisik yang berlaku saat melamar |
| `kota_kabupaten_domisili_id` | INTEGER FK → `kota_kabupaten.id` | salinan domisili saat melamar |
| `kota_kabupaten_tes_id` | INTEGER FK → `kota_kabupaten.id`, NULL | kota tes yang dipilih pelamar |

UNIQUE (`kandidat_id`, `program_rekrutmen_id`)

Contoh isi:

```
 id  kandidat  program_rekrutmen                              nomor_pendaftaran  no_bumn    tanggal     pendidikan (prodi)          kota_domisili  kota_tes
  1     1      PLN Group D3/S1 2024                 PLN-2024-0004821   NULL       2024-02-03  S1 Undip, Teknik Elektro    Kota Semarang  Semarang
  2     2      PLN Group D3/S1 2024                 PLN-2024-0005190   NULL       2024-02-05  S1 ITB, Teknik Elektro      Kota Bandung   Bandung
  3     3      Rekrutmen Bersama BUMN 2025          PLN-2025-0000317   RBB-88213  2025-04-11  S1 USU, Manajemen           Kota Medan     Medan
  4     1      PLN Group S2 2026                    PLN-2026-0001044   NULL       2026-01-22  S2 Undip, Teknik Elektro    Kota Semarang  Semarang
```

Baris 1 dan 4 orang yang sama melamar dua kali dengan ijazah berbeda, dua tahun berjarak.
Itulah gunanya `kandidat` dipisah dari `pendaftaran`.

UNIQUE (`kandidat_id`, `program_rekrutmen_id`) sekaligus menjawab pertanyaan terbuka sebelumnya: satu
orang punya paling banyak satu lamaran per program_rekrutmen, karena tidak ada lagi profesi_rekrutmen untuk
dipilih ganda.

**`nomor_pendaftaran` — tiga nomor berbeda, jangan tertukar.** Dikonfirmasi:

| nomor | milik | terbit kapan |
|---|---|---|
| id/nomor akun di web rekrutmen | `kandidat` | saat orang membuat akun |
| **nomor pendaftaran / NO TES** | `pendaftaran` | setelah mendaftar ke satu program |
| NIP | `pegawai` | saat TTD kontrak |

Contoh format asli dari berkas HTD: `2511/ES/92/D3-ELE/135615` — di dalamnya sudah terkandung
angkatan (92) dan jurusan (D3-ELE). Namanya tetap `nomor_pendaftaran`, bukan `nomor_tes`,
mengikuti kebiasaan penamaanmu sendiri: kolom membawa nama tabelnya, seperti `nomor_kontrak`
di tabel kontrak. "NO TES" ditulis di keterangan supaya kosakata HTD tetap terlacak.

**`nomor_peserta_bumn`** — dikonfirmasi wajib ada, NULL untuk jalur selain RBB. Selain untuk
merujuk orang balik ke sumbernya, ini satu-satunya bukti di basis data bahwa tahap
administrasi dan adaptif memang terjadi di sistem BUMN walau PLN tidak mencatat hasilnya.

**`kandidat_pendidikan_id`** kini memikul dua tugas. Pertama, menjawab pertanyaan yang tidak
bisa dijawab kalau hanya menyimpan `kandidat_id`: orang yang punya ijazah SMK, S1, dan S2
melamar dengan yang mana? Untuk baris 4 jawabannya S2, dan itu yang menentukan
`syarat_pelamar` mana yang berlaku serta grade masuknya lewat `aturan_grade_masuk`.

Kedua, **ia yang membawa program_rekrutmen studi pelamar**. Karena yang dibuka ke publik adalah daftar
prodi, syarat sah sebuah lamaran adalah: prodi dari ijazah ini ada di daftar prodi program_rekrutmen
tersebut. Aturannya:

```sql
-- prodi pelamar harus muncul di salah satu bukaan_profesi program_rekrutmen ini
kandidat_pendidikan → institusi_jurusan → jurusan_id
  ADA DI (SELECT jurusan_id
          FROM bukaan_profesi_jurusan bps
          JOIN bukaan_profesi bp ON bp.id = bps.bukaan_profesi_id
          WHERE bp.program_rekrutmen_id = pendaftaran.program_rekrutmen_id)
```

Tidak bisa dijamin FK biasa — harus dijaga saat populasi dan layak jadi tes.

**`kandidat_data_fisik_id`** menunjuk baris data fisik yang berlaku saat itu, bukan menyalin
13 kolomnya. Ini bisa berupa FK karena `kandidat_data_fisik` bertanggal dan tidak pernah
ditimpa — barisnya akan tetap ada apa adanya sepuluh tahun lagi. NULL wajar untuk kandidat RBB
yang datanya belum pernah diminta PLN.

**`kota_kabupaten_domisili_id` justru disalin, bukan FK ke `kandidat_alamat`.** Alasannya persis
kebalikan dari yang di atas: `kandidat_alamat` **ditimpa** setiap kandidat memperbarui profil,
jadi FK ke sana akan ikut berubah dan sebaran pelamar 2024 berubah surut ketika orangnya
pindah kota pada 2026. Satu-satunya cara mengunci nilainya adalah menyalin.

Aturan ini yang membedakan kapan boleh FK dan kapan harus salin, dan berlaku untuk seluruh
skema: **FK ke baris yang tidak pernah berubah, salin dari baris yang ditimpa.**

**`kota_kabupaten_tes_id`** pilihan pelamar saat mendaftar, dan **berlaku untuk seluruh tahap** —
dikonfirmasi. Program dibuka di beberapa kota, pelamar memilih satu, lalu mengikuti semua
tahap di kota itu. Boleh NULL untuk jalur yang tidak menawarkan pilihan (Ikatan Dinas).

Karena itu `pendaftaran_tahap.lokasi_tes_id` bukan pilihan baru tiap tahap, melainkan
**venue** di dalam kota yang sudah dipilih: gedung mana, alamatnya di mana — ditentukan tim
HTD dan vendor di masing-masing kota. Aturan konsistensinya: `lokasi_tes` yang ditunjuk tiap
baris tahap harus berada di kota yang sama dengan `pendaftaran.kota_kabupaten_tes_id`. Ini tidak bisa
dipaksakan lewat FK biasa dan harus dijaga saat populasi.

**Tidak ada kolom `status` atau `tahap_terakhir`.** Keduanya turunan penuh dari
`pendaftaran_tahap` dan akan bertentangan dengan barisnya begitu ada satu update yang lupa.
"Sampai tahap mana orang ini" = ambil baris tahapnya dengan `urutan` tertinggi.

**Tidak ada kolom `diterima`.** Diterima artinya punya baris tahap SK penempatan berhasil.

**Tidak ada kolom `profesi_rekrutmen_id`.** Profesi bukan pilihan pelamar. Ia ditetapkan HTD di ujung,
dan tempatnya di section PENEMPATAN bersama hasil pembidangan dan SK. Ini yang membuat
keluhan BPO bisa diukur: kuota per profesi_rekrutmen direncanakan di `bukaan_profesi` jauh di depan,
sedangkan profesi_rekrutmen yang benar-benar terisi baru ketahuan setelah OJT — dan selisih keduanya
kelihatan tanpa perlu kolom khusus.

---

## B. Kejadian per tahap

### `alasan_gugur`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `nama` | VARCHAR | |

Contoh isi:

```
 id  nama
  1  Nilai di bawah ambang
  2  Peringkat di bawah kuota
  3  Tidak memenuhi syarat administrasi
  4  Tidak hadir
  5  Mengundurkan diri
  6  Tidak memenuhi syarat kesehatan
  7  Dibatalkan panitia
```

Dipisah dari `hasil` karena dua hal berbeda: `hasil` menjawab lanjut atau tidak, `alasan_gugur`
menjawab kenapa. "Tidak Lolos karena nilai" dan "Tidak Lolos karena mengundurkan diri" adalah
angka yang sangat berbeda artinya bagi tim HTD — yang satu soal mutu pelamar, yang satu soal
daya tarik PLN sebagai tempat kerja.

### `pendaftaran_tahap`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `pendaftaran_id` | INTEGER FK → `pendaftaran.id` | |
| `tahap_program_id` | INTEGER FK → `tahap_program.id` | tahap mana di program_rekrutmen mana |
| `kesempatan_ke` | INTEGER | 1 untuk kesempatan pertama; >1 hanya untuk tahap yang boleh diulang |
| `tanggal_pelaksanaan` | DATE | tanggal peserta menjalani tahap ini |
| `hasil_tahap` | VARCHAR | Lolos / Tidak Lolos / Tidak Hadir / Mengundurkan Diri |
| `alasan_gugur_id` | INTEGER FK → `alasan_gugur.id`, NULL | NULL kalau hasilnya Lolos |
| `lokasi_tes_id` | INTEGER FK → `lokasi_tes.id`, NULL | NULL untuk tahap online |

UNIQUE (`pendaftaran_id`, `tahap_program_id`, `kesempatan_ke`)

**`kesempatan_ke` ditambahkan karena ujian OJT boleh diulang** — dikonfirmasi. Ujiannya
digelar berkala sekitar tiga bulan sekali; yang belum lulus tetap menjalani OJT sampai jadwal
ujian berikutnya, dan bisa mencoba sampai tiga kali. Contoh: ujian Juli, keputusan Agustus,
yang belum lulus ikut lagi September.

**Jarak OJT ke ujian pertama: 3-4 bulan** — dikonfirmasi untuk mockdbv3. Dihitung dari tanggal
peserta mulai OJT di lokasi sampai tanggal ujian OJT digelar. Percobaan berikutnya sekitar
tiga bulan sesudahnya.

Tanpa kolom ini, kunci lama (`pendaftaran_id`, `tahap_program_id`) melarang percobaan kedua
masuk ke basis data sama sekali — percobaan pertama harus ditimpa, dan riwayat "berapa orang
lulus di percobaan kedua" hilang.

```
 pendaftaran  tahap      kesempatan_ke  tanggal     hasil
     41       ujian_ojt        1        2025-11-20  Tidak Lolos
     41       ujian_ojt        2        2026-02-18  Lolos
```

Untuk tahap lain nilainya selalu 1. "Lulus tahap ini atau tidak" = baris dengan
`kesempatan_ke` tertinggi.

Contoh isi (pendaftaran 1, jalur Mandiri, gugur di psikologi):

```
 id  pendaftaran  tahap            tanggal     hasil        alasan_gugur           lokasi_tes
  1       1       administrasi     2024-02-10  Lolos        NULL                   NULL
  2       1       adaptif          2024-02-24  Lolos        NULL                   NULL
  3       1       akademik_inggris 2024-03-09  Lolos        NULL                   Semarang
  4       1       psikologi        2024-03-23  Tidak Lolos  Nilai di bawah ambang  Semarang
```

**Tidak ada baris untuk tahap sesudah gugur.** Pendaftaran 1 berhenti di baris 4 — tidak ada
baris MCU ber-hasil "Tidak Diproses". Menulis baris untuk tahap yang tidak pernah dijalani
berarti mengarang kejadian, dan membuat setiap hitungan "berapa peserta ikut tahap MCU" salah
kecuali orang ingat memfilternya.

Contoh isi (pendaftaran 3, jalur RBB, lolos sampai jadi pegawai):

```
 id  pendaftaran  tahap            tanggal     hasil  alasan_gugur  lokasi_tes
 20       3       akademik_inggris 2025-05-06  Lolos  NULL          Medan
 21       3       psikologi        2025-05-20  Lolos  NULL          Medan
 22       3       fisik_mcu        2025-06-03  Lolos  NULL          Medan
 23       3       wawancara        2025-06-17  Lolos  NULL          Medan
 24       3       pengumuman_akhir 2025-07-01  Lolos  NULL          NULL
 25       3       ttd_kontrak      2025-07-15  Lolos  NULL          NULL
 26       3       samapta          2025-07-28  Lolos  NULL          NULL
 27       3       pembidangan      2025-08-08  Lolos  NULL          NULL
 28       3       ojt              2025-08-18  Lolos  NULL          NULL
 29       3       ujian_ojt        2025-11-20  Lolos  NULL          NULL
 30       3       sk_penempatan    2025-12-15  Lolos  NULL          NULL
```

Perhatikan tahap pertamanya `akademik_inggris`, bukan `administrasi`. **Kandidat RBB memang
tidak punya baris administrasi dan adaptif** — kedua tahap itu berjalan di sistem BUMN dan
tidak pernah dicatat PLN. Ini bukan data bolong, dan tidak boleh "diperbaiki" oleh generator.

Baris 26-30 adalah tahap pasca-seleksi, tetap di tabel ini. Isi keputusannya — bidang apa,
unit OJT mana, unit SK mana — ada di section PENEMPATAN.

`lokasi_tes_id` menunjuk ke `lokasi_tes` di PROGRAM, bukan langsung ke `kota_kabupaten`.
Efeknya: peserta tidak bisa tercatat tes di kota yang tidak pernah dibuka untuk tahap itu.

---

## C. Nilai

`komponen_nilai` — daftar komponen tiap tahap — **pindah ke MASTER**, dan ambang per komponen
jadi `tahap_program_komponen` di PROGRAM. Lihat bagian "Ambang per komponen" di bawah.

### `pendaftaran_nilai`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `pendaftaran_tahap_id` | INTEGER FK → `pendaftaran_tahap.id` | |
| `komponen_nilai_id` | INTEGER FK → `komponen_nilai.id` | |
| `nilai` | DECIMAL(5,2) | |

UNIQUE (`pendaftaran_tahap_id`, `komponen_nilai_id`)

Contoh isi (tahap 3 di atas — akademik_inggris pendaftaran 1):

```
 id  pendaftaran_tahap  komponen        nilai
  1         3           TPA             78.50
  2         3           Bahasa Inggris  62.00
```

Format panjang, bukan kolom `nilai_1` sampai `nilai_5`. Alasannya: jumlah komponen berbeda
per tahap dan berubah antar tahun. Dengan bentuk ini, menambah komponen "Learning Agility"
pada 2027 cukup satu baris `komponen_nilai` baru, bukan mengubah struktur tabel yang sudah
berisi jutaan baris.

Perhatikan `pendaftaran_tahap` **tidak** punya kolom `nilai` sendiri. Kalau ada, akan langsung
muncul pertanyaan "nilai yang mana" untuk tahap dua komponen seperti di atas, dan jawaban apa
pun yang dipilih akan salah untuk sebagian analisis. Nilai gabungan dihitung saat query.

Tahap tanpa nilai — administrasi, MCU, pengumuman, TTD kontrak, pembidangan, OJT, SK — tidak
punya baris di sini sama sekali. Hasilnya cukup di `pendaftaran_tahap.hasil`.

---

## D. Kesehatan

### `pemeriksaan_kesehatan`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `pendaftaran_tahap_id` | INTEGER FK → `pendaftaran_tahap.id` | tahap `fisik_mcu` yang bersangkutan |
| `tinggi_badan` | INTEGER | cm |
| `berat_badan` | DECIMAL(5,2) | kg |
| `lingkar_perut` | INTEGER, NULL | cm |
| `visus_kiri` | DECIMAL(3,1), NULL | |
| `visus_kanan` | DECIMAL(3,1), NULL | |
| `is_buta_warna` | BOOLEAN | |
| `tekanan_darah_sistolik` | INTEGER, NULL | |
| `tekanan_darah_diastolik` | INTEGER, NULL | |
| `gula_darah_puasa` | INTEGER, NULL | mg/dL |
| `kolesterol_total` | INTEGER, NULL | mg/dL |
| `status_merokok` | VARCHAR, NULL | Tidak / Ya / Pernah |
| `kondisi_gigi` | VARCHAR, NULL | Baik / Perlu Perawatan / Bermasalah |
| `kesimpulan_mcu` | VARCHAR | Memenuhi Syarat / Memenuhi Syarat dengan Catatan / Tidak Memenuhi Syarat |

UNIQUE (`pendaftaran_tahap_id`)

Contoh isi:

```
 id  tahap  tinggi  berat  lingkar  visus_ki/ka  is_buta_warna  TD      gula  kolesterol  merokok  gigi              kesimpulan
  1   22     170    82.0     94      1.0 / 0.8     false     138/88  112     238        Ya      Perlu Perawatan   Memenuhi Syarat dengan Catatan
  2   41     165    58.0     74      1.0 / 1.0     false     118/76   88     174        Tidak   Baik              Memenuhi Syarat
```

Empat kolom terakhir ditambahkan atas usulanmu: merokok, gigi, kolesterol, gula darah.
Semuanya NULL-able karena tidak setiap program_rekrutmen memeriksa semuanya, dan kandidat RBB bisa
membawa hasil MCU dari pemeriksaan yang cakupannya berbeda.

Yang perlu diingat saat populasi: **merokok dan kolesterol tinggi jarang membuat orang gugur
langsung** — biasanya jatuh ke "Memenuhi Syarat dengan Catatan", seperti baris 1. Yang benar-
benar menggugurkan biasanya buta warna untuk profesi_rekrutmen teknik, dan temuan berat lain. Kalau
generator membuat perokok gugur MCU, angkanya akan menyesatkan.

**Ini hasil ukur vendor, bukan deklarasi kandidat.** Kembarannya di
`kandidat_data_fisik` adalah apa yang orangnya ketik sendiri di akun. Sengaja dipisah, dan
selisih keduanya justru angka yang menarik: berapa persen pelamar salah melaporkan berat
badannya, dan apakah yang selisihnya besar lebih sering gugur MCU.

Tidak ada `bmi` di sini juga — sama alasannya dengan di `kandidat_data_fisik`.

Vendor pelaksananya tidak diulang di sini; sudah melekat pada `tahap_program.vendor_id`.

---

## Contoh utuh: satu program_rekrutmen dari bukaan sampai peserta

Ini menjawab "bukaan itu apa". **Bukaan profesi_rekrutmen** adalah satu baris di `bukaan_profesi`: satu
profesi_rekrutmen yang dibuka oleh satu program_rekrutmen, beserta kuotanya. Satu program_rekrutmen membuka beberapa
profesi_rekrutmen sekaligus, dan pelamar memilih **satu** di antaranya.

**1. Program** (section PROGRAM)

```
program_rekrutmen 7 · "Rekrutmen PLN Group Tingkat D3/S1 Tahun 2024"
  tahun_program 2024 · angkatan 41 · jenis_program: PLN Group · jalur: MANDIRI
  buka 2024-02-01 · tutup 2024-02-20
```

**2. Bukaan profesi_rekrutmen** — apa saja yang dibuka program_rekrutmen itu, dengan kuota masing-masing

```
 id  program_rekrutmen  profesi_rekrutmen                 kuota
 21     7     Technician Distribusi    120
 22     7     Engineer Distribusi       45
 23     7     Engineer Transmisi        30
 24     7     Analyst Niaga             25
```

**3. Jurusan yang diterima tiap bukaan** (`bukaan_profesi_jurusan`)

```
 bukaan  program_rekrutmen studi
   22    Teknik Elektro
   22    Teknik Tenaga Listrik
   22    Teknik Mesin
   24    Manajemen
   24    Akuntansi
   24    Administrasi Bisnis
```

Inilah jembatan antara pagu yang berbicara soal posisi dan bukaan yang berbicara soal
jurusan — bukaan 22 memenuhi pagu Engineer Distribusi di berbagai unit lewat
`bukaan_profesi_pagu`, dan menerima tiga jurusan di atas.

**4. Venue tiap tahap** (`lokasi_tes` → `venue`)

```
 tahap_program  tahap             venue                       jenis        kota
      73        akademik_inggris  Universitas Indonesia       Kampus       Jakarta
      73        akademik_inggris  Telkom University           Kampus       Bandung
      73        akademik_inggris  Universitas Diponegoro      Kampus       Semarang
      75        fisik_mcu         Klinik Kimia Farma Bandung  Klinik       Bandung
      76        wawancara         Kantor PLN UID Jawa Barat   Kantor PLN   Bandung
```

Daftar kota program_rekrutmen ("dibuka di 5 kota") adalah DISTINCT kota dari baris-baris ini.

**5. Yang dilihat pelamar — bukan tabel, tapi turunan**

Langkah 2 dan 3 adalah kacamata penyelenggara. Pelamar tidak pernah melihatnya. Yang
diumumkan ke publik adalah DISTINCT prodi dari langkah 3:

```
Program Rekrutmen PLN Group Tingkat D3/S1 Tahun 2024
Program studi yang dibuka:
  Teknik Elektro · Teknik Tenaga Listrik · Teknik Mesin
  Manajemen · Akuntansi · Administrasi Bisnis
```

Tidak ada tabel baru untuk ini — ia query atas `bukaan_profesi_jurusan`.

**6. Kandidat mendaftar**

Anisa (kandidat 2, S1 Teknik Elektro ITB, domisili Kota Bandung) melihat Teknik Elektro ada
di daftar, lalu mendaftar ke **program_rekrutmen**-nya. Dia tidak memilih profesi_rekrutmen — dan memang tidak
tahu akan berakhir sebagai Engineer Distribusi atau Engineer Transmisi.

```
pendaftaran
 id  kandidat  program_rekrutmen  nomor_pendaftaran  tanggal     pendidikan                kota_domisili  kota_tes
  2      2        7     PLN-2024-0005190   2024-02-05  S1 ITB, Teknik Elektro    Kota Bandung   Bandung
```

Satu baris. Dia memilih kota tes Bandung di awal, dan seluruh tahapnya digelar di sana.
Profesinya baru ditetapkan setelah pembidangan dan OJT — di section PENEMPATAN.

**7. Yang terjadi berikutnya**

```
pendaftaran_tahap (pendaftaran 2)
 tahap             tanggal     hasil  lokasi_tes
 administrasi      2024-02-24  Lolos  NULL             ← daring, tidak ada venue
 adaptif           2024-03-02  Lolos  NULL
 akademik_inggris  2024-03-16  Lolos  Telkom University
 psikologi         2024-03-30  Lolos  Telkom University
 fisik_mcu         2024-04-13  Lolos  Klinik Kimia Farma Bandung
 wawancara         2024-04-27  Lolos  Kantor PLN UID Jabar
 pengumuman_akhir  2024-05-10  Lolos  NULL
 ttd_kontrak       2024-05-24  Lolos  NULL

pendaftaran_nilai (tahap akademik_inggris)
 komponen        nilai   ambang di tahap_program_komponen
 TPA             81.00   65.00   ← lolos
 Bahasa Inggris  57.50   50.00   ← lolos

pemeriksaan_kesehatan (tahap fisik_mcu)
 tinggi 159 · berat 52.0 · visus 1.0/1.0 · is_buta_warna false
 TD 118/76 · gula 88 · kolesterol 174 · merokok Tidak · gigi Baik
 kesimpulan: Memenuhi Syarat
```

Selama seluruh proses ini, tidak ada satu pun baris yang menyebut profesi_rekrutmen Anisa. Kuota 45
Engineer Distribusi di langkah 2 adalah rencana; siapa yang benar-benar mengisinya baru
ketahuan setelah pembidangan dan OJT.

---

## Flow section PENDAFTARAN

```
[KANDIDAT] orang sudah punya baris kandidat
[PROGRAM]  bukaan_profesi sudah dibuka, tahap_program sudah tersusun

  → pendaftaran                1 baris, menunjuk kandidat + bukaan_profesi
                               menyalin kota domisili, menunjuk ijazah & data fisik
  → pendaftaran_tahap          1 baris tiap tahap yang BENAR-BENAR dijalani
       ├─ pendaftaran_nilai    0-n baris, hanya untuk tahap bernilai
       └─ pemeriksaan_kesehatan 1 baris, hanya untuk tahap fisik_mcu
  → berhenti di baris terakhir kalau gugur — tidak ada baris sesudahnya
  → kalau lolos terus sampai sk_penempatan, keputusan penempatannya di PENEMPATAN
```

Empat jalur masuk dari KANDIDAT bertemu di sini dengan bentuk yang berbeda-beda:

| jalur | tahap pertama yang punya baris | catatan |
|---|---|---|
| Mandiri | `administrasi` | lengkap dari awal |
| Pro Hire | `administrasi` | pengalaman kerja dicek di tahap ini |
| RBB | `akademik_inggris` | administrasi & adaptif di sistem BUMN, `nomor_peserta_bumn` terisi |
| Ikatan Dinas | `samapta` | seluruh tahap seleksi terjadi 3-4 tahun sebelumnya dan tidak dilacak |

Tabel ini yang membuat keempatnya bisa dihitung bersama sejak samapta tanpa perlakuan khusus.

---

## Cara mengisi venue nanti

Pertanyaanmu soal populasi venue dijawab di sini supaya tidak hilang.

Venue tidak diacak. Urutannya tiga langkah:

**1. Kolam venue per kota, dibuat sekali di MASTER.** Untuk tiap kota yang pernah jadi lokasi
tes, siapkan beberapa baris `venue` dengan `jenis` yang berbeda — misal 2-3 kampus, 1 kantor
PLN, 1-2 klinik/RS. Nama kampus dan kantor PLN bisa memakai yang benar-benar ada; klinik boleh
nama umum. Jumlahnya tidak perlu banyak: 5-6 venue per kota sudah cukup untuk 10 tahun data.

**2. Cocokkan jenis venue dengan tahap.** Ini aturan yang membuat hasilnya masuk akal:

| tahap | jenis venue |
|---|---|
| administrasi, adaptif | tidak ada venue — daring, `lokasi_tes_id` NULL |
| akademik_inggris, psikologi | Kampus / Gedung Serbaguna |
| fisik_mcu | Klinik / Rumah Sakit |
| wawancara | Kantor PLN |
| samapta | Kantor PLN / lokasi diklat |
| pembidangan, OJT, ujian OJT, SK | unit PLN — bukan venue tes |

**3. Venue tetap antar tahun, tidak berganti tiap program_rekrutmen.** Kalau tes Semarang 2023 di Undip,
2024 juga wajar di Undip. Mengacak venue tiap tahun bikin pertanyaan "venue mana yang paling
sering dipakai" jadi tidak berarti, padahal itu salah satu gunanya tabel ini.

Yang tidak boleh: peserta tercatat tes di venue yang kotanya berbeda dari
`pendaftaran.kota_kabupaten_tes_id`. Aturan ini tidak bisa dipaksakan lewat FK dan harus jadi tes saat
populasi.

---

## Yang sengaja tidak dibuat

**Kolom `status` / `tahap_terakhir` / `is_lolos` di `pendaftaran`.** Turunan penuh dari
`pendaftaran_tahap`.

**Baris tahap "Tidak Diproses" untuk peserta yang sudah gugur.** Lihat bagian B.

**Tabel `gelombang` seperti v1** dengan kolom `pendaftar`, `diterima_target`, `lolos_administrasi`
dan seterusnya. Semuanya angka agregat yang bisa dihitung dari tabel ini, dan di v1 justru
sering tidak cocok dengan detailnya.

**Peringkat peserta.** Peringkat berubah tergantung siapa yang ikut dihitung dan tahap mana
yang dipakai; ia hasil query, bukan fakta yang dicatat.

---

## Yang perlu diputuskan

1. **Nama tabel dan kolom** — semua di atas usulan saya.
2. ~~Satu orang boleh melamar berapa bukaan dalam satu program_rekrutmen?~~ — pertanyaannya gugur
   sendiri: pelamar tidak memilih profesi_rekrutmen. Kunci `pendaftaran` jadi (`kandidat_id`,
   `program_rekrutmen_id`), satu orang satu lamaran per program_rekrutmen.
3. ~~Ambang nilai per komponen~~ — diputuskan: ambang pindah dari `tahap_program` ke
   `tahap_program_komponen` di PROGRAM, `komponen_nilai` pindah ke MASTER.
4. ~~Nilai adaptif RBB~~ — diputuskan: PLN hanya menerima daftar nama yang lolos, tanpa nilai.
   Tidak ada yang berubah di skema; kandidat RBB tetap tidak punya baris `pendaftaran_tahap`
   maupun `pendaftaran_nilai` untuk administrasi dan adaptif.
5. ~~Pilihan lokasi tes~~ — diputuskan: pelamar memilih **satu kota di awal**, lalu mengikuti
   semua tahap di kota itu. Venue pastinya ditentukan HTD & vendor, jadi `lokasi_tes` di
   PROGRAM ditambah `nama_lokasi` dan `alamat`.
6. ~~Detail MCU~~ — diterapkan: gula darah, kolesterol, status merokok, kondisi gigi.
   Ambang kelulusan tahap MCU **adalah kolom `kesimpulan`** — dikonfirmasi. MCU tidak punya
   baris `komponen_nilai` maupun ambang angka di `tahap_program_komponen`; vendor yang
   menyimpulkan, dan `pendaftaran_tahap.hasil` mengikuti kesimpulan itu.

---

## Daftar tabel section PENDAFTARAN (5 tabel)

| # | tabel | fungsi |
|---|---|---|
| 1 | `pendaftaran` | satu kandidat melamar satu bukaan profesi_rekrutmen |
| 2 | `alasan_gugur` | lookup sebab tidak lanjut |
| 3 | `pendaftaran_tahap` | kejadian per tahap yang benar-benar dijalani |
| 4 | `pendaftaran_nilai` | nilai per komponen |
| 5 | `pemeriksaan_kesehatan` | hasil ukur MCU oleh vendor |

`komponen_nilai` pindah ke MASTER (30 tabel), `tahap_program_komponen` masuk ke PROGRAM
(13 tabel).
