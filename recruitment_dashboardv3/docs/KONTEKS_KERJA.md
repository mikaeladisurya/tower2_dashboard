# Konteks kerja tim rekrutmen PLN

Dokumen ini menjawab satu pertanyaan: **pekerjaan siapa yang sedang dibantu dashboard ini,
dan pertanyaan apa yang muncul di meja mereka berulang-ulang.**

Disusun di G1 sebagai bahan G2. Susunan halaman v3 dirancang dari dokumen ini, **bukan** dari
bentuk tabel database — itu kesalahan pokok v2.

Sumber: `referensi/PLN_Recruitment_Master_Context_2019_2026.docx` (wajib, dibaca utuh) ·
`referensi/ReqGathering 1–4.txt` (notulen requirement gathering dengan pemilik proses) ·
`referensi/WhatsApp Chat with Willy Hendrawan` · tangkapan layar portal rekrutmen ·
pembacaan langsung `mockdb/out/rekrutmen.duckdb`.

---

## 1. Siapa yang bekerja

Rekrutmen PLN bukan satu tim. Ia dikerjakan empat pihak yang **saling menyerahkan pekerjaan**,
dan setiap serah-terima itulah tempat pertanyaan muncul.

| Pihak | Perannya | Yang dipegang |
|---|---|---|
| **HST** — Div. Perencanaan & Evaluasi Tenaga Kerja | Merencanakan: berapa yang kurang, di mana, jabatan apa | pagu, FTK, proyeksi jabatan kosong, kategori 2T/3T |
| **HTD** — Div. Akuisisi Talenta | Melaksanakan rekrutmen secara teknis, menerbitkan SK | pelaksanaan seleksi, kontrak, pengangkatan |
| **HSC** — Human Services Center | Kustodian data pegawai | DAPEG, statistik bulanan |
| **Pusdiklat** | Menyelenggarakan prajabatan/OJT | pelaksanaan diklat, hasil ujian OJT |

Vendor luar: **seleksi.pln.co.id** (tes akademik & Inggris) · **UPAG** (tes adaptif) ·
**Kimia Farma** (pemeriksaan kesehatan).

Pembagian yang paling menentukan bentuk dashboard:

> **HST merencanakan. HTD melaksanakan.** Keduanya memegang angka rencana masing-masing, dan
> angka itu **tidak pernah didamaikan**.

---

## 2. Alur kerja, tahap demi tahap

Nilai `pemilik_proses` dan `sistem_sumber` di bawah bukan tafsiran — keduanya kolom nyata di
tabel `tahap_ref`, dibaca langsung dari database.

### Fase A — Perencanaan formasi (HST, sepanjang tahun)

| | |
|---|---|
| **Pelaku** | HST, dengan data pegawai dari HSC |
| **Sistem** | DAPEG (Excel dari NAS, tarik bulanan) · HXMS · Direktori Kompetensi |
| **Keputusan** | Berapa formasi kosong tahun depan · pagu per unit · prioritas 2T/3T · kompetensi yang dicari |

Kekosongan tidak datang dari satu sebab. Yang dihitung: pensiun, APS (permintaan pindah
pribadi), rotasi, mutasi, **dan tugas karya** — termasuk pegawai tugas karya yang akan kembali
ke holding dan harus ditempatkan.

Perencanaan berjalan **jauh di muka**: untuk rekrutmen 2026, HST sudah bergerak sejak
November 2025.

### Fase B — Pembukaan gelombang (HTD)

| | |
|---|---|
| **Pelaku** | HTD, koordinasi dengan Komunikasi untuk penyebaran |
| **Sistem** | `rekrutmen.pln.co.id` |
| **Keputusan** | Metode rekrutmen (open recruitment web PLN / direct sourcing / campus hiring / BUMN) · vendor asesmen · susunan tahap |

Satu pagu bisa dipecah ke beberapa metode. Pembukaan tertutup disebarkan lewat direct
sourcing, bukan web publik.

### Fase C — Seleksi

Dua jalur berbeda, satu struktur data. Kolom `masuk_mandiri` dan `masuk_rbb` di `tahap_ref`
yang menentukan tahap mana berlaku untuk jalur mana.

**Jalur mandiri (PLN sendiri)** — enam tahap, per kandidat sejak awal:

