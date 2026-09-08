# Skema mockdbv3 — Section 3: PROGRAM

Section ini menjawab: **pagu yang sudah ditetapkan itu dieksekusi lewat bukaan rekrutmen
yang mana, menawarkan profesi_rekrutmen apa, dengan kuota berapa, jurusan apa yang diterima, dan
tahapan seleksi apa yang dijalankan.** Ini wilayah kerja tim HTD.

Prinsip desain sama dengan section sebelumnya:
1. Semua tabel entitas punya primary key sendiri.
2. Tidak menyimpan nilai turunan yang bisa dihitung ulang lewat join/agregat.
3. Tidak ada kolom untuk kepentingan generator/analis — bentuknya database produksi.
4. Data yang berubah menurut waktu wajib punya kolom periode.
5. Kosakata yang dipakai lintas tabel jadi tabel lookup, bukan teks bebas.
6. Usulan dan keputusan dipisah; referensi dan keputusan dipisah.

Tambahan prinsip khusus section ini:

7. **Atribut induk tidak disalin ke anak.** Tanggal buka/tutup, tahun, jenis program_rekrutmen hanya
   ada di satu tempat. v1 menyalin tujuh kolom program_rekrutmen ke tiap baris profesi_rekrutmen.

---

## Alur data section ini

```
pagu_rekrutmen           (dari PERENCANAAN, per unit × jabatan × jenjang × jalur)
       ↓  HTD meramu bukaan
angkatan  →  program_rekrutmen  →  bukaan_profesi   (satuan yang diumumkan & didaftari)
                            ├─→ bukaan_profesi_jurusan  (jurusan yang diterima)
                            ├─→ bukaan_profesi_pagu           (memenuhi pagu yang mana)
                            └─→ bukaan_profesi_pagu_perusahaan      (jatah SubHolding/AP)
       ↓
kelas_ikatan_dinas       (jalur terpisah: kelas di universitas, lulusannya bergabung
                          langsung di pasca-seleksi)
       ↓
tahap_program            (tahapan yang benar-benar dijalankan: urutan, tanggal,
                          vendor, cara meluluskan, ambang nilai)
                            └─→ lokasi_tes              (kota tempat tahap digelar)
       ↓
(section KANDIDAT & PENDAFTARAN)
```

---

## A. Bukaan rekrutmen

### `angkatan`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `nomor` | INTEGER | nomor angkatan, mis. 70 |
| `nama` | VARCHAR | mis. Angkatan 70 |
| `tahun_masuk` | INTEGER | tahun kohort ini mulai bekerja |

Kohort masuk. Dipisah dari `program_rekrutmen` karena satu angkatan bisa diisi lebih dari satu
program_rekrutmen (mis. satu program_rekrutmen jalur Mandiri dan satu program_rekrutmen jalur RBB yang lulusannya masuk
bersamaan), dan sebaliknya nomor angkatan dipakai terus di data kepegawaian setelah
rekrutmen selesai.

Tidak ada `n_program` atau `diterima_target` di sini — keduanya agregat turunan. v1
menyimpannya dan itu jadi angka kedua yang bisa berbeda dari hitungan sebenarnya.

### `jenis_program`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `nama` | VARCHAR | Reguler, Pro Hire, PLN Group, Ikatan Dinas |

### `program_rekrutmen`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `tahun_program_id` | INTEGER FK → `tahun_program.id` | |
| `angkatan_id` | INTEGER FK → `angkatan.id` | |
| `jenis_program_id` | INTEGER FK → `jenis_program.id` | |
| `jalur_rekrutmen_id` | INTEGER FK → `jalur_rekrutmen.id` | Mandiri atau RBB |
| `nama` | VARCHAR | judul pengumuman apa adanya |
| `tanggal_buka` | DATE | |
| `tanggal_tutup` | DATE | |
| `status_program` | VARCHAR | Dibuka, Ditutup, Selesai, Dibatalkan |

