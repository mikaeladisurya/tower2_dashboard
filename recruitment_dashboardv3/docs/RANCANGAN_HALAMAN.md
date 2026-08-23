# Rancangan halaman — Dashboard Rekrutmen PLN v3

Usulan susunan halaman, dirancang dari [KONTEKS_KERJA.md](KONTEKS_KERJA.md) — dari **pekerjaan
tim rekrutmen**, bukan dari bentuk tabel database.

Status: **disetujui pemilik.** Susunan tujuh halaman dan jangkar waktu `date()` sudah
diputuskan; halaman boleh dibangun mulai G10.

Setiap angka di dokumen ini sudah dijalankan terhadap `rekrutmen.duckdb`. Tidak ada yang
diperkirakan.

> Revisi 3 — memuat koreksi pemilik: dashboard bersifat **realtime** dengan jangkar
> **`date()` sungguhan + pemilih tanggal** · halaman **Seleksi Berjalan** tetap dibuat ·
> halaman **Pasca-Seleksi** berdiri sendiri · semua fitur tanpa data dikumpulkan jadi **satu
> halaman bersection**. Perbaikan generator mockdb dicatat terpisah untuk v4.

---

## 1. Prinsip pertama: ini dashboard realtime

**Tanggal potong 2026-09-15 hanya simbolik** — penanda bahwa data mock berhenti di situ. Ia
**bukan** tanggal tampil dashboard.

Orang akan membuka dashboard ini pada 16 September, 6 Januari 2027, atau kapan pun. Halaman
yang menjawab *"berhenti di tanggal potong 15 Sep 2026"* adalah halaman yang gagal — kalau
begitu, buat apa dashboardnya.

### Konsekuensi arsitektur yang mengikat semua halaman

**Kolom `status` di `pasca_tahap` adalah snapshot beku** saat data digenerate. Dibaca apa
adanya, dashboard akan menyatakan "2.000 sedang OJT" selamanya. Sudah diuji:

| Dibuka tanggal | Dihitung dari tanggal | Kolom `status` dibaca mentah |
|---|---|---|
| 2026-08-22 | berjalan 2.000 · selesai 5.711 | 2.000 |
| 2026-09-15 | berjalan 2.000 · selesai 5.711 | 2.000 |
| 2026-10-05 | berjalan **1.021** · selesai 6.690 | 2.000 ❌ |
| 2026-10-20 | berjalan **0** · selesai 7.711 | 2.000 ❌ |
| 2027-01-06 | berjalan **0** · selesai 7.711 | 2.000 ❌ |

**Aturan:** status apa pun — sedang berjalan, sudah selesai, belum mulai — **dihitung dari
perbandingan tanggal terhadap hari ini**, tidak pernah dibaca dari kolom status. Berlaku untuk
`pasca_tahap`, `gelombang` (buka/tutup), dan `seleksi_tahap`.

`core/db.py` (G5) menyediakan `hari_ini()`, dan itulah jangkar semua hitungan "terkini".

### KEPUTUSAN PEMILIK — jangkar waktu adalah `date()` sungguhan

**Jangkar = tanggal berjalan sungguhan**, bukan `TANGGAL_POTONG`. Ditambah **pemilih "lihat
per tanggal"** yang defaultnya hari ini, supaya dashboard tetap bisa didemokan pada titik mana
pun sepanjang umur data.

`core/db.py` (G5) menyediakan `hari_ini()` yang mengembalikan tanggal berjalan, dapat
di-override oleh pemilih tanggal di `session_state`. Seluruh halaman membaca dari situ —
**tidak ada halaman yang memanggil `date.today()` sendiri**, supaya pemilih tanggal berlaku
seragam.

`TANGGAL_POTONG` turun pangkat jadi penanda **horison data** di `CATATAN_DATA.md`, bukan
patokan tampilan.

**Apa yang berubah dibanding jangkar beku:**

