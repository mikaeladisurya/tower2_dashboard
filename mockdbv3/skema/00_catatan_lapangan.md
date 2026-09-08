# Catatan lapangan — fakta dari user, belum semuanya masuk skema

Berkas ini menampung fakta proses yang disampaikan user langsung (bukan hasil tebakan
generator, bukan hasil baca dokumen). Dipakai saat merancang section yang relevan.
Setiap butir menyebut section mana yang harus memakainya.

---

## Alur besar (dikonfirmasi 2026-09-06)

```
unit pelaksana  → mengajukan usulan kebutuhan
      ↓ dikumpulkan
unit induk      → merekap usulan seluruh unit pelaksananya
      ↓
tim HST         → menyusun pagu (sampai tingkat unit pelaksana)
      ↓
tim HTD         → pelaksana rekrutmen; mengeksekusi pagu lewat program_rekrutmen
                   (satu tahun bisa punya beberapa program_rekrutmen)
      ↓ seleksi selesai
penempatan OJT  → diberikan di tingkat UNIT INDUK.
                   Unit induk sendiri yang memutuskan peserta ditaruh di kantor induk
                   atau di salah satu unit pelaksananya.
      ↓ lulus OJT
SK penempatan   → HTD mereview ulang, terbit SK sampai tingkat UNIT PELAKSANA.
```

**Keluhan BPO saat requirement gathering:** perencanaan dan penempatan akhir di lapangan
sebagian tidak sesuai. Ini bukan cacat data, ini temuan yang justru harus bisa diukur.
Implikasi desain: SK penempatan **tidak boleh dipaksa** menunjuk baris pagu yang cocok —
kalau relasinya dibuat wajib dan selalu valid, ketidaksesuaian itu lenyap dari data dan
keluhan BPO jadi tidak bisa dibuktikan lewat dashboard.

→ dipakai section PENEMPATAN.

## Perpindahan antara OJT dan SK penempatan

- SK penempatan biasanya mirip dengan penempatan OJT-nya.
- Hanya **5–10%** yang berpindah unit induk.
- **Jenjang S2 ke atas: ~90% berpindah unit induk.**
- Peserta yang OJT di **Kantor Pusat atau unit pusat lain** (bukan unit induk) biasanya
  tetap di situ saat SK penempatan terbit.

→ dipakai section PENEMPATAN, dan jadi angka kalibrasi saat generate data.

## Struktur organisasi (diputuskan 2026-09-06)

- Perusahaan (Holding / SubHolding / Anak Perusahaan) jadi tabel sendiri, bukan salah satu
  lapis di dalam `unit`.
- Unit hanya punya 2 lapis: **level 1** = Divisi (Kantor Pusat) / Unit Induk (daerah),
  lapis manajemen, tidak ada penempatan langsung. **level 2** = Bidang / Unit Pelaksana,
  tempat pegawai duduk dan tempat pagu mendarat.
- Sub Bidang dan ULP ada di dunia nyata tapi **tidak** dimodelkan — granulasi berhenti di
  level 2.
- Kantor Pusat tidak diagregasi: penempatan menunjuk Bidang tertentu di Divisi tertentu
  (mis. "Bidang Digitalisasi Kelistrikan" di "DIV Manajemen Digital"), bukan "Kantor Pusat".
- Kantor unit induk juga dipecah jadi bidang-bidangnya (Bidang Perencanaan, Bidang
  Distribusi, Bidang Niaga, Bidang Keuangan/SDM/Umum), supaya level 2 punya arti yang sama
  di mana-mana.
- Ada beberapa "pusat" yang setara unit induk: Pusdiklat, Pusertif, Pusharlis, Pusmanpro.
  Daftar lengkap lini bisnis ditetapkan di putaran pengisian data.

### Asumsi yang harus diingat saat pengisian data

Lembar FTK resmi menaruh KANTOR INDUK sebagai **satu** baris dengan satu angka FTK (mis.
150), tidak dipecah per bidang. Karena kita memecahnya jadi bidang, pembagian angka itu ke
tiap bidang adalah angka yang **kita tetapkan sendiri**, bukan salinan dari sumber. Daftar
bidangnya nyata; angkanya asumsi.