Satu baris = satu bukaan rekrutmen yang diumumkan. Tanggal buka/tutup **hanya** di sini,
tidak disalin ke profesi_rekrutmen.

Tidak ada kolom `jenjang_pendidikan_id` di program_rekrutmen: satu program_rekrutmen bisa membuka beberapa
jenjang sekaligus. Jenjang melekat pada profesi_rekrutmen.

**Komposisi jenjang program_rekrutmen adalah turunan dari komposisi jenjang pagu.** HTD meramu program_rekrutmen
mengikuti pagu — kalau pagu tahun itu banyak menuntut SMK maka dibuka program_rekrutmen level SMK.
Ini bukan kolom, ini aturan yang harus dipatuhi saat pengisian data.

---

## B. Profesi yang ditawarkan

### `bukaan_profesi`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `program_rekrutmen_id` | INTEGER FK → `program_rekrutmen.id` | |
| `profesi_rekrutmen_id` | INTEGER FK → `profesi_rekrutmen.id` | nama profesi_rekrutmen, dari MASTER |
| `kuota` | INTEGER | jumlah orang yang akan diterima |

UNIQUE (`program_rekrutmen_id`, `profesi_rekrutmen_id`)

**Profesi adalah satuan yang diumumkan ke publik dan satuan tempat orang mendaftar** —
bukan program_rekrutmen, bukan unit. Ini aturan yang sudah terkunci sejak riset.

Nama profesi_rekrutmen, sub bidang, dan jenjangnya ada di `profesi_rekrutmen` (MASTER) karena tetap dari tahun
ke tahun. Yang berubah tiap bukaan hanyalah **kuota**, dan itu yang disimpan di sini.

Satu bukaan profesi_rekrutmen menggabungkan pagu banyak unit yang `sub_bidang` dan jenjangnya sama.
Contoh: pagu Junior Technician Distribusi D3 di UP3 Surabaya Selatan (5), UP3 Malang (3),
UP3 Kediri (4), dan seterusnya, digabung jadi satu bukaan berkuota 87.

`kuota` **tetap disimpan**, meski sekilas terlihat sebagai jumlah pagu yang terhubung.
Alasannya justru itu yang mau diukur: HTD bisa membuka kuota yang tidak persis sama dengan
jumlah pagu — dan selisihnya adalah asal-usul keluhan BPO soal perencanaan yang tidak
nyambung dengan pelaksanaan. Kalau `kuota` dihitung otomatis dari pagu, selisih itu mustahil
ada, dan datanya jadi berbohong bahwa semua selalu pas.

Kuota berbeda dari `headcount_current` yang dulu dibuang dari tabel unit. `headcount_current`
adalah **pengukuran atas kenyataan yang terus berubah** tanpa titik waktu, jadi tanpa periode
tidak punya arti. `kuota` adalah **keputusan yang diumumkan sekali** dan tidak bergeser
karena waktu berjalan. Yang berubah adalah berapa yang sudah diterima, dan itu **tidak**
disimpan — dihitung dari jumlah baris penempatan. (v1 menyimpannya sebagai
`gelombang.diterima_target`, dan itu memang salah jenis.)

Kuota hanya butuh riwayat kalau pengumuman pernah direvisi lewat adendum di tengah bukaan.
Belum ada informasi bahwa itu terjadi.

Guna `kuota`, supaya jelas kenapa tidak bisa dibuang:
1. **Rasio persaingan** — 12.400 pelamar : kuota 87 = 1:143. Penyebutnya kuota.
2. **Titik potong tahap berjenis Peringkat** — tes meluluskan sekian kali kuota.
3. **Kursi tidak terisi** — kuota 87, diterima 79, delapan kursi menganggur.
4. **Selisih terhadap pagu** — pagu terhubung 52, kuota dibuka 46: enam kursi direncanakan
   tapi tidak pernah dibuka.

