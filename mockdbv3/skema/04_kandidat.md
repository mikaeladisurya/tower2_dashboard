# Skema mockdbv3 — Section 4: KANDIDAT

Status: **draft, menunggu review user.** Belum ada data, belum ada DDL final.

Prinsip yang dipakai di seluruh skema ini:

1. Setiap tabel entitas punya **primary key surrogate** (`id`), bukan nama/teks bisnis.
2. **Tidak ada nilai agregat/turunan** yang disimpan (mis. usia, BMI, jenjang pendidikan
   tertinggi, lama pengalaman) — dihitung saat query.
3. **Tidak ada kolom "untuk generator/analis"**. Tabel berbentuk seperti database produksi.
4. Apa pun yang **berubah menurut waktu** disimpan sebagai baris ber-periode, bukan kolom
   "current" yang ditimpa terus.
5. Kosakata yang **dipakai untuk join/filter lintas tabel** diberi tabel lookup sendiri.
6. **Usulan dan keputusan adalah dua kejadian berbeda** → dua tabel berbeda.
7. Atribut milik induk tidak disalin ke anak.

---

## Batas section ini

Section KANDIDAT berisi **orangnya**, bukan lamarannya.

Yang masuk sini: identitas, alamat, data fisik, riwayat pendidikan, pengalaman kerja,
sertifikasi, ikatan dinas yang sedang dijalani. Semua melekat pada orang dan tetap benar
walau dia melamar nol kali atau lima kali.

Yang **tidak** masuk sini, ditunda ke PENDAFTARAN: lamaran, profesi_rekrutmen yang dipilih, kota tes,
nilai tiap tahap, lolos/gugur, dan hasil MCU yang sesungguhnya.

Konsekuensi terpenting: **satu orang yang melamar tiga tahun berturut-turut adalah satu baris
`kandidat`, bukan tiga.** v1 tidak bisa menjawab "berapa persen pelamar 2024 pernah melamar
sebelumnya" karena tiap gelombang membuat kandidat baru. Di sini pertanyaan itu jadi hitung
baris `pendaftaran` per `kandidat_id`.

Sumber daftar kolom: hasil crawl halaman akun rekrutmen.pln.co.id. Kolom-kolom itu dipecah
ke tabel-tabel di bawah menurut sifatnya, bukan disalin apa adanya jadi satu tabel lebar.

---

## A. Identitas

### `kandidat`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `nomor_identitas` | VARCHAR UNIQUE | no_ktp |
| `nama` | VARCHAR | nama_lengkap |
| `jenis_kelamin` | VARCHAR | L / P |
| `tanggal_lahir` | DATE | |
| `kota_kabupaten_lahir_id` | INTEGER FK → `kota_kabupaten.id`, NULL | tempat_lahir; NULL untuk lahir di luar negeri |
| `agama_id` | INTEGER FK → `agama.id` | |
| `status_perkawinan_id` | INTEGER FK → `status_perkawinan.id` | |
| `email` | VARCHAR UNIQUE | identitas akun pendaftaran |
| `nomor_telepon` | VARCHAR | no_handphone |

Contoh isi:

```
 id  nomor_identitas   nama              JK  tanggal_lahir  kota_lahir  agama    status_perkawinan
  1  3374xxxxxxxx0003  Rizky Ramadhan    L   2001-03-14     Semarang    Islam    Belum Menikah
  2  3273xxxxxxxx0021  Anisa Rahmawati   P   2000-11-02     Bandung     Islam    Belum Menikah
  3  1271xxxxxxxx0007  Josua Situmorang  L   1998-06-25     Medan       Kristen  Menikah
```

`tempat_lahir` di crawl berupa teks; di sini jadi FK ke `kota_kabupaten` supaya bisa
di-rollup ke provinsi tanpa mencocokkan ejaan.

`agama` dan `status_perkawinan` jadi lookup di MASTER, bukan teks bebas — dua ejaan berbeda
("Belum Menikah" / "Belum menikah") akan jadi dua kelompok terpisah di laporan yang sama.

