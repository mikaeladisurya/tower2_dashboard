# Skema mockdbv3 — Section 1: MASTER

Status: **draft, menunggu review user.** Belum ada data, belum ada DDL final.

Prinsip yang dipakai di seluruh skema ini:

1. Setiap tabel entitas punya **primary key surrogate** (`id`), bukan nama/teks bisnis.
2. **Tidak ada nilai agregat/turunan** yang disimpan di tabel master (mis. jumlah pegawai
   di tabel unit) — angka semacam itu dihitung dari tabel fakta/snapshot.
3. **Tidak ada kolom "untuk generator/analis"** (mis. penanda sintetis, penanda keputusan
   analisis). Tabel berbentuk seperti database produksi. Catatan asumsi/provenance ditulis
   di dokumen ini, bukan sebagai kolom data.
4. Apa pun yang **berubah menurut waktu** disimpan sebagai snapshot ber-`periode`, bukan
   kolom "current" yang ditimpa terus.
5. Kosakata yang **dipakai untuk join/filter lintas tabel** diberi tabel lookup sendiri,
   supaya tidak jadi teks bebas yang tidak terjamin cocok antar tabel.

---

## A. Lookup wilayah

### `provinsi`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `nama` | VARCHAR | nama provinsi |

### `kota_kabupaten`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `provinsi_id` | INTEGER FK → `provinsi.id` | |
| `nama` | VARCHAR | nama kota/kabupaten |

Tidak ada kolom `is_3t` di sini. Status daerah tertinggal ditetapkan pemerintah per periode
dan bisa berubah, jadi berupa dua tabel bertanggal di bawah — bukan sifat tetap sebuah kota.

### `peraturan_3t`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `nomor_peraturan` | VARCHAR | mis. Perpres 63/2020 |
| `tahun_terbit` | INTEGER | |
| `berlaku_mulai` | DATE | |
| `berlaku_sampai` | DATE, NULL | NULL = masih berlaku |

### `daerah_3t`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `peraturan_3t_id` | INTEGER FK → `peraturan_3t.id` | |
| `kota_kabupaten_id` | INTEGER FK → `kota_kabupaten.id` | |

UNIQUE (`peraturan_3t_id`, `kota_kabupaten_id`)

Satu kota bisa berstatus 3T di satu periode lalu lepas di periode berikutnya, dan riwayatnya
tetap utuh. Pertanyaan "apakah unit ini 3T saat pagu 2024 ditetapkan" jadi join dengan filter
tanggal. v1 menyimpannya sebagai teks `keterangan` di tiap baris pagu ("3T" / "Rekrut 2019"),
sehingga status wilayah dan tahun program_rekrutmen bercampur di satu kolom dan tidak punya riwayat.

---

## B. Lookup bidang & jabatan

### `bidang`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `nama` | VARCHAR | tingkat teratas, mis. TEKNIK / NON-TEKNIK |

### `sub_bidang`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `bidang_id` | INTEGER FK → `bidang.id` | |
| `nama` | VARCHAR | mis. Distribusi, Transmisi, Pembangkitan, Niaga, Keuangan |

### `fungsi`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `nama` | VARCHAR | mis. Enjiniring, Pemeliharaan, Operasi, Perencanaan |

Membedakan "Enjiniring Distribusi" dari "Pemeliharaan Distribusi" — sub bidang sama, fungsi beda.

### `grade`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `kode` | VARCHAR | G1, G2, G3, MAK, MM, MA, MD, JE, SSP, SPC |
| `nama` | VARCHAR | sebutan panjangnya |
| `urutan` | INTEGER | urutan senioritas, supaya bisa diurutkan tanpa mengandalkan urutan abjad kode |

### `kelompok_jabatan`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `nama` | VARCHAR | mis. Officer, Junior Officer, Team Leader, Assistant Manager, Manager, VP |
| `is_struktural` | BOOLEAN | penanda jabatan struktural |

`is_struktural` ada di sini (bukan di `jabatan`) karena sifat struktural melekat pada kelompok
jabatannya, bukan pada tiap judul jabatan satu per satu.