| # | Tahap | Pemilik | Sistem | Mode |
|---|---|---|---|---|
| 1 | Seleksi Administrasi | PLN_HTD | rekrutmen.pln.co.id | dokumen |
| 2 | Tes Adaptif PLN (TAP) | PLN_HTD | rekrutmen.pln.co.id | online, dari rumah |
| 3 | Tes Akademik (TKB) & Inggris | PLN_HTD | seleksi.pln.co.id | online, dari rumah |
| 4 | Tes Psikologi | VENDOR | rekrutmen.pln.co.id (hasil di-upload) | offline, kota terkunci |
| 5 | Tes Fisik & MCU | VENDOR | rekrutmen.pln.co.id (hasil di-upload) | offline, kota terkunci |
| 6 | Wawancara User & HR | PLN_USER | rekrutmen.pln.co.id | offline, kota terkunci |

**Jalur RBB (Rekrutmen Bersama BUMN)** — tiga tahap pertama dikerjakan **FHCI**, di
`rekrutmenbersama.fhcibumn.id`, dan PLN hanya menerima **jumlah agregat tanpa identitas**.
PLN baru masuk di tahap akademik. Ini bukan kekurangan data yang perlu ditutupi — PLN memang
tidak pernah memegangnya.

Dua hal yang ditegaskan pemilik proses:

> "apakah tahapan seleksi selalu sama? sepertinya tidak" · "urutan tahapan bisa berubah"
> — `ReqGathering 4.txt:2,7`

Artinya susunan tahap **tidak boleh di-hardcode** di halaman mana pun.

**Serah-terima hasil tes masih manual.** Hasil dari `seleksi.pln.co.id` diunduh per angkatan
lalu diunggah ke `rekrutmen.pln.co.id`. Tidak ada integrasi otomatis antara kedua sistem.

### Fase D — Pasca-seleksi (kedua jalur sama)

Kepemilikan berpindah: HTD → Pusdiklat → HTD.

| Urutan | Tahap | Pemilik | Sistem |
|---|---|---|---|
| 100 | Pengumuman Hasil Seleksi | PLN_HTD | rekrutmen.pln.co.id |
| 101 | Penandatanganan Perjanjian | PLN_HTD | rekrutmen.pln.co.id |
| 102 | SAMAPTA | PUSDIKLAT | aplikasi Pusdiklat |
| 103 | Penetapan Pembidangan | PUSDIKLAT | aplikasi Pusdiklat |
| 104 | Diklat Prajabatan / First OJT | PUSDIKLAT | aplikasi Pusdiklat |
| 105 | Ujian Akhir OJT | PUSDIKLAT | aplikasi Pusdiklat |
| 106 | SK Pengangkatan & Penempatan | PLN_HTD | rekrutmen.pln.co.id |

Pusdiklat memakai **aplikasi terpisah**; hasilnya dilaporkan balik ke HTD. Ini serah-terima
kedua, dan sumber pertanyaan alignment di bawah.

---

## 3. Pertanyaan yang muncul berulang

**Bagian ini yang menjadi bahan G2.** Semua kutipan verbatim dari notulen; ejaan asli
dipertahankan.

### Dari HST — perencanaan

> "Untuk perencanaan rekrutmen, harapannya di digital analytic bisa ada data pagu, ftk,
> proyeksi jabatan yg sudah direncanakan, sehingga teman yg eksekusi rekrutmen saat print SK
> sesuai dengan yg direncanakan." — `ReqGathering 1.txt:3`

> "misal untuk perencanaan 1 januari 2027, akan ada kosong berapa banyak, dimana, jabatan apa,
> kompetensi yg dibutuhkan, dst, kami ingin bisa melihat yg akan kosong, yg akan diproses aps,
> sehingga perencanaan rekrutmen untuk beberapa bulan ke depan bisa update realtime."
> — `ReqGathering 1.txt:6`

> "Misal di rekrutmen 2026 kmrn, kami sudah bergerak dari november2025, berapa yg akan pensiun
> di tiap bulan ke depan, setiap aps yg memang eksekusi dst, atau tiba2 ada yg ikut pegawai
> tugas belajar keluar sehingga kosong." — `ReqGathering 1.txt:7`

> "Pada saat realisasi pengangkatan, databasenya mungkin bisa berbeda karena aps, rotasi,
> mutasi, nah apkah bisa diakomodir data2nya link dengan data aps, rotasi, mutasi ini di mas
> Gerry supaya terlihat tempat yg memang kosong dimana." — `ReqGathering 1.txt:4`

### Dari HTD — pelaksanaan

> "saat ini dashboard rekrutmen hanya filter, tidak ada analisis" — `ReqGathering 4.txt:4`

> "apakah aligment penempatannya sudah sesuai?" — `ReqGathering 4.txt:8`