Tidak ada kolom `usia`. Tanggal acuannya berbeda-beda (usia saat mendaftar, usia saat SK
penempatan); menyimpan satu angka berarti diam-diam memilih satu tanggal lalu salah untuk
semua pertanyaan lain. Syarat usia di `syarat_pelamar` dicek terhadap tanggal pendaftaran.

Tidak ada `jenjang_pendidikan_tertinggi` — turunan dari `kandidat_pendidikan`.

Tidak ada kolom status (`is_lolos`, `status_terakhir`). Orang tidak "lolos" sebagai orang;
dia lolos di satu lamaran tertentu. Itu milik PENDAFTARAN.

---

## B. Alamat

### `kandidat_alamat`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `kandidat_id` | INTEGER FK → `kandidat.id` | |
| `jenis_alamat` | VARCHAR | Domisili / Asal — hanya dua nilai ini |
| `alamat` | VARCHAR | alamat_domisili / alamat_asal |
| `kota_kabupaten_id` | INTEGER FK → `kota_kabupaten.id` | kota_domisili / kota_asal |
| `kode_pos` | VARCHAR, NULL | |

UNIQUE (`kandidat_id`, `jenis_alamat`)

`jenis` sengaja kolom teks, bukan FK ke tabel lookup — dikonfirmasi. Nilainya hanya pernah
dua dan tidak pernah di-join ke tabel lain, jadi lookup terpisah cuma menambah satu join di
tiap query tanpa mencegah apa pun. (Beda dengan `agama`, yang dipakai mengelompokkan laporan
dan nilainya banyak.) Kalau mau dijamin di tingkat basis data, cukup CHECK constraint.

Contoh isi:

```
 id  kandidat  jenis     alamat                    kota           kode_pos
  1     1      Domisili  Jl. Sultan Agung No. 12   Kota Semarang  50232
  2     1      Asal      Jl. Diponegoro No. 4      Kab. Kendal    51314
  3     2      Domisili  Jl. Cihampelas No. 88     Kota Bandung   40131
  4     2      Asal      Jl. Cihampelas No. 88     Kota Bandung   40131
```

Tujuh kolom di crawl (`alamat_domisili`, `kota_domisili`, `propinsi_domisili`,
`kode_pos_domisili`, `alamat_asal`, `kota_asal`, `propinsi_asal`) menyusut jadi satu tabel
dua baris per orang. Alasannya: domisili dan asal punya bentuk yang persis sama, jadi kalau
suatu saat muncul jenis ketiga (alamat surat-menyurat), tidak ada kolom baru yang perlu
ditambahkan.

`propinsi_domisili` dan `propinsi_asal` **tidak** disimpan — provinsi sudah melekat pada
`kota_kabupaten`. Menyalinnya ke sini melanggar prinsip 7 dan membuka peluang kota Bandung
tercatat di provinsi Jawa Tengah.

**Tabel ini menyimpan nilai "saat ini" di akun, dan itu memang perilaku yang benar** —
dikonfirmasi. Saat kandidat mau mendaftar, UI memintanya memperbarui data diri; hasil
pembaruan itu menimpa baris di sini **dan** disalin ke baris `pendaftaran` sebagai data
peserta.

Jadi dua tempat, dua pertanyaan berbeda:

| tabel | menjawab |
|---|---|
| `kandidat_alamat` | di mana orang ini sekarang |
| `pendaftaran` (section berikutnya) | dari mana dia melamar waktu itu |

Kolom kembar yang disengaja. Tanpa salinan di `pendaftaran`, orang yang pindah kota pada 2026
akan mengubah surut sebaran pelamar 2023, dan analisis sebaran per tahun tidak bisa dipercaya.

---

## C. Data fisik