Tidak ada `min_ipk` dan `umur_maks` di sini: keduanya sudah diatur `syarat_pelamar` per
jalur × jenjang di PERENCANAAN, dan dikonfirmasi tidak ada profesi_rekrutmen yang menyimpang.

### `bukaan_profesi_jurusan`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `bukaan_profesi_id` | INTEGER FK → `bukaan_profesi.id` | |
| `jurusan_id` | INTEGER FK → `jurusan.id` | |

UNIQUE (`bukaan_profesi_id`, `jurusan_id`)

Jurusan yang diterima untuk bukaan ini. Seragam se-Indonesia untuk satu profesi_rekrutmen — itu
sebabnya menempel di sini, bukan di baris pagu per unit. Menempel ke **bukaan**, bukan ke
`profesi_rekrutmen` di MASTER, karena daftarnya keputusan HTD yang boleh berbeda tiap tahun.

Isinya **keputusan**, bukan referensi. `pemetaan_jurusan_sub_bidang` di MASTER berisi semua
jurusan yang relevan dengan sebuah sub bidang; tabel ini berisi yang benar-benar dibuka kali
ini, dan boleh lebih sempit. Selisih keduanya bisa ditanyakan: "jurusan relevan apa saja
yang tahun ini justru tidak dibuka?"

### `bukaan_profesi_pagu`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `bukaan_profesi_id` | INTEGER FK → `bukaan_profesi.id` | |
| `pagu_rekrutmen_id` | INTEGER FK → `pagu_rekrutmen.id` | |

UNIQUE (`bukaan_profesi_id`, `pagu_rekrutmen_id`)

Penghubung rencana dan eksekusi. Tanpa tabel ini, pagu dan program_rekrutmen jadi dua dunia terpisah
dan pertanyaan "pagu mana yang tidak pernah dibuka sama sekali" tidak bisa dijawab.

Sengaja **tidak** wajib: boleh ada baris pagu yang tidak punya bukaan (tidak dieksekusi
tahun itu), dan boleh ada bukaan yang tidak menunjuk pagu mana pun (bukaan di luar
perencanaan). Dua-duanya terjadi di lapangan, dan dua-duanya adalah temuan.

### `bukaan_profesi_pagu_perusahaan`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `bukaan_profesi_id` | INTEGER FK → `bukaan_profesi.id` | |
| `pagu_rekrutmen_perusahaan_id` | INTEGER FK → `pagu_rekrutmen_perusahaan.id` | |

UNIQUE (`bukaan_profesi_id`, `pagu_rekrutmen_perusahaan_id`)

Sama perannya, untuk jatah SubHolding / Anak Perusahaan. Dipisah karena pagu SH/AP memang
tabel tersendiri (bentuk data dan penetapnya berbeda).


**Catatan nama:** akhiran `_perusahaan` di sini adalah pengganti singkatan **SH/AP**, yaitu
**SubHolding dan Anak Perusahaan**. Nama lamanya `..._shap`, diganti karena "shap" singkatan
internal yang tidak bisa ditebak siapa pun di luar tim — termasuk chatbot yang membaca skema
ini. Pilihan kata "perusahaan" cocok karena baris-baris ini memang menunjuk
`perusahaan.id` yang berkategori SubHolding atau Anak Perusahaan, bukan Holding.

---

## B2. Ikatan Dinas

Jalur ini bentuknya berbeda: seleksinya terjadi bertahun-tahun sebelumnya, saat orangnya
masih calon mahasiswa, dan **tidak dilacak** di sini. Yang dilacak adalah kelas yang sedang
berjalan, supaya bisa diketahui kapan lulusannya mulai masuk PLN. Orangnya bergabung dengan
jalur lain saat masuk pasca-seleksi (samapta → pembidangan → OJT → ujian OJT → SK
penempatan).