### `jenjang_pendidikan`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `kode` | VARCHAR | SMA, SMK, D3, D4, S1, S2 |
| `nama` | VARCHAR | |
| `urutan` | INTEGER | urutan jenjang |

Dipisahkan dari `grade` walau sama-sama "jenjang" — yang satu jenjang pendidikan kandidat,
yang satu jenjang jabatan di perusahaan.

### `agama`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `nama` | VARCHAR | Islam, Kristen, Katolik, Hindu, Buddha, Konghucu |

### `status_perkawinan`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `nama` | VARCHAR | Belum Menikah, Menikah, Cerai Hidup, Cerai Mati |

Dua lookup ini ada karena formulir akun pendaftar rekrutmen.pln.co.id memintanya, dan
keduanya dipakai untuk memfilter/mengelompokkan pelamar. Sebagai teks bebas, "Belum Menikah"
dan "Belum menikah" akan jadi dua kelompok berbeda dalam laporan yang sama.

---

## C. Struktur organisasi

Perusahaan dan unit dipisah jadi dua tabel. Perusahaan (Holding / SubHolding / Anak
Perusahaan) adalah badan hukum tersendiri, bukan "unit yang tingkatnya paling atas".

Unit disimpan dalam **satu** tabel untuk semua lapis, bukan `unit_induk` / `unit_pelaksana`
terpisah. Hubungan atasan-bawahan jadi rujukan ke tabel itu sendiri (`unit_atasan_id`).

Alasan:
- Tabel lain cukup menyimpan **satu** `unit_id`, bukan pasangan `unit_induk_id` +
  `unit_pelaksana_id` yang harus selalu konsisten. Sepasang kolom yang bisa saling
  bertentangan adalah sumber bug yang tidak perlu ada.
- Lapis baru (Sub Bidang, ULP) tidak mengubah struktur tabel.
- Status Holding/SubHolding/AP tidak diulang di tiap baris unit — cukup di perusahaannya.

Harga yang dibayar, disadari sejak awal:
- FK tidak bisa memaksa "kolom ini harus unit level 2". Penjagaannya lewat CHECK constraint
  atau kode, bukan lewat relasi.
- Rekap ke atas ("semua unit di bawah UID Jawa Timur") perlu `WITH RECURSIVE`.
- Perlu dijaga agar tidak terbentuk lingkaran induk (A induk B, B induk A).

### `perusahaan`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `nama` | VARCHAR | |
| `kategori_perusahaan` | VARCHAR | Holding, SubHolding, Anak Perusahaan |
| `kota_kabupaten_id` | INTEGER FK → `kota_kabupaten.id` | lokasi kantor pusatnya |

SubHolding dan Anak Perusahaan sengaja dangkal: punya baris di sini, tidak punya baris di
`unit` sama sekali. Penempatan ke sana menunjuk perusahaan saja — lihat catatan di
`00_catatan_lapangan.md`.

### `jenis_unit`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `nama` | VARCHAR | Divisi, Bidang, Unit Induk, Unit Pelaksana |
| `level_unit` | INTEGER | 1 untuk Divisi & Unit Induk, 2 untuk Bidang & Unit Pelaksana |

`level` ada di sini, bukan di tiap baris `unit`, karena level selalu ditentukan oleh
jenisnya: semua Divisi level 1, semua Bidang level 2. Kalau disalin ke tiap unit, suatu
saat ada unit ber-jenis Bidang tapi level 1 dan tidak ada yang menahan.

Justru `level` inilah yang menyatakan **Divisi setara Unit Induk** dan **Bidang setara Unit
Pelaksana**. Aturan "pagu diputuskan sampai unit pelaksana" ditulis sebagai `level = 2`, dan
otomatis mencakup Bidang di Kantor Pusat tanpa cabang khusus.

Arti tiap level:
- **level 1** — lapis manajemen. Tidak ada penempatan pegawai langsung ke sini.
- **level 2** — tempat pegawai benar-benar duduk, dan tempat pagu mendarat.

Granulasi berhenti di level 2. Sub Bidang di bawah Bidang, dan ULP di bawah UP3, memang ada
di dunia nyata tapi tidak dimodelkan untuk mockdb ini.