### `kandidat_data_fisik`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `kandidat_id` | INTEGER FK → `kandidat.id` | |
| `tanggal_pencatatan` | DATE | kapan diisi/diperbarui di akun |
| `tinggi_badan` | INTEGER | cm — body_height |
| `berat_badan` | DECIMAL(5,2) | kg — body_weight |
| `lingkar_perut` | INTEGER, NULL | cm — abdominal_circumference |
| `visus_kiri` | DECIMAL(3,1), NULL | |
| `visus_kanan` | DECIMAL(3,1), NULL | |
| `tingkat_ketajaman` | VARCHAR, NULL | |
| `silinder` | DECIMAL(3,2), NULL | |
| `is_buta_warna` | BOOLEAN | |
| `is_bertato` | BOOLEAN | tatto |
| `ukuran_baju` | VARCHAR | S/M/L/XL |
| `ukuran_celana` | VARCHAR | |
| `ukuran_sepatu` | VARCHAR | |

UNIQUE (`kandidat_id`, `tanggal_pencatatan`)

Contoh isi:

```
 id  kandidat  tanggal     tinggi  berat  lingkar  visus_ki  visus_ka  is_buta_warna  tato   baju  sepatu
  1     1      2023-02-11   172    68.0     82       1.0       1.0      false      false  L     42
  2     1      2026-01-20   172    74.5     88       0.8       1.0      false      false  XL    42
  3     2      2026-01-18   159    52.0     70       1.0       1.0      false      false  S     38
```

**Tidak ada kolom `bmi`.** BMI seluruhnya turunan dari tinggi dan berat badan; menyimpannya
berarti menyimpan angka yang bisa bertentangan dengan dua kolom di sebelahnya. Kalau berat
badan diperbarui tanpa BMI ikut dihitung ulang, laporan kesehatan salah tanpa ada yang tahu.
Hitung saat query: `berat_badan / POWER(tinggi_badan/100.0, 2)`.

**Bertanggal, bukan satu baris ditimpa.** Ini satu-satunya kelompok kolom di crawl yang
benar-benar berubah antar lamaran — berat badan dan visus orang yang sama pada 2023 dan 2026
memang beda (lihat kandidat 1 di contoh). Kalau ditimpa, syarat kesehatan lamaran lama akan
dinilai dengan angka tahun ini.

**Ini data deklarasi mandiri di akun, bukan hasil MCU.** Hasil pemeriksaan kesehatan
sungguhan yang menentukan lolos/gugur di tahap `fisik_mcu` adalah kejadian di satu lamaran,
dan tempatnya di section PENDAFTARAN. Keduanya sengaja dipisah — selisih antara yang
dideklarasikan dan yang terukur adalah angka yang menarik tersendiri.

---

## D. Pendidikan

### `kandidat_pendidikan`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `kandidat_id` | INTEGER FK → `kandidat.id` | |
| `institusi_jurusan_id` | INTEGER FK → `institusi_jurusan.id` | institusi + prodi + jenjang sekaligus |
| `tahun_masuk` | INTEGER | |
| `tahun_lulus` | INTEGER, NULL | NULL = belum lulus |
| `ipk` | DECIMAL(3,2), NULL | untuk D3 ke atas |
| `nilai_rata_rata` | DECIMAL(4,2), NULL | untuk SMA/SMK |

UNIQUE (`kandidat_id`, `institusi_jurusan_id`)

Contoh isi:

```
 id  kandidat  institusi                   program_rekrutmen studi               jenjang  masuk  lulus  ipk   nilai
  1     1      SMK Negeri 7 Semarang       Teknik Instalasi Tenaga L.  SMK      2016   2019   —     86.40
  2     1      Universitas Diponegoro      Teknik Elektro              S1       2019   2023   3.41  —
  3     2      SMA Negeri 3 Bandung        IPA                         SMA      2015   2018   —     88.10
  4     2      Institut Teknologi Bandung  Teknik Elektro              S1       2018   2022   3.62  —
  5     2      Institut Teknologi Bandung  Teknik Tenaga Listrik       S2       2022   2024   3.80  —
```