| | Jangkar beku | `date()` sungguhan |
|---|---|---|
| 2026-08-22 | 2.000 OJT, "16 hari lagi" (salah) | 2.000 OJT, **40 hari lagi** |
| Gelombang terakhir tutup | selalu "345 hari lalu" | **321 hari lalu**, bertambah tiap hari |
| 2026-10-16 | tetap "2.000 sedang OJT" ❌ | 0 OJT, 7.711 selesai ✅ |
| 2027-01-06 | tetap "2.000 sedang OJT" ❌ | 0 OJT, halaman live kosong (jujur) |

**Konsekuensi yang diterima sadar:** horison data berakhir **2026-10-15**. Sesudah itu Beranda
dan Seleksi Berjalan permanen kosong, dan 2.000 orang menggantung tanpa SK (lihat J9, J10).
Perbaikan generator dicatat di [USULAN_DATABASE.md](USULAN_DATABASE.md) bagian A untuk
dikerjakan di sesi terpisah dan dipakai **dashboard v4**. **Bukan lingkup v3.**

**Tidak boleh ada angka hari yang di-hardcode** di kode maupun dokumen — semuanya dihitung
terhadap `hari_ini()`.

### Penyesuaian P3 yang perlu disahkan di G4

P3 berbunyi *"Terkini = relatif `TANGGAL_POTONG`"*. Maksud aslinya tetap berlaku: **jangan
pernah memakai `max(tanggal)` sebagai pengganti hari ini.** Yang berubah hanya jangkarnya —
**hari ini yang sesungguhnya**, bukan konstanta beku.

### Setiap halaman wajib punya keadaan kosong yang bermartabat

Karena waktu berjalan, tiap halaman akan mengalami saat datanya nihil. Keadaan kosong
ditampilkan sebagai **fakta keadaan**, bukan pesan galat dan bukan penjelasan developer (P2).

- Salah: *"Tidak ada data — gelombang terakhir tutup 345 hari lalu"*
- Benar: *"Tidak ada gelombang yang sedang dibuka"* + arahkan ke gelombang terakhir yang selesai

---

## 2. Tujuh halaman berdata nyata + satu halaman usulan

| # | Halaman | Pertanyaan yang dijawab | Goal |
|---|---|---|---|
| 1 | **Beranda** | Apa yang perlu perhatian hari ini? | G10 |
| 2 | **Perencanaan Formasi** | Berapa yang akan kosong, di mana, jabatan apa? | G11 |
| 3 | **Seleksi Berjalan** | Gelombang yang jalan sekarang sampai mana? | G12 |
| 4 | **Corong Seleksi** | Di tahap mana orang hilang, dan kenapa? | G13 |
| 5 | **Pasca-Seleksi** | Yang sudah lulus, sekarang di mana prosesnya? | G14 |
| 6 | **Rencana & Realisasi** | Seberapa tepat perencanaan kami ternyata? | G15 |
| 7 | **Profil Pelamar** | Siapa yang melamar? | G16 |
| — | **Eksplorasi** | Semua yang datanya belum ada | G17 |
| — | **RecruitMan** | Tanya-jawab bebas | G8 |

Tujuh halaman, naik dari lima di revisi 1. Penomoran goal digeser: Eksplorasi jadi **G17**,
konsolidasi jadi **G18**.

---

## 3. Halaman 1 · Beranda

**Pertanyaan harian:** *Apa yang perlu perhatianku hari ini?*

Halaman ini **menghitung ulang seluruh isinya terhadap hari ini**. Isinya berubah sendiri
seiring tanggal maju — itu inti rancangannya, bukan tambahan.

**Blok isi:**

1. **Kartu keadaan sekarang** — masing-masing dihitung terhadap hari ini:
   gelombang sedang dibuka · kandidat sedang diseleksi · peserta sedang OJT ·
   menunggu SK. Nilai 0 ditampilkan apa adanya sebagai fakta.
2. **Tenggat terdekat** — kohort/tahap apa pun yang selesai dalam 30 hari ke depan, dengan
   hitungan hari tersisa. Ini yang berubah tiap hari.
3. **Denyut pipeline** — berapa orang di tiap tahap saat ini, dari pendaftaran sampai SK,
   seluruhnya diturunkan dari tanggal.