### `lini_bisnis`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `nama` | VARCHAR | Kantor Pusat, Distribusi, Transmisi, Pembangkitan, Penyaluran, Diklat, Sertifikasi, … |

Sumbu yang berbeda dari `jenis_unit`: jenis menjawab "di lapis mana", lini bisnis menjawab
"mengurus apa". UPDL dan UP3 sama-sama jenis Unit Pelaksana tapi beda lini bisnis; Bidang di
Kantor Pusat dan Bidang di UID sama-sama jenis Bidang tapi beda lini bisnis — dan justru
beda itu yang menentukan perlakuan penempatan (peserta OJT di lini Kantor Pusat biasanya
tetap di situ saat SK terbit).

Daftar lengkapnya ditetapkan saat pengisian data. Termasuk pusat-pusat setara unit induk:
Pusdiklat, Pusertif, Pusharlis, Pusmanpro.

### `unit`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `perusahaan_id` | INTEGER FK → `perusahaan.id` | |
| `unit_atasan_id` | INTEGER FK → `unit.id`, NULL | NULL = unit teratas di perusahaannya (level 1) |
| `kode` | VARCHAR | kode unit di sistem internal |
| `nama` | VARCHAR | nama resmi lengkap |
| `nama_singkat` | VARCHAR | |
| `jenis_unit_id` | INTEGER FK → `jenis_unit.id` | |
| `lini_bisnis_id` | INTEGER FK → `lini_bisnis.id` | |
| `kota_kabupaten_id` | INTEGER FK → `kota_kabupaten.id` | lokasi kantor unit |
| `tanggal_dibentuk` | DATE | |
| `tanggal_dibubarkan` | DATE, NULL | NULL = masih aktif |

Tidak ada kolom `is_aktif`: status aktif dihitung dari `tanggal_dibubarkan`, dan menyimpan
keduanya membuka peluang keduanya bertentangan.

Contoh isi:

```
perusahaan
  1  PT PLN (Persero)      Holding
  9  PLN Nusantara Power   SubHolding
 14  PLN Icon Plus         Anak Perusahaan

unit
 id  persh  atasan  nama                                   lvl  jenis           lini_bisnis
  2    1    NULL    DIV Manajemen Digital                    1   Divisi          Kantor Pusat
  4    1    NULL    DIV Manajemen Rantai Pasok               1   Divisi          Kantor Pusat
 32    1     2      Bidang Digitalisasi Kelistrikan          2   Bidang          Kantor Pusat
 45    1    NULL    PLN Pusdiklat                            1   Unit Induk      Diklat
 46    1    45      PLN UPDL Semarang                        2   Unit Pelaksana  Diklat
 51    1    NULL    PLN Unit Induk Distribusi Jawa Timur     1   Unit Induk      Distribusi
 52    1    51      Bidang Perencanaan                       2   Bidang          Distribusi
 53    1    51      Bidang Distribusi                        2   Bidang          Distribusi
 54    1    51      Bidang Niaga dan Pelayanan Pelanggan     2   Bidang          Distribusi
 55    1    51      Bidang Keuangan, SDM dan Umum            2   Bidang          Distribusi
 75    1    51      PLN UP3 Surabaya Selatan                 2   Unit Pelaksana  Distribusi
 98    1    62      PLN UPT Semarang                         2   Unit Pelaksana  Transmisi
```

Kantor unit induk tidak jadi satu baris utuh, melainkan dipecah jadi bidang-bidangnya
(baris 52-55). Ini pilihan sadar dan ada ongkosnya: lembar FTK resmi
(`Sample-02-Contoh Format Pagu FTK 2026.xlsx`) menaruh KANTOR INDUK sebagai **satu** baris
dengan satu angka FTK (150), tidak dipecah per bidang. Jadi saat pengisian data nanti,
pembagian 150 itu ke tiap bidang adalah angka yang **kita tetapkan**, bukan yang kita salin
dari sumber. Daftar bidangnya sendiri nyata (struktur organisasi UID memang begitu).