## Penempatan ke SubHolding / Anak Perusahaan

Program rekrutmen PLN Group menempatkan sebagian peserta ke SH/AP. Untuk mockdb ini SH/AP
tetap dangkal: kita tahu peserta ditempatkan di perusahaan mana, **tidak** tahu di unit apa.

Konsekuensi skema: tabel penempatan nanti butuh `perusahaan_id` (wajib) **dan** `unit_id`
(boleh NULL). NULL di situ berarti "unit internal SH/AP memang tidak dilacak", bukan
"tidak diketahui" — harus tertulis supaya tidak dikira data bolong.

→ dipakai section PENEMPATAN.

## Grain FTK dan pagu

Dari `Sample-02-Contoh Format Pagu FTK 2026.xlsx` (`rekrutmenHST/`):

- Satu berkas per unit induk. Rekap di atas memecah FTK per unit, dengan **"KANTOR INDUK"
  sebagai satu baris unit sejajar dengan unit pelaksana**.
- Rincian per unit: `NAMA JABATAN` (General, Senior Specialist, Officer) ·
  `SEBUTAN JABATAN` (Perencanaan Pengusahaan dan Kinerja) ·
  `JENJANG JABATAN` (MA, MM, SSP, SPC, G3, G2) · `FORMASI TENAGA KERJA (FTK)`.
- Lembar FTK **tidak** memuat jenjang pendidikan maupun jalur rekrutmen — dua hal itu baru
  muncul di tahap pagu.

→ sudah dipakai section PERENCANAAN.

## Alur tahapan per jalur (dari user, 2026-09-06)

### Jalur Mandiri — bukaan oleh PLN untuk PLN / PLN Group

PLN menetapkan pagu tiap jabatan dan kuota tiap profesi_rekrutmen, lalu:

```
pendaftaran → administrasi → tes adaptif PLN → TPA & Bahasa Inggris → psikologi
→ kesehatan → wawancara → TTD SK → samapta → pembidangan → OJT → tes OJT → SK penempatan
```

### Jalur RBB — bukaan oleh BUMN, PLN dapat beberapa slot

PLN memberi usulan posisi/profesi_rekrutmen beserta kuotanya, lalu:

```
peserta mendaftar → administrasi & tes adaptif BERSAMA (dijalankan BUMN/FHCI,
                    TIDAK di-track PLN)
→ sebagian yang lolos diteruskan ke PLN
→ TPA & Bahasa Inggris → psikologi → kesehatan → wawancara → TTD SK → samapta
→ pembidangan → OJT → tes OJT → SK penempatan
```

Konsekuensi data: kandidat jalur RBB **tidak punya baris tahap** untuk administrasi dan tes
adaptif. Itu bukan data hilang, itu memang tidak pernah dicatat PLN. Harus tertulis supaya
tidak dikira bolong.

### Jalur Ikatan Dinas

Seleksinya terjadi jauh sebelumnya, saat orangnya masih calon mahasiswa:

```
mahasiswa masuk jurusan tertentu
→ ada tes lanjutan bagi yang jurusannya sedang dibuka kelas ikatan dinas
   DAN yang mau ikut kelas itu
→ tesnya lebih berat dari masuk kuliah biasa, sampai wawancara
   (kemungkinan mirip alur tes masuk PLN — belum dikonfirmasi ke tim HTD,
   dan belum jelas apakah HTD yang menjalankan seleksinya)
→ lolos → TTD kontrak (setara peserta rekrutmen yang lolos wawancara)
→ selama kuliah: dibiayai PLN, disiapkan jadi pegawai
→ LULUS KULIAH — belum jadi pegawai
→ langsung masuk pasca-seleksi: samapta → pembidangan (sesuai jurusan)
   → OJT → ujian OJT → SK penempatan
```