Beberapa baris per orang, bukan satu baris dengan kolom berpasangan seperti v1
(`universitas` + `sma`), yang memaksa tiap query pendidikan menebak kolom mana yang relevan.

Satu FK, bukan tiga kolom lepas. Efeknya: kombinasi mustahil — "S2 Teknik Instalasi Tenaga
Listrik di SMK Negeri 1" — ditolak FK. v1 mengisi ketiganya sendiri-sendiri sehingga
kombinasi semacam itu bisa lolos.

`ipk` dan `nilai_rata_rata` dua kolom terpisah dan sengaja bukan satu kolom `nilai`, karena
skalanya beda (0-4 vs 0-100) dan ambangnya dicek terhadap kolom berbeda di `syarat_pelamar`
(`ipk_minimal` vs `nilai_minimal`).

---

## E. Riwayat di luar PLN

### `kandidat_pengalaman_kerja`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `kandidat_id` | INTEGER FK → `kandidat.id` | |
| `nama_perusahaan` | VARCHAR | teks bebas — perusahaan luar tidak ada di master |
| `nama_jabatan` | VARCHAR | teks bebas, bukan FK ke `jabatan` |
| `sub_bidang_id` | INTEGER FK → `sub_bidang.id`, NULL | pengalaman ini setara sub bidang PLN yang mana |
| `tanggal_mulai` | DATE | |
| `tanggal_selesai` | DATE, NULL | NULL = masih bekerja di sana |

Contoh isi:

```
 id  kandidat  nama_perusahaan        nama_jabatan            sub_bidang   mulai       selesai
  1     3      PT Trafoindo Prima P.  Engineer Distribusi     Distribusi   2019-08-01  2022-07-31
  2     3      PT Wijaya Karya        Site Engineer           Konstruksi   2022-09-01  NULL
  3     2      PT Len Industri        Asisten Riset (magang)  NULL         2021-06-01  2021-08-31
```

Total pengalaman kandidat 3 dihitung dari kedua tanggal, tidak disimpan: 36 bulan di baris 1
ditambah yang masih berjalan di baris 2. Perhatikan baris 3 — magang tiga bulan yang tidak
layak disebut pengalaman kerja. Batas apa yang dihitung ditentukan di query, bukan dengan
membuang barisnya.

`nama_perusahaan` dan `nama_jabatan` sengaja teks bebas. `jabatan` di MASTER adalah katalog
jabatan **PLN**; jabatan di perusahaan lain bukan anggota katalog itu, dan memaksanya masuk
akan mengotori master. Ini satu-satunya tempat di seluruh skema yang menerima teks bebas
dengan sadar.

`sub_bidang_id` boleh NULL dan itu lapisan judgment, bukan fakta. Tanpanya, teks bebas tadi
tidak bisa dipakai untuk apa pun selain dibaca satu per satu — pertanyaan "berapa pelamar Pro
Hire punya pengalaman di sub bidang Distribusi" tidak akan bisa dijawab. Pemetaannya harus
kamu review, tidak boleh ditebak generator; perlakuannya sama dengan
`pemetaan_jurusan_sub_bidang` dan `klasifikasi_jabatan`.

### `kandidat_sertifikasi`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `kandidat_id` | INTEGER FK → `kandidat.id` | |
| `nama_sertifikat` | VARCHAR | |
| `penerbit` | VARCHAR | |
| `tanggal_terbit` | DATE | |
| `tanggal_kedaluwarsa` | DATE, NULL | |

Contoh isi:

```
 id  kandidat  nama_sertifikat                      penerbit  terbit      kedaluwarsa
  1     3      Ahli K3 Umum                         Kemnaker  2021-05-10  2024-05-10
  2     3      Sertifikat Kompetensi Distribusi TM  LSK PLN   2020-11-02  2025-11-02
  3     1      TOEFL ITP (527)                      ETS       2022-09-15  2024-09-15
```