### `kelas_ikatan_dinas`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `institusi_jurusan_id` | INTEGER FK → `institusi_jurusan.id` | universitas + jurusan + jenjang sekaligus |
| `angkatan_id` | INTEGER FK → `angkatan.id`, NULL | diisi saat lulus: bergabung ke angkatan mana |
| `tahun_mulai` | INTEGER | tahun kelas mulai kuliah |
| `tahun_lulus_rencana` | INTEGER | perkiraan lulus, dari lama studi jenjangnya |
| `kuota` | INTEGER | jumlah kursi yang dibuka untuk kelas ini |

UNIQUE (`institusi_jurusan_id`, `tahun_mulai`)

Satu FK ke `institusi_jurusan`, bukan tiga FK terpisah ke universitas + jurusan +
jenjang — pola yang sama dengan `posisi`, dan langsung menjamin kombinasi itu benar-benar
ada (tidak bisa muncul "S1 Teknik Elektro di universitas yang tidak membuka jurusan itu").

**Tidak ada kolom "jumlah yang sedang kuliah".** Itu pengukuran atas kenyataan yang berubah
— ada yang mengundurkan diri di tengah kuliah — jadi dihitung dari jumlah kandidat yang
terhubung ke kelas ini dan statusnya masih kuliah. Yang disimpan adalah `kuota`, karena itu
keputusan yang ditetapkan sekali saat kelas dibuka.

`angkatan_id` boleh NULL selama kelasnya belum lulus. Untuk jalur Mandiri dan RBB, angkatan
ditentukan di tingkat `program_rekrutmen`; untuk ikatan dinas, angkatan baru diketahui saat lulus,
jadi tempatnya di sini.

Kelas ikatan dinas **tidak** punya `bukaan_profesi`: tidak ada profesi_rekrutmen yang diumumkan, dan
pembidangan ditentukan belakangan mengikuti jurusan kuliahnya.

### `kelas_ikatan_dinas_pagu`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `kelas_ikatan_dinas_id` | INTEGER FK → `kelas_ikatan_dinas.id` | |
| `pagu_rekrutmen_id` | INTEGER FK → `pagu_rekrutmen.id` | pagu berjalur Ikatan Dinas |

UNIQUE (`kelas_ikatan_dinas_id`, `pagu_rekrutmen_id`)

Asal-usul anggaran dan kebutuhan kelas ikatan dinas. HTD tidak mungkin membuka kelas di
universitas tanpa anggaran, dan anggaran itu turun dari rencana HST — jadi kelas ini pasti
punya jejak pagu, sama seperti bukaan rekrutmen biasa.

Bedanya jaraknya jauh: pagu diputuskan di siklus 2022 tapi `tahun_terisi_id`-nya 2026,
karena mahasiswanya baru lulus 2025 dan menerima SK penempatan 2026. Itulah sebabnya
`pagu_rekrutmen` punya dua kolom tahun.

Rantai penelusuran lengkapnya:

```
proyeksi_kekosongan   siklus 2022, proyeksi untuk 2026
                      posisi Junior Technician Distribusi @ UP3 Surabaya Selatan
                      Pensiun · 4 orang
        ↓
pagu_rekrutmen  9902  tahun_program 2022 · tahun_terisi 2026
                      posisi sama · D3 · jalur Ikatan Dinas · jumlah_pagu 4
        ↓
kelas_ikatan_dinas 12 Politeknik Negeri Bandung · D3 Teknik Listrik
                      mulai 2022 · lulus rencana 2025 · kuota 30
        ↓
kelas_ikatan_dinas_pagu
                      kelas 12 ↔ pagu 9902  (4 kursi, UP3 Surabaya Selatan)
                      kelas 12 ↔ pagu 9915  (3 kursi, UP3 Malang)
                      …                     (total 30)
        ↓
2025 lulus → samapta → pembidangan → OJT → ujian OJT
2026 SK penempatan → kursi terisi
```

---

## C. Tahapan seleksi yang dijalankan

### `metode_kelulusan`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `nama` | VARCHAR | Ambang Nilai, Peringkat, Kualitatif |