**Cakupan yang disepakati untuk mockdb:** seleksi masuk kuliahnya **tidak** dilacak. Yang
dilacak hanya kelas ikatan dinas yang sedang berjalan (universitas apa, jurusan apa, mulai
kapan, lulus kapan, berapa kursi), supaya bisa diketahui kapan lulusannya mulai masuk PLN.
Orangnya baru bergabung dengan jalur lain di tahap pasca-seleksi.

**Ujian OJT untuk ikatan dinas formalitas — tidak ada yang gagal.** Angka kalibrasi saat
generate data.

### Nama tahap ketiga: TPA, bukan TKB

Dikonfirmasi user: **TPA (Tes Potensi Akademik)**, bukan TKB (Tes Kompetensi Bidang) seperti
tertulis di `tahap_ref.csv` v1. Kadang disebut **AKDING** (Akademik & Bahasa Inggris) karena
TPA dan tes Bahasa Inggris biasanya digabung dalam satu hari. Label v1 salah, jangan disalin.

### Pembidangan — bagaimana bidang ditentukan

Urutannya: TTD SK kontrak → samapta (sekitar 10 hari) → pembidangan. Di awal pembidangan
tiap peserta baru tahu akan lanjut ke bidang apa.

**Pembidangan sangat mengikuti jurusan yang dibuka di program_rekrutmen itu.** Angkatan yang membuka
jurusan-jurusan teknik akan dibagi ke bidang-bidang teknis; angkatan non-teknik dibagi ke
bidang non-teknis (mis. Niaga). Jadi distribusi bidang hasil pembidangan bukan acak — ia
turunan dari komposisi jurusan yang dibuka.

→ aturan generate data untuk section PENEMPATAN.

### Cocok dengan `tahap_ref.csv` v1

Daftar tahap v1 cocok dengan alur di atas: `administrasi`, `adaptif`,
`akademik_inggris`, `psikologi`, `fisik_mcu`, `wawancara` (kategori seleksi), lalu
`pengumuman_akhir`, `ttd_kontrak`, `samapta`, `pembidangan`, `ojt`, `ujian_ojt`,
`sk_penempatan` (kategori pasca). Jalur RBB di v1 juga masuk lewat `fhci_administrasi`,
`fhci_tes_online_1` (TKD, AKHLAK, TWK), `fhci_tes_online_2` (Inggris, Learning Agility)
yang bertanda agregat.

**Beda penamaan yang belum tuntas:** v1 menyebut tahap ketiga "Tes Akademik (TKB) &
Bahasa Inggris" (TKB = Tes Kompetensi Bidang), user menyebutnya "TPA & Bahasa Inggris"
(TPA = Tes Potensi Akademik). Dua hal berbeda. Perlu dipastikan yang mana.

### Batas antar section

Tahapan berlanjut melewati titik seseorang jadi pegawai (TTD SK). Tahap sesudahnya —
samapta, pembidangan, OJT, ujian OJT, SK penempatan — bukan seleksi lagi, tapi onboarding.
Ini yang menentukan di mana batas section PENDAFTARAN berakhir dan PENEMPATAN dimulai.

**Pembidangan terjadi setelah TTD SK**, artinya sub bidang seseorang ditetapkan setelah dia
diterima — belum tentu sama dengan sub bidang profesi_rekrutmen yang dilamarnya. Perlu dimodelkan
sebagai kejadian tersendiri, bukan disalin dari profesi_rekrutmen.

## Horison perencanaan (dikonfirmasi 2026-09-07)

Perencanaan tidak hanya tahunan. Ada rencana tahunan **dan** lima tahunan (RJPP, RUPTL),
dan pensiun — terutama yang tepat waktu — bisa dihitung jauh di muka. Jadi satu siklus
perencanaan bisa menghasilkan proyeksi untuk 1-5 tahun ke depan.

Konsekuensi skema, sudah diterapkan:
- `proyeksi_kekosongan` punya **dua** kolom tahun: `tahun_program_id` (kapan diproyeksikan)
  dan `tahun_proyeksi_id` (untuk tahun berapa). Proyeksi 2026 buatan siklus 2022 dan buatan
  siklus 2025 hidup berdampingan, tidak saling menimpa — dan selisihnya bisa diukur
  ("seberapa meleset proyeksi jangka panjang HST?").