Alasan memilih ongkos itu: kalau kantor induk tetap satu baris, level 2 punya dua arti
berbeda — "satu bidang" di Kantor Pusat tapi "seluruh kantor induk" di UID. Grain yang tidak
seragam membuat perbandingan rencana-vs-penempatan membandingkan hal yang tidak setara.

---

## D. Katalog jabatan

### `jabatan`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `nama_jabatan` | VARCHAR | judul jabatan apa adanya |
| `grade_id` | INTEGER FK → `grade.id` | |
| `kelompok_jabatan_id` | INTEGER FK → `kelompok_jabatan.id` | |

### `klasifikasi_jabatan`
| kolom | tipe | keterangan |
|---|---|---|
| `jabatan_id` | INTEGER PK, FK → `jabatan.id` | satu klasifikasi per jabatan |
| `sub_bidang_id` | INTEGER FK → `sub_bidang.id` | |
| `fungsi_id` | INTEGER FK → `fungsi.id` | |

Dipisah dari `jabatan` karena isinya lapisan penilaian (hasil pengelompokan), bukan atribut
mentah jabatan dari sumber.

---

### `posisi`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `unit_id` | INTEGER FK → `unit.id` | |
| `jabatan_id` | INTEGER FK → `jabatan.id` | |

UNIQUE (`unit_id`, `jabatan_id`)

Satu kursi: jabatan tertentu **di unit tertentu**. "Junior Technician Jaringan Distribusi
di UP3 Surabaya Selatan".

Ada tabelnya sendiri karena pasangan `unit_id` + `jabatan_id` tadinya diulang di lima
tabel (`jumlah_pegawai_bulanan`, `formasi_tenaga_kerja`, `proyeksi_kekosongan`,
`usulan_kebutuhan`, `pagu_rekrutmen`) tanpa ada yang menjamin kombinasinya masuk akal —
tidak ada yang menahan kalau muncul "General Manager" di sebuah UP3, atau "Junior
Technician Transmisi" di Bidang Keuangan. Dengan `posisi_id`, kombinasi yang tidak terdaftar
langsung ditolak FK.

Alasannya sama seperti unit digabung jadi satu tabel: sepasang kolom yang harus selalu
konsisten sebaiknya jadi satu rujukan. v1 sebenarnya sudah punya ini
(`posisi_unit_induk.csv`, `posisi_unit_pelaksana.csv`), tapi dipecah dua dan tidak dipakai
sebagai FK ke mana-mana.

Ongkosnya: satu join tambahan tiap kali butuh nama unit atau nama jabatan.

### `profesi_rekrutmen`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `kode` | VARCHAR | |
| `nama` | VARCHAR | mis. Junior Technician Distribusi |
| `sub_bidang_id` | INTEGER FK → `sub_bidang.id` | |
| `jenjang_pendidikan_id` | INTEGER FK → `jenjang_pendidikan.id` | |

Nama profesi_rekrutmen yang dipakai di pengumuman rekrutmen. Dipakai berulang tiap tahun dengan sub
bidang dan jenjang yang sama, jadi ini master — sementara **bukaannya** (program_rekrutmen mana,
kuota berapa) transaksi, ada di section PROGRAM sebagai `bukaan_profesi`.

Pemisahan ini mengikuti pola yang sama dengan `tahap_referensi` (MASTER) vs `tahap_program`
(PROGRAM). Kalau tidak dipisah, nama profesi_rekrutmen ditulis ulang sebagai teks tiap tahun, dan
satu spasi ekstra di tahun 2026 memecah tren lima tahun jadi dua garis — persis penyakit
`minat_profesi` di v1.

Perbedaan tiga istilah yang mudah tertukar:

| istilah | artinya |
|---|---|
| `jabatan` | judul jabatan di struktur organisasi |
| `posisi` | jabatan itu di unit tertentu — satu kursi |
| `profesi_rekrutmen` | nama publik di pengumuman, menggabungkan banyak jabatan yang sub bidang + jenjangnya sama |

---

## E. Snapshot jumlah pegawai