4. **Aktivitas terakhir** — kalau tidak ada yang berjalan, tunjukkan peristiwa terakhir yang
   selesai dan yang dijadwalkan berikutnya. Halaman tidak pernah kosong melompong.

**Contoh keadaan saat dokumen ini ditulis (22 Agustus 2026)** — akan berbeda tiap hari, dan
memang itu maksudnya: 979 orang selesai OJT dalam 40 hari · 1.021 orang dalam 54 hari · 2.000
sedang OJT · **0 menunggu SK** · **0 dari 2.000 sudah ditetapkan unit penempatannya** ·
0 gelombang terbuka.

> Dikoreksi di G6 setelah metriknya dijalankan. Revisi 3 sempat menulis “2.000 menunggu SK”,
> memakai bacaan longgar `status_sk = 'BELUM'`. Yang benar **0**: pada 22 Agustus 2026 kedua
> kohort masih **di dalam** OJT, jadi belum menunggu apa pun — mereka sudah terhitung di kartu
> “sedang OJT”. Menghitung mereka dua kali akan melipatgandakan orang yang sama di satu layar.
> Angka itu naik jadi 979 pada 2026-10-05 dan 2.000 pada 2027-01-06, seiring OJT selesai.

**Metrik dibutuhkan:** hitungan pipeline per tahap terhadap hari ini · tenggat N hari ke depan ·
peristiwa terakhir & berikutnya.

---

## 4. Halaman 2 · Perencanaan Formasi

**Pertanyaan harian:** *Berapa yang akan kosong, di mana, jabatan apa?* — pertanyaan HST.

Rantai perencanaan yang ada di data:

```
proyeksi kekosongan  →  usulan unit  →  pagu disetujui
 (per unit × posisi)    (kekosongan +     (2019–2025)
    2019–2026            gap FTK)
```

2025: 906 kekosongan + 333 gap FTK = **1.238 usulan** → pagu **1.050**.
2026: **919 kekosongan**, **780 karena pensiun (85%)**.

**Blok isi:**

1. **Kekosongan tahun berjalan & berikutnya per sebab** — pensiun mendominasi, dan pensiun
   bisa diprediksi jauh di muka. Tahun yang ditampilkan **mengikuti hari ini**, bukan
   di-hardcode 2026.
2. **Kekosongan per unit induk** — 48 unit, mana yang paling terancam.
3. **Kekosongan per posisi & sub-bidang** — `posisi_unit_induk` punya 11.781 baris, granular.
4. **Gap FTK per unit** — nasional 561 setelah filter anomali J4 (`jumlah_pegawai > 50`);
   701 adalah seluruh 48 baris apa adanya, termasuk baris duplikat J4 (lihat
   `CATATAN_DATA.md` J8). Wajib `realisasi_mar_2026`; `apr_2026` menghasilkan 33.934 yang
   palsu karena hanya 1 dari 48 unit terisi.
5. **Usulan vs pagu per tahun** — berapa diminta unit, berapa disetujui pusat.

**Batas jujur:** `proyeksi_kekosongan` berhenti di **2026**. Begitu hari ini melewati 2026,
halaman ini kehabisan tahun ke depan — dan harus mengatakannya sebagai keadaan data, lalu
menawarkan tahun historis. Proyeksi 2027+ masuk Eksplorasi.

**Metrik dibutuhkan:** proyeksi kekosongan per tahun/unit/posisi/sebab · gap FTK (filter
`jumlah_pegawai > 50`) · usulan vs pagu per tahun.

---

## 5. Halaman 3 · Seleksi Berjalan

**Pertanyaan harian:** *Gelombang yang sedang jalan sudah sampai mana?*

Halaman ini **kosong pada tanggal potong** — dan itu benar, karena memang tidak ada gelombang
terbuka. Tapi halaman ini tetap dibuat: begitu ada gelombang berjalan, dashboard langsung
berfungsi tanpa perlu dibangun ulang. Inilah halaman yang paling diminta pemilik proses, yang
sampai sekarang **belum pernah ada** — *"saat ini belum ada mas kalau dashboard"*.