- `pagu_rekrutmen` punya `tahun_terisi_id` terpisah dari `tahun_program_id`.

**Ikatan dinas punya asal-usul pagu.** HTD tidak mungkin membuka kelas di universitas tanpa
anggaran, dan anggaran itu turun dari rencana HST. Jejaknya:
`proyeksi_kekosongan` (siklus 2022, proyeksi 2026) → `pagu_rekrutmen` (jalur Ikatan Dinas,
tahun_program 2022, tahun_terisi 2026) → `kelas_ikatan_dinas_pagu` → `kelas_ikatan_dinas`.

## Siapa memutuskan apa (dikonfirmasi 2026-09-06)

| keputusan | pihak | muncul pertama di |
|---|---|---|
| jabatan/posisi apa yang kosong, berapa orang | unit pelaksana | `usulan_kebutuhan` |
| jenjang pendidikan pengisi (SMK atau D3 untuk G1, dst) | tim HST | `pagu_rekrutmen` |
| jalur Mandiri vs RBB | tim HST | `pagu_rekrutmen` |
| program_rekrutmen apa yang dibuka, level pendidikan apa | tim HTD | section PROGRAM |
| jurusan apa yang diterima per profesi_rekrutmen | tim HTD | section PROGRAM |

Unit **tidak pernah** menyebut jenjang pendidikan maupun jurusan. Usulan murni berbasis
posisi kosong.

HTD meramu program_rekrutmen mengikuti komposisi pagu: kalau pagu banyak menuntut SMA/SMK maka dibuka
rekrutmen level itu, kalau banyak D3 atau S1 maka dibuka level itu. Jadi **komposisi jenjang
di program_rekrutmen adalah turunan dari komposisi jenjang di pagu**, bukan angka bebas.

→ dipakai section PROGRAM, dan jadi aturan saat generate data.

## Jembatan tunggal: sub bidang

Karena usulan tidak pernah menyebut jurusan dan pengumuman selalu menyebut jurusan,
**satu-satunya penghubung keduanya adalah `sub_bidang`**. Kalau `klasifikasi_jabatan`
(jabatan → sub bidang) atau `pemetaan_jurusan_sub_bidang` (jurusan → sub bidang) salah isi,
seluruh rantai kebutuhan-ke-bukaan ikut salah — dan salahnya tidak terlihat di mana pun,
karena semua angka tetap konsisten, hanya maknanya keliru.

Konsekuensi: **dua tabel itu tidak boleh digenerate dengan tebakan otomatis.** Keduanya
lapisan penilaian, bukan salinan fakta, dan isinya harus di-review user.

## Profesi, dan daftar jurusan yang dibuka

**KOREKSI 2026-09-07 — yang dilihat pelamar adalah PROGRAM STUDI, bukan profesi_rekrutmen.**

Catatan sebelumnya di sini menulis "kandidat mendaftar ke profesi_rekrutmen". Itu keliru, dan
dikoreksi langsung oleh user:

> "yang dilihat oleh peserta itu program_rekrutmen studi yg dibuka. memang, kalau dari sisi
> penyelenggara, misal diistilahkan kita buka 7 profesi_rekrutmen dengan kuota xx, maka yang dilihat
> oleh peserta itu bukan profesinya tapi prodi apa aja yg bisa daftar. nanti kan keputusan
> si peserta bakal masuk profesi_rekrutmen mana itu keputusan dari htd berdasarkan hasil2 tes,
> wawancara, pembidangan, dan ojtnya."

Jadi ada dua sisi yang tidak boleh dicampur:

| sisi | melihat apa |
|---|---|
| penyelenggara (HST/HTD) | profesi_rekrutmen + kuota tiap profesi_rekrutmen |
| pelamar | daftar program_rekrutmen studi yang boleh mendaftar |

Profesi seseorang **bukan pilihan saat mendaftar**, melainkan hasil keputusan HTD di
belakang, berdasarkan nilai tes, wawancara, pembidangan, dan OJT.