Grain: satu baris per (unit × jabatan × periode). Periode bulanan, tanggal akhir bulan.
Berisi **realisasi** (jumlah pegawai yang benar-benar ada), bukan target/formasi —
target/FTK masuk section Perencanaan.

### `jumlah_pegawai_bulanan`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `posisi_id` | INTEGER FK → `posisi.id` | unit × jabatan |
| `periode` | DATE | akhir bulan |
| `jumlah_pegawai` | INTEGER | |

UNIQUE (`posisi_id`, `periode`)

Satu tabel, bukan dua seperti rancangan sebelumnya — begitu unit jadi satu tabel, pemisahan
snapshot per tingkat kehilangan alasannya. Snapshot diisi di tingkat unit terbawah tempat
pegawai benar-benar duduk; angka tingkat induk didapat lewat rekap rekursif, bukan disimpan
ulang (kalau disimpan ulang, dua angka bisa berbeda dan tidak ada yang tahu mana yang benar).

---

## F. Pendidikan

### `jurusan`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `nama` | VARCHAR | mis. Teknik Elektro, Akuntansi, Teknik Instalasi Tenaga Listrik |

**`jurusan` = program studi.** Dua kata untuk hal yang persis sama. Dipilih "jurusan" karena
itu kata yang dipakai tim HTD di berkas kerja mereka ("JURUSAN PENDIDIKAN" di Sample-01 dan
Sample-04), sedangkan "program studi" istilah resmi kampus. Catatan ini perlu ada supaya
siapa pun yang membaca skema — termasuk chatbot yang diberi deskripsi ini — tahu keduanya
merujuk hal yang sama, dan pertanyaan yang memakai kata "program studi" tetap terjawab.

Jenjang tidak di sini — satu nama program_rekrutmen studi bisa dibuka di jenjang berbeda oleh
institusi berbeda, jadi jenjang ada di tabel penghubung. Jurusan SMK (mis. Teknik
Instalasi Tenaga Listrik, Teknik Distribusi Tenaga Listrik) juga baris di tabel ini,
bukan tabel terpisah — perlakuannya sama persis dengan jurusan kuliah: dipetakan ke
sub bidang lewat `pemetaan_jurusan_sub_bidang`.

### `institusi_pendidikan`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `nama` | VARCHAR | |
| `jenis_institusi` | VARCHAR | SMA, SMK, Politeknik, Sekolah Tinggi, Institut, Universitas |
| `kota_kabupaten_id` | INTEGER FK → `kota_kabupaten.id`, NULL | NULL untuk institusi luar negeri |
| `negara` | VARCHAR | mendukung kandidat lulusan luar negeri (jalur diaspora) |

Satu tabel untuk semua tingkat, bukan `universitas` dan `sekolah` terpisah. Alasannya:
biodata kandidat cukup menunjuk satu kolom FK apa pun jenjang lulusannya. Kalau dipisah,
biodata butuh dua kolom FK yang saling-nullable dan tiap query pendidikan harus UNION.

SD dan SMP tidak dimasukkan: bukan syarat masuk mana pun (jenjang terendah yang direkrut
SMK/SMA), tidak pernah di-join, tidak pernah difilter.

### `institusi_jurusan`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `institusi_pendidikan_id` | INTEGER FK → `institusi_pendidikan.id` | |
| `jurusan_id` | INTEGER FK → `jurusan.id` | |
| `jenjang_pendidikan_id` | INTEGER FK → `jenjang_pendidikan.id` | |

UNIQUE (`institusi_pendidikan_id`, `jurusan_id`, `jenjang_pendidikan_id`)

Gunanya: saat membuat biodata kandidat, kombinasi institusi + program_rekrutmen studi + jenjang
harus yang benar-benar ada, bukan asal pasang. Baris SMK masuk lewat jalur yang sama —
institusi berjenis SMK + program_rekrutmen studi jurusan SMK + jenjang SMK.

### `pemetaan_jurusan_sub_bidang`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `jurusan_id` | INTEGER FK → `jurusan.id` | |
| `sub_bidang_id` | INTEGER FK → `sub_bidang.id` | |

UNIQUE (`jurusan_id`, `sub_bidang_id`)

