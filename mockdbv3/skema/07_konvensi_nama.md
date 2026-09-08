# Konvensi nama untuk mockdbv3

Status: **usulan, menunggu keputusan user.** Nama akhir tabel dan kolom kamu yang putuskan.

Tujuan dokumen ini: menyiapkan nama yang mudah dipakai chatbot LLM untuk membuat query.
Semua usulan di sini berangkat dari satu pertanyaan — kalau model hanya membaca daftar nama
tabel dan kolom tanpa penjelasan, apakah ia bisa menebak join yang benar?

---

## Syaratnya ada, dan ini delapan yang paling menentukan

**1. Nama FK harus menyebut tabel tujuannya.**
Ini yang paling berpengaruh. `posisi_id` → `posisi.id` bisa ditebak tanpa membaca dokumentasi
apa pun. `kota_kabupaten_id` → `kota_kabupaten.id` tidak bisa. Model akan mencari tabel `kota` yang tidak
ada, lalu menebak, dan tebakan yang salah menghasilkan query yang tetap jalan tapi hasilnya
keliru — kegagalan paling berbahaya karena tidak ada pesan error.

Kalau satu tabel menunjuk tabel yang sama dua kali, barulah pakai awalan peran:
`tahun_program_id` dan `tahun_terisi_id` keduanya ke `tahun_program`. Awalan peran boleh, tapi
akhirannya tetap harus menyisakan jejak tabel tujuan.

**2. Satu nama, satu arti, di seluruh basis data.**
`nama` muncul di 30 tabel dan itu justru bagus — artinya selalu sama. Yang berbahaya sebaliknya:
`jenis` di tiga tabel dengan arti berbeda-beda, `hasil` di dua tabel, `status` di dua tabel.
Ketika model menulis query dengan lima join, kolom bernama `jenis` tanpa awalan akan diambil
dari tabel yang salah.

**3. Nama tabel harus mengatakan isi satu barisnya.**
`pendaftaran_tahap` = satu tahap dari satu pendaftaran. Jelas. `jumlah_pegawai_bulanan` = satu apa?
Model harus menebak apakah satu baris berarti satu pegawai atau satu pengukuran.

**4. Hindari nama yang berbeda tipis.**
`pagu_rekrutmen` vs `pagu_rekrutmen_perusahaan`, `bukaan_profesi_pagu` vs `bukaan_profesi_pagu_perusahaan`.
Model yang salah pilih satu huruf akan menghasilkan angka yang salah tanpa error.

**5. Hindari awalan yang sama untuk hal yang tidak berkerabat.**
`program_rekrutmen` dan `jurusan` bukan induk-anak, tapi namanya seolah begitu. Model akan
menyangka `jurusan` adalah detail dari `program_rekrutmen`, lalu mencoba join lewat `program_rekrutmen_id`
yang tidak ada.

**6. Boolean berawalan seragam.**
Sekarang campur: `is_struktural`, `is_buta_warna`, `is_bertato`. Tiga gaya untuk satu jenis kolom.
Pilih satu.

**7. Satu bahasa.**
Sudah hampir seragam bahasa Indonesia. Sisa istilah Inggris: `grade`, `jumlah_pegawai_bulanan`,
`mode`, `venue`. `grade` sebaiknya tetap — itu istilah resmi PLN yang dipakai sehari-hari, dan
menerjemahkannya justru menjauhkan dari kosakata pengguna.

**8. Kata bilangan dan satuan ikut di nama kolom.**
`jumlah_pagu` lebih baik dari `jumlah`. `pengalaman_minimal_bulan` sudah benar — satuannya
ikut, jadi model tidak perlu menebak bulan atau tahun.

---

## Yang perlu diganti — risiko tinggi

Ini yang benar-benar berpotensi menghasilkan query salah.