**Blok isi:**

1. **Gelombang yang sedang terbuka** — `tgl_buka <= hari ini <= tgl_tutup`. Nama, profesi yang
   dibuka, kota, hari tersisa sampai tutup.
2. **Posisi peserta per tahap sekarang** — berapa orang menunggu di tiap tahap, berapa sudah
   lewat. Diturunkan dari `seleksi_tahap.tanggal_tahap` terhadap hari ini.
3. **Jadwal tahap berikutnya** — tahap apa, tanggal berapa, di kota mana, vendor siapa.
4. **Kehadiran tahap terakhir** — hadir vs tidak hadir untuk tahap yang baru saja lewat.
   Sinyal paling dini bahwa ada yang tidak beres.
5. **Keadaan kosong** — kalau tidak ada gelombang terbuka: sebutkan itu apa adanya, tampilkan
   gelombang terakhir yang selesai beserta hasil akhirnya.

**Metrik dibutuhkan:** gelombang aktif terhadap hari ini · posisi peserta per tahap · jadwal
tahap mendatang · kehadiran tahap terakhir.

---

## 6. Halaman 4 · Corong Seleksi

**Pertanyaan harian:** *Di tahap mana orang hilang, dan kenapa?* — analisis bottleneck yang
diminta nota dinas.

Berbeda dari Halaman 3: yang ini **analisis lintas gelombang**, bukan pemantauan yang sedang
jalan.

**Corong jalur mandiri, sudah dijalankan:**

| # | Tahap | Masuk | Hadir | Lulus | Tidak hadir |
|---|---|---|---|---|---|
| 1 | Seleksi Administrasi | 213.648 | — | 143.831 | — |
| 2 | Tes Adaptif (TAP) | 143.831 | 68.896 | 48.627 | **74.935** |
| 3 | Akademik & Inggris | 53.907 | 44.358 | 24.699 | 9.549 |
| 4 | Psikologi | 24.699 | 22.651 | 15.980 | 2.048 |
| 5 | Fisik & MCU | 15.980 | 14.826 | 12.623 | 1.154 |
| 6 | Wawancara | 12.623 | 11.859 | **7.711** | 764 |

**Temuan pokok:** kehilangan terbesar bukan karena gagal tes. Di Tes Adaptif **74.935 orang
tidak hadir sama sekali**. Sebabnya bukan jarak, melainkan mode tes:

| Tahap | Mode | Tidak hadir |
|---|---|---|
| Tes Adaptif | online | **52,1%** |
| Akademik & Inggris | online | 17,7% |
| Psikologi | offline | 8,3% |
| Fisik & MCU | offline | 7,2% |
| Wawancara | offline | 6,1% |

Kolom `mode` berpola benar, jadi temuan ini kokoh meski `kota_domisili` cacat.

**Blok isi:**

1. **Corong enam tahap** — bentuk corong/Sankey baku (P4), memisahkan *gugur karena gagal* dari
   *gugur karena tidak hadir*.
2. **No-show per tahap × mode** — inti temuannya.
3. **Titik serah-terima RBB** — tahap 3 kemasukan 53.907 padahal tahap 2 meluluskan 48.627.
   Selisih 5.280 adalah jalur RBB yang masuk di sini; corong harus menggambarkan **aliran**.
4. **Corong FHCI terpisah** — 3 tahap agregat tanpa identitas, ditampilkan sebagai fakta
   struktural.
5. **Pembanding antar gelombang** — corong gelombang mana pun bisa disandingkan.

**Batas jujur:** tidak ada skor tes — `tahap_ref.skor_ada_di_sistem_asli` tidak pernah `True`.
Passing grade dan analisis prediktif masuk Eksplorasi.

**Metrik dibutuhkan:** corong per tahap · no-show per tahap × mode · gugur per tahap · corong
agregat FHCI · corong per gelombang.

---

## 7. Halaman 5 · Pasca-Seleksi

**Pertanyaan harian:** *Yang sudah lulus, sekarang prosesnya di mana?*

