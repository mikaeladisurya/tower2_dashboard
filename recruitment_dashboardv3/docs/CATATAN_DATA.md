# Catatan data

Tempat bermuaranya **semua** penjelasan "kenapa angkanya begini": jebakan data, asumsi
pemodelan, keputusan query, anomali yang diketahui.

**Tidak satu pun isi berkas ini boleh tampil di UI** (P2). Setiap kali tergoda menulis
penjelasan di `help=`, judul, atau caption — tulis di sini.

Semua angka di bawah **dijalankan langsung** terhadap `mockdb/out/rekrutmen.duckdb` saat G1,
bukan disalin dari dokumen.

---

## 0. PERINGATAN PERTAMA — jangan percaya `mockdb/docs/ERD.md` dan `kamus_data.md`

**Kedua dokumen itu tidak menggambarkan database yang benar-benar dibangun.** Keduanya
ditulis 2026-08-19 21:40, sedangkan `rekrutmen.duckdb` dibangun 13:13 hari yang sama —
dokumennya lebih baru dari databasenya dan menjelaskan skema yang tidak pernah jadi.

**Sebelas tabel dijelaskan panjang lebar di dokumen tapi TIDAK ADA di database:**

`perusahaan` · `jabatan` · `posisi_unit` · `pengumuman` · `seleksi_skor` · `tahap_agregat` ·
`kontrak` · `prajabatan` · `pegawai` · `headcount_tahunan` · `peristiwa_pegawai`

**Enam tabel ADA di database tapi nol kali disebut dokumen:**

`pasca_tahap` · `seleksi_tahap_agregat` · `jabatan_katalog` · `kekosongan_ringkas` ·
`minat_profesi` · `profil_usia` (juga `_meta_generator`)

Beberapa hanya berganti nama — `prajabatan`+`kontrak` → `pasca_tahap`, `tahap_agregat` →
`seleksi_tahap_agregat`, `posisi_unit` → `posisi_unit_induk`/`posisi_unit_pelaksana` — tapi
`seleksi_skor`, `peristiwa_pegawai`, dan `pegawai` benar-benar **tidak ada padanannya**.
Jumlah barisnya pun meleset jauh (dokumen menyebut `pendaftaran` ±314.730; sesungguhnya
218.928).

**Yang boleh dipakai dari kedua dokumen itu:** penjelasan *maksud* dan *aturan bisnis*.
**Yang tidak boleh:** nama tabel, nama kolom, jumlah baris, nilai enum.

**`recruitment_dashboardv2/docs/metrik.md` justru andal** — angka-angkanya diuji ulang di G1
dan cocok persis dengan database. Dokumen itu diverifikasi terhadap DB nyata; dokumen skema
tidak.

> Aturan kerja: **skema dibaca dari database, bukan dari dokumen.**
> `SELECT column_name FROM information_schema.columns WHERE table_name = '…'`

---

## 1. Bentuk database sesungguhnya

**35 tabel · 4.224.932 baris · 59,8 MB.**

Perhatikan selisih kecil yang membingungkan: tabel `_meta_generator` mencatat
`jumlah_tabel = 34` dan `jumlah_baris_total = 4224925`, karena **tidak menghitung dirinya
sendiri** (7 baris). Keduanya benar; yang dipakai di tes G5 harus disebut jelas yang mana.

`TANGGAL_POTONG = 2026-09-15`, sumbernya `_meta_generator` kunci `tanggal_sekarang` —
**dibaca, tidak diketik dari ingatan** (P3).

Horison gelombang **2019–2025**. Tidak ada gelombang 2026: tahun itu murni fase perencanaan.