| sekarang | usul | alasan |
|---|---|---|
| `vendor.kota_kabupaten_id` | `kota_kabupaten_id` | tabel `kota` tidak ada |
| `institusi_pendidikan.kota_kabupaten_id` | `kota_kabupaten_id` | sama |
| `kandidat.kota_kabupaten_lahir_id` | `kota_kabupaten_lahir_id` | perannya tetap terbaca, tabel tujuannya juga |
| `pendaftaran.kota_kabupaten_domisili_id` | `kota_kabupaten_domisili_id` | sama |
| `pendaftaran.kota_kabupaten_tes_id` | `kota_kabupaten_tes_id` | sama |
| `tahap_jalur.jalur_rekrutmen_id` | `jalur_rekrutmen_id` | tabelnya `jalur_rekrutmen` |
| `klasifikasi_jabatan.bidang` / `.sub_bidang` | pastikan `sub_bidang_id`, `fungsi_id` | kalau masih teks, ini teks bebas yang seharusnya FK |
| `jumlah_pegawai_bulanan` | `jumlah_pegawai_bulanan` | satu baris = satu pengukuran per posisi per bulan, bukan "snapshot" |
| `jurusan` | `jurusan` | kata yang dipakai HTD di berkas mereka; sekaligus memutus tabrakan awalan dengan `program_rekrutmen`, sehingga `program_rekrutmen` tidak perlu diganti |
| `pagu_rekrutmen_perusahaan` | `pagu_rekrutmen_perusahaan` | "shap" = SubHolding & Anak Perusahaan, singkatan internal yang tidak bisa ditebak model |
| `bukaan_profesi_pagu_perusahaan` | `bukaan_profesi_pagu_perusahaan` | sama |
| `proyeksi_kekosongan.jumlah` | `jumlah_kekosongan` | `jumlah` telanjang terlalu umum |
| `pendaftaran_tahap.tanggal` | `tanggal_pelaksanaan` | ada belasan kolom tanggal di skema ini |

---

## Yang perlu diganti — kolom generik

Semua ini nama telanjang yang artinya bergantung tabelnya. Aman kalau query cuma satu tabel;
berbahaya begitu ada join.

| tabel | sekarang | usul |
|---|---|---|
| `perusahaan` | `kategori` | `kategori_perusahaan` |
| `institusi_pendidikan` | `jenis` | `jenis_institusi` |
| `venue` | `jenis` | `jenis_venue` |
| `kandidat_alamat` | `jenis` | `jenis_alamat` |
| `program_rekrutmen` | `status` | `status_program` |
| `tahun_program` | `status` | `status_tahun` |
| `tahap_program` | `mode` | `mode_pelaksanaan` |
| `pendaftaran_tahap` | `hasil` | `hasil_tahap` |
| `kandidat_ikatan_dinas` | `hasil` | `hasil_ikatan_dinas` |
| `peraturan_3t` | `nomor` | `nomor_peraturan` |
| `jenis_unit` | `level` | `level_unit` |
| `pemeriksaan_kesehatan` | `kesimpulan` | `kesimpulan_mcu` |

`nama`, `kode`, dan `urutan` **tidak** perlu diubah. Ketiganya artinya persis sama di mana pun
muncul, dan justru membantu model mengenali pola "ini tabel lookup".

---

## Boolean: pilih satu gaya

Sekarang ada tiga: `is_struktural`, `is_buta_warna`, `is_bertato`.

Usul: pakai awalan `is_` untuk semuanya — `is_struktural`, `is_buta_warna`, `is_bertato`.
Alasannya bukan selera: awalan seragam membuat model langsung tahu kolom itu boolean tanpa
membaca tipenya, dan `is_buta_warna` tanpa awalan bisa disangka kolom teks berisi jenis buta
warna.

Kalau lebih suka bahasa Indonesia penuh, alternatifnya awalan `apakah_`. Yang penting satu
gaya, bukan tiga.

---

## Kosakata tim HTD, dari berkas mereka sendiri

Dibaca dari lima berkas `Sample-0X` di folder `data sintetis`. Ini bukan tebakan gaya
penamaan — ini kata yang benar-benar dipakai tim HTD di kolom-kolom kerja mereka.