Ini yang **belum ada di v2**, dan datanya ternyata jauh lebih kaya dari dugaan awal. Tiap tahap
punya jendela pelaksanaan nyata per kohort — bukan peristiwa titik.

**Lini masa kohort 2025, sudah dijalankan:**

| Tahap | Angkatan 91 (979 orang) | Angkatan 92 (1.021 orang) | Rentang |
|---|---|---|---|
| Pengumuman akhir | 2026-02-13 | 2026-02-27 | 0 hari |
| Ttd kontrak | 2026-02-23 → 03-08 | 2026-03-09 → 03-22 | **13 hari** |
| SAMAPTA | 2026-03-15 → 03-29 | 2026-03-29 → 04-12 | **14 hari** |
| Pembidangan | 2026-03-30 | 2026-04-13 | 0 hari |
| OJT | 2026-04-04 → 10-01 | 2026-04-18 → 10-15 | **180 hari** |
| Ujian OJT | belum | belum | 10 hari |
| SK penempatan | belum | belum | 0 hari |

**Blok isi — persis pertanyaan yang kamu ajukan:**

1. **Lini masa tujuh tahap per kohort** — kapan mulai, kapan selesai, berapa peserta, **posisi
   hari ini di mana** (penanda bergerak seiring tanggal).
2. **SAMAPTA** — berapa peserta, jendela pelaksanaan, berapa lama.
3. **Pembidangan** — sebaran 9 bidang. Kohort 2025: Pembangkitan 481 · SDM 362 · Distribusi 258 ·
   Transmisi & GI 215 · Konstruksi 197 · Keuangan 169 · Niaga 165 · Perencanaan Sistem 91 ·
   Proteksi & Kontrol 62.
4. **OJT per UPDL** — 11 UPDL. Kohort 2025: Semarang 257 · Pandaan 234 · Surabaya 228 ·
   Tuntungan 201 · Palembang 195 · Padang 162 · Makassar 158 · Jakarta 152 · Bogor 141 ·
   Suralaya 136 · Banjarbaru 136. Berguna untuk pertanyaan kapasitas diklat.
5. **SK penempatan** — berapa sudah terbit, berapa menunggu, unit tujuan mana saja.

**Batas jujur yang harus tampak di halaman:**
- **Lokasi SAMAPTA tidak ada di data.** `pasca_tahap` tidak punya kolom lokasi; `updl_id` ada
  di `penempatan`, satu per orang, dan itu lokasi diklat — bukan lokasi SAMAPTA.
- **Unit penempatan kohort 2025 masih kosong seluruhnya** (2.000 baris). Memang belum
  diputuskan; itu keadaan nyata, bukan data hilang.
- Rentang tiap tahap **konstan lintas kohort** (13/14/180/10 hari), jadi perbandingan durasi
  antar kohort tidak bermakna. Lini masa **posisi** tetap bermakna.
- **2.000 orang kohort 2025 berhenti di OJT dan tidak pernah bergerak lagi** (J9). Di
  `denyut_pipeline` mereka muncul sebagai `sudah_tuntas` di tahap OJT — label yang harfiahnya
  berarti “beres, tinggal tahap berikutnya”, padahal `ujian_ojt` dan `sk_penempatan` untuk
  kohort ini **tidak punya baris sama sekali**. Menampilkan `sudah_tuntas` sendirian akan
  menenangkan pembaca atas orang-orang yang justru macet. Halaman ini wajib menyandingkannya
  dengan jumlah di `ujian_ojt`/`sk_penempatan` supaya selisih 2.000 yang menggantung terlihat.
  Ditemukan saat audit G6; **jangan ditambal di SQL**, tampilkan apa adanya.

**Metrik dibutuhkan:** lini masa tahap per kohort dengan posisi hari ini · peserta & jendela per
tahap · pembidangan per kohort · sebaran UPDL · status SK.

---

## 8. Halaman 6 · Rencana & Realisasi

**Pertanyaan harian:** *Seberapa tepat perencanaan kami ternyata?* — kutipan langsung dari
notulen.