| Rumpun | Tabel |
|---|---|
| Program | `gelombang` (19) · `program` (76) · `profesi` (226) · `profesi_prodi` (427) |
| Kandidat | `kandidat` (368.912) · `kandidat_pendidikan` (1.071.976) · `kandidat_berkas` (1.351.088) · `kandidat_keluarga` (365.640) · `kandidat_sertifikasi` (146.783) |
| Seleksi | `pendaftaran` (218.928) · `seleksi_tahap` (464.688) · `seleksi_tahap_agregat` (9) · `tahap_ref` (16) |
| Pasca | `pasca_tahap` (49.977) · `penempatan` (7.711) |
| Perencanaan | `usulan_kebutuhan` (34.006) · `pagu_rekrutmen` (4.975) · `proyeksi_kekosongan` (92.928) · `kekosongan_ringkas` (384) · `realisasi_bulanan` (665) |
| Organisasi | `unit_induk` (48) · `unit_pelaksana` (357) · `posisi_unit_induk` (11.781) · `posisi_unit_pelaksana` (20.271) · `jabatan_katalog` (6.148) · `jabatan_klasifikasi` (6.148) · `updl` (11) |
| Referensi | `kota` (43) · `program_studi` (546) · `rumpun_jurusan` (18) · `rumpun_subbidang` (68) · `minat_profesi` (34) · `profil_usia` (8) · `vendor` (10) |

---

## 2. Angka jangkar — sudah dieksekusi

| Angka | Nilai | Query |
|---|---|---|
| Pendaftaran | **218.928** | `count(*) FROM pendaftaran` |
| Diterima | **7.711** | `hasil_akhir = 'DITERIMA'` |
| Sudah ber-SK | **5.711** | `penempatan.status_sk = 'SUDAH'` |
| Sedang OJT | **2.000** | `pasca_tahap tahap_kode='ojt' AND status='BERJALAN'` |
| Gap FTK nasional | **701** | `sum(ftk_2025) - sum(realisasi_mar_2026)` |

`hasil_akhir` **hanya punya dua nilai**: `DITERIMA` (7.711) dan `GAGAL` (211.217). Tidak ada
`MENGUNDURKAN_DIRI` atau `DALAM_PROSES` meskipun dokumen menyebutnya. Begitu pula
`status_lamaran` — nilainya **hanya** `SELESAI` untuk seluruh 218.928 baris, jadi kolom itu
tidak berguna sebagai penyaring.

**7.711 diterima ≠ 5.711 ber-SK.** Selisih 2.000 bukan kebocoran data — itu kohort yang sedang
OJT. Label di UI harus selalu eksplisit membedakan keduanya.

---

## 3. Yang sedang berjalan pada tanggal potong

Fakta terpenting untuk merancang halaman harian:

- Gelombang terakhir tutup **2025-10-05** → **345 hari** sebelum tanggal potong.
- Aktivitas `seleksi_tahap` terakhir **2026-02-16** → 211 hari sebelum tanggal potong.
- **2.000 orang sedang OJT** — dari G2025-092 (1.021 orang, selesai 2026-10-15) dan G2025-091
  (979 orang, selesai 2026-10-01). Progres 0,83 dan 0,91.
- Persis 2.000 orang itu yang `status_sk = 'BELUM'` (1.050 INDUK + 950 SUBHOLDING).

Jadi **angka 0 untuk "pendaftaran 30 hari terakhir" adalah jawaban yang benar**, bukan kartu
rusak. Jangan pernah menggantinya dengan `max(tanggal) - 30` supaya terlihat berisi (P3).
Tapi jangan pula menyimpulkan tidak ada yang berjalan — pipeline pasca-seleksinya hidup.

---

## 4. Jebakan data terverifikasi

Delapan butir pertama (J1–J8) diuji ulang di G1; **tiga di antaranya ternyata tidak akurat
seperti yang tercatat sebelumnya di `GOALS_V3.md`** — versi yang benar ada di sini. Dua butir
terakhir (J9–J10) ditemukan di G2 saat menguji perilaku dashboard dengan jangkar tanggal
berjalan; keduanya tidak terlihat selama jangkar waktunya dibekukan di tanggal potong.