Tidak semua tahap meluluskan dengan cara yang sama: TKD memakai ambang nilai, tes bidang
sering memakai peringkat sejumlah kuota, wawancara dan MCU bersifat kualitatif
(lulus/tidak lulus tanpa skor ambang). Kalau tidak dibedakan, angka `nilai_ambang` yang
kosong jadi ambigu — tidak ada ambangnya, atau ambangnya belum diisi?

### `tahap_program`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `program_rekrutmen_id` | INTEGER FK → `program_rekrutmen.id` | |
| `tahap_kode` | VARCHAR FK → `tahap_referensi.kode` | |
| `urutan` | INTEGER | urutan tahap di program_rekrutmen ini |
| `metode_kelulusan_id` | INTEGER FK → `metode_kelulusan.id` | |
| `vendor_id` | INTEGER FK → `vendor.id`, NULL | NULL = dijalankan sendiri, tanpa vendor |
| `tanggal_mulai` | DATE | |
| `tanggal_selesai` | DATE | |
| `mode_pelaksanaan` | VARCHAR | online, offline |

UNIQUE (`program_rekrutmen_id`, `tahap_kode`)

Tahapan yang **benar-benar dijalankan** program_rekrutmen ini. `tahap_jalur` di MASTER adalah
**referensi** (tahapan baku tiap jalur, beserta urutan dan pemiliknya); tabel ini adalah
pelaksanaannya, yang boleh menyimpang — tahap dilewati, urutan ditukar, ambang dinaikkan.
Selisih antara keduanya adalah informasi, bukan kesalahan data.

Passing grade tidak lagi di tabel ini — pindah ke `tahap_program_komponen` di bawah, karena
satu tahap bisa punya beberapa komponen dengan ambang berbeda. Passing grade disimpan karena ini salah satu dari tiga hal yang memang
tidak ada di sumber mana pun dan justru jadi alasan dashboard ini dibuat (dua lainnya:
kuota per posisi, dan skor tes mentah per kandidat).

### `tahap_program_komponen`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `tahap_program_id` | INTEGER FK → `tahap_program.id` | |
| `komponen_nilai_id` | INTEGER FK → `komponen_nilai.id` | |
| `nilai_ambang` | DECIMAL(5,2), NULL | NULL jika komponen ini tidak punya ambang sendiri |
| `bobot` | DECIMAL(4,3), NULL | porsi komponen ini kalau nilainya digabung |

UNIQUE (`tahap_program_id`, `komponen_nilai_id`)

Kolom `nilai_ambang` dipindahkan ke sini dari `tahap_program` — dikonfirmasi bahwa TPA dan
Bahasa Inggris memang dinilai berbeda. Sebelumnya satu tahap hanya punya satu angka ambang,
yang berarti "TPA 65, Inggris 50" tidak bisa dinyatakan sama sekali: dua-duanya dipaksa
memakai angka yang sama, atau salah satunya diam-diam tidak diperiksa.

Contoh isi (tahap `akademik_inggris` di program_rekrutmen 7):

```
 id  tahap_program  komponen        nilai_ambang  bobot
  1       73        TPA                65.00      0.600
  2       73        Bahasa Inggris     50.00      0.400
```

Dengan bentuk ini, "gugur karena Inggris walau TPA tinggi" jadi kejadian yang bisa dihitung.

`bobot` boleh NULL dan hanya dipakai kalau program_rekrutmen itu menggabungkan nilai jadi satu angka.
Nilai gabungannya sendiri tidak disimpan di mana pun — dihitung saat query dari
`pendaftaran_nilai` dan bobot di sini.

### `lokasi_tes`
| kolom | tipe | keterangan |
|---|---|---|
| `id` | INTEGER PK | |
| `tahap_program_id` | INTEGER FK → `tahap_program.id` | |
| `venue_id` | INTEGER FK → `venue.id` | tempat pelaksanaan; kotanya ikut dari venue |