**Tidak dipakai untuk keputusan gugur/lolos** — dikonfirmasi. Tabel ini murni untuk dashboard
kapabilitas individu. Karena itu tidak ada kolom apa pun yang menghubungkannya ke tahap
seleksi, dan tidak boleh ada aturan generate yang membuat pemegang sertifikat lebih mungkin
lolos. Kalau relasi itu muncul di data, itu bug, bukan temuan.

---

## F. Ikatan dinas

### `kandidat_ikatan_dinas`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `kandidat_id` | INTEGER FK → `kandidat.id` | |
| `kelas_ikatan_dinas_id` | INTEGER FK → `kelas_ikatan_dinas.id` | |
| `tanggal_kontrak` | DATE | TTD kontrak ikatan dinas, masih calon mahasiswa/mahasiswa |
| `tanggal_selesai` | DATE, NULL | NULL = masih kuliah |
| `hasil_ikatan_dinas` | VARCHAR, NULL | Lulus / Mengundurkan Diri / Diberhentikan — NULL selama masih kuliah |

UNIQUE (`kandidat_id`, `kelas_ikatan_dinas_id`)

Contoh isi (kelas 12 kursi di Politeknik Negeri Bandung, mulai 2022):

```
 id  kandidat  kelas  tanggal_kontrak  tanggal_selesai  hasil
  1    401       7     2022-08-15       2026-07-20      Lulus
  2    402       7     2022-08-15       2026-07-20      Lulus
  3    403       7     2022-08-15       2024-03-02      Mengundurkan Diri
 ..    ...       7     2022-08-15       ...             ...
 12    412       7     2022-08-15       2026-07-20      Lulus
```

Inilah jembatan yang membuat orang ikatan dinas masuk pipeline yang sama dengan jalur lain.
Rantainya utuh dari ujung ke ujung:

```
proyeksi_kekosongan (siklus 2022, untuk 2026)
  → pagu_rekrutmen (tahun_program 2022, tahun_terisi 2026, jalur Ikatan Dinas)
  → kelas_ikatan_dinas_pagu
  → kelas_ikatan_dinas (Politeknik Negeri Bandung, D3 Teknik Listrik, mulai 2022, 12 kursi)
  → kandidat_ikatan_dinas (12 baris, satu per orang)
  → kandidat (12 orang, kandidat_pendidikan-nya tahun_lulus masih NULL sampai 2026)
  → [2026, lulus] → pasca-seleksi: samapta → pembidangan → OJT → ujian OJT → SK penempatan
```

`kuota` di `kelas_ikatan_dinas` (12) dan jumlah yang benar-benar lulus (11) sengaja dibiarkan
bisa berbeda. Selisihnya justru angka yang berguna: berapa persen investasi kuliah yang tidak
sampai jadi pegawai.

`hasil` ditulis sekali di akhir dan tidak ditimpa berulang, jadi bukan kolom "current" yang
dilarang prinsip 4. Kalau nanti status perlu dilacak per semester (cuti, mengulang), itu harus
jadi tabel kejadian tersendiri — belum ada tanda kita membutuhkannya.

---

## Flow section KANDIDAT

Tiga cara orang masuk ke tabel `kandidat`, dan ketiganya berakhir di titik yang sama.

**1. Jalur Mandiri — baris kandidat lahir saat orangnya buat akun sendiri**

```
buka rekrutmen.pln.co.id → daftar akun (email, no_ktp)
  → kandidat                      1 baris
  → kandidat_alamat               2 baris (Domisili, Asal)
  → kandidat_data_fisik           1 baris, tanggal_pencatatan = hari itu
  → kandidat_pendidikan           1-3 baris (SMK/SMA, S1, mungkin S2)
  → kandidat_pengalaman_kerja     0-n baris
  → kandidat_sertifikasi          0-n baris
  → [section PENDAFTARAN] pilih program_rekrutmen & profesi_rekrutmen
```

Melamar lagi tahun berikutnya **tidak** membuat baris `kandidat` baru. Yang bertambah: satu
baris `pendaftaran`, dan biasanya satu baris `kandidat_data_fisik` baru karena data fisik
diminta diperbarui.