| berkas | kolom di sana | nama kita sekarang |
|---|---|---|
| Sample-01 DTPEG | Posisi · Kode Posisi · Nama Panjang Posisi | `posisi` ✓ |
| Sample-01 DTPEG | Pendidikan Terakhir · Jurusan Pendidikan | `jenjang_pendidikan` · `jurusan` |
| Sample-01 DTPEG | Personel Number · NIP | `nomor_pegawai` ✓ |
| Sample-01 DTPEG | Jenjang - Sub Grp Text → "Generalist 1 (G1) - 10" | `grade` ✓ |
| Sample-02 Pagu FTK | FORMASI TENAGA KERJA (FTK) · JENIS UNIT · NAMA UNIT | `formasi_tenaga_kerja` ✓ · `jenis_unit` ✓ |
| Sample-03 Realisasi | % Pengisian · Realisasi \<bulan\> \<tahun\> | dihitung, tidak disimpan |
| Sample-04 Penetapan Pagu | JABATAN · JURUSAN PENDIDIKAN · JUMLAH · PENDIDIKAN | `posisi` · `jurusan` · `jumlah_pagu` · `jenjang_pendidikan` |
| Sample-05 Penempatan OJT | NO TES · ANGKATAN · SEBUTAN JABATAN · PROYEKSI OJT | `nomor_pendaftaran` · `angkatan` ✓ · `jabatan.nama` · `penempatan_ojt` |

Tiga temuan yang mengubah usul saya sebelumnya:

**1. `jurusan` sebaiknya jadi `jurusan`.** Tim HTD menulis "JURUSAN PENDIDIKAN" di dua
berkas berbeda, tidak pernah "program_rekrutmen studi". Bonusnya besar: tabrakan awalan antara `program_rekrutmen`
dan `jurusan` hilang dengan sendirinya, jadi `program_rekrutmen` **tidak perlu** diganti jadi
`program_rekrutmen`. Satu penggantian menyelesaikan dua masalah, dan hasilnya justru lebih
dekat ke kosakata pengguna.

**2. `posisi` sudah kata mereka.** Sample-01 punya kolom Posisi, Kode Posisi, dan Nama Panjang
Posisi. Jadi tidak perlu diganti jadi `formasi_jabatan_unit` — nama panjang itu malah menjauh
dari kata yang dipakai sehari-hari.

**3. `nomor_pendaftaran` mungkin lebih tepat `nomor_tes`.** Sample-05 memakai "NO TES" dengan
format `2511/ES/92/D3-ELE/135615` — di dalamnya sudah terkandung angkatan (92) dan jurusan
(D3-ELE). Perlu kamu pastikan: apakah nomor tes ini sama dengan nomor yang didapat pelamar
saat mendaftar, atau nomor baru yang terbit belakangan?

Satu hal di luar penamaan yang perlu dicek, karena kalau benar ia mengubah struktur, bukan
cuma nama: **Sample-05 memproyeksikan penempatan OJT sampai tiga lapis — UI (Unit Induk), UP
(Unit Pelaksana), dan UL (Unit Layanan).** Skema kita menyepakati OJT berhenti di unit induk,
dan `unit` hanya dua lapis. Kalau Unit Layanan memang lapis ketiga yang nyata, `unit` perlu
lapis tambahan dan `penempatan_ojt` perlu ditinjau ulang.

---

## Trio yang paling berisiko: `jabatan` · `posisi` · `profesi_rekrutmen`

Tiga tabel, tiga arti berbeda, dan namanya terdengar mirip bagi siapa pun — termasuk model.

```
jabatan   katalog nama jabatan               "Engineer Distribusi"
posisi    jabatan × unit, satu kursi         "Engineer Distribusi di UP3 Bandung"
profesi_rekrutmen   nama yang diumumkan ke pelamar     "Engineer Distribusi" (untuk seluruh Indonesia)
```

Model yang diminta "berapa lowongan Engineer Distribusi" punya tiga tabel yang semuanya
tampak benar. Dua cara memperjelas:

- **Opsi A — ganti namanya** supaya bedanya kelihatan tanpa membaca dokumentasi:
  `posisi` → `formasi_jabatan_unit`, `profesi_rekrutmen` → `profesi_rekrutmen`. Panjang, tapi tidak
  bisa tertukar.
- **Opsi B — biarkan namanya**, dan pastikan deskripsi tiap tabel ikut dikirim ke chatbot
  bersama skemanya. Deskripsi biasanya lebih menentukan akurasi daripada nama itu sendiri.

Setelah membaca berkas HTD, usul saya berubah jadi **B untuk `jabatan` dan `posisi`** (dua-
duanya kata yang benar-benar mereka pakai — menggantinya justru merugikan) dan **A hanya
untuk `profesi_rekrutmen`** → `profesi_rekrutmen`, karena `profesi_rekrutmen` tidak muncul di berkas kerja mereka
sama sekali dan tidak punya padanan jelas bagi orang di luar proses rekrutmen.