UNIQUE (`tahap_program_id`, `venue_id`)

`kota_kabupaten_id` dihapus dari sini: kota sudah melekat pada venue, dan menyimpan keduanya
membuka peluang venue Bandung tercatat di kota Semarang (prinsip 7).

Kota adalah keputusan program_rekrutmen — "program_rekrutmen ini dibuka di 5 kota" — sedangkan venue urusan
pelaksanaan yang ditentukan tim HTD dan vendor di tiap kota. Keduanya sekarang tersimpan di
satu baris: daftar kota program_rekrutmen = DISTINCT kota dari venue yang dipakai.

Satu tahap bisa digelar di banyak kota; kota yang dipakai berbeda antar tahap (TKD di
banyak kota, wawancara terpusat di beberapa kota saja). v1 menyimpannya sebagai teks
`kota_rekrutmen` = "Seluruh Indonesia" di tiap profesi_rekrutmen, yang tidak bisa dihitung maupun
dipetakan.

Tahap yang tidak punya lokasi fisik (seleksi administrasi, tes online dari rumah) tidak
punya baris di sini.

---

## Daftar tabel section PROGRAM (13 tabel)

| # | tabel | isi |
|---|---|---|
| 1 | `angkatan` | kohort masuk |
| 2 | `jenis_program` | lookup jenis bukaan |
| 3 | `program_rekrutmen` | satu bukaan rekrutmen yang diumumkan |
| 4 | `bukaan_profesi` | profesi_rekrutmen yang dibuka program_rekrutmen ini + kuotanya |
| 5 | `bukaan_profesi_jurusan` | jurusan yang diterima tiap bukaan |
| 6 | `bukaan_profesi_pagu` | bukaan ini memenuhi pagu holding yang mana |
| 7 | `bukaan_profesi_pagu_perusahaan` | bukaan ini memenuhi pagu SH/AP yang mana |
| 8 | `kelas_ikatan_dinas` | kelas ikatan dinas yang sedang berjalan di universitas |
| 9 | `kelas_ikatan_dinas_pagu` | kelas ini memenuhi pagu yang mana |
| 10 | `metode_kelulusan` | lookup cara meluluskan tahap |
| 11 | `tahap_program` | tahapan yang dijalankan + vendor |
| 12 | `tahap_program_komponen` | ambang & bobot tiap komponen nilai |
| 13 | `lokasi_tes` | venue tempat tiap tahap digelar |

---

## Yang perlu kamu putuskan

1. **Nama tabel dan kolom** — semua di atas usulan saya.
2. ~~Angkatan~~ — sudah diputuskan: **satu program_rekrutmen menghasilkan tepat satu angkatan**
   (`program_rekrutmen.angkatan_id`), dan beberapa program_rekrutmen bisa bergabung jadi satu angkatan asalkan
   tingkat jenjangnya sekelompok (SMA/SMK/MA · D3/S1 · S2 ke atas) dan tanggal
   pelaksanaannya berdekatan. Bukaan D3 Januari dan bukaan D3 Juli di tahun yang sama =
   dua program_rekrutmen, dua angkatan.
3. **Tahapan per program_rekrutmen atau per profesi_rekrutmen?** Sekarang `tahap_program` menempel ke program_rekrutmen,
   jadi semua profesi_rekrutmen di satu program_rekrutmen melewati tahapan yang sama. Kalau tes bidang (TKB)
   berbeda isi/ambangnya antar profesi_rekrutmen, tabel ini harus pindah menempel ke profesi_rekrutmen.
4. ~~Kuota~~ — sudah diputuskan: kuota adalah jumlah yang dibuka **per profesi_rekrutmen per bukaan**,
   disimpan sebagai kolom di `bukaan_profesi`.
5. ~~Syarat menyimpang~~ — sudah diputuskan: tidak ada. `syarat_pelamar` berlaku seragam.