Konsekuensi skema: `pendaftaran` menunjuk **program_rekrutmen**, bukan `bukaan_profesi`. Prodi yang
dipakai melamar sudah terkandung di ijazah yang dipilih (`kandidat_pendidikan_id`). Daftar
prodi yang diumumkan adalah turunan: DISTINCT prodi dari seluruh `bukaan_profesi` program_rekrutmen
itu. Penetapan profesi_rekrutmen jatuh ke section PENEMPATAN.

Ini juga membuat keluhan BPO makin bisa diukur: kuota per profesi_rekrutmen direncanakan di depan,
sementara profesi_rekrutmen yang benar-benar terisi baru ketahuan di ujung — selisihnya kelihatan.

Yang tetap benar dari catatan lama: profesi_rekrutmen adalah gabungan pagu banyak unit yang sub bidang
dan jenjang pendidikannya sama, dan kandidat tidak pernah mendaftar ke unit.

**Daftar jurusan yang diterima seragam se-Indonesia untuk satu profesi_rekrutmen** (dikonfirmasi
2026-09-06). Tidak ada kasus UP3 A menerima D3 Teknik Elektro sementara UP3 B tidak.
Karena itu daftar jurusan menempel ke profesi_rekrutmen di section PROGRAM, bukan ke baris pagu.

Rantai dari kebutuhan ke jurusan:

```
pagu (jabatan) → klasifikasi_jabatan (sub_bidang) → pemetaan_jurusan_sub_bidang → jurusan
```

Jabatan tidak pernah menunjuk jurusan langsung; **sub bidang** yang menjembatani permintaan
(jabatan) dan pasokan (lulusan). Itu sebabnya `pemetaan_jurusan_sub_bidang` dan
`klasifikasi_jabatan` wajib memakai kosakata `sub_bidang` yang sama.

→ dipakai section PROGRAM.

## Pagu bersifat tahunan

Tidak ada revisi pagu tengah tahun. Tidak perlu kolom `versi` atau tabel riwayat revisi.

→ sudah dipakai section PERENCANAAN.

## Data akun kandidat (dikonfirmasi 2026-09-07)

Daftar kolom biodata kandidat berasal dari hasil crawl halaman akun rekrutmen.pln.co.id,
bukan tebakan: kandidat_id, nama_lengkap, email, no_ktp, no_handphone, tempat_lahir,
tanggal_lahir, jenis_kelamin, agama, status_perkawinan, alamat_domisili, kota_domisili,
propinsi_domisili, kode_pos_domisili, alamat_asal, kota_asal, propinsi_asal, ukuran_baju,
ukuran_celana, ukuran_sepatu, body_height, body_weight, bmi, visus_kiri, visus_kanan,
tingkat_ketajaman, silinder, abdominal_circumference, tatto, is_buta_warna.

Keputusan lain di putaran ini:

- **Tidak ada jalur/kuota disabilitas** di mockdbv3. Tidak dibuat kolomnya sama sekali.
- **Pengalaman kerja dimodelkan sungguhan** (perusahaan, jabatan, lama), karena jalur Pro
  Hire perlu dinilai kelayakannya. Akibatnya `syarat_pelamar` bertambah kolom
  `pengalaman_minimal_bulan`.
- **Sertifikasi dicatat tapi tidak menentukan lolos/gugur.** Gunanya untuk dashboard
  kapabilitas individu. Aturan generate tidak boleh membuat pemegang sertifikat lebih
  mungkin lolos.
- **Pelamar yang pernah jadi pegawai PLN ada, tapi tidak lebih dari 50 kasus dalam 10
  tahun.** Dimodelkan lewat FK `pegawai.kandidat_id` di section PENEMPATAN, tanpa kolom
  penanda apa pun di `kandidat`. Bentuk kasusnya: masuk lewat SMA lalu melamar bukaan
  S1/S2/Pro Hire, atau masuk lewat S1 lalu melamar S2/Pro Hire. Logikanya perlu cek ricek
  ketat — mustahil orang masuk lewat SMA lalu 20 tahun kemudian melamar S1, karena grade-nya
  sebagai pegawai sudah melewati grade masuk S1 dan usianya sudah lewat batas. Lima aturan
  lengkapnya ditulis di `04_kandidat.md`.