**2. Jalur RBB — baris kandidat lahir saat limpahan dari sistem BUMN**

Ini berbeda dari Mandiri dan penting untuk tidak disamakan. Dari sisi pendaftar:

```
lihat iklan bukaan RBB (bisa di akun PLN, Pertamina, Mandiri, BUMN mana pun)
  → daftar di SISTEM BUMN, bukan di sistem PLN
  → tes administrasi & adaptif di sistem BUMN
  → yang lolos diteruskan ke perusahaan tujuan
  → mulai dari sini sistem rekrutmen PLN yang melanjutkan:
    akademik & inggris → psikologi → MCU → dst
```

Dari sisi PLN, kontribusinya hanya dua hal di ujung awal: menyediakan kuota — posisi apa saja
yang dibuka dan butuh berapa — lalu **menunggu** daftar orang yang lolos tahap BUMN.

Akibatnya untuk skema ini:

- Baris `kandidat` jalur RBB **tidak lahir dari orang membuat akun di PLN**, tapi dari
  limpahan data saat sistem BUMN menyampaikan siapa saja yang lolos. Tanggal lahir barisnya
  bukan tanggal orang itu mendaftar, melainkan tanggal serah terima.
- Profilnya bisa **lebih tipis** dari pelamar Mandiri: apa yang ada tergantung apa yang
  dikirim sistem BUMN. `kandidat_data_fisik` dan `kandidat_sertifikasi` wajar kosong sampai
  PLN memintanya sendiri. Itu bukan data bolong, itu memang tidak pernah ada.
- Menguatkan catatan yang sudah ada: kandidat RBB tidak punya baris tahap administrasi dan
  adaptif, karena kedua tahap itu berjalan di sistem BUMN dan tidak di-track PLN.
- `pendaftaran` **wajib punya kolom nomor peserta sistem BUMN** — dikonfirmasi. Itu satu-
  satunya cara merujuk orang ini balik ke sumbernya, dan satu-satunya bukti bahwa tahap
  administrasi & adaptif memang terjadi walau tidak dicatat PLN. Kolomnya NULL untuk jalur
  selain RBB.

Kuota yang PLN sediakan tidak ada di section ini — itu `bukaan_profesi` di PROGRAM, yang
menempel ke `pagu_rekrutmen` lewat `bukaan_profesi_pagu`. Jalurnya sudah ada, tidak perlu
tabel baru.

**3. Pro Hire — pintu masuknya sama dengan Mandiri, bedanya di isi tabel**

Sama persis dengan cara 1, tapi `kandidat_pengalaman_kerja` terisi dan **dicek di tahap
administrasi** — dikonfirmasi. Jadi `syarat_pelamar.pengalaman_minimal_bulan` bukan sekadar
catatan, ia penentu gugur/lolos di tahap pertama, sederajat dengan syarat usia dan IPK.

Umur kandidatnya lebih tua, `ipk` sering kosong karena lulusnya sudah lama, dan grade masuknya
ditentukan pengalaman — bukan ijazah. Lihat bagian "Efek keputusan" di bawah.

**4. Ikatan dinas — baris kandidat lahir 3-4 tahun sebelum melamar**

```
[2022] lolos seleksi kelas ikatan dinas (seleksinya TIDAK dilacak di mock ini)
  → kandidat                      1 baris
  → kandidat_pendidikan           1 baris, tahun_lulus = NULL (masih kuliah)
  → kandidat_ikatan_dinas         1 baris, hasil = NULL
  → [2022-2026] kuliah dibiayai PLN
  → [2026] lulus
        kandidat_pendidikan.tahun_lulus  ← 2026
        kandidat_ikatan_dinas.hasil      ← Lulus
  → langsung ke pasca-seleksi, tanpa pernah punya baris tahap seleksi
```

Titik temunya: sejak samapta, keempatnya jadi satu populasi yang sama dan diperlakukan
identik sampai SK penempatan.

---

## Yang sengaja tidak dibuat