> "temen2 ojt harusnya ditempatkan di 3T tapi penempatannya kok ngga sesuai? HST sudah
> merencanakan, tapi HTD menempatkan berbedadg rencana" — `ReqGathering 4.txt:9`

> "fulfillment 3T ini menjadi poin yg diperhatikan (rekrutmen diprioritaskan ke 3T)"
> — `ReqGathering 4.txt:3`

Dan saat ditanya apakah HTD punya dashboard untuk memantau perjalanan peserta:

> "saat ini belum ada mas kalau dashboard" — Willy Hendrawan, HTD

### Dari nota dinas resmi

> "dashboard yang dikembangkan diharapkan dapat mendukung monitoring proses rekrutmen
> end-to-end, analisis bottleneck dari tahapan rekrutmen, evaluasi kesesuaian kandidat
> terhadap kebutuhan jabatan, serta penyediaan insight dari data rekrutmen."
> — `ReqGathering 3.txt:50`

### Pertanyaan penutup yang paling tajam

> "Seberapa tepat perenanaan mereka?" — `ReqGathering 1.txt:31`

---

## 4. Enam pertanyaan inti, disarikan

Semua kutipan di atas bermuara ke enam pertanyaan. Inilah yang harus dijawab halaman v3.

1. **Apa yang sedang berjalan hari ini, dan adakah yang tersendat?**
   Satu-satunya yang benar-benar berjalan pada tanggal potong: **2.000 orang sedang OJT**,
   selesai 1–15 Oktober 2026, semuanya belum ber-SK.
2. **Berapa yang akan kosong, di mana, jabatan apa?** — pertanyaan HST, berorientasi ke depan.
3. **Seberapa tepat perencanaan itu ternyata?** — rencana vs realisasi, per tahun, per unit.
4. **Apakah penempatan akhir sesuai rencana?** — khususnya pemenuhan 3T. Pertanyaan alignment
   HST↔HTD, dan yang paling sering disebut sebagai keluhan.
5. **Di tahap mana orang hilang, dan kenapa?** — gugur karena gagal tes, atau karena tidak
   hadir sama sekali.
6. **Siapa yang melamar, dan apakah cocok dengan yang dibutuhkan?**

---

## 5. Yang perlu diketahui sebelum merancang halaman

**Ini bukan sistem yang sibuk setiap hari.** Gelombang terakhir tutup 2025-10-05 — **345 hari**
sebelum tanggal potong. Halaman yang dirancang dengan asumsi "ada seleksi berlangsung hari ini"
akan kosong dan terlihat rusak.

Tapi "tidak ada gelombang dibuka" **tidak sama dengan** "tidak ada yang berjalan". Pipeline-nya
hidup: 2.000 orang sedang OJT dan menunggu SK. Halaman harian yang jujur dibangun di atas fakta
itu, bukan dengan memundurkan tanggal supaya angkanya terlihat ramai.

**Ukuran keberhasilan rancangan G2:** layak dibuka setiap hari. Kalau isi sebuah halaman sama
persis tiap kali dibuka, halaman itu gagal.

**Rekrutmen PLN bukan satu pipeline.** Kesimpulan pokok dokumen master, dan ini membantah cara
v2 memandangnya:

> "The key conclusion is that PLN recruitment should NOT be modeled as one annual recruitment
> program. It is better understood as a Talent Acquisition Portfolio consisting of multiple
> external recruitment channels and separate internal/group workforce movements."

Data mendukungnya: 19 gelombang di database terbagi ke enam `jenis_program` — REGULER,
AFIRMASI, RBB, PRO_HIRE, S2, DIASPORA — dengan perilaku yang sangat berbeda. Chart yang
meleburnya jadi satu garis mulus menyembunyikan justru hal yang paling penting.

**Dua peringatan lain dari dokumen master** yang membatasi cara menyajikan angka:

> "Always distinguish PLN Holding from PLN Group."
> "Do not combine outsourced/TAD workers with employees."

**Yang diminta tapi datanya belum ada** — kandidat untuk halaman Eksplorasi (G15), bukan untuk
halaman berdata nyata: kompetensi jabatan & direktori kompetensi · data APS/rotasi/mutasi/tugas
karya per orang · kategori 2T/3T per lokasi · recruitment source effectiveness · pencocokan
kandidat dengan kebutuhan jabatan.

Rinciannya, beserta apa yang cacat dan apa yang aman dipakai, ada di
[CATATAN_DATA.md](CATATAN_DATA.md).
