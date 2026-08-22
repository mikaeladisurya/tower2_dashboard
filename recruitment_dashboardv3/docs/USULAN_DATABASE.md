# Usulan pengembangan database

Kebutuhan data yang **belum terpenuhi** oleh `mockdb/out/rekrutmen.duckdb`. Berkas ini
bermuara ke sesi perbaikan generator mockdb dan ke **dashboard v4**.

**Tidak satu pun isi berkas ini tampil di UI.**

Dua sumber isian:
- **Bagian A–C** ditulis di G2, saat merancang halaman dan menguji perilaku dashboard dengan
  jangkar tanggal berjalan.
- **Bagian D** akan diisi otomatis oleh G17 — tiap section di halaman Eksplorasi jadi satu
  baris di sini.

Rujukan jebakan (J1–J10) ada di [CATATAN_DATA.md](CATATAN_DATA.md) §4.

---

## A. Bug generator — data yang ada tapi salah

Yang paling mendesak, karena dashboard v3 sudah menabraknya.

### A1 · Kohort 2025 tidak punya baris `ujian_ojt` dan `sk_penempatan` ⚠️ prioritas tertinggi

| Gelombang | `ojt` | `ujian_ojt` | `sk_penempatan` |
|---|---|---|---|
| G2024-087 (pembanding sehat) | 990 | 990 | 990 |
| G2025-091 | 979 | **0** | **0** |
| G2025-092 | 1.021 | **0** | **0** |

Generator berhenti menulis peristiwa pasca-OJT untuk kohort 2025. Begitu tanggal berjalan
melewati **2026-10-15**, 2.000 orang selesai OJT lalu **lenyap dari pipeline** — tidak pernah
ujian, tidak pernah ber-SK, selamanya.

**Yang perlu ditambah:** baris `ujian_ojt` (rentang ~10 hari) dan `sk_penempatan` untuk kedua
gelombang, plus pengisian `penempatan.unit_induk` yang saat ini kosong di seluruh 2.000 baris.

**Rujukan:** J9.

### A2 · Horison data berhenti 2026-10-15 — tidak ada gelombang 2026/2027

| Kolom | Tanggal terjauh |
|---|---|
| `gelombang.tgl_tutup` · `pendaftaran.tanggal_lamar` | 2025-10-05 |
| `seleksi_tahap.tanggal_tahap` | 2026-02-16 |
| `pasca_tahap.tanggal_selesai` | **2026-10-15** |

Sesudah 2026-10-15 tidak ada apa pun yang pernah berstatus "sedang berjalan". Halaman
**Seleksi Berjalan** bahkan kosong sejak sekarang — gelombang terakhir tutup 2025-10-05.

**Yang perlu ditambah:** minimal satu gelombang 2026 dan satu 2027 dengan `seleksi_tahap`
lengkap, supaya halaman pemantauan seleksi punya isi dan pipeline terus mengalir.

**Rujukan:** J10.

### A3 · Lima kolom dibagikan acak seragam

`kandidat.kota_domisili` · `kandidat.kota_asal` · `kandidat.tempat_lahir` ·
`kandidat.ukuran_baju` · `kandidat_pendidikan.sekolah_universitas`

Rasio frekuensi tertinggi:terendah 1,017–1,074 — tidak ada sinyal sama sekali. `demografi.yaml`
sudah mendefinisikan `sebaran_provinsi_asal`, tapi generator memanggil `rng.choice()` tanpa
bobot `p=`.

**Akibat ke dashboard:** analisis almamater dan sebaran asal kandidat **dibatalkan** di v3.

**Rujukan:** J1.

### A4 · `kota_asal` menyalin `kota_domisili`

199.310 dari 201.092 baris (99,1%) identik. Aturan
`pct_domisili_beda_provinsi_dari_asal: 0.34` tidak pernah dieksekusi. Fitur "dua blok alamat"
jadi kosmetik, dan peta "asal vs kota tes" tidak bisa dibuat.

**Rujukan:** J2.

### A5 · Kota dan propinsi diundi terpisah

Menghasilkan **1.333** pasangan kota–propinsi unik, padahal seharusnya 43 — satu per kota.
Contoh: `Jakarta` / `Jawa Barat`. Akibatnya kota dan propinsi **tidak boleh** ditampilkan
berdampingan di mana pun.

**Rujukan:** J3.

### A6 · Baris `unit_induk` Yogyakarta mewarisi identitas induknya