Satu program_rekrutmen studi boleh memasok lebih dari satu sub bidang. Memakai `sub_bidang_id` yang
sama dengan `klasifikasi_jabatan`, jadi pasokan (lulusan) dan permintaan (kursi jabatan)
memakai kosakata yang identik dan dijamin FK.

---

## G. Vendor

### `vendor`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `nama` | VARCHAR | |
| `jenis_layanan` | VARCHAR | mis. medical check up, psikotes |
| `kota_kabupaten_id` | INTEGER FK → `kota_kabupaten.id` | kota basis |

---

## H. Jalur & tahapan rekrutmen

### `venue`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `nama` | VARCHAR | |
| `jenis_venue` | VARCHAR | Kampus / Kantor PLN / Klinik / Rumah Sakit / Hotel / Gedung Serbaguna |
| `kota_kabupaten_id` | INTEGER FK → `kota_kabupaten.id` | |
| `alamat` | VARCHAR, NULL | |

Contoh isi:

```
 id  nama                          jenis          kota
  1  Universitas Diponegoro        Kampus         Kota Semarang
  2  Telkom University             Kampus         Kota Bandung
  3  Kantor PLN UID Jawa Barat     Kantor PLN     Kota Bandung
  4  Klinik Kimia Farma Bandung    Klinik         Kota Bandung
  5  RS Pelni                      Rumah Sakit    Kota Jakarta Barat
```

Venue jadi tabel tersendiri, bukan teks di `lokasi_tes`, karena venue yang sama dipakai
berulang lintas tahap dan lintas tahun. Sebagai teks bebas, "Telkom University" dan "Telkom
Univ." akan jadi dua tempat berbeda dan pertanyaan "venue mana yang paling sering dipakai"
tidak bisa dijawab.

`jenis` menentukan venue itu cocok untuk tahap apa, dan itu yang membuat populasinya bisa
masuk akal: tes tulis di kampus atau gedung serbaguna, MCU di klinik atau rumah sakit,
wawancara di kantor PLN. Tanpa `jenis_venue`, generator akan menaruh MCU di kampus.

### `jalur_rekrutmen`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `kode` | VARCHAR | mis. MANDIRI, RBB |
| `nama` | VARCHAR | |

### `tahap_referensi`
| kolom | tipe | keterangan |
|---|---|---|
| `kode` | VARCHAR PK | mis. ADM, TKD, AKHLAK, AKADEMIK, PSIKOLOGI, MCU, WAWANCARA, KONTRAK, SAMAPTA, OJT, SK |
| `nama` | VARCHAR | |
| `kategori` | VARCHAR | Seleksi / Pasca-seleksi |

Hanya berisi fakta yang **tidak tergantung jalur**.

### `komponen_nilai`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `tahap_kode` | VARCHAR FK → `tahap_referensi.kode` | komponen ini milik tahap apa |
| `nama` | VARCHAR | |
| `nilai_maksimal` | DECIMAL(5,2), NULL | skala nilai |

Contoh isi:

```
 id  tahap_kode        nama                 nilai_maksimal
  1  adaptif           Skor Adaptif         100.00
  2  akademik_inggris  TPA                  100.00
  3  akademik_inggris  Bahasa Inggris       100.00
  4  psikologi         Kecerdasan Umum      100.00
  5  psikologi         Kepribadian          100.00
  6  wawancara         Kompetensi Teknis    100.00
  7  wawancara         Kompetensi Perilaku  100.00
  8  samapta           Kesamaptaan          100.00
  9  ujian_ojt         Ujian OJT            100.00
```

Satu tahap bisa punya beberapa komponen yang dinilai sendiri-sendiri. Tahap
`akademik_inggris` yang contohnya paling jelas: TPA dan Bahasa Inggris digelar dalam satu
hari tapi dinilai terpisah dan punya ambang masing-masing.

Ada di MASTER, bukan di PENDAFTARAN, karena daftar komponen adalah kosakata tetap yang sudah
harus tersedia saat program_rekrutmen disusun — `tahap_program_komponen` di section PROGRAM menetapkan
ambang tiap komponen jauh sebelum ada satu pun pelamar.