### J1 · Kolom yang dibagikan acak seragam — jangan bangun analisis di atasnya

Diukur sebagai rasio frekuensi tertinggi : terendah. Makin dekat 1,0 makin seragam.

| Kolom | Nilai unik | Rasio | Putusan |
|---|---|---|---|
| `kandidat.ukuran_baju` | 4 | **1,017** | acak seragam |
| `kandidat.tempat_lahir` | 43 | **1,038** | acak seragam |
| `kandidat.kota_domisili` | 43 | **1,054** | acak seragam |
| `kandidat.kota_asal` | 43 | **1,074** | acak seragam |
| `kandidat_pendidikan.sekolah_universitas` | 68 | 6,182 mentah — **1,018** dengan filter `pendidikan_terakhir` | acak seragam **di dalam jenjang** |

**Koreksi.** `sekolah_universitas` tampak berpola (rasio 6,18) kalau dihitung mentah, semata
karena jenjang SD/SMP punya kumpulan sekolah lebih banyak. Dengan filter `pendidikan_terakhir`
— satu-satunya cara yang benar memakainya — tinggal 15 nilai dengan rasio **1,018**. Tetap
tidak layak dipakai.

Sebagai pembanding, kolom yang **berpola benar**: `propinsi_domisili` (rasio 16,4) ·
`status_perkawinan` (184) · `agama` (867).

### J2 · `kota_asal` menyalin `kota_domisili`

Dari 201.092 baris yang mengisi `kota_asal`, **199.310 identik** dengan `kota_domisili` —
**99,1%**, bukan 100%. Bug generator. Aturan `pct_domisili_beda_provinsi_dari_asal: 0.34`
tidak pernah dijalankan. Jangan buat analisis "asal vs tempat tes".

### J3 · Pasangan kota–propinsi mustahil

Kota dan propinsi diundi terpisah, menghasilkan **1.333** pasangan unik (bukan 1.334 seperti
tercatat sebelumnya), padahal seharusnya 43 — satu per kota. Contoh: `Jakarta` /
`Jawa Barat`. **Jangan pernah menampilkan kota dan propinsi berdampingan.**

### J4 · `unit_induk` — Yogyakarta terpecah, mewarisi identitas induknya

Satu-satunya `nama_pendek` yang duplikat di seluruh 48 baris. Yang membuatnya berbahaya:
**`kode_cocd` kedua baris sama-sama `5200`**, jadi join lewat `nama_pendek` *maupun*
`kode_cocd` akan menggandakan.

| `unit_induk` (nama panjang) | `kode_cocd` | `nama_pendek` | pegawai | ftk_2025 | realisasi_mar_2026 |
|---|---|---|---|---|---|
| PT PLN (PERSERO) UNIT INDUK DISTRIBUSI JAWA TENGAH DAN D.I. YOGYAKARTA | 5200 | UID Jawa Tengah & DIY | 1.643 | 1.516 | 1.654 |
| PT PLN (PERSERO) UNIT INDUK DISTRIBUSI YOGYAKARTA | 5200 | UID Jawa Tengah & DIY | **4** | 144 | **4** |

Baris kedua adalah pecahan Yogyakarta yang gagal match saat ekstraksi DAPEG lalu mewarisi
nama pendek dan kode induknya. `jumlah_pegawai = 4` mustahil untuk sebuah unit induk,
sementara `ftk_2025 = 144` masuk akal sebagai formasi yang salah dialokasikan.

Tanpa filter, unit ini menempati peringkat 1 gap secara palsu. Mitigasi:
`WHERE jumlah_pegawai > 50`. Anomalinya **dilaporkan**, bukan dihapus diam-diam.

### J5 · Kode gender adalah P/W, bukan L/P

`P` = Pria (233.982) · `W` = Wanita (134.930). Menganggap `P` = Perempuan akan **membalik
seluruh grafik gender**.

### J6 · Durasi konstan — analisis SLA tidak bermakna