Dua baris dengan `nama_pendek` sama (`UID Jawa Tengah & DIY`) **dan `kode_cocd` sama (5200)`**,
tapi nama panjang berbeda. Baris kedua (`jumlah_pegawai = 4`) adalah pecahan Yogyakarta yang
gagal match saat ekstraksi DAPEG. Join lewat `nama_pendek` maupun `kode_cocd` akan menggandakan.

Mitigasi sementara di dashboard: `WHERE jumlah_pegawai > 50`.

**Rujukan:** J4.

### A7 · Durasi antar tahap konstan

Jarak tutup gelombang → SK **persis 400 hari** di seluruh 15 gelombang. OJT persis 180 hari,
ttd kontrak 13 hari, SAMAPTA 14 hari, ujian OJT 10 hari — sama di semua kohort.

**Akibat:** analisis SLA, bottleneck pasca-seleksi, dan time-to-hire **tidak bermakna** dan
sengaja tidak dibuat di v3. Butuh variasi realistis supaya bisa dianalisis.

**Rujukan:** J6.

### A8 · `realisasi_apr_2026` hanya terisi 1 dari 48 unit

Memakainya menghasilkan gap FTK palsu 33.934, dibanding 701 yang benar dari
`realisasi_mar_2026`.

**Rujukan:** J8.

---

## B. Data yang belum ada sama sekali

Semuanya diminta pemilik proses di requirement gathering, dan **tidak satu pun ada di
database**. Ini yang jadi section di halaman Eksplorasi (G17).

| # | Kebutuhan | Yang diminta | Tabel/kolom yang perlu ditambah |
|---|---|---|---|
| B1 | **Kategori 2T/3T** | *"fulfillment 3T ini menjadi poin yg diperhatikan"* · *"temen2 ojt harusnya ditempatkan di 3T tapi penempatannya kok ngga sesuai?"* | Kolom kategori keterpencilan di `unit_pelaksana` / `kota`. Nol kolom bertanda 2T/3T di 35 tabel — sudah dipindai seluruh `information_schema`. |
| B2 | **Proyeksi kekosongan 2027+** | *"misal untuk perencanaan 1 januari 2027, akan ada kosong berapa banyak, dimana, jabatan apa"* | Perpanjang `proyeksi_kekosongan` ke 2027–2031 |
| B3 | **Kompetensi jabatan (KKJ)** | *"mengacu ke kompetensi jabatan, direktori kompetensi"* — plus kompetensi jabatan **masa depan** | Tabel `kompetensi`, `kompetensi_jabatan`, `kompetensi_kandidat` |
| B4 | **Skor tes & passing grade** | analisis bottleneck berbasis skor, prediksi kelulusan | `seleksi_skor` per komponen. `tahap_ref.skor_ada_di_sistem_asli` tidak pernah `True` — sistem asli PLN memang hanya menyimpan lulus/gagal |
| B5 | **Peristiwa pegawai per orang** | *"apkah bisa diakomodir data2nya link dengan data aps, rotasi, mutasi"* — termasuk tugas karya yang kembali ke holding | Tabel `peristiwa_pegawai` (pensiun, APS, rotasi, mutasi, tugas karya) per orang per tanggal. Sekarang hanya ada agregat di `proyeksi_kekosongan` |
| B6 | **Lokasi tiap tahap pasca** | *"dimana samaptanya"* · *"dimana updl pembidangannya"* | Kolom lokasi di `pasca_tahap`. Sekarang `updl_id` hanya ada di `penempatan`, satu per orang |
| B7 | **Kapasitas UPDL** | apakah 11 UPDL sanggup menampung kohort berikutnya | Kolom kapasitas kelas per UPDL per periode |
| B8 | **Efektivitas sumber rekrutmen** | *"source mana paling banyak yield"* · *"source mana paling banyak kandidat berkualitas"* | Jalur sudah ada (`sumber_rekrutmen`, `jenis_program`), tapi **kualitas hasil** tidak terukur — butuh B4 dan data kinerja pasca-masuk |
| B9 | **Biaya rekrutmen** | cost per hire, cost per applicant, quality-adjusted cost | Tabel biaya per program/kanal. Dokumen master memuat kerangkanya lengkap |
| B10 | **Kinerja & retensi pasca-masuk** | *"Does TPA predict OJT performance?"* dari dokumen master | Data kinerja tahun pertama, retensi, evaluasi atasan |

---

## C. Dokumen yang perlu disinkronkan

### C1 · `mockdb/docs/ERD.md` dan `kamus_data.md` tidak menggambarkan database yang dibangun

Ditulis **2026-08-19 21:40**; database dibangun **13:13** hari yang sama. Dokumennya lebih baru
tapi menjelaskan skema yang tidak pernah jadi.

- **Sebelas tabel** dijelaskan panjang lebar tapi tidak ada: `perusahaan`, `jabatan`,
  `posisi_unit`, `pengumuman`, `seleksi_skor`, `tahap_agregat`, `kontrak`, `prajabatan`,
  `pegawai`, `headcount_tahunan`, `peristiwa_pegawai`
- **Enam tabel** ada tapi nol kali disebut: `pasca_tahap`, `seleksi_tahap_agregat`,
  `jabatan_katalog`, `kekosongan_ringkas`, `minat_profesi`, `profil_usia`
- Jumlah baris meleset jauh (`pendaftaran` disebut ±314.730; sesungguhnya 218.928)

**Yang perlu:** regenerate kedua dokumen dari `information_schema` database yang sudah jadi,
bukan ditulis manual.

### C2 · `_meta_generator` tidak menghitung dirinya sendiri

Mencatat `jumlah_tabel = 34` dan `jumlah_baris_total = 4224925`, sedangkan database berisi
**35 tabel / 4.224.932 baris**. Selisihnya persis tabel `_meta_generator` (7 baris). Bukan
salah, tapi perlu dinyatakan eksplisit supaya tes tidak salah patokan.

### C3 · Nilai enum lebih sempit dari yang didokumentasikan

- `pendaftaran.hasil_akhir` hanya `DITERIMA` / `GAGAL`. Tidak ada `MENGUNDURKAN_DIRI` maupun
  `DALAM_PROSES` meski dokumen menyebutnya.
- `pendaftaran.status_lamaran` hanya `SELESAI` untuk seluruh 218.928 baris — kolomnya tidak
  berguna sebagai penyaring.

---

## D. Dari halaman Eksplorasi

*Diisi di G17. Tiap section di halaman Eksplorasi menambah satu baris di sini: fitur apa · data
apa yang kurang · tabel/kolom yang perlu ditambah.*