**Kolom `bmi`.** Turunan penuh dari tinggi dan berat. Lihat bagian C.

**Kolom disabilitas.** Dikonfirmasi tidak ada jalur/kuota disabilitas untuk mock ini. Tidak
dibuat sama sekali, bukan dibuat lalu dibiarkan kosong — kolom yang selalu NULL cuma bikin
orang bertanya apa maksudnya.

**Kolom `pernah_pegawai_pln` / `is_eks_ojt`.** Tidak butuh kolom apa pun di sini. Di section
PENEMPATAN, tabel `pegawai` akan punya `kandidat_id` FK; "pernah jadi pegawai" jadi pertanyaan
"ada baris `pegawai` untuk `kandidat_id` ini". Menambah boolean di sini berarti menyimpan
turunan yang bisa bertentangan dengan tabel `pegawai` — melanggar prinsip 2. Aturan logikanya
di bagian berikutnya.

**Tabel dokumen/lampiran** (ijazah, KTP, pas foto). Tidak ada berkas sungguhan di mock ini.

**Tabel akun/login, kata sandi, riwayat masuk.** Bagian dari sistem portal, bukan proses
rekrutmen.

---

## Pegawai PLN yang melamar lagi

Kasus khusus, dikonfirmasi ada tapi **tidak lebih dari 50 kasus dalam 10 tahun**. Bentuknya:
pegawai yang masuk lewat jenjang SMA lalu melamar bukaan S1/S2/Pro Hire, atau yang masuk
lewat S1 lalu melamar S2/Pro Hire.

Secara skema tidak ada yang baru: satu `kandidat`, beberapa `pendaftaran`, dan sebuah baris
`pegawai` yang menunjuk balik ke `kandidat_id`. Yang mahal di sini bukan strukturnya, tapi
**logikanya** — dan ini yang harus dicek ricek saat populasi, karena baris yang tidak masuk
akal di sini jauh lebih merusak daripada baris yang tidak ada.

Aturan yang harus dipatuhi generator, dari alasan yang kamu sebutkan:

| aturan | alasan |
|---|---|
| jenjang lamaran baru harus **lebih tinggi** dari jenjang saat dia masuk PLN | tidak ada pegawai S1 melamar bukaan SMA |
| ijazah baru harus **lulus setelah** dia jadi pegawai | kalau ijazah S1-nya terbit sebelum masuk, dia akan melamar S1 sejak awal |
| jarak masuk-PLN ke lamaran baru harus **wajar** — cukup lama untuk kuliah lagi, tidak sampai belasan tahun | masuk SMA lalu 20 tahun kemudian melamar S1 mustahil: usianya sudah lewat `syarat_pelamar.usia_maksimal` |
| grade dia saat itu harus **belum melewati** grade masuk jenjang yang dilamar | pegawai SMA yang sudah naik ke G2 tidak akan melamar bukaan S1 yang juga masuk di G2 — tidak ada yang didapat |
| usia saat melamar tetap dicek ke `syarat_pelamar` | tidak ada pengecualian untuk pegawai |

Aturan keempat yang paling gampang terlewat dan paling menentukan. Ia yang membuat jendela
kasus ini sempit dengan sendirinya: hanya pegawai yang masih di grade awal dan baru saja
menyelesaikan kuliah lanjutan yang punya alasan melamar lagi. Kalau generator memakai kelima
aturan ini, angka 50-an kasus per 10 tahun akan muncul sendiri tanpa perlu dipatok.

Konsekuensi kecil yang mudah luput: orang ini punya **dua** baris `kandidat_pendidikan`
dengan tahun lulus berjauhan, dan pendidikan keduanya diselesaikan sambil bekerja di PLN.
Di analisis "asal kampus pelamar" dia akan muncul di dua kampus — itu benar, bukan duplikat.

---

## Efek keputusan "pengalaman kerja dimodelkan sungguhan"

Tabel yang terkena, di luar `kandidat_pengalaman_kerja` sendiri:

| tabel | section | perubahan |
|---|---|---|
| `syarat_pelamar` | PERENCANAAN | **sudah ditambah** kolom `pengalaman_minimal_bulan` (NULL untuk jalur fresh graduate) |
| `sub_bidang` | MASTER | bentuknya tidak berubah, tapi kini juga jadi kosakata pengalaman kerja — bukan cuma jabatan dan program_rekrutmen studi |
| `aturan_grade_masuk` | PERENCANAAN | **belum diputuskan** — lihat di bawah |

**Sudah diterapkan (pilihan A).** `aturan_grade_masuk` kini punya `jalur_rekrutmen_id` dan
`pengalaman_minimal_bulan`. Dasarnya: Pro Hire merekrut untuk grade tinggi dan orangnya
disiapkan menjabat dalam sekitar satu tahun, jadi grade masuknya di kisaran S2 ke atas apa
pun ijazahnya. Tanpa kolom jalur, baris "S1 → G2" akan diterapkan ke pelamar Pro Hire
berpengalaman 10 tahun dan menghasilkan grade yang salah.

`pengalaman_minimal_bulan` di tabel itu memungkinkan beberapa tingkat dalam satu jalur —
Pro Hire 5 tahun dan Pro Hire 12 tahun tidak masuk di grade yang sama. Angka pastinya belum
dikonfirmasi, ditentukan saat putaran populasi.

Pengalaman kerja **dicek di tahap administrasi** — dikonfirmasi. Artinya
`syarat_pelamar.pengalaman_minimal_bulan` penentu gugur/lolos di tahap pertama, sederajat
dengan syarat usia dan IPK, bukan sekadar catatan.

Satu peringatan untuk putaran populasi: pengalaman kerja memang sangat bervariasi, dan itu
bukan alasan mengisinya acak. Yang harus tetap masuk akal — `tanggal_mulai` tidak boleh
mendahului `tahun_lulus` pendidikan tertingginya, rentang antar pekerjaan tidak boleh tumpang
tindih terlalu lama, dan total pengalaman harus konsisten dengan usia. Tiga aturan itu yang
membedakan data bervariasi dari data sampah.

---

## Yang perlu diputuskan

1. **Nama tabel dan kolom** — semua di atas usulan saya.
2. ~~Grade masuk Pro Hire~~ — diputuskan: `aturan_grade_masuk` ditambah `jalur_rekrutmen_id`
   dan `pengalaman_minimal_bulan`. Sudah diterapkan di PERENCANAAN.
3. ~~Salinan kota domisili ke `pendaftaran`~~ — diputuskan: ya. `kandidat_alamat` menyimpan
   nilai terkini (diperbarui lewat profil akun), `pendaftaran` menyalinnya saat melamar.
4. ~~Bentuk `silinder`~~ — diputuskan: satu nilai saja cukup untuk mockdbv3.
5. ~~Nomor peserta sistem BUMN~~ — diputuskan: ya, jadi kolom di `pendaftaran`, NULL untuk
   jalur selain RBB.
6. **Kelengkapan profil kandidat RBB** — seberapa tipis data yang dilimpahkan sistem BUMN?
   Menentukan tabel mana yang wajar kosong saat populasi.

---

## Daftar tabel section KANDIDAT (7 tabel)

| # | tabel | fungsi |
|---|---|---|
| 1 | `kandidat` | identitas orang, satu baris seumur hidup |
| 2 | `kandidat_alamat` | alamat domisili & asal, nilai terkini |
| 3 | `kandidat_data_fisik` | ukuran badan, penglihatan, ukuran seragam — bertanggal |
| 4 | `kandidat_pendidikan` | riwayat pendidikan, satu baris per jenjang |
| 5 | `kandidat_pengalaman_kerja` | riwayat kerja di luar PLN |
| 6 | `kandidat_sertifikasi` | sertifikat yang dimiliki — bukan penentu lolos/gugur |
| 7 | `kandidat_ikatan_dinas` | orang yang terikat kelas ikatan dinas |