---

## Empat tabel bernama "tahap"

```
tahap_referensi         katalog tahap                    ADM, TPA, PSIKOLOGI, …
tahap_jalur              urutan tahap baku per jalur      referensi
tahap_program           tahap yang dijalankan program_rekrutmen    pelaksanaan
tahap_program_komponen  ambang tiap komponen nilai
pendaftaran_tahap       satu peserta di satu tahap       kejadian
```

Ini sebenarnya sudah cukup jelas kalau dibaca berurutan, tapi `tahap_jalur` menyimpang dari
pola yang lain. Usul: `tahap_jalur` — supaya kelima-limanya berawalan atau berakhiran `tahap`
dengan pola yang sama, dan model bisa mengenali kelompoknya.

---

## Yang sudah benar dan sebaiknya tidak diutak-atik

- Semua nama junction sudah `induk_anak`: `bukaan_profesi_jurusan`,
  `kelas_ikatan_dinas_pagu`, `daerah_3t`.
- Semua tabel bentuk tunggal. Konsisten, jangan sebagian dijamakkan.
- `kandidat_*` sebagai awalan tabel milik kandidat — polanya langsung terbaca.
- Kolom satuan sudah ikut nama: `pengalaman_minimal_bulan`, `tinggi_badan`, `lingkar_perut`.
- `grade` tetap `grade`. Istilah resmi PLN, dipakai sehari-hari, dan mengindonesiakannya justru
  menjauhkan dari kosakata penggunanya.

---

## Hal yang lebih menentukan daripada nama

Perlu dikatakan supaya tidak salah harap: penamaan yang rapi menaikkan akurasi text-to-SQL,
tapi bukan faktor terbesar. Tiga hal berikut biasanya lebih menentukan, dan semuanya urusan
tahap berikutnya, bukan tahap ini:

1. **Deskripsi tiap tabel dan kolom yang ikut dikirim ke model.** Enam file skema ini sudah
   berisi alasan tiap kolom — itu bahan mentah yang jauh lebih berharga daripada nama pendek.
2. **Contoh query untuk pertanyaan yang sering ditanya.** Model meniru pola.
3. **View untuk join yang panjang.** Rantai `sk_penempatan → pendaftaran_tahap → pendaftaran →
   kandidat` akan sering salah kalau ditulis ulang tiap kali. Satu view menghapus seluruh
   kelas kesalahan itu.

---

## Yang perlu kamu putuskan

1. ~~Terima atau tolak usulan penggantian nama~~ — diterima seluruhnya, dengan satu
   perubahan setelah membaca berkas HTD: `program_rekrutmen` **tidak** jadi diganti; yang diganti
   `jurusan` → `jurusan`.
2. ~~Gaya boolean~~ — diputuskan: awalan `is_`. Jadi `is_struktural`, `is_buta_warna`,
   `is_bertato`.
3. **Trio jabatan/posisi/profesi_rekrutmen** — usul terbaru: B untuk `jabatan` & `posisi`, A untuk
   `profesi_rekrutmen` → `profesi_rekrutmen`. Perlu keputusanmu.
4. ~~`alur_tahap` → `tahap_jalur`~~ — diputuskan: diganti jadi `tahap_jalur`. Tabel di MASTER section H, isinya jalur × tahap: urutan
   dan pemilik proses tiap tahap **per jalur rekrutmen** (TKD dijalankan PLN di jalur Mandiri,
   dijalankan FHCI di jalur RBB). Ini tabel referensi, pasangannya `tahap_program` yang
   pelaksanaan.
5. ~~`nomor_pendaftaran` atau `nomor_tes`~~ — diputuskan tetap `nomor_pendaftaran`. Nomor tes
   di Sample-05 memang nomor yang didapat setelah mendaftar ke program, dan **berbeda** dari
   id akun di web rekrutmen. Ada tiga nomor di skema ini: id akun (`kandidat`), nomor
   pendaftaran (`pendaftaran`), NIP (`pegawai`).
6. ~~Unit Layanan — lapis ketiga?~~ — diputuskan: **tidak untuk mockdbv3**. ULP memang ada di
   kenyataan, tapi tidak dimodelkan. Seluruh tahap dan seluruh proses berhenti di level 2,
   unit pelaksana.