**Koreksi.** Yang konstan 400 hari adalah jarak **tutup gelombang → tanggal SK**, persis 400
di seluruh 15 gelombang. Bukan "durasi pasca-seleksi 400 hari" seperti tercatat sebelumnya.

Durasi tahap pasca yang sebenarnya:

| Tahap | Durasi |
|---|---|
| `ojt` | **180 hari**, konstan di seluruh 17 gelombang |
| `ttd_kontrak`, `samapta`, `pembidangan`, `ujian_ojt`, `pengumuman_akhir`, `sk_penempatan` | **0 hari** — peristiwa titik, `tanggal_mulai = tanggal_selesai` |

Nol variasi berarti **analisis bottleneck / SLA / time-to-hire akan menyesatkan**. Jangan
dibuat.

### J7 · Jangan JOIN `seleksi_tahap_agregat` ke `pendaftaran`

`seleksi_tahap_agregat` **tidak punya `kandidat_id` maupun `pendaftaran_id`** — kolomnya hanya
`tahun_program, tahap_kode, nama, urutan, jumlah_masuk, jumlah_lulus, tanggal_estimasi,
pemilik_proses, status_sumber`. Isinya 3 baris per tahun RBB (2020, 2021, 2024).

JOIN langsung ke `pendaftaran` melipatgandakan hasil **3×**. Ketiadaan `kandidat_id` itu
disengaja: PLN memang tidak pernah memegang data per-kandidat tahap FHCI.

### J8 · Gap FTK wajib pakai `realisasi_mar_2026`

`realisasi_mar_2026` terisi untuk **48 dari 48** unit. `realisasi_apr_2026` terisi untuk
**1 dari 48**.

| Kolom dipakai | Gap FTK nasional |
|---|---|
| `realisasi_mar_2026` | **701** ← benar |
| `realisasi_apr_2026` | 33.934 ← palsu |
### J9 · Kohort 2025 tidak punya baris `ujian_ojt` dan `sk_penempatan`

Ditemukan saat menguji perilaku dashboard dengan jangkar tanggal berjalan.

| Gelombang | `ojt` | `ujian_ojt` | `sk_penempatan` |
|---|---|---|---|
| G2024-087 | 990 | 990 | 990 |
| G2025-091 | 979 | **0** | **0** |
| G2025-092 | 1.021 | **0** | **0** |

Generator berhenti menulis peristiwa pasca-OJT untuk kohort 2025. Akibatnya, begitu tanggal
berjalan melewati **2026-10-15** (OJT terakhir selesai), 2.000 orang **selesai OJT tapi tidak
pernah ujian dan tidak pernah ber-SK** — mereka lenyap dari pipeline:

| Tanggal | OJT kelar | Ujian kelar | SK terbit | Menggantung |
|---|---|---|---|---|
| 2026-10-15 | 7.711 | 5.711 | 5.711 | **2.000** |
| 2027-01-06 | 7.711 | 5.711 | 5.711 | **2.000** |

Cacat ini **tidak terlihat** kalau jangkar waktunya dibekukan di tanggal potong. Halaman
Pasca-Seleksi harus menampilkan keadaan ini apa adanya, bukan menyembunyikannya.

### J10 · Horison data berakhir 2026-10-15

Peristiwa terjadwal paling akhir di seluruh database adalah `pasca_tahap.tanggal_selesai`
maksimum = **2026-10-15**. Sesudah tanggal itu tidak ada apa pun yang pernah berstatus
"sedang berjalan" lagi.

Horison per tabel:

| Kolom | Terjauh |
|---|---|
| `gelombang.tgl_tutup` · `profesi.tgl_tutup` · `pendaftaran.tanggal_lamar` | 2025-10-05 |
| `seleksi_tahap.tanggal_tahap` | 2026-02-16 |
| `pasca_tahap.tanggal_mulai` | 2026-04-18 |
| `pasca_tahap.tanggal_selesai` | **2026-10-15** |