**Temuan A — dua angka rencana tidak pernah didamaikan:**

| Tahun | Pagu | Target gelombang | Ditempatkan | Selisih pagu↔target |
|---|---|---|---|---|
| 2019 | 1.093 | 1.353 | 1.353 | +260 |
| 2020 | 325 | 325 | 125 | 0 |
| 2021 | 689 | 689 | 49 | 0 |
| 2022 | 689 | 1.109 | 1.109 | +420 |
| 2023 | 1.277 | 1.797 | 1.797 | +520 |
| 2024 | 1.098 | 1.578 | 1.278 | +480 |
| 2025 | 1.050 | 2.000 | 2.000 | **+950** |

Realisasi konsisten mengikuti **target gelombang**, bukan pagu. Artinya pagu bukan yang
mengikat — temuan yang layak ditampilkan, bukan cacat yang disembunyikan.

**Temuan B — alignment rencana vs penempatan.** `usulan_kebutuhan` menyimpan unit yang
direncanakan, `penempatan` menyimpan unit yang terisi. Bisa dibandingkan untuk **2019–2024**.

**Blok isi:**

1. **Tiga angka per tahun** — pagu, target gelombang, realisasi, berdampingan.
2. **Rencana vs realisasi per unit induk** — unit mana yang kebagian sesuai rencana.
3. **Pemenuhan per tahun**, dengan tahun RBB (2020, 2021, 2024) **diberi penanda dan
   dikeluarkan dari rata-rata** — yang tercatat cuma sisa setelah saringan FHCI; menyebutnya
   "gagal 7,1%" adalah salah baca.

**Batas jujur:** kohort yang belum ditempatkan (saat ini 2025) otomatis di luar analisis
alignment, dan halaman menyebutkan alasannya sebagai keadaan proses.

**Metrik dibutuhkan:** pagu/target/realisasi per tahun · rencana vs realisasi per unit ·
pemenuhan per tahun dengan penanda jalur.

---

## 9. Halaman 7 · Profil Pelamar

**Pertanyaan harian:** *Siapa yang melamar, dan cocok tidak dengan yang dibutuhkan?*

**Blok isi:**

1. **Piramida umur × jenis kelamin** — konvensi piramida penduduk (P4), **per tahun umur, bukan
   dikelompokkan lima tahunan** (P5). Umur dihitung saat **melamar**, bukan saat hari ini.
   Kode gender **P = Pria, W = Wanita** — salah baca membalik seluruh grafik.
2. **Jenjang pendidikan** — wajib filter `pendidikan_terakhir`, tanpa itu tiap kandidat
   menyumbang ±4 baris riwayat sekolah.
3. **Rumpun jurusan: melamar vs diterima** — konversi per rumpun.
4. **Sebaran provinsi domisili** — kolom ini berpola benar (rasio 16,4).
5. **Volume tes per kota** — 43 kota, rasio 37,7×, berpola benar.
6. **Kelengkapan akun per kohort** — membaik tiap tahun; kurva kematangan sistem.

**Batas jujur — kolom yang dilarang dipakai:** `kota_domisili`, `kota_asal`, `tempat_lahir`,
`ukuran_baju`, `sekolah_universitas` semuanya acak seragam. **Tidak ada analisis almamater,
tidak ada peta asal-vs-tes.** Kolom PII tidak pernah tampil.

**Metrik dibutuhkan:** umur × gender saat melamar · jenjang · konversi rumpun jurusan ·
provinsi · volume tes per kota · kelengkapan akun per kohort.

---

## 10. Halaman Eksplorasi — satu halaman, banyak section

Satu halaman, jelas ditandai terpisah dari halaman berdata nyata, berisi **semua fitur yang
datanya belum ada di database**, dibagi per section. Dibangun penuh dengan data sintetis supaya
bentuknya bisa dinilai. Tiap section otomatis jadi satu baris di `docs/USULAN_DATABASE.md`,
sebagai bahan keputusan v4.

**Section yang sudah teridentifikasi:**