- **Alamat**: `kandidat_alamat` menyimpan nilai terkini. Saat kandidat akan mendaftar, UI
  memintanya memperbarui data diri; hasilnya menimpa data akun **dan** disalin ke baris
  pendaftaran sebagai data peserta.
- **`jenis` di `kandidat_alamat` kolom teks biasa**, bukan FK lookup — nilainya hanya
  "Domisili" dan "Asal".
- **`silinder` cukup satu nilai** untuk mockdbv3, tidak dipecah kiri/kanan.

## Jalur RBB: akun kandidat adalah limpahan dari sistem BUMN (dikonfirmasi 2026-09-07)

Dari sisi pendaftar:

```
lihat iklan bukaan RBB (bisa di akun PLN, Pertamina, Mandiri, BUMN mana pun)
  → daftar di SISTEM BUMN, bukan di sistem PLN
  → tes administrasi & adaptif di sistem BUMN
  → yang lolos diteruskan ke perusahaan tujuan masing-masing
  → sistem rekrutmen PLN melanjutkan: akademik & inggris → psikologi → MCU → dst
```

Dari sisi PLN, kontribusinya di ujung awal hanya dua: menyediakan kuota (posisi apa yang
dibuka, butuh berapa), lalu **menunggu** sistem BUMN menyampaikan siapa saja yang lolos
tahap mereka.

Konsekuensi desain:

- Baris `kandidat` jalur RBB lahir dari **limpahan data**, bukan dari orang membuat akun di
  PLN. Tanggal barisnya adalah tanggal serah terima.
- Profil kandidat RBB bisa lebih tipis dari pelamar Mandiri — isinya tergantung apa yang
  dikirim sistem BUMN. `kandidat_data_fisik` dan `kandidat_sertifikasi` wajar kosong.
- Memperkuat catatan yang sudah ada: kandidat RBB tidak punya baris tahap administrasi dan
  adaptif sama sekali.
- **Kolom nomor peserta sistem BUMN wajib ada di `pendaftaran`** (dikonfirmasi 2026-09-07),
  NULL untuk jalur selain RBB. Satu-satunya cara merujuk kandidat RBB balik ke sumbernya.

## Pro Hire (dikonfirmasi 2026-09-07)

- Pengalaman kerja **dicek saat seleksi administrasi**, jadi penentu gugur/lolos di tahap
  pertama — sederajat dengan syarat usia dan IPK.
- Pro Hire selalu untuk **grade tinggi**; orangnya disiapkan menjabat dalam sekitar satu
  tahun setelah jadi pegawai, jadi grade masuknya di kisaran S2 ke atas apa pun ijazahnya.
- Karena itu `aturan_grade_masuk` di PERENCANAAN ditambah `jalur_rekrutmen_id` dan
  `pengalaman_minimal_bulan` — aturan pendidikan→grade tidak boleh dipakai untuk Pro Hire.

## Pasca-seleksi & penempatan (dikonfirmasi 2026-09-07)

- **TTD kontrak terjadi setelah lulus wawancara, sebelum samapta.** Sejak saat itu orangnya
  sudah pegawai dan punya NIP, jauh sebelum SK penempatan terbit. Seluruh tahap samapta
  sampai OJT dijalani dalam status pegawai.
- **Pembidangan menetapkan sub bidang, bukan profesi_rekrutmen.** Beberapa profesi_rekrutmen bisa berbagi satu
  bidang — Analyst Keuangan dan Officer Akuntansi sama-sama masuk pembidangan KEUANGAN.
  Profesi baru ditetapkan di SK penempatan.
- **Ujian OJT boleh diulang sampai tiga kali**, berjarak sekitar tiga bulan. Contoh: ujian
  Juli, keputusan Agustus, yang belum lulus ikut lagi September dan tetap menjalani OJT di
  sela itu. Karena itu jarang ada yang benar-benar gagal. Diterapkan lewat kolom
  `kesempatan_ke` di `pendaftaran_tahap` (kunci uniknya ikut berubah).