Halaman yang bergantung pada "sedang berjalan" harus punya keadaan kosong yang bermartabat,
karena keadaan itu **pasti** akan tiba.


---

## 5. Kolom yang aman dipakai

Sudah tervalidasi berpola, bukan acak seragam:

`kandidat.propinsi_domisili` · `kandidat.agama` · `kandidat.status_perkawinan` ·
`kandidat.tanggal_lahir` (umur berpuncak di 21) · `kandidat_pendidikan.degree` ·
`kandidat_pendidikan.program_studi` · `seleksi_tahap.mode` · `seleksi_tahap.lokasi_kota` ·
`seleksi_tahap.status_hadir` · `seleksi_tahap.vendor_id` · `penempatan.bidang_pembidangan` ·
`penempatan.unit_induk` · `penempatan.kode_grade` · `gelombang.*`

---

## 6. Penanda kualitas yang sudah ada di data

Database membawa penanda provenans sendiri — **pakai, jangan diabaikan**:

| Kolom | Nilai | Artinya |
|---|---|---|
| `gelombang.sumber_nomor` | `nyata` / `inferensi` / `inferensi_kuat` | seberapa kuat dasar nomor angkatan |
| `gelombang.tgl_status` | `nyata` / `estimasi` | tanggal buka/tutup asli atau diperkirakan |
| `gelombang.kualitas_kohort` | `rendah` / `sedang` / `tinggi` | 2019–2021 rendah, 2023 & 2025 tinggi |
| `seleksi_tahap.sumber_skor` | seluruh 464.688 baris DIMODELKAN | skor tes **tidak pernah ada** di sistem asli |
| `tahap_ref.skor_ada_di_sistem_asli` | **False** untuk 9 tahap berskor (6 seleksi + 3 FHCI); `NULL` untuk 7 tahap pasca yang memang tak berskor | sistem PLN hanya menyimpan lulus/gagal |

`tahap_ref.skor_ada_di_sistem_asli` yang tidak pernah bernilai True adalah pernyataan penting:
**passing grade dan skor mentah tidak ada di sumber manapun.** Apa pun yang dibangun di atas
skor adalah bahan halaman Eksplorasi (G15), bukan halaman berdata nyata.

---

## 7. Perangkap penyajian

**Tahun RBB tidak boleh dibandingkan langsung dengan tahun mandiri.** Untuk 2020, 2021, dan
2024, yang tercatat di PLN hanya sisa setelah saringan FHCI — bukan seluruh pelamar. Menyajikan
2021 sebagai "pemenuhan 7,1%" adalah salah baca. Beri penanda jalur; jangan satu garis mulus.

**Dua angka rencana tidak pernah didamaikan.** `pagu_rekrutmen` (sisi anggaran) dan
`gelombang.diterima_target` (sisi program) berbeda untuk tahun yang sama, dan selisihnya
melebar. Ini **temuan yang layak ditampilkan**, bukan cacat yang disembunyikan — dan justru
menjawab "Seberapa tepat perenanaan mereka?"

**`kandidat_pendidikan` wajib difilter `pendidikan_terakhir`.** Tanpa itu, tiap kandidat
menyumbang ±4 baris riwayat sekolah dan seluruh hitungan jenjang membengkak (1.071.976 baris
untuk 368.912 kandidat).

**Kolom PII dilarang tampil di UI** (ditegakkan mekanis di `tests/uji_disiplin.py`):
`nama_lengkap` · `no_ktp` · `email` · `no_handphone` · `alamat_domisili` · `alamat_asal`.

---

## 8. Jangan pernah

- Menunjuk `mockdb/out/rekrutmen.duckdb.tmp/` — pakai `mockdb/out/rekrutmen.duckdb`.
- Memuat tabel penuh ke DataFrame. Selalu agregat atau `LIMIT`.
- Membuka database selain **read-only**.
- Memakai `max(tanggal_x)` sebagai pengganti hari ini (P3).