| Section | Yang diminta | Kenapa belum bisa |
|---|---|---|
| **Pemenuhan 3T** | *"fulfillment 3T ini menjadi poin yg diperhatikan"* · *"temen2 ojt harusnya ditempatkan di 3T tapi penempatannya kok ngga sesuai?"* | Nol kolom menandai 2T/3T di 35 tabel — sudah dipindai seluruh `information_schema` |
| **Proyeksi kekosongan 2027+** | *"misal untuk perencanaan 1 januari 2027, akan ada kosong berapa banyak, dimana, jabatan apa"* | `proyeksi_kekosongan` berhenti di 2026 |
| **Pencocokan kompetensi** | *"mengacu ke kompetensi jabatan, direktori kompetensi"* | Tidak ada tabel kompetensi |
| **Skor tes & passing grade** | analisis bottleneck berbasis skor | `skor_ada_di_sistem_asli` tidak pernah `True` |
| **APS / rotasi / mutasi / tugas karya per orang** | *"apkah bisa diakomodir data2nya link dengan data aps, rotasi, mutasi"* | Hanya ada agregat kekosongan, tidak ada peristiwa per pegawai |
| **Efektivitas sumber rekrutmen** | *"source mana paling banyak yield"* | Jalur ada (`sumber_rekrutmen`), tapi kualitas hasil tidak terukur |
| **Lokasi SAMAPTA & kapasitas UPDL** | *"dimana samaptanya, berapa lama, berapa peserta"* | Lokasi per tahap tidak ada; kapasitas UPDL tidak ada |
| **Biaya rekrutmen** | cost per hire dari dokumen master | Tidak ada data biaya sama sekali |

Daftar ini akan bertambah saat halaman berdata nyata dibangun dan menemukan batas baru.

---

## 11. Susunan navigasi yang diusulkan

| Urutan | Halaman | Ikon Material | Goal |
|---|---|---|---|
| 1 | Beranda | `:material/home:` | G10 |
| 2 | Perencanaan Formasi | `:material/event_upcoming:` | G11 |
| 3 | Seleksi Berjalan | `:material/pending_actions:` | G12 |
| 4 | Corong Seleksi | `:material/filter_alt:` | G13 |
| 5 | Pasca-Seleksi | `:material/workspace_premium:` | G14 |
| 6 | Rencana & Realisasi | `:material/balance:` | G15 |
| 7 | Profil Pelamar | `:material/groups:` | G16 |
| 8 | Eksplorasi | `:material/science:` | G17 |
| 9 | RecruitMan | `:material/smart_toy:` | G8 |

Judul semuanya **frasa benda** (P1) — tidak ada yang bisa basi kalau datanya berubah. Tanpa
emoji (P10).

**Yang sengaja tidak ada, dibandingkan v2:** tidak ada halaman "Kualitas Data" tersendiri.
Setiap batas data disebutkan **di tempat angkanya muncul**, bukan dikumpulkan di halaman
terpisah yang tak pernah dibuka. Penjelasan panjangnya tetap di `CATATAN_DATA.md`, tidak di UI.

---

## 12. Yang berubah dari hipotesis awal PROMPT_V3 §6

| Hipotesis | Putusan |
|---|---|
| Beranda operasional | **Diterima** → Beranda, dihitung realtime |
| Perencanaan formasi & pagu | **Diterima** → Perencanaan Formasi |
| Pelaksanaan seleksi yang sedang berjalan | **Diterima** → Seleksi Berjalan. Kosong pada tanggal potong, tapi berfungsi begitu ada gelombang jalan. |
| Kandidat | **Diterima** → Profil Pelamar |
| Pasca-seleksi, penempatan & SK | **Diterima, diperluas** → Pasca-Seleksi berdiri sendiri: SAMAPTA, pembidangan, OJT per UPDL, SK. Belum ada di v2. |
| Pertanggungjawaban / pelaporan | **Digabung** ke Rencana & Realisasi |
| — | **Ditambah** Corong Seleksi, memisahkan analisis bottleneck dari pemantauan yang sedang jalan |

Enam hipotesis menjadi tujuh halaman.