- **Tidak ada penempatan ke jabatan struktural** untuk mockdbv3. Populasi wajib memfilter
  `posisi` lewat `kelompok_jabatan.is_struktural = false`.
- **Benang merah data adalah nomor pendaftaran.** Alur yang diminta user:
  akun kandidat → mendaftar program_rekrutmen → dapat nomor pendaftaran → nomor itu jadi FK di tiap
  tahap seleksi dan pasca-seleksi → lulus ujian OJT → SK penempatan → NIP. Karena itu
  `pembidangan`, `penempatan_ojt`, dan `sk_penempatan` menunjuk **`pendaftaran_tahap_id`**
  (diputuskan 2026-09-07 setelah membandingkan dua opsi berdampingan): satu lompatan lebih
  panjang, ditukar dengan tanggal yang tidak terduplikasi dan mustahilnya baris keputusan
  untuk orang yang tidak pernah menjalani tahapnya. Pola ini sama dengan `pendaftaran_nilai`
  dan `pemeriksaan_kesehatan`, jadi seluruh skema konsisten.

## Calon pegawai vs pegawai (dikoreksi 2026-09-07)

TTD kontrak TIDAK langsung menjadikan orang pegawai. Setelah TTD kontrak statusnya **calon
pegawai**, karena masih ada sisa tahapan pasca-seleksi: samapta, pembidangan, OJT, ujian OJT.
Pengangkatan jadi pegawai terjadi di SK penempatan.

Diterapkan di tabel `pegawai`: dua tanggal (`tanggal_mulai_calon` = TTD kontrak,
`tanggal_diangkat` = SK penempatan), tanpa kolom status — statusnya turunan dari kedua
tanggal itu plus `tanggal_berhenti`.

- **Jarak mulai OJT ke ujian OJT pertama: 3-4 bulan** untuk mockdbv3.
- **SK peserta yang gagal ujian OJT pertama memang terbit belakangan**; selama itu dia masih
  calon pegawai.
- **NIP terbit saat TTD kontrak, sebelum samapta** (dikonfirmasi 2026-09-07). Jadi calon
  pegawai sudah punya NIP sejak hari pertama, dan `pegawai.nomor_pegawai` NOT NULL.

## Kedalaman unit untuk mockdbv3 (dikonfirmasi 2026-09-07)

`unit` hanya dua lapis: **level 1 (unit induk / divisi / unit pusat)** dan **level 2 (unit
pelaksana / bidang)**. ULP dan Unit Layanan ada di kenyataan — Sample-05 bahkan memproyeksikan
penempatan OJT sampai UI/UP/UL — tapi **tidak dimodelkan di mockdbv3**. Seluruh tahap dan
seluruh proses berhenti di level 2, unit pelaksana.

## Tiga nomor yang berbeda (dikonfirmasi 2026-09-07)

| nomor | tabel | terbit kapan |
|---|---|---|
| id/nomor akun web rekrutmen | `kandidat` | saat membuat akun |
| nomor pendaftaran, disebut HTD "NO TES" | `pendaftaran` | setelah mendaftar ke satu program |
| NIP | `pegawai` | saat TTD kontrak |

Contoh format nomor tes dari berkas HTD: `2511/ES/92/D3-ELE/135615` — mengandung angkatan (92)
dan jurusan (D3-ELE).

## Singkatan SH/AP dalam nama tabel (diputuskan 2026-09-07)

**SH/AP = SubHolding dan Anak Perusahaan.** Dua tabel yang dulu berakhiran `_shap` diganti
jadi `_perusahaan`: `pagu_rekrutmen_perusahaan` dan `bukaan_profesi_pagu_perusahaan`.
Alasannya "shap" singkatan internal yang tidak bisa ditebak dari luar, termasuk oleh chatbot
yang membaca skema. Kata "perusahaan" dipilih karena baris-barisnya memang menunjuk
`perusahaan.id` berkategori SubHolding atau Anak Perusahaan.