### `tahap_jalur`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `jalur_rekrutmen_id` | INTEGER FK → `jalur_rekrutmen.id` | |
| `tahap_kode` | VARCHAR FK → `tahap_referensi.kode` | |
| `urutan` | INTEGER | urutan tahap **di jalur itu** |
| `pemilik_proses` | VARCHAR | pihak yang menjalankan, mis. PLN / FHCI / Vendor |
| `mode_default` | VARCHAR | online / offline |

UNIQUE (`jalur_rekrutmen_id`, `tahap_kode`)

Tahap yang sama bisa dimiliki pihak berbeda tergantung jalur — TKD dijalankan PLN di jalur
Mandiri, dijalankan FHCI di jalur RBB. Urutan juga berbeda: jalur RBB masuk di tengah
pipeline. Karena itu kedua kolom ini ada di sini, bukan di `tahap_referensi`.

---

## Daftar tabel section MASTER (31 tabel)

| # | tabel | isi |
|---|---|---|
| 1 | `provinsi` | lookup wilayah |
| 2 | `kota_kabupaten` | lookup wilayah |
| 3 | `peraturan_3t` | periode penetapan daerah tertinggal |
| 4 | `daerah_3t` | kota/kabupaten mana 3T di periode mana |
| 5 | `bidang` | lookup bidang teratas |
| 6 | `sub_bidang` | lookup sub bidang |
| 7 | `fungsi` | lookup fungsi pekerjaan |
| 8 | `grade` | lookup jenjang jabatan |
| 9 | `kelompok_jabatan` | lookup kelompok + penanda struktural |
| 10 | `jenjang_pendidikan` | lookup jenjang pendidikan |
| 11 | `agama` | lookup agama |
| 12 | `status_perkawinan` | lookup status perkawinan |
| 13 | `perusahaan` | Holding / SubHolding / Anak Perusahaan |
| 14 | `jenis_unit` | lookup lapis unit + level |
| 15 | `lini_bisnis` | lookup lini bisnis unit |
| 16 | `unit` | seluruh unit, berjenjang lewat `unit_atasan_id` |
| 17 | `jabatan` | katalog jabatan |
| 18 | `klasifikasi_jabatan` | pemetaan jabatan → sub bidang & fungsi |
| 19 | `posisi` | jabatan × unit — satu kursi |
| 20 | `profesi_rekrutmen` | nama profesi_rekrutmen di pengumuman rekrutmen |
| 21 | `jumlah_pegawai_bulanan` | realisasi jumlah pegawai per posisi per bulan |
| 22 | `jurusan` | katalog program_rekrutmen studi |
| 23 | `institusi_pendidikan` | katalog SMA/SMK/politeknik/universitas |
| 24 | `institusi_jurusan` | prodi apa dibuka di institusi mana, jenjang apa |
| 25 | `pemetaan_jurusan_sub_bidang` | pasokan lulusan → sub bidang |
| 26 | `vendor` | penyedia layanan seleksi |
| 27 | `venue` | tempat pelaksanaan tahap |
| 28 | `jalur_rekrutmen` | jalur rekrutmen |
| 29 | `tahap_referensi` | kosakata tahapan |
| 30 | `komponen_nilai` | komponen nilai yang dimiliki tiap tahap |
| 31 | `tahap_jalur` | urutan & pemilik tahap per jalur |

---

## Catatan terbuka (belum diputuskan, dibawa ke section berikutnya)

1. **Aturan grade masuk per jenjang pendidikan** (S1 → G2, D3 → G1, S2 → G3) belum punya
   tempat. Kandidatnya tabel aturan sendiri di section Perencanaan, atau tetap jadi aturan
   di dokumen. Perlu diputuskan sebelum section Kandidat/Penempatan.
2. **Target/FTK per unit per tahun** sengaja tidak masuk section Master — masuk Perencanaan.
3. `jenis_unit`, `jenis_layanan`, `mode_default`, `kategori` sengaja dibiarkan teks biasa
   karena tidak dipakai join lintas tabel. Kalau nanti ternyata dipakai untuk filter analitik,
   ubah jadi lookup.
